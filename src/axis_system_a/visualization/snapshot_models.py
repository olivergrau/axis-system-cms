"""Snapshot data models for the Visualization Layer (VWP2).

Defines the replay coordinate system and the resolved snapshot type
used by the SnapshotResolver and consumed by later VWPs (viewer state,
view models, rendering).
"""

from __future__ import annotations

import enum

from pydantic import BaseModel, ConfigDict, Field

from axis_system_a.enums import Action, TerminationReason
from axis_system_a.types import Position
from axis_system_a.world import Cell


class ReplayPhase(enum.IntEnum):
    """Intra-step phase in the replay coordinate system.

    Ordering: BEFORE < AFTER_REGEN < AFTER_ACTION.
    IntEnum provides natural comparison operators for phase cycling.
    """

    BEFORE = 0
    AFTER_REGEN = 1
    AFTER_ACTION = 2


class ReplayCoordinate(BaseModel):
    """A point in the replay coordinate system: (step_index, phase)."""

    model_config = ConfigDict(frozen=True)

    step_index: int = Field(..., ge=0)
    phase: ReplayPhase


class ReplaySnapshot(BaseModel):
    """Fully resolved system state at a specific replay coordinate.

    Immutable. Derived only from validated replay data via SnapshotResolver.
    Contains all state required for downstream rendering (VWP5/VWP6).
    """

    model_config = ConfigDict(frozen=True)

    # --- Coordinate identification ---
    step_index: int = Field(..., ge=0)
    phase: ReplayPhase
    timestep: int = Field(..., ge=0)

    # --- World state at this phase ---
    grid: tuple[tuple[Cell, ...], ...]
    grid_width: int = Field(..., gt=0)
    grid_height: int = Field(..., gt=0)

    # --- Agent state at this phase ---
    agent_position: Position
    agent_energy: float = Field(..., ge=0)

    # --- Step-level action context (same for all phases of one step) ---
    action: Action
    moved: bool
    consumed: bool
    resource_consumed: float
    energy_delta: float
    terminated: bool
    termination_reason: TerminationReason | None
