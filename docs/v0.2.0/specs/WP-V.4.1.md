# WP-V.4.1 Implementation Brief -- CanvasWidget

## Context

The v0.1.0 `GridWidget` is a 407-line PySide6 widget that hard-codes rectangular cell geometry (`_cell_rect`), fixed green resource colors (`_resource_color`), three System A overlay renderers, and direct `CellType` enum access. In v0.2.0, all geometry and coloring is delegated to the world adapter via `CellLayout` and `CellColorConfig`, and overlay rendering is extracted to a dedicated `OverlayRenderer` (WP-V.4.2).

### Predecessor State (After Phase V-3)

```
src/axis/visualization/
    __init__.py
    types.py                             # CellLayout, CellColorConfig, TopologyIndicator, etc.
    protocols.py
    registry.py
    errors.py
    replay_models.py
    replay_validation.py
    replay_access.py
    snapshot_models.py
    snapshot_resolver.py
    viewer_state.py
    viewer_state_transitions.py
    playback_controller.py
    view_models.py                       # GridViewModel, AgentViewModel, etc.
    view_model_builder.py
    adapters/
        default_world.py
        null_system.py
```

### v0.1.0 Source File Being Migrated

| v0.1.0 file | v0.2.0 destination | Changes |
|---|---|---|
| `axis_system_a/visualization/ui/grid_widget.py` | `axis/visualization/ui/canvas_widget.py` | Remove `_cell_rect`, delegate to CellLayout; remove `_resource_color`, delegate to CellColorConfig; extract overlay drawing to OverlayRenderer; remove CellType/DebugOverlayViewModel imports |

### Reference Documents

- `docs/v0.2.0/architecture/evolution/visualization-architecture.md` -- Section 10 (CanvasWidget Design)
- `docs/v0.2.0/architecture/evolution/visualization-architecture-roadmap.md` -- WP-V.4.1

---

## Objective

Implement `CanvasWidget` that delegates all cell geometry to the world adapter via `CellLayout`, all cell coloring to `CellColorConfig`, hit-testing to `pixel_to_grid()`, and overlay rendering to `OverlayRenderer`.

---

## Scope

### 1. CanvasWidget

**File**: `src/axis/visualization/ui/canvas_widget.py` (new)

```python
"""World-adapter-aware canvas for rendering the world grid.

Replaces v0.1.0's GridWidget. All geometry and coloring is delegated
to the world adapter via CellLayout and CellColorConfig.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
)
from PySide6.QtWidgets import QWidget

from axis.visualization.types import (
    CellColorConfig,
    CellLayout,
    TopologyIndicator,
)
from axis.visualization.view_models import (
    AgentViewModel,
    GridCellViewModel,
    GridViewModel,
    SelectionViewModel,
)


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

        # OverlayRenderer injected later (WP-V.4.2)
        self._overlay_renderer: Any = None

        self.setMinimumSize(200, 200)

    def set_overlay_renderer(self, renderer: Any) -> None:
        """Inject the overlay renderer (WP-V.4.2)."""
        self._overlay_renderer = renderer

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
            self.width(),
            self.height(),
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
        ...
        # For each cell in self._grid.cells:
        #   polygon = self._cell_layout.cell_polygons[(cell.col, cell.row)]
        #   color = self._resolve_cell_color(cell)
        #   painter.setBrush(QBrush(QColor(*color)))
        #   painter.setPen(Qt.PenStyle.NoPen)
        #   painter.drawPolygon(polygon_to_qpolygon(polygon))

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
        r = int(cc.resource_color_min[0] + t * (cc.resource_color_max[0] - cc.resource_color_min[0]))
        g = int(cc.resource_color_min[1] + t * (cc.resource_color_max[1] - cc.resource_color_min[1]))
        b = int(cc.resource_color_min[2] + t * (cc.resource_color_max[2] - cc.resource_color_min[2]))
        return (r, g, b)

    def _draw_grid_lines(self, painter: QPainter) -> None:
        """Draw grid lines along polygon edges."""
        ...
        # painter.setPen(QPen(QColor(*self._cell_color_config.grid_line_color), 1))
        # For each cell, draw polygon edges

    def _draw_topology_indicators(self, painter: QPainter) -> None:
        """Draw topology indicators (wrap edges, hotspot markers)."""
        ...
        # For each indicator in self._topology_indicators:
        #   Dispatch on indicator.indicator_type:
        #     "wrap_edge" -> draw dashed line at indicator.position
        #     "hotspot_center" -> draw marker at indicator.position

    def _draw_selection(self, painter: QPainter) -> None:
        """Draw selection highlight using CellLayout polygon."""
        ...
        # if selection has a selected cell:
        #   polygon = self._cell_layout.cell_polygons[(col, row)]
        #   draw orange border around polygon

    def _draw_agent(self, painter: QPainter) -> None:
        """Draw agent marker at CellLayout cell center."""
        ...
        # center = self._cell_layout.cell_centers[(agent.col, agent.row)]
        # bbox = self._cell_layout.cell_bounding_boxes[(agent.col, agent.row)]
        # Draw filled ellipse at center

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
```

**Key design decisions**:

1. **No `_cell_rect()` method**: All geometry comes from `CellLayout.cell_polygons`, `cell_centers`, and `cell_bounding_boxes`. This works for rectangular, hexagonal, or any future cell shape.

2. **Color resolution method**: `_resolve_cell_color()` implements linear RGB interpolation using `CellColorConfig`. This replaces the v0.1.0 module-level `_resource_color()` function and the `CellType`-based switch.

3. **Topology indicator rendering**: New in v0.2.0 -- the canvas draws topology indicators (wrap edges for toroidal, hotspot markers for signal landscape) between grid lines and selection highlight.

4. **Overlay delegation**: The canvas does not contain overlay drawing code. It calls `self._overlay_renderer.render()` (injected from WP-V.4.2). During WP-V.4.1, `_overlay_renderer` is `None` and overlays are skipped.

5. **Hit-testing delegation**: `mousePressEvent` calls `self._world_adapter.pixel_to_grid()` instead of computing `int(px / cell_w)` directly. This supports non-rectangular grids.

6. **`set_frame` signature**: Takes `GridViewModel`, `AgentViewModel`, `SelectionViewModel`, `overlay_data` tuple, and `topology_indicators` tuple. This replaces the v0.1.0 signature that took `DebugOverlayViewModel`.

### 2. Topology Indicator Rendering

The topology indicator renderer dispatches on `indicator.indicator_type`:

| `indicator_type` | Rendering |
|---|---|
| `"wrap_edge"` | Dashed line at `indicator.position` along the grid edge. `data["edge"]` indicates which edge ("left", "right", "top", "bottom"). `data["style"]` is "dashed". |
| `"hotspot_center"` | Crosshair or circle at `indicator.position`. `data["radius_pixels"]` determines size. `data["intensity"]` determines opacity. `data["label"]` text shown near marker. |

This is a simple `if/elif` dispatch -- not complex enough to warrant a separate renderer class.

### 3. Helper: Polygon to QPolygon

```python
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPolygonF


def _polygon_to_qpolygon(
    vertices: tuple[tuple[float, float], ...],
) -> QPolygonF:
    """Convert a tuple of (x, y) vertices to a QPolygonF."""
    return QPolygonF([QPointF(x, y) for x, y in vertices])
```

This utility function is private to the module.

---

## Out of Scope

- Overlay rendering logic (WP-V.4.2 -- `OverlayRenderer`)
- UI panels (WP-V.4.3)
- Signal wiring and session controller (WP-V.4.4)
- Keyboard shortcuts
- Zoom/pan functionality

---

## Architectural Constraints

### 1. No Cell Geometry Computation

The canvas never computes cell positions itself. It reads `CellLayout.cell_polygons`, `cell_centers`, and `cell_bounding_boxes` from the world adapter. On resize, it calls `world_adapter.cell_layout()` to get a new layout.

### 2. No System-Specific Code

The canvas has no knowledge of System A, System B, or any system type. It renders `GridCellViewModel` cells, an `AgentViewModel` marker, and passes `OverlayData` to the renderer.

### 3. No CellType Enum

The v0.1.0 `GridWidget` imports `CellType` and branches on `CellType.OBSTACLE` vs `CellType.FLOOR`. The v0.2.0 `CanvasWidget` uses `GridCellViewModel.is_obstacle` and `is_traversable` booleans, plus `resource_value` for color interpolation.

### 4. QPainter Only in This Module

The canvas owns the `QPainter` lifecycle. All drawing happens in `paintEvent()`. The `OverlayRenderer` receives the `QPainter` as a parameter -- it does not create its own.

---

## Testing Requirements

**File**: `tests/v02/visualization/test_canvas_widget.py` (new)

PySide6 widget tests require a `QApplication` instance. Use a session-scoped fixture.

### Construction tests

1. **`test_canvas_construction`**: Create `CanvasWidget(world_adapter)`, assert minimum size set, no crash
2. **`test_canvas_cell_color_config_from_adapter`**: Assert `_cell_color_config` matches adapter's `cell_color_config()`

### Color resolution tests (can be tested without QPainter)

3. **`test_resolve_cell_color_obstacle`**: `is_obstacle=True` → `obstacle_color`
4. **`test_resolve_cell_color_empty`**: `resource_value=0.0` → `empty_color`
5. **`test_resolve_cell_color_full_resource`**: `resource_value=1.0` → `resource_color_max`
6. **`test_resolve_cell_color_half_resource`**: `resource_value=0.5` → midpoint between min and max
7. **`test_resolve_cell_color_clamped`**: `resource_value=1.5` → `resource_color_max` (clamped)

### Layout tests

8. **`test_recompute_layout_on_set_frame`**: Assert `_cell_layout` is set after first `set_frame()`
9. **`test_layout_recomputed_on_resize`**: Resize widget, assert `_cell_layout` updated

### Hit-testing tests

10. **`test_mouse_click_emits_cell_clicked`**: Simulate click at known position, assert `cell_clicked` emitted with correct (row, col)
11. **`test_mouse_click_on_agent_emits_agent_clicked`**: Click on agent position, assert `agent_clicked` emitted
12. **`test_mouse_click_out_of_bounds`**: Click outside grid, assert no signal emitted

### Frame update tests

13. **`test_set_frame_stores_data`**: After `set_frame()`, assert internal state matches
14. **`test_set_frame_triggers_update`**: Assert `update()` called (mock or flag)

### Topology indicator tests

15. **`test_topology_indicators_stored`**: Pass topology indicators to `set_frame()`, assert stored

### Painting tests (smoke tests)

16. **`test_paint_event_no_crash`**: Call `repaint()` with valid frame data, assert no exception
17. **`test_paint_event_without_frame`**: Call `repaint()` before `set_frame()`, assert no crash

---

## Expected Deliverable

1. `src/axis/visualization/ui/__init__.py` (new, empty)
2. `src/axis/visualization/ui/canvas_widget.py`
3. `tests/v02/visualization/test_canvas_widget.py`
4. Confirmation that all existing tests still pass

---

## Expected File Structure

```
src/axis/visualization/
    ui/
        __init__.py                      # NEW (empty)
        canvas_widget.py                 # NEW

tests/v02/visualization/
    test_canvas_widget.py                # NEW
```

---

## Important Final Constraint

The canvas is approximately 250-300 lines. The v0.1.0 `GridWidget` was 407 lines because it contained all overlay drawing code inline -- that is now extracted to `OverlayRenderer` (WP-V.4.2). The canvas is lighter: it delegates geometry, coloring, hit-testing, and overlay rendering. Its only custom logic is `_resolve_cell_color()` (linear interpolation), `_draw_topology_indicators()` (type dispatch to 2 renderers), and the `QPainter` lifecycle.
