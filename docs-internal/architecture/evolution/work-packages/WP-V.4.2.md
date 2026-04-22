# WP-V.4.2 Implementation Brief -- OverlayRenderer

## Context

In v0.1.0, overlay rendering lives inside `GridWidget` as three private methods: `_draw_overlay_action_preference` (direction arrows, consume dot, stay ring), `_draw_overlay_drive_contribution` (bar chart), and `_draw_overlay_consumption_opportunity` (diamond, neighbor dots, X markers). These are tightly coupled to System A's overlay data models (`ActionPreferenceOverlay`, `DriveContributionOverlay`, `ConsumptionOpportunityOverlay`).

In v0.2.0, overlay rendering is extracted into a dedicated `OverlayRenderer` that dispatches on `OverlayItem.item_type` strings. The renderer receives structured `OverlayData` (produced by any system adapter) and `CellLayout` (produced by any world adapter), and uses `QPainter` to draw. This is the only module besides `CanvasWidget` that uses QPainter.

### Predecessor State (After WP-V.4.1)

```
src/axis/visualization/
    ui/
        __init__.py
        canvas_widget.py                 # CanvasWidget with _draw_overlays stub
    ...
```

### Known item_type Values (from Architecture Spec Section 8.1)

| `item_type` | Rendering | Origin |
|---|---|---|
| `direction_arrow` | Line from cell center in direction, length proportional to value | System A action_preference, System B action_weights |
| `center_dot` | Filled circle at cell center | System A consume indicator |
| `center_ring` | Unfilled ring at cell center | System A stay indicator |
| `bar_chart` | Mini horizontal bars within cell bounds | System A drive_contribution |
| `diamond_marker` | Rotated square at center, opacity by resource | System A consumption_opportunity |
| `neighbor_dot` | Circle at a cell center, opacity by resource | System A consumption_opportunity |
| `x_marker` | Red X at center | System A non-traversable indicator |
| `radius_circle` | Circle around cell with given radius | System B scan_result |

### Reference Documents

- `docs/architecture/evolution/visualization-architecture.md` -- Section 8 (Overlay Rendering Pipeline)
- `docs/architecture/evolution/visualization-architecture-roadmap.md` -- WP-V.4.2

---

## Objective

Extract overlay rendering into a data-driven `OverlayRenderer` that dispatches on `item_type` strings, resolves grid positions to pixel coordinates via `CellLayout`, and draws with `QPainter`.

---

## Scope

### 1. OverlayRenderer

**File**: `src/axis/visualization/ui/overlay_renderer.py` (new)

```python
"""Data-driven overlay renderer.

Translates OverlayData + CellLayout into QPainter draw calls.
Dispatches on OverlayItem.item_type strings. This is the only
module besides CanvasWidget that uses QPainter for overlays.
"""

from __future__ import annotations

import math

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

        color = QColor(255, 200, 0) if is_selected else QColor(200, 200, 200, 180)
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

        color = QColor(255, 200, 0) if is_selected else QColor(200, 200, 200, 180)
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

        color = QColor(255, 200, 0) if is_selected else QColor(200, 200, 200, 180)
        painter.setPen(QPen(color, 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(*center), r, r)

    def _draw_bar_chart(
        self, painter: QPainter, item: OverlayItem, layout: CellLayout,
    ) -> None:
        """Draw mini horizontal bars within cell bounds."""
        bbox = layout.cell_bounding_boxes.get(item.grid_position)
        if bbox is None:
            return

        activation = item.data.get("activation", 0.0)
        values = item.data.get("values", [])
        labels = item.data.get("labels", [])

        bx, by, bw, bh = bbox
        n = len(values)
        if n == 0:
            return

        bar_h = bh * 0.7 / n
        max_bar_w = bw * 0.6
        y_start = by + bh * 0.15

        painter.setFont(QFont("monospace", 7))
        for i, val in enumerate(values):
            y = y_start + i * bar_h
            w = max(1.0, abs(val) * max_bar_w)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(100, 180, 255, 150))
            painter.drawRect(QRectF(bx + bw * 0.3, y, w, bar_h * 0.8))
            if i < len(labels):
                painter.setPen(QColor(220, 220, 220))
                painter.drawText(
                    QPointF(bx + 2, y + bar_h * 0.7), labels[i][:1],
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
        painter.setPen(QPen(QColor(100, 200, 255, 150), 1.5, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), radius_px, radius_px)

        if label:
            painter.setPen(QColor(200, 200, 200))
            painter.setFont(QFont("monospace", 8))
            painter.drawText(QPointF(cx + radius_px + 3, cy), label)

    # -- Dispatch table -----------------------------------------------------

    _RENDERERS: dict[str, ...] = {
        "direction_arrow": _draw_direction_arrow,
        "center_dot": _draw_center_dot,
        "center_ring": _draw_center_ring,
        "bar_chart": _draw_bar_chart,
        "diamond_marker": _draw_diamond_marker,
        "neighbor_dot": _draw_neighbor_dot,
        "x_marker": _draw_x_marker,
        "radius_circle": _draw_radius_circle,
    }
```

**Design notes**:

1. **Dispatch table**: `_RENDERERS` maps `item_type` strings to bound methods. Unknown item types are silently skipped (no crash for future extensions).

2. **Position resolution**: Each renderer reads `cell_layout.cell_centers[item.grid_position]` and optionally `cell_layout.cell_bounding_boxes[item.grid_position]`. Missing positions (e.g., out-of-bounds grid positions) cause the item to be silently skipped.

3. **Color choices**: Default colors match the v0.1.0 aesthetic. Selected items use gold `(255, 200, 0)`, unselected use translucent gray. These are reasonable defaults; the renderer does not need adapter-configurable colors.

4. **New `radius_circle`**: Not in v0.1.0. Draws a dashed circle centered on the agent cell, radius in grid cell units (converted to pixels via `canvas_width / grid_width`). Used by System B's scan_result overlay.

5. **Stateless**: The renderer holds no state. All rendering parameters come from `OverlayItem.data` and `CellLayout`.

### 2. Wire into CanvasWidget

After implementing the `OverlayRenderer`, update `CanvasWidget.__init__()` to create and inject it:

```python
# In canvas_widget.py constructor:
from axis.visualization.ui.overlay_renderer import OverlayRenderer

self._overlay_renderer = OverlayRenderer()
```

Remove the `set_overlay_renderer()` provisional injection method.

---

## Out of Scope

- UI panels (WP-V.4.3)
- Session controller and signal wiring (WP-V.4.4)
- New overlay item types beyond the 8 listed
- Overlay color configuration (colors are hard-coded defaults)

---

## Architectural Constraints

### 1. QPainter Boundary

This module plus `CanvasWidget` are the ONLY modules that use `QPainter`. Everything above (adapters, view model builder, viewer state) works with structured data.

### 2. Item Type Extensibility

Adding a new `item_type` requires only adding a new `_draw_*` method and a dispatch table entry. No changes to the renderer interface, no changes to the adapter protocol.

### 3. Graceful Unknown Type Handling

Unknown `item_type` values are silently skipped. This prevents crashes when a newer system adapter produces overlay items that an older renderer doesn't know about.

### 4. Position Resolution via CellLayout

The renderer resolves `grid_position` to pixels through `CellLayout`. It never computes cell geometry directly. This ensures overlays render correctly on any grid geometry.

---

## Testing Requirements

**File**: `tests/visualization/test_overlay_renderer.py` (new)

Testing QPainter calls is inherently tricky. The recommended approach is to use a mock or recording QPainter, or to test the dispatch logic separately from the actual drawing.

### Dispatch tests

1. **`test_render_dispatches_direction_arrow`**: Pass 1 overlay item with `item_type="direction_arrow"`, assert `_draw_direction_arrow` is called
2. **`test_render_dispatches_all_known_types`**: Pass 8 items (one per type), assert all 8 renderers called
3. **`test_render_skips_unknown_type`**: Pass item with `item_type="unknown_future_type"`, assert no crash, no call

### Position resolution tests

4. **`test_renderer_reads_cell_centers`**: Provide a `CellLayout` with known centers, pass a `direction_arrow` item at a known grid position, assert the renderer reads the correct center coordinates
5. **`test_renderer_skips_missing_position`**: Item at grid position not in `CellLayout`, assert gracefully skipped

### Integration tests (with QPixmap)

6. **`test_render_direction_arrow_no_crash`**: Create a QPixmap, get QPainter, render a `direction_arrow` item, assert no exception
7. **`test_render_center_dot_no_crash`**: Same for `center_dot`
8. **`test_render_bar_chart_no_crash`**: Same for `bar_chart` with 6 values
9. **`test_render_radius_circle_no_crash`**: Same for `radius_circle`
10. **`test_render_x_marker_no_crash`**: Same for `x_marker`
11. **`test_render_diamond_marker_no_crash`**: Same for `diamond_marker`

### Overlay filtering tests

12. **`test_render_multiple_overlays`**: Pass 2 `OverlayData` objects with multiple items each, assert all rendered
13. **`test_render_empty_overlay_list`**: Pass empty tuple, assert no crash

### Selected action highlight tests

14. **`test_direction_arrow_selected_color`**: Item with `is_selected=True`, verify different color used (if using recording painter)
15. **`test_center_dot_selected`**: Same for center_dot

---

## Expected Deliverable

1. `src/axis/visualization/ui/overlay_renderer.py`
2. Update `src/axis/visualization/ui/canvas_widget.py` to import and use `OverlayRenderer`
3. `tests/visualization/test_overlay_renderer.py`
4. Confirmation that all existing tests still pass

---

## Expected File Structure

```
src/axis/visualization/
    ui/
        __init__.py                      # UNCHANGED (WP-V.4.1)
        canvas_widget.py                 # MODIFIED (import OverlayRenderer)
        overlay_renderer.py              # NEW

tests/visualization/
    test_overlay_renderer.py             # NEW
```

---

## Important Final Constraint

The renderer is approximately 200-250 lines. Each `_draw_*` method is 15-25 lines. The dispatch table pattern keeps the module clean and extensible. Resist the urge to over-engineer the rendering (alpha blending, line caps, anti-aliasing configuration) -- match the v0.1.0 visual quality, which is functional rather than polished.
