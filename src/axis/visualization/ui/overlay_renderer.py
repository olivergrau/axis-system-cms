"""Data-driven overlay renderer.

Translates OverlayData + CellLayout into QPainter draw calls.
Dispatches on OverlayItem.item_type strings. This is the only
module besides CanvasWidget that uses QPainter for overlays.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen

from axis.visualization.types import CellLayout, OverlayData, OverlayItem


# Direction deltas for arrow rendering (grid coordinates)
_DIRECTION_DELTAS: dict[str, tuple[float, float]] = {
    "up": (0.0, -1.0),
    "down": (0.0, 1.0),
    "left": (-1.0, 0.0),
    "right": (1.0, 0.0),
}


class OverlayRenderer:
    """Renders overlay items by dispatching on item_type.

    Stateless -- all rendering parameters come from the OverlayItem's
    data dict and the CellLayout's pixel geometry.
    """

    def render(
        self,
        painter: QPainter,
        overlay_data_list: tuple[OverlayData, ...],
        cell_layout: CellLayout,
    ) -> None:
        """Render all overlay items from all active overlays."""
        for overlay in overlay_data_list:
            for item in overlay.items:
                self._render_item(painter, item, cell_layout)

    def _render_item(
        self,
        painter: QPainter,
        item: OverlayItem,
        cell_layout: CellLayout,
    ) -> None:
        """Dispatch to the appropriate renderer based on item_type."""
        renderer = self._RENDERERS.get(item.item_type)
        if renderer is not None:
            renderer(self, painter, item, cell_layout)

    # -- Item renderers -----------------------------------------------------

    def _draw_direction_arrow(
        self, painter: QPainter, item: OverlayItem, layout: CellLayout,
    ) -> None:
        """Draw an arrow from cell center in the specified direction."""
        center = layout.cell_centers.get(item.grid_position)
        bbox = layout.cell_bounding_boxes.get(item.grid_position)
        if center is None or bbox is None:
            return

        direction = item.data.get("direction", "up")
        length = item.data.get("length", 0.0)
        is_selected = item.data.get("is_selected", False)

        dx, dy = _DIRECTION_DELTAS.get(direction, (0.0, 0.0))
        cell_w, cell_h = bbox[2], bbox[3]
        scale = min(cell_w, cell_h) * 0.4 * length

        cx, cy = center
        ex, ey = cx + dx * scale, cy + dy * scale

        color = QColor(255, 200, 0) if is_selected else QColor(
            200, 200, 200, 180)
        painter.setPen(QPen(color, 2.0))
        painter.drawLine(QPointF(cx, cy), QPointF(ex, ey))

    def _draw_center_dot(
        self, painter: QPainter, item: OverlayItem, layout: CellLayout,
    ) -> None:
        """Draw a filled circle at cell center (consume indicator)."""
        center = layout.cell_centers.get(item.grid_position)
        if center is None:
            return

        radius = item.data.get("radius", 0.1)
        is_selected = item.data.get("is_selected", False)
        r = max(3.0, radius * 20.0)

        color = QColor(255, 200, 0) if is_selected else QColor(
            200, 200, 200, 180)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(QPointF(*center), r, r)

    def _draw_center_ring(
        self, painter: QPainter, item: OverlayItem, layout: CellLayout,
    ) -> None:
        """Draw an unfilled ring at cell center (stay indicator)."""
        center = layout.cell_centers.get(item.grid_position)
        if center is None:
            return

        radius = item.data.get("radius", 0.1)
        is_selected = item.data.get("is_selected", False)
        r = max(4.0, radius * 20.0)

        color = QColor(255, 200, 0) if is_selected else QColor(
            200, 200, 200, 180)
        painter.setPen(QPen(color, 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(*center), r, r)

    def _draw_bar_chart(
        self, painter: QPainter, item: OverlayItem, layout: CellLayout,
    ) -> None:
        """Draw horizontal bars with labels within cell bounds.

        In the zoomed view (cell width >= 100px) full action names are
        shown to the left of bars.  In the small grid view, single-letter
        labels are drawn inside each bar for readability.
        """
        bbox = layout.cell_bounding_boxes.get(item.grid_position)
        if bbox is None:
            return

        values = item.data.get("values", [])
        labels = item.data.get("labels", [])

        bx, by, bw, bh = bbox
        n = len(values)
        if n == 0:
            return

        # Adaptive sizing: zoomed view has room for full labels on the left
        zoomed = bw >= 100
        font_size = 9 if zoomed else 7
        label_area = 0.4 if zoomed else 0.05

        bar_h = bh * 0.7 / n
        bar_x = bx + bw * label_area
        max_bar_w = bw * (1.0 - label_area - 0.05)
        y_start = by + bh * 0.15

        painter.setFont(QFont("monospace", font_size))
        bar_color = QColor(100, 180, 255, 150)
        for i, val in enumerate(values):
            y = y_start + i * bar_h
            w = max(1.0, abs(val) * max_bar_w)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bar_color)
            painter.drawRect(QRectF(bar_x, y, w, bar_h * 0.8))
            if i < len(labels):
                if zoomed:
                    # Dark backdrop behind label for contrast
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QColor(0, 0, 0, 140))
                    painter.drawRect(QRectF(
                        bx, y, bw * label_area - 2, bar_h * 0.8,
                    ))
                    # Full label on the backdrop
                    painter.setPen(QColor(255, 255, 255))
                    painter.drawText(
                        QPointF(bx + 3, y + bar_h * 0.7), labels[i],
                    )
                else:
                    # Single letter inside the bar for contrast
                    painter.setPen(QColor(255, 255, 255))
                    painter.drawText(
                        QPointF(bar_x + 2, y + bar_h * 0.7),
                        labels[i][:1].upper(),
                    )

    def _draw_diamond_marker(
        self, painter: QPainter, item: OverlayItem, layout: CellLayout,
    ) -> None:
        """Draw a rotated square at cell center."""
        center = layout.cell_centers.get(item.grid_position)
        if center is None:
            return

        opacity = item.data.get("opacity", 0.5)
        cx, cy = center
        s = 6.0

        color = QColor(255, 220, 0, int(opacity * 200))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(45)
        painter.drawRect(QRectF(-s / 2, -s / 2, s, s))
        painter.restore()

    def _draw_neighbor_dot(
        self, painter: QPainter, item: OverlayItem, layout: CellLayout,
    ) -> None:
        """Draw a circle at a cell center, opacity by resource."""
        center = layout.cell_centers.get(item.grid_position)
        if center is None:
            return

        resource = item.data.get("resource_value", 0.0)
        r = 4.0

        color = QColor(100, 255, 100, int(resource * 200))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(QPointF(*center), r, r)

    def _draw_x_marker(
        self, painter: QPainter, item: OverlayItem, layout: CellLayout,
    ) -> None:
        """Draw a red X at cell center."""
        center = layout.cell_centers.get(item.grid_position)
        if center is None:
            return

        cx, cy = center
        s = 5.0

        painter.setPen(QPen(QColor(255, 80, 80, 200), 2.0))
        painter.drawLine(QPointF(cx - s, cy - s), QPointF(cx + s, cy + s))
        painter.drawLine(QPointF(cx - s, cy + s), QPointF(cx + s, cy - s))

    def _draw_radius_circle(
        self, painter: QPainter, item: OverlayItem, layout: CellLayout,
    ) -> None:
        """Draw a circle around cell with given radius in grid cells."""
        center = layout.cell_centers.get(item.grid_position)
        if center is None:
            return

        radius_cells = item.data.get("radius_cells", 1)
        label = item.data.get("label", "")

        # Convert radius from grid cells to pixels
        cell_w = layout.canvas_width / layout.grid_width
        radius_px = radius_cells * cell_w

        cx, cy = center
        # Dark halo under bright cyan ring for better contrast.
        painter.setPen(QPen(QColor(10, 20, 30, 200),
                       2.5, Qt.PenStyle.SolidLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), radius_px, radius_px)

        painter.setPen(QPen(QColor(110, 220, 255, 210),
                       1.5, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), radius_px, radius_px)

        if label:
            painter.setPen(QColor(5, 5, 5, 230))
            painter.setFont(QFont("monospace", 8))
            text_pos = QPointF(cx + radius_px + 3, cy)
            painter.drawText(
                QPointF(text_pos.x() + 1, text_pos.y() + 1), label)
            painter.setPen(QColor(230, 240, 250, 245))
            painter.drawText(text_pos, label)

    def _draw_heatmap_cell(
        self, painter: QPainter, item: OverlayItem, layout: CellLayout,
    ) -> None:
        """Draw a colored rectangle over a cell, intensity by visit count."""
        bbox = layout.cell_bounding_boxes.get(item.grid_position)
        if bbox is None:
            return

        visit_count = item.data.get("visit_count", 0)
        # Intensity decays with visits: high visits = warm color
        intensity = 1.0 - 1.0 / (1 + visit_count)

        r = int(255 * intensity)
        g = int(100 * (1 - intensity))
        b = 50
        alpha = int(80 + 120 * intensity)

        bx, by, bw, bh = bbox
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(r, g, b, alpha))
        painter.drawRect(QRectF(bx, by, bw, bh))

        # Draw visit count text
        if visit_count > 0:
            painter.setPen(QColor(255, 255, 255, 200))
            painter.setFont(QFont("monospace", 8))
            painter.drawText(
                QRectF(bx, by, bw, bh),
                Qt.AlignmentFlag.AlignCenter,
                str(visit_count),
            )

    def _draw_novelty_arrow(
        self, painter: QPainter, item: OverlayItem, layout: CellLayout,
    ) -> None:
        """Draw a novelty indicator arrow from cell center."""
        center = layout.cell_centers.get(item.grid_position)
        bbox = layout.cell_bounding_boxes.get(item.grid_position)
        if center is None or bbox is None:
            return

        direction = item.data.get("direction", "up")
        length = item.data.get("length", 0.0)

        dx, dy = _DIRECTION_DELTAS.get(direction, (0.0, 0.0))
        cell_w, cell_h = bbox[2], bbox[3]
        scale = min(cell_w, cell_h) * 0.4 * length

        cx, cy = center
        ex, ey = cx + dx * scale, cy + dy * scale

        # Green-tinted arrows for novelty
        alpha = int(80 + 175 * length)
        color = QColor(100, 255, 150, min(alpha, 255))
        painter.setPen(QPen(color, 2.0))
        painter.drawLine(QPointF(cx, cy), QPointF(ex, ey))

    def _draw_saturation_ring(
        self, painter: QPainter, item: OverlayItem, layout: CellLayout,
    ) -> None:
        """Draw a colored ring encoding observation buffer saturation.

        Color interpolates blue (low resource) to green (high resource).
        Line width scales with buffer fill ratio.
        """
        center = layout.cell_centers.get(item.grid_position)
        bbox = layout.cell_bounding_boxes.get(item.grid_position)
        if center is None or bbox is None:
            return

        saturation = item.data.get("saturation", 0.0)
        fill_ratio = item.data.get("fill_ratio", 0.0)

        # Ring radius: slightly larger than other overlays
        cell_w, cell_h = bbox[2], bbox[3]
        r = min(cell_w, cell_h) * 0.38

        # Color: blue (low sat) → green (high sat)
        red = int(80 * (1 - saturation))
        green = int(80 + 175 * saturation)
        blue = int(255 * (1 - saturation))
        alpha = int(120 + 135 * fill_ratio)
        color = QColor(red, green, blue, min(alpha, 255))

        # Width: thicker when buffer is fuller
        width = 1.0 + 2.5 * fill_ratio

        painter.setPen(QPen(color, width))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(*center), r, r)

    # -- Dispatch table -----------------------------------------------------

    _RENDERERS: dict = {
        "direction_arrow": _draw_direction_arrow,
        "center_dot": _draw_center_dot,
        "center_ring": _draw_center_ring,
        "bar_chart": _draw_bar_chart,
        "diamond_marker": _draw_diamond_marker,
        "neighbor_dot": _draw_neighbor_dot,
        "x_marker": _draw_x_marker,
        "radius_circle": _draw_radius_circle,
        "heatmap_cell": _draw_heatmap_cell,
        "novelty_arrow": _draw_novelty_arrow,
        "saturation_ring": _draw_saturation_ring,
    }
