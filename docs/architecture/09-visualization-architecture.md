# 9. Visualization Architecture

## Layer Structure

The visualization subsystem follows a strict unidirectional data flow pattern:

```
Repository (filesystem)
      │
      v
ReplayAccessService ──► ReplayEpisodeHandle (validated episode data)
      │
      v
SnapshotResolver ──► ReplaySnapshot (world state at step+phase)
      │
      v
ViewModelBuilder ──► ViewerFrameViewModel (UI-ready projection)
      │
      v
VisualizationMainWindow ──► Child widgets (rendering)
      ▲
      │ (signals: user intent)
      │
VisualizationSessionController (state owner, pure transitions)
```

## Data Access Layer

### ReplayAccessService (`replay_access.py`)

Read-only gateway wrapping `ExperimentRepository`. Provides:
- **Discovery**: `list_experiments()`, `list_runs()`, `list_episode_indices()`
- **Handle construction**: `get_experiment_handle()`, `get_run_handle()`
- **Episode loading**: `load_replay_episode()` -- loads, validates, returns `ReplayEpisodeHandle`

Error handling: wraps `FileNotFoundError`, `ValidationError`, `KeyError` into domain-specific exceptions (`ExperimentNotFoundError`, `RunNotFoundError`, `MalformedArtifactError`).

### Replay Validation (`replay_validation.py`)

`validate_episode_for_replay(episode: EpisodeResult) -> ReplayValidationResult`

Checks (never fails early, collects all violations):
- Non-empty steps
- Unique, monotonic, contiguous timesteps
- Per-step phase availability (validates WorldSnapshot at each phase)
- Agent energy non-negative
- Agent position presence
- Grid dimension consistency across all valid snapshots

### ReplayEpisodeHandle

Frozen model carrying the raw `EpisodeResult` and its `ReplayValidationResult`. This is the validated artifact that all downstream layers consume.

## Snapshot Layer

### ReplayPhase (IntEnum)

Three phases per step: `BEFORE = 0`, `AFTER_REGEN = 1`, `AFTER_ACTION = 2`

### ReplayCoordinate

`(step_index, phase)` -- uniquely identifies every point in the replay timeline.

### SnapshotResolver (`snapshot_resolver.py`)

```python
resolve(episode_handle, step_index, phase) -> ReplaySnapshot
```

Selects the appropriate WorldSnapshot and agent state from the step's `TransitionTrace`:

| Phase | World Snapshot | Agent Position | Agent Energy |
|-------|---------------|----------------|--------------|
| BEFORE | `world_before` | `position_before` | `energy_before` |
| AFTER_REGEN | `world_after_regen` | `position_before` | `energy_before` |
| AFTER_ACTION | `world_after_action` | `position_after` | `energy_after` |

## State Management

### ViewerState (`viewer_state.py`)

Single source of truth for all UI state. Frozen Pydantic model.

| Field | Type | Purpose |
|-------|------|---------|
| `episode_handle` | `ReplayEpisodeHandle` | The loaded episode |
| `coordinate` | `ReplayCoordinate` | Current position in replay |
| `playback_mode` | `PlaybackMode` | `STOPPED`, `PLAYING`, `PAUSED` |
| `selected_cell` | `tuple[int,int] \| None` | Currently selected grid cell |
| `selected_agent` | `bool` | Whether agent is selected |
| `debug_overlay_config` | `DebugOverlayConfig` | Overlay toggle state |

Model validator ensures `step_index` in bounds and `selected_cell` within grid dimensions.

### State Transitions (`viewer_state_transitions.py`)

All transitions are pure functions: `(ViewerState, params) -> ViewerState` via `model_copy(update={...})`.

| Transition | Effect |
|------------|--------|
| `next_step(state)` | step_index + 1, same phase |
| `previous_step(state)` | step_index - 1, same phase |
| `set_phase(state, phase)` | Change phase, same step |
| `seek(state, coordinate)` | Jump to arbitrary coordinate |
| `select_cell(state, row, col)` | Set selected_cell, clear agent |
| `select_agent(state)` | Set selected_agent, clear cell |
| `clear_selection(state)` | Clear both |
| `set_playback_mode(state, mode)` | Change playback mode |
| `toggle_debug_overlay(state)` | Flip master_enabled |
| `set_overlay_type_enabled(state, field, enabled)` | Set one overlay toggle |

### PlaybackController (`playback_controller.py`)

Phase-aware navigation. Traversal order within a step:

```
BEFORE → AFTER_REGEN → AFTER_ACTION → (next step) BEFORE → ...
```

Key methods:
- `step_forward(state)` / `step_backward(state)` -- advance/retreat one phase unit
- `tick(state)` -- auto-play advance: calls `step_forward`, auto-stops at final position
- `seek_to_step(state, step_index)` -- jump to step (phase = BEFORE)

Boundary helpers: `is_at_initial()`, `is_at_final()`, `get_initial_coordinate()`, `get_final_coordinate()`.

## View Model Layer

### ViewModelBuilder (`view_model_builder.py`)

Stateless projection: `build(state: ViewerState) -> ViewerFrameViewModel`

1. Resolves `ReplaySnapshot` via `SnapshotResolver`
2. Projects grid cells (flat tuple, row-major) with `is_obstacle`, `is_agent_here`, `is_selected`
3. Projects agent position, energy, selection state
4. Projects status bar (step index, total, phase, mode, boundary flags)
5. Projects selection model
6. Projects action context (action, moved, consumed, etc.)
7. Builds debug overlay (only if master_enabled) from DecisionTrace, HungerDriveOutput, Observation
8. Builds step analysis (always) -- full decision pipeline readout

**Coordinate translation**: Domain `Position(x, y)` maps to `row = y, col = x`. The builder is the single translation point.

### ViewerFrameViewModel

Top-level composite carrying all data needed to render one frame:

```
ViewerFrameViewModel
├── coordinate: ReplayCoordinate
├── grid: GridViewModel (width, height, flat cells tuple)
├── agent: AgentViewModel (row, col, energy, is_selected)
├── status: StatusBarViewModel (step, phase, mode, energy, boundaries)
├── selection: SelectionViewModel (type, cell coords, agent flag)
├── action_context: ActionContextViewModel (action, moved, consumed, ...)
├── debug_overlay: DebugOverlayViewModel | None
│   ├── action_preference: ActionPreferenceOverlay | None
│   ├── drive_contribution: DriveContributionOverlay | None
│   └── consumption_opportunity: ConsumptionOpportunityOverlay | None
└── step_analysis: StepAnalysisViewModel | None
    (timestep, energy, observation, drive, decision pipeline, outcome)
```

## UI Layer (PySide6)

### Widget Hierarchy

```
VisualizationMainWindow (QMainWindow)
├── ReplayControlsPanel         [buttons: ◄ ▶ ⏸ ⏹ ►] [phase combo]
├── DebugOverlayPanel           [master checkbox] [3 sub-checkboxes] [legend]
├── StatusPanel                 [step] [phase] [mode] [energy] [boundary]
└── QSplitter (horizontal)
    ├── StepAnalysisPanel       [scrollable monospace text, 250px]
    ├── GridWidget              [custom paint, 700px]
    └── DetailPanel             [cell/agent details, 250px]
```

### GridWidget (`grid_widget.py`)

Custom `QWidget` with `paintEvent` rendering:

1. **Cell backgrounds**: Black (obstacle), gray (empty), green gradient (resource)
2. **Grid lines**: Gray
3. **Selection**: Orange 3px border on selected cell
4. **Agent**: Blue circle (darker when selected)
5. **Overlays** (when enabled):
   - Action preference: Direction arrows (cyan=selected, orange=candidates)
   - Drive contribution: Bar chart with labels
   - Consumption opportunity: Diamond/circle indicators

Mouse interaction: `mousePressEvent` converts pixel to `(row, col)`, emits `cell_clicked` or `agent_clicked`.

### StepAnalysisPanel (`step_analysis_panel.py`)

Comprehensive numeric readout, always visible when step data is available (not gated by overlay checkboxes). Five sections:

- **Step Overview**: Timestep, energy before/after, delta
- **Observation**: Current resource, neighbor table (direction, resource, traversable/blocked)
- **Drive Output**: Activation, per-action contribution table
- **Decision Pipeline**: Temperature, selection mode, selected action, per-action table (Raw, Adm, Eff, Prob)
- **Outcome**: Moved, position change, consumed, resource eaten, terminated

### Signal Wiring

Wiring is performed in the bridge functions (`app.py:launch_interactive_session` and `launch.py:launch_visualization_from_cli`).

```
User Intent Signals                  Controller Methods
────────────────────                 ──────────────────
step_backward_requested()     ───►   controller.step_backward()
step_forward_requested()      ───►   controller.step_forward()
play_requested()              ───►   controller.play()
pause_requested()             ───►   controller.pause()
stop_requested()              ───►   controller.stop()
phase_selected(int)           ───►   controller.set_phase(ReplayPhase(idx))
cell_clicked(row, col)        ───►   controller.select_cell(row, col)
agent_clicked()               ───►   controller.select_agent()
master_toggled(bool)          ───►   controller.set_debug_overlay_master(enabled)
overlay_toggled(bool)         ───►   controller.set_overlay_enabled(field, v)

Controller Output                    Widget Updates
────────────────                     ──────────────
frame_changed(frame)          ───►   window.set_frame(frame)
  └── routes to: grid_widget, status_panel, detail_panel,
                 replay_controls, step_analysis_panel
```

### SessionController (`session_controller.py`)

Central coordinator. Owns the mutable `ViewerState` reference.

Every public method follows the same pattern:
1. Compute new state via a pure transition function
2. Pass to `_apply(new_state)`

`_apply()`:
1. Identity check (`is` comparison) -- if unchanged, no-op
2. Store new state
3. Rebuild frame via `ViewModelBuilder.build()`
4. Emit `frame_changed` signal

Timer management: `play()` starts a 500ms `QTimer`, `pause()`/`stop()` stop it. `tick()` auto-stops at final position.

### Launch Flow

```
CLI: --experiment E --run R --episode N [--start-step S] [--start-phase P]
        │
        v
prepare_visualization_session()
  ├── ReplayAccessService(repository)
  ├── access.load_replay_episode(E, R, N) → ReplayEpisodeHandle
  ├── SnapshotResolver()
  ├── VisualizationSessionController(handle, resolver)
  └── controller.seek_to_coordinate(S, P)  [if specified]
        │
        v
launch_visualization_from_cli()
  ├── QApplication()
  ├── VisualizationMainWindow()
  ├── Wire all signals
  ├── window.set_frame(controller.current_frame)
  ├── window.show()
  └── app.exec()  [event loop]
```
