"""Reduction tests -- System C degenerates to System A.

When prediction is neutralized, System C should produce identical
actions and scores to System A.
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


def _make_world(
    *,
    current: tuple[bool, float],
    up: tuple[bool, float],
    down: tuple[bool, float],
    left: tuple[bool, float],
    right: tuple[bool, float],
) -> World:
    def _cell(traversable: bool, resource: float) -> Cell:
        if not traversable:
            return Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
        if resource > 0.0:
            return Cell(cell_type=CellType.RESOURCE, resource_value=resource)
        return Cell(cell_type=CellType.EMPTY, resource_value=0.0)

    grid = [
        [
            Cell(cell_type=CellType.EMPTY, resource_value=0.0),
            _cell(*up),
            Cell(cell_type=CellType.EMPTY, resource_value=0.0),
        ],
        [
            _cell(*left),
            _cell(*current),
            _cell(*right),
        ],
        [
            Cell(cell_type=CellType.EMPTY, resource_value=0.0),
            _cell(*down),
            Cell(cell_type=CellType.EMPTY, resource_value=0.0),
        ],
    ]
    return World(grid, Position(x=1, y=1))


def _make_neutral_systems() -> tuple[SystemA, SystemC]:
    a_cfg = (
        SystemAConfigBuilder()
        .with_selection_mode("argmax")
        .with_initial_energy(50.0)
        .build()
    )
    c_cfg = (
        SystemCConfigBuilder()
        .with_selection_mode("argmax")
        .with_initial_energy(50.0)
        .with_positive_sensitivity(0.0)
        .with_negative_sensitivity(0.0)
        .with_modulation_min(1.0)
        .with_modulation_max(1.0)
        .with_modulation_mode("multiplicative")
        .with_prediction_bias_scale(0.0)
        .build()
    )
    return SystemA(SystemAConfig(**a_cfg)), SystemC(SystemCConfig(**c_cfg))


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


class TestScoreReduction:
    """System C must reduce to System A when prediction is neutral."""

    def test_scores_and_actions_match_for_fixed_observations(self) -> None:
        a_system, c_system = _make_neutral_systems()
        assert a_system.action_space() == c_system.action_space()

        cases = [
            (
                "balanced-open",
                _make_world(
                    current=(True, 0.0),
                    up=(True, 0.2),
                    down=(True, 0.3),
                    left=(True, 0.1),
                    right=(True, 0.4),
                ),
                11,
            ),
            (
                "direction-tie",
                _make_world(
                    current=(True, 0.0),
                    up=(True, 0.5),
                    down=(True, 0.5),
                    left=(True, 0.2),
                    right=(True, 0.2),
                ),
                23,
            ),
            (
                "consume-favored",
                _make_world(
                    current=(True, 0.9),
                    up=(True, 0.1),
                    down=(True, 0.0),
                    left=(True, 0.1),
                    right=(True, 0.0),
                ),
                37,
            ),
            (
                "masked-mix",
                _make_world(
                    current=(True, 0.0),
                    up=(False, 0.0),
                    down=(True, 0.4),
                    left=(False, 0.0),
                    right=(True, 0.4),
                ),
                41,
            ),
        ]

        for label, world, seed in cases:
            a_state = a_system.initialize_state()
            c_state = c_system.initialize_state()
            rng_a = np.random.default_rng(seed)
            rng_c = np.random.default_rng(seed)

            a_result = a_system.decide(world, a_state, rng_a)
            c_result = c_system.decide(world, c_state, rng_c)

            assert a_result.action == c_result.action, label
            assert a_result.decision_data["observation"] == \
                c_result.decision_data["observation"], label
            assert a_result.decision_data["drive"]["activation"] == \
                pytest.approx(c_result.decision_data["drive"]["activation"]), label
            assert a_result.decision_data["drive"]["action_contributions"] == \
                pytest.approx(c_result.decision_data["drive"]["action_contributions"], abs=1e-12), label
            assert a_result.decision_data["policy"]["raw_contributions"] == \
                pytest.approx(c_result.decision_data["policy"]["raw_contributions"], abs=1e-12), label
            assert a_result.decision_data["policy"]["admissibility_mask"] == \
                c_result.decision_data["policy"]["admissibility_mask"], label
            assert a_result.decision_data["policy"]["selected_action"] == \
                c_result.decision_data["policy"]["selected_action"], label
            assert c_result.decision_data["prediction"]["reliability_factors"] == \
                pytest.approx((1.0, 1.0, 1.0, 1.0, 1.0, 1.0), abs=1e-12), label
            assert c_result.decision_data["prediction"]["prediction_biases"] == \
                pytest.approx((0.0, 0.0, 0.0, 0.0, 0.0, 0.0), abs=1e-12), label
            assert c_result.decision_data["prediction"]["final_scores"] == \
                pytest.approx(a_result.decision_data["drive"]["action_contributions"], abs=1e-12), label
