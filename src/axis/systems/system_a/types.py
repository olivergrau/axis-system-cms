"""System A internal types -- agent state."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from axis.systems.construction_kit.memory.types import ObservationBuffer


class AgentState(BaseModel):
    """System A agent state: energy + observation buffer.

    Position is explicitly NOT part of AgentState -- it belongs to
    the world state (agent/world separation).
    """

    model_config = ConfigDict(frozen=True)

    energy: float = Field(..., ge=0)
    observation_buffer: ObservationBuffer
