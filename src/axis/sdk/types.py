"""SDK data types -- framework-visible output types from system interfaces."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class DecideResult(BaseModel):
    """Output of SystemInterface.decide().

    Contains the chosen action and system-specific decision data
    that will be included in the step trace.
    """

    model_config = ConfigDict(frozen=True)

    action: str
    decision_data: dict[str, Any]


class TransitionResult(BaseModel):
    """Output of SystemInterface.transition().

    Contains the new agent state, system-specific trace data,
    and termination information.
    """

    model_config = ConfigDict(frozen=True)

    new_state: Any  # system-specific AgentState, opaque to framework
    trace_data: dict[str, Any]
    terminated: bool
    termination_reason: str | None = None


class PolicyResult(BaseModel):
    """Output of PolicyInterface.select().

    Contains the selected action and any policy trace data
    (e.g., probabilities, temperature, selection mode).
    """

    model_config = ConfigDict(frozen=True)

    action: str
    policy_data: dict[str, Any]
