"""Replay contract types for full and delta episode traces."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.world_types import CellView


class BaseStepTrace(BaseModel):
    """The global replay contract for a single simulation step.

    Every system must produce data conforming to this schema.
    The framework assembles this from system outputs and world state.

    System-specific data (drive outputs, decision traces, detailed
    transition data) is packed into system_data as an opaque dict.
    Only the system's visualization adapter interprets it.
    """

    model_config = ConfigDict(frozen=True)

    # ── Step identification ──
    timestep: int = Field(..., ge=0)
    action: str

    # ── World snapshots (mandatory) ──
    world_before: WorldSnapshot
    world_after: WorldSnapshot

    # ── World snapshots (optional, system-declared) ──
    intermediate_snapshots: dict[str, WorldSnapshot] = Field(
        default_factory=dict)

    # ── Agent position ──
    agent_position_before: Position
    agent_position_after: Position

    # ── Vitality (normalized [0, 1]) ──
    vitality_before: float = Field(..., ge=0.0, le=1.0)
    vitality_after: float = Field(..., ge=0.0, le=1.0)

    # ── Termination ──
    terminated: bool
    termination_reason: str | None = None

    # ── System-specific trace data ──
    system_data: dict[str, Any] = Field(default_factory=dict)

    # ── World-specific trace data ──
    world_data: dict[str, Any] = Field(default_factory=dict)


class BaseEpisodeTrace(BaseModel):
    """The global replay contract for a complete episode.

    Contains the sequence of step traces and episode-level metadata.
    This is the top-level type serialized to disk per episode.
    """

    model_config = ConfigDict(frozen=True)

    system_type: str
    steps: tuple[BaseStepTrace, ...]
    total_steps: int = Field(..., ge=0)
    termination_reason: str
    final_vitality: float = Field(..., ge=0.0, le=1.0)
    final_position: Position

    # ── World identity (visualization pipeline) ──
    world_type: str = "grid_2d"
    world_config: dict[str, Any] = Field(default_factory=dict)


class DeltaCellUpdate(BaseModel):
    """One changed cell within a delta-applied world transition."""

    model_config = ConfigDict(frozen=True)

    position: Position
    cell: CellView


class WorldDelta(BaseModel):
    """Compact world-state delta relative to a previous snapshot."""

    model_config = ConfigDict(frozen=True)

    agent_position: Position
    changed_cells: tuple[DeltaCellUpdate, ...] = ()


class DeltaStepTrace(BaseModel):
    """Per-step delta representation for replay-capable persistence."""

    model_config = ConfigDict(frozen=True)

    timestep: int = Field(..., ge=0)
    action: str
    regen_delta: WorldDelta
    action_delta: WorldDelta
    agent_position_before: Position
    agent_position_after: Position
    vitality_before: float = Field(..., ge=0.0, le=1.0)
    vitality_after: float = Field(..., ge=0.0, le=1.0)
    terminated: bool
    termination_reason: str | None = None
    system_data: dict[str, Any] = Field(default_factory=dict)
    world_data: dict[str, Any] = Field(default_factory=dict)


class DeltaEpisodeTrace(BaseModel):
    """Compact replay-capable episode trace stored as initial state + deltas."""

    model_config = ConfigDict(frozen=True)

    result_type: str = "delta_episode"
    system_type: str
    initial_world: WorldSnapshot
    steps: tuple[DeltaStepTrace, ...]
    total_steps: int = Field(..., ge=0)
    termination_reason: str
    final_vitality: float = Field(..., ge=0.0, le=1.0)
    final_position: Position
    world_type: str = "grid_2d"
    world_config: dict[str, Any] = Field(default_factory=dict)


def diff_world_snapshots(
    before: WorldSnapshot,
    after: WorldSnapshot,
) -> WorldDelta:
    """Build a compact delta from two full snapshots."""
    changed_cells: list[DeltaCellUpdate] = []
    for y in range(before.height):
        for x in range(before.width):
            if before.grid[y][x] != after.grid[y][x]:
                changed_cells.append(
                    DeltaCellUpdate(
                        position=Position(x=x, y=y),
                        cell=after.grid[y][x],
                    )
                )
    return WorldDelta(
        agent_position=after.agent_position,
        changed_cells=tuple(changed_cells),
    )


def apply_world_delta(
    snapshot: WorldSnapshot,
    delta: WorldDelta,
) -> WorldSnapshot:
    """Apply a compact delta to a snapshot and return a new snapshot."""
    mutable_grid = [list(row) for row in snapshot.grid]
    for update in delta.changed_cells:
        mutable_grid[update.position.y][update.position.x] = update.cell
    return WorldSnapshot(
        grid=tuple(tuple(row) for row in mutable_grid),
        agent_position=delta.agent_position,
        width=snapshot.width,
        height=snapshot.height,
    )


def reconstruct_episode_trace(
    delta_episode: DeltaEpisodeTrace,
) -> BaseEpisodeTrace:
    """Materialize a full replay trace from a delta episode."""
    current_world = delta_episode.initial_world
    steps: list[BaseStepTrace] = []

    for step in delta_episode.steps:
        world_before = current_world
        world_after_regen = apply_world_delta(world_before, step.regen_delta)
        world_after = apply_world_delta(world_after_regen, step.action_delta)
        steps.append(
            BaseStepTrace(
                timestep=step.timestep,
                action=step.action,
                world_before=world_before,
                world_after=world_after,
                intermediate_snapshots={"AFTER_REGEN": world_after_regen},
                agent_position_before=step.agent_position_before,
                agent_position_after=step.agent_position_after,
                vitality_before=step.vitality_before,
                vitality_after=step.vitality_after,
                terminated=step.terminated,
                termination_reason=step.termination_reason,
                system_data=step.system_data,
                world_data=step.world_data,
            )
        )
        current_world = world_after

    return BaseEpisodeTrace(
        system_type=delta_episode.system_type,
        steps=tuple(steps),
        total_steps=delta_episode.total_steps,
        termination_reason=delta_episode.termination_reason,
        final_vitality=delta_episode.final_vitality,
        final_position=delta_episode.final_position,
        world_type=delta_episode.world_type,
        world_config=delta_episode.world_config,
    )
