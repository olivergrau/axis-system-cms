"""World-adapter-aware canvas for rendering the world grid.

Replaces v0.1.0's GridWidget. All geometry and coloring is delegated
to the world adapter via CellLayout and CellColorConfig.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
    QPolygonF,
)
from PySide6.QtWidgets import QWidget

from axis.visualization.types import (
    CellColorConfig,
    CellLayout,
    TopologyIndicator,
)
from axis.visualization.ui.overlay_renderer import OverlayRenderer
from axis.visualization.view_models import (
    AgentViewModel,
    GridCellViewModel,
    GridViewModel,
    SelectionViewModel,
)


def _polygon_to_qpolygon(
    vertices: tuple[tuple[float, float], ...],
) -> QPolygonF:
    """Convert a tuple of (x, y) vertices to a QPolygonF."""
    return QPolygonF([QPointF(x, y) for x, y in vertices])


class CanvasWidget(QWidget):
    """World-adapter-aware canvas for rendering the world grid.

    All geometry comes from CellLayout (produced by the world adapter).
    All coloring comes from CellColorConfig (produced by the world adapter).
    Overlay rendering is delegated to OverlayRenderer (WP-V.4.2).
    """

    cell_clicked = Signal(int, int)  # (row, col)
    agent_clicked = Signal()

    def __init__(
        self,
        world_adapter: Any,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._world_adapter = world_adapter
        self._cell_layout: CellLayout | None = None
        self._cell_color_config: CellColorConfig = world_adapter.cell_color_config()

        # Frame data (set via set_frame)
        self._grid: GridViewModel | None = None
        self._agent: AgentViewModel | None = None
        self._selection: SelectionViewModel | None = None
        self._overlay_data: tuple = ()
        self._topology_indicators: tuple[TopologyIndicator, ...] = ()

        # OverlayRenderer (WP-V.4.2)
        self._overlay_renderer = OverlayRenderer()

        self.setMinimumSize(200, 200)

    def set_frame(
        self,
        grid: GridViewModel,
        agent: AgentViewModel,
        selection: SelectionViewModel,
        overlay_data: tuple = (),
        topology_indicators: tuple[TopologyIndicator, ...] = (),
    ) -> None:
        """Update the frame data and trigger repaint."""
        self._grid = grid
        self._agent = agent
        self._selection = selection
        self._overlay_data = overlay_data
        self._topology_indicators = topology_indicators

        # Recompute layout if grid dimensions changed
        if self._cell_layout is None or (
            self._cell_layout.grid_width != grid.width
            or self._cell_layout.grid_height != grid.height
        ):
            self._recompute_layout()

        self.update()

    def _recompute_layout(self) -> None:
        """Recompute CellLayout from world adapter."""
        if self._grid is None:
            return
        self._cell_layout = self._world_adapter.cell_layout(
            self._grid.width,
            self._grid.height,
            float(self.width()),
            float(self.height()),
        )

    # -- Paint event --------------------------------------------------------

    def paintEvent(self, event: QPaintEvent) -> None:
        if self._grid is None or self._cell_layout is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        try:
            self._draw_cells(painter)
            self._draw_grid_lines(painter)
            self._draw_topology_indicators(painter)
            self._draw_selection(painter)
            self._draw_agent(painter)
            self._draw_overlays(painter)
        finally:
            painter.end()

    # -- Cell rendering (uses CellLayout + CellColorConfig) -----------------

    def _draw_cells(self, painter: QPainter) -> None:
        """Draw cell backgrounds using CellLayout polygons and CellColorConfig."""
        assert self._grid is not None
        assert self._cell_layout is not None
        for cell in self._grid.cells:
            key = (cell.col, cell.row)
            polygon = self._cell_layout.cell_polygons.get(key)
            if polygon is None:
                continue
            color = self._resolve_cell_color(cell)
            painter.setBrush(QBrush(QColor(*color)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(_polygon_to_qpolygon(polygon))

    def _resolve_cell_color(
        self, cell: GridCellViewModel,
    ) -> tuple[int, int, int]:
        """Determine the RGB color for a cell using CellColorConfig."""
        cc = self._cell_color_config
        if cell.is_obstacle:
            return cc.obstacle_color
        if cell.resource_value <= 0.0:
            return cc.empty_color
        # Linear interpolation between resource_color_min and resource_color_max
        t = min(1.0, max(0.0, cell.resource_value))
        r = int(cc.resource_color_min[0]
                + t * (cc.resource_color_max[0] - cc.resource_color_min[0]))
        g = int(cc.resource_color_min[1]
                + t * (cc.resource_color_max[1] - cc.resource_color_min[1]))
        b = int(cc.resource_color_min[2]
                + t * (cc.resource_color_max[2] - cc.resource_color_min[2]))
        return (r, g, b)

    def _draw_grid_lines(self, painter: QPainter) -> None:
        """Draw grid lines along polygon edges."""
        assert self._cell_layout is not None
        pen = QPen(QColor(*self._cell_color_config.grid_line_color), 1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for polygon in self._cell_layout.cell_polygons.values():
            painter.drawPolygon(_polygon_to_qpolygon(polygon))

    def _draw_topology_indicators(self, painter: QPainter) -> None:
        """Draw topology indicators (wrap edges, hotspot markers)."""
        for indicator in self._topology_indicators:
            if indicator.indicator_type == "wrap_edge":
                self._draw_wrap_edge(painter, indicator)
            elif indicator.indicator_type == "hotspot_center":
                self._draw_hotspot_center(painter, indicator)

    def _draw_wrap_edge(
        self, painter: QPainter, indicator: TopologyIndicator,
    ) -> None:
        """Draw a dashed line for wrap-edge topology indicator."""
        pen = QPen(QColor(100, 100, 255, 180), 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        x, y = indicator.position
        painter.drawLine(QPointF(x - 5, y), QPointF(x + 5, y))

    def _draw_hotspot_center(
        self, painter: QPainter, indicator: TopologyIndicator,
    ) -> None:
        """Draw a crosshair/circle for hotspot center indicator."""
        x, y = indicator.position
        radius = indicator.data.get("radius_pixels", 8)
        intensity = indicator.data.get("intensity", 0.8)
        alpha = int(255 * max(0.25, intensity))

        # Two-pass stroke to ensure visibility on bright backgrounds.
        painter.setPen(QPen(QColor(10, 20, 30, 220), 3.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(x, y), radius, radius)

        painter.setPen(QPen(QColor(90, 230, 255, alpha), 2.0))
        painter.drawEllipse(QPointF(x, y), radius, radius)

        # Mark center point for faster visual targeting.
        painter.setBrush(QBrush(QColor(90, 230, 255, min(255, alpha + 20))))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(x, y), 2.5, 2.5)

        # Label
        label = indicator.data.get("label", "")
        if label:
            text_pos = QPointF(x + radius + 4, y + 5)
            painter.setPen(QColor(5, 5, 5, 220))
            painter.drawText(
                QPointF(text_pos.x() + 1, text_pos.y() + 1), label)
            painter.setPen(QColor(235, 245, 255, 245))
            painter.drawText(text_pos, label)

    def _draw_selection(self, painter: QPainter) -> None:
        """Draw selection highlight using CellLayout polygon."""
        assert self._cell_layout is not None
        if self._selection is None or self._selection.selected_cell is None:
            return
        row, col = self._selection.selected_cell
        key = (col, row)
        polygon = self._cell_layout.cell_polygons.get(key)
        if polygon is None:
            return
        pen = QPen(QColor(*self._cell_color_config.selection_border_color), 3)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPolygon(_polygon_to_qpolygon(polygon))

    def _draw_agent(self, painter: QPainter) -> None:
        """Draw agent marker at CellLayout cell center."""
        assert self._cell_layout is not None
        if self._agent is None:
            return
        key = (self._agent.col, self._agent.row)
        center = self._cell_layout.cell_centers.get(key)
        bbox = self._cell_layout.cell_bounding_boxes.get(key)
        if center is None or bbox is None:
            return
        cx, cy = center
        _, _, cw, ch = bbox
        radius = min(cw, ch) * 0.3

        if self._agent.is_selected:
            color = self._cell_color_config.agent_selected_color
        else:
            color = self._cell_color_config.agent_color
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(*color)))
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

    def _draw_overlays(self, painter: QPainter) -> None:
        """Delegate overlay rendering to OverlayRenderer."""
        if self._overlay_renderer is not None and self._overlay_data:
            self._overlay_renderer.render(
                painter, self._overlay_data, self._cell_layout,
            )

    # -- Mouse events (uses world adapter hit-testing) ----------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._cell_layout is None or self._grid is None:
            return
        pos = self._world_adapter.pixel_to_grid(
            event.position().x(),
            event.position().y(),
            self._cell_layout,
        )
        if pos is None:
            return
        col, row = pos.x, pos.y
        # Check if click landed on agent
        if (self._agent is not None
                and row == self._agent.row
                and col == self._agent.col):
            self.agent_clicked.emit()
        else:
            self.cell_clicked.emit(row, col)

    # -- Resize event -------------------------------------------------------

    def resizeEvent(self, event) -> None:
        self._recompute_layout()
        super().resizeEvent(event)
