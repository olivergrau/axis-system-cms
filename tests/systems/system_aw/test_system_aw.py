"""WP-10 unit tests -- SystemAW construction, interface, decide, transition."""

from __future__ import annotations

import numpy as np
import pytest

from axis.framework.registry import create_system, registered_system_types
from axis.sdk.position import Position
from axis.sdk.types import DecideResult, TransitionResult
from axis.sdk.world_types import ActionOutcome
from axis.systems.system_a.types import CellObservation, MemoryState, Observation
from axis.systems.system_aw.config import SystemAWConfig
from axis.systems.system_aw.system import SystemAW
from axis.systems.system_aw.types import AgentStateAW
from axis.world.grid_2d.model import Cell, CellType, World
from tests.builders.system_aw_config_builder import SystemAWConfigBuilder


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def config_dict() -> dict:
    return SystemAWConfigBuilder().build()


@pytest.fixture()
def config(config_dict: dict) -> SystemAWConfig:
    return SystemAWConfig(**config_dict)


@pytest.fixture()
def system(config: SystemAWConfig) -> SystemAW:
    return SystemAW(config)


@pytest.fixture()
def initial_state(system: SystemAW) -> AgentStateAW:
    return system.initialize_state()


def _make_grid(width: int, height: int) -> list[list[Cell]]:
    return [
        [Cell(cell_type=CellType.EMPTY, resource_value=0.0)
         for _ in range(width)]
        for _ in range(height)
    ]


def _make_resource_grid(width: int, height: int, value: float = 0.5) -> list[list[Cell]]:
    return [
        [Cell(cell_type=CellType.RESOURCE, resource_value=value)
         for _ in range(width)]
        for _ in range(height)
    ]


@pytest.fixture()
def simple_world() -> World:
    grid = _make_grid(5, 5)
    return World(grid, Position(x=2, y=2))


@pytest.fixture()
def resource_world() -> World:
    grid = _make_resource_grid(5, 5, 0.5)
    return World(grid, Position(x=2, y=2))


@pytest.fixture()
def rng() -> np.random.Generator:
    return np.random.default_rng(42)


def _make_observation() -> Observation:
    cell = CellObservation(traversability=1.0, resource=0.0)
    return Observation(current=cell, up=cell, down=cell, left=cell, right=cell)


# ===========================================================================
# Construction and Interface
# ===========================================================================


class TestConstructionAndInterface:
    """SystemAW construction and identity."""

    def test_system_type(self, system: SystemAW) -> None:
        assert system.system_type() == "system_aw"

    def test_action_space(self, system: SystemAW) -> None:
        assert system.action_space() == ("up", "down", "left", "right", "consume", "stay")

    def test_initialize_state(self, system: SystemAW) -> None:
        state = system.initialize_state()
        assert isinstance(state, AgentStateAW)
        assert state.energy == 50.0
        assert state.memory_state.entries == ()
        assert state.world_model.relative_position == (0, 0)
        # World model starts with visit count 1 at origin
        visits = dict(state.world_model.visit_counts)
        assert visits.get((0, 0)) == 1

    def test_vitality(self, system: SystemAW) -> None:
        state = system.initialize_state()
        assert system.vitality(state) == pytest.approx(0.5)

    def test_action_handlers(self, system: SystemAW) -> None:
        handlers = system.action_handlers()
        assert "consume" in handlers
        assert callable(handlers["consume"])

    def test_action_context(self, system: SystemAW) -> None:
        context = system.action_context()
        assert "max_consume" in context

    def test_observe(self, system: SystemAW, simple_world: World) -> None:
        obs = system.observe(simple_world, simple_world.agent_position)
        assert isinstance(obs, Observation)


# ===========================================================================
# Registration
# ===========================================================================


class TestRegistration:
    """Framework registration tests."""

    def test_registry_create_system(self, config_dict: dict) -> None:
        system = create_system("system_aw", config_dict)
        assert system.system_type() == "system_aw"

    def test_registry_system_type_listed(self) -> None:
        assert "system_aw" in registered_system_types()

    def test_registry_default_curiosity(self) -> None:
        """Config without curiosity/arbitration keys uses defaults."""
        base = SystemAWConfigBuilder().build()
        # Remove curiosity and arbitration to test defaults
        base.pop("curiosity", None)
        base.pop("arbitration", None)
        system = create_system("system_aw", base)
        assert system.system_type() == "system_aw"


# ===========================================================================
# Decide
# ===========================================================================


class TestDecide:
    """SystemAW.decide() tests."""

    def test_decide_returns_decide_result(
        self, system: SystemAW, resource_world: World,
        initial_state: AgentStateAW, rng: np.random.Generator,
    ) -> None:
        result = system.decide(resource_world, initial_state, rng)
        assert isinstance(result, DecideResult)

    def test_decide_action_in_action_space(
        self, system: SystemAW, resource_world: World,
        initial_state: AgentStateAW, rng: np.random.Generator,
    ) -> None:
        result = system.decide(resource_world, initial_state, rng)
        assert result.action in system.action_space()

    def test_decide_decision_data_structure(
        self, system: SystemAW, resource_world: World,
        initial_state: AgentStateAW, rng: np.random.Generator,
    ) -> None:
        result = system.decide(resource_world, initial_state, rng)
        data = result.decision_data
        assert "observation" in data
        assert "hunger_drive" in data
        assert "curiosity_drive" in data
        assert "arbitration" in data
        assert "combined_scores" in data
        assert "policy" in data

    def test_decide_curiosity_data_present(
        self, system: SystemAW, resource_world: World,
        initial_state: AgentStateAW, rng: np.random.Generator,
    ) -> None:
        result = system.decide(resource_world, initial_state, rng)
        cd = result.decision_data["curiosity_drive"]
        assert "activation" in cd
        assert "spatial_novelty" in cd
        assert "sensory_novelty" in cd
        assert "composite_novelty" in cd
        assert "action_contributions" in cd


# ===========================================================================
# Transition
# ===========================================================================


class TestTransition:
    """SystemAW.transition() tests."""

    def test_transition_returns_transition_result(
        self, system: SystemAW, initial_state: AgentStateAW,
    ) -> None:
        outcome = ActionOutcome(
            action="up", moved=True,
            new_position=Position(x=2, y=1),
        )
        result = system.transition(initial_state, outcome, _make_observation())
        assert isinstance(result, TransitionResult)

    def test_transition_new_state_is_aw(
        self, system: SystemAW, initial_state: AgentStateAW,
    ) -> None:
        outcome = ActionOutcome(
            action="up", moved=True,
            new_position=Position(x=2, y=1),
        )
        result = system.transition(initial_state, outcome, _make_observation())
        assert isinstance(result.new_state, AgentStateAW)

    def test_transition_updates_world_model(
        self, system: SystemAW, initial_state: AgentStateAW,
    ) -> None:
        outcome = ActionOutcome(
            action="right", moved=True,
            new_position=Position(x=3, y=2),
        )
        result = system.transition(initial_state, outcome, _make_observation())
        assert result.new_state.world_model.relative_position == (1, 0)

    def test_transition_updates_energy(
        self, system: SystemAW, initial_state: AgentStateAW,
    ) -> None:
        outcome = ActionOutcome(
            action="up", moved=True,
            new_position=Position(x=2, y=1),
        )
        result = system.transition(initial_state, outcome, _make_observation())
        assert result.new_state.energy < initial_state.energy
