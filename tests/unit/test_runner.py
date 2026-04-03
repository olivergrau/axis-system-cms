"""Unit tests for episode_step function."""

from __future__ import annotations

import numpy as np

from axis_system_a import (
    AgentState,
    CellType,
    Observation,
    build_observation,
)
from axis_system_a.results import StepResult
from axis_system_a.runner import episode_step
from tests.builders.agent_state_builder import AgentStateBuilder
from tests.builders.world_builder import WorldBuilder
from tests.fixtures.scenario_fixtures import make_config


class TestEpisodeStep:
    def test_produces_valid_record(self):
        config = make_config(
            overrides={"world": {"grid_width": 3, "grid_height": 3}})
        world = WorldBuilder().with_all_food(0.8).with_food(1, 1, 0.5).build()
        agent_state = AgentStateBuilder().build()
        obs = build_observation(world, world.agent_position)
        rng = np.random.default_rng(42)

        new_state, new_obs, record = episode_step(
            world, agent_state, obs, 0, config, rng,
        )

        assert isinstance(record, StepResult)
        assert record.timestep == 0
        assert isinstance(new_state, AgentState)
        assert isinstance(new_obs, Observation)

    def test_action_consistent_with_policy(self):
        config = make_config(
            overrides={"world": {"grid_width": 3, "grid_height": 3}})
        world = WorldBuilder().with_all_food(0.8).with_food(1, 1, 0.5).build()
        agent_state = AgentStateBuilder().build()
        obs = build_observation(world, world.agent_position)
        rng = np.random.default_rng(42)

        _, _, record = episode_step(world, agent_state, obs, 0, config, rng)

        assert record.selected_action is record.decision_result.selected_action

    def test_energy_after_matches_trace(self):
        config = make_config(
            overrides={"world": {"grid_width": 3, "grid_height": 3}})
        world = WorldBuilder().with_all_food(0.8).with_food(1, 1, 0.5).build()
        agent_state = AgentStateBuilder().build()
        obs = build_observation(world, world.agent_position)
        rng = np.random.default_rng(42)

        new_state, _, record = episode_step(
            world, agent_state, obs, 0, config, rng,
        )

        assert record.energy_after == record.transition_trace.energy_after
        assert record.energy_after == new_state.energy

    def test_observation_is_pre_step(self):
        config = make_config(
            overrides={"world": {"grid_width": 3, "grid_height": 3}})
        world = WorldBuilder().with_all_food(0.8).with_food(1, 1, 0.5).build()
        agent_state = AgentStateBuilder().build()
        obs = build_observation(world, world.agent_position)
        rng = np.random.default_rng(42)

        _, _, record = episode_step(world, agent_state, obs, 0, config, rng)

        assert record.observation is obs

    def test_returned_observation_is_post_step(self):
        config = make_config(
            overrides={"world": {"grid_width": 3, "grid_height": 3}})
        world = WorldBuilder().with_all_food(0.8).with_food(1, 1, 0.5).build()
        agent_state = AgentStateBuilder().build()
        obs = build_observation(world, world.agent_position)
        rng = np.random.default_rng(42)

        _, new_obs, record = episode_step(
            world, agent_state, obs, 0, config, rng,
        )

        expected = build_observation(world, world.agent_position)
        assert new_obs == expected

    def test_world_mutated_in_place(self):
        config = make_config(
            overrides={"world": {"grid_width": 3, "grid_height": 3}})
        world = WorldBuilder().with_all_food(0.8).with_food(1, 1, 0.5).build()
        agent_state = AgentStateBuilder().build()
        obs = build_observation(world, world.agent_position)
        pos_before = world.agent_position
        rng = np.random.default_rng(42)

        new_state, _, record = episode_step(
            world, agent_state, obs, 0, config, rng,
        )

        if record.transition_trace.moved:
            assert world.agent_position != pos_before
        if record.transition_trace.consumed:
            cell = world.get_cell(record.transition_trace.position_after)
            assert cell.resource_value < 0.5 or cell.cell_type is CellType.EMPTY
