"""Tests for GridWidget mouse interaction (VWP7)."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QPointF, Qt  # noqa: E402
from PySide6.QtGui import QMouseEvent  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from axis_system_a.enums import CellType  # noqa: E402
from axis_system_a.visualization.view_models import (  # noqa: E402
    AgentViewModel,
    GridCellViewModel,
    GridViewModel,
    SelectionType,
    SelectionViewModel,
)
from axis_system_a.visualization.ui.grid_widget import GridWidget  # noqa: E402


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _make_grid(width: int = 3, height: int = 3) -> GridViewModel:
    cells: list[GridCellViewModel] = []
    for row in range(height):
        for col in range(width):
            cells.append(
                GridCellViewModel(
                    row=row, col=col, cell_type=CellType.EMPTY,
                    resource_value=0.0, is_obstacle=False, is_traversable=True,
                    is_agent_here=False, is_selected=False,
                ),
            )
    return GridViewModel(width=width, height=height, cells=tuple(cells))


def _make_selection() -> SelectionViewModel:
    return SelectionViewModel(
        selection_type=SelectionType.NONE,
        selected_cell=None,
        agent_selected=False,
    )


def _make_agent(row: int = 0, col: int = 0) -> AgentViewModel:
    return AgentViewModel(row=row, col=col, energy=50.0, is_selected=False)


def _click(widget: GridWidget, x: float, y: float) -> None:
    event = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(x, y),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.mousePressEvent(event)


class TestCellClick:
    def test_click_top_left(self, qapp):
        widget = GridWidget()
        widget.resize(300, 300)
        widget.set_frame(_make_grid(), _make_agent(1, 1), _make_selection())
        received = []
        widget.cell_clicked.connect(lambda r, c: received.append((r, c)))
        _click(widget, 50, 50)  # center of (0,0) in 300x300 / 3x3
        assert received == [(0, 0)]

    def test_click_bottom_right(self, qapp):
        widget = GridWidget()
        widget.resize(300, 300)
        widget.set_frame(_make_grid(), _make_agent(1, 1), _make_selection())
        received = []
        widget.cell_clicked.connect(lambda r, c: received.append((r, c)))
        _click(widget, 250, 250)
        assert received == [(2, 2)]

    def test_click_middle(self, qapp):
        widget = GridWidget()
        widget.resize(300, 300)
        widget.set_frame(_make_grid(), _make_agent(0, 0), _make_selection())
        received = []
        widget.cell_clicked.connect(lambda r, c: received.append((r, c)))
        _click(widget, 150, 250)  # col=1, row=2
        assert received == [(2, 1)]


class TestAgentClick:
    def test_agent_cell_emits_agent_clicked(self, qapp):
        widget = GridWidget()
        widget.resize(300, 300)
        widget.set_frame(_make_grid(), _make_agent(0, 0), _make_selection())
        agent_received = []
        cell_received = []
        widget.agent_clicked.connect(lambda: agent_received.append(True))
        widget.cell_clicked.connect(lambda r, c: cell_received.append((r, c)))
        _click(widget, 50, 50)  # agent at (0,0)
        assert agent_received
        assert not cell_received

    def test_non_agent_cell_emits_cell_clicked(self, qapp):
        widget = GridWidget()
        widget.resize(300, 300)
        widget.set_frame(_make_grid(), _make_agent(0, 0), _make_selection())
        agent_received = []
        cell_received = []
        widget.agent_clicked.connect(lambda: agent_received.append(True))
        widget.cell_clicked.connect(lambda r, c: cell_received.append((r, c)))
        _click(widget, 150, 150)  # (1,1), not agent
        assert not agent_received
        assert cell_received == [(1, 1)]


class TestBoundsCheck:
    def test_click_outside_ignored(self, qapp):
        widget = GridWidget()
        widget.resize(300, 300)
        widget.set_frame(_make_grid(), _make_agent(0, 0), _make_selection())
        received = []
        widget.cell_clicked.connect(lambda r, c: received.append((r, c)))
        _click(widget, 350, 150)  # outside
        assert not received

    def test_negative_coords_ignored(self, qapp):
        widget = GridWidget()
        widget.resize(300, 300)
        widget.set_frame(_make_grid(), _make_agent(0, 0), _make_selection())
        received = []
        widget.cell_clicked.connect(lambda r, c: received.append((r, c)))
        _click(widget, -10, 50)  # negative x → col < 0
        assert not received


class TestNoData:
    def test_click_without_frame_no_crash(self, qapp):
        widget = GridWidget()
        widget.resize(300, 300)
        _click(widget, 50, 50)  # no set_frame called


class TestSignalTypes:
    def test_cell_clicked_signal_exists(self, qapp):
        assert hasattr(GridWidget, "cell_clicked")

    def test_agent_clicked_signal_exists(self, qapp):
        assert hasattr(GridWidget, "agent_clicked")
