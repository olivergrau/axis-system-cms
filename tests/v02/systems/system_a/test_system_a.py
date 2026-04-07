"""WP-2.3 verification tests -- System A conformance.

Tests the SystemA class, its sub-components, and their conformance
to the SDK interfaces defined in WP-1.1.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from axis.sdk.actions import MOVEMENT_DELTAS, STAY
from axis.sdk.interfaces import (
    DriveInterface,
    PolicyInterface,
    SensorInterface,
    SystemInterface,
    TransitionInterface,
)
from axis.sdk.position import Position
from axis.sdk.types import DecideResult, PolicyResult, TransitionResult
from axis.sdk.world_types import ActionOutcome, CellView
from axis.systems.system_a.actions import handle_consume
from axis.systems.system_a.config import (
    AgentConfig,
    PolicyConfig,
    SystemAConfig,
    TransitionConfig,
    WorldDynamicsConfig,
)
from axis.systems.system_a.drive import SystemAHungerDrive
from axis.systems.system_a.memory import update_memory
from axis.systems.system_a.policy import SystemAPolicy
from axis.systems.system_a.sensor import SystemASensor
from axis.systems.system_a.system import SystemA
from axis.systems.system_a.transition import SystemATransition
from axis.systems.system_a.types import (
    AgentState,
    CellObservation,
    HungerDriveOutput,
    MemoryEntry,
    MemoryState,
    Observation,
    clip_energy,
)
from axis.world.model import Cell, CellType, World
from tests.v02.builders.system_config_builder import SystemAConfigBuilder


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def config_dict() -> dict:
    """Default config dict from builder."""
    return SystemAConfigBuilder().build()


@pytest.fixture()
def config(config_dict: dict) -> SystemAConfig:
    """Default parsed SystemAConfig."""
    return SystemAConfig(**config_dict)


@pytest.fixture()
def system(config: SystemAConfig) -> SystemA:
    """Default SystemA instance."""
    return SystemA(config)


@pytest.fixture()
def initial_state(config: SystemAConfig) -> AgentState:
    """Agent state at initial energy with empty memory."""
    return AgentState(
        energy=config.agent.initial_energy,
        memory_state=MemoryState(
            entries=(), capacity=config.agent.memory_capacity,
        ),
    )


def _make_grid(width: int, height: int) -> list[list[Cell]]:
    """Create a uniform empty grid."""
    return [
        [Cell(cell_type=CellType.EMPTY, resource_value=0.0) for _ in range(width)]
        for _ in range(height)
    ]


def _make_resource_grid(width: int, height: int, value: float = 0.5) -> list[list[Cell]]:
    """Create a grid filled with resource cells."""
    return [
        [Cell(cell_type=CellType.RESOURCE, resource_value=value) for _ in range(width)]
        for _ in range(height)
    ]


@pytest.fixture()
def simple_world() -> World:
    """5x5 empty world, agent at center."""
    grid = _make_grid(5, 5)
    return World(grid, Position(x=2, y=2))


@pytest.fixture()
def resource_world() -> World:
    """5x5 resource world, agent at center."""
    grid = _make_resource_grid(5, 5, 0.5)
    return World(grid, Position(x=2, y=2))


@pytest.fixture()
def rng() -> np.random.Generator:
    """Seeded RNG for reproducible tests."""
    return np.random.default_rng(42)


# ===========================================================================
# 1. SystemAConfig parsing
# ===========================================================================


class TestSystemAConfig:
    """Config parsing and validation."""

    def test_construct_from_dict(self, config_dict: dict) -> None:
        config = SystemAConfig(**config_dict)
        assert config.agent.initial_energy == 50.0
        assert config.agent.max_energy == 100.0
        assert config.policy.selection_mode == "sample"
        assert config.transition.move_cost == 1.0

    def test_energy_bounds_validation(self) -> None:
        with pytest.raises(ValueError, match="initial_energy"):
            AgentConfig(initial_energy=200.0, max_energy=100.0, memory_capacity=5)

    def test_sub_configs_accessible(self, config: SystemAConfig) -> None:
        assert isinstance(config.agent, AgentConfig)
        assert isinstance(config.policy, PolicyConfig)
        assert isinstance(config.transition, TransitionConfig)
        assert isinstance(config.world_dynamics, WorldDynamicsConfig)

    def test_world_dynamics_defaults(self) -> None:
        cfg = SystemAConfig(
            agent=AgentConfig(initial_energy=50, max_energy=100, memory_capacity=5),
            policy=PolicyConfig(
                selection_mode="sample", temperature=1.0,
                stay_suppression=0.1, consume_weight=1.5,
            ),
            transition=TransitionConfig(
                move_cost=1.0, consume_cost=1.0, stay_cost=0.5,
                max_consume=1.0, energy_gain_factor=10.0,
            ),
        )
        assert cfg.world_dynamics.resource_regen_rate == 0.0


# ===========================================================================
# 2. SystemA construction
# ===========================================================================


class TestSystemAConstruction:
    """SystemA construction and identity."""

    def test_constructs_successfully(self, config: SystemAConfig) -> None:
        system = SystemA(config)
        assert system is not None

    def test_system_type(self, system: SystemA) -> None:
        assert system.system_type() == "system_a"

    def test_action_space(self, system: SystemA) -> None:
        assert system.action_space() == ("up", "down", "left", "right", "consume", "stay")


# ===========================================================================
# 3. SystemInterface conformance
# ===========================================================================


class TestSystemInterfaceConformance:
    """Protocol conformance checks."""

    def test_system_interface(self, system: SystemA) -> None:
        assert isinstance(system, SystemInterface)


# ===========================================================================
# 4. Sub-interface conformance
# ===========================================================================


class TestSubInterfaceConformance:
    """Sub-component protocol conformance."""

    def test_sensor_interface(self) -> None:
        sensor = SystemASensor()
        assert isinstance(sensor, SensorInterface)

    def test_drive_interface(self) -> None:
        drive = SystemAHungerDrive(
            consume_weight=1.5, stay_suppression=0.1, max_energy=100.0,
        )
        assert isinstance(drive, DriveInterface)

    def test_policy_interface(self) -> None:
        policy = SystemAPolicy(temperature=1.0, selection_mode="sample")
        assert isinstance(policy, PolicyInterface)

    def test_transition_interface(self) -> None:
        transition = SystemATransition(
            max_energy=100.0, move_cost=1.0, consume_cost=1.0,
            stay_cost=0.5, energy_gain_factor=10.0,
        )
        assert isinstance(transition, TransitionInterface)


# ===========================================================================
# 5. initialize_state
# ===========================================================================


class TestInitializeState:
    """State initialization from config dict."""

    def test_returns_agent_state(self, system: SystemA, config_dict: dict) -> None:
        state = system.initialize_state(config_dict)
        assert isinstance(state, AgentState)

    def test_initial_energy(self, system: SystemA, config_dict: dict) -> None:
        state = system.initialize_state(config_dict)
        assert state.energy == 50.0

    def test_empty_memory(self, system: SystemA, config_dict: dict) -> None:
        state = system.initialize_state(config_dict)
        assert state.memory_state.entries == ()

    def test_memory_capacity(self, system: SystemA, config_dict: dict) -> None:
        state = system.initialize_state(config_dict)
        assert state.memory_state.capacity == 5


# ===========================================================================
# 6. vitality
# ===========================================================================


class TestVitality:
    """Normalized vitality metric."""

    def test_full_energy(self, system: SystemA, config: SystemAConfig) -> None:
        state = AgentState(
            energy=config.agent.max_energy,
            memory_state=MemoryState(entries=(), capacity=5),
        )
        assert system.vitality(state) == 1.0

    def test_half_energy(self, system: SystemA, config: SystemAConfig) -> None:
        state = AgentState(
            energy=config.agent.max_energy / 2,
            memory_state=MemoryState(entries=(), capacity=5),
        )
        assert system.vitality(state) == 0.5

    def test_zero_energy(self, system: SystemA) -> None:
        state = AgentState(
            energy=0.0,
            memory_state=MemoryState(entries=(), capacity=5),
        )
        assert system.vitality(state) == 0.0


# ===========================================================================
# 7. Sensor
# ===========================================================================


class TestSensor:
    """Sensor observation tests."""

    def test_observation_structure(self, simple_world: World) -> None:
        sensor = SystemASensor()
        obs = sensor.observe(simple_world, simple_world.agent_position)
        assert isinstance(obs, Observation)
        assert isinstance(obs.current, CellObservation)
        assert isinstance(obs.up, CellObservation)
        assert isinstance(obs.down, CellObservation)
        assert isinstance(obs.left, CellObservation)
        assert isinstance(obs.right, CellObservation)

    def test_empty_cells_traversable(self, simple_world: World) -> None:
        sensor = SystemASensor()
        obs = sensor.observe(simple_world, simple_world.agent_position)
        assert obs.current.traversability == 1.0
        assert obs.up.traversability == 1.0

    def test_obstacle_neighbor(self) -> None:
        grid = _make_grid(5, 5)
        # Put obstacle above agent (x=2, y=1)
        grid[1][2] = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
        world = World(grid, Position(x=2, y=2))
        sensor = SystemASensor()
        obs = sensor.observe(world, world.agent_position)
        assert obs.up.traversability == 0.0

    def test_resource_neighbor(self) -> None:
        grid = _make_grid(5, 5)
        # Put resource to the right (x=3, y=2)
        grid[2][3] = Cell(cell_type=CellType.RESOURCE, resource_value=0.7)
        world = World(grid, Position(x=2, y=2))
        sensor = SystemASensor()
        obs = sensor.observe(world, world.agent_position)
        assert obs.right.resource == 0.7
        assert obs.right.traversability == 1.0

    def test_out_of_bounds(self) -> None:
        """Agent at corner -- some neighbors are OOB."""
        grid = _make_grid(5, 5)
        world = World(grid, Position(x=0, y=0))
        sensor = SystemASensor()
        obs = sensor.observe(world, world.agent_position)
        assert obs.up.traversability == 0.0
        assert obs.up.resource == 0.0
        assert obs.left.traversability == 0.0
        assert obs.left.resource == 0.0

    def test_to_vector(self, simple_world: World) -> None:
        sensor = SystemASensor()
        obs = sensor.observe(simple_world, simple_world.agent_position)
        vec = obs.to_vector()
        assert len(vec) == 10
        assert obs.dimension == 10


# ===========================================================================
# 8. Drive
# ===========================================================================


class TestDrive:
    """Hunger drive computation."""

    def _make_drive(self) -> SystemAHungerDrive:
        return SystemAHungerDrive(
            consume_weight=1.5, stay_suppression=0.1, max_energy=100.0,
        )

    def _make_observation(self, resource: float = 0.5) -> Observation:
        cell = CellObservation(traversability=1.0, resource=resource)
        return Observation(
            current=cell, up=cell, down=cell, left=cell, right=cell,
        )

    def test_high_energy_low_activation(self) -> None:
        drive = self._make_drive()
        state = AgentState(
            energy=100.0,
            memory_state=MemoryState(entries=(), capacity=5),
        )
        output = drive.compute(state, self._make_observation())
        assert output.activation == 0.0
        assert all(c == 0.0 for c in output.action_contributions)

    def test_low_energy_high_activation(self) -> None:
        drive = self._make_drive()
        state = AgentState(
            energy=10.0,
            memory_state=MemoryState(entries=(), capacity=5),
        )
        output = drive.compute(state, self._make_observation())
        assert output.activation == pytest.approx(0.9)
        # Movement contributions: d_h * resource = 0.9 * 0.5 = 0.45
        assert output.action_contributions[0] == pytest.approx(0.45)

    def test_stay_always_negative(self) -> None:
        drive = self._make_drive()
        state = AgentState(
            energy=50.0,
            memory_state=MemoryState(entries=(), capacity=5),
        )
        output = drive.compute(state, self._make_observation())
        assert output.action_contributions[5] < 0  # stay

    def test_consume_weighted(self) -> None:
        drive = self._make_drive()
        state = AgentState(
            energy=50.0,
            memory_state=MemoryState(entries=(), capacity=5),
        )
        obs = self._make_observation(resource=0.5)
        output = drive.compute(state, obs)
        d_h = 0.5  # 1 - 50/100
        expected_consume = d_h * 1.5 * 0.5  # d_h * consume_weight * resource
        assert output.action_contributions[4] == pytest.approx(expected_consume)

    def test_returns_hunger_drive_output(self) -> None:
        drive = self._make_drive()
        state = AgentState(
            energy=50.0,
            memory_state=MemoryState(entries=(), capacity=5),
        )
        output = drive.compute(state, self._make_observation())
        assert isinstance(output, HungerDriveOutput)
        assert len(output.action_contributions) == 6


# ===========================================================================
# 9. Policy
# ===========================================================================


class TestPolicy:
    """Policy action selection."""

    def _make_observation(self) -> Observation:
        cell = CellObservation(traversability=1.0, resource=0.5)
        blocked = CellObservation(traversability=0.0, resource=0.0)
        return Observation(
            current=cell, up=cell, down=cell, left=blocked, right=cell,
        )

    def _make_drive_output(self) -> HungerDriveOutput:
        return HungerDriveOutput(
            activation=0.5,
            action_contributions=(0.25, 0.25, 0.25, 0.25, 0.35, -0.05),
        )

    def test_returns_policy_result(self) -> None:
        policy = SystemAPolicy(temperature=1.0, selection_mode="sample")
        rng = np.random.default_rng(42)
        result = policy.select(self._make_drive_output(), self._make_observation(), rng)
        assert isinstance(result, PolicyResult)
        assert isinstance(result.action, str)

    def test_admissibility_masking(self) -> None:
        policy = SystemAPolicy(temperature=1.0, selection_mode="sample")
        rng = np.random.default_rng(42)
        result = policy.select(self._make_drive_output(), self._make_observation(), rng)
        probs = result.policy_data["probabilities"]
        assert probs[2] == 0.0  # left is blocked

    def test_argmax_deterministic(self) -> None:
        policy = SystemAPolicy(temperature=1.0, selection_mode="argmax")
        rng = np.random.default_rng(42)
        actions = set()
        for _ in range(10):
            result = policy.select(self._make_drive_output(), self._make_observation(), rng)
            actions.add(result.action)
        assert len(actions) == 1  # always same action

    def test_sample_reproducible(self) -> None:
        policy = SystemAPolicy(temperature=1.0, selection_mode="sample")
        drive_out = self._make_drive_output()
        obs = self._make_observation()
        rng1 = np.random.default_rng(123)
        rng2 = np.random.default_rng(123)
        r1 = policy.select(drive_out, obs, rng1)
        r2 = policy.select(drive_out, obs, rng2)
        assert r1.action == r2.action

    def test_policy_data_keys(self) -> None:
        policy = SystemAPolicy(temperature=1.0, selection_mode="sample")
        rng = np.random.default_rng(42)
        result = policy.select(self._make_drive_output(), self._make_observation(), rng)
        data = result.policy_data
        assert "raw_contributions" in data
        assert "admissibility_mask" in data
        assert "masked_contributions" in data
        assert "probabilities" in data
        assert "selected_action" in data
        assert "temperature" in data
        assert "selection_mode" in data


# ===========================================================================
# 10. Transition
# ===========================================================================


class TestTransition:
    """Transition function tests."""

    def _make_transition(self) -> SystemATransition:
        return SystemATransition(
            max_energy=100.0, move_cost=1.0, consume_cost=1.0,
            stay_cost=0.5, energy_gain_factor=10.0,
        )

    def _make_state(self, energy: float = 50.0) -> AgentState:
        return AgentState(
            energy=energy,
            memory_state=MemoryState(entries=(), capacity=5),
        )

    def _make_observation(self) -> Observation:
        cell = CellObservation(traversability=1.0, resource=0.0)
        return Observation(
            current=cell, up=cell, down=cell, left=cell, right=cell,
        )

    def test_movement_costs_energy(self) -> None:
        trans = self._make_transition()
        outcome = ActionOutcome(
            action="up", moved=True,
            new_position=Position(x=2, y=1), resource_consumed=0.0,
        )
        result = trans.transition(self._make_state(50.0), outcome, self._make_observation())
        assert result.new_state.energy == 49.0

    def test_consume_gains_energy(self) -> None:
        trans = self._make_transition()
        outcome = ActionOutcome(
            action="consume", moved=False,
            new_position=Position(x=2, y=2),
            consumed=True, resource_consumed=0.5,
        )
        result = trans.transition(self._make_state(50.0), outcome, self._make_observation())
        # energy = 50 - 1.0 (consume_cost) + 10 * 0.5 (gain) = 54.0
        assert result.new_state.energy == 54.0

    def test_energy_clipped_to_max(self) -> None:
        trans = self._make_transition()
        outcome = ActionOutcome(
            action="consume", moved=False,
            new_position=Position(x=2, y=2),
            consumed=True, resource_consumed=1.0,
        )
        result = trans.transition(self._make_state(95.0), outcome, self._make_observation())
        # energy = 95 - 1 + 10 = 104 -> clipped to 100
        assert result.new_state.energy == 100.0

    def test_stay_cost(self) -> None:
        trans = self._make_transition()
        outcome = ActionOutcome(
            action="stay", moved=False,
            new_position=Position(x=2, y=2), resource_consumed=0.0,
        )
        result = trans.transition(self._make_state(50.0), outcome, self._make_observation())
        assert result.new_state.energy == 49.5

    def test_termination_on_zero_energy(self) -> None:
        trans = self._make_transition()
        outcome = ActionOutcome(
            action="up", moved=True,
            new_position=Position(x=2, y=1), resource_consumed=0.0,
        )
        result = trans.transition(self._make_state(1.0), outcome, self._make_observation())
        assert result.new_state.energy == 0.0
        assert result.terminated is True
        assert result.termination_reason == "energy_depleted"

    def test_no_termination_with_energy(self) -> None:
        trans = self._make_transition()
        outcome = ActionOutcome(
            action="stay", moved=False,
            new_position=Position(x=2, y=2), resource_consumed=0.0,
        )
        result = trans.transition(self._make_state(50.0), outcome, self._make_observation())
        assert result.terminated is False
        assert result.termination_reason is None

    def test_memory_updated(self) -> None:
        trans = self._make_transition()
        outcome = ActionOutcome(
            action="stay", moved=False,
            new_position=Position(x=2, y=2), resource_consumed=0.0,
        )
        result = trans.transition(self._make_state(), outcome, self._make_observation())
        assert len(result.new_state.memory_state.entries) == 1

    def test_trace_data_keys(self) -> None:
        trans = self._make_transition()
        outcome = ActionOutcome(
            action="stay", moved=False,
            new_position=Position(x=2, y=2), resource_consumed=0.0,
        )
        result = trans.transition(self._make_state(), outcome, self._make_observation())
        assert isinstance(result, TransitionResult)
        assert "energy_before" in result.trace_data
        assert "energy_after" in result.trace_data
        assert "energy_delta" in result.trace_data
        assert "action_cost" in result.trace_data
        assert "energy_gain" in result.trace_data


# ===========================================================================
# 11. Consume handler
# ===========================================================================


class TestConsumeHandler:
    """Consume action handler tests."""

    def test_consume_on_resource_cell(self) -> None:
        grid = _make_grid(5, 5)
        grid[2][2] = Cell(cell_type=CellType.RESOURCE, resource_value=0.8)
        world = World(grid, Position(x=2, y=2))
        outcome = handle_consume(world, context={"max_consume": 1.0})
        assert outcome.consumed is True
        assert outcome.resource_consumed == 0.8
        assert outcome.action == "consume"

    def test_consume_on_empty_cell(self) -> None:
        grid = _make_grid(5, 5)
        world = World(grid, Position(x=2, y=2))
        outcome = handle_consume(world, context={"max_consume": 1.0})
        assert outcome.consumed is False
        assert outcome.resource_consumed == 0.0

    def test_partial_consume(self) -> None:
        grid = _make_grid(5, 5)
        grid[2][2] = Cell(cell_type=CellType.RESOURCE, resource_value=0.8)
        world = World(grid, Position(x=2, y=2))
        outcome = handle_consume(world, context={"max_consume": 0.3})
        assert outcome.consumed is True
        assert outcome.resource_consumed == pytest.approx(0.3)
        # Cell should still be resource with remainder
        cell = world.get_internal_cell(Position(x=2, y=2))
        assert cell.cell_type == CellType.RESOURCE
        assert cell.resource_value == pytest.approx(0.5)

    def test_full_consume_makes_cell_empty(self) -> None:
        grid = _make_grid(5, 5)
        grid[2][2] = Cell(cell_type=CellType.RESOURCE, resource_value=0.5)
        world = World(grid, Position(x=2, y=2))
        handle_consume(world, context={"max_consume": 1.0})
        cell = world.get_internal_cell(Position(x=2, y=2))
        assert cell.cell_type == CellType.EMPTY
        assert cell.resource_value == 0.0


# ===========================================================================
# 12. decide() integration
# ===========================================================================


class TestDecideIntegration:
    """Integration test for decide()."""

    def test_returns_decide_result(
        self, system: SystemA, resource_world: World,
        initial_state: AgentState, rng: np.random.Generator,
    ) -> None:
        result = system.decide(resource_world, initial_state, rng)
        assert isinstance(result, DecideResult)

    def test_action_in_action_space(
        self, system: SystemA, resource_world: World,
        initial_state: AgentState, rng: np.random.Generator,
    ) -> None:
        result = system.decide(resource_world, initial_state, rng)
        assert result.action in system.action_space()

    def test_decision_data_structure(
        self, system: SystemA, resource_world: World,
        initial_state: AgentState, rng: np.random.Generator,
    ) -> None:
        result = system.decide(resource_world, initial_state, rng)
        assert "observation" in result.decision_data
        assert "drive" in result.decision_data
        assert "policy" in result.decision_data
        assert "activation" in result.decision_data["drive"]
        assert "action_contributions" in result.decision_data["drive"]


# ===========================================================================
# 13. transition() integration
# ===========================================================================


class TestTransitionIntegration:
    """Integration test for transition()."""

    def test_returns_transition_result(self, system: SystemA) -> None:
        state = AgentState(
            energy=50.0,
            memory_state=MemoryState(entries=(), capacity=5),
        )
        outcome = ActionOutcome(
            action="up", moved=True,
            new_position=Position(x=2, y=1), resource_consumed=0.0,
        )
        obs = Observation(
            current=CellObservation(traversability=1.0, resource=0.0),
            up=CellObservation(traversability=1.0, resource=0.0),
            down=CellObservation(traversability=1.0, resource=0.0),
            left=CellObservation(traversability=1.0, resource=0.0),
            right=CellObservation(traversability=1.0, resource=0.0),
        )
        result = system.transition(state, outcome, obs)
        assert isinstance(result, TransitionResult)
        assert result.new_state.energy < state.energy

    def test_trace_data_present(self, system: SystemA) -> None:
        state = AgentState(
            energy=50.0,
            memory_state=MemoryState(entries=(), capacity=5),
        )
        outcome = ActionOutcome(
            action="stay", moved=False,
            new_position=Position(x=2, y=2), resource_consumed=0.0,
        )
        obs = Observation(
            current=CellObservation(traversability=1.0, resource=0.0),
            up=CellObservation(traversability=1.0, resource=0.0),
            down=CellObservation(traversability=1.0, resource=0.0),
            left=CellObservation(traversability=1.0, resource=0.0),
            right=CellObservation(traversability=1.0, resource=0.0),
        )
        result = system.transition(state, outcome, obs)
        assert "energy_before" in result.trace_data
        assert "energy_after" in result.trace_data


# ===========================================================================
# 14. Import verification
# ===========================================================================


class TestImportVerification:
    """Package import tests."""

    def test_top_level_imports(self) -> None:
        from axis.systems.system_a import SystemA, SystemAConfig, handle_consume  # noqa: F401

    def test_system_a_module_imports(self) -> None:
        from axis.systems.system_a.types import AgentState, Observation  # noqa: F401
        from axis.systems.system_a.sensor import SystemASensor  # noqa: F401
        from axis.systems.system_a.drive import SystemAHungerDrive  # noqa: F401
        from axis.systems.system_a.policy import SystemAPolicy  # noqa: F401
        from axis.systems.system_a.transition import SystemATransition  # noqa: F401
        from axis.systems.system_a.memory import update_memory  # noqa: F401


# ===========================================================================
# Supporting types
# ===========================================================================


class TestTypes:
    """System A internal types."""

    def test_clip_energy_within_bounds(self) -> None:
        assert clip_energy(50.0, 100.0) == 50.0

    def test_clip_energy_above_max(self) -> None:
        assert clip_energy(150.0, 100.0) == 100.0

    def test_clip_energy_below_zero(self) -> None:
        assert clip_energy(-10.0, 100.0) == 0.0

    def test_memory_state_capacity_validation(self) -> None:
        cell = CellObservation(traversability=1.0, resource=0.0)
        obs = Observation(
            current=cell, up=cell, down=cell, left=cell, right=cell,
        )
        entries = tuple(
            MemoryEntry(timestep=i, observation=obs) for i in range(5)
        )
        # Should succeed with capacity=5
        MemoryState(entries=entries, capacity=5)
        # Should fail with capacity=3
        with pytest.raises(ValueError, match="exceeds capacity"):
            MemoryState(entries=entries, capacity=3)


class TestMemory:
    """Memory update function."""

    def _make_observation(self) -> Observation:
        cell = CellObservation(traversability=1.0, resource=0.0)
        return Observation(
            current=cell, up=cell, down=cell, left=cell, right=cell,
        )

    def test_append_entry(self) -> None:
        mem = MemoryState(entries=(), capacity=5)
        new_mem = update_memory(mem, self._make_observation(), timestep=0)
        assert len(new_mem.entries) == 1
        assert new_mem.entries[0].timestep == 0

    def test_fifo_overflow(self) -> None:
        mem = MemoryState(entries=(), capacity=2)
        mem = update_memory(mem, self._make_observation(), timestep=0)
        mem = update_memory(mem, self._make_observation(), timestep=1)
        mem = update_memory(mem, self._make_observation(), timestep=2)
        assert len(mem.entries) == 2
        assert mem.entries[0].timestep == 1  # oldest dropped
        assert mem.entries[1].timestep == 2
