"""World model: Cell, World, and factory for AXIS System A."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axis_system_a.config import WorldConfig
from axis_system_a.enums import CellType
from axis_system_a.types import Position


class Cell(BaseModel):
    """A single cell in the grid world.

    Invariants:
    - OBSTACLE: resource_value == 0, not traversable
    - RESOURCE: resource_value > 0, traversable
    - EMPTY: resource_value == 0, traversable
    """

    model_config = ConfigDict(frozen=True)

    cell_type: CellType
    resource_value: float = Field(..., ge=0, le=1)

    @model_validator(mode="after")
    def check_cell_invariants(self) -> Cell:
        if self.cell_type == CellType.OBSTACLE and self.resource_value != 0.0:
            raise ValueError("OBSTACLE cells must have resource_value == 0")
        if self.cell_type == CellType.RESOURCE and self.resource_value <= 0.0:
            raise ValueError("RESOURCE cells must have resource_value > 0")
        if self.cell_type == CellType.EMPTY and self.resource_value != 0.0:
            raise ValueError("EMPTY cells must have resource_value == 0")
        return self

    @property
    def is_traversable(self) -> bool:
        """EMPTY and RESOURCE cells are traversable; OBSTACLE cells are not."""
        return self.cell_type != CellType.OBSTACLE


class World:
    """Passive 2D grid world state container.

    Stores the grid of cells and the agent's position.
    Provides side-effect-free read access and explicit mutation methods.
    Does not contain behavioral logic.
    """

    def __init__(
        self,
        grid: list[list[Cell]],
        agent_position: Position,
    ) -> None:
        if not grid or not grid[0]:
            raise ValueError("Grid must be non-empty")

        height = len(grid)
        width = len(grid[0])

        for y, row in enumerate(grid):
            if len(row) != width:
                raise ValueError(
                    f"Row {y} has width {len(row)}, expected {width}"
                )

        if not (0 <= agent_position.x < width and 0 <= agent_position.y < height):
            raise ValueError(
                f"Agent position {agent_position} is out of bounds "
                f"for grid of size ({width}, {height})"
            )

        cell_at_agent = grid[agent_position.y][agent_position.x]
        if not cell_at_agent.is_traversable:
            raise ValueError(
                f"Agent position {agent_position} is on a non-traversable cell"
            )

        self._grid: list[list[Cell]] = grid
        self._width: int = width
        self._height: int = height
        self._agent_position: Position = agent_position

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def agent_position(self) -> Position:
        return self._agent_position

    @agent_position.setter
    def agent_position(self, position: Position) -> None:
        if not self.is_within_bounds(position):
            raise ValueError(f"Position {position} is out of bounds")
        if not self._grid[position.y][position.x].is_traversable:
            raise ValueError(
                f"Position {position} is on a non-traversable cell")
        self._agent_position = position

    def is_within_bounds(self, position: Position) -> bool:
        return 0 <= position.x < self._width and 0 <= position.y < self._height

    def get_cell(self, position: Position) -> Cell:
        if not self.is_within_bounds(position):
            raise ValueError(
                f"Position {position} is out of bounds "
                f"for grid of size ({self._width}, {self._height})"
            )
        return self._grid[position.y][position.x]

    def set_cell(self, position: Position, cell: Cell) -> None:
        if not self.is_within_bounds(position):
            raise ValueError(
                f"Position {position} is out of bounds "
                f"for grid of size ({self._width}, {self._height})"
            )
        self._grid[position.y][position.x] = cell

    def is_traversable(self, position: Position) -> bool:
        if not self.is_within_bounds(position):
            return False
        return self._grid[position.y][position.x].is_traversable


def create_world(
    config: WorldConfig,
    agent_position: Position,
    grid: list[list[Cell]] | None = None,
) -> World:
    """Create a World from configuration.

    If grid is None, creates a grid of EMPTY cells.
    If grid is provided, validates dimensions against config.
    """
    if grid is None:
        empty_cell = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
        grid = [
            [empty_cell for _ in range(config.grid_width)]
            for _ in range(config.grid_height)
        ]
    else:
        if len(grid) != config.grid_height:
            raise ValueError(
                f"Grid height {len(grid)} does not match "
                f"config grid_height {config.grid_height}"
            )
        for y, row in enumerate(grid):
            if len(row) != config.grid_width:
                raise ValueError(
                    f"Row {y} width {len(row)} does not match "
                    f"config grid_width {config.grid_width}"
                )

    return World(grid=grid, agent_position=agent_position)
