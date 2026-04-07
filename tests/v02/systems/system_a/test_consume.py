"""WP-2.4 unit tests -- handle_consume."""

from __future__ import annotations

import pytest

from axis.sdk.position import Position
from axis.sdk.world_types import ActionOutcome
from axis.systems.system_a.actions import handle_consume
from axis.world.model import Cell, CellType, World


def _make_grid(width: int = 5, height: int = 5) -> list[list[Cell]]:
    return [
        [Cell(cell_type=CellType.EMPTY, resource_value=0.0) for _ in range(width)]
        for _ in range(height)
    ]


class TestConsumeHandler:
    """handle_consume() unit tests."""

    def test_consume_resource_cell(self) -> None:
        grid = _make_grid()
        grid[2][2] = Cell(cell_type=CellType.RESOURCE, resource_value=0.8)
        world = World(grid, Position(x=2, y=2))
        outcome = handle_consume(world, context={"max_consume": 1.0})
        assert outcome.consumed is True
        assert outcome.resource_consumed == 0.8

    def test_consume_empty_cell(self) -> None:
        grid = _make_grid()
        world = World(grid, Position(x=2, y=2))
        outcome = handle_consume(world, context={"max_consume": 1.0})
        assert outcome.consumed is False
        assert outcome.resource_consumed == 0.0

    def test_partial_consume(self) -> None:
        grid = _make_grid()
        grid[2][2] = Cell(cell_type=CellType.RESOURCE, resource_value=0.8)
        world = World(grid, Position(x=2, y=2))
        outcome = handle_consume(world, context={"max_consume": 0.3})
        assert outcome.consumed is True
        assert outcome.resource_consumed == pytest.approx(0.3)
        cell = world.get_internal_cell(Position(x=2, y=2))
        assert cell.cell_type == CellType.RESOURCE
        assert cell.resource_value == pytest.approx(0.5)

    def test_full_consume(self) -> None:
        grid = _make_grid()
        grid[2][2] = Cell(cell_type=CellType.RESOURCE, resource_value=0.5)
        world = World(grid, Position(x=2, y=2))
        outcome = handle_consume(world, context={"max_consume": 1.0})
        assert outcome.consumed is True
        cell = world.get_internal_cell(Position(x=2, y=2))
        assert cell.cell_type == CellType.EMPTY
        assert cell.resource_value == 0.0

    def test_world_cell_updated(self) -> None:
        grid = _make_grid()
        grid[2][2] = Cell(cell_type=CellType.RESOURCE, resource_value=0.8)
        world = World(grid, Position(x=2, y=2))
        handle_consume(world, context={"max_consume": 0.5})
        cell = world.get_internal_cell(Position(x=2, y=2))
        assert cell.resource_value == pytest.approx(0.3)

    def test_returns_action_outcome(self) -> None:
        grid = _make_grid()
        world = World(grid, Position(x=2, y=2))
        outcome = handle_consume(world, context={"max_consume": 1.0})
        assert isinstance(outcome, ActionOutcome)
        assert outcome.action == "consume"

    def test_agent_position_unchanged(self) -> None:
        grid = _make_grid()
        grid[2][2] = Cell(cell_type=CellType.RESOURCE, resource_value=0.5)
        world = World(grid, Position(x=2, y=2))
        outcome = handle_consume(world, context={"max_consume": 1.0})
        assert outcome.moved is False
        assert outcome.new_position == Position(x=2, y=2)
