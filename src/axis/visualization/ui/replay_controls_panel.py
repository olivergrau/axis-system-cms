"""Replay controls with dynamically populated phase combo box."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QWidget

from axis.visualization.view_models import StatusBarViewModel


class ReplayControlsPanel(QWidget):
    """Playback controls and phase selection."""

    step_backward_requested = Signal()
    step_forward_requested = Signal()
    play_requested = Signal()
    pause_requested = Signal()
    stop_requested = Signal()
    phase_selected = Signal(int)  # phase_index

    def __init__(
        self,
        phase_names: list[str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._updating = False

        # Buttons
        self._btn_back = QPushButton("<")
        self._btn_play = QPushButton("Play")
        self._btn_pause = QPushButton("Pause")
        self._btn_stop = QPushButton("Stop")
        self._btn_fwd = QPushButton(">")

        # Phase combo box -- populated from system adapter
        self._phase_combo = QComboBox()
        for name in phase_names:
            self._phase_combo.addItem(name)

        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        for btn in (
            self._btn_back, self._btn_play, self._btn_pause,
            self._btn_stop, self._btn_fwd,
        ):
            layout.addWidget(btn)
        layout.addWidget(self._phase_combo)
        self.setMaximumHeight(50)

        # Signals
        self._btn_back.clicked.connect(self.step_backward_requested)
        self._btn_play.clicked.connect(self.play_requested)
        self._btn_pause.clicked.connect(self.pause_requested)
        self._btn_stop.clicked.connect(self.stop_requested)
        self._btn_fwd.clicked.connect(self.step_forward_requested)
        self._phase_combo.currentIndexChanged.connect(self._on_phase_changed)

    def _on_phase_changed(self, index: int) -> None:
        if not self._updating:
            self.phase_selected.emit(index)

    def set_frame(self, status: StatusBarViewModel) -> None:
        self._updating = True
        try:
            self._phase_combo.setCurrentIndex(status.phase_index)
            self._btn_back.setEnabled(not status.at_start)
            self._btn_fwd.setEnabled(not status.at_end)
            playing = status.playback_mode.value == "playing"
            self._btn_play.setEnabled(not playing and not status.at_end)
            self._btn_pause.setEnabled(playing)
        finally:
            self._updating = False
