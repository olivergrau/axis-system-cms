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
        """Apply a state transition: rebuild frame if state changed.

        If the new state leads to an unavailable phase (e.g. an
        intermediate snapshot that was not recorded), the transition
        is silently rejected and the previous state is preserved.
        """
        from axis.visualization.errors import PhaseNotAvailableError

        if new_state is self._state:
            return
        try:
            new_frame = self._builder.build(new_state)
        except PhaseNotAvailableError:
            # Phase not available — emit current frame to reset the UI
            self.frame_changed.emit(self._frame)
            return
        self._state = new_state
        self._frame = new_frame
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
