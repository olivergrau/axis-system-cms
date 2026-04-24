"""Main window for the visualization viewer."""

from __future__ import annotations

from typing import Any

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from axis.visualization.types import OverlayTypeDeclaration
from axis.visualization.ui.canvas_widget import CanvasWidget
from axis.visualization.ui.config_viewer import ConfigViewerWindow
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
        *,
        experiment_config_text: str | None = None,
        run_config_text: str | None = None,
        initial_width: int = 1440,
        initial_height: int = 800,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("AXIS Replay Viewer")
        self.resize(initial_width, initial_height)
        self._experiment_config_text = experiment_config_text
        self._run_config_text = run_config_text
        self._config_window: ConfigViewerWindow | None = None

        icon_path = Path(__file__).resolve(
        ).parents[4] / "docs" / "assets" / "images" / "logo_futuristic_elegant.png"
        if icon_path.exists():
            icon = QIcon()
            pixmap = QPixmap(str(icon_path))
            for size in (16, 24, 32, 48, 64, 128, 256):
                icon.addPixmap(
                    pixmap.scaled(size, size, mode=Qt.TransformationMode.SmoothTransformation),
                )
            self.setWindowIcon(icon)

        # Create child widgets with adapter parameters
        self._canvas = CanvasWidget(world_adapter)
        self._status_panel = StatusPanel()
        self._step_analysis_panel = StepAnalysisPanel()
        self._detail_panel = DetailPanel(world_adapter.cell_color_config())
        self._replay_controls = ReplayControlsPanel(phase_names)
        self._overlay_panel = OverlayPanel(overlay_declarations)
        self._config_button = QPushButton("Show Config")
        self._config_button.clicked.connect(self.show_config_viewer)
        self._config_button.setEnabled(
            bool(self._experiment_config_text or self._run_config_text),
        )

        # Layout: controls + config button + overlay panel on top, splitter in center
        central = QWidget()
        layout = QVBoxLayout(central)
        controls_row = QHBoxLayout()
        controls_row.addWidget(self._replay_controls, stretch=1)
        controls_row.addWidget(self._config_button, stretch=0)
        layout.addLayout(controls_row)
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
    def config_button(self) -> QPushButton:
        return self._config_button

    @property
    def step_analysis_panel(self) -> StepAnalysisPanel:
        return self._step_analysis_panel

    @property
    def config_window(self) -> ConfigViewerWindow | None:
        return self._config_window

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

    def show_config_viewer(self) -> None:
        """Open or focus the detached config viewer window."""
        if self._config_window is None:
            self._config_window = ConfigViewerWindow(
                experiment_config_text=self._experiment_config_text or "Unavailable.",
                run_config_text=self._run_config_text or "Unavailable.",
                parent=self,
            )
        self._config_window.show()
        self._config_window.raise_()
        self._config_window.activateWindow()
