"""System C internal types -- agent state."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from axis.systems.construction_kit.memory.types import ObservationBuffer
from axis.systems.construction_kit.observation.types import Observation
from axis.systems.construction_kit.prediction.memory import PredictiveMemory
from axis.systems.construction_kit.traces.state import TraceState


class AgentStateC(BaseModel):
    """System C agent state.

    Extends System A's state with predictive memory, trace state,
    and the last observation (used by the transition to compute
    prediction errors retrospectively).

    Position is explicitly NOT part of agent state -- it belongs to
    the world state (agent/world separation).
    """

    model_config = ConfigDict(frozen=True)

    energy: float = Field(..., ge=0)
    observation_buffer: ObservationBuffer
    predictive_memory: PredictiveMemory
    trace_state: TraceState
    last_observation: Observation | None = None
