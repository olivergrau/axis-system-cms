"""Replay contract types -- base step trace and episode trace."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot


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
    intermediate_snapshots: dict[str, WorldSnapshot] = Field(default_factory=dict)

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
