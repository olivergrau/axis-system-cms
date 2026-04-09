"""Snapshot data models for the Visualization Layer.

Defines the replay coordinate system and the resolved snapshot type.
Phase indices replace the v0.1.0 ReplayPhase IntEnum to support
variable phase counts across systems.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot


class ReplayCoordinate(BaseModel):
    """A point in the replay coordinate system: (step_index, phase_index).

    Unlike v0.1.0's ReplayPhase IntEnum, phase_index is a plain int
    that ranges from 0 to len(phase_names)-1, adapting to any system's
    phase count.
    """

    model_config = ConfigDict(frozen=True)

    step_index: int = Field(..., ge=0)
    phase_index: int = Field(..., ge=0)


class ReplaySnapshot(BaseModel):
    """Fully resolved state at a specific replay coordinate.

    Immutable. Contains all state required by downstream rendering.
    System-specific action context is NOT included -- it lives in
    system_data on the BaseStepTrace and is interpreted by the
    system adapter (WP-V.3.4).
    """

    model_config = ConfigDict(frozen=True)

    # Coordinate identification
    step_index: int = Field(..., ge=0)
    phase_index: int = Field(..., ge=0)
    phase_name: str
    timestep: int = Field(..., ge=0)

    # World state at this phase
    world_snapshot: WorldSnapshot

    # Agent state at this phase
    agent_position: Position
    vitality: float = Field(..., ge=0.0, le=1.0)

    # Step-level context (same for all phases of one step)
    action: str
    terminated: bool
    termination_reason: str | None
