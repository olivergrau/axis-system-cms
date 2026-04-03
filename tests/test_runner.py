"""Tests for the episode execution loop."""

from __future__ import annotations

import copy

import numpy as np
import pytest

from axis_system_a import (
    AgentState,
    Cell,
    CellType,
    MemoryState,
    Observation,
    Position,
    SimulationConfig,
    TerminationReason,
    World,
    build_observation,
)
from axis_system_a.results import EpisodeResult, EpisodeStepRecord
from axis_system_a.runner import episode_step, run_episode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(
    overrides: dict | None = None,
) -> SimulationConfig:
    """Build a SimulationConfig from defaults with optional overrides."""
    d: dict = {
        "general": {"seed": 42},
        "world": {"grid_width": 3, "grid_height": 3},
        "agent": {
            "initial_energy": 50.0,
            "max_energy": 100.0,
            "memory_capacity": 5,
        },
        "policy": {
            "selection_mode": "sample",
            "temperature": 1.0,
            "stay_suppression": 0.1,
            "consume_weight": 1.5,
        },
        "transition": {
            "move_cost": 1.0,
            "consume_cost": 1.0,
            "stay_cost": 0.5,
            "max_consume": 1.0,
            "energy_gain_factor": 10.0,
        },
        "execution": {"max_steps": 1000},
    }
    if overrides:
        for section, vals in overrides.items():
            if section in d and isinstance(d[section], dict):
                d[section].update(vals)
            else:
                d[section] = vals
    return SimulationConfig(**d)


def _make_resource_world() -> World:
    """3x3 world with resources everywhere (agent at center).

    All cells are RESOURCE(0.8) except center which is RESOURCE(0.5).
    """
    res = Cell(cell_type=CellType.RESOURCE, resource_value=0.8)
    center = Cell(cell_type=CellType.RESOURCE, resource_value=0.5)
    grid = [
        [res, res, res],
        [res, center, res],
        [res, res, res],
    ]
    return World(grid=grid, agent_position=Position(x=1, y=1))


def _make_empty_world() -> World:
    """3x3 world with no resources (agent at center)."""
    empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    grid = [
        [empty, empty, empty],
        [empty, empty, empty],
        [empty, empty, empty],
    ]
    return World(grid=grid, agent_position=Position(x=1, y=1))


def _make_corridor_world() -> World:
    """3x1 corridor: agent at (0,0), resource at (2,0).

    Forces limited action choices.
    """
    empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    res = Cell(cell_type=CellType.RESOURCE, resource_value=1.0)
    grid = [[empty, empty, res]]
    return World(grid=grid, agent_position=Position(x=0, y=0))


# ---------------------------------------------------------------------------
# Single-step tests
# ---------------------------------------------------------------------------


class TestEpisodeStep:
    def test_produces_valid_record(self):
        config = _make_config()
        world = _make_resource_world()
        agent_state = AgentState(
            energy=50.0, memory_state=MemoryState(entries=(), capacity=5),
        )
        obs = build_observation(world, world.agent_position)
        rng = np.random.default_rng(42)

        new_state, new_obs, record = episode_step(
            world, agent_state, obs, 0, config, rng,
        )

        assert isinstance(record, EpisodeStepRecord)
        assert record.timestep == 0
        assert isinstance(new_state, AgentState)
        assert isinstance(new_obs, Observation)

    def test_action_consistent_with_policy(self):
        config = _make_config()
        world = _make_resource_world()
        agent_state = AgentState(
            energy=50.0, memory_state=MemoryState(entries=(), capacity=5),
        )
        obs = build_observation(world, world.agent_position)
        rng = np.random.default_rng(42)

        _, _, record = episode_step(world, agent_state, obs, 0, config, rng)

        assert record.action is record.decision_result.selected_action

    def test_energy_after_matches_trace(self):
        config = _make_config()
        world = _make_resource_world()
        agent_state = AgentState(
            energy=50.0, memory_state=MemoryState(entries=(), capacity=5),
        )
        obs = build_observation(world, world.agent_position)
        rng = np.random.default_rng(42)

        new_state, _, record = episode_step(
            world, agent_state, obs, 0, config, rng,
        )

        assert record.energy_after == record.transition_trace.energy_after
        assert record.energy_after == new_state.energy

    def test_observation_is_pre_step(self):
        config = _make_config()
        world = _make_resource_world()
        agent_state = AgentState(
            energy=50.0, memory_state=MemoryState(entries=(), capacity=5),
        )
        obs = build_observation(world, world.agent_position)
        rng = np.random.default_rng(42)

        _, _, record = episode_step(world, agent_state, obs, 0, config, rng)

        # Record observation should be the one we passed in (pre-step)
        assert record.observation is obs

    def test_returned_observation_is_post_step(self):
        config = _make_config()
        world = _make_resource_world()
        agent_state = AgentState(
            energy=50.0, memory_state=MemoryState(entries=(), capacity=5),
        )
        obs = build_observation(world, world.agent_position)
        rng = np.random.default_rng(42)

        _, new_obs, record = episode_step(
            world, agent_state, obs, 0, config, rng,
        )

        # Returned observation should reflect the world state after the step
        expected = build_observation(world, world.agent_position)
        assert new_obs == expected

    def test_world_mutated_in_place(self):
        config = _make_config()
        world = _make_resource_world()
        agent_state = AgentState(
            energy=50.0, memory_state=MemoryState(entries=(), capacity=5),
        )
        obs = build_observation(world, world.agent_position)
        pos_before = world.agent_position
        rng = np.random.default_rng(42)

        new_state, _, record = episode_step(
            world, agent_state, obs, 0, config, rng,
        )

        # World should reflect the step outcomes
        if record.transition_trace.moved:
            assert world.agent_position != pos_before
        if record.transition_trace.consumed:
            cell = world.get_cell(record.transition_trace.position_after)
            # After consuming, cell should have less resource
            assert cell.resource_value < 0.5 or cell.cell_type is CellType.EMPTY


# ---------------------------------------------------------------------------
# Episode tests
# ---------------------------------------------------------------------------


class TestRunEpisode:
    def test_terminates_on_energy_depletion(self):
        # Low energy, high cost, no resources → quick death
        config = _make_config(overrides={
            "agent": {"initial_energy": 2.0, "max_energy": 100.0, "memory_capacity": 5},
        })
        world = _make_empty_world()
        result = run_episode(config, world)

        assert result.termination_reason is TerminationReason.ENERGY_DEPLETED
        assert result.steps[-1].terminated is True

    def test_terminates_on_max_steps(self):
        # High energy, low max_steps → max steps hit first
        config = _make_config(overrides={
            "execution": {"max_steps": 3},
        })
        world = _make_resource_world()
        result = run_episode(config, world)

        assert result.termination_reason is TerminationReason.MAX_STEPS_REACHED
        assert result.total_steps == 3

    def test_runs_multiple_steps(self):
        config = _make_config(overrides={
            "execution": {"max_steps": 10},
        })
        world = _make_resource_world()
        result = run_episode(config, world)

        assert result.total_steps > 1
        assert len(result.steps) == result.total_steps

    def test_timesteps_sequential(self):
        config = _make_config(overrides={
            "execution": {"max_steps": 5},
        })
        world = _make_resource_world()
        result = run_episode(config, world)

        for i, record in enumerate(result.steps):
            assert record.timestep == i

    def test_final_state_matches_last_step(self):
        config = _make_config(overrides={
            "execution": {"max_steps": 5},
        })
        world = _make_resource_world()
        result = run_episode(config, world)

        assert result.final_agent_state.energy == result.steps[-1].energy_after

    def test_final_position_from_world(self):
        config = _make_config(overrides={
            "execution": {"max_steps": 5},
        })
        world = _make_resource_world()
        result = run_episode(config, world)

        assert result.final_position == world.agent_position

    def test_final_observation_available(self):
        config = _make_config(overrides={
            "execution": {"max_steps": 5},
        })
        world = _make_resource_world()
        result = run_episode(config, world)

        assert isinstance(result.final_observation, Observation)


# ---------------------------------------------------------------------------
# Determinism tests
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_seed_same_trajectory(self):
        config = _make_config(overrides={
            "execution": {"max_steps": 10},
        })
        world1 = _make_resource_world()
        world2 = _make_resource_world()

        result1 = run_episode(config, world1)
        result2 = run_episode(config, world2)

        assert result1.total_steps == result2.total_steps
        for r1, r2 in zip(result1.steps, result2.steps):
            assert r1.action == r2.action
            assert r1.energy_after == r2.energy_after
            assert r1.transition_trace == r2.transition_trace

    def test_different_seed_different_trajectory(self):
        config1 = _make_config(overrides={
            "general": {"seed": 42},
            "execution": {"max_steps": 20},
        })
        config2 = _make_config(overrides={
            "general": {"seed": 99},
            "execution": {"max_steps": 20},
        })
        world1 = _make_resource_world()
        world2 = _make_resource_world()

        result1 = run_episode(config1, world1)
        result2 = run_episode(config2, world2)

        # With different seeds and stochastic sampling, at least one action should differ
        actions1 = [r.action for r in result1.steps]
        actions2 = [r.action for r in result2.steps]
        assert actions1 != actions2


# ---------------------------------------------------------------------------
# Max-step guard tests
# ---------------------------------------------------------------------------


class TestMaxStepsGuard:
    def test_max_steps_one(self):
        config = _make_config(overrides={
            "execution": {"max_steps": 1},
        })
        world = _make_resource_world()
        result = run_episode(config, world)

        assert result.total_steps == 1

    def test_stops_before_energy_depletion(self):
        # Agent has plenty of energy but max_steps cuts it short
        config = _make_config(overrides={
            "execution": {"max_steps": 3},
        })
        world = _make_resource_world()
        result = run_episode(config, world)

        assert result.termination_reason is TerminationReason.MAX_STEPS_REACHED
        assert result.final_agent_state.energy > 0.0


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestIntegration:
    def test_full_pipeline_components_populated(self):
        """Verify no component is bypassed — all traces contain real data."""
        config = _make_config(overrides={
            "execution": {"max_steps": 3},
        })
        world = _make_resource_world()
        result = run_episode(config, world)

        for record in result.steps:
            # Drive output should have real activation
            assert 0.0 <= record.drive_output.activation <= 1.0
            # Decision result should have probabilities summing to ~1
            assert abs(sum(record.decision_result.probabilities) - 1.0) < 1e-9
            # Transition trace should have energy values
            assert record.transition_trace.energy_before >= 0.0

    def test_observation_chain_continuity(self):
        """Each step's pre-observation equals the previous step's post-observation."""
        config = _make_config(overrides={
            "execution": {"max_steps": 5},
        })
        world = _make_resource_world()

        # Manually run steps to track observation flow
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

        # Each step's input observation should be the previous step's output
        for i in range(1, len(observations_in)):
            assert observations_in[i] == observations_out[i - 1]

    def test_energy_decreases_on_empty_grid(self):
        """On a grid with no resources, energy should decrease every step."""
        config = _make_config(overrides={
            "execution": {"max_steps": 10},
        })
        world = _make_empty_world()
        result = run_episode(config, world)

        energies = [50.0] + [r.energy_after for r in result.steps]
        for i in range(1, len(energies)):
            assert energies[i] < energies[i - 1]

    def test_initial_observation_uses_build_observation(self):
        """The first step's pre-observation should match build_observation."""
        config = _make_config(overrides={
            "execution": {"max_steps": 1},
        })
        world = _make_resource_world()
        expected_obs = build_observation(world, world.agent_position)

        result = run_episode(config, world)

        assert result.steps[0].observation == expected_obs

    def test_argmax_mode_deterministic(self):
        """Argmax mode produces identical trajectories without RNG dependence."""
        config = _make_config(overrides={
            "policy": {
                "selection_mode": "argmax",
                "temperature": 1.0,
                "stay_suppression": 0.1,
                "consume_weight": 1.5,
            },
            "execution": {"max_steps": 5},
        })
        world1 = _make_resource_world()
        world2 = _make_resource_world()

        result1 = run_episode(config, world1)
        result2 = run_episode(config, world2)

        for r1, r2 in zip(result1.steps, result2.steps):
            assert r1.action == r2.action
            assert r1.energy_after == r2.energy_after
