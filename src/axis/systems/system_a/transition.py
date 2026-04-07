"""System A transition -- energy, memory, and termination updates."""

from __future__ import annotations

from axis.sdk.actions import MOVEMENT_DELTAS, STAY
from axis.sdk.types import TransitionResult
from axis.sdk.world_types import ActionOutcome
from axis.systems.system_a.memory import update_memory
from axis.systems.system_a.types import AgentState, Observation, clip_energy


class SystemATransition:
    """Transition function for System A.

    Satisfies TransitionInterface. Processes the ActionOutcome from
    the framework and updates energy, memory, and termination status.

    This handles v0.1.0 phases 4-6 only:
    - Phase 4: Energy update
    - Phase 5: Memory update
    - Phase 6: Termination check
    """

    def __init__(
        self,
        *,
        max_energy: float,
        move_cost: float,
        consume_cost: float,
        stay_cost: float,
        energy_gain_factor: float,
    ) -> None:
        self._max_energy = max_energy
        self._move_cost = move_cost
        self._consume_cost = consume_cost
        self._stay_cost = stay_cost
        self._energy_gain_factor = energy_gain_factor

    def transition(
        self,
        agent_state: AgentState,
        action_outcome: ActionOutcome,
        observation: Observation,
        *,
        timestep: int = 0,
    ) -> TransitionResult:
        """Process action outcome: energy, memory, termination.

        Args:
            agent_state: Current agent state.
            action_outcome: Result of the framework applying the action.
            observation: Post-action observation from the sensor.
            timestep: Current timestep for memory entry.

        Returns:
            TransitionResult with new agent state and trace data.
        """
        # Phase 4: Energy update
        cost = self._get_action_cost(action_outcome.action)
        energy_gain = self._energy_gain_factor * action_outcome.resource_consumed
        new_energy = clip_energy(
            agent_state.energy - cost + energy_gain,
            self._max_energy,
        )

        # Phase 5: Memory update (post-action observation)
        new_memory = update_memory(
            agent_state.memory_state, observation, timestep,
        )
        new_state = AgentState(energy=new_energy, memory_state=new_memory)

        # Phase 6: Termination check
        terminated = new_energy <= 0.0
        termination_reason = "energy_depleted" if terminated else None

        trace_data = {
            "energy_before": agent_state.energy,
            "energy_after": new_energy,
            "energy_delta": new_energy - agent_state.energy,
            "action_cost": cost,
            "energy_gain": energy_gain,
            "memory_entries_before": len(agent_state.memory_state.entries),
            "memory_entries_after": len(new_memory.entries),
        }

        return TransitionResult(
            new_state=new_state,
            trace_data=trace_data,
            terminated=terminated,
            termination_reason=termination_reason,
        )

    def _get_action_cost(self, action: str) -> float:
        """Return the energy cost for a given action."""
        if action in MOVEMENT_DELTAS:
            return self._move_cost
        if action == "consume":
            return self._consume_cost
        if action == STAY:
            return self._stay_cost
        return self._stay_cost
