"""WP-11 reduction tests -- System A+W degenerates to System A.

Validates Model Section 12: when curiosity parameters are zeroed,
System A+W behavior matches System A.
"""

from __future__ import annotations

import numpy as np
import pytest

from axis.sdk.position import Position
from axis.sdk.world_types import ActionOutcome
from axis.systems.system_a.config import SystemAConfig
from axis.systems.system_a.system import SystemA
from axis.systems.system_a.types import CellObservation, MemoryState, Observation
from axis.systems.system_aw.config import SystemAWConfig
from axis.systems.system_aw.drive_curiosity import (
    compute_composite_novelty,
    compute_spatial_novelty,
)
from axis.systems.system_aw.system import SystemAW
from axis.systems.system_aw.types import AgentStateAW
from axis.systems.system_aw.world_model import create_world_model
from axis.world.grid_2d.model import Cell, CellType, World
from tests.builders.system_aw_config_builder import SystemAWConfigBuilder
from tests.builders.system_config_builder import SystemAConfigBuilder


def _make_grid(width: int, height: int) -> list[list[Cell]]:
    return [
        [Cell(cell_type=CellType.EMPTY, resource_value=0.0)
         for _ in range(width)]
        for _ in range(height)
    ]


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
    return Observation(current=cell, up=cell, down=cell, left=cell, right=cell)


# ---------------------------------------------------------------------------
# Reduction: mu_C = 0
# ---------------------------------------------------------------------------


class TestReductionMuCZero:
    """With base_curiosity=0, A+W action ordering matches System A."""

    def test_reduction_mu_c_zero(self) -> None:
        """For 5 (energy, observation) pairs: argmax action matches."""
        aw_builder = (
            SystemAWConfigBuilder()
            .with_base_curiosity(0.0)
            .with_selection_mode("argmax")
        )
        a_builder = SystemAConfigBuilder().with_selection_mode("argmax")

        # Test with various energy levels
        for energy in [10.0, 30.0, 50.0, 70.0, 90.0]:
            aw_dict = aw_builder.with_initial_energy(energy).build()
            aw_config = SystemAWConfig(**aw_dict)
            aw_system = SystemAW(aw_config)
            aw_state = aw_system.initialize_state()

            a_dict = a_builder.with_initial_energy(energy).build()
            a_config = SystemAConfig(**a_dict)
            a_system = SystemA(a_config)
            a_state = a_system.initialize_state()

            world = World(
                _make_resource_grid(5, 5, 0.5), Position(x=2, y=2))

            rng_aw = np.random.default_rng(123)
            rng_a = np.random.default_rng(123)

            aw_result = aw_system.decide(world, aw_state, rng_aw)
            a_result = a_system.decide(world, a_state, rng_a)

            assert aw_result.action == a_result.action, \
                f"Mismatch at energy={energy}"


class TestReductionWCBaseNearZero:
    """With curiosity_weight_base near 0, A+W action ordering matches System A.

    Config constrains curiosity_weight_base > 0, so we use a very small
    epsilon to approximate the reduction.
    """

    def test_reduction_w_c_base_near_zero(self) -> None:
        """curiosity_weight_base~=0 -> w_C~=0, action ordering matches."""
        aw_builder = (
            SystemAWConfigBuilder()
            .with_curiosity_weight_base(1e-9)
            .with_selection_mode("argmax")
        )
        a_builder = SystemAConfigBuilder().with_selection_mode("argmax")

        for energy in [10.0, 30.0, 50.0, 70.0, 90.0]:
            aw_dict = aw_builder.with_initial_energy(energy).build()
            aw_config = SystemAWConfig(**aw_dict)
            aw_system = SystemAW(aw_config)
            aw_state = aw_system.initialize_state()

            a_dict = a_builder.with_initial_energy(energy).build()
            a_config = SystemAConfig(**a_dict)
            a_system = SystemA(a_config)
            a_state = a_system.initialize_state()

            world = World(
                _make_resource_grid(5, 5, 0.5), Position(x=2, y=2))

            rng_aw = np.random.default_rng(123)
            rng_a = np.random.default_rng(123)

            aw_result = aw_system.decide(world, aw_state, rng_aw)
            a_result = a_system.decide(world, a_state, rng_a)

            assert aw_result.action == a_result.action, \
                f"Mismatch at energy={energy}"


# ---------------------------------------------------------------------------
# Multi-step reduction
# ---------------------------------------------------------------------------


class TestReductionMultiStep:
    """Multi-step reduction: mu_C=0, same actions and energy as System A."""

    def test_reduction_multi_step(self) -> None:
        """10 steps argmax: identical action sequences."""
        aw_dict = (
            SystemAWConfigBuilder()
            .with_base_curiosity(0.0)
            .with_selection_mode("argmax")
            .build()
        )
        a_dict = (
            SystemAConfigBuilder()
            .with_selection_mode("argmax")
            .build()
        )

        aw_system = SystemAW(SystemAWConfig(**aw_dict))
        a_system = SystemA(SystemAConfig(**a_dict))

        aw_state = aw_system.initialize_state()
        a_state = a_system.initialize_state()

        world = World(
            _make_resource_grid(5, 5, 0.3), Position(x=2, y=2))

        for step in range(10):
            rng_aw = np.random.default_rng(42 + step)
            rng_a = np.random.default_rng(42 + step)

            aw_result = aw_system.decide(world, aw_state, rng_aw)
            a_result = a_system.decide(world, a_state, rng_a)

            assert aw_result.action == a_result.action, \
                f"Action mismatch at step {step}"

            # Apply same action to both systems
            action = aw_result.action
            moved = action in ("up", "down", "left", "right")
            outcome = ActionOutcome(
                action=action, moved=moved,
                new_position=Position(x=2, y=2),
            )
            obs = _make_observation(0.3)

            aw_trans = aw_system.transition(aw_state, outcome, obs)
            a_trans = a_system.transition(a_state, outcome, obs)

            aw_state = aw_trans.new_state
            a_state = a_trans.new_state

    def test_reduction_energy_trajectory(self) -> None:
        """10 steps argmax: identical energy levels."""
        aw_dict = (
            SystemAWConfigBuilder()
            .with_base_curiosity(0.0)
            .with_selection_mode("argmax")
            .build()
        )
        a_dict = (
            SystemAConfigBuilder()
            .with_selection_mode("argmax")
            .build()
        )

        aw_system = SystemAW(SystemAWConfig(**aw_dict))
        a_system = SystemA(SystemAConfig(**a_dict))

        aw_state = aw_system.initialize_state()
        a_state = a_system.initialize_state()

        world = World(
            _make_resource_grid(5, 5, 0.3), Position(x=2, y=2))

        for step in range(10):
            rng_aw = np.random.default_rng(42 + step)
            rng_a = np.random.default_rng(42 + step)

            aw_result = aw_system.decide(world, aw_state, rng_aw)
            a_result = a_system.decide(world, a_state, rng_a)

            action = aw_result.action
            moved = action in ("up", "down", "left", "right")
            outcome = ActionOutcome(
                action=action, moved=moved,
                new_position=Position(x=2, y=2),
            )
            obs = _make_observation(0.3)

            aw_trans = aw_system.transition(aw_state, outcome, obs)
            a_trans = a_system.transition(a_state, outcome, obs)

            aw_state = aw_trans.new_state
            a_state = a_trans.new_state

        assert aw_state.energy == pytest.approx(a_state.energy, abs=0.001)


# ---------------------------------------------------------------------------
# Alpha boundary conditions
# ---------------------------------------------------------------------------


class TestAlphaBoundary:
    """Alpha boundary: memory independence at alpha=1, wm independence at alpha=0."""

    def test_alpha_one_memory_independent(self) -> None:
        """alpha=1.0: vary memory contents, composite novelty unchanged."""
        wm = create_world_model()
        spatial = compute_spatial_novelty(wm)

        # With alpha=1.0, composite = spatial only
        for sensory_vals in [
            (0.0, 0.0, 0.0, 0.0),
            (0.5, 0.5, 0.5, 0.5),
            (1.0, 0.0, 0.3, 0.7),
        ]:
            composite = compute_composite_novelty(
                spatial, sensory_vals, alpha=1.0)
            for i in range(4):
                assert composite[i] == pytest.approx(
                    spatial[i], abs=0.001)

    def test_alpha_zero_world_model_independent(self) -> None:
        """alpha=0.0: vary visit counts, composite novelty unchanged."""
        # Fixed sensory novelty
        sensory = (0.3, 0.5, 0.1, 0.8)

        for spatial_vals in [
            (1.0, 1.0, 1.0, 1.0),
            (0.5, 0.5, 0.5, 0.5),
            (0.1, 0.9, 0.3, 0.7),
        ]:
            composite = compute_composite_novelty(
                spatial_vals, sensory, alpha=0.0)
            for i in range(4):
                assert composite[i] == pytest.approx(
                    sensory[i], abs=0.001)


# ---------------------------------------------------------------------------
# World model updated even when curiosity disabled
# ---------------------------------------------------------------------------


class TestCuriosityDisabledWorldModel:
    """World model still updated when mu_C=0."""

    def test_curiosity_disabled_world_model_updated(self) -> None:
        """With mu_C=0: world model visit counts still increment."""
        config_dict = (
            SystemAWConfigBuilder()
            .with_base_curiosity(0.0)
            .build()
        )
        system = SystemAW(SystemAWConfig(**config_dict))
        state = system.initialize_state()

        # Initial visit counts: {(0,0): 1}
        assert dict(state.world_model.visit_counts).get((0, 0)) == 1

        world = World(_make_grid(5, 5), Position(x=2, y=2))
        rng = np.random.default_rng(42)

        result = system.decide(world, state, rng)
        outcome = ActionOutcome(
            action="right", moved=True,
            new_position=Position(x=3, y=2),
        )
        obs = _make_observation()
        trans = system.transition(state, outcome, obs)

        new_state = trans.new_state
        visits = dict(new_state.world_model.visit_counts)
        # Should have (0,0):1 and (1,0):1
        assert visits.get((0, 0)) == 1
        assert visits.get((1, 0)) == 1
        assert new_state.world_model.relative_position == (1, 0)
