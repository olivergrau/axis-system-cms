"""Integration tests for episode execution, determinism, and result structures."""

from __future__ import annotations

import json

from axis_system_a import (
    Observation,
    TerminationReason,
)
from axis_system_a.results import EpisodeSummary
from axis_system_a.runner import run_episode
from tests.builders.world_builder import WorldBuilder
from tests.fixtures.scenario_fixtures import make_config


def _resource_world():
    return WorldBuilder().with_all_food(0.8).with_food(1, 1, 0.5).build()


def _empty_world():
    return WorldBuilder().build()


# ---------------------------------------------------------------------------
# Episode execution tests
# ---------------------------------------------------------------------------


class TestRunEpisode:
    def test_terminates_on_energy_depletion(self):
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "agent": {"initial_energy": 2.0, "max_energy": 100.0, "memory_capacity": 5},
        })
        world = _empty_world()
        result = run_episode(config, world)

        assert result.termination_reason is TerminationReason.ENERGY_DEPLETED
        assert result.steps[-1].terminated is True

    def test_terminates_on_max_steps(self):
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 3},
        })
        world = _resource_world()
        result = run_episode(config, world)

        assert result.termination_reason is TerminationReason.MAX_STEPS_REACHED
        assert result.total_steps == 3

    def test_runs_multiple_steps(self):
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 10},
        })
        world = _resource_world()
        result = run_episode(config, world)

        assert result.total_steps > 1
        assert len(result.steps) == result.total_steps

    def test_timesteps_sequential(self):
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 5},
        })
        world = _resource_world()
        result = run_episode(config, world)

        for i, record in enumerate(result.steps):
            assert record.timestep == i

    def test_final_state_matches_last_step(self):
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 5},
        })
        world = _resource_world()
        result = run_episode(config, world)

        assert result.final_agent_state.energy == result.steps[-1].energy_after

    def test_final_position_from_world(self):
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 5},
        })
        world = _resource_world()
        result = run_episode(config, world)

        assert result.final_position == world.agent_position

    def test_final_observation_available(self):
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 5},
        })
        world = _resource_world()
        result = run_episode(config, world)

        assert isinstance(result.final_observation, Observation)


# ---------------------------------------------------------------------------
# Max-step guard tests
# ---------------------------------------------------------------------------


class TestMaxStepsGuard:
    def test_max_steps_one(self):
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 1},
        })
        world = _resource_world()
        result = run_episode(config, world)

        assert result.total_steps == 1

    def test_stops_before_energy_depletion(self):
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 3},
        })
        world = _resource_world()
        result = run_episode(config, world)

        assert result.termination_reason is TerminationReason.MAX_STEPS_REACHED
        assert result.final_agent_state.energy > 0.0


# ---------------------------------------------------------------------------
# WP8: Result & Trace structure tests
# ---------------------------------------------------------------------------


class TestWP8ResultStructures:
    def test_result_has_summary(self):
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 3},
        })
        world = _resource_world()
        result = run_episode(config, world)

        assert isinstance(result.summary, EpisodeSummary)

    def test_summary_survival_length(self):
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 5},
        })
        world = _resource_world()
        result = run_episode(config, world)

        assert result.summary.survival_length == result.total_steps

    def test_summary_action_counts_sum(self):
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 5},
        })
        world = _resource_world()
        result = run_episode(config, world)

        assert sum(result.summary.action_counts.values()) == result.total_steps

    def test_step_has_energy_before(self):
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 3},
        })
        world = _resource_world()
        result = run_episode(config, world)

        for record in result.steps:
            assert hasattr(record, "energy_before")
            assert record.energy_before >= 0.0

    def test_energy_before_chain(self):
        """Each step's energy_before equals the previous step's energy_after."""
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 5},
        })
        world = _resource_world()
        result = run_episode(config, world)

        assert result.steps[0].energy_before == config.agent.initial_energy
        for i in range(1, len(result.steps)):
            assert result.steps[i].energy_before == result.steps[i - 1].energy_after

    def test_world_snapshots_in_trace(self):
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 3},
        })
        world = _resource_world()
        result = run_episode(config, world)

        for record in result.steps:
            trace = record.transition_trace
            assert trace.world_before is not None
            assert trace.world_after_regen is not None
            assert trace.world_after_action is not None

    def test_agent_snapshots_in_trace(self):
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 3},
        })
        world = _resource_world()
        result = run_episode(config, world)

        for record in result.steps:
            trace = record.transition_trace
            assert trace.agent_snapshot_before is not None
            assert trace.agent_snapshot_after is not None

    def test_serialization_round_trip(self):
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 3},
        })
        world = _resource_world()
        result = run_episode(config, world)

        d = result.to_dict()
        assert isinstance(d, dict)
        json.dumps(d, default=str)

    def test_step_serialization(self):
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 1},
        })
        world = _resource_world()
        result = run_episode(config, world)

        d = result.steps[0].to_dict()
        assert isinstance(d, dict)
        json.dumps(d, default=str)
