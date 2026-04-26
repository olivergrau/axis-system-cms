"""System C+W internal types."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from axis.systems.construction_kit.memory.types import ObservationBuffer, WorldModelState
from axis.systems.construction_kit.observation.types import Observation
from axis.systems.construction_kit.prediction.memory import PredictiveMemory
from axis.systems.construction_kit.traces.state import TraceState


class AgentStateCW(BaseModel):
    """System C+W agent state."""

    model_config = ConfigDict(frozen=True)

    energy: float = Field(..., ge=0)
    observation_buffer: ObservationBuffer
    world_model: WorldModelState
    predictive_memory: PredictiveMemory
    hunger_trace_state: TraceState
    curiosity_trace_state: TraceState
    last_observation: Observation | None = None
