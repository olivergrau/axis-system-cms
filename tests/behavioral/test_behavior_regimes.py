"""Behavioral tests: system-level behavior regimes."""

from __future__ import annotations

from axis_system_a.runner import run_episode
from tests.builders.world_builder import WorldBuilder
from tests.fixtures.scenario_fixtures import make_config


def _resource_world():
    return WorldBuilder().with_all_food(0.8).with_food(1, 1, 0.5).build()


def _empty_world():
    return WorldBuilder().build()


class TestEnergyBehavior:
    def test_energy_decreases_on_empty_grid(self):
        """On a grid with no resources, energy should decrease every step."""
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 10},
        })
        world = _empty_world()
        result = run_episode(config, world)

        energies = [50.0] + [r.energy_after for r in result.steps]
        for i in range(1, len(energies)):
            assert energies[i] < energies[i - 1]

    def test_agent_energy_always_bounded(self):
        """Energy never drops below 0 or exceeds max_energy across all steps."""
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 20},
        })
        world = _resource_world()
        result = run_episode(config, world)

        for record in result.steps:
            assert 0.0 <= record.energy_after <= config.agent.max_energy

    def test_agent_survives_longer_with_food(self):
        """Agent survives longer with resources than without."""
        config_short = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "agent": {"initial_energy": 10.0, "max_energy": 100.0, "memory_capacity": 5},
            "execution": {"max_steps": 100},
        })
        no_food = _empty_world()
        with_food = _resource_world()

        result_no_food = run_episode(config_short, no_food)
        result_with_food = run_episode(config_short, with_food)

        assert result_with_food.total_steps >= result_no_food.total_steps


class TestDeterminism:
    def test_same_seed_same_trajectory(self):
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 10},
        })
        world1 = _resource_world()
        world2 = _resource_world()

        result1 = run_episode(config, world1)
        result2 = run_episode(config, world2)

        assert result1.total_steps == result2.total_steps
        for r1, r2 in zip(result1.steps, result2.steps):
            assert r1.selected_action == r2.selected_action
            assert r1.energy_after == r2.energy_after
            assert r1.transition_trace == r2.transition_trace

    def test_different_seed_different_trajectory(self):
        config1 = make_config(overrides={
            "general": {"seed": 42},
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 20},
        })
        config2 = make_config(overrides={
            "general": {"seed": 99},
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 20},
        })
        world1 = _resource_world()
        world2 = _resource_world()

        result1 = run_episode(config1, world1)
        result2 = run_episode(config2, world2)

        actions1 = [r.selected_action for r in result1.steps]
        actions2 = [r.selected_action for r in result2.steps]
        assert actions1 != actions2

    def test_argmax_mode_deterministic(self):
        """Argmax mode produces identical trajectories without RNG dependence."""
        config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "policy": {
                "selection_mode": "argmax",
                "temperature": 1.0,
                "stay_suppression": 0.1,
                "consume_weight": 1.5,
            },
            "execution": {"max_steps": 5},
        })
        world1 = _resource_world()
        world2 = _resource_world()

        result1 = run_episode(config, world1)
        result2 = run_episode(config, world2)

        for r1, r2 in zip(result1.steps, result2.steps):
            assert r1.selected_action == r2.selected_action
            assert r1.energy_after == r2.energy_after
