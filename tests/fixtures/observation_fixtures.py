"""Observation factory and fixtures."""

from __future__ import annotations

import pytest

from axis_system_a import CellObservation, Observation


def make_observation(
    current: float = 0.0,
    up: float = 0.0,
    down: float = 0.0,
    left: float = 0.0,
    right: float = 0.0,
    *,
    b_up: float = 1.0,
    b_down: float = 1.0,
    b_left: float = 1.0,
    b_right: float = 1.0,
) -> Observation:
    """Create an Observation with specified resource values and traversabilities.

    By default all directions are traversable (b=1.0) and current cell is always
    traversable (b_current=1.0). Resource values default to 0.0.
    """
    return Observation(
        current=CellObservation(traversability=1.0, resource=current),
        up=CellObservation(traversability=b_up, resource=up),
        down=CellObservation(traversability=b_down, resource=down),
        left=CellObservation(traversability=b_left, resource=left),
        right=CellObservation(traversability=b_right, resource=right),
    )


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


@pytest.fixture
def uniform_observation() -> Observation:
    """All cells identical: traversable with resource=0.5."""
    return make_observation(0.5, 0.5, 0.5, 0.5, 0.5)


@pytest.fixture
def sample_observation() -> Observation:
    """Mixed observation: current and 3 dirs traversable, down blocked."""
    return Observation(
        current=CellObservation(traversability=1.0, resource=0.5),
        up=CellObservation(traversability=1.0, resource=0.5),
        down=CellObservation(traversability=0.0, resource=0.0),
        left=CellObservation(traversability=1.0, resource=0.5),
        right=CellObservation(traversability=1.0, resource=0.5),
    )
