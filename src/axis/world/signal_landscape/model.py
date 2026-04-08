"""Signal landscape cell types and world model.

Defines its own cell representation independent of the grid_2d world.
Only imports from the SDK -- no cross-world dependencies.
"""

from __future__ import annotations

import enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.world_types import CellView

import numpy as np


# ---------------------------------------------------------------------------
# Cell types (independent of grid_2d)
# ---------------------------------------------------------------------------

class SignalCellType(str, enum.Enum):
    """Cell type classification for the signal landscape."""

    EMPTY = "empty"
    RESOURCE = "resource"
    OBSTACLE = "obstacle"


class SignalCell(BaseModel):
    """Internal cell for the signal landscape world.

    Invariants:
    - OBSTACLE: resource_value == 0, not traversable
    - RESOURCE: resource_value > 0, traversable
    - EMPTY: resource_value == 0, traversable
    """

    model_config = ConfigDict(frozen=True)

    cell_type: SignalCellType
    resource_value: float = Field(..., ge=0, le=1)

    @model_validator(mode="after")
    def check_cell_invariants(self) -> SignalCell:
        if self.cell_type == SignalCellType.OBSTACLE and self.resource_value != 0.0:
            raise ValueError("OBSTACLE cells must have resource_value == 0")
        if self.cell_type == SignalCellType.RESOURCE and self.resource_value <= 0.0:
            raise ValueError("RESOURCE cells must have resource_value > 0")
        if self.cell_type == SignalCellType.EMPTY and self.resource_value != 0.0:
            raise ValueError("EMPTY cells must have resource_value == 0")
        return self

    @property
    def is_traversable(self) -> bool:
        return self.cell_type != SignalCellType.OBSTACLE


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------

class SignalLandscapeWorld:
    """Mutable 2D signal landscape satisfying MutableWorldProtocol.

    Cells carry signal strength as ``resource_value``. Hotspots drift
    each tick, creating a dynamic landscape suited for scout agents.
    """

    def __init__(
        self,
        grid: list[list[SignalCell]],
        agent_position: Position,
        hotspots: list[Any],
        *,
        drift_speed: float,
        decay_rate: float,
        rng: np.random.Generator,
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

        self._grid: list[list[SignalCell]] = grid
        self._width: int = width
        self._height: int = height
        self._agent_position: Position = agent_position
        self._hotspots = hotspots
        self._drift_speed: float = drift_speed
        self._decay_rate: float = decay_rate
        self._rng: np.random.Generator = rng

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
        if not self.is_within_bounds(position):
            raise ValueError(f"Position {position} is out of bounds")
        if not self._grid[position.y][position.x].is_traversable:
            raise ValueError(
                f"Position {position} is on a non-traversable cell"
            )
        self._agent_position = position

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
        if not self.is_within_bounds(position):
            return False
        return self._grid[position.y][position.x].is_traversable

    # --- Internal mutation API ---

    def get_internal_cell(self, position: Position) -> Any:
        if not self.is_within_bounds(position):
            raise ValueError(
                f"Position {position} is out of bounds "
                f"for grid of size ({self._width}, {self._height})"
            )
        return self._grid[position.y][position.x]

    def set_cell(self, position: Position, cell: Any) -> None:
        if not self.is_within_bounds(position):
            raise ValueError(
                f"Position {position} is out of bounds "
                f"for grid of size ({self._width}, {self._height})"
            )
        self._grid[position.y][position.x] = cell

    # --- Signal dynamics ---

    def tick(self) -> None:
        """Advance world dynamics: drift hotspots, decay signals, recompute field."""
        from axis.world.signal_landscape.dynamics import (
            drift_hotspots,
            recompute_signals,
        )

        drift_hotspots(
            self._hotspots, self._drift_speed,
            self._width, self._height, self._rng,
        )
        recompute_signals(
            self._grid, self._hotspots,
            self._width, self._height, self._decay_rate,
        )

    def extract_resource(self, position: Position, max_amount: float) -> float:
        """Signal landscape is non-extractive. Always returns 0.0."""
        return 0.0

    def snapshot(self) -> WorldSnapshot:
        """Create an immutable snapshot of the current world state."""
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
