"""Tests for VWP5 view model types."""

from __future__ import annotations

import pytest

from axis_system_a.enums import Action, CellType, TerminationReason
from axis_system_a.visualization.snapshot_models import (
    ReplayCoordinate,
    ReplayPhase,
)
from axis_system_a.visualization.view_models import (
    ActionContextViewModel,
    AgentViewModel,
    GridCellViewModel,
    GridViewModel,
    SelectionType,
    SelectionViewModel,
    StatusBarViewModel,
    ViewerFrameViewModel,
)
from axis_system_a.visualization.viewer_state import PlaybackMode


# ---------------------------------------------------------------------------
# SelectionType
# ---------------------------------------------------------------------------


class TestSelectionType:
    def test_values(self):
        assert SelectionType.NONE == "none"
        assert SelectionType.CELL == "cell"
        assert SelectionType.AGENT == "agent"

    def test_member_count(self):
        assert len(SelectionType) == 3

    def test_names(self):
        assert SelectionType.NONE.name == "NONE"
        assert SelectionType.CELL.name == "CELL"
        assert SelectionType.AGENT.name == "AGENT"


# ---------------------------------------------------------------------------
# GridCellViewModel
# ---------------------------------------------------------------------------


class TestGridCellViewModel:
    def test_construction(self):
        cell = GridCellViewModel(
            row=1, col=2,
            cell_type=CellType.RESOURCE,
            resource_value=0.5,
            is_obstacle=False,
            is_traversable=True,
            is_agent_here=False,
            is_selected=True,
        )
        assert cell.row == 1
        assert cell.col == 2
        assert cell.cell_type is CellType.RESOURCE
        assert cell.resource_value == 0.5
        assert cell.is_obstacle is False
        assert cell.is_traversable is True
        assert cell.is_agent_here is False
        assert cell.is_selected is True

    def test_frozen(self):
        cell = GridCellViewModel(
            row=0, col=0,
            cell_type=CellType.EMPTY,
            resource_value=0.0,
            is_obstacle=False,
            is_traversable=True,
            is_agent_here=False,
            is_selected=False,
        )
        with pytest.raises(Exception):
            cell.row = 5  # type: ignore[misc]

    def test_all_fields_present(self):
        expected = {
            "row", "col", "cell_type", "resource_value",
            "is_obstacle", "is_traversable", "is_agent_here", "is_selected",
        }
        assert set(GridCellViewModel.model_fields.keys()) == expected


# ---------------------------------------------------------------------------
# GridViewModel
# ---------------------------------------------------------------------------


class TestGridViewModel:
    def test_construction(self):
        cell = GridCellViewModel(
            row=0, col=0,
            cell_type=CellType.EMPTY,
            resource_value=0.0,
            is_obstacle=False,
            is_traversable=True,
            is_agent_here=False,
            is_selected=False,
        )
        grid = GridViewModel(width=1, height=1, cells=(cell,))
        assert grid.width == 1
        assert grid.height == 1
        assert len(grid.cells) == 1

    def test_frozen(self):
        cell = GridCellViewModel(
            row=0, col=0,
            cell_type=CellType.EMPTY,
            resource_value=0.0,
            is_obstacle=False,
            is_traversable=True,
            is_agent_here=False,
            is_selected=False,
        )
        grid = GridViewModel(width=1, height=1, cells=(cell,))
        with pytest.raises(Exception):
            grid.width = 5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# AgentViewModel
# ---------------------------------------------------------------------------


class TestAgentViewModel:
    def test_construction(self):
        agent = AgentViewModel(row=2, col=3, energy=10.5, is_selected=True)
        assert agent.row == 2
        assert agent.col == 3
        assert agent.energy == 10.5
        assert agent.is_selected is True

    def test_frozen(self):
        agent = AgentViewModel(row=0, col=0, energy=1.0, is_selected=False)
        with pytest.raises(Exception):
            agent.energy = 0.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# StatusBarViewModel
# ---------------------------------------------------------------------------


class TestStatusBarViewModel:
    def test_construction(self):
        status = StatusBarViewModel(
            step_index=3,
            total_steps=10,
            phase=ReplayPhase.AFTER_REGEN,
            playback_mode=PlaybackMode.PLAYING,
            energy=5.0,
            at_start=False,
            at_end=False,
        )
        assert status.step_index == 3
        assert status.total_steps == 10
        assert status.phase is ReplayPhase.AFTER_REGEN
        assert status.playback_mode is PlaybackMode.PLAYING
        assert status.energy == 5.0
        assert status.at_start is False
        assert status.at_end is False

    def test_frozen(self):
        status = StatusBarViewModel(
            step_index=0, total_steps=5,
            phase=ReplayPhase.BEFORE,
            playback_mode=PlaybackMode.STOPPED,
            energy=1.0, at_start=True, at_end=False,
        )
        with pytest.raises(Exception):
            status.step_index = 1  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ActionContextViewModel
# ---------------------------------------------------------------------------


class TestActionContextViewModel:
    def test_construction(self):
        ctx = ActionContextViewModel(
            action=Action.UP,
            moved=True,
            consumed=False,
            resource_consumed=0.0,
            energy_delta=-0.5,
            terminated=False,
            termination_reason=None,
        )
        assert ctx.action is Action.UP
        assert ctx.moved is True
        assert ctx.consumed is False
        assert ctx.resource_consumed == 0.0
        assert ctx.energy_delta == -0.5
        assert ctx.terminated is False
        assert ctx.termination_reason is None

    def test_construction_with_termination(self):
        ctx = ActionContextViewModel(
            action=Action.STAY,
            moved=False,
            consumed=False,
            resource_consumed=0.0,
            energy_delta=-1.0,
            terminated=True,
            termination_reason=TerminationReason.ENERGY_DEPLETED,
        )
        assert ctx.terminated is True
        assert ctx.termination_reason is TerminationReason.ENERGY_DEPLETED


# ---------------------------------------------------------------------------
# ViewerFrameViewModel
# ---------------------------------------------------------------------------


class TestViewerFrameViewModel:
    def test_all_sub_models_present(self):
        expected = {
            "coordinate", "grid", "agent", "status",
            "selection", "action_context", "debug_overlay",
            "step_analysis",
        }
        assert set(ViewerFrameViewModel.model_fields.keys()) == expected
