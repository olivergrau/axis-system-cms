"""System A+W internal types -- agent state."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from axis.systems.construction_kit.memory.types import ObservationBuffer, WorldModelState


class AgentStateAW(BaseModel):
    """System A+W agent state: energy + observation buffer + world model.

    Extends System A's AgentState with the spatial world model.
    Position is explicitly NOT part of AgentStateAW in the absolute
    sense -- only the *relative* position estimate (inside WorldModelState)
    is tracked, via dead reckoning.

    Model reference: Section 4.
    """

    model_config = ConfigDict(frozen=True)

    energy: float = Field(..., ge=0)
    observation_buffer: ObservationBuffer
    world_model: WorldModelState
