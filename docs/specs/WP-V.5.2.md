# WP-V.5.2 Implementation Brief -- Replay Infrastructure Test Suite

## Context

Phase V-3 implemented the replay infrastructure: error types, replay models, validation, replay access, snapshot resolver, viewer state, state transitions, playback controller, view models, and the ViewModelBuilder. Each WP included focused tests for the module being built. This WP provides a **cross-cutting** test suite that exercises the replay pipeline as an integrated system: data flows from replay access through snapshot resolution, state transitions, and playback control into view model construction.

The Phase V-3 per-WP tests (e.g., `test_snapshot_resolver.py`) validated each module in isolation with mocked dependencies. This suite tests the modules wired together: a snapshot resolver consuming real replay models, a playback controller advancing through real state transitions, and a ViewModelBuilder consuming resolved snapshots through real adapters.

### Predecessor State (After Phase V-4)

```
src/axis/visualization/
    __init__.py
    types.py
    protocols.py
    registry.py
    errors.py                            # PhaseNotAvailableError, etc.
    replay_models.py                     # ReplayStepDescriptor, ReplayEpisodeHandle, etc.
    replay_validation.py                 # validate_episode_for_replay()
    replay_access.py                     # ReplayAccessService
    snapshot_models.py                   # ReplayCoordinate, ReplaySnapshot
    snapshot_resolver.py                 # SnapshotResolver
    viewer_state.py                      # ViewerState, OverlayConfig, create_initial_state()
    viewer_state_transitions.py          # next_step, previous_step, set_phase, etc.
    playback_controller.py               # PlaybackController
    view_models.py                       # ViewerFrameViewModel, GridViewModel, etc.
    view_model_builder.py                # ViewModelBuilder
    adapters/
        default_world.py
        null_system.py
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
```

### Reference Documents

- `docs/architecture/evolution/visualization-architecture.md` -- Sections 3, 9, 13 (Data flow, replay contract, snapshot resolver)
- `docs/architecture/evolution/visualization-architecture-roadmap.md` -- WP-V.5.2
- Individual infrastructure WP specs: WP-V.3.1 through WP-V.3.4

---

## Objective

Provide comprehensive, cross-cutting tests for the replay infrastructure: snapshot resolution with variable phase counts, playback controller boundary conditions, viewer state transitions (valid and invalid), replay validation edge cases, and the OverlayRenderer dispatch with controlled `CellLayout` geometries.

---

## Scope

### 1. Replay Pipeline Fixtures

**File**: `tests/visualization/replay_fixtures.py` (new)

Shared fixtures for constructing replay data structures without depending on a real experiment repository.

```python
"""Shared fixtures for replay infrastructure tests.

Provides factory functions for BaseEpisodeTrace, BaseStepTrace,
ReplayEpisodeHandle, and related structures with configurable
phase counts and step data.
"""

from __future__ import annotations

from typing import Any

from axis.sdk.snapshot import CellView, Position, WorldSnapshot
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace


def make_step_trace(
    timestep: int = 0,
    action: str = "up",
    world_before: WorldSnapshot | None = None,
    world_after: WorldSnapshot | None = None,
    intermediate_snapshots: dict[str, WorldSnapshot] | None = None,
    vitality_before: float = 1.0,
    vitality_after: float = 0.9,
    agent_position_before: tuple[int, int] = (2, 2),
    agent_position_after: tuple[int, int] = (2, 1),
    system_data: dict[str, Any] | None = None,
    world_data: dict[str, Any] | None = None,
) -> BaseStepTrace:
    """Create a BaseStepTrace with configurable fields."""
    ...


def make_episode_trace(
    system_type: str = "system_a",
    world_type: str = "grid_2d",
    world_config: dict[str, Any] | None = None,
    num_steps: int = 5,
    num_phases: int = 3,
    grid_width: int = 5,
    grid_height: int = 5,
) -> BaseEpisodeTrace:
    """Create a BaseEpisodeTrace with the specified number of steps.

    Generates consistent world snapshots and step data. If num_phases
    is 3, each step has world_before, one intermediate snapshot
    ("AFTER_REGEN"), and world_after. If 2, only world_before and
    world_after.
    """
    ...


def make_episode_handle(
    episode_trace: BaseEpisodeTrace | None = None,
    **kwargs,
) -> "ReplayEpisodeHandle":
    """Create a ReplayEpisodeHandle wrapping an episode trace."""
    ...
```

### 2. Snapshot Resolver Integration Tests

**File**: `tests/visualization/test_snapshot_resolver_suite.py` (new)

Tests the snapshot resolver with realistic episode traces that have varying phase counts.

#### 2-phase resolution (System B-style)

1. **`test_resolve_2_phase_step_before`**: Resolve `ReplayCoordinate(step_index=0, phase_index=0)` on a 2-phase episode, assert snapshot uses `world_before`
2. **`test_resolve_2_phase_step_after`**: Resolve `phase_index=1`, assert snapshot uses `world_after`
3. **`test_resolve_2_phase_vitality_before`**: Assert `snapshot.vitality == step.vitality_before`
4. **`test_resolve_2_phase_vitality_after`**: Assert `snapshot.vitality == step.vitality_after`
5. **`test_resolve_2_phase_action`**: Assert `snapshot.action == step.action`
6. **`test_resolve_2_phase_phase_name`**: Assert `snapshot.phase_name` matches the appropriate phase name from the resolver's phase list

#### 3-phase resolution (System A-style)

7. **`test_resolve_3_phase_before`**: `phase_index=0` → `world_before`
8. **`test_resolve_3_phase_intermediate`**: `phase_index=1` → `intermediate_snapshots["AFTER_REGEN"]`
9. **`test_resolve_3_phase_after`**: `phase_index=2` → `world_after`
10. **`test_resolve_3_phase_vitality_interpolation`**: Phase 1 (intermediate) uses appropriate vitality value
11. **`test_resolve_3_phase_all_snapshots_have_valid_grid`**: All 3 phases produce snapshots with `grid.width == expected`

#### Boundary conditions

12. **`test_resolve_first_step_first_phase`**: `(0, 0)` -- valid
13. **`test_resolve_last_step_last_phase`**: `(num_steps-1, num_phases-1)` -- valid
14. **`test_resolve_out_of_range_step`**: `step_index >= num_steps` -- raises `StepIndexOutOfRangeError`
15. **`test_resolve_out_of_range_phase`**: `phase_index >= num_phases` -- raises `PhaseNotAvailableError`
16. **`test_resolve_negative_step`**: `step_index = -1` -- raises error
17. **`test_resolve_missing_intermediate_snapshot`**: Step has no intermediate but resolver requests `phase_index=1` on 3-phase -- raises `PhaseNotAvailableError`

#### Phase name mapping

18. **`test_phase_names_2_phase`**: Assert resolver returns `["BEFORE", "AFTER_ACTION"]` for System B
19. **`test_phase_names_3_phase`**: Assert resolver returns `["BEFORE", "AFTER_REGEN", "AFTER_ACTION"]` for System A
20. **`test_phase_name_in_snapshot`**: Resolved snapshot's `phase_name` matches the name at the given index

### 3. Playback Controller Integration Tests

**File**: `tests/visualization/test_playback_controller_suite.py` (new)

Tests the playback controller wired to real viewer state and state transitions.

#### Forward traversal

1. **`test_step_forward_increments_phase`**: From `phase_index=0`, step forward → `phase_index=1`
2. **`test_step_forward_wraps_to_next_step`**: From last phase of step N, step forward → step N+1, phase 0
3. **`test_step_forward_at_end_stops`**: At last step, last phase -- step forward returns same state (no crash)
4. **`test_step_forward_3_phase`**: 3-phase episodes: forward cycles through phases 0→1→2→(next step, 0)
5. **`test_step_forward_2_phase`**: 2-phase episodes: forward cycles through phases 0→1→(next step, 0)

#### Backward traversal

6. **`test_step_backward_decrements_phase`**: From `phase_index=1`, step backward → `phase_index=0`
7. **`test_step_backward_wraps_to_previous_step`**: From step N phase 0, backward → step N-1 last phase
8. **`test_step_backward_at_start_stops`**: At step 0, phase 0 -- backward returns same state
9. **`test_step_backward_2_phase`**: 2-phase: backward from step 1 phase 0 → step 0 phase 1

#### Seek

10. **`test_seek_to_step`**: `seek(step_index=3)` → state at step 3, phase 0
11. **`test_seek_to_last_step`**: Seek to last valid step
12. **`test_seek_beyond_bounds_clamps`**: Seek to `step_index=999` on 5-step episode -- clamps or raises

#### Speed and playback mode

13. **`test_set_playback_mode_play`**: Set to play mode, assert state reflects it
14. **`test_set_playback_mode_pause`**: Set to pause
15. **`test_auto_advance_increments`**: After timer tick in play mode, coordinate advances

#### Full traversal

16. **`test_full_forward_traversal_3_phase`**: Start at (0, 0), step forward repeatedly, assert visits all `num_steps * 3` coordinates, ends at `(num_steps-1, 2)`
17. **`test_full_forward_traversal_2_phase`**: Same with 2 phases, visits `num_steps * 2` coordinates
18. **`test_round_trip`**: Forward to end, then backward to start, assert returns to `(0, 0)`

### 4. Viewer State Transition Tests

**File**: `tests/visualization/test_viewer_state_suite.py` (new)

Tests all viewer state transitions as pure functions.

#### Phase transitions

1. **`test_set_phase_valid`**: `set_phase(state, 1)` → `phase_index == 1`
2. **`test_set_phase_out_of_range`**: `set_phase(state, 5)` on 3-phase state -- raises or clamps
3. **`test_set_phase_preserves_step`**: Phase change doesn't affect `step_index`

#### Step transitions

4. **`test_next_step_increments`**: `next_step(state)` increments `step_index` and resets `phase_index` to 0
5. **`test_previous_step_decrements`**: `previous_step(state)` decrements
6. **`test_next_step_at_boundary`**: Already at last step -- no change
7. **`test_previous_step_at_boundary`**: Already at step 0 -- no change

#### Selection transitions

8. **`test_select_cell`**: `select_cell(state, 2, 3)` → selection at (2, 3)
9. **`test_select_agent`**: `select_agent(state)` → agent selected
10. **`test_clear_selection`**: `clear_selection(state)` → no selection
11. **`test_select_cell_clears_agent`**: Selecting a cell clears agent selection

#### Overlay transitions

12. **`test_toggle_overlay_master_on`**: `toggle_overlay_master(state)` -- flips master enabled
13. **`test_toggle_overlay_master_off`**: Second toggle -- master disabled
14. **`test_set_overlay_enabled`**: `set_overlay_enabled(state, "action_preference", True)` → overlay in `enabled_overlays`
15. **`test_set_overlay_disabled`**: `set_overlay_enabled(state, "action_preference", False)` → overlay removed
16. **`test_set_overlay_preserves_others`**: Enabling one overlay doesn't affect other enabled overlays

#### State creation

17. **`test_create_initial_state_3_phase`**: `create_initial_state(num_phases=3)` → phase_index=0, step_index=0, num_phases=3
18. **`test_create_initial_state_2_phase`**: Same with 2 phases
19. **`test_initial_state_overlays_disabled`**: Initial state has `master_enabled=False`, empty `enabled_overlays`

### 5. Replay Validation Tests

**File**: `tests/visualization/test_replay_validation_suite.py` (new)

Tests replay validation with various edge cases.

1. **`test_valid_episode_passes`**: Well-formed 5-step episode passes validation
2. **`test_empty_episode_fails`**: Episode with 0 steps fails validation
3. **`test_missing_world_before_fails`**: Step with `world_before=None` fails
4. **`test_missing_world_after_fails`**: Step with `world_after=None` fails
5. **`test_mismatched_grid_dimensions_fails`**: `world_before` has 5×5, `world_after` has 3×3 -- fails
6. **`test_zero_width_world_fails`**: `WorldSnapshot` with `width=0` -- fails
7. **`test_zero_height_world_fails`**: `WorldSnapshot` with `height=0` -- fails
8. **`test_negative_vitality_passes`**: Vitality can be negative (not an error)
9. **`test_missing_vitality_fails`**: `vitality_before=None` or `vitality_after=None` -- fails
10. **`test_valid_2_phase_episode`**: 2-phase episode (no intermediates) passes
11. **`test_valid_3_phase_episode`**: 3-phase episode (with intermediate) passes
12. **`test_intermediate_snapshot_wrong_dimensions`**: Intermediate has different dimensions -- fails
13. **`test_single_step_episode_valid`**: Episode with exactly 1 step -- passes
14. **`test_large_episode_valid`**: Episode with 100 steps -- passes (performance sanity)

### 6. Overlay Rendering Dispatch Tests

**File**: `tests/visualization/test_overlay_rendering_suite.py` (new)

Tests the OverlayRenderer dispatch logic with controlled `CellLayout` data. These tests use mock QPainter or QPixmap to verify rendering doesn't crash. No pixel-level comparison.

#### Dispatch completeness

1. **`test_dispatch_all_8_item_types`**: Create 8 items (one per known type), render all, assert no crash
2. **`test_dispatch_unknown_type_skipped`**: Item with `item_type="future_type"` -- no crash, silently skipped
3. **`test_dispatch_mixed_known_and_unknown`**: Mix of known and unknown items -- known items rendered, unknown skipped

#### Per-item rendering (smoke tests with QPixmap)

4. **`test_render_direction_arrow_all_directions`**: 4 items for up/down/left/right -- all render without crash
5. **`test_render_center_dot_varying_radius`**: Radii 0.0, 0.5, 1.0 -- no crash
6. **`test_render_center_ring_selected_and_unselected`**: `is_selected=True` and `False` -- both render
7. **`test_render_bar_chart_varying_values`**: 0, 3, 6 values -- no crash
8. **`test_render_bar_chart_empty_values`**: Empty values list -- no crash (graceful skip)
9. **`test_render_diamond_marker_varying_opacity`**: Opacity 0.0, 0.5, 1.0 -- all render
10. **`test_render_neighbor_dot`**: Standard neighbor dot -- renders
11. **`test_render_x_marker`**: Standard x marker -- renders
12. **`test_render_radius_circle_with_label`**: `radius_circle` with label text -- renders
13. **`test_render_radius_circle_without_label`**: No label -- renders

#### CellLayout edge cases

14. **`test_render_item_missing_position`**: Item at grid position `(99, 99)` not in layout -- silently skipped
15. **`test_render_item_at_origin`**: Item at `(0, 0)` -- renders at correct center
16. **`test_render_on_1x1_layout`**: Single-cell layout -- items render
17. **`test_render_empty_overlay_list`**: Empty overlay tuple -- no crash

---

## Out of Scope

- Adapter tests (WP-V.5.1)
- End-to-end tests with real experiments (WP-V.5.3)
- Widget interaction tests (clicking, signal emission)
- Visual pixel comparison or screenshot tests

---

## Architectural Constraints

### 1. PySide6 Dependency for Overlay Tests

The overlay rendering tests (Section 6) require a `QApplication` instance and `QPixmap` for the QPainter. These tests should be marked with `@pytest.mark.skipif` if PySide6 is not available, or use a `pytest-qt` fixture. All other tests in this WP are pure Python with no PySide6 dependency.

### 2. No External I/O

All tests construct data in-memory. No file system access, no experiment repository loading, no network calls.

### 3. Deterministic Fixtures

All fixture factories produce deterministic data. No randomness. This ensures test reproducibility.

### 4. Phase Count Parametrization

Where applicable, tests are parametrized over `num_phases=2` and `num_phases=3` to cover both System A and System B lifecycle patterns.

---

## Testing Requirements

This WP is itself a test suite. Total test count:

| File | Tests |
|---|---|
| `test_snapshot_resolver_suite.py` | 20 |
| `test_playback_controller_suite.py` | 18 |
| `test_viewer_state_suite.py` | 19 |
| `test_replay_validation_suite.py` | 14 |
| `test_overlay_rendering_suite.py` | 17 |
| **Total** | **88** |

All existing tests from prior WPs must continue to pass.

---

## Expected Deliverable

1. `tests/visualization/replay_fixtures.py` (shared fixture module)
2. `tests/visualization/test_snapshot_resolver_suite.py`
3. `tests/visualization/test_playback_controller_suite.py`
4. `tests/visualization/test_viewer_state_suite.py`
5. `tests/visualization/test_replay_validation_suite.py`
6. `tests/visualization/test_overlay_rendering_suite.py`
7. Confirmation that all tests pass (new + existing)

---

## Expected File Structure

```
tests/visualization/
    replay_fixtures.py                   # NEW (shared fixtures)
    test_snapshot_resolver_suite.py       # NEW
    test_playback_controller_suite.py     # NEW
    test_viewer_state_suite.py           # NEW
    test_replay_validation_suite.py      # NEW
    test_overlay_rendering_suite.py      # NEW
    test_snapshot_resolver.py            # UNCHANGED (WP-V.3.2)
    test_viewer_state.py                 # UNCHANGED (WP-V.3.3)
    test_playback_controller.py          # UNCHANGED (WP-V.3.3)
    test_view_model_builder.py           # UNCHANGED (WP-V.3.4)
    test_overlay_renderer.py             # UNCHANGED (WP-V.4.2)
    ...
```

---

## Important Final Constraint

The per-module tests from Phase V-3 remain. This suite adds **cross-module integration** and **boundary condition coverage**. The key difference: Phase V-3 tests mock their dependencies; these tests wire real modules together. A bug at an integration boundary (e.g., the snapshot resolver returning data that the ViewModelBuilder misinterprets) would only be caught here.
