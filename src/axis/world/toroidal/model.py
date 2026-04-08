"""Toroidal grid world -- edges wrap around.

A 2D grid where movement wraps at the edges instead of being blocked.
Cell types, resources, and regeneration work identically to the
built-in ``grid_2d`` world. Only the movement topology differs.

Reuses the grid_2d ``Cell``, ``CellType``, and ``apply_regeneration``
because the internal cell model is identical -- the only difference
is coordinate wrapping.

Registered as world type ``"toroidal"``.
"""

from __future__ import annotations

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.world_types import CellView
from axis.world.grid_2d.model import Cell, CellType


class ToroidalWorld:
    """A 2D grid where movement wraps around at the edges.

    Walking off the right edge places the agent on the left edge
    (and vice versa). Same for top/bottom. All other behavior
    (cells, resources, obstacles) is identical to the built-in grid.

    Satisfies MutableWorldProtocol.
    """

    def __init__(
        self,
        grid: list[list[Cell]],
        agent_position: Position,
        *,
        regen_rate: float = 0.0,
    ) -> None:
        if not grid or not grid[0]:
            raise ValueError("Grid must be non-empty")
        self._height = len(grid)
        self._width = len(grid[0])

        for y, row in enumerate(grid):
            if len(row) != self._width:
                raise ValueError(
                    f"Row {y} has width {len(row)}, expected {self._width}"
                )

        self._grid = grid
        self._regen_rate = regen_rate
        # Wrap the starting position for safety
        wrapped = self._wrap(agent_position)
        if not self._grid[wrapped.y][wrapped.x].is_traversable:
            raise ValueError(
                f"Agent position {wrapped} is on a non-traversable cell"
            )
        self._agent_position = wrapped

    def _wrap(self, position: Position) -> Position:
        """Wrap coordinates to stay within the grid (toroidal)."""
        return Position(
            x=position.x % self._width,
            y=position.y % self._height,
        )

    # --- WorldView protocol (read-only) ---

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
        wrapped = self._wrap(position)
        if not self._grid[wrapped.y][wrapped.x].is_traversable:
            raise ValueError(
                f"Position {wrapped} is on a non-traversable cell"
            )
        self._agent_position = wrapped

    def get_cell(self, position: Position) -> CellView:
        if not self.is_within_bounds(position):
            raise ValueError(
                f"Position {position} is out of bounds "
                f"for grid of size ({self._width}, {self._height})"
            )
        cell = self._grid[position.y][position.x]
        return CellView(
            cell_type=cell.cell_type.value,
            resource_value=cell.resource_value,
        )

    def is_within_bounds(self, position: Position) -> bool:
        return 0 <= position.x < self._width and 0 <= position.y < self._height

    def is_traversable(self, position: Position) -> bool:
        # Wrap first, then check -- this is the toroidal magic.
        wrapped = self._wrap(position)
        return self._grid[wrapped.y][wrapped.x].is_traversable

    # --- Internal mutation API (framework-only) ---

    def get_internal_cell(self, position: Position) -> Cell:
        if not self.is_within_bounds(position):
            raise ValueError(f"Position {position} is out of bounds")
        return self._grid[position.y][position.x]

    def set_cell(self, position: Position, cell: Cell) -> None:
        if not self.is_within_bounds(position):
            raise ValueError(f"Position {position} is out of bounds")
        self._grid[position.y][position.x] = cell

    # --- World dynamics ---

    def tick(self) -> None:
        """Advance world dynamics (regeneration)."""
        from axis.world.grid_2d.dynamics import apply_regeneration

        apply_regeneration(self, regen_rate=self._regen_rate)

    def extract_resource(self, position: Position, max_amount: float) -> float:
        """Extract resource from a cell."""
        cell = self.get_internal_cell(position)
        if cell.resource_value <= 0:
            return 0.0
        delta = min(cell.resource_value, max_amount)
        remainder = cell.resource_value - delta
        if remainder <= 0:
            new_cell = Cell(
                cell_type=CellType.EMPTY, resource_value=0.0,
                regen_eligible=cell.regen_eligible,
            )
        else:
            new_cell = Cell(
                cell_type=CellType.RESOURCE, resource_value=remainder,
                regen_eligible=cell.regen_eligible,
            )
        self.set_cell(position, new_cell)
        return delta

    def snapshot(self) -> WorldSnapshot:
        """Create an immutable snapshot."""
        grid = tuple(
            tuple(self.get_cell(Position(x=x, y=y))
                  for x in range(self._width))
            for y in range(self._height)
        )
        return WorldSnapshot(
            grid=grid, agent_position=self._agent_position,
            width=self._width, height=self._height,
        )
