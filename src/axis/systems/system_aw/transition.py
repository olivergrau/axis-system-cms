"""System A+W transition -- energy, observation buffer, dead reckoning, world model, termination."""

from __future__ import annotations

from axis.sdk.actions import MOVEMENT_DELTAS, STAY
from axis.sdk.types import TransitionResult
from axis.sdk.world_types import ActionOutcome
from axis.systems.construction_kit.memory.observation_buffer import update_observation_buffer
from axis.systems.construction_kit.observation.types import Observation
from axis.systems.construction_kit.energy.functions import clip_energy
from axis.systems.system_aw.types import AgentStateAW
from axis.systems.construction_kit.memory.world_model import update_world_model


class SystemAWTransition:
    """Transition function for System A+W.

    Extends System A's transition with dead reckoning and
    world model update.

    Five phases (Model Section 8):
    1. Energy update
    2. Observation buffer update
    3. Dead reckoning update
    4. World model update
    5. Termination check

    Critical: reads only action_outcome.action and action_outcome.moved.
    Never reads action_outcome.new_position.
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
        agent_state: AgentStateAW,
        action_outcome: ActionOutcome,
        observation: Observation,
        *,
        timestep: int = 0,
    ) -> TransitionResult:
        """Process action outcome: energy, observation buffer, world model, termination."""

        # Phase 1: Energy update (unchanged from System A)
        cost = self._get_action_cost(action_outcome.action)
        energy_gain = self._energy_gain_factor * action_outcome.data.get(
            "resource_consumed", 0.0,
        )
        new_energy = clip_energy(
            agent_state.energy - cost + energy_gain,
            self._max_energy,
        )

        # Phase 2: Observation buffer update (unchanged from System A)
        new_buffer = update_observation_buffer(
            agent_state.observation_buffer, observation, timestep,
        )

        # Phase 3 + 4: Dead reckoning + world model update (NEW)
        new_world_model = update_world_model(
            agent_state.world_model,
            action_outcome.action,
            action_outcome.moved,
        )

        # Assemble new state
        new_state = AgentStateAW(
            energy=new_energy,
            observation_buffer=new_buffer,
            world_model=new_world_model,
        )

        # Phase 5: Termination check (unchanged from System A)
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
            "relative_position": new_world_model.relative_position,
            "visit_count_at_current": dict(new_world_model.visit_counts).get(
                new_world_model.relative_position, 0,
            ),
            "visit_counts_map": [
                [[x, y], count]
                for (x, y), count in new_world_model.visit_counts
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
