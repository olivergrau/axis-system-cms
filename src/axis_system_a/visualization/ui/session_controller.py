"""Visualization session controller (VWP7).

Thin coordination layer that wires user intents (button clicks, cell
selection) to pure state transitions and rebuilds the frame view model.
This is a **bridge module** — it legitimately imports both domain types
and UI types.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Signal

from axis_system_a.visualization.playback_controller import (
    PlaybackController,
    get_initial_coordinate,
)
from axis_system_a.visualization.replay_models import ReplayEpisodeHandle
from axis_system_a.visualization.snapshot_models import ReplayPhase
from axis_system_a.visualization.snapshot_resolver import SnapshotResolver
from axis_system_a.visualization.view_model_builder import ViewModelBuilder
from axis_system_a.visualization.view_models import ViewerFrameViewModel
from axis_system_a.visualization.viewer_state import (
    PlaybackMode,
    ViewerState,
    create_initial_state,
)
from axis_system_a.visualization.viewer_state_transitions import (
    clear_selection,
    select_agent,
    select_cell,
    set_playback_mode,
)

_PLAYBACK_INTERVAL_MS = 500


class VisualizationSessionController(QObject):
    """Coordinates replay interactions for a single episode session.

    Receives intent signals from widgets, applies pure state transitions,
    rebuilds the view model, and emits ``frame_changed``.
    """

    frame_changed = Signal(object)

    def __init__(
        self,
        episode_handle: ReplayEpisodeHandle,
        snapshot_resolver: SnapshotResolver,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._playback = PlaybackController()
        self._builder = ViewModelBuilder(snapshot_resolver)
        self._state = create_initial_state(episode_handle)
        self._frame = self._builder.build(self._state)

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
        if new_state is self._state:
            return
        self._state = new_state
        self._frame = self._builder.build(self._state)
        self.frame_changed.emit(self._frame)

    # -- Navigation --------------------------------------------------------

    def step_forward(self) -> None:
        self._apply(self._playback.step_forward(self._state))

    def step_backward(self) -> None:
        self._apply(self._playback.step_backward(self._state))

    # -- Playback ----------------------------------------------------------

    def play(self) -> None:
        new = set_playback_mode(self._state, PlaybackMode.PLAYING)
        self._apply(new)
        self._timer.start()

    def pause(self) -> None:
        self._timer.stop()
        new = set_playback_mode(self._state, PlaybackMode.PAUSED)
        self._apply(new)

    def stop(self) -> None:
        self._timer.stop()
        coord = get_initial_coordinate(self._state.episode_handle)
        new = self._playback.seek_to_coordinate(self._state, coord)
        new = set_playback_mode(new, PlaybackMode.STOPPED)
        self._apply(new)

    def tick(self) -> None:
        new = self._playback.tick(self._state)
        self._apply(new)
        if new.playback_mode != PlaybackMode.PLAYING:
            self._timer.stop()

    # -- Phase -------------------------------------------------------------

    def set_phase(self, phase: ReplayPhase) -> None:
        self._apply(self._playback.set_phase(self._state, phase))

    # -- Selection ---------------------------------------------------------

    def select_cell(self, row: int, col: int) -> None:
        self._apply(select_cell(self._state, row, col))

    def select_agent(self) -> None:
        self._apply(select_agent(self._state))

    def clear_selection(self) -> None:
        self._apply(clear_selection(self._state))
