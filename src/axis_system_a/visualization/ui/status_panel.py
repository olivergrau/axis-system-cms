"""Always-visible status panel (VWP6).

Displays critical current-frame information via ``QLabel`` widgets.
"""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from axis_system_a.visualization.view_models import StatusBarViewModel


class StatusPanel(QWidget):
    """Horizontal bar of read-only status labels."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._step_label = QLabel("Step: –")
        self._phase_label = QLabel("Phase: –")
        self._playback_label = QLabel("Playback: –")
        self._energy_label = QLabel("Energy: –")
        self._boundary_label = QLabel("")

        layout = QHBoxLayout(self)
        layout.addWidget(self._step_label)
        layout.addWidget(self._phase_label)
        layout.addWidget(self._playback_label)
        layout.addWidget(self._energy_label)
        layout.addWidget(self._boundary_label)
        self.setMaximumHeight(40)

    def set_frame(self, status: StatusBarViewModel) -> None:
        """Update all labels from the status view model."""
        self._step_label.setText(
            f"Step: {status.step_index}/{status.total_steps - 1}",
        )
        self._phase_label.setText(f"Phase: {status.phase.name}")
        self._playback_label.setText(
            f"Playback: {status.playback_mode.value}",
        )
        self._energy_label.setText(f"Energy: {status.energy:.2f}")
        if status.at_start:
            self._boundary_label.setText("START")
        elif status.at_end:
            self._boundary_label.setText("END")
        else:
            self._boundary_label.setText("")
