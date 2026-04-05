"""Main visualization window (VWP6).

Composes child widgets into a stable structural layout and routes
frame view models downward.  Thin compositor — no replay logic.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QSplitter, QVBoxLayout, QWidget

from axis_system_a.visualization.ui.detail_placeholder_panel import (
    DetailPlaceholderPanel,
)
from axis_system_a.visualization.ui.grid_widget import GridWidget
from axis_system_a.visualization.ui.status_panel import StatusPanel
from axis_system_a.visualization.view_models import ViewerFrameViewModel


class VisualizationMainWindow(QMainWindow):
    """PySide6 main window for the visualization layer."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AXIS System A \u2014 Visualization")
        self.resize(1200, 800)

        # Child widgets
        self._status_panel = StatusPanel()
        self._grid_widget = GridWidget()
        self._detail_panel = DetailPlaceholderPanel()
        self._control_placeholder = QWidget()  # reserved for VWP7+

        # Layout
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.addWidget(self._status_panel)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.addWidget(self._grid_widget)
        self._splitter.addWidget(self._detail_panel)
        self._splitter.addWidget(self._control_placeholder)
        self._splitter.setSizes([650, 250, 100])

        main_layout.addWidget(self._splitter)
        self.setCentralWidget(central)

    def set_frame(self, frame: ViewerFrameViewModel) -> None:
        """Route frame sub-models to all child widgets."""
        self._grid_widget.set_frame(frame.grid, frame.agent, frame.selection)
        self._status_panel.set_frame(frame.status)
        self._detail_panel.set_frame(frame.selection)
