"""World contract types -- read-only view, action outcome, base config."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from axis.sdk.position import Position

if TYPE_CHECKING:
    from axis.sdk.snapshot import WorldSnapshot


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


@runtime_checkable
class MutableWorldProtocol(WorldView, Protocol):
    """Full mutable world contract used by the framework and action handlers.

    Extends WorldView with the mutation API that the framework needs.
    Custom world implementations must satisfy this protocol.
    """

    @property
    def agent_position(self) -> Position:  # type: ignore[override]
        """Get/set agent position."""
        ...

    @agent_position.setter
    def agent_position(self, position: Position) -> None: ...

    def get_internal_cell(self, position: Position) -> Any:
        """Get the internal cell representation. Framework-only."""
        ...

    def set_cell(self, position: Position, cell: Any) -> None:
        """Replace a cell. Framework-only."""
        ...

    def tick(self) -> None:
        """Advance world dynamics by one step (e.g. regeneration)."""
        ...

    def extract_resource(self, position: Position, max_amount: float) -> float:
        """Extract up to *max_amount* resource from *position*.

        Returns the amount actually extracted. Mutates the cell.
        """
        ...

    def snapshot(self) -> WorldSnapshot:
        """Create an immutable snapshot of the current world state."""
        ...

    def world_metadata(self) -> dict[str, Any]:
        """Return per-step metadata for replay visualization."""
        ...


class ActionOutcome(BaseModel):
    """Result of applying an action to the world.

    Returned by the framework to the system after action application.
    The system uses this to update its internal state (energy, memory, etc.).

    Universal fields (action, moved, new_position) are provided by the
    framework. The ``data`` dict carries action-specific results set by
    the action handler (e.g. consume results, scan results). Systems
    read what they need from ``data``; the framework never inspects it.
    """

    model_config = ConfigDict(frozen=True)

    action: str
    moved: bool
    new_position: Position
    data: dict[str, Any] = Field(default_factory=dict)


class BaseWorldConfig(BaseModel):
    """Framework-level world configuration.

    Only ``world_type`` is framework-owned. All other fields are
    world-type-specific and passed through to the world factory via
    ``extra="allow"``.  This mirrors how system config is an opaque
    dict validated by the system at instantiation.

    Custom world types add their own fields (e.g. ``hex_radius``) and
    the framework stores them transparently.
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    world_type: str = "grid_2d"
