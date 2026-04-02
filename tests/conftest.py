"""Shared test fixtures for WP1."""

import pytest

from axis_system_a import (
    CellObservation,
    MemoryState,
    Observation,
    SimulationConfig,
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
