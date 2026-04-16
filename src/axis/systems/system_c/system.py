"""System C -- predictive action modulation agent implementing SystemInterface."""

from __future__ import annotations

from typing import Any

import numpy as np

from axis.sdk.types import DecideResult, TransitionResult
from axis.systems.construction_kit.drives.hunger import HungerDrive
from axis.systems.construction_kit.memory.types import ObservationBuffer
from axis.systems.construction_kit.modulation.modulation import modulate_action_scores
from axis.systems.construction_kit.observation.sensor import VonNeumannSensor
from axis.systems.construction_kit.policy.softmax import SoftmaxPolicy
from axis.systems.construction_kit.prediction.context import encode_context
from axis.systems.construction_kit.prediction.features import extract_predictive_features
from axis.systems.construction_kit.prediction.memory import create_predictive_memory
from axis.systems.construction_kit.traces.state import create_trace_state
from axis.systems.system_c.config import SystemCConfig
from axis.systems.system_c.transition import SystemCTransition
from axis.systems.system_c.types import AgentStateC


class SystemC:
    """System C: predictive action modulation agent.

    Extends System A by inserting a prediction-based modulation factor
    into the hunger action projection:

        psi_C(a) = d_H(t) * phi_H(a, u_t) * mu_H(s_t, a)

    When prediction is disabled (lambda_+ = lambda_- = 0), System C
    reduces exactly to System A.

    Implements SystemInterface.
    """

    def __init__(self, config: SystemCConfig) -> None:
        self._config = config
        self._sensor = VonNeumannSensor()
        self._drive = HungerDrive(
            consume_weight=config.policy.consume_weight,
            stay_suppression=config.policy.stay_suppression,
            max_energy=config.agent.max_energy,
        )
        self._policy = SoftmaxPolicy(
            temperature=config.policy.temperature,
            selection_mode=config.policy.selection_mode,
        )
        self._transition = SystemCTransition(config=config)

    def system_type(self) -> str:
        """Return the system's unique type identifier."""
        return "system_c"

    def action_space(self) -> tuple[str, ...]:
        """Return the ordered tuple of action names."""
        return ("up", "down", "left", "right", "consume", "stay")

    def initialize_state(self) -> AgentStateC:
        """Create initial agent state from stored config."""
        return AgentStateC(
            energy=self._config.agent.initial_energy,
            observation_buffer=ObservationBuffer(
                entries=(),
                capacity=self._config.agent.buffer_capacity,
            ),
            predictive_memory=create_predictive_memory(),
            trace_state=create_trace_state(),
            last_observation=None,
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
        """6-step pipeline: perceive -> drive -> features/context -> modulate -> policy -> return."""
        actions = self.action_space()
        pred_cfg = self._config.prediction

        # Step 1: Perception
        observation = self._sensor.observe(
            world_view, world_view.agent_position)

        # Step 2: Drive evaluation
        drive_output = self._drive.compute(agent_state, observation)

        # Step 3: Predictive feature extraction and context encoding
        features = extract_predictive_features(observation)
        context = encode_context(
            features, threshold=pred_cfg.context_threshold)

        # Step 4: Action score modulation
        modulated_scores = modulate_action_scores(
            drive_output.action_contributions,
            context,
            actions,
            agent_state.trace_state,
            positive_sensitivity=pred_cfg.positive_sensitivity,
            negative_sensitivity=pred_cfg.negative_sensitivity,
            modulation_min=pred_cfg.modulation_min,
            modulation_max=pred_cfg.modulation_max,
        )

        # Step 5: Policy selection
        policy_result = self._policy.select(modulated_scores, observation, rng)

        # Step 6: Assemble decision data
        decision_data = {
            "observation": observation.model_dump(),
            "drive": {
                "activation": drive_output.activation,
                "action_contributions": drive_output.action_contributions,
            },
            "prediction": {
                "context": context,
                "features": features,
                "modulated_scores": modulated_scores,
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
        """Delegate to SystemCTransition for state update."""
        return self._transition.transition(
            agent_state, action_outcome, new_observation,
        )

    def action_handlers(self) -> dict[str, Any]:
        """Return custom action handlers for ActionRegistry registration."""
        from axis.systems.construction_kit.types.actions import handle_consume

        return {"consume": handle_consume}

    def observe(self, world_view: Any, position: Any) -> Any:
        """Produce observation from world state."""
        return self._sensor.observe(world_view, position)

    def action_context(self) -> dict[str, Any]:
        """Return context dict for action handlers."""
        return {"max_consume": self._config.transition.max_consume}

    @property
    def sensor(self) -> VonNeumannSensor:
        """Access the sensor component."""
        return self._sensor

    @property
    def config(self) -> SystemCConfig:
        """Access the parsed system config."""
        return self._config
