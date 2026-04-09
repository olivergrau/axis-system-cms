# WP-V.5.3 Implementation Brief -- End-to-End Validation

## Context

WP-V.5.1 tests adapters in isolation and combination. WP-V.5.2 tests the replay infrastructure with in-memory fixtures. This WP closes the loop: it runs short experiments, persists them with the framework runner, loads them through the visualization pipeline, and verifies the output matches expectations. These are true **end-to-end** tests that exercise the full stack from experiment execution to view model construction.

Additionally, this WP includes a **visual regression baseline** for System A: the v0.1.0 viewer produced specific analysis content for known episode data. The System A visualization adapter must reproduce identical analysis text for the same input. This guards against behavior regression during the migration.

### Predecessor State (After WP-V.5.1 and WP-V.5.2)

The full visualization system is implemented and unit-tested:

```
src/axis/visualization/                  # Base layer (Phase V-3, V-4)
    types.py, protocols.py, registry.py
    errors.py, replay_models.py, replay_validation.py, replay_access.py
    snapshot_models.py, snapshot_resolver.py
    viewer_state.py, viewer_state_transitions.py, playback_controller.py
    view_models.py, view_model_builder.py
    adapters/
        default_world.py, null_system.py
    ui/
        canvas_widget.py, overlay_renderer.py
        status_panel.py, step_analysis_panel.py, detail_panel.py
        replay_controls_panel.py, overlay_panel.py
        main_window.py, session_controller.py, app.py
    launch.py

src/axis/world/
    grid_2d/visualization.py             # Grid2D adapter (WP-V.2.1)
    toroidal/visualization.py            # Toroidal adapter (WP-V.2.2)
    signal_landscape/visualization.py    # Signal landscape adapter (WP-V.2.3)

src/axis/systems/
    system_a/visualization.py            # System A adapter (WP-V.2.4)
    system_b/visualization.py            # System B adapter (WP-V.2.5)

tests/v02/visualization/
    adapter_fixtures.py                  # WP-V.5.1
    replay_fixtures.py                   # WP-V.5.2
    test_world_adapter_suite.py          # WP-V.5.1
    test_system_adapter_suite.py         # WP-V.5.1
    test_adapter_registry_suite.py       # WP-V.5.1
    test_adapter_combinations.py         # WP-V.5.1
    test_snapshot_resolver_suite.py      # WP-V.5.2
    test_playback_controller_suite.py    # WP-V.5.2
    test_viewer_state_suite.py           # WP-V.5.2
    test_replay_validation_suite.py      # WP-V.5.2
    test_overlay_rendering_suite.py      # WP-V.5.2
    ...
```

### Reference Documents

- `docs/v0.2.0/architecture/evolution/visualization-architecture.md` -- Sections 3, 12, 14
- `docs/v0.2.0/architecture/evolution/visualization-architecture-roadmap.md` -- WP-V.5.3
- WP-V.4.4 (launch.py, CLI entry point)

---

## Objective

Validate the complete visualization pipeline end-to-end: run experiments → persist → load → validate → resolve snapshots → build view models → verify content. Include a System A regression test and a CLI smoke test.

---

## Scope

### 1. E2E Test Helpers

**File**: `tests/v02/visualization/e2e_helpers.py` (new)

Utilities for running short experiments and loading them back through the visualization pipeline.

```python
"""End-to-end test helpers.

Provides functions to run short experiments, persist them, and
load them back through the visualization pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from axis.framework.persistence import ExperimentRepository
from axis.visualization.replay_access import ReplayAccessService
from axis.visualization.replay_validation import validate_episode_for_replay
from axis.visualization.snapshot_resolver import SnapshotResolver
from axis.visualization.view_model_builder import ViewModelBuilder
from axis.visualization.viewer_state import create_initial_state
from axis.visualization.view_models import ViewerFrameViewModel


def run_and_persist_experiment(
    tmp_path: Path,
    system_type: str,
    world_type: str,
    num_episodes: int = 1,
    max_steps: int = 10,
    grid_width: int = 5,
    grid_height: int = 5,
) -> Path:
    """Run a short experiment and persist it to tmp_path.

    Returns the experiment directory path.
    """
    ...


def load_episode_through_pipeline(
    experiment_dir: Path,
    episode_index: int = 0,
    run_index: int = 0,
) -> tuple[ViewerFrameViewModel, dict[str, Any]]:
    """Load an episode and produce a ViewerFrameViewModel.

    Returns (frame_view_model, pipeline_metadata) where metadata
    includes resolved adapters, phase names, and overlay declarations
    for further assertions.
    """
    ...
```

### 2. System A on Grid2D E2E

**File**: `tests/v02/visualization/test_e2e_system_a_grid2d.py` (new)

The primary regression target. System A on grid_2d is the baseline that must reproduce v0.1.0 behavior.

1. **`test_run_and_persist`**: Run a 10-step System A experiment on grid_2d, persist, assert episode file exists
2. **`test_load_episode_trace`**: Load episode trace via `ReplayAccessService`, assert `system_type == "system_a"`, `world_type == "grid_2d"`
3. **`test_validate_episode`**: Validate loaded episode, assert no errors
4. **`test_resolve_snapshot_step_0_before`**: Resolve snapshot at (0, 0), assert valid grid with correct dimensions
5. **`test_resolve_snapshot_step_0_after_regen`**: Resolve at (0, 1), assert valid (3-phase with intermediate)
6. **`test_resolve_snapshot_step_0_after_action`**: Resolve at (0, 2), assert valid
7. **`test_build_frame_step_0`**: Build ViewerFrameViewModel for step 0, phase 0, assert non-null grid, agent, status
8. **`test_frame_grid_dimensions`**: Assert `frame.grid.width == 5`, `frame.grid.height == 5`
9. **`test_frame_agent_position`**: Assert agent position matches snapshot
10. **`test_frame_status_phase_name`**: Assert `frame.status.phase_name == "BEFORE"` for phase 0
11. **`test_frame_status_vitality_label`**: Assert `"Energy"` in vitality label
12. **`test_frame_status_vitality_display`**: Assert slash format `"X.XX / Y.YY"`
13. **`test_frame_five_analysis_sections`**: Assert 5 analysis sections
14. **`test_frame_analysis_titles_match_v01`**: Assert section titles: "Step Overview", "Observation", "Drive Output", "Decision Pipeline", "Outcome"
15. **`test_frame_observation_section_content`**: Assert observation section contains rows for current cell and 4 neighbors
16. **`test_frame_decision_section_has_probabilities`**: Assert decision section rows contain probability values for all 6 actions
17. **`test_frame_topology_indicators_empty`**: Grid2D has no topology indicators
18. **`test_frame_overlay_data_present`**: With overlays enabled, assert `action_preference`, `drive_contribution`, `consumption_opportunity` overlays present
19. **`test_overlay_items_have_valid_positions`**: All overlay items have `grid_position` within grid bounds
20. **`test_full_episode_traversal`**: Build frames for all steps × all phases, assert no crash and all frames valid

### 3. System A on Toroidal E2E

**File**: `tests/v02/visualization/test_e2e_system_a_toroidal.py` (new)

Tests the toroidal-specific visual additions atop System A's analysis.

1. **`test_run_and_persist_toroidal`**: Run System A on toroidal world, persist
2. **`test_load_world_type`**: Assert `world_type == "toroidal"` on loaded trace
3. **`test_validate_episode`**: Validation passes
4. **`test_frame_topology_indicators_wrap_edges`**: Assert 4 wrap-edge topology indicators present
5. **`test_frame_wrap_edges_cover_all_sides`**: Assert `{"left", "right", "top", "bottom"}` in indicator data
6. **`test_frame_world_info_toroidal`**: Assert `frame.status.world_info` mentions toroidal/wrap
7. **`test_frame_analysis_sections_same_as_grid2d`**: Same 5 System A sections (world type doesn't affect system analysis)
8. **`test_frame_overlays_same_as_grid2d`**: Same 3 System A overlay types
9. **`test_full_traversal`**: All steps × phases produce valid frames

### 4. System B on Signal Landscape E2E

**File**: `tests/v02/visualization/test_e2e_system_b_signal.py` (new)

Tests the most visually distinct combination: heatmap colors, hotspot markers, and scan-area overlay.

1. **`test_run_and_persist_signal`**: Run System B on signal landscape, persist
2. **`test_load_types`**: Assert `system_type == "system_b"`, `world_type == "signal_landscape"`
3. **`test_validate_episode`**: Validation passes
4. **`test_frame_2_phases`**: Assert status shows 2 phases (System B lifecycle)
5. **`test_frame_hotspot_indicators`**: Assert topology indicators with `indicator_type == "hotspot_center"`
6. **`test_frame_world_info_hotspots`**: Assert `frame.status.world_info` mentions hotspots
7. **`test_frame_world_metadata_sections`**: Assert metadata section with hotspot info in detail panel data
8. **`test_frame_five_analysis_sections`**: Assert 5 System B sections
9. **`test_frame_analysis_titles`**: Assert: "Step Overview", "Decision Weights", "Probabilities", "Last Scan", "Outcome"
10. **`test_frame_scan_result_overlay`**: Assert `radius_circle` item in overlays
11. **`test_frame_action_weights_overlay`**: Assert `direction_arrow` items in overlays
12. **`test_full_traversal`**: All steps × 2 phases produce valid frames

### 4a. System B on Grid2D E2E

**File**: `tests/v02/visualization/test_e2e_system_b_grid2d.py` (new)

Validates that System B works correctly on the baseline grid_2d world.

1. **`test_run_and_persist`**: Run System B on grid_2d, persist
2. **`test_load_types`**: Assert `system_type == "system_b"`, `world_type == "grid_2d"`
3. **`test_validate_episode`**: Validation passes
4. **`test_frame_2_phases`**: Assert 2-phase lifecycle
5. **`test_frame_no_topology_indicators`**: Assert empty topology indicators (grid_2d is bounded)
6. **`test_frame_analysis_titles`**: Assert System B analysis section titles
7. **`test_full_traversal`**: All steps × 2 phases produce valid frames

### 4b. System B on Toroidal E2E

**File**: `tests/v02/visualization/test_e2e_system_b_toroidal.py` (new)

Validates System B on toroidal world -- 2-phase lifecycle with wrap-edge indicators.

1. **`test_run_and_persist`**: Run System B on toroidal, persist
2. **`test_load_types`**: Assert `system_type == "system_b"`, `world_type == "toroidal"`
3. **`test_validate_episode`**: Validation passes
4. **`test_frame_2_phases`**: Assert 2-phase lifecycle
5. **`test_frame_topology_indicators_wrap_edges`**: Assert 4 wrap-edge indicators
6. **`test_frame_analysis_titles`**: Assert System B analysis section titles (world doesn't affect system analysis)
7. **`test_full_traversal`**: All steps × 2 phases produce valid frames

### 4c. System A on Signal Landscape E2E

**File**: `tests/v02/visualization/test_e2e_system_a_signal.py` (new)

Validates System A on signal landscape -- 3-phase lifecycle with heatmap colors and hotspot indicators.

1. **`test_run_and_persist`**: Run System A on signal landscape, persist
2. **`test_load_types`**: Assert `system_type == "system_a"`, `world_type == "signal_landscape"`
3. **`test_validate_episode`**: Validation passes
4. **`test_frame_3_phases`**: Assert 3-phase lifecycle
5. **`test_frame_hotspot_indicators`**: Assert hotspot topology indicators
6. **`test_frame_analysis_titles`**: Assert System A's 5 analysis section titles
7. **`test_frame_overlays`**: Assert 3 System A overlay types
8. **`test_full_traversal`**: All steps × 3 phases produce valid frames

### 5. System A Regression Test

**File**: `tests/v02/visualization/test_system_a_regression.py` (new)

Compares System A adapter output against known reference values to ensure the v0.2.0 adapter reproduces v0.1.0 analysis content exactly.

```python
"""System A visualization regression test.

Verifies that the System A adapter produces identical analysis
content to v0.1.0 for a known, fixed system_data input. This
prevents behavior regression during the v0.1.0 → v0.2.0 migration.
"""
```

1. **`test_observation_section_matches_reference`**: Given a fixed `system_data` dict, assert the Observation section rows match expected strings exactly
2. **`test_drive_section_matches_reference`**: Assert Drive Output section matches expected activation and contribution values
3. **`test_decision_section_matches_reference`**: Assert Decision Pipeline section matches expected probability table
4. **`test_outcome_section_matches_reference`**: Assert Outcome section matches expected moved/consumed/terminated values
5. **`test_vitality_format_matches_reference`**: Assert `format_vitality(3.45, system_data)` with `max_energy=5.0` returns `"3.45 / 5.00"`
6. **`test_overlay_item_count_matches_reference`**: For fixed input, assert same number of overlay items per overlay type as v0.1.0 would produce
7. **`test_direction_arrow_lengths_match_reference`**: Assert arrow `length` values match the expected probabilities from the policy
8. **`test_selected_action_highlighted_correctly`**: For `selected_action="right"`, assert exactly one direction_arrow has `is_selected=True` and it's the "right" direction
9. **`test_consumption_opportunity_diamond_present`**: When current cell has resource > 0, diamond_marker is present
10. **`test_consumption_opportunity_no_diamond_when_empty`**: When current cell resource is 0, no diamond_marker

The reference values in these tests are computed from the v0.1.0 code and hard-coded as expected values. They serve as a frozen contract.

### 6. CLI Smoke Test

**File**: `tests/v02/visualization/test_cli_smoke.py` (new)

Tests the CLI entry point without actually opening a GUI window.

1. **`test_cli_visualize_help`**: Run `axis visualize --help`, assert exit code 0 and help text printed
2. **`test_cli_visualize_missing_experiment`**: Run `axis visualize --experiment nonexistent --run 0 --episode 0`, assert appropriate error message
3. **`test_cli_visualize_loads_episode`**: Run a short experiment, then invoke the visualization pipeline up to adapter resolution (mock the QApplication launch), assert adapters resolved correctly
4. **`test_adapter_module_import`**: Call `_import_adapter_modules()` (from launch.py), assert all world and system adapters registered in the registry
5. **`test_backward_compatibility_no_world_type`**: Load an episode trace that lacks `world_type` field, assert `getattr(episode, "world_type", "grid_2d")` defaults to `"grid_2d"`

---

## Out of Scope

- Pixel-level screenshot comparison (deferred: PySide6 rendering varies across platforms and graphics drivers, making pixel-exact comparison fragile)
- Performance benchmarks
- Multi-episode or multi-run visualization
- Interactive UI testing (mouse clicks, keyboard shortcuts)

---

## Architectural Constraints

### 1. Experiment Runner Dependency

Tests in Sections 2-4 depend on the framework runner to execute short experiments. These tests use `tmp_path` fixtures for isolated persistence. If running an actual experiment is too slow or fragile in CI, they should be marked with `@pytest.mark.slow` and excluded from the fast test suite.

### 2. No GUI Window

No test in this WP opens a PySide6 window. The pipeline is tested up to `ViewerFrameViewModel` construction. Widget rendering is covered by WP-V.4.x unit tests and WP-V.5.2 overlay smoke tests.

### 3. Fixed Reference Data

The regression tests (Section 5) use hard-coded reference values. When the System A adapter intentionally changes its output format (e.g., adding a new analysis row), the reference values must be updated manually. This is by design -- the test catches unintentional changes.

### 4. World Type Configurations

Each E2E test uses a minimal experiment configuration:

| Combination | Grid | Steps | Episodes |
|---|---|---|---|
| System A + grid_2d | 5×5 | 10 | 1 |
| System A + toroidal | 5×5 | 10 | 1 |
| System A + signal_landscape | 8×8 | 10 | 1 |
| System B + grid_2d | 5×5 | 10 | 1 |
| System B + toroidal | 5×5 | 10 | 1 |
| System B + signal_landscape | 8×8 | 10 | 1 |

These are small enough to run quickly but large enough to exercise the pipeline meaningfully.

---

## Testing Requirements

This WP is itself a test suite. Total test count:

| File | Tests |
|---|---|
| `test_e2e_system_a_grid2d.py` | 20 |
| `test_e2e_system_a_toroidal.py` | 9 |
| `test_e2e_system_b_signal.py` | 12 |
| `test_e2e_system_b_grid2d.py` | 7 |
| `test_e2e_system_b_toroidal.py` | 7 |
| `test_e2e_system_a_signal.py` | 8 |
| `test_system_a_regression.py` | 10 |
| `test_cli_smoke.py` | 5 |
| **Total** | **78** |

All existing tests from prior WPs must continue to pass.

---

## Expected Deliverable

1. `tests/v02/visualization/e2e_helpers.py` (shared helper module)
2. `tests/v02/visualization/test_e2e_system_a_grid2d.py`
3. `tests/v02/visualization/test_e2e_system_a_toroidal.py`
4. `tests/v02/visualization/test_e2e_system_a_signal.py`
5. `tests/v02/visualization/test_e2e_system_b_signal.py`
6. `tests/v02/visualization/test_e2e_system_b_grid2d.py`
7. `tests/v02/visualization/test_e2e_system_b_toroidal.py`
8. `tests/v02/visualization/test_system_a_regression.py`
9. `tests/v02/visualization/test_cli_smoke.py`
10. Confirmation that all tests pass (new + existing)

---

## Expected File Structure

```
tests/v02/visualization/
    e2e_helpers.py                       # NEW (shared helpers)
    test_e2e_system_a_grid2d.py          # NEW
    test_e2e_system_a_toroidal.py        # NEW
    test_e2e_system_a_signal.py          # NEW
    test_e2e_system_b_signal.py          # NEW
    test_e2e_system_b_grid2d.py          # NEW
    test_e2e_system_b_toroidal.py        # NEW
    test_system_a_regression.py          # NEW
    test_cli_smoke.py                    # NEW
    adapter_fixtures.py                  # UNCHANGED (WP-V.5.1)
    replay_fixtures.py                   # UNCHANGED (WP-V.5.2)
    test_world_adapter_suite.py          # UNCHANGED (WP-V.5.1)
    test_system_adapter_suite.py         # UNCHANGED (WP-V.5.1)
    ...
```

---

## Important Final Constraint

The end-to-end tests are intentionally **coarse-grained**: they verify that the pipeline produces structurally correct output, not that every pixel is right. The regression tests are the exception -- they verify exact string matches for analysis content. This balance keeps the suite maintainable while catching real regressions. If a future change breaks analysis formatting, the regression test catches it. If a future change breaks the pipeline wiring, the E2E tests catch it.
