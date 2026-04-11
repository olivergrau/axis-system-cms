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
        self._detail_panel = DetailPanel(world_adapter.cell_color_config())
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
        self._replay_controls.set_frame(frame.status)
        self._step_analysis_panel.set_sections(frame.analysis_sections)
        self._detail_panel.set_frame(frame)
