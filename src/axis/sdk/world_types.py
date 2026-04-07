"""World contract types -- read-only view, action outcome, base config."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from axis.sdk.position import Position


class CellView(BaseModel):
    """Read-only view of a single grid cell, as seen by systems.

    This is the system-facing representation of a cell.
    The framework may store additional internal cell data
    (e.g., regen_eligible) that is not exposed to systems.
    """

    model_config = ConfigDict(frozen=True)

    cell_type: str  # "empty", "resource", "obstacle"
    resource_value: float = Field(..., ge=0.0, le=1.0)


@runtime_checkable
class WorldView(Protocol):
    """Read-only view of the world, passed to systems.

    Systems receive this in decide(). They cannot mutate the world
    through this view. The framework provides the implementation.
    """

    @property
    def width(self) -> int:
        """Grid width."""
        ...

    @property
    def height(self) -> int:
        """Grid height."""
        ...

    @property
    def agent_position(self) -> Position:
        """Current agent position."""
        ...

    def get_cell(self, position: Position) -> CellView:
        """Get the read-only view of a cell.

        Raises ValueError if position is out of bounds.
        """
        ...

    def is_within_bounds(self, position: Position) -> bool:
        """Check if a position is within the grid."""
        ...

    def is_traversable(self, position: Position) -> bool:
        """Check if a position is traversable (not obstacle, within bounds).

        Returns False for out-of-bounds positions (safe to call with any position).
        """
        ...


class ActionOutcome(BaseModel):
    """Result of applying an action to the world.

    Returned by the framework to the system after action application.
    The system uses this to update its internal state (energy, memory, etc.).
    """

    model_config = ConfigDict(frozen=True)

    action: str
    moved: bool
    new_position: Position
    consumed: bool = False
    resource_consumed: float = 0.0


class BaseWorldConfig(BaseModel):
    """Framework-level world configuration.

    Defines the structural properties of the world grid.
    System-specific world dynamics (e.g., regeneration parameters)
    are part of the system config, not this type.
    """

    model_config = ConfigDict(frozen=True)

    grid_width: int = Field(..., gt=0)
    grid_height: int = Field(..., gt=0)
    obstacle_density: float = Field(default=0.0, ge=0.0, lt=1.0)
