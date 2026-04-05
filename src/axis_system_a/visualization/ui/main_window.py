"""Main visualization window (VWP6/VWP7/VWP11).

Composes child widgets into a stable structural layout and routes
frame view models downward.  Thin compositor — no replay logic.

VWP11 replaces ``DebugInfoPanel`` with ``StepAnalysisPanel``.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QSplitter, QVBoxLayout, QWidget

from axis_system_a.visualization.ui.debug_overlay_panel import DebugOverlayPanel
from axis_system_a.visualization.ui.detail_panel import DetailPanel
from axis_system_a.visualization.ui.grid_widget import GridWidget
from axis_system_a.visualization.ui.replay_controls_panel import ReplayControlsPanel
from axis_system_a.visualization.ui.status_panel import StatusPanel
from axis_system_a.visualization.ui.step_analysis_panel import StepAnalysisPanel
from axis_system_a.visualization.view_models import ViewerFrameViewModel


class VisualizationMainWindow(QMainWindow):
    """PySide6 main window for the visualization layer."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AXIS System A \u2014 Visualization")
        self.resize(1200, 800)

        # Child widgets
        self._replay_controls = ReplayControlsPanel()
        self._debug_overlay_panel = DebugOverlayPanel()
        self._status_panel = StatusPanel()
        self._step_analysis_panel = StepAnalysisPanel()
        self._grid_widget = GridWidget()
        self._detail_panel = DetailPanel()

        # Layout
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.addWidget(self._replay_controls)
        main_layout.addWidget(self._debug_overlay_panel)
        main_layout.addWidget(self._status_panel)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.addWidget(self._step_analysis_panel)
        self._splitter.addWidget(self._grid_widget)
        self._splitter.addWidget(self._detail_panel)
        self._splitter.setSizes([250, 700, 250])

        main_layout.addWidget(self._splitter)
        self.setCentralWidget(central)

    @property
    def grid_widget(self) -> GridWidget:
        return self._grid_widget

    @property
    def replay_controls(self) -> ReplayControlsPanel:
        return self._replay_controls

    @property
    def debug_overlay_panel(self) -> DebugOverlayPanel:
        return self._debug_overlay_panel

    @property
    def step_analysis_panel(self) -> StepAnalysisPanel:
        return self._step_analysis_panel

    def set_frame(self, frame: ViewerFrameViewModel) -> None:
        """Route frame sub-models to all child widgets."""
        self._grid_widget.set_frame(
            frame.grid, frame.agent, frame.selection, frame.debug_overlay,
        )
        self._status_panel.set_frame(frame.status)
        self._detail_panel.set_frame(frame)
        self._replay_controls.set_frame(frame.status)
        self._step_analysis_panel.set_frame(frame.step_analysis)
