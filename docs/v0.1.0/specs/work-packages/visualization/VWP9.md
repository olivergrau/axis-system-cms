# VWP9 — Debug Overlay Mode

## Context

The Visualization Architecture (Section 14) specifies a Debug Overlay Mode that renders
internal decision-making signals directly on top of the grid. This was never assigned to
a work package and has zero implementation. VWP9 fills this gap.

The overlay system lets users understand *why* the agent chose an action by visualizing
probabilities, drive scores, and consumption opportunities directly on the grid cells.

## Overlay Types (Baseline)

Three overlays for VWP9 (architecture allows easy addition of more later):

1. **Action Preference** — directional arrows from the agent cell, sized/colored by probability
2. **Drive Contribution** — mini bar chart on agent cell showing per-action hunger drive scores
3. **Consumption Opportunity** — diamond on agent cell for local resource; circles on neighbors

*Value Function overlay excluded — this system has no value function, only drive-based scoring.*

## Files to Create

### `src/axis_system_a/visualization/debug_overlay_models.py`
All overlay data models (frozen Pydantic):
- `DebugOverlayType` enum (3 members)
- `DebugOverlayConfig` — master + per-type booleans (all default False)
- `ActionPreferenceOverlay` — agent_row/col, probabilities(6), admissibility_mask(6), selected_action_index
- `DriveContributionOverlay` — agent_row/col, activation, action_contributions(6)
- `ConsumptionOpportunityOverlay` — agent_row/col, current_resource, neighbor_resources(4), neighbor_traversable(4)
- `DebugOverlayViewModel` — composite: config + optional overlay per type

### `src/axis_system_a/visualization/ui/debug_overlay_panel.py`
Checkbox toggle panel (QWidget, max height 35px):
- Master "Debug Overlays" checkbox controls enable of 3 sub-checkboxes
- Signals: `master_toggled(bool)`, `action_preference_toggled(bool)`, `drive_contribution_toggled(bool)`, `consumption_opportunity_toggled(bool)`
- Sub-checkboxes disabled when master is off

### Test files (4 new)
- `tests/visualization/test_debug_overlay_models.py` — model construction, frozen, field completeness
- `tests/visualization/test_debug_overlay_builder.py` — builder projection from StepResult data
- `tests/visualization/test_debug_overlay_transitions.py` — toggle/set pure transitions
- `tests/visualization/test_debug_overlay_panel.py` — panel construction, signals, master toggle behavior

## Files to Modify

### `src/axis_system_a/visualization/viewer_state.py`
- Add field: `debug_overlay_config: DebugOverlayConfig = DebugOverlayConfig()`
- Import `DebugOverlayConfig` from `debug_overlay_models`
- No changes to validator or `create_initial_state` (field has default)

### `src/axis_system_a/visualization/viewer_state_transitions.py`
- Add `toggle_debug_overlay(state) -> ViewerState` — flips master flag
- Add `set_overlay_type_enabled(state, field_name, enabled) -> ViewerState` — sets one overlay boolean

### `src/axis_system_a/visualization/view_models.py`
- Add field to `ViewerFrameViewModel`: `debug_overlay: DebugOverlayViewModel | None = None`
- None default preserves backward compatibility

### `src/axis_system_a/visualization/view_model_builder.py`
- Add `_build_debug_overlay(self, state, snapshot) -> DebugOverlayViewModel | None`
- Returns None if master disabled; otherwise projects from `state.episode_handle.episode_result.steps[step_index]`
- Data sources: `step.decision_result.probabilities`, `.admissibility_mask`, `step.drive_output.activation`, `.action_contributions`, `step.observation`
- Call it in `build()`, pass result to `ViewerFrameViewModel` constructor

### `src/axis_system_a/visualization/ui/grid_widget.py`
- Add `_overlay: DebugOverlayViewModel | None = None` field
- Extend `set_frame` signature: add `overlay: DebugOverlayViewModel | None = None` (backward compatible)
- Add `_draw_overlays(painter, cell_w, cell_h)` dispatcher called between grid lines and selection
- Add `_draw_overlay_action_preference(painter, cell_w, cell_h)` — arrows from agent cell
- Add `_draw_overlay_drive_contribution(painter, cell_w, cell_h)` — bar chart on agent cell
- Add `_draw_overlay_consumption_opportunity(painter, cell_w, cell_h)` — diamond + neighbor circles
- Updated paintEvent z-order: cells → grid lines → **overlays** → selection → agent

### `src/axis_system_a/visualization/ui/main_window.py`
- Add `DebugOverlayPanel` between ReplayControlsPanel and StatusPanel in layout
- Expose `debug_overlay_panel` property
- Update `set_frame` to pass `frame.debug_overlay` to grid widget

### `src/axis_system_a/visualization/ui/session_controller.py`
- Add `set_debug_overlay_master(enabled: bool)` — toggles master via pure transition
- Add `set_overlay_enabled(field_name: str, enabled: bool)` — sets one overlay via pure transition

### `src/axis_system_a/visualization/ui/app.py`
- Wire overlay panel signals to controller in `launch_interactive_session`

### `src/axis_system_a/visualization/launch.py`
- Wire overlay panel signals to controller in `launch_visualization_from_cli` (same pattern as app.py)

### Existing tests to update
- `tests/visualization/test_view_models.py` — add `"debug_overlay"` to expected field set
- `tests/visualization/test_ui_construction.py` — verify panel exists in window
- `tests/visualization/test_session_controller.py` — test overlay toggle methods

## Rendering Details

**Action Preference**: For each of 4 movement actions (UP/DOWN/LEFT/RIGHT) where admissible
and prob > 0.01, draw an arrow from agent cell center toward neighbor. Arrow length and opacity
scale with probability. The actually-selected action drawn in cyan; others in semi-transparent
orange. CONSUME shown as filled dot, STAY as ring.

**Drive Contribution**: Semi-transparent dark backdrop on agent cell. 6 horizontal bars (U/D/L/R/C/S)
— green rightward for positive, red leftward for negative. Normalized to max absolute value.

**Consumption Opportunity**: Yellow diamond on agent cell if resource > 0. Green circles on
traversable neighbors with resource > 0 (opacity = resource level). Red X on non-traversable neighbors.

## Implementation Order

1. Create `debug_overlay_models.py` + tests → run tests
2. Extend `viewer_state.py` (add field) → verify existing tests pass
3. Add transitions to `viewer_state_transitions.py` + tests → run tests
4. Extend `view_models.py` (add field) + update test → run tests
5. Extend `view_model_builder.py` (projection) + tests → run tests
6. Create `debug_overlay_panel.py` + tests → run tests
7. Extend `grid_widget.py` (rendering) → run tests
8. Extend `main_window.py` (layout + routing) + update tests → run tests
9. Extend `session_controller.py` (toggle methods) + update tests → run tests
10. Extend `app.py` + `launch.py` (signal wiring) → run full suite

## Verification

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python -m pytest tests/ -v --tb=short
```

All 1097+ existing tests must continue to pass. New tests should add ~50-60 tests.
Manual verification: launch visualizer, check "Debug Overlays" checkbox, enable sub-overlays,
step through episode and confirm arrows/bars/indicators update per step.
