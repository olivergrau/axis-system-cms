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
        bar_chart_counts: dict[tuple[int, int], int] = {}
        for overlay in overlay_data_list:
            for item in overlay.items:
                if (
                    item.item_type == "bar_chart"
                    and item.data.get("layout_mode") == "stack"
                ):
                    pos = item.grid_position
                    bar_chart_counts[pos] = bar_chart_counts.get(pos, 0) + 1

        bar_chart_seen: dict[tuple[int, int], int] = {}
        for overlay in overlay_data_list:
            for item in overlay.items:
                if (
                    item.item_type == "bar_chart"
                    and item.data.get("layout_mode") == "stack"
                ):
                    pos = item.grid_position
                    stack_total = bar_chart_counts.get(pos, 1)
                    stack_index = bar_chart_seen.get(pos, 0)
                    bar_chart_seen[pos] = stack_index + 1
                    if (
                        stack_total > 1
                        and "height_fraction" not in item.data
                        and "y_offset_fraction" not in item.data
                    ):
                        item = item.model_copy(
                            update={
                                "data": {
                                    **item.data,
                                    "height_fraction": 1.0 / stack_total,
                                    "y_offset_fraction": stack_index / stack_total,
                                },
                            },
                        )
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
        baseline = item.data.get("baseline", None)
        segments = item.data.get("segments", [])

        bx, by, bw, bh = bbox
        n = len(values)
        if n == 0:
            return

        # Normalize values so the longest bar fills the available width.
        # An explicit max_value in data overrides auto-detection.
        max_value = item.data.get("max_value", None)
        signed_mode = baseline is not None or any(v < 0 for v in values)

        # Adaptive sizing: zoomed view has room for full labels on the left
        zoomed = bw >= 100
        font_size = 9 if zoomed else 7
        label_area = 0.4 if zoomed else 0.05
        height_fraction = item.data.get("height_fraction", 1.0)
        y_offset_fraction = item.data.get("y_offset_fraction", 0.0)

        chart_h = bh * 0.7 * height_fraction
        chart_y = by + bh * 0.15 + bh * 0.7 * y_offset_fraction
        bar_h = chart_h / n
        bar_x = bx + bw * label_area
        max_bar_w = bw * (1.0 - label_area - 0.05)
        y_start = chart_y

        painter.setFont(QFont("monospace", font_size))
        bar_color = item.data.get("bar_color", None)
        if bar_color is not None:
            bar_color = QColor(*bar_color)
        else:
            bar_color = QColor(100, 180, 255, 150)
        positive_bar_color = item.data.get("positive_bar_color", None)
        if positive_bar_color is not None:
            positive_bar_color = QColor(*positive_bar_color)
        negative_bar_color = item.data.get("negative_bar_color", None)
        if negative_bar_color is not None:
            negative_bar_color = QColor(*negative_bar_color)

        if signed_mode:
            if baseline is None:
                baseline = 0.0
            min_value = item.data.get("min_value", None)
            if min_value is None:
                min_value = min(values, default=baseline)
                min_value = min(min_value, baseline)
            if max_value is None:
                max_value = max(values, default=baseline)
                max_value = max(max_value, baseline)

            total_span = max(max_value - min_value, 1e-9)
            baseline_ratio = (baseline - min_value) / total_span
            baseline_ratio = max(0.0, min(1.0, baseline_ratio))
            baseline_x = bar_x + max_bar_w * baseline_ratio
            negative_width = max_bar_w * baseline_ratio
            positive_width = max_bar_w * (1.0 - baseline_ratio)
            negative_span = max(baseline - min_value, 1e-9)
            positive_span = max(max_value - baseline, 1e-9)
            painter.setPen(QPen(QColor(230, 230, 230, 120), 1.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawLine(
                QPointF(baseline_x, y_start - 1),
                QPointF(baseline_x, y_start + n * bar_h - bar_h * 0.2),
            )
        else:
            if max_value is None or max_value <= 0:
                max_value = max((abs(v) for v in values), default=1.0) or 1.0

        for i, val in enumerate(values):
            y = y_start + i * bar_h
            if signed_mode:
                delta = val - baseline
                if abs(delta) > 1e-12:
                    if delta >= 0:
                        normalized = min(delta / positive_span, 1.0)
                        w = normalized * positive_width
                        x = baseline_x
                        color = positive_bar_color or bar_color
                    else:
                        normalized = min(abs(delta) / negative_span, 1.0)
                        w = normalized * negative_width
                        x = baseline_x - w
                        color = negative_bar_color or bar_color
                    self._draw_bar_fill(
                        painter, QRectF(x, y, w, bar_h * 0.8), color,
                        segments[i] if i < len(segments) else None,
                    )
            else:
                normalized = abs(val) / max_value
                if normalized > 1e-12:
                    w = normalized * max_bar_w
                    self._draw_bar_fill(
                        painter, QRectF(bar_x, y, w, bar_h * 0.8), bar_color,
                        segments[i] if i < len(segments) else None,
                    )
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

    def _draw_bar_fill(
        self,
        painter: QPainter,
        rect: QRectF,
        default_color: QColor,
        segments: list[dict[str, object]] | None,
    ) -> None:
        """Draw a solid bar or optional segmented fill within a bar rect."""
        if rect.width() <= 0 or rect.height() <= 0:
            return

        if not segments:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(default_color)
            painter.drawRect(rect)
            return

        segment_specs = []
        for segment in segments:
            value = float(segment.get("value", 0.0))
            if value <= 1e-12:
                continue
            color_spec = segment.get("color", None)
            color = self._coerce_color(color_spec) or default_color
            segment_specs.append((value, color))

        if not segment_specs:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(default_color)
            painter.drawRect(rect)
            return

        total_value = sum(value for value, _ in segment_specs)
        x = rect.x()
        remaining_width = rect.width()
        for index, (value, color) in enumerate(segment_specs):
            if index == len(segment_specs) - 1:
                segment_width = remaining_width
            else:
                segment_width = rect.width() * (value / total_value)
                remaining_width -= segment_width
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRect(QRectF(x, rect.y(), segment_width, rect.height()))
            x += segment_width

    def _coerce_color(
        self, color_spec: object,
    ) -> QColor | None:
        """Convert `[r,g,b,a]` style color specs into QColor."""
        if isinstance(color_spec, QColor):
            return color_spec
        if isinstance(color_spec, (list, tuple)) and 3 <= len(color_spec) <= 4:
            return QColor(*color_spec)
        return None

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

    def _draw_modulation_cell(
        self, painter: QPainter, item: OverlayItem, layout: CellLayout,
    ) -> None:
        """Draw a green/red rectangle over a cell by modulation factor.

        Green (mu > 1) = reinforced, red (mu < 1) = suppressed.
        Alpha scales with distance from 1.0.
        """
        bbox = layout.cell_bounding_boxes.get(item.grid_position)
        if bbox is None:
            return

        mu = item.data.get("modulation_factor", 1.0)
        delta = mu - 1.0
        if abs(delta) < 0.01:
            return  # neutral, skip

        intensity = min(abs(delta), 1.0)
        if delta > 0:
            color = QColor(50, 220, 80, int(40 + 120 * intensity))
        else:
            color = QColor(220, 50, 50, int(40 + 120 * intensity))

        bx, by, bw, bh = bbox
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRect(QRectF(bx, by, bw, bh))

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
        "modulation_cell": _draw_modulation_cell,
    }
