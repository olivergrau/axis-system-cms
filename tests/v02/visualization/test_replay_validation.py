"""Tests for WP-V.3.1: Replay Validation and Error Types."""

from __future__ import annotations

from typing import Any

import pytest

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
from axis.sdk.world_types import CellView

from axis.visualization.errors import (
    CellOutOfBoundsError,
    PhaseNotAvailableError,
    ReplayContractViolation,
    ReplayError,
    StepOutOfBoundsError,
)
from axis.visualization.replay_validation import validate_episode_for_replay


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cell(resource: float = 0.0) -> CellView:
    return CellView(cell_type="empty", resource_value=resource)


def _make_snapshot(
    width: int = 5, height: int = 5,
) -> WorldSnapshot:
    grid = tuple(
        tuple(_make_cell() for _ in range(width))
        for _ in range(height)
    )
    return WorldSnapshot(
        grid=grid, agent_position=Position(x=0, y=0),
        width=width, height=height,
    )


def _make_step(
    *,
    timestep: int = 0,
    action: str = "stay",
    world_before: WorldSnapshot | None = None,
    world_after: WorldSnapshot | None = None,
    vitality_before: float = 1.0,
    vitality_after: float = 0.9,
    intermediate_snapshots: dict[str, WorldSnapshot] | None = None,
) -> BaseStepTrace:
    snap = _make_snapshot()
    return BaseStepTrace(
        timestep=timestep,
        action=action,
        world_before=world_before or snap,
        world_after=world_after or snap,
        intermediate_snapshots=intermediate_snapshots or {},
        agent_position_before=Position(x=0, y=0),
        agent_position_after=Position(x=0, y=0),
        vitality_before=vitality_before,
        vitality_after=vitality_after,
        terminated=False,
    )


def _make_episode(*steps: BaseStepTrace) -> BaseEpisodeTrace:
    return BaseEpisodeTrace(
        system_type="test",
        steps=steps,
        total_steps=len(steps),
        termination_reason="max_steps",
        final_vitality=0.9,
        final_position=Position(x=0, y=0),
    )


def _valid_episode(num_steps: int = 3) -> BaseEpisodeTrace:
    steps = tuple(_make_step(timestep=i) for i in range(num_steps))
    return _make_episode(*steps)


# ---------------------------------------------------------------------------
# Error type tests
# ---------------------------------------------------------------------------


class TestErrorTypes:

    def test_replay_contract_violation_message(self) -> None:
        v = ("bad field A", "bad field B")
        err = ReplayContractViolation(v)
        assert "2 replay contract violation(s)" in str(err)
        assert err.violations == v

    def test_step_out_of_bounds_message(self) -> None:
        err = StepOutOfBoundsError(10, 5)
        assert "10" in str(err)
        assert "0..4" in str(err)
        assert err.step_index == 10
        assert err.total_steps == 5

    def test_phase_not_available_error(self) -> None:
        err = PhaseNotAvailableError(3, 2)
        assert err.step_index == 3
        assert err.phase_index == 2
        assert "2" in str(err)

    def test_cell_out_of_bounds_error(self) -> None:
        err = CellOutOfBoundsError(10, 5, 8, 8)
        assert err.row == 10
        assert err.col == 5
        assert err.grid_width == 8
        assert err.grid_height == 8
        assert "10" in str(err)

    def test_all_errors_inherit_replay_error(self) -> None:
        assert issubclass(ReplayContractViolation, ReplayError)
        assert issubclass(StepOutOfBoundsError, ReplayError)
        assert issubclass(PhaseNotAvailableError, ReplayError)
        assert issubclass(CellOutOfBoundsError, ReplayError)


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


class TestValidation:

    def test_valid_episode_passes(self) -> None:
        result = validate_episode_for_replay(_valid_episode(3))
        assert result.valid is True
        assert result.total_steps == 3
        assert result.violations == ()

    def test_empty_episode_fails(self) -> None:
        episode = _make_episode()
        result = validate_episode_for_replay(episode)
        assert result.valid is False
        assert any("no steps" in v.lower() for v in result.violations)

    def test_duplicate_timestep(self) -> None:
        steps = (_make_step(timestep=0), _make_step(timestep=0))
        result = validate_episode_for_replay(_make_episode(*steps))
        assert result.valid is False
        assert any("Duplicate" in v for v in result.violations)

    def test_non_monotonic_timesteps(self) -> None:
        steps = (_make_step(timestep=0), _make_step(timestep=2),
                 _make_step(timestep=1))
        result = validate_episode_for_replay(_make_episode(*steps))
        assert result.valid is False
        assert any("ordering" in v.lower() for v in result.violations)

    def test_timestep_gap(self) -> None:
        steps = (_make_step(timestep=0), _make_step(timestep=2),
                 _make_step(timestep=3))
        result = validate_episode_for_replay(_make_episode(*steps))
        assert result.valid is False
        assert any("gap" in v.lower() for v in result.violations)

    def test_invalid_world_before(self) -> None:
        # Grid has an empty first row → _is_valid_snapshot returns False
        bad_snap = WorldSnapshot(
            grid=((),), agent_position=Position(x=0, y=0),
            width=1, height=1,
        )
        steps = (_make_step(timestep=0, world_before=bad_snap),)
        result = validate_episode_for_replay(_make_episode(*steps))
        assert result.valid is False
        assert any("world_before" in v for v in result.violations)

    def test_invalid_world_after(self) -> None:
        # Grid has an empty first row → _is_valid_snapshot returns False
        bad_snap = WorldSnapshot(
            grid=((),), agent_position=Position(x=0, y=0),
            width=1, height=1,
        )
        steps = (_make_step(timestep=0, world_after=bad_snap),)
        result = validate_episode_for_replay(_make_episode(*steps))
        assert result.valid is False
        assert any("world_after" in v for v in result.violations)

    def test_invalid_vitality(self) -> None:
        # Use model_construct to bypass Pydantic constraints and test
        # the validation function's vitality check defense-in-depth
        snap = _make_snapshot()
        bad_step = BaseStepTrace.model_construct(
            timestep=0,
            action="stay",
            world_before=snap,
            world_after=snap,
            intermediate_snapshots={},
            agent_position_before=Position(x=0, y=0),
            agent_position_after=Position(x=0, y=0),
            vitality_before=1.5,
            vitality_after=0.9,
            terminated=False,
            termination_reason=None,
            system_data={},
            world_data={},
        )
        episode = BaseEpisodeTrace.model_construct(
            system_type="test",
            steps=(bad_step,),
            total_steps=1,
            termination_reason="max_steps",
            final_vitality=0.9,
            final_position=Position(x=0, y=0),
            world_type="grid_2d",
            world_config={},
        )
        result = validate_episode_for_replay(episode)
        assert result.valid is False
        assert any("vitality" in v.lower() for v in result.violations)

    def test_grid_dimension_consistency(self) -> None:
        snap_10x10 = _make_snapshot(10, 10)
        snap_8x8 = _make_snapshot(8, 8)
        steps = (
            _make_step(timestep=0, world_before=snap_10x10,
                       world_after=snap_10x10),
            _make_step(timestep=1, world_before=snap_8x8,
                       world_after=snap_8x8),
        )
        result = validate_episode_for_replay(_make_episode(*steps))
        assert result.valid is False
        assert any("Inconsistent" in v for v in result.violations)

    def test_step_descriptors_populated(self) -> None:
        result = validate_episode_for_replay(_valid_episode(3))
        assert len(result.step_descriptors) == 3
        for i, desc in enumerate(result.step_descriptors):
            assert desc.step_index == i
            assert desc.has_world_before is True
            assert desc.has_world_after is True
            assert desc.has_agent_position is True
            assert desc.has_vitality is True
            assert desc.has_world_state is True

    def test_intermediate_snapshots_recorded(self) -> None:
        snap = _make_snapshot()
        steps = (_make_step(
            timestep=0,
            intermediate_snapshots={"after_regen": snap},
        ),)
        result = validate_episode_for_replay(_make_episode(*steps))
        assert result.valid is True
        assert result.step_descriptors[0].has_intermediate_snapshots == (
            "after_regen",)

    def test_multiple_violations_collected(self) -> None:
        # Bad grid (empty rows) + bad vitality via model_construct
        bad_snap = WorldSnapshot(
            grid=((),), agent_position=Position(x=0, y=0),
            width=1, height=1,
        )
        bad_step = BaseStepTrace.model_construct(
            timestep=0,
            action="stay",
            world_before=bad_snap,
            world_after=bad_snap,
            intermediate_snapshots={},
            agent_position_before=Position(x=0, y=0),
            agent_position_after=Position(x=0, y=0),
            vitality_before=1.5,
            vitality_after=0.9,
            terminated=False,
            termination_reason=None,
            system_data={},
            world_data={},
        )
        episode = BaseEpisodeTrace.model_construct(
            system_type="test",
            steps=(bad_step,),
            total_steps=1,
            termination_reason="max_steps",
            final_vitality=0.9,
            final_position=Position(x=0, y=0),
            world_type="grid_2d",
            world_config={},
        )
        result = validate_episode_for_replay(episode)
        assert result.valid is False
        assert len(result.violations) >= 3

    def test_grid_dimensions_set_on_valid(self) -> None:
        result = validate_episode_for_replay(_valid_episode(2))
        assert result.grid_width == 5
        assert result.grid_height == 5
