"""Reduction tests -- System C degenerates to System A.

When prediction is disabled (lambda_+ = lambda_- = 0), System C
should produce identical actions and energy trajectories to System A.
"""

from __future__ import annotations

import numpy as np
import pytest

from axis.sdk.position import Position
from axis.sdk.world_types import ActionOutcome
from axis.systems.construction_kit.observation.types import CellObservation, Observation
from axis.systems.system_a.config import SystemAConfig
from axis.systems.system_a.system import SystemA
from axis.systems.system_c.config import SystemCConfig
from axis.systems.system_c.system import SystemC
from axis.world.grid_2d.model import Cell, CellType, World
from tests.builders.system_c_config_builder import SystemCConfigBuilder
from tests.builders.system_config_builder import SystemAConfigBuilder


def _make_resource_grid(
    width: int, height: int, value: float = 0.5,
) -> list[list[Cell]]:
    return [
        [Cell(cell_type=CellType.RESOURCE, resource_value=value)
         for _ in range(width)]
        for _ in range(height)
    ]


def _make_observation(resource: float = 0.0) -> Observation:
    cell = CellObservation(traversability=1.0, resource=resource)
    return Observation(
        current=cell, up=cell, down=cell, left=cell, right=cell,
    )


class TestSingleStepReduction:
    """With lambda_+ = lambda_- = 0 and fresh state, decide() matches System A."""

    def test_reduction_across_energy_levels(self) -> None:
        for energy in [10.0, 30.0, 50.0, 70.0, 90.0]:
            c_builder = (
                SystemCConfigBuilder()
                .with_positive_sensitivity(0.0)
                .with_negative_sensitivity(0.0)
                .with_selection_mode("argmax")
                .with_initial_energy(energy)
            )
            a_builder = (
                SystemAConfigBuilder()
                .with_selection_mode("argmax")
                .with_initial_energy(energy)
            )

            c_system = SystemC(SystemCConfig(**c_builder.build()))
            a_system = SystemA(SystemAConfig(**a_builder.build()))

            c_state = c_system.initialize_state()
            a_state = a_system.initialize_state()

            world = World(
                _make_resource_grid(5, 5, 0.5), Position(x=2, y=2),
            )

            rng_c = np.random.default_rng(123)
            rng_a = np.random.default_rng(123)

            c_result = c_system.decide(world, c_state, rng_c)
            a_result = a_system.decide(world, a_state, rng_a)

            assert c_result.action == a_result.action, (
                f"Mismatch at energy={energy}"
            )


class TestMultiStepReduction:
    """Multi-step reduction: lambda=0, same actions and energy as System A."""

    def _make_systems(self):
        c_dict = (
            SystemCConfigBuilder()
            .with_positive_sensitivity(0.0)
            .with_negative_sensitivity(0.0)
            .with_selection_mode("argmax")
            .build()
        )
        a_dict = (
            SystemAConfigBuilder()
            .with_selection_mode("argmax")
            .build()
        )
        return (
            SystemC(SystemCConfig(**c_dict)),
            SystemA(SystemAConfig(**a_dict)),
        )

    def test_identical_action_sequences(self) -> None:
        c_system, a_system = self._make_systems()
        c_state = c_system.initialize_state()
        a_state = a_system.initialize_state()

        world = World(
            _make_resource_grid(5, 5, 0.3), Position(x=2, y=2),
        )

        for step in range(10):
            rng_c = np.random.default_rng(42 + step)
            rng_a = np.random.default_rng(42 + step)

            c_result = c_system.decide(world, c_state, rng_c)
            a_result = a_system.decide(world, a_state, rng_a)

            assert c_result.action == a_result.action, (
                f"Action mismatch at step {step}"
            )

            action = c_result.action
            moved = action in ("up", "down", "left", "right")
            outcome = ActionOutcome(
                action=action, moved=moved,
                new_position=Position(x=2, y=2),
            )
            obs = _make_observation(0.3)

            c_trans = c_system.transition(c_state, outcome, obs)
            a_trans = a_system.transition(a_state, outcome, obs)

            c_state = c_trans.new_state
            a_state = a_trans.new_state

    def test_identical_energy_trajectory(self) -> None:
        c_system, a_system = self._make_systems()
        c_state = c_system.initialize_state()
        a_state = a_system.initialize_state()

        world = World(
            _make_resource_grid(5, 5, 0.3), Position(x=2, y=2),
        )

        for step in range(10):
            rng_c = np.random.default_rng(42 + step)
            rng_a = np.random.default_rng(42 + step)

            c_result = c_system.decide(world, c_state, rng_c)
            a_result = a_system.decide(world, a_state, rng_a)

            action = c_result.action
            moved = action in ("up", "down", "left", "right")
            outcome = ActionOutcome(
                action=action, moved=moved,
                new_position=Position(x=2, y=2),
            )
            obs = _make_observation(0.3)

            c_trans = c_system.transition(c_state, outcome, obs)
            a_trans = a_system.transition(a_state, outcome, obs)

            c_state = c_trans.new_state
            a_state = a_trans.new_state

        assert c_state.energy == pytest.approx(a_state.energy, abs=0.001)
