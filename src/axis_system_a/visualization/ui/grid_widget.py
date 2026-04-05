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

    def set_frame(
        self,
        grid: GridViewModel,
        agent: AgentViewModel,
        selection: SelectionViewModel,
    ) -> None:
        """Store view model data and schedule a repaint."""
        self._grid = grid
        self._agent = agent
        self._selection = selection
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
