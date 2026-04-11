"""Zoomed rendering of the agent's cell with overlays.

Draws a single grid cell at larger scale so overlay details
(arrows, bars, rings) are legible in the detail panel.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from axis.visualization.types import (
    CellColorConfig,
    CellLayout,
    CellShape,
    OverlayData,
    OverlayItem,
)
from axis.visualization.ui.overlay_renderer import OverlayRenderer
from axis.visualization.view_models import AgentViewModel, GridCellViewModel


class AgentCellZoomWidget(QWidget):
    """Renders the agent's cell at zoomed scale with all overlays."""

    def __init__(
        self,
        cell_color_config: CellColorConfig,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._color_config = cell_color_config
        self._overlay_renderer = OverlayRenderer()

        self._cell: GridCellViewModel | None = None
        self._agent: AgentViewModel | None = None
        self._overlay_data: tuple[OverlayData, ...] = ()

        self.setFixedHeight(150)

    def set_data(
        self,
        cell: GridCellViewModel | None,
        agent: AgentViewModel | None,
        overlay_data: tuple[OverlayData, ...],
    ) -> None:
        """Update cell, agent, and overlay data, then repaint."""
        self._cell = cell
        self._agent = agent
        self._overlay_data = overlay_data
        self.update()

    # -- Painting --------------------------------------------------------------

    def paintEvent(self, event: QPaintEvent) -> None:
        if self._cell is None or self._agent is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        try:
            side = min(self.width(), self.height())
            ox = (self.width() - side) / 2.0
            oy = (self.height() - side) / 2.0
            layout = self._synthetic_layout(
                self._agent.col, self._agent.row, ox, oy, side,
            )
            # Clip to the cell area so overlays like radius_circle
            # don't bleed outside the widget.
            painter.setClipRect(QRectF(ox, oy, side, side))
            self._draw_cell_background(painter, layout)
            self._draw_agent_marker(painter, layout)
            self._draw_overlays(painter, layout)
        finally:
            painter.end()

    def _synthetic_layout(
        self, col: int, row: int, ox: float, oy: float, side: float,
    ) -> CellLayout:
        """Build a 1x1 CellLayout mapping (col, row) to the widget area."""
        key = (col, row)
        return CellLayout(
            cell_shape=CellShape.RECTANGULAR,
            grid_width=1,
            grid_height=1,
            canvas_width=side,
            canvas_height=side,
            cell_polygons={key: (
                (ox, oy), (ox + side, oy),
                (ox + side, oy + side), (ox, oy + side),
            )},
            cell_centers={key: (ox + side / 2.0, oy + side / 2.0)},
            cell_bounding_boxes={key: (ox, oy, side, side)},
        )

    def _draw_cell_background(
        self, painter: QPainter, layout: CellLayout,
    ) -> None:
        cc = self._color_config
        cell = self._cell
        assert cell is not None
        if cell.is_obstacle:
            color = cc.obstacle_color
        elif cell.resource_value <= 0.0:
            color = cc.empty_color
        else:
            t = min(1.0, max(0.0, cell.resource_value))
            color = tuple(
                int(cc.resource_color_min[i]
                    + t * (cc.resource_color_max[i] - cc.resource_color_min[i]))
                for i in range(3)
            )
        key = next(iter(layout.cell_polygons))
        bbox = layout.cell_bounding_boxes[key]
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(*color)))
        painter.drawRect(int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3]))

    def _draw_agent_marker(
        self, painter: QPainter, layout: CellLayout,
    ) -> None:
        assert self._agent is not None
        key = (self._agent.col, self._agent.row)
        center = layout.cell_centers[key]
        bbox = layout.cell_bounding_boxes[key]
        radius = min(bbox[2], bbox[3]) * 0.3
        if self._agent.is_selected:
            color = self._color_config.agent_selected_color
        else:
            color = self._color_config.agent_color
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(*color)))
        painter.drawEllipse(QPointF(*center), radius, radius)

    def _draw_overlays(
        self, painter: QPainter, layout: CellLayout,
    ) -> None:
        if not self._overlay_data:
            return
        agent_key = (self._agent.col, self._agent.row)
        filtered: list[OverlayData] = []
        for od in self._overlay_data:
            items = tuple(
                item for item in od.items
                if item.grid_position == agent_key
            )
            if items:
                filtered.append(OverlayData(
                    overlay_type=od.overlay_type, items=items,
                ))
        if filtered:
            self._overlay_renderer.render(painter, tuple(filtered), layout)
