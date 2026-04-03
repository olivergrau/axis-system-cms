"""Shared test fixtures for WP1–WP6."""

import pytest

from axis_system_a import (
    AgentState,
    Cell,
    CellObservation,
    CellType,
    MemoryEntry,
    MemoryState,
    Observation,
    Position,
    SimulationConfig,
    World,
    WorldConfig,
)


@pytest.fixture
def valid_config_dict() -> dict:
    """Minimal valid configuration dictionary."""
    return {
        "general": {"seed": 42},
        "world": {"grid_width": 10, "grid_height": 10},
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


@pytest.fixture
def valid_config(valid_config_dict: dict) -> SimulationConfig:
    return SimulationConfig(**valid_config_dict)


@pytest.fixture
def traversable_cell() -> CellObservation:
    return CellObservation(traversability=1.0, resource=0.5)


@pytest.fixture
def blocked_cell() -> CellObservation:
    return CellObservation(traversability=0.0, resource=0.0)


@pytest.fixture
def sample_observation(
    traversable_cell: CellObservation, blocked_cell: CellObservation
) -> Observation:
    return Observation(
        current=traversable_cell,
        up=traversable_cell,
        down=blocked_cell,
        left=traversable_cell,
        right=traversable_cell,
    )


@pytest.fixture
def empty_memory() -> MemoryState:
    return MemoryState(capacity=5)


@pytest.fixture
def sample_memory_entry(sample_observation: Observation) -> MemoryEntry:
    return MemoryEntry(timestep=0, observation=sample_observation)


# --- WP2 Fixtures ---


@pytest.fixture
def empty_cell() -> Cell:
    return Cell(cell_type=CellType.EMPTY, resource_value=0.0)


@pytest.fixture
def resource_cell() -> Cell:
    return Cell(cell_type=CellType.RESOURCE, resource_value=0.7)


@pytest.fixture
def obstacle_cell() -> Cell:
    return Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)


@pytest.fixture
def small_world_config() -> WorldConfig:
    return WorldConfig(grid_width=3, grid_height=3)


@pytest.fixture
def small_world(
    empty_cell: Cell,
    resource_cell: Cell,
    obstacle_cell: Cell,
) -> World:
    """3x3 world (y increases downward):

    Row 0: [EMPTY,    RESOURCE, EMPTY   ]
    Row 1: [EMPTY,    EMPTY,    OBSTACLE]
    Row 2: [RESOURCE, EMPTY,    EMPTY   ]

    Agent at (1, 1) (center).
    """
    grid = [
        [empty_cell, resource_cell, empty_cell],
        [empty_cell, empty_cell, obstacle_cell],
        [resource_cell, empty_cell, empty_cell],
    ]
    return World(grid=grid, agent_position=Position(x=1, y=1))


# --- WP5 Fixtures ---


@pytest.fixture
def all_open_observation() -> Observation:
    """All 4 directions traversable with varying resources."""
    return Observation(
        current=CellObservation(traversability=1.0, resource=0.5),
        up=CellObservation(traversability=1.0, resource=0.3),
        down=CellObservation(traversability=1.0, resource=0.1),
        left=CellObservation(traversability=1.0, resource=0.0),
        right=CellObservation(traversability=1.0, resource=0.8),
    )


@pytest.fixture
def all_blocked_movement_observation() -> Observation:
    """All 4 movement directions blocked (only CONSUME/STAY admissible)."""
    return Observation(
        current=CellObservation(traversability=1.0, resource=0.5),
        up=CellObservation(traversability=0.0, resource=0.0),
        down=CellObservation(traversability=0.0, resource=0.0),
        left=CellObservation(traversability=0.0, resource=0.0),
        right=CellObservation(traversability=0.0, resource=0.0),
    )


# --- WP6 Fixtures ---


@pytest.fixture
def default_step_kwargs() -> dict:
    """Standard cost parameters for transition tests."""
    return dict(
        move_cost=1.0,
        consume_cost=1.0,
        stay_cost=0.5,
        max_consume=1.0,
        energy_gain_factor=10.0,
        max_energy=100.0,
        resource_regen_rate=0.0,
    )


@pytest.fixture
def default_agent_state() -> AgentState:
    """Agent with energy=50.0 and empty memory (capacity=5)."""
    return AgentState(
        energy=50.0,
        memory_state=MemoryState(capacity=5),
    )
