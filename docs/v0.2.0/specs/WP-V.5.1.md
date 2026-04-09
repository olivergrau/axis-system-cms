# WP-V.5.1 Implementation Brief -- Adapter Test Suite

## Context

Phases V-1 and V-2 introduced the adapter protocols, fallback adapters, the visualization registry, and all concrete adapters (4 world adapters, 3 system adapters). Each WP included a handful of smoke tests. This WP provides a **systematic, combinatorial** test suite that validates all adapter contracts, exercises all (world, system) pairs through the ViewModelBuilder, and confirms registry resolution correctness.

The individual per-WP tests (e.g., `test_grid2d_world_adapter.py`) verified basic construction and registration. This suite goes further: it validates the full adapter protocol contract for each adapter, tests cross-adapter integration through the ViewModelBuilder, and exercises edge cases (empty system_data, missing hotspots, boundary grid sizes).

### Predecessor State (After Phase V-4)

```
src/axis/visualization/
    __init__.py
    types.py                             # CellLayout, CellColorConfig, OverlayData, etc.
    protocols.py                         # WorldVisualizationAdapter, SystemVisualizationAdapter
    registry.py                          # register/resolve functions
    errors.py
    replay_models.py
    replay_validation.py
    replay_access.py
    snapshot_models.py
    snapshot_resolver.py
    viewer_state.py
    viewer_state_transitions.py
    playback_controller.py
    view_models.py
    view_model_builder.py
    adapters/
        default_world.py                 # DefaultWorldVisualizationAdapter
        null_system.py                   # NullSystemVisualizationAdapter
    ui/
        __init__.py
        canvas_widget.py
        overlay_renderer.py
        status_panel.py
        step_analysis_panel.py
        detail_panel.py
        replay_controls_panel.py
        overlay_panel.py
        main_window.py
        session_controller.py
        app.py
    launch.py

src/axis/world/grid_2d/visualization.py     # Grid2DWorldVisualizationAdapter
src/axis/world/toroidal/visualization.py    # ToroidalWorldVisualizationAdapter
src/axis/world/signal_landscape/visualization.py  # SignalLandscapeWorldVisualizationAdapter
src/axis/systems/system_a/visualization.py  # SystemAVisualizationAdapter
src/axis/systems/system_b/visualization.py  # SystemBVisualizationAdapter
```

### Reference Documents

- `docs/v0.2.0/architecture/evolution/visualization-architecture.md` -- Sections 4, 5, 11 (Adapter protocols and concrete adapters)
- `docs/v0.2.0/architecture/evolution/visualization-architecture-roadmap.md` -- WP-V.5.1
- Individual adapter WP specs: WP-V.1.3, WP-V.2.1 through WP-V.2.5

---

## Objective

Provide comprehensive, systematic tests for all concrete adapters and their interaction through the ViewModelBuilder, covering all (world, system) pair combinations.

---

## Scope

### 1. Test Fixtures Module

**File**: `tests/v02/visualization/adapter_fixtures.py` (new)

Shared fixtures used across all adapter test files. Having a common fixtures module avoids duplicating mock data across the three test files in this WP.

```python
"""Shared fixtures for adapter test suite.

Provides factory functions for mock data structures:
WorldSnapshot, BaseStepTrace, system_data dicts.
"""

from __future__ import annotations

from typing import Any

from axis.sdk.snapshot import CellView, Position, WorldSnapshot
from axis.sdk.trace import BaseStepTrace


# -- World Snapshot Factories -------------------------------------------------

def make_world_snapshot(
    width: int = 5,
    height: int = 5,
    agent_position: tuple[int, int] = (2, 2),
    resource_positions: dict[tuple[int, int], float] | None = None,
    obstacle_positions: set[tuple[int, int]] | None = None,
) -> WorldSnapshot:
    """Create a WorldSnapshot with configurable layout.

    Args:
        width: Grid width.
        height: Grid height.
        agent_position: (col, row) of the agent.
        resource_positions: Mapping of (col, row) → resource value.
        obstacle_positions: Set of (col, row) positions that are obstacles.
    """
    resources = resource_positions or {}
    obstacles = obstacle_positions or set()

    grid = []
    for row in range(height):
        row_cells = []
        for col in range(width):
            is_obstacle = (col, row) in obstacles
            resource = resources.get((col, row), 0.0)
            row_cells.append(CellView(
                is_traversable=not is_obstacle,
                resource_value=resource,
            ))
        grid.append(tuple(row_cells))

    return WorldSnapshot(
        grid=tuple(grid),
        agent_position=Position(x=agent_position[0], y=agent_position[1]),
        width=width,
        height=height,
    )


# -- System Data Factories ---------------------------------------------------

def make_system_a_system_data(
    energy_before: float = 3.0,
    energy_after: float = 2.5,
    selected_action: str = "up",
) -> dict[str, Any]:
    """Create a realistic System A system_data dict."""
    return {
        "decision_data": {
            "observation": {
                "current": {"traversability": 1.0, "resource": 0.5},
                "up":      {"traversability": 1.0, "resource": 0.0},
                "down":    {"traversability": 1.0, "resource": 0.3},
                "left":    {"traversability": 0.0, "resource": 0.0},
                "right":   {"traversability": 1.0, "resource": 0.8},
            },
            "drive": {
                "activation": 0.75,
                "action_contributions": (0.2, 0.1, 0.0, 0.3, 0.25, 0.15),
            },
            "policy": {
                "raw_contributions": (0.2, 0.1, 0.0, 0.3, 0.25, 0.15),
                "admissibility_mask": (True, True, False, True, True, True),
                "masked_contributions": (0.2, 0.1, float("-inf"), 0.3, 0.25, 0.15),
                "probabilities": (0.18, 0.12, 0.0, 0.30, 0.22, 0.18),
                "selected_action": selected_action,
                "temperature": 1.0,
                "selection_mode": "sample",
            },
        },
        "trace_data": {
            "energy_before": energy_before,
            "energy_after": energy_after,
            "energy_delta": energy_after - energy_before,
            "action_cost": 0.1,
            "energy_gain": 0.0,
            "memory_entries_before": 0,
            "memory_entries_after": 0,
        },
    }


def make_system_b_system_data(
    energy_before: float = 4.0,
    energy_after: float = 3.5,
    selected_action: str = "right",
) -> dict[str, Any]:
    """Create a realistic System B system_data dict."""
    return {
        "decision_data": {
            "weights": [0.15, 0.10, 0.05, 0.35, 0.20, 0.15],
            "probabilities": [0.14, 0.11, 0.07, 0.33, 0.20, 0.15],
            "last_scan": {
                "total_resource": 2.5,
                "cell_count": 5,
            },
        },
        "trace_data": {
            "energy_before": energy_before,
            "energy_after": energy_after,
            "energy_delta": energy_after - energy_before,
            "action_cost": 0.5,
            "scan_total": 2.5,
        },
    }


# -- World Data Factories ----------------------------------------------------

def make_grid_2d_world_data() -> dict[str, Any]:
    """World data for grid_2d (empty -- no extra metadata)."""
    return {}


def make_toroidal_world_data() -> dict[str, Any]:
    """World data for toroidal world."""
    return {"topology": "toroidal"}


def make_signal_landscape_world_data(
    hotspots: list[dict[str, float]] | None = None,
) -> dict[str, Any]:
    """World data for signal landscape world."""
    if hotspots is None:
        hotspots = [
            {"cx": 2.0, "cy": 3.0, "radius": 2.0, "intensity": 0.8},
            {"cx": 7.0, "cy": 1.0, "radius": 1.5, "intensity": 0.5},
        ]
    return {"hotspots": hotspots}
```

### 2. World Adapter Protocol Compliance Tests

**File**: `tests/v02/visualization/test_world_adapter_suite.py` (new)

This file tests all 4 world adapters against the full `WorldVisualizationAdapter` protocol contract. A parametrized test class ensures every adapter satisfies every protocol method.

```python
"""Systematic tests for all world visualization adapters.

Each test is parametrized over all 4 adapters: grid_2d, toroidal,
signal_landscape, and default. This ensures protocol compliance
across all implementations.
"""
```

#### Protocol compliance tests (parametrized over all 4 adapters)

1. **`test_cell_shape_returns_valid_enum`**: Assert `cell_shape()` returns a `CellShape` enum member
2. **`test_cell_layout_returns_complete_layout`**: For a 5×5 grid at 500×500 canvas:
   - Assert `CellLayout` has all 25 positions in `cell_centers`
   - Assert all 25 positions in `cell_bounding_boxes`
   - Assert all 25 positions in `cell_polygons`
   - Assert `grid_width == 5`, `grid_height == 5`
   - Assert `canvas_width == 500`, `canvas_height == 500`
3. **`test_cell_layout_centers_within_canvas`**: All centers have `0 <= x <= canvas_width` and `0 <= y <= canvas_height`
4. **`test_cell_layout_bounding_boxes_positive_area`**: All bounding boxes have `w > 0, h > 0`
5. **`test_cell_color_config_has_all_fields`**: Assert all required fields: `obstacle_color`, `empty_color`, `resource_color_min`, `resource_color_max`, `agent_color`, `agent_selected_color`, `selection_border_color`, `grid_line_color`
6. **`test_cell_color_config_rgb_values_valid`**: All color tuples have 3 ints in `[0, 255]`
7. **`test_topology_indicators_returns_list`**: Assert `topology_indicators()` returns a list of `TopologyIndicator`
8. **`test_pixel_to_grid_center_of_cell`**: Compute layout, read center of cell `(2, 2)`, assert `pixel_to_grid(cx, cy, layout)` returns `Position(x=2, y=2)`
9. **`test_pixel_to_grid_out_of_bounds`**: Assert `pixel_to_grid(-10, -10, layout)` returns `None`
10. **`test_world_metadata_sections_returns_list`**: Assert returns a list of `MetadataSection`
11. **`test_format_world_info_returns_string_or_none`**: Assert returns `str | None`

#### Adapter-specific tests

12. **`test_grid2d_no_topology_indicators`**: Assert empty list
13. **`test_grid2d_color_config_green_gradient`**: Assert `resource_color_max` is green `(46, 125, 50)`
14. **`test_grid2d_format_world_info_none`**: Assert `None`
15. **`test_toroidal_four_wrap_edges`**: Assert `topology_indicators()` returns 4 indicators with `indicator_type == "wrap_edge"`
16. **`test_toroidal_wrap_edges_cover_all_sides`**: Assert edges `{"left", "right", "top", "bottom"}` present in indicator data
17. **`test_toroidal_format_world_info`**: Assert contains `"Toroidal"` or `"wrap"`
18. **`test_toroidal_inherits_grid2d_colors`**: Assert color config matches grid_2d color config
19. **`test_signal_landscape_heatmap_colors`**: Assert `resource_color_max` is orange-range, not green
20. **`test_signal_landscape_hotspot_indicators`**: Assert `topology_indicators(world_data)` returns indicators with `indicator_type == "hotspot_center"` when hotspots present
21. **`test_signal_landscape_hotspot_count_matches`**: Assert number of hotspot indicators matches number of hotspots in `world_data`
22. **`test_signal_landscape_no_hotspots`**: Assert empty indicators when `world_data["hotspots"]` is `[]`
23. **`test_signal_landscape_metadata_sections`**: Assert `world_metadata_sections()` returns section with "Hotspot" in title
24. **`test_signal_landscape_format_world_info`**: Assert contains "hotspot"
25. **`test_default_adapter_matches_grid2d`**: Assert `DefaultWorldVisualizationAdapter` produces same `CellLayout` and `CellColorConfig` as `Grid2DWorldVisualizationAdapter`

#### Edge cases

26. **`test_cell_layout_1x1_grid`**: Layout for 1×1 grid -- single cell center exists
27. **`test_cell_layout_large_grid`**: Layout for 50×50 grid at 1000×1000 canvas -- all 2500 positions in layout, no crash
28. **`test_cell_layout_non_square_canvas`**: Layout for 5×5 grid at 800×400 canvas -- centers within bounds
29. **`test_pixel_to_grid_on_grid_boundary`**: Click at exact grid boundary (edge of cell 0) -- returns a valid position

### 3. System Adapter Protocol Compliance Tests

**File**: `tests/v02/visualization/test_system_adapter_suite.py` (new)

```python
"""Systematic tests for all system visualization adapters.

Each test is parametrized over all 3 adapters: system_a, system_b,
and null. This ensures protocol compliance across all implementations.
"""
```

#### Protocol compliance tests (parametrized over all 3 adapters)

1. **`test_phase_names_non_empty`**: Assert `phase_names()` returns a non-empty list of strings
2. **`test_phase_names_starts_with_before`**: Assert first phase is `"BEFORE"`
3. **`test_vitality_label_returns_string`**: Assert `vitality_label()` returns a non-empty string
4. **`test_format_vitality_returns_string`**: Assert `format_vitality(0.5, {})` returns a string
5. **`test_build_step_analysis_returns_sections`**: Assert `build_step_analysis()` returns a `list[AnalysisSection]`
6. **`test_build_step_analysis_section_structure`**: Each section has a non-empty `title` and a list of `AnalysisRow`
7. **`test_build_overlays_returns_list`**: Assert `build_overlays()` returns a `list[OverlayData]`
8. **`test_available_overlay_types_returns_list`**: Assert `available_overlay_types()` returns a list of `OverlayTypeDeclaration`
9. **`test_overlay_types_have_unique_keys`**: Assert no duplicate `overlay_key` values

#### System A-specific tests

10. **`test_system_a_three_phases`**: Assert `phase_names() == ["BEFORE", "AFTER_REGEN", "AFTER_ACTION"]`
11. **`test_system_a_vitality_label_energy`**: Assert `"Energy"` in label
12. **`test_system_a_format_vitality_slash_format`**: With `max_energy=5.0`, assert output matches `"X.XX / 5.00"` pattern
13. **`test_system_a_five_analysis_sections`**: Assert exactly 5 sections returned
14. **`test_system_a_analysis_section_titles`**: Assert titles match: Step Overview, Observation, Drive Output, Decision Pipeline, Outcome
15. **`test_system_a_observation_section_rows`**: Assert 5 neighbor rows (current + 4 directions) in observation section
16. **`test_system_a_drive_section_has_activation`**: Assert activation value appears in Drive Output section
17. **`test_system_a_decision_section_has_all_actions`**: Assert all 6 actions appear in Decision Pipeline section
18. **`test_system_a_three_overlay_types`**: Assert 3 overlay declarations: `action_preference`, `drive_contribution`, `consumption_opportunity`
19. **`test_system_a_action_preference_overlay`**: Build overlays, find `action_preference`, assert items with `item_type in {"direction_arrow", "center_dot", "center_ring"}`
20. **`test_system_a_drive_contribution_overlay`**: Assert items with `item_type == "bar_chart"`
21. **`test_system_a_consumption_opportunity_overlay`**: Assert items with `item_type in {"diamond_marker", "neighbor_dot", "x_marker"}`
22. **`test_system_a_arrow_item_has_direction_and_length`**: Assert `direction_arrow` item data has `direction`, `length`, `is_selected` keys
23. **`test_system_a_selected_action_highlighted`**: For `selected_action="up"`, assert the "up" arrow has `is_selected=True`

#### System B-specific tests

24. **`test_system_b_two_phases`**: Assert `phase_names() == ["BEFORE", "AFTER_ACTION"]`
25. **`test_system_b_vitality_label_energy`**: Assert `"Energy"` in label
26. **`test_system_b_five_analysis_sections`**: Assert 5 sections: Step Overview, Decision Weights, Probabilities, Last Scan, Outcome
27. **`test_system_b_weights_section_six_rows`**: Assert 6 rows in Decision Weights section (one per action)
28. **`test_system_b_scan_section_has_resource_and_count`**: Assert scan section contains total_resource and cell_count
29. **`test_system_b_two_overlay_types`**: Assert `action_weights` and `scan_result`
30. **`test_system_b_action_weights_overlay_items`**: Assert `direction_arrow` items for 4 directional actions
31. **`test_system_b_scan_result_overlay`**: Assert `radius_circle` item with `radius_cells` and `label` in data

#### Null adapter tests

32. **`test_null_adapter_two_phases`**: Assert 2 phases
33. **`test_null_adapter_vitality_label`**: Assert `"Vitality"` in label
34. **`test_null_adapter_format_vitality_percent`**: Assert percentage format
35. **`test_null_adapter_no_analysis`**: Assert empty list from `build_step_analysis()`
36. **`test_null_adapter_no_overlays`**: Assert empty list from `build_overlays()`
37. **`test_null_adapter_no_overlay_types`**: Assert empty list from `available_overlay_types()`

#### Edge cases

38. **`test_system_a_empty_system_data`**: `system_data = {}` -- adapter doesn't crash, returns valid (possibly empty) sections
39. **`test_system_b_empty_system_data`**: Same for System B
40. **`test_system_a_zero_energy`**: Energy at 0.0 -- vitality formats correctly
41. **`test_system_b_no_last_scan`**: Missing `last_scan` in decision_data -- graceful handling

### 4. Registry Resolution Tests

**File**: `tests/v02/visualization/test_adapter_registry_suite.py` (new)

```python
"""Systematic tests for adapter registration and resolution.

Tests both positive resolution (registered adapters) and fallback
behavior (unknown world/system types).
"""
```

1. **`test_all_world_types_registered`**: After importing all adapter modules, assert `resolve_world_adapter()` succeeds for `"grid_2d"`, `"toroidal"`, `"signal_landscape"`
2. **`test_all_system_types_registered`**: Assert `resolve_system_adapter()` succeeds for `"system_a"`, `"system_b"`
3. **`test_unknown_world_type_returns_default`**: `resolve_world_adapter("hexagonal_grid", {})` returns `DefaultWorldVisualizationAdapter`
4. **`test_unknown_system_type_returns_null`**: `resolve_system_adapter("system_c", {})` returns `NullSystemVisualizationAdapter`
5. **`test_world_adapter_correct_types`**: Assert each resolved adapter is the expected class
6. **`test_system_adapter_correct_types`**: Same for system adapters
7. **`test_world_factory_receives_world_config`**: Register a custom factory that captures `world_config`, resolve, assert config was passed
8. **`test_system_factory_receives_system_config`**: Same for system factory

### 5. Combinatorial ViewModelBuilder Tests

**File**: `tests/v02/visualization/test_adapter_combinations.py` (new)

This file verifies that the ViewModelBuilder produces valid output for all (world, system) pairs: 4 world adapters × 3 system adapters = 12 combinations.

```python
"""Combinatorial tests: ViewModelBuilder × all adapter pairs.

Verifies that every (world, system) pair produces a valid
ViewerFrameViewModel without crashes or missing data.
"""
```

#### Setup

A parametrized fixture produces `(world_adapter, system_adapter, world_data, system_data, snapshot)` for each of the 12 combinations:

| World adapter | System adapter | World data | System data |
|---|---|---|---|
| Grid2D | System A | `{}` | System A fixture |
| Grid2D | System B | `{}` | System B fixture |
| Grid2D | Null | `{}` | `{}` |
| Toroidal | System A | `{"topology": "toroidal"}` | System A fixture |
| Toroidal | System B | `{"topology": "toroidal"}` | System B fixture |
| Toroidal | Null | `{"topology": "toroidal"}` | `{}` |
| SignalLandscape | System A | hotspots fixture | System A fixture |
| SignalLandscape | System B | hotspots fixture | System B fixture |
| SignalLandscape | Null | hotspots fixture | `{}` |
| Default | System A | `{}` | System A fixture |
| Default | System B | `{}` | System B fixture |
| Default | Null | `{}` | `{}` |

#### Tests (parametrized over all 12 combinations)

1. **`test_build_frame_no_crash`**: Build a `ViewerFrameViewModel`, assert no exception
2. **`test_frame_has_grid_view_model`**: Assert `frame.grid` is a `GridViewModel` with correct dimensions
3. **`test_frame_has_agent_view_model`**: Assert `frame.agent` is an `AgentViewModel` with correct position
4. **`test_frame_has_status_bar`**: Assert `frame.status_bar` has `phase_name`, `vitality_display`, `vitality_label`
5. **`test_frame_analysis_sections_are_valid`**: All analysis sections have non-empty title, rows are `AnalysisRow`
6. **`test_frame_overlay_data_valid`**: All overlay items have valid `item_type` and `grid_position`
7. **`test_frame_topology_indicators_valid`**: All topology indicators have `indicator_type` string and `position`

#### Cross-adapter consistency

8. **`test_same_world_same_cell_colors`**: For (Grid2D, System A) and (Grid2D, System B), assert `CellColorConfig` is identical
9. **`test_same_system_same_analysis_titles`**: For (Grid2D, System A) and (Toroidal, System A), assert analysis section titles are identical
10. **`test_topology_indicators_world_determined`**: For (Toroidal, System A) and (Toroidal, System B), assert same number of topology indicators
11. **`test_overlay_count_system_determined`**: For (Grid2D, System A) and (Toroidal, System A), assert same number of overlay types

---

## Out of Scope

- Replay infrastructure tests (WP-V.5.2)
- End-to-end validation with actual experiment runs (WP-V.5.3)
- QPainter or widget tests
- Performance benchmarks

---

## Architectural Constraints

### 1. No PySide6 Dependency

All tests in this WP work with structured data only. No `QApplication` fixture is needed.

### 2. Import-Triggered Registration

Tests that verify resolution must import the adapter modules to trigger registration. Use a setup function or fixture that imports `axis.world.grid_2d.visualization`, `axis.world.toroidal.visualization`, `axis.world.signal_landscape.visualization`, `axis.systems.system_a.visualization`, `axis.systems.system_b.visualization`.

### 3. Test Isolation

Tests that modify the registry (registering custom factories) must use the `_clear_registries` fixture from the registry module to avoid cross-test contamination.

---

## Testing Requirements

This WP is itself a test suite. The deliverable is the test files. **All tests must pass.** Total test count:

| File | Tests |
|---|---|
| `test_world_adapter_suite.py` | 29 |
| `test_system_adapter_suite.py` | 41 |
| `test_adapter_registry_suite.py` | 8 |
| `test_adapter_combinations.py` | 11 |
| **Total** | **89** |

All existing tests from prior WPs must continue to pass.

---

## Expected Deliverable

1. `tests/v02/visualization/adapter_fixtures.py` (shared fixture module)
2. `tests/v02/visualization/test_world_adapter_suite.py`
3. `tests/v02/visualization/test_system_adapter_suite.py`
4. `tests/v02/visualization/test_adapter_registry_suite.py`
5. `tests/v02/visualization/test_adapter_combinations.py`
6. Confirmation that all tests pass (new + existing)

---

## Expected File Structure

```
tests/v02/visualization/
    adapter_fixtures.py                  # NEW (shared fixtures)
    test_world_adapter_suite.py          # NEW
    test_system_adapter_suite.py         # NEW
    test_adapter_registry_suite.py       # NEW
    test_adapter_combinations.py         # NEW
    test_grid2d_world_adapter.py         # UNCHANGED (WP-V.2.1)
    test_toroidal_world_adapter.py       # UNCHANGED (WP-V.2.2)
    test_signal_landscape_adapter.py     # UNCHANGED (WP-V.2.3)
    test_system_a_adapter.py             # UNCHANGED (WP-V.2.4)
    test_system_b_adapter.py             # UNCHANGED (WP-V.2.5)
    ...
```

---

## Important Final Constraint

The combinatorial tests (12 adapter pairs) are the most valuable part of this WP. Individual adapter tests already exist from Phase V-2 -- the new value here is verifying that adapters compose correctly through the ViewModelBuilder. A world adapter that works in isolation but crashes when paired with a specific system adapter would only be caught by these combinatorial tests.
