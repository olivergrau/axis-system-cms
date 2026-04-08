"""World model: CellType, RegenerationMode, Cell, and World."""

from __future__ import annotations

import enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axis.sdk.position import Position
from axis.sdk.world_types import CellView


class CellType(str, enum.Enum):
    """Internal cell type classification."""

    EMPTY = "empty"
    RESOURCE = "resource"
    OBSTACLE = "obstacle"


class RegenerationMode(str, enum.Enum):
    """Regeneration eligibility mode for the world grid."""

    ALL_TRAVERSABLE = "all_traversable"
    SPARSE_FIXED_RATIO = "sparse_fixed_ratio"


class Cell(BaseModel):
    """Internal cell representation.

    Invariants:
    - OBSTACLE: resource_value == 0, not traversable, regen_eligible forced False
    - RESOURCE: resource_value > 0, traversable
    - EMPTY: resource_value == 0, traversable
    """

    model_config = ConfigDict(frozen=True)

    cell_type: CellType
    resource_value: float = Field(..., ge=0, le=1)
    regen_eligible: bool = True

    @model_validator(mode="after")
    def check_cell_invariants(self) -> Cell:
        if self.cell_type == CellType.OBSTACLE and self.resource_value != 0.0:
            raise ValueError("OBSTACLE cells must have resource_value == 0")
        if self.cell_type == CellType.RESOURCE and self.resource_value <= 0.0:
            raise ValueError("RESOURCE cells must have resource_value > 0")
        if self.cell_type == CellType.EMPTY and self.resource_value != 0.0:
            raise ValueError("EMPTY cells must have resource_value == 0")
        if self.cell_type == CellType.OBSTACLE and self.regen_eligible:
            object.__setattr__(self, "regen_eligible", False)
        return self

    @property
    def is_traversable(self) -> bool:
        """EMPTY and RESOURCE cells are traversable; OBSTACLE cells are not."""
        return self.cell_type != CellType.OBSTACLE


class World:
    """Mutable 2D grid world that satisfies the WorldView protocol.

    The sole mutable container in the runtime. Stores the grid
    of cells and the agent's position. Provides both the internal
    mutation API (for the framework) and the read-only WorldView
    protocol (for systems).
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
        self._regen_rate: float = regen_rate

    # --- WorldView protocol (read-only) ---

    @property
    def width(self) -> int:
        """Grid width."""
        return self._width

    @property
    def height(self) -> int:
        """Grid height."""
        return self._height

    @property
    def agent_position(self) -> Position:
        """Current agent position."""
        return self._agent_position

    @agent_position.setter
    def agent_position(self, position: Position) -> None:
        """Set agent position. Validates bounds and traversability."""
        if not self.is_within_bounds(position):
            raise ValueError(f"Position {position} is out of bounds")
        if not self._grid[position.y][position.x].is_traversable:
            raise ValueError(
                f"Position {position} is on a non-traversable cell"
            )
        self._agent_position = position

    def get_cell(self, position: Position) -> CellView:
        """Get the read-only CellView of a cell (WorldView protocol).

        Returns CellView, bridging from the internal Cell representation.
        Raises ValueError if position is out of bounds.
        """
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
        """Check if a position is within the grid."""
        return 0 <= position.x < self._width and 0 <= position.y < self._height

    def is_traversable(self, position: Position) -> bool:
        """Check if a position is traversable (not obstacle, within bounds).

        Returns False for out-of-bounds positions.
        """
        if not self.is_within_bounds(position):
            return False
        return self._grid[position.y][position.x].is_traversable

    # --- Internal mutation API (framework-only) ---

    def get_internal_cell(self, position: Position) -> Cell:
        """Get the internal Cell (with regen_eligible). Framework-only."""
        if not self.is_within_bounds(position):
            raise ValueError(
                f"Position {position} is out of bounds "
                f"for grid of size ({self._width}, {self._height})"
            )
        return self._grid[position.y][position.x]

    def set_cell(self, position: Position, cell: Cell) -> None:
        """Replace a cell. Framework-only."""
        if not self.is_within_bounds(position):
            raise ValueError(
                f"Position {position} is out of bounds "
                f"for grid of size ({self._width}, {self._height})"
            )
        self._grid[position.y][position.x] = cell

    def is_regen_eligible(self, position: Position) -> bool:
        """Check regen eligibility. Framework-only."""
        return self.get_internal_cell(position).regen_eligible

    # --- World dynamics ---

    def tick(self) -> None:
        """Advance world dynamics by one step (regeneration)."""
        from axis.world.grid_2d.dynamics import apply_regeneration

        apply_regeneration(self, regen_rate=self._regen_rate)

    def extract_resource(self, position: Position, max_amount: float) -> float:
        """Extract up to *max_amount* resource from the cell at *position*.

        Returns the amount actually extracted. Mutates the cell accordingly:
        - If the cell has no resource, returns 0.0
        - If the cell is fully consumed, it becomes EMPTY
        - If partially consumed, it stays RESOURCE with the remainder
        """
        cell = self.get_internal_cell(position)
        if cell.resource_value <= 0:
            return 0.0

        delta = min(cell.resource_value, max_amount)
        remainder = cell.resource_value - delta

        if remainder <= 0:
            new_cell = Cell(
                cell_type=CellType.EMPTY,
                resource_value=0.0,
                regen_eligible=cell.regen_eligible,
            )
        else:
            new_cell = Cell(
                cell_type=CellType.RESOURCE,
                resource_value=remainder,
                regen_eligible=cell.regen_eligible,
            )
        self.set_cell(position, new_cell)
        return delta

    def snapshot(self) -> WorldSnapshot:
        """Create an immutable snapshot of the current world state."""
        from axis.sdk.snapshot import WorldSnapshot

        grid = tuple(
            tuple(self.get_cell(Position(x=x, y=y))
                  for x in range(self._width))
            for y in range(self._height)
        )
        return WorldSnapshot(
            grid=grid,
            agent_position=self._agent_position,
            width=self._width,
            height=self._height,
        )
