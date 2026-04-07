"""World snapshot types and construction helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from axis.sdk.position import Position
from axis.sdk.world_types import CellView

if TYPE_CHECKING:
    from axis.sdk.world_types import WorldView


class WorldSnapshot(BaseModel):
    """Immutable snapshot of the world grid state at a point in time.

    Used for replay visualization and audit trail. Contains the full
    grid state and agent position. This is the framework-level snapshot;
    system-specific state (agent energy, memory) is in system_data.
    """

    model_config = ConfigDict(frozen=True)

    grid: tuple[tuple[CellView, ...], ...]  # grid[row][col], nested immutable tuples
    agent_position: Position
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)


def snapshot_world(world_view: WorldView, width: int, height: int) -> WorldSnapshot:
    """Create an immutable snapshot of the current world state.

    Iterates over all cells via WorldView.get_cell() and captures
    them as CellView instances in a nested tuple structure.

    Args:
        world_view: Read-only view of the world.
        width: Grid width.
        height: Grid height.

    Returns:
        A frozen WorldSnapshot capturing the complete grid state.
    """
    grid = tuple(
        tuple(world_view.get_cell(Position(x=x, y=y)) for x in range(width))
        for y in range(height)
    )
    return WorldSnapshot(
        grid=grid,
        agent_position=world_view.agent_position,
        width=width,
        height=height,
    )
