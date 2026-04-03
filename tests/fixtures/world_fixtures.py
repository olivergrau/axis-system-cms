"""World fixtures and cell factory functions."""

from __future__ import annotations

import pytest

from axis_system_a import Cell, CellType, Position, World, WorldConfig
from tests.builders.world_builder import WorldBuilder


def empty_cell() -> Cell:
    return Cell(cell_type=CellType.EMPTY, resource_value=0.0)


def resource_cell(value: float = 0.7) -> Cell:
    return Cell(cell_type=CellType.RESOURCE, resource_value=value)


def obstacle_cell() -> Cell:
    return Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)


@pytest.fixture(name="empty_cell")
def empty_cell_fixture() -> Cell:
    return empty_cell()


@pytest.fixture(name="resource_cell")
def resource_cell_fixture() -> Cell:
    return resource_cell()


@pytest.fixture(name="obstacle_cell")
def obstacle_cell_fixture() -> Cell:
    return obstacle_cell()


@pytest.fixture
def small_world_config() -> WorldConfig:
    return WorldConfig(grid_width=3, grid_height=3)


@pytest.fixture
def small_world() -> World:
    """3x3 world:
    Row 0: [EMPTY,    RESOURCE(0.7), EMPTY   ]
    Row 1: [EMPTY,    EMPTY,         OBSTACLE]
    Row 2: [RESOURCE(0.7), EMPTY,    EMPTY   ]
    Agent at (1, 1).
    """
    return (
        WorldBuilder()
        .with_food(1, 0, 0.7)
        .with_obstacle(2, 1)
        .with_food(0, 2, 0.7)
        .build()
    )


@pytest.fixture
def empty_3x3_world() -> World:
    """3x3 all-empty grid, agent at center."""
    return WorldBuilder().build()


@pytest.fixture
def resource_everywhere_world() -> World:
    """3x3 all RESOURCE(0.8), center RESOURCE(0.5), agent at center."""
    return (
        WorldBuilder()
        .with_all_food(0.8)
        .with_food(1, 1, 0.5)
        .build()
    )


@pytest.fixture
def corridor_world() -> World:
    """3x1 corridor: agent at (0,0), resource at (2,0)."""
    return (
        WorldBuilder()
        .with_size(3, 1)
        .with_agent_at(0, 0)
        .with_food(2, 0, 1.0)
        .build()
    )
