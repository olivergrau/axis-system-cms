"""System A+W -- dual-drive agent with curiosity and world model."""

from __future__ import annotations

from typing import Any

import numpy as np

from axis.sdk.types import DecideResult, TransitionResult
from axis.systems.system_a.types import MemoryState
from axis.systems.system_aw.config import SystemAWConfig
from axis.systems.system_aw.drive_arbitration import (
    compute_action_scores,
    compute_drive_weights,
)
from axis.systems.system_aw.drive_curiosity import SystemAWCuriosityDrive
from axis.systems.system_aw.drive_hunger import SystemAWHungerDrive
from axis.systems.system_aw.policy import SystemAWPolicy
from axis.systems.system_aw.sensor import SystemAWSensor
from axis.systems.system_aw.transition import SystemAWTransition
from axis.systems.system_aw.types import AgentStateAW
from axis.systems.system_aw.world_model import create_world_model


class SystemAW:
    """System A+W: dual-drive agent with curiosity and world model.

    Implements SystemInterface. Extends System A with:
    - A curiosity drive (novelty-seeking)
    - A spatial world model (visit-count map via dead reckoning)
    - Dynamic drive arbitration (hunger gates curiosity)

    Model reference: Section 9 (Execution Cycle).
    """

    def __init__(self, config: SystemAWConfig) -> None:
        self._config = config
        self._sensor = SystemAWSensor()
        self._hunger_drive = SystemAWHungerDrive(
            consume_weight=config.policy.consume_weight,
            stay_suppression=config.policy.stay_suppression,
            max_energy=config.agent.max_energy,
        )
        self._curiosity_drive = SystemAWCuriosityDrive(
            base_curiosity=config.curiosity.base_curiosity,
            spatial_sensory_balance=config.curiosity.spatial_sensory_balance,
            explore_suppression=config.curiosity.explore_suppression,
            novelty_sharpness=config.curiosity.novelty_sharpness,
        )
        self._policy = SystemAWPolicy(
            temperature=config.policy.temperature,
            selection_mode=config.policy.selection_mode,
        )
        self._transition = SystemAWTransition(
            max_energy=config.agent.max_energy,
            move_cost=config.transition.move_cost,
            consume_cost=config.transition.consume_cost,
            stay_cost=config.transition.stay_cost,
            energy_gain_factor=config.transition.energy_gain_factor,
        )

    def system_type(self) -> str:
        """Return the system's unique type identifier."""
        return "system_aw"

    def action_space(self) -> tuple[str, ...]:
        """Return the ordered tuple of action names."""
        return ("up", "down", "left", "right", "consume", "stay")

    def initialize_state(self) -> AgentStateAW:
        """Create initial agent state from stored config."""
        return AgentStateAW(
            energy=self._config.agent.initial_energy,
            memory_state=MemoryState(
                entries=(),
                capacity=self._config.agent.memory_capacity,
            ),
            world_model=create_world_model(),
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
        """Execution cycle steps 1-6: perceive, evaluate, arbitrate, select."""

        # Step 1: Perception
        observation = self._sensor.observe(
            world_view, world_view.agent_position)

        # Step 2: Drive evaluation
        hunger_output = self._hunger_drive.compute(agent_state, observation)
        curiosity_output = self._curiosity_drive.compute(
            observation, agent_state.memory_state, agent_state.world_model,
        )

        # Step 3: Drive arbitration
        weights = compute_drive_weights(
            hunger_output.activation, self._config.arbitration,
        )

        # Step 4: Action modulation (score combination)
        scores = compute_action_scores(
            hunger_output, curiosity_output, weights)

        # Steps 5-6: Admissibility masking + action selection
        policy_result = self._policy.select(scores, observation, rng)

        # Assemble decision data for trace
        decision_data = {
            "observation": observation.model_dump(),
            "hunger_drive": {
                "activation": hunger_output.activation,
                "action_contributions": hunger_output.action_contributions,
            },
            "curiosity_drive": {
                "activation": curiosity_output.activation,
                "spatial_novelty": curiosity_output.spatial_novelty,
                "sensory_novelty": curiosity_output.sensory_novelty,
                "composite_novelty": curiosity_output.composite_novelty,
                "action_contributions": curiosity_output.action_contributions,
            },
            "arbitration": {
                "hunger_weight": weights.hunger_weight,
                "curiosity_weight": weights.curiosity_weight,
            },
            "combined_scores": scores,
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
        """Execution cycle steps 7-8: state transition + termination."""
        return self._transition.transition(
            agent_state, action_outcome, new_observation,
        )

    def action_handlers(self) -> dict[str, Any]:
        """Return custom action handlers for ActionRegistry registration."""
        from axis.systems.system_aw.actions import handle_consume

        return {"consume": handle_consume}

    def observe(self, world_view: Any, position: Any) -> Any:
        """Produce System A+W observation from world state."""
        return self._sensor.observe(world_view, position)

    def action_context(self) -> dict[str, Any]:
        """Return context dict for action handlers."""
        return {"max_consume": self._config.transition.max_consume}

    @property
    def config(self) -> SystemAWConfig:
        """Access the parsed system config."""
        return self._config
