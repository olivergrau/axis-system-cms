"""Tests for WP-V.5.2: Replay Validation Suite.

Validation with real episode structures using System A / System B patterns.
"""

from __future__ import annotations

import pytest

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
from axis.sdk.world_types import CellView
from axis.visualization.replay_validation import validate_episode_for_replay

from tests.visualization.replay_fixtures import (
    make_2phase_episode,
    make_3phase_episode,
    make_step_trace,
)


# ---------------------------------------------------------------------------
# With System A episodes (3-phase, intermediate snapshots)
# ---------------------------------------------------------------------------


class TestValidationWithSystemAEpisodes:

    def test_valid_3phase_episode_passes(self) -> None:
        ep = make_3phase_episode(num_steps=5)
        result = validate_episode_for_replay(ep)
        assert result.valid is True
        assert result.total_steps == 5

    def test_step_descriptors_record_intermediates(self) -> None:
        ep = make_3phase_episode(num_steps=3)
        result = validate_episode_for_replay(ep)
        for desc in result.step_descriptors:
            assert "AFTER_REGEN" in desc.has_intermediate_snapshots

    def test_grid_dimensions_captured(self) -> None:
        ep = make_3phase_episode(num_steps=3, width=8, height=6)
        result = validate_episode_for_replay(ep)
        assert result.grid_width == 8
        assert result.grid_height == 6

    def test_total_steps_matches(self) -> None:
        ep = make_3phase_episode(num_steps=7)
        result = validate_episode_for_replay(ep)
        assert result.total_steps == 7

    def test_invalid_episode_detected(self) -> None:
        cell = CellView(cell_type="empty", resource_value=0.0)
        # Non-monotonic timesteps
        snap = WorldSnapshot(
            grid=((cell,),),
            agent_position=Position(x=0, y=0),
            width=1, height=1,
        )
        step_0 = BaseStepTrace(
            timestep=1, action="stay",
            world_before=snap, world_after=snap,
            agent_position_before=Position(x=0, y=0),
            agent_position_after=Position(x=0, y=0),
            vitality_before=0.5, vitality_after=0.5,
            terminated=False,
        )
        step_1 = BaseStepTrace(
            timestep=0, action="stay",
            world_before=snap, world_after=snap,
            agent_position_before=Position(x=0, y=0),
            agent_position_after=Position(x=0, y=0),
            vitality_before=0.5, vitality_after=0.5,
            terminated=True,
        )
        ep = BaseEpisodeTrace(
            system_type="test", steps=(step_0, step_1), total_steps=2,
            termination_reason="max_steps", final_vitality=0.5,
            final_position=Position(x=0, y=0),
        )
        result = validate_episode_for_replay(ep)
        assert result.valid is False


# ---------------------------------------------------------------------------
# With System B episodes (2-phase, no intermediates)
# ---------------------------------------------------------------------------


class TestValidationWithSystemBEpisodes:

    def test_valid_2phase_episode_passes(self) -> None:
        ep = make_2phase_episode(num_steps=5)
        result = validate_episode_for_replay(ep)
        assert result.valid is True

    def test_no_intermediate_descriptors(self) -> None:
        ep = make_2phase_episode(num_steps=3)
        result = validate_episode_for_replay(ep)
        for desc in result.step_descriptors:
            assert desc.has_intermediate_snapshots == ()

    def test_contiguous_timesteps_required(self) -> None:
        step_0 = make_step_trace(timestep=0)
        step_2 = make_step_trace(timestep=2)  # gap at timestep 1
        ep = BaseEpisodeTrace(
            system_type="test", steps=(step_0, step_2), total_steps=2,
            termination_reason="max_steps", final_vitality=0.75,
            final_position=Position(x=2, y=1),
        )
        result = validate_episode_for_replay(ep)
        assert result.valid is False
        assert any("gap" in v.lower() for v in result.violations)

    def test_dimension_consistency(self) -> None:
        step_5x5 = make_step_trace(timestep=0, width=5, height=5)
        step_3x3 = make_step_trace(timestep=1, width=3, height=3)
        ep = BaseEpisodeTrace(
            system_type="test", steps=(step_5x5, step_3x3), total_steps=2,
            termination_reason="max_steps", final_vitality=0.75,
            final_position=Position(x=2, y=1),
        )
        result = validate_episode_for_replay(ep)
        assert result.valid is False
        assert any("dimension" in v.lower() for v in result.violations)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestValidationEdgeCases:

    def test_single_step_valid(self) -> None:
        ep = make_2phase_episode(num_steps=1)
        result = validate_episode_for_replay(ep)
        assert result.valid is True
        assert result.total_steps == 1

    def test_empty_episode_fails(self) -> None:
        ep = BaseEpisodeTrace(
            system_type="test", steps=(), total_steps=0,
            termination_reason="max_steps", final_vitality=0.0,
            final_position=Position(x=0, y=0),
        )
        result = validate_episode_for_replay(ep)
        assert result.valid is False

    def test_100_step_episode(self) -> None:
        ep = make_2phase_episode(num_steps=100)
        result = validate_episode_for_replay(ep)
        assert result.valid is True
        assert result.total_steps == 100
        assert len(result.step_descriptors) == 100

    def test_terminated_final_step(self) -> None:
        ep = make_2phase_episode(num_steps=3)
        result = validate_episode_for_replay(ep)
        last_desc = result.step_descriptors[-1]
        assert last_desc.has_world_before is True
        assert last_desc.has_world_after is True

    def test_multiple_violations_collected(self) -> None:
        step_0 = make_step_trace(timestep=0)
        step_2 = make_step_trace(timestep=2, width=3, height=3)
        ep = BaseEpisodeTrace(
            system_type="test", steps=(step_0, step_2), total_steps=2,
            termination_reason="max_steps", final_vitality=0.75,
            final_position=Position(x=2, y=1),
        )
        result = validate_episode_for_replay(ep)
        assert result.valid is False
        assert len(result.violations) >= 2
