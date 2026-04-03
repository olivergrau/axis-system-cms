"""Fluent builder for World objects."""

from __future__ import annotations

from axis_system_a import Cell, CellType, Position, World


class WorldBuilder:
    """Fluent builder for constructing World objects in tests.

    Default: 3x3 empty grid with agent at (1, 1).
    """

    def __init__(self) -> None:
        self._width = 3
        self._height = 3
        self._agent_x = 1
        self._agent_y = 1
        self._cells: dict[tuple[int, int], Cell] = {}

    def with_size(self, width: int, height: int) -> WorldBuilder:
        self._width = width
        self._height = height
        return self

    def with_agent_at(self, x: int, y: int) -> WorldBuilder:
        self._agent_x = x
        self._agent_y = y
        return self

    def with_food(self, x: int, y: int, value: float = 0.5) -> WorldBuilder:
        self._cells[(x, y)] = Cell(
            cell_type=CellType.RESOURCE, resource_value=value)
        return self

    def with_obstacle(self, x: int, y: int) -> WorldBuilder:
        self._cells[(x, y)] = Cell(
            cell_type=CellType.OBSTACLE, resource_value=0.0)
        return self

    def with_empty(self, x: int, y: int) -> WorldBuilder:
        self._cells[(x, y)] = Cell(
            cell_type=CellType.EMPTY, resource_value=0.0)
        return self

    def with_all_food(self, value: float = 0.5) -> WorldBuilder:
        for y in range(self._height):
            for x in range(self._width):
                if (x, y) not in self._cells or self._cells[(x, y)].cell_type != CellType.OBSTACLE:
                    self._cells[(x, y)] = Cell(
                        cell_type=CellType.RESOURCE, resource_value=value)
        return self

    def build(self) -> World:
        empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
        grid = [
            [self._cells.get((x, y), empty) for x in range(self._width)]
            for y in range(self._height)
        ]
        return World(grid=grid, agent_position=Position(x=self._agent_x, y=self._agent_y))
