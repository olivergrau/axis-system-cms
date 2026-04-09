# WP-V.4.4 Implementation Brief -- Main Window, Session Controller, and Launch

## Context

This is the final assembly WP for the visualization system. It wires all components into a running application: the `MainWindow` arranges widgets, the `SessionController` coordinates state transitions and adapter delegation, `app.py` wires signals, and `launch.py` provides the entry point.

In v0.1.0, the `VisualizationMainWindow` (80 lines), `VisualizationSessionController` (145 lines), `app.py` (96 lines), and `launch.py` (123 lines) have several System A-specific bindings: `ReplayPhase` enum in signal wiring, `EpisodeResult` in data loading, hard-coded 3-overlay signal connections, and `ExperimentRepository` from `axis_system_a`. All of these become generic in v0.2.0.

A notable v0.1.0 issue is duplicated signal-wiring code between `app.py` and `launch.py`. The v0.2.0 version consolidates this into a single `_wire_signals()` function.

### Predecessor State (After WP-V.4.3)

```
src/axis/visualization/
    __init__.py
    types.py
    protocols.py
    registry.py
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
```

### v0.1.0 Source Files Being Migrated

| v0.1.0 file | v0.2.0 destination | Key changes |
|---|---|---|
| `ui/main_window.py` | `ui/main_window.py` | Takes adapters for panel construction; routes new VM fields |
| `ui/session_controller.py` | `ui/session_controller.py` | Uses generic viewer state, phase_index, overlay_key toggle |
| `ui/app.py` | `ui/app.py` | Dynamic signal wiring via overlay_key; consolidated wiring |
| `launch.py` | `launch.py` | Adapter resolution, generic entry point |

### Reference Documents

- `docs/architecture/evolution/visualization-architecture.md` -- Sections 2, 3, 12.3, 14.1
- `docs/architecture/evolution/visualization-architecture-roadmap.md` -- WP-V.4.4

---

## Objective

Wire all visualization components into a running application with adapter resolution, signal wiring, and CLI entry point.

---

## Scope

### 1. MainWindow

**File**: `src/axis/visualization/ui/main_window.py` (new)

```python
"""Main window for the visualization viewer."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QSplitter, QVBoxLayout, QWidget

from axis.visualization.types import OverlayTypeDeclaration
from axis.visualization.ui.canvas_widget import CanvasWidget
from axis.visualization.ui.detail_panel import DetailPanel
from axis.visualization.ui.overlay_panel import OverlayPanel
from axis.visualization.ui.replay_controls_panel import ReplayControlsPanel
from axis.visualization.ui.status_panel import StatusPanel
from axis.visualization.ui.step_analysis_panel import StepAnalysisPanel
from axis.visualization.view_models import ViewerFrameViewModel


class VisualizationMainWindow(QMainWindow):
    """Top-level window assembling all visualization panels.

    Takes adapter information at construction time to parameterize
    panels that differ by system/world type.
    """

    def __init__(
        self,
        world_adapter: Any,
        phase_names: list[str],
        overlay_declarations: list[OverlayTypeDeclaration],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("AXIS Replay Viewer")
        self.resize(1200, 800)

        # Create child widgets with adapter parameters
        self._canvas = CanvasWidget(world_adapter)
        self._status_panel = StatusPanel()
        self._step_analysis_panel = StepAnalysisPanel()
        self._detail_panel = DetailPanel()
        self._replay_controls = ReplayControlsPanel(phase_names)
        self._overlay_panel = OverlayPanel(overlay_declarations)

        # Layout: controls + overlay panel on top, splitter in center
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self._replay_controls)
        layout.addWidget(self._overlay_panel)
        layout.addWidget(self._status_panel)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._step_analysis_panel)
        splitter.addWidget(self._canvas)
        splitter.addWidget(self._detail_panel)
        splitter.setSizes([250, 700, 250])
        layout.addWidget(splitter, stretch=1)

        self.setCentralWidget(central)

    # -- Properties for signal wiring ---------------------------------------

    @property
    def canvas(self) -> CanvasWidget:
        return self._canvas

    @property
    def replay_controls(self) -> ReplayControlsPanel:
        return self._replay_controls

    @property
    def overlay_panel(self) -> OverlayPanel:
        return self._overlay_panel

    @property
    def step_analysis_panel(self) -> StepAnalysisPanel:
        return self._step_analysis_panel

    # -- Frame routing ------------------------------------------------------

    def set_frame(self, frame: ViewerFrameViewModel) -> None:
        """Route a frame view model to all child widgets."""
        self._canvas.set_frame(
            frame.grid,
            frame.agent,
            frame.selection,
            frame.overlay_data,
            frame.topology_indicators,
        )
        self._status_panel.set_frame(frame.status)
        self._step_analysis_panel.set_sections(frame.analysis_sections)
        self._detail_panel.set_frame(frame)
```

**Changes from v0.1.0**:
- Constructor takes `world_adapter`, `phase_names`, `overlay_declarations` to parameterize child widgets
- `set_frame()` routes `frame.overlay_data` and `frame.topology_indicators` to canvas
- `set_frame()` routes `frame.analysis_sections` to step analysis panel (generic tuple, not System A ViewModel)
- `replay_controls` property renamed neutral (was `grid_widget`)
- `debug_overlay_panel` property → `overlay_panel`

### 2. SessionController

**File**: `src/axis/visualization/ui/session_controller.py` (new)

```python
"""Session controller coordinating replay state and view model building."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, QTimer, Signal

from axis.visualization.playback_controller import PlaybackController
from axis.visualization.replay_models import ReplayEpisodeHandle
from axis.visualization.snapshot_models import ReplayCoordinate
from axis.visualization.snapshot_resolver import SnapshotResolver
from axis.visualization.view_model_builder import ViewModelBuilder
from axis.visualization.view_models import ViewerFrameViewModel
from axis.visualization.viewer_state import (
    PlaybackMode,
    ViewerState,
    create_initial_state,
)
from axis.visualization.viewer_state_transitions import (
    clear_selection,
    select_agent,
    select_cell,
    set_overlay_enabled,
    set_playback_mode,
    toggle_overlay_master,
)


_PLAYBACK_INTERVAL_MS = 500


class VisualizationSessionController(QObject):
    """Coordinates viewer state, playback, and view model building.

    Holds the current ViewerState, delegates transitions to pure
    functions, rebuilds the ViewerFrameViewModel on each change,
    and emits frame_changed for the UI to consume.
    """

    frame_changed = Signal(object)  # ViewerFrameViewModel

    def __init__(
        self,
        episode_handle: ReplayEpisodeHandle,
        world_adapter: Any,
        system_adapter: Any,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        phase_names = system_adapter.phase_names()
        num_phases = len(phase_names)

        self._state = create_initial_state(episode_handle, num_phases)
        self._playback = PlaybackController()
        self._builder = ViewModelBuilder(
            SnapshotResolver(), world_adapter, system_adapter,
        )
        self._system_adapter = system_adapter

        # Build initial frame
        self._frame = self._builder.build(self._state)

        # Playback timer
        self._timer = QTimer(self)
        self._timer.setInterval(_PLAYBACK_INTERVAL_MS)
        self._timer.timeout.connect(self.tick)

    @property
    def current_state(self) -> ViewerState:
        return self._state

    @property
    def current_frame(self) -> ViewerFrameViewModel:
        return self._frame

    def _apply(self, new_state: ViewerState) -> None:
        """Apply a state transition: rebuild frame if state changed."""
        if new_state is self._state:
            return
        self._state = new_state
        self._frame = self._builder.build(self._state)
        self.frame_changed.emit(self._frame)

    # -- Navigation ---------------------------------------------------------

    def step_forward(self) -> None:
        self._apply(self._playback.step_forward(self._state))

    def step_backward(self) -> None:
        self._apply(self._playback.step_backward(self._state))

    def play(self) -> None:
        self._apply(set_playback_mode(self._state, PlaybackMode.PLAYING))
        self._timer.start()

    def pause(self) -> None:
        self._timer.stop()
        self._apply(set_playback_mode(self._state, PlaybackMode.PAUSED))

    def stop(self) -> None:
        self._timer.stop()
        self._apply(set_playback_mode(self._state, PlaybackMode.STOPPED))

    def tick(self) -> None:
        new_state = self._playback.tick(self._state)
        self._apply(new_state)
        if new_state.playback_mode is not PlaybackMode.PLAYING:
            self._timer.stop()

    def set_phase(self, phase_index: int) -> None:
        self._apply(self._playback.set_phase(self._state, phase_index))

    # -- Selection ----------------------------------------------------------

    def select_cell(self, row: int, col: int) -> None:
        self._apply(select_cell(self._state, row, col))

    def select_agent(self) -> None:
        self._apply(select_agent(self._state))

    def clear_selection(self) -> None:
        self._apply(clear_selection(self._state))

    def seek_to_coordinate(self, coordinate: ReplayCoordinate) -> None:
        self._apply(self._playback.seek_to_coordinate(self._state, coordinate))

    # -- Overlay control ----------------------------------------------------

    def set_overlay_master(self, enabled: bool) -> None:
        if enabled:
            if not self._state.overlay_config.master_enabled:
                self._apply(toggle_overlay_master(self._state))
        else:
            if self._state.overlay_config.master_enabled:
                self._apply(toggle_overlay_master(self._state))

    def set_overlay_type_enabled(
        self, overlay_key: str, enabled: bool,
    ) -> None:
        self._apply(set_overlay_enabled(self._state, overlay_key, enabled))
```

**Changes from v0.1.0**:
- Constructor takes `world_adapter` and `system_adapter` (creates `ViewModelBuilder` with both adapters and `SnapshotResolver`)
- `set_phase(phase_index: int)` replaces `set_phase(phase: ReplayPhase)`
- `set_debug_overlay_master` → `set_overlay_master`
- `set_overlay_enabled(field_name, enabled)` → `set_overlay_type_enabled(overlay_key, enabled)` using string key from `OverlayTypeDeclaration`
- `toggle_debug_overlay` import → `toggle_overlay_master`
- `create_initial_state` called with `num_phases`

### 3. App (Signal Wiring)

**File**: `src/axis/visualization/ui/app.py` (new)

```python
"""Application assembly and signal wiring.

Consolidates signal wiring that was duplicated between app.py
and launch.py in v0.1.0.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from axis.visualization.ui.main_window import VisualizationMainWindow
from axis.visualization.ui.session_controller import (
    VisualizationSessionController,
)
from axis.visualization.view_models import ViewerFrameViewModel


def wire_signals(
    window: VisualizationMainWindow,
    controller: VisualizationSessionController,
) -> None:
    """Wire all signals between window and controller.

    Consolidates the signal-wiring pattern that was duplicated
    in v0.1.0 between app.py and launch.py.
    """
    # Frame updates: controller -> window
    controller.frame_changed.connect(window.set_frame)

    # Replay controls -> controller
    controls = window.replay_controls
    controls.step_backward_requested.connect(controller.step_backward)
    controls.step_forward_requested.connect(controller.step_forward)
    controls.play_requested.connect(controller.play)
    controls.pause_requested.connect(controller.pause)
    controls.stop_requested.connect(controller.stop)
    controls.phase_selected.connect(controller.set_phase)

    # Canvas -> controller
    window.canvas.cell_clicked.connect(controller.select_cell)
    window.canvas.agent_clicked.connect(controller.select_agent)

    # Overlay panel -> controller
    overlay = window.overlay_panel
    overlay.master_toggled.connect(controller.set_overlay_master)
    overlay.overlay_toggled.connect(controller.set_overlay_type_enabled)


def launch_interactive_session(
    window: VisualizationMainWindow,
    controller: VisualizationSessionController,
) -> int:
    """Wire signals, show window, and run the Qt event loop."""
    app = QApplication.instance() or QApplication(sys.argv)

    wire_signals(window, controller)

    # Set initial frame
    window.set_frame(controller.current_frame)
    window.show()

    return app.exec()
```

**Changes from v0.1.0**:
- `wire_signals()` extracted as a standalone function (eliminates code duplication between app.py and launch.py)
- Overlay wiring uses single `overlay.overlay_toggled.connect(controller.set_overlay_type_enabled)` instead of 3 per-type lambda connections
- Phase wiring uses `controls.phase_selected.connect(controller.set_phase)` directly (int signal → int parameter, no lambda)
- `launch_visualization_app` (static one-shot display) removed -- not needed in v0.2.0 (all viewing is interactive)

### 4. Launch Entry Point

**File**: `src/axis/visualization/launch.py` (new)

```python
"""Visualization viewer entry point.

Resolves adapters from episode data, builds session, launches UI.
"""

from __future__ import annotations

from axis.framework.persistence import ExperimentRepository
from axis.visualization.errors import StepOutOfBoundsError
from axis.visualization.registry import (
    resolve_system_adapter,
    resolve_world_adapter,
)
from axis.visualization.replay_access import ReplayAccessService
from axis.visualization.snapshot_models import ReplayCoordinate
from axis.visualization.ui.app import launch_interactive_session
from axis.visualization.ui.main_window import VisualizationMainWindow
from axis.visualization.ui.session_controller import (
    VisualizationSessionController,
)


def launch_visualization(
    repository: ExperimentRepository,
    experiment_id: str,
    run_id: str,
    episode_index: int,
    *,
    start_step: int | None = None,
    start_phase: int | None = None,
) -> int:
    """Load episode, resolve adapters, and launch the visualization viewer.

    Args:
        repository: Experiment repository root.
        experiment_id: Experiment to visualize.
        run_id: Run within the experiment.
        episode_index: Episode index within the run.
        start_step: Optional initial step (0-based).
        start_phase: Optional initial phase index.

    Returns:
        Qt application exit code.
    """
    # 1. Load and validate episode
    access = ReplayAccessService(repository)
    episode_handle = access.load_replay_episode(
        experiment_id, run_id, episode_index,
    )

    # 2. Read type identifiers from episode trace
    episode = episode_handle.episode_trace
    system_type = episode.system_type
    world_type = getattr(episode, "world_type", "grid_2d")
    world_config = getattr(episode, "world_config", {})

    # 3. Resolve adapters
    world_adapter = resolve_world_adapter(world_type, world_config)
    system_adapter = resolve_system_adapter(system_type)

    # 4. Build session controller
    controller = VisualizationSessionController(
        episode_handle, world_adapter, system_adapter,
    )

    # 5. Optional seek
    if start_step is not None:
        phase = start_phase if start_phase is not None else 0
        total = episode_handle.validation.total_steps
        if start_step < 0 or start_step >= total:
            raise StepOutOfBoundsError(start_step, total)
        controller.seek_to_coordinate(
            ReplayCoordinate(step_index=start_step, phase_index=phase),
        )

    # 6. Build window
    phase_names = system_adapter.phase_names()
    overlay_declarations = system_adapter.available_overlay_types()

    # Import adapter visualization modules to trigger registration
    _import_adapter_modules()

    window = VisualizationMainWindow(
        world_adapter, phase_names, overlay_declarations,
    )

    # 7. Launch
    return launch_interactive_session(window, controller)


def _import_adapter_modules() -> None:
    """Import adapter visualization modules to trigger registration.

    Each module calls register_world_visualization() or
    register_system_visualization() at import time.
    """
    try:
        import axis.world.grid_2d.visualization  # noqa: F401
    except ImportError:
        pass
    try:
        import axis.world.toroidal.visualization  # noqa: F401
    except ImportError:
        pass
    try:
        import axis.world.signal_landscape.visualization  # noqa: F401
    except ImportError:
        pass
    try:
        import axis.systems.system_a.visualization  # noqa: F401
    except ImportError:
        pass
    try:
        import axis.systems.system_b.visualization  # noqa: F401
    except ImportError:
        pass
```

**Changes from v0.1.0**:
- `start_phase` parameter is `int | None` (not `ReplayPhase | None`)
- Adapter resolution: reads `episode.world_type` and `episode.system_type`, calls `resolve_world_adapter()` and `resolve_system_adapter()` from the visualization registry
- `_import_adapter_modules()` triggers registration of all known adapters
- Uses `getattr(episode, "world_type", "grid_2d")` for backward compatibility with episodes serialized before WP-V.0.1
- No duplicated signal wiring -- delegates to `launch_interactive_session()` which calls `wire_signals()`
- Uses `axis.framework.persistence.ExperimentRepository` instead of `axis_system_a.repository.ExperimentRepository`

### 5. CLI Integration

**File**: `src/axis/framework/cli.py` (modified)

Add a `visualize` subcommand:

```python
# In the CLI argument parser, add:
visualize_parser = subparsers.add_parser("visualize", help="Launch replay viewer")
visualize_parser.add_argument("--experiment", required=True)
visualize_parser.add_argument("--run", required=True)
visualize_parser.add_argument("--episode", type=int, required=True)
visualize_parser.add_argument("--step", type=int, default=None)
visualize_parser.add_argument("--phase", type=int, default=None)

# In the command dispatcher:
if args.command == "visualize":
    from axis.visualization.launch import launch_visualization
    repository = ExperimentRepository(Path(args.output_dir))
    sys.exit(launch_visualization(
        repository, args.experiment, args.run, args.episode,
        start_step=args.step, start_phase=args.phase,
    ))
```

**Note**: The CLI modification is minimal -- just adding the subcommand routing. The actual work is in `launch.py`.

---

## Out of Scope

- New overlay types or rendering improvements
- Playback speed configuration UI (slider)
- Multi-episode loading or comparison views
- Theme/styling configuration
- Export/screenshot functionality

---

## Architectural Constraints

### 1. Adapter Resolution at Launch

Adapters are resolved once at launch time from the episode trace's `world_type` and `system_type`. They are injected into the `SessionController` and `MainWindow`. This is the only point where the application touches the visualization registry.

### 2. Signal Wiring Consolidation

All signal connections are made in `wire_signals()` -- a single function that the launch entry point calls. This eliminates the v0.1.0 duplication between `app.py` and `launch.py`.

### 3. No System-Specific Imports in Base Layer

`main_window.py`, `session_controller.py`, `app.py`, and `launch.py` import only from `axis.visualization.*` and `axis.framework.*`. The adapter modules (`axis.world.*.visualization`, `axis.systems.*.visualization`) are imported only in `_import_adapter_modules()` for registration, never for type references.

### 4. Backward Compatibility

`getattr(episode, "world_type", "grid_2d")` handles episodes persisted before WP-V.0.1 added the `world_type` field. The `DefaultWorldVisualizationAdapter` handles unknown world types gracefully.

---

## Testing Requirements

**File**: `tests/visualization/test_session_controller.py` (new)
**File**: `tests/visualization/test_launch.py` (new)

### SessionController tests (`test_session_controller.py`)

1. **`test_controller_construction`**: Create with episode handle and mock adapters, assert no crash
2. **`test_initial_frame_built`**: Assert `current_frame` is not None after construction
3. **`test_step_forward_emits_frame`**: Connect to `frame_changed`, call `step_forward()`, assert signal emitted
4. **`test_step_backward_emits_frame`**: Same for backward
5. **`test_play_starts_timer`**: Call `play()`, assert playback mode is PLAYING
6. **`test_pause_stops_timer`**: Call `play()` then `pause()`, assert PAUSED
7. **`test_stop_resets`**: Call `play()` then `stop()`, assert STOPPED
8. **`test_set_phase`**: Call `set_phase(1)`, assert phase_index updated in state
9. **`test_select_cell`**: Call `select_cell(2, 3)`, assert selection in state
10. **`test_select_agent`**: Call `select_agent()`, assert agent selected
11. **`test_clear_selection`**: Call `clear_selection()`, assert no selection
12. **`test_overlay_master_toggle`**: Call `set_overlay_master(True)`, assert enabled
13. **`test_overlay_type_toggle`**: Call `set_overlay_type_enabled("action_preference", True)`, assert in enabled set
14. **`test_identity_transition_no_emit`**: If transition returns same state, assert `frame_changed` NOT emitted

### MainWindow tests

15. **`test_main_window_construction`**: Create with mock adapters, 3 phases, 2 overlays, assert no crash
16. **`test_main_window_set_frame`**: Call `set_frame()` with valid frame, assert no crash
17. **`test_main_window_properties`**: Assert canvas, replay_controls, overlay_panel properties return correct types

### Wire signals tests

18. **`test_wire_signals_no_crash`**: Wire signals between window and controller, assert no crash
19. **`test_wire_signals_forward`**: Click forward button, assert controller `step_forward` called

### Launch tests (`test_launch.py`)

20. **`test_launch_visualization_not_found`**: Invalid experiment_id, assert `ExperimentNotFoundError`
21. **`test_launch_visualization_invalid_step`**: start_step out of bounds, assert `StepOutOfBoundsError`
22. **`test_import_adapter_modules_no_crash`**: Call `_import_adapter_modules()`, assert no crash even if modules not available

---

## Expected Deliverable

1. `src/axis/visualization/ui/main_window.py`
2. `src/axis/visualization/ui/session_controller.py`
3. `src/axis/visualization/ui/app.py`
4. `src/axis/visualization/launch.py`
5. Update `src/axis/framework/cli.py` with `visualize` subcommand
6. `tests/visualization/test_session_controller.py`
7. `tests/visualization/test_launch.py`
8. Confirmation that all existing tests still pass

---

## Expected File Structure

```
src/axis/visualization/
    __init__.py                          # UNCHANGED
    types.py                             # UNCHANGED
    protocols.py                         # UNCHANGED
    registry.py                          # UNCHANGED
    errors.py                            # UNCHANGED (WP-V.3.1)
    replay_models.py                     # UNCHANGED (WP-V.3.1)
    replay_validation.py                 # UNCHANGED (WP-V.3.1)
    replay_access.py                     # UNCHANGED (WP-V.3.1)
    snapshot_models.py                   # UNCHANGED (WP-V.3.2)
    snapshot_resolver.py                 # UNCHANGED (WP-V.3.2)
    viewer_state.py                      # UNCHANGED (WP-V.3.3)
    viewer_state_transitions.py          # UNCHANGED (WP-V.3.3)
    playback_controller.py               # UNCHANGED (WP-V.3.3)
    view_models.py                       # UNCHANGED (WP-V.3.4)
    view_model_builder.py                # UNCHANGED (WP-V.3.4)
    launch.py                            # NEW
    adapters/
        default_world.py                 # UNCHANGED
        null_system.py                   # UNCHANGED
    ui/
        __init__.py                      # UNCHANGED (WP-V.4.1)
        canvas_widget.py                 # UNCHANGED (WP-V.4.1/4.2)
        overlay_renderer.py              # UNCHANGED (WP-V.4.2)
        status_panel.py                  # UNCHANGED (WP-V.4.3)
        step_analysis_panel.py           # UNCHANGED (WP-V.4.3)
        detail_panel.py                  # UNCHANGED (WP-V.4.3)
        replay_controls_panel.py         # UNCHANGED (WP-V.4.3)
        overlay_panel.py                 # UNCHANGED (WP-V.4.3)
        main_window.py                   # NEW
        session_controller.py            # NEW
        app.py                           # NEW

src/axis/framework/
    cli.py                               # MODIFIED (add visualize subcommand)

tests/visualization/
    test_session_controller.py           # NEW
    test_launch.py                       # NEW
```

---

## Important Final Constraint

This WP completes the visualization system. After it, a user can run:

```bash
axis visualize --experiment exp_001 --run run_001 --episode 0
```

The viewer will:
1. Load `BaseEpisodeTrace` from the repository
2. Read `system_type` and `world_type` from the episode
3. Resolve the correct world and system adapters
4. Build the session controller and main window
5. Display the replay with correct cell geometry (rectangular/toroidal/heatmap), analysis panels (5 System A sections / 5 System B sections), and overlay controls (3 System A overlays / 2 System B overlays)

The only remaining phase (V-5) is test suite and validation.
