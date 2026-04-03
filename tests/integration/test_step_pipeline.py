"""Integration tests for the full step pipeline."""

from __future__ import annotations

import numpy as np

from axis_system_a import (
    AgentState,
    MemoryState,
    Observation,
    build_observation,
)
from axis_system_a.runner import episode_step, run_episode
from tests.builders.world_builder import WorldBuilder
from tests.fixtures.scenario_fixtures import make_config
from tests.utils.assertions import assert_probabilities_sum_to_one


def _resource_world():
    return WorldBuilder().with_all_food(0.8).with_food(1, 1, 0.5).build()


class TestStepPipeline:
    def test_full_pipeline_components_populated(self):
        """Verify no component is bypassed — all traces contain real data."""
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 3},
        })
        world = _resource_world()
        result = run_episode(config, world)

        for record in result.steps:
            assert 0.0 <= record.drive_output.activation <= 1.0
            assert_probabilities_sum_to_one(
                record.decision_result.probabilities)
            assert record.transition_trace.energy_before >= 0.0

    def test_observation_chain_continuity(self):
        """Each step's pre-observation equals the previous step's post-observation."""
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 5},
        })
        world = _resource_world()

        rng = np.random.default_rng(config.general.seed)
        agent_state = AgentState(
            energy=config.agent.initial_energy,
            memory_state=MemoryState(
                entries=(), capacity=config.agent.memory_capacity),
        )
        obs = build_observation(world, world.agent_position)

        observations_in: list[Observation] = []
        observations_out: list[Observation] = []

        for t in range(5):
            observations_in.append(obs)
            agent_state, obs, record = episode_step(
                world, agent_state, obs, t, config, rng,
            )
            observations_out.append(obs)
            if record.terminated:
                break

        for i in range(1, len(observations_in)):
            assert observations_in[i] == observations_out[i - 1]

    def test_initial_observation_uses_build_observation(self):
        """The first step's pre-observation should match build_observation."""
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 1},
        })
        world = _resource_world()
        expected_obs = build_observation(world, world.agent_position)

        result = run_episode(config, world)

        assert result.steps[0].observation == expected_obs
