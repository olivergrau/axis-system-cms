"""Replay controls panel (VWP7).

Emits intent signals for replay navigation. Contains no replay logic —
the ``VisualizationSessionController`` interprets the intents.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QWidget

from axis_system_a.visualization.view_models import StatusBarViewModel


class ReplayControlsPanel(QWidget):
    """Horizontal bar of replay control buttons and phase selector."""

    step_backward_requested = Signal()
    step_forward_requested = Signal()
    play_requested = Signal()
    pause_requested = Signal()
    stop_requested = Signal()
    phase_selected = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._updating = False

        self._step_back_btn = QPushButton("\u25c0\u25c0")
        self._play_btn = QPushButton("\u25b6")
        self._pause_btn = QPushButton("\u23f8")
        self._stop_btn = QPushButton("\u25a0")
        self._step_fwd_btn = QPushButton("\u25b6\u25b6")

        self._phase_combo = QComboBox()
        self._phase_combo.addItems(["BEFORE", "AFTER_REGEN", "AFTER_ACTION"])

        layout = QHBoxLayout(self)
        layout.addWidget(self._step_back_btn)
        layout.addWidget(self._play_btn)
        layout.addWidget(self._pause_btn)
        layout.addWidget(self._stop_btn)
        layout.addWidget(self._step_fwd_btn)
        layout.addWidget(self._phase_combo)
        self.setMaximumHeight(50)

        # Wire button clicks to signals
        self._step_back_btn.clicked.connect(self.step_backward_requested)
        self._play_btn.clicked.connect(self.play_requested)
        self._pause_btn.clicked.connect(self.pause_requested)
        self._stop_btn.clicked.connect(self.stop_requested)
        self._step_fwd_btn.clicked.connect(self.step_forward_requested)

        self._phase_combo.currentIndexChanged.connect(self._on_phase_changed)

    def _on_phase_changed(self, index: int) -> None:
        if not self._updating:
            self.phase_selected.emit(index)

    def set_frame(self, status: StatusBarViewModel) -> None:
        """Update button enabled states and phase combo from status."""
        self._updating = True
        try:
            self._phase_combo.setCurrentIndex(status.phase.value)

            self._step_back_btn.setEnabled(not status.at_start)
            self._step_fwd_btn.setEnabled(not status.at_end)

            is_playing = status.playback_mode.value == "playing"

            self._play_btn.setEnabled(not is_playing and not status.at_end)
            self._pause_btn.setEnabled(is_playing)
            self._stop_btn.setEnabled(status.playback_mode.value != "stopped")
        finally:
            self._updating = False
