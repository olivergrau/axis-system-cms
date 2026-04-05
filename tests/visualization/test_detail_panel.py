"""Tests for DetailPanel (VWP7)."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from axis_system_a.enums import Action, CellType, TerminationReason  # noqa: E402
from axis_system_a.visualization.snapshot_models import (  # noqa: E402
    ReplayCoordinate,
    ReplayPhase,
)
from axis_system_a.visualization.view_models import (  # noqa: E402
    ActionContextViewModel,
    AgentViewModel,
    GridCellViewModel,
    GridViewModel,
    SelectionType,
    SelectionViewModel,
    StatusBarViewModel,
    ViewerFrameViewModel,
)
from axis_system_a.visualization.viewer_state import PlaybackMode  # noqa: E402
from axis_system_a.visualization.ui.detail_panel import DetailPanel  # noqa: E402


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _make_cells(
    selected: tuple[int, int] | None = None,
    agent_row: int = 0,
    agent_col: int = 0,
) -> tuple[GridCellViewModel, ...]:
    cells: list[GridCellViewModel] = []
    for row in range(3):
        for col in range(3):
            if row == 1 and col == 1:
                ct, rv, obs = CellType.OBSTACLE, 0.0, True
            elif row == 0 and col == 2:
                ct, rv, obs = CellType.RESOURCE, 0.75, False
            else:
                ct, rv, obs = CellType.EMPTY, 0.0, False
            cells.append(
                GridCellViewModel(
                    row=row, col=col, cell_type=ct, resource_value=rv,
                    is_obstacle=obs, is_traversable=not obs,
                    is_agent_here=(row == agent_row and col == agent_col),
                    is_selected=(selected == (row, col)),
                ),
            )
    return tuple(cells)


def _make_frame(
    selection_type: SelectionType = SelectionType.NONE,
    selected_cell: tuple[int, int] | None = None,
    agent_selected: bool = False,
    terminated: bool = False,
    termination_reason: TerminationReason | None = None,
) -> ViewerFrameViewModel:
    return ViewerFrameViewModel(
        coordinate=ReplayCoordinate(step_index=1, phase=ReplayPhase.AFTER_ACTION),
        grid=GridViewModel(
            width=3, height=3,
            cells=_make_cells(selected=selected_cell),
        ),
        agent=AgentViewModel(row=0, col=0, energy=42.5, is_selected=agent_selected),
        status=StatusBarViewModel(
            step_index=1, total_steps=5, phase=ReplayPhase.AFTER_ACTION,
            playback_mode=PlaybackMode.STOPPED, energy=42.5,
            at_start=False, at_end=False,
        ),
        selection=SelectionViewModel(
            selection_type=selection_type,
            selected_cell=selected_cell,
            agent_selected=agent_selected,
        ),
        action_context=ActionContextViewModel(
            action=Action.RIGHT, moved=True, consumed=False,
            resource_consumed=0.0, energy_delta=-1.0,
            terminated=terminated, termination_reason=termination_reason,
        ),
    )


class TestNoSelection:
    def test_shows_no_entity_selected(self, qapp):
        panel = DetailPanel()
        frame = _make_frame()
        panel.set_frame(frame)
        assert "No entity selected" in panel._content_label.text()


class TestCellSelection:
    def test_shows_coordinate(self, qapp):
        panel = DetailPanel()
        frame = _make_frame(
            selection_type=SelectionType.CELL, selected_cell=(1, 1),
        )
        panel.set_frame(frame)
        assert "(1, 1)" in panel._title_label.text()

    def test_shows_cell_type(self, qapp):
        panel = DetailPanel()
        frame = _make_frame(
            selection_type=SelectionType.CELL, selected_cell=(1, 1),
        )
        panel.set_frame(frame)
        assert "obstacle" in panel._content_label.text().lower()

    def test_shows_obstacle_flag(self, qapp):
        panel = DetailPanel()
        frame = _make_frame(
            selection_type=SelectionType.CELL, selected_cell=(1, 1),
        )
        panel.set_frame(frame)
        assert "Obstacle: True" in panel._content_label.text()

    def test_shows_resource_value(self, qapp):
        panel = DetailPanel()
        frame = _make_frame(
            selection_type=SelectionType.CELL, selected_cell=(0, 2),
        )
        panel.set_frame(frame)
        assert "0.75" in panel._content_label.text()


class TestAgentSelection:
    def test_shows_position(self, qapp):
        panel = DetailPanel()
        frame = _make_frame(
            selection_type=SelectionType.AGENT, agent_selected=True,
        )
        panel.set_frame(frame)
        assert "(0, 0)" in panel._content_label.text()

    def test_shows_energy(self, qapp):
        panel = DetailPanel()
        frame = _make_frame(
            selection_type=SelectionType.AGENT, agent_selected=True,
        )
        panel.set_frame(frame)
        assert "42.50" in panel._content_label.text()

    def test_shows_action(self, qapp):
        panel = DetailPanel()
        frame = _make_frame(
            selection_type=SelectionType.AGENT, agent_selected=True,
        )
        panel.set_frame(frame)
        assert "right" in panel._content_label.text().lower()

    def test_shows_termination_when_terminated(self, qapp):
        panel = DetailPanel()
        frame = _make_frame(
            selection_type=SelectionType.AGENT, agent_selected=True,
            terminated=True, termination_reason=TerminationReason.ENERGY_DEPLETED,
        )
        panel.set_frame(frame)
        assert "Terminated" in panel._content_label.text()


class TestFrameUpdate:
    def test_content_changes_on_reframe(self, qapp):
        panel = DetailPanel()
        frame1 = _make_frame()
        frame2 = _make_frame(
            selection_type=SelectionType.AGENT, agent_selected=True,
        )
        panel.set_frame(frame1)
        assert "No entity selected" in panel._content_label.text()
        panel.set_frame(frame2)
        assert "Agent" in panel._title_label.text()
