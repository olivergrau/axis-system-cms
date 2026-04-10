"""System A -- hunger-driven baseline agent implementing SystemInterface."""

from __future__ import annotations

from typing import Any

import numpy as np

from axis.sdk.types import DecideResult, TransitionResult
from axis.sdk.world_types import WorldView
from axis.systems.system_a.config import SystemAConfig
from axis.systems.system_a.drive import SystemAHungerDrive
from axis.systems.system_a.policy import SystemAPolicy
from axis.systems.system_a.sensor import SystemASensor
from axis.systems.system_a.transition import SystemATransition
from axis.systems.system_a.types import AgentState, ObservationBuffer


class SystemA:
    """System A: hunger-driven baseline agent.

    Implements SystemInterface. Encapsulates sensor, drive, policy,
    and transition as internal components.
    """

    def __init__(self, config: SystemAConfig) -> None:
        self._config = config
        self._sensor = SystemASensor()
        self._drive = SystemAHungerDrive(
            consume_weight=config.policy.consume_weight,
            stay_suppression=config.policy.stay_suppression,
            max_energy=config.agent.max_energy,
        )
        self._policy = SystemAPolicy(
            temperature=config.policy.temperature,
            selection_mode=config.policy.selection_mode,
        )
        self._transition = SystemATransition(
            max_energy=config.agent.max_energy,
            move_cost=config.transition.move_cost,
            consume_cost=config.transition.consume_cost,
            stay_cost=config.transition.stay_cost,
            energy_gain_factor=config.transition.energy_gain_factor,
        )

    def system_type(self) -> str:
        """Return the system's unique type identifier."""
        return "system_a"

    def action_space(self) -> tuple[str, ...]:
        """Return the ordered tuple of action names."""
        return ("up", "down", "left", "right", "consume", "stay")

    def initialize_state(self) -> AgentState:
        """Create initial agent state from stored config."""
        return AgentState(
            energy=self._config.agent.initial_energy,
            observation_buffer=ObservationBuffer(
                entries=(),
                capacity=self._config.agent.buffer_capacity,
            ),
        )

    def vitality(self, agent_state: Any) -> float:
        """Normalized vitality: energy / max_energy."""
        return agent_state.energy / self._config.agent.max_energy

    def decide(
        self,
        world_view: Any,
        agent_state: Any,
        rng: np.random.Generator,
    ) -> DecideResult:
        """Phase 1: sensor -> drive -> policy -> action intent."""
        # 1. Observe
        observation = self._sensor.observe(world_view, world_view.agent_position)

        # 2. Drive
        drive_output = self._drive.compute(agent_state, observation)

        # 3. Policy
        policy_result = self._policy.select(drive_output, observation, rng)

        # 4. Assemble decision data (for system_data in trace)
        decision_data = {
            "observation": observation.model_dump(),
            "drive": {
                "activation": drive_output.activation,
                "action_contributions": drive_output.action_contributions,
            },
            "policy": policy_result.policy_data,
        }

        return DecideResult(
            action=policy_result.action,
            decision_data=decision_data,
        )

    def transition(
        self,
        agent_state: Any,
        action_outcome: Any,
        new_observation: Any,
    ) -> TransitionResult:
        """Phase 2: energy update, observation buffer update, termination check."""
        return self._transition.transition(
            agent_state, action_outcome, new_observation,
        )

    def action_handlers(self) -> dict[str, Any]:
        """Return custom action handlers for ActionRegistry registration."""
        from axis.systems.system_a.actions import handle_consume

        return {"consume": handle_consume}

    def observe(self, world_view: Any, position: Any) -> Any:
        """Produce System A observation from world state."""
        return self._sensor.observe(world_view, position)

    def action_context(self) -> dict[str, Any]:
        """Return context dict for System A's action handlers."""
        return {"max_consume": self._config.transition.max_consume}

    @property
    def sensor(self) -> SystemASensor:
        """Access the sensor component."""
        return self._sensor

    @property
    def config(self) -> SystemAConfig:
        """Access the parsed system config."""
        return self._config
