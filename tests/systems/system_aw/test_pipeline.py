"""WP-10 pipeline tests -- end-to-end episode execution."""

from __future__ import annotations

import numpy as np
import pytest

from axis.framework.config import (
    ExecutionConfig,
    FrameworkConfig,
    GeneralConfig,
)
from axis.framework.run import RunConfig, RunExecutor
from axis.sdk.position import Position
from axis.sdk.world_types import ActionOutcome, BaseWorldConfig
from axis.systems.system_a.system import SystemA
from axis.systems.system_a.types import CellObservation, Observation
from axis.systems.system_aw.config import SystemAWConfig
from axis.systems.system_aw.system import SystemAW
from axis.systems.system_aw.types import AgentStateAW
from axis.world.grid_2d.model import Cell, CellType, World
from tests.builders.system_aw_config_builder import SystemAWConfigBuilder
from tests.builders.system_config_builder import SystemAConfigBuilder


def _make_resource_grid(width: int, height: int, value: float = 0.5) -> list[list[Cell]]:
    return [
        [Cell(cell_type=CellType.RESOURCE, resource_value=value)
         for _ in range(width)]
        for _ in range(height)
    ]


def _make_empty_grid(width: int, height: int) -> list[list[Cell]]:
    return [
        [Cell(cell_type=CellType.EMPTY, resource_value=0.0)
         for _ in range(width)]
        for _ in range(height)
    ]


def _make_observation() -> Observation:
    cell = CellObservation(traversability=1.0, resource=0.0)
    return Observation(current=cell, up=cell, down=cell, left=cell, right=cell)


class TestSingleStep:
    """Single-step pipeline test."""

    def test_single_step_pipeline(self) -> None:
        """decide() -> framework applies action -> transition() -> verify."""
        config = SystemAWConfig(**SystemAWConfigBuilder().build())
        system = SystemAW(config)
        state = system.initialize_state()
        rng = np.random.default_rng(42)

        world = World(
            _make_resource_grid(5, 5, 0.5),
            Position(x=2, y=2),
        )

        decide_result = system.decide(world, state, rng)
        assert decide_result.action in system.action_space()

        # Simulate framework applying the action
        outcome = ActionOutcome(
            action=decide_result.action,
            moved=decide_result.action in ("up", "down", "left", "right"),
            new_position=Position(x=2, y=2),
        )
        obs = system.observe(world, world.agent_position)
        trans_result = system.transition(state, outcome, obs)

        assert isinstance(trans_result.new_state, AgentStateAW)
        assert trans_result.new_state.energy >= 0


class TestMultiStep:
    """Multi-step episode tests."""

    def test_multi_step_episode(self) -> None:
        """Run 10 steps: energy decreases, world model grows, memory fills."""
        config = SystemAWConfig(**SystemAWConfigBuilder().build())
        system = SystemAW(config)
        state = system.initialize_state()
        rng = np.random.default_rng(42)

        world = World(
            _make_resource_grid(5, 5, 0.3),
            Position(x=2, y=2),
        )

        for step in range(10):
            decide_result = system.decide(world, state, rng)
            action = decide_result.action
            moved = action in ("up", "down", "left", "right")
            outcome = ActionOutcome(
                action=action, moved=moved,
                new_position=Position(x=2, y=2),
            )
            obs = system.observe(world, world.agent_position)
            trans_result = system.transition(state, outcome, obs)
            state = trans_result.new_state

        assert isinstance(state, AgentStateAW)
        assert state.energy < config.agent.initial_energy
        assert len(state.memory_state.entries) > 0
        assert len(state.world_model.visit_counts) >= 1

    def test_episode_until_termination(self) -> None:
        """Run until energy depleted."""
        config_dict = SystemAWConfigBuilder().with_initial_energy(10.0).build()
        config = SystemAWConfig(**config_dict)
        system = SystemAW(config)
        state = system.initialize_state()
        rng = np.random.default_rng(42)

        world = World(
            _make_empty_grid(5, 5),
            Position(x=2, y=2),
        )

        terminated = False
        for step in range(200):
            decide_result = system.decide(world, state, rng)
            action = decide_result.action
            moved = action in ("up", "down", "left", "right")
            outcome = ActionOutcome(
                action=action, moved=moved,
                new_position=Position(x=2, y=2),
            )
            obs = system.observe(world, world.agent_position)
            trans_result = system.transition(state, outcome, obs)
            state = trans_result.new_state
            if trans_result.terminated:
                terminated = True
                break

        assert terminated


class TestBehavioralProperties:
    """Behavioral property tests."""

    def test_curiosity_disabled_matches_system_a(self) -> None:
        """With base_curiosity=0, A+W combined scores are proportional to A's."""
        from axis.systems.system_a.config import SystemAConfig

        aw_dict = (
            SystemAWConfigBuilder()
            .with_base_curiosity(0.0)
            .build()
        )
        aw_config = SystemAWConfig(**aw_dict)
        aw_system = SystemAW(aw_config)

        a_dict = SystemAConfigBuilder().build()
        a_system = SystemA(SystemAConfig(**a_dict))

        world = World(
            _make_resource_grid(5, 5, 0.5),
            Position(x=2, y=2),
        )

        aw_state = aw_system.initialize_state()
        a_state = a_system.initialize_state()

        rng_aw = np.random.default_rng(123)
        rng_a = np.random.default_rng(123)

        aw_result = aw_system.decide(world, aw_state, rng_aw)
        a_result = a_system.decide(world, a_state, rng_a)

        # With base_curiosity=0, d_C=0. A+W scores = w_H * d_H * phi_H(a).
        # System A uses phi_H(a) directly. The A+W scores are a constant
        # multiple of System A's, so relative ordering must match.
        aw_scores = aw_result.decision_data["combined_scores"]
        a_contributions = a_result.decision_data["drive"]["action_contributions"]

        # Verify the scores are proportional (same ratios between actions)
        # Find the scale factor from a non-zero element
        scale = None
        for i in range(6):
            if abs(a_contributions[i]) > 1e-9:
                scale = aw_scores[i] / a_contributions[i]
                break
        assert scale is not None
        for i in range(6):
            assert aw_scores[i] == pytest.approx(
                scale * a_contributions[i], abs=1e-6,
            )

    def test_well_fed_prefers_exploration(self) -> None:
        """Well-fed agent: movement probability > consume probability."""
        config_dict = SystemAWConfigBuilder().with_initial_energy(100.0).build()
        config = SystemAWConfig(**config_dict)
        system = SystemAW(config)
        state = system.initialize_state()

        # Empty world: no resources
        world = World(_make_empty_grid(5, 5), Position(x=2, y=2))

        rng = np.random.default_rng(42)
        result = system.decide(world, state, rng)
        probs = result.decision_data["policy"]["probabilities"]
        movement_prob = sum(probs[:4])
        assert movement_prob > probs[4]  # movement > consume

    def test_starving_prefers_consume(self) -> None:
        """Starving agent with resource: consume probability dominates."""
        config_dict = SystemAWConfigBuilder().with_initial_energy(5.0).build()
        config = SystemAWConfig(**config_dict)
        system = SystemAW(config)
        state = system.initialize_state()

        # Resource-rich world
        world = World(_make_resource_grid(5, 5, 0.8), Position(x=2, y=2))

        rng = np.random.default_rng(42)
        result = system.decide(world, state, rng)
        probs = result.decision_data["policy"]["probabilities"]
        # Consume should have high probability
        assert probs[4] > probs[5]  # consume > stay

    def test_world_model_consistent_across_steps(self) -> None:
        """After 5 steps, visit counts sum = 6 (1 initial + 5 increments)."""
        config = SystemAWConfig(**SystemAWConfigBuilder().build())
        system = SystemAW(config)
        state = system.initialize_state()
        rng = np.random.default_rng(42)

        world = World(_make_empty_grid(5, 5), Position(x=2, y=2))

        for step in range(5):
            decide_result = system.decide(world, state, rng)
            action = decide_result.action
            moved = action in ("up", "down", "left", "right")
            outcome = ActionOutcome(
                action=action, moved=moved,
                new_position=Position(x=2, y=2),
            )
            obs = system.observe(world, world.agent_position)
            trans_result = system.transition(state, outcome, obs)
            state = trans_result.new_state

        total_visits = sum(
            count for _, count in state.world_model.visit_counts)
        assert total_visits == 6  # 1 initial + 5 steps


class TestFrameworkIntegration:
    """Framework runner integration test."""

    def test_framework_runner_integration(self) -> None:
        """Run a full experiment via RunExecutor."""
        config_dict = SystemAWConfigBuilder().build()
        framework_config = FrameworkConfig(
            general=GeneralConfig(seed=42),
            execution=ExecutionConfig(max_steps=10),
            world=BaseWorldConfig(
                world_type="grid_2d",
                grid_width=5,
                grid_height=5,
            ),
        )
        run_config = RunConfig(
            system_type="system_aw",
            system_config=config_dict,
            framework_config=framework_config,
            num_episodes=1,
            base_seed=42,
        )
        executor = RunExecutor()
        result = executor.execute(run_config)
        assert result.num_episodes == 1
        assert len(result.episode_traces) == 1
        assert result.summary.num_episodes == 1
