"""Immutable state snapshot types for AXIS System A traces."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from axis_system_a.types import AgentState, Position
from axis_system_a.world import Cell, World


class WorldSnapshot(BaseModel):
    """Immutable snapshot of the world grid state."""

    model_config = ConfigDict(frozen=True)

    grid: tuple[tuple[Cell, ...], ...]
    agent_position: Position
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)


class AgentSnapshot(BaseModel):
    """Minimal snapshot of agent state."""

    model_config = ConfigDict(frozen=True)

    energy: float = Field(..., ge=0)
    position: Position
    memory_entry_count: int = Field(..., ge=0)
    memory_timestep_range: tuple[int, int] | None


class RegenSummary(BaseModel):
    """Summary of world regeneration effects."""

    model_config = ConfigDict(frozen=True)

    cells_updated: int = Field(..., ge=0)
    regen_rate: float = Field(..., ge=0)


def snapshot_world(world: World) -> WorldSnapshot:
    """Create an immutable snapshot of the current world state."""
    grid = tuple(
        tuple(world.get_cell(Position(x=x, y=y)) for x in range(world.width))
        for y in range(world.height)
    )
    return WorldSnapshot(
        grid=grid,
        agent_position=world.agent_position,
        width=world.width,
        height=world.height,
    )


def snapshot_agent(agent_state: AgentState, position: Position) -> AgentSnapshot:
    """Create a minimal snapshot of agent state."""
    entries = agent_state.memory_state.entries
    if entries:
        ts_range = (entries[0].timestep, entries[-1].timestep)
    else:
        ts_range = None
    return AgentSnapshot(
        energy=agent_state.energy,
        position=position,
        memory_entry_count=len(entries),
        memory_timestep_range=ts_range,
    )
