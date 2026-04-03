"""Episode result structures for AXIS System A."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from axis_system_a.drives import HungerDriveOutput
from axis_system_a.enums import Action, TerminationReason
from axis_system_a.policy import DecisionResult
from axis_system_a.transition import TransitionTrace
from axis_system_a.types import AgentState, Observation, Position


class EpisodeStepRecord(BaseModel):
    """Record of a single step within an episode.

    Captures the full decision-execution cycle:
    observation (pre-step) -> drive -> policy -> transition.
    """

    model_config = ConfigDict(frozen=True)

    timestep: int = Field(..., ge=0)
    observation: Observation
    action: Action
    drive_output: HungerDriveOutput
    decision_result: DecisionResult
    transition_trace: TransitionTrace
    energy_after: float = Field(..., ge=0)
    terminated: bool


class EpisodeResult(BaseModel):
    """Complete episode result."""

    model_config = ConfigDict(frozen=True)

    steps: tuple[EpisodeStepRecord, ...]
    total_steps: int = Field(..., ge=0)
    termination_reason: TerminationReason
    final_agent_state: AgentState
    final_position: Position
    final_observation: Observation
