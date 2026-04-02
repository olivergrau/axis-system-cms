"""Fundamental runtime types for AXIS System A."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Position(BaseModel):
    """Grid position (x, y). Not part of AgentState — belongs to world state."""

    model_config = ConfigDict(frozen=True)

    x: int
    y: int


class CellObservation(BaseModel):
    """Per-cell sensory vector z_j = (b_j, r_j).

    traversability: b_j in {0, 1} — binary traversability signal
    resource: r_j in [0, 1] — normalized resource intensity
    """

    model_config = ConfigDict(frozen=True)

    traversability: float = Field(..., ge=0, le=1)
    resource: float = Field(..., ge=0, le=1)


class Observation(BaseModel):
    """Baseline observation vector u_t in R^10.

    Von Neumann neighborhood: current cell + 4 cardinal neighbors.
    Fixed ordering: (b_c, r_c, b_up, r_up, b_down, r_down, b_left, r_left, b_right, r_right).
    """

    model_config = ConfigDict(frozen=True)

    current: CellObservation
    up: CellObservation
    down: CellObservation
    left: CellObservation
    right: CellObservation

    def to_vector(self) -> tuple[float, ...]:
        """Return the flat 10-element observation vector in canonical order."""
        return (
            self.current.traversability,
            self.current.resource,
            self.up.traversability,
            self.up.resource,
            self.down.traversability,
            self.down.resource,
            self.left.traversability,
            self.left.resource,
            self.right.traversability,
            self.right.resource,
        )

    @property
    def dimension(self) -> int:
        """Observation vector dimensionality."""
        return 10


class MemoryEntry(BaseModel):
    """Single episodic memory record: timestep + observation.

    Memory entries are observation-derived only — no position, world state,
    or hidden environment variables.
    """

    model_config = ConfigDict(frozen=True)

    timestep: int = Field(..., ge=0)
    observation: Observation


class MemoryState(BaseModel):
    """Bounded episodic memory buffer.

    Stores an ordered sequence of MemoryEntry instances.
    FIFO update behavior is provided by update_memory() in memory.py.
    """

    model_config = ConfigDict(frozen=True)

    entries: tuple[MemoryEntry, ...] = Field(default_factory=tuple)
    capacity: int = Field(..., gt=0)

    @model_validator(mode="after")
    def check_capacity(self) -> MemoryState:
        if len(self.entries) > self.capacity:
            raise ValueError(
                f"entries length ({len(self.entries)}) "
                f"exceeds capacity ({self.capacity})"
            )
        return self


class AgentState(BaseModel):
    """Internal agent state: energy + memory.

    Position is explicitly NOT part of AgentState — it belongs to the
    world state (agent/world separation).
    """

    model_config = ConfigDict(frozen=True)

    energy: float = Field(..., ge=0)
    memory_state: MemoryState


def clip_energy(energy: float, max_energy: float) -> float:
    """Clip energy to the valid interval [0, max_energy]."""
    return max(0.0, min(energy, max_energy))
