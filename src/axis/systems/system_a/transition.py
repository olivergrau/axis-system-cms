"""System A transition -- energy, observation buffer, and termination updates."""

from __future__ import annotations

from axis.sdk.actions import MOVEMENT_DELTAS, STAY
from axis.sdk.types import TransitionResult
from axis.sdk.world_types import ActionOutcome
from axis.systems.construction_kit.memory.observation_buffer import update_observation_buffer
from axis.systems.construction_kit.energy.functions import clip_energy
from axis.systems.construction_kit.observation.types import Observation
from axis.systems.system_a.types import AgentState


class SystemATransition:
    """Transition function for System A.

    Satisfies TransitionInterface. Processes the ActionOutcome from
    the framework and updates energy, observation buffer, and
    termination status.

    This handles v0.1.0 phases 4-6 only:
    - Phase 4: Energy update
    - Phase 5: Observation buffer update
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
        """Process action outcome: energy, observation buffer, termination.

        Args:
            agent_state: Current agent state.
            action_outcome: Result of the framework applying the action.
            observation: Post-action observation from the sensor.
            timestep: Current timestep for buffer entry.

        Returns:
            TransitionResult with new agent state and trace data.
        """
        # Phase 4: Energy update
        cost = self._get_action_cost(action_outcome.action)
        energy_gain = self._energy_gain_factor * \
            action_outcome.data.get("resource_consumed", 0.0)
        new_energy = clip_energy(
            agent_state.energy - cost + energy_gain,
            self._max_energy,
        )

        # Phase 5: Observation buffer update (post-action observation)
        new_buffer = update_observation_buffer(
            agent_state.observation_buffer, observation, timestep,
        )
        new_state = AgentState(
            energy=new_energy, observation_buffer=new_buffer)

        # Phase 6: Termination check
        terminated = new_energy <= 0.0
        termination_reason = "energy_depleted" if terminated else None

        trace_data = {
            "energy_before": agent_state.energy,
            "energy_after": new_energy,
            "energy_delta": new_energy - agent_state.energy,
            "action_cost": cost,
            "energy_gain": energy_gain,
            "buffer_entries_before": len(agent_state.observation_buffer.entries),
            "buffer_entries_after": len(new_buffer.entries),
            "buffer_capacity": new_buffer.capacity,
            "buffer_snapshot": [
                {
                    "timestep": entry.timestep,
                    "current_res": entry.observation.current.resource,
                    "up_res": entry.observation.up.resource,
                    "down_res": entry.observation.down.resource,
                    "left_res": entry.observation.left.resource,
                    "right_res": entry.observation.right.resource,
                    "current_trav": entry.observation.current.traversability,
                    "up_trav": entry.observation.up.traversability,
                    "down_trav": entry.observation.down.traversability,
                    "left_trav": entry.observation.left.traversability,
                    "right_trav": entry.observation.right.traversability,
                }
                for entry in new_buffer.entries
            ],
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
