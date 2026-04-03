"""Episode result structures for AXIS System A."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from axis_system_a.drives import HungerDriveOutput
from axis_system_a.enums import Action, TerminationReason
from axis_system_a.policy import DecisionTrace
from axis_system_a.transition import TransitionTrace
from axis_system_a.types import AgentState, Observation, Position


class StepResult(BaseModel):
    """Unified result of a single execution step.

    Captures the full decision-execution cycle:
    observation (pre-step) -> drive -> policy -> transition.
    """

    model_config = ConfigDict(frozen=True)

    timestep: int = Field(..., ge=0)
    observation: Observation
    selected_action: Action
    drive_output: HungerDriveOutput
    decision_result: DecisionTrace
    transition_trace: TransitionTrace
    energy_before: float = Field(..., ge=0)
    energy_after: float = Field(..., ge=0)
    terminated: bool

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dict."""
        return self.model_dump(mode="python")


# Backward compatibility alias
EpisodeStepRecord = StepResult


class EpisodeSummary(BaseModel):
    """Aggregate statistics for an episode."""

    model_config = ConfigDict(frozen=True)

    survival_length: int = Field(..., ge=0)
    action_counts: dict[str, int]
    total_consume_events: int = Field(..., ge=0)
    total_failed_consumes: int = Field(..., ge=0)
    mean_energy: float
    min_energy: float
    max_energy: float


def compute_episode_summary(steps: tuple[StepResult, ...]) -> EpisodeSummary:
    """Compute aggregate statistics from step results."""
    action_counts: dict[str, int] = {a.name: 0 for a in Action}
    total_consumes = 0
    failed_consumes = 0
    energies: list[float] = []

    for s in steps:
        action_counts[s.selected_action.name] += 1
        energies.append(s.energy_after)
        if s.selected_action is Action.CONSUME:
            if s.transition_trace.consumed:
                total_consumes += 1
            else:
                failed_consumes += 1

    return EpisodeSummary(
        survival_length=len(steps),
        action_counts=action_counts,
        total_consume_events=total_consumes,
        total_failed_consumes=failed_consumes,
        mean_energy=sum(energies) / len(energies) if energies else 0.0,
        min_energy=min(energies) if energies else 0.0,
        max_energy=max(energies) if energies else 0.0,
    )


class EpisodeResult(BaseModel):
    """Complete episode result."""

    model_config = ConfigDict(frozen=True)

    steps: tuple[StepResult, ...]
    total_steps: int = Field(..., ge=0)
    termination_reason: TerminationReason
    final_agent_state: AgentState
    final_position: Position
    final_observation: Observation
    summary: EpisodeSummary

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dict."""
        return self.model_dump(mode="python")
