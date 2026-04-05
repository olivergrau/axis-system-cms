"""Grid rendering widget (VWP6/VWP7).

Custom ``QWidget`` with ``paintEvent`` that renders the world grid,
agent position, and selection highlight from VWP5 view models.
VWP7 adds mouse interaction signals.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QMouseEvent, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from axis_system_a.enums import CellType
from axis_system_a.visualization.debug_overlay_models import (
    ActionPreferenceOverlay,
    ConsumptionOpportunityOverlay,
    DebugOverlayViewModel,
    DriveContributionOverlay,
)
from axis_system_a.visualization.view_models import (
    AgentViewModel,
    GridViewModel,
    SelectionType,
    SelectionViewModel,
)

# ---------------------------------------------------------------------------
# Color constants
# ---------------------------------------------------------------------------

COLOR_EMPTY = QColor(0xE0, 0xE0, 0xE0)
COLOR_OBSTACLE = QColor(0x40, 0x40, 0x40)
COLOR_RESOURCE_MIN = QColor(0xE8, 0xF5, 0xE9)
COLOR_RESOURCE_MAX = QColor(0x2E, 0x7D, 0x32)
COLOR_AGENT = QColor(0x21, 0x96, 0xF3)
COLOR_AGENT_SELECTED = QColor(0x0D, 0x47, 0xA1)
COLOR_SELECTION_BORDER = QColor(0xFF, 0xA0, 0x00)
COLOR_GRID_LINE = QColor(0x9E, 0x9E, 0x9E)


def _resource_color(value: float) -> QColor:
    """Linear RGB interpolation between pale and saturated green."""
    t = max(0.0, min(1.0, value))
    r = int(COLOR_RESOURCE_MIN.red() +
            (COLOR_RESOURCE_MAX.red() - COLOR_RESOURCE_MIN.red()) * t)
    g = int(COLOR_RESOURCE_MIN.green() +
            (COLOR_RESOURCE_MAX.green() - COLOR_RESOURCE_MIN.green()) * t)
    b = int(COLOR_RESOURCE_MIN.blue() +
            (COLOR_RESOURCE_MAX.blue() - COLOR_RESOURCE_MIN.blue()) * t)
    return QColor(r, g, b)


class GridWidget(QWidget):
    """Renders the world grid from view model data."""

    cell_clicked = Signal(int, int)
    agent_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._grid: GridViewModel | None = None
        self._agent: AgentViewModel | None = None
        self._selection: SelectionViewModel | None = None
        self._overlay: DebugOverlayViewModel | None = None

    def set_frame(
        self,
        grid: GridViewModel,
        agent: AgentViewModel,
        selection: SelectionViewModel,
        overlay: DebugOverlayViewModel | None = None,
    ) -> None:
        """Store view model data and schedule a repaint."""
        self._grid = grid
        self._agent = agent
        self._selection = selection
        self._overlay = overlay
        self.update()

    # -- Geometry helpers ---------------------------------------------------

    def _cell_rect(
        self, row: int, col: int, cell_w: float, cell_h: float,
    ) -> tuple[float, float, float, float]:
        """Return (x, y, w, h) in widget pixels for the given cell."""
        return (col * cell_w, row * cell_h, cell_w, cell_h)

    # -- Paint --------------------------------------------------------------

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        if self._grid is None:
            return
        if self.width() == 0 or self.height() == 0:
            return

        cell_w = self.width() / self._grid.width
        cell_h = self.height() / self._grid.height

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self._draw_cells(painter, cell_w, cell_h)
        self._draw_grid_lines(painter, cell_w, cell_h)
        self._draw_overlays(painter, cell_w, cell_h)
        self._draw_selection(painter, cell_w, cell_h)
        self._draw_agent(painter, cell_w, cell_h)

        painter.end()

    def _draw_cells(
        self, painter: QPainter, cell_w: float, cell_h: float,
    ) -> None:
        assert self._grid is not None
        painter.setPen(Qt.PenStyle.NoPen)
        for cell in self._grid.cells:
            x, y, w, h = self._cell_rect(cell.row, cell.col, cell_w, cell_h)
            if cell.is_obstacle:
                color = COLOR_OBSTACLE
            elif cell.cell_type == CellType.RESOURCE:
                color = _resource_color(cell.resource_value)
            else:
                color = COLOR_EMPTY
            painter.setBrush(QBrush(color))
            painter.drawRect(int(x), int(y), int(w), int(h))

    def _draw_grid_lines(
        self, painter: QPainter, cell_w: float, cell_h: float,
    ) -> None:
        assert self._grid is not None
        pen = QPen(COLOR_GRID_LINE, 1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        w_px = self.width()
        h_px = self.height()
        for row in range(self._grid.height + 1):
            y = int(row * cell_h)
            painter.drawLine(0, y, w_px, y)
        for col in range(self._grid.width + 1):
            x = int(col * cell_w)
            painter.drawLine(x, 0, x, h_px)

    def _draw_selection(
        self, painter: QPainter, cell_w: float, cell_h: float,
    ) -> None:
        if self._selection is None:
            return
        if self._selection.selection_type != SelectionType.CELL:
            return
        if self._selection.selected_cell is None:
            return
        row, col = self._selection.selected_cell
        x, y, w, h = self._cell_rect(row, col, cell_w, cell_h)
        pen = QPen(COLOR_SELECTION_BORDER, 3)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(int(x) + 1, int(y) + 1, int(w) - 2, int(h) - 2)

    def _draw_agent(
        self, painter: QPainter, cell_w: float, cell_h: float,
    ) -> None:
        if self._agent is None:
            return
        x, y, w, h = self._cell_rect(
            self._agent.row, self._agent.col, cell_w, cell_h,
        )
        cx = x + w / 2
        cy = y + h / 2
        radius = min(w, h) * 0.35

        color = COLOR_AGENT_SELECTED if self._agent.is_selected else COLOR_AGENT
        painter.setBrush(QBrush(color))
        if self._agent.is_selected:
            painter.setPen(QPen(COLOR_AGENT_SELECTED.darker(150), 2))
        else:
            painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            int(cx - radius), int(cy - radius),
            int(2 * radius), int(2 * radius),
        )

    # -- Debug overlays (VWP9) ---------------------------------------------

    def _draw_overlays(
        self, painter: QPainter, cell_w: float, cell_h: float,
    ) -> None:
        """Dispatch to enabled overlay renderers."""
        if self._overlay is None:
            return
        if self._overlay.action_preference is not None:
            self._draw_overlay_action_preference(
                painter, cell_w, cell_h, self._overlay.action_preference,
            )
        if self._overlay.drive_contribution is not None:
            self._draw_overlay_drive_contribution(
                painter, cell_w, cell_h, self._overlay.drive_contribution,
            )
        if self._overlay.consumption_opportunity is not None:
            self._draw_overlay_consumption_opportunity(
                painter, cell_w, cell_h, self._overlay.consumption_opportunity,
            )

    def _draw_overlay_action_preference(
        self,
        painter: QPainter,
        cell_w: float,
        cell_h: float,
        ap: ActionPreferenceOverlay,
    ) -> None:
        """Draw probability arrows from the agent cell."""
        x, y, w, h = self._cell_rect(ap.agent_row, ap.agent_col, cell_w, cell_h)
        cx = x + w / 2
        cy = y + h / 2

        # Direction vectors: UP, DOWN, LEFT, RIGHT (indices 0-3)
        dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]

        for i, (dx, dy) in enumerate(dirs):
            if not ap.admissibility_mask[i] or ap.probabilities[i] < 0.01:
                continue
            prob = ap.probabilities[i]
            length = min(w, h) * 0.4 * prob
            alpha = int(60 + 195 * prob)

            if i == ap.selected_action_index:
                color = QColor(0, 255, 255, alpha)
                pen_width = 3
            else:
                color = QColor(255, 165, 0, alpha)
                pen_width = 2

            painter.setPen(QPen(color, pen_width))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            ex = cx + dx * length
            ey = cy + dy * length
            painter.drawLine(int(cx), int(cy), int(ex), int(ey))

        # CONSUME (index 4): filled dot at center
        if ap.admissibility_mask[4] and ap.probabilities[4] >= 0.01:
            prob = ap.probabilities[4]
            alpha = int(60 + 195 * prob)
            radius = min(w, h) * 0.08
            if 4 == ap.selected_action_index:
                color = QColor(0, 255, 255, alpha)
            else:
                color = QColor(255, 165, 0, alpha)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(
                int(cx - radius), int(cy - radius),
                int(2 * radius), int(2 * radius),
            )

        # STAY (index 5): ring at center
        if ap.admissibility_mask[5] and ap.probabilities[5] >= 0.01:
            prob = ap.probabilities[5]
            alpha = int(60 + 195 * prob)
            radius = min(w, h) * 0.12
            if 5 == ap.selected_action_index:
                color = QColor(0, 255, 255, alpha)
            else:
                color = QColor(255, 165, 0, alpha)
            painter.setPen(QPen(color, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(
                int(cx - radius), int(cy - radius),
                int(2 * radius), int(2 * radius),
            )

    def _draw_overlay_drive_contribution(
        self,
        painter: QPainter,
        cell_w: float,
        cell_h: float,
        dc: DriveContributionOverlay,
    ) -> None:
        """Draw mini bar chart of drive contributions on the agent cell."""
        x, y, w, h = self._cell_rect(dc.agent_row, dc.agent_col, cell_w, cell_h)

        # Semi-transparent backdrop
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
        painter.drawRect(int(x) + 1, int(y) + 1, int(w) - 2, int(h) - 2)

        contribs = dc.action_contributions
        max_abs = max(abs(v) for v in contribs) if any(contribs) else 1.0
        if max_abs == 0:
            max_abs = 1.0

        bar_h = (h - 4) / 6
        mid_x = x + w / 2

        for i, val in enumerate(contribs):
            bar_y = y + 2 + i * bar_h
            norm = val / max_abs
            bar_w = (w / 2 - 4) * abs(norm)

            if val >= 0:
                color = QColor(0, 200, 0, 180)
                bx = mid_x
            else:
                color = QColor(200, 0, 0, 180)
                bx = mid_x - bar_w

            painter.setBrush(QBrush(color))
            painter.drawRect(int(bx), int(bar_y), int(bar_w), int(bar_h - 1))

    def _draw_overlay_consumption_opportunity(
        self,
        painter: QPainter,
        cell_w: float,
        cell_h: float,
        co: ConsumptionOpportunityOverlay,
    ) -> None:
        """Draw resource indicators on agent cell and neighbors."""
        x, y, w, h = self._cell_rect(co.agent_row, co.agent_col, cell_w, cell_h)
        cx = x + w / 2
        cy = y + h / 2

        # Yellow diamond on agent cell if resource > 0
        if co.current_resource > 0:
            size = min(w, h) * 0.2
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(255, 215, 0, 200)))
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(45)
            painter.drawRect(int(-size / 2), int(-size / 2), int(size), int(size))
            painter.restore()

        # Neighbor indicators: UP, DOWN, LEFT, RIGHT
        offsets = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        for i, (dx, dy) in enumerate(offsets):
            nr = co.agent_row + dy
            nc = co.agent_col + dx
            nx, ny, nw, nh = self._cell_rect(nr, nc, cell_w, cell_h)
            ncx = nx + nw / 2
            ncy = ny + nh / 2
            radius = min(nw, nh) * 0.15

            if not co.neighbor_traversable[i]:
                # Red X for non-traversable
                painter.setPen(QPen(QColor(255, 0, 0, 150), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                d = radius * 0.7
                painter.drawLine(
                    int(ncx - d), int(ncy - d), int(ncx + d), int(ncy + d),
                )
                painter.drawLine(
                    int(ncx + d), int(ncy - d), int(ncx - d), int(ncy + d),
                )
            elif co.neighbor_resources[i] > 0:
                # Green circle, opacity scales with resource level
                alpha = int(80 + 175 * co.neighbor_resources[i])
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(0, 200, 0, alpha)))
                painter.drawEllipse(
                    int(ncx - radius), int(ncy - radius),
                    int(2 * radius), int(2 * radius),
                )

    # -- Mouse interaction (VWP7) ------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._grid is None:
            return
        if self.width() == 0 or self.height() == 0:
            return
        cell_w = self.width() / self._grid.width
        cell_h = self.height() / self._grid.height
        col = int(event.position().x() / cell_w)
        row = int(event.position().y() / cell_h)
        if not (0 <= row < self._grid.height and 0 <= col < self._grid.width):
            return
        # Agent click priority (arch spec §12.5.3)
        if self._agent and row == self._agent.row and col == self._agent.col:
            self.agent_clicked.emit()
        else:
            self.cell_clicked.emit(row, col)
