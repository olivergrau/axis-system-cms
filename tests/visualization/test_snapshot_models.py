"""Tests for VWP2 snapshot data models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from axis_system_a.enums import Action, TerminationReason
from axis_system_a.types import Position
from axis_system_a.world import Cell, CellType
from axis_system_a.visualization.snapshot_models import (
    ReplayCoordinate,
    ReplayPhase,
    ReplaySnapshot,
)


# ---------------------------------------------------------------------------
# ReplayPhase
# ---------------------------------------------------------------------------


class TestReplayPhase:
    def test_values(self):
        assert ReplayPhase.BEFORE == 0
        assert ReplayPhase.AFTER_REGEN == 1
        assert ReplayPhase.AFTER_ACTION == 2

    def test_ordering(self):
        assert ReplayPhase.BEFORE < ReplayPhase.AFTER_REGEN
        assert ReplayPhase.AFTER_REGEN < ReplayPhase.AFTER_ACTION

    def test_member_count(self):
        assert len(ReplayPhase) == 3

    def test_names(self):
        assert ReplayPhase.BEFORE.name == "BEFORE"
        assert ReplayPhase.AFTER_REGEN.name == "AFTER_REGEN"
        assert ReplayPhase.AFTER_ACTION.name == "AFTER_ACTION"


# ---------------------------------------------------------------------------
# ReplayCoordinate
# ---------------------------------------------------------------------------


class TestReplayCoordinate:
    def test_construction(self):
        c = ReplayCoordinate(step_index=0, phase=ReplayPhase.BEFORE)
        assert c.step_index == 0
        assert c.phase is ReplayPhase.BEFORE

    def test_frozen(self):
        c = ReplayCoordinate(step_index=0, phase=ReplayPhase.BEFORE)
        with pytest.raises(Exception):
            c.step_index = 1  # type: ignore[misc]

    def test_equality(self):
        a = ReplayCoordinate(step_index=2, phase=ReplayPhase.AFTER_REGEN)
        b = ReplayCoordinate(step_index=2, phase=ReplayPhase.AFTER_REGEN)
        assert a == b

    def test_negative_step_rejected(self):
        with pytest.raises(ValidationError):
            ReplayCoordinate(step_index=-1, phase=ReplayPhase.BEFORE)


# ---------------------------------------------------------------------------
# ReplaySnapshot
# ---------------------------------------------------------------------------


def _minimal_grid():
    """1x1 grid for lightweight snapshot construction."""
    cell = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    return ((cell,),)


class TestReplaySnapshot:
    def test_construction(self):
        s = ReplaySnapshot(
            step_index=0,
            phase=ReplayPhase.BEFORE,
            timestep=0,
            grid=_minimal_grid(),
            grid_width=1,
            grid_height=1,
            agent_position=Position(x=0, y=0),
            agent_energy=50.0,
            action=Action.STAY,
            moved=False,
            consumed=False,
            resource_consumed=0.0,
            energy_delta=-0.5,
            terminated=False,
            termination_reason=None,
        )
        assert s.step_index == 0
        assert s.phase is ReplayPhase.BEFORE
        assert s.agent_energy == 50.0
        assert s.action is Action.STAY
        assert s.termination_reason is None

    def test_frozen(self):
        s = ReplaySnapshot(
            step_index=0,
            phase=ReplayPhase.BEFORE,
            timestep=0,
            grid=_minimal_grid(),
            grid_width=1,
            grid_height=1,
            agent_position=Position(x=0, y=0),
            agent_energy=50.0,
            action=Action.STAY,
            moved=False,
            consumed=False,
            resource_consumed=0.0,
            energy_delta=-0.5,
            terminated=False,
            termination_reason=None,
        )
        with pytest.raises(Exception):
            s.step_index = 1  # type: ignore[misc]

    def test_all_fields_present(self):
        s = ReplaySnapshot(
            step_index=3,
            phase=ReplayPhase.AFTER_ACTION,
            timestep=3,
            grid=_minimal_grid(),
            grid_width=1,
            grid_height=1,
            agent_position=Position(x=0, y=0),
            agent_energy=42.0,
            action=Action.CONSUME,
            moved=False,
            consumed=True,
            resource_consumed=0.8,
            energy_delta=7.0,
            terminated=True,
            termination_reason=TerminationReason.ENERGY_DEPLETED,
        )
        expected_fields = {
            "step_index", "phase", "timestep",
            "grid", "grid_width", "grid_height",
            "agent_position", "agent_energy",
            "action", "moved", "consumed", "resource_consumed",
            "energy_delta", "terminated", "termination_reason",
        }
        assert set(ReplaySnapshot.model_fields.keys()) == expected_fields
