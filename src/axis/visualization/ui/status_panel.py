"""Always-visible status bar for the visualization viewer."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from axis.visualization.view_models import StatusBarViewModel


class StatusPanel(QWidget):
    """Displays step, phase, playback, vitality, and world info."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._step_label = QLabel()
        self._phase_label = QLabel()
        self._playback_label = QLabel()
        self._vitality_label = QLabel()
        self._world_info_label = QLabel()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        for w in (
            self._step_label,
            self._phase_label,
            self._playback_label,
            self._vitality_label,
            self._world_info_label,
        ):
            layout.addWidget(w)
        self.setMaximumHeight(40)

    def set_frame(self, status: StatusBarViewModel) -> None:
        self._step_label.setText(
            f"Step: {status.step_index + 1} / {status.total_steps}"
        )
        self._phase_label.setText(f"Phase: {status.phase_name}")
        self._playback_label.setText(
            f"Playback: {status.playback_mode.value}"
        )
        self._vitality_label.setText(
            f"{status.vitality_label}: {status.vitality_display}"
        )
        if status.world_info:
            self._world_info_label.setText(status.world_info)
            self._world_info_label.show()
        else:
            self._world_info_label.hide()
