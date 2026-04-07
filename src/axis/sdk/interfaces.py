"""SDK interfaces -- abstract contracts that all systems must implement."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import numpy as np

from axis.sdk.types import DecideResult, PolicyResult, TransitionResult


@runtime_checkable
class SystemInterface(Protocol):
    """Primary contract between a system and the framework.

    The framework interacts with systems exclusively through this interface.
    Systems own all internal logic (sensor, drives, policy, transition).
    The framework owns world mutation and episode orchestration.

    Two-phase step contract:
      1. decide()     -- system produces action intent
      2. transition() -- system processes action outcome
    """

    def system_type(self) -> str:
        """Return the system's unique type identifier (e.g., 'system_a')."""
        ...

    def action_space(self) -> tuple[str, ...]:
        """Return the ordered tuple of action names this system can produce.

        Must include all base actions ('up', 'down', 'left', 'right', 'stay')
        plus any system-specific actions (e.g., 'consume').
        """
        ...

    def initialize_state(self, system_config: dict[str, Any]) -> Any:
        """Create the initial agent state from the system config.

        The returned state is opaque to the framework. Only the system
        and its sub-components interpret it. The framework passes it
        back to decide() and transition() without inspection.
        """
        ...

    def vitality(self, agent_state: Any) -> float:
        """Return the agent's normalized vitality in [0.0, 1.0].

        This is the only framework-readable metric from agent state.
        For System A, this is energy / max_energy.
        """
        ...

    def decide(
        self,
        world_view: Any,
        agent_state: Any,
        rng: np.random.Generator,
    ) -> DecideResult:
        """Phase 1 of the two-phase step: produce an action intent.

        The system reads the world via world_view (read-only), evaluates
        its internal pipeline (sensor -> drives -> policy), and returns
        the chosen action plus any decision trace data.

        The framework will apply this action to the world and call
        transition() with the outcome.
        """
        ...

    def transition(
        self,
        agent_state: Any,
        action_outcome: Any,
        new_observation: Any,
    ) -> TransitionResult:
        """Phase 2 of the two-phase step: process the action outcome.

        Receives the outcome of the applied action (what happened in the
        world) and the post-action observation. Updates internal state
        (energy, memory, etc.) and checks for system-level termination.
        """
        ...


@runtime_checkable
class SensorInterface(Protocol):
    """Constructs observations from the world state.

    System-specific: each system defines its own observation type.
    For System A, this produces a 10-dimensional Observation
    (Von Neumann neighborhood with traversability and resource signals).
    """

    def observe(self, world_view: Any, position: Any) -> Any:
        """Produce an observation from the current world state and position."""
        ...


@runtime_checkable
class DriveInterface(Protocol):
    """Computes a drive output that modulates action selection.

    Every system must have at least one drive. Drive outputs flow
    into the policy for action selection.
    """

    def compute(self, agent_state: Any, observation: Any) -> Any:
        """Compute drive output from current state and observation."""
        ...


@runtime_checkable
class PolicyInterface(Protocol):
    """Selects an action based on drive outputs and observation.

    Receives the combined drive outputs, the current observation,
    and a random number generator for stochastic selection.
    """

    def select(
        self,
        drive_outputs: Any,
        observation: Any,
        rng: np.random.Generator,
    ) -> PolicyResult:
        """Select an action from the drive-modulated contributions."""
        ...


@runtime_checkable
class TransitionInterface(Protocol):
    """Updates agent state after an action has been applied to the world.

    Handles state evolution: energy changes, memory updates,
    termination checks. Does NOT mutate the world.
    """

    def transition(
        self,
        agent_state: Any,
        action_outcome: Any,
        observation: Any,
    ) -> TransitionResult:
        """Process action outcome and produce new agent state."""
        ...
