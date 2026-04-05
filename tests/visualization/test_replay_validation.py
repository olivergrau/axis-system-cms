"""Tests for replay contract validation."""

from __future__ import annotations

import pytest

from axis_system_a.results import EpisodeResult, StepResult
from axis_system_a.snapshots import WorldSnapshot
from axis_system_a.visualization.replay_validation import (
    validate_episode_for_replay,
)


class TestValidEpisode:
    """A real episode from the runner must pass validation."""

    def test_valid_episode_passes(self, small_episode: EpisodeResult):
        result = validate_episode_for_replay(small_episode)
        assert result.valid is True
        assert result.violations == ()
        assert result.total_steps == len(small_episode.steps)

    def test_step_descriptors_populated(self, small_episode: EpisodeResult):
        result = validate_episode_for_replay(small_episode)
        assert len(result.step_descriptors) == len(small_episode.steps)

    def test_all_phases_available(self, small_episode: EpisodeResult):
        result = validate_episode_for_replay(small_episode)
        for sd in result.step_descriptors:
            assert sd.phase_availability.before is True
            assert sd.phase_availability.after_regen is True
            assert sd.phase_availability.after_action is True

    def test_grid_dimensions_present(self, small_episode: EpisodeResult):
        result = validate_episode_for_replay(small_episode)
        assert result.grid_width == 3
        assert result.grid_height == 3

    def test_agent_state_present(self, small_episode: EpisodeResult):
        result = validate_episode_for_replay(small_episode)
        for sd in result.step_descriptors:
            assert sd.has_agent_position is True
            assert sd.has_agent_energy is True
            assert sd.has_world_state is True


class TestEmptyEpisode:
    def test_empty_steps_fails(self, small_episode: EpisodeResult):
        empty = small_episode.model_copy(
            update={"steps": (), "total_steps": 0}
        )
        result = validate_episode_for_replay(empty)
        assert result.valid is False
        assert result.total_steps == 0
        assert any("no steps" in v.lower() for v in result.violations)


class TestStepOrdering:
    """Ordering, contiguity, and duplicate checks."""

    def test_duplicate_timestep(self, small_episode: EpisodeResult):
        steps = list(small_episode.steps)
        if len(steps) < 2:
            pytest.skip("Need at least 2 steps")
        # Make step[1] have same timestep as step[0]
        dup = steps[0].model_copy(update={"timestep": steps[0].timestep})
        steps[1] = dup
        bad = small_episode.model_copy(update={"steps": tuple(steps)})
        result = validate_episode_for_replay(bad)
        assert result.valid is False
        assert any("duplicate" in v.lower() for v in result.violations)

    def test_non_monotonic(self, small_episode: EpisodeResult):
        steps = list(small_episode.steps)
        if len(steps) < 2:
            pytest.skip("Need at least 2 steps")
        # Swap first two steps — timesteps will be reversed
        steps[0], steps[1] = steps[1], steps[0]
        bad = small_episode.model_copy(update={"steps": tuple(steps)})
        result = validate_episode_for_replay(bad)
        assert result.valid is False
        assert any("ordering" in v.lower() or "gap" in v.lower()
                   for v in result.violations)

    def test_non_contiguous(self, small_episode: EpisodeResult):
        steps = list(small_episode.steps)
        if len(steps) < 2:
            pytest.skip("Need at least 2 steps")
        # Shift step[1] to skip an index
        shifted = steps[1].model_copy(
            update={"timestep": steps[1].timestep + 10}
        )
        steps[1] = shifted
        bad = small_episode.model_copy(update={"steps": tuple(steps)})
        result = validate_episode_for_replay(bad)
        assert result.valid is False
        assert any("gap" in v.lower() for v in result.violations)


class TestPhaseValidation:
    """Missing or invalid world snapshots per phase."""

    def _break_snapshot(self, snapshot: WorldSnapshot) -> WorldSnapshot:
        """Return a snapshot with an empty grid."""
        return snapshot.model_copy(
            update={"grid": (), "width": 0, "height": 0}
        )

    def test_missing_world_before(self, small_episode: EpisodeResult):
        steps = list(small_episode.steps)
        tt = steps[0].transition_trace
        bad_tt = tt.model_copy(
            update={"world_before": self._break_snapshot(tt.world_before)}
        )
        steps[0] = steps[0].model_copy(update={"transition_trace": bad_tt})
        bad = small_episode.model_copy(update={"steps": tuple(steps)})
        result = validate_episode_for_replay(bad)
        assert result.valid is False
        assert any("world_before" in v for v in result.violations)

    def test_missing_world_after_regen(self, small_episode: EpisodeResult):
        steps = list(small_episode.steps)
        tt = steps[0].transition_trace
        bad_tt = tt.model_copy(
            update={
                "world_after_regen": self._break_snapshot(
                    tt.world_after_regen
                )
            }
        )
        steps[0] = steps[0].model_copy(update={"transition_trace": bad_tt})
        bad = small_episode.model_copy(update={"steps": tuple(steps)})
        result = validate_episode_for_replay(bad)
        assert result.valid is False
        assert any("world_after_regen" in v for v in result.violations)

    def test_missing_world_after_action(self, small_episode: EpisodeResult):
        steps = list(small_episode.steps)
        tt = steps[0].transition_trace
        bad_tt = tt.model_copy(
            update={
                "world_after_action": self._break_snapshot(
                    tt.world_after_action
                )
            }
        )
        steps[0] = steps[0].model_copy(update={"transition_trace": bad_tt})
        bad = small_episode.model_copy(update={"steps": tuple(steps)})
        result = validate_episode_for_replay(bad)
        assert result.valid is False
        assert any("world_after_action" in v for v in result.violations)


class TestEnergyValidation:
    def test_negative_energy_before(self, small_episode: EpisodeResult):
        steps = list(small_episode.steps)
        steps[0] = steps[0].model_copy(update={"energy_before": -1.0})
        bad = small_episode.model_copy(update={"steps": tuple(steps)})
        result = validate_episode_for_replay(bad)
        assert result.valid is False
        assert any("energy" in v.lower() for v in result.violations)

    def test_negative_energy_after(self, small_episode: EpisodeResult):
        steps = list(small_episode.steps)
        steps[0] = steps[0].model_copy(update={"energy_after": -1.0})
        bad = small_episode.model_copy(update={"steps": tuple(steps)})
        result = validate_episode_for_replay(bad)
        assert result.valid is False
        assert any("energy" in v.lower() for v in result.violations)


class TestGridDimensionConsistency:
    def test_inconsistent_dimensions(self, small_episode: EpisodeResult):
        steps = list(small_episode.steps)
        if len(steps) < 2:
            pytest.skip("Need at least 2 steps")
        tt = steps[1].transition_trace
        snap = tt.world_before
        # Make a 2x2 snapshot where step 0 was 3x3
        row = snap.grid[0][:2]
        bad_snap = snap.model_copy(
            update={"grid": (row, row), "width": 2, "height": 2}
        )
        bad_tt = tt.model_copy(update={"world_before": bad_snap})
        steps[1] = steps[1].model_copy(update={"transition_trace": bad_tt})
        bad = small_episode.model_copy(update={"steps": tuple(steps)})
        result = validate_episode_for_replay(bad)
        assert result.valid is False
        assert any("dimension" in v.lower() for v in result.violations)


class TestForwardCompatibility:
    """Extra fields must not break validation (Pydantic ignores them)."""

    def test_extra_fields_tolerated(self, small_episode: EpisodeResult):
        """Serialise, inject extra fields, re-validate — must still pass."""
        data = small_episode.model_dump(mode="json")
        data["extra_future_field"] = "some_value"
        for step in data["steps"]:
            step["extra_step_field"] = 42
        reloaded = EpisodeResult.model_validate(data)
        result = validate_episode_for_replay(reloaded)
        assert result.valid is True
