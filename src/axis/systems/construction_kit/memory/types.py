"""Memory types -- buffer entry and observation buffer models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axis.systems.construction_kit.observation.types import Observation


__all__ = [
    "BufferEntry",
    "ObservationBuffer",
    "WorldModelState",
]


class BufferEntry(BaseModel):
    """Single observation buffer record: timestep + observation."""

    model_config = ConfigDict(frozen=True)

    timestep: int = Field(..., ge=0)
    observation: Observation


class ObservationBuffer(BaseModel):
    """Bounded observation buffer.

    FIFO update behavior is provided by update_observation_buffer()
    in observation_buffer.py.
    """

    model_config = ConfigDict(frozen=True)

    entries: tuple[BufferEntry, ...] = Field(default_factory=tuple)
    capacity: int = Field(..., gt=0)

    @model_validator(mode="after")
    def check_capacity(self) -> ObservationBuffer:
        if len(self.entries) > self.capacity:
            raise ValueError(
                f"entries length ({len(self.entries)}) "
                f"exceeds capacity ({self.capacity})"
            )
        return self


class WorldModelState(BaseModel):
    """Spatial world model: relative position + visit counts.

    The world model uses agent-relative coordinates maintained
    through dead reckoning (path integration). No absolute position
    data is stored or consumed.

    Model reference: Section 4.1.
    """

    model_config = ConfigDict(frozen=True)

    relative_position: tuple[int, int] = Field(
        default=(0, 0),
        description="Agent's position estimate via dead reckoning, relative to start",
    )
    visit_counts: tuple[tuple[tuple[int, int], int], ...] = Field(
        default_factory=tuple,
        description="Immutable sequence of ((x, y), count) pairs",
    )
