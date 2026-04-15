"""WP-2.4 integration tests -- full decide/transition pipeline."""

from __future__ import annotations

import numpy as np
import pytest

from axis.sdk.position import Position
from axis.sdk.types import DecideResult, TransitionResult
from axis.sdk.world_types import BaseWorldConfig
from axis.systems.construction_kit.types.actions import handle_consume
from axis.systems.system_a.config import SystemAConfig
from axis.systems.system_a.system import SystemA
from axis.systems.system_a.types import AgentState
from axis.systems.construction_kit.memory.types import ObservationBuffer
from axis.world.actions import create_action_registry
from axis.world.grid_2d.factory import create_world
from axis.world.grid_2d.factory import create_world
from axis.world.grid_2d.model import Cell, CellType, World
from tests.builders.system_config_builder import SystemAConfigBuilder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_resource_grid(
    width: int = 5, height: int = 5, value: float = 0.5,
) -> list[list[Cell]]:
    return [
        [Cell(cell_type=CellType.RESOURCE, resource_value=value)
         for _ in range(width)]
        for _ in range(height)
    ]


def _setup(
    seed: int = 42,
    config_dict: dict | None = None,
    grid: list[list[Cell]] | None = None,
) -> tuple[SystemA, object, World, AgentState, np.random.Generator]:
    """Build system, registry, world, initial state, and rng."""
    if config_dict is None:
        config_dict = SystemAConfigBuilder().build()
    config = SystemAConfig(**config_dict)
    system = SystemA(config)

    registry = create_action_registry()
    registry.register("consume", handle_consume)

    if grid is None:
        grid = _make_resource_grid()
    world = World(grid, Position(x=2, y=2))

    state = system.initialize_state()
    rng = np.random.default_rng(seed)
    return system, registry, world, state, rng


def _full_step(
    system: SystemA,
    registry: object,
    world: World,
    agent_state: AgentState,
    rng: np.random.Generator,
) -> tuple[AgentState, TransitionResult]:
    """Run one full decide -> apply -> transition cycle."""
    decide_result = system.decide(world, agent_state, rng)

    world.tick()

    context = {"max_consume": system.config.transition.max_consume}
    # type: ignore[attr-defined]
    outcome = registry.apply(world, decide_result.action, context=context)

    new_obs = system.sensor.observe(world, world.agent_position)
    result = system.transition(agent_state, outcome, new_obs)
    return result.new_state, result


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPipeline:
    """Full decide->apply->transition integration tests."""

    def test_decide_returns_valid_action(self) -> None:
        system, _, world, state, rng = _setup()
        result = system.decide(world, state, rng)
        assert isinstance(result, DecideResult)
        assert result.action in system.action_space()

    def test_decide_action_is_string(self) -> None:
        system, _, world, state, rng = _setup()
        result = system.decide(world, state, rng)
        assert isinstance(result.action, str)

    def test_transition_updates_energy(self) -> None:
        system, registry, world, state, rng = _setup()
        new_state, _ = _full_step(system, registry, world, state, rng)
        assert new_state.energy != state.energy

    def test_full_step_cycle(self) -> None:
        system, registry, world, state, rng = _setup()
        new_state, result = _full_step(system, registry, world, state, rng)
        assert isinstance(new_state, AgentState)
        assert new_state.energy >= 0.0
        assert new_state.energy <= system.config.agent.max_energy

    def test_multi_step_execution(self) -> None:
        system, registry, world, state, rng = _setup()
        energies = [state.energy]
        for _ in range(10):
            state, result = _full_step(system, registry, world, state, rng)
            energies.append(state.energy)
            if result.terminated:
                break
        assert len(energies) >= 2

    def test_termination_reached(self) -> None:
        config_dict = SystemAConfigBuilder().with_initial_energy(5).build()
        system, registry, world, state, rng = _setup(config_dict=config_dict)
        terminated = False
        for _ in range(200):
            state, result = _full_step(system, registry, world, state, rng)
            if result.terminated:
                terminated = True
                break
        assert terminated

    def test_consume_increases_energy(self) -> None:
        """When consuming a resource cell, energy gain should exceed cost."""
        config_dict = SystemAConfigBuilder().build()
        config = SystemAConfig(**config_dict)
        system = SystemA(config)

        grid = _make_resource_grid(5, 5, 0.8)
        world = World(grid, Position(x=2, y=2))
        state = AgentState(
            energy=50.0,
            observation_buffer=ObservationBuffer(entries=(), capacity=5),
        )

        from axis.sdk.world_types import ActionOutcome
        outcome = ActionOutcome(
            action="consume", moved=False,
            new_position=Position(x=2, y=2),
            data={"consumed": True, "resource_consumed": 0.8},
        )
        from axis.systems.construction_kit.observation.types import CellObservation, Observation
        obs = Observation(
            current=CellObservation(traversability=1.0, resource=0.0),
            up=CellObservation(traversability=1.0, resource=0.8),
            down=CellObservation(traversability=1.0, resource=0.8),
            left=CellObservation(traversability=1.0, resource=0.8),
            right=CellObservation(traversability=1.0, resource=0.8),
        )
        result = system.transition(state, outcome, obs)
        # 50 - consume_cost(1.0) + 10 * 0.8 = 57.0
        assert result.new_state.energy > state.energy

    def test_vitality_tracks_energy(self) -> None:
        system, registry, world, state, rng = _setup()
        for _ in range(5):
            assert system.vitality(state) == pytest.approx(
                state.energy / system.config.agent.max_energy
            )
            state, result = _full_step(system, registry, world, state, rng)
            if result.terminated:
                break
