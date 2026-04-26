"""System C+W -- predictive dual-drive agent."""

from __future__ import annotations

from typing import Any

import numpy as np

from axis.sdk.types import DecideResult, TransitionResult
from axis.systems.construction_kit.arbitration.scoring import combine_drive_scores
from axis.systems.construction_kit.arbitration.weights import compute_maslow_weights
from axis.systems.construction_kit.drives.curiosity import CuriosityDrive
from axis.systems.construction_kit.drives.hunger import HungerDrive
from axis.systems.construction_kit.memory.types import ObservationBuffer
from axis.systems.construction_kit.memory.world_model import create_world_model
from axis.systems.construction_kit.modulation.modulation import describe_action_modulation
from axis.systems.construction_kit.observation.sensor import VonNeumannSensor
from axis.systems.construction_kit.policy.softmax import SoftmaxPolicy
from axis.systems.construction_kit.prediction.memory import create_predictive_memory
from axis.systems.construction_kit.traces.state import create_trace_state
from axis.systems.system_cw.config import SystemCWConfig
from axis.systems.system_cw.context import encode_context_cw
from axis.systems.system_cw.features import extract_predictive_features_cw
from axis.systems.system_cw.transition import SystemCWTransition
from axis.systems.system_cw.types import AgentStateCW


class SystemCW:
    """System C+W: shared predictive memory with dual drive-specific traces."""

    def __init__(self, config: SystemCWConfig) -> None:
        self._config = config
        self._sensor = VonNeumannSensor()
        self._hunger_drive = HungerDrive(
            consume_weight=config.policy.consume_weight,
            stay_suppression=config.policy.stay_suppression,
            max_energy=config.agent.max_energy,
        )
        self._curiosity_drive = CuriosityDrive(
            base_curiosity=config.curiosity.base_curiosity,
            spatial_sensory_balance=config.curiosity.spatial_sensory_balance,
            explore_suppression=config.curiosity.explore_suppression,
            novelty_sharpness=config.curiosity.novelty_sharpness,
        )
        self._policy = SoftmaxPolicy(
            temperature=config.policy.temperature,
            selection_mode=config.policy.selection_mode,
        )
        self._transition = SystemCWTransition(config=config)

    def system_type(self) -> str:
        return "system_cw"

    def action_space(self) -> tuple[str, ...]:
        return ("up", "down", "left", "right", "consume", "stay")

    def initialize_state(self) -> AgentStateCW:
        shared_cfg = self._config.prediction.shared
        return AgentStateCW(
            energy=self._config.agent.initial_energy,
            observation_buffer=ObservationBuffer(
                entries=(),
                capacity=self._config.agent.buffer_capacity,
            ),
            world_model=create_world_model(),
            predictive_memory=create_predictive_memory(
                num_contexts=shared_cfg.context_cardinality,
                feature_dim=10,
            ),
            hunger_trace_state=create_trace_state(),
            curiosity_trace_state=create_trace_state(),
            last_observation=None,
        )

    def vitality(self, agent_state: Any) -> float:
        return agent_state.energy / self._config.agent.max_energy

    def decide(
        self,
        world_view: Any,
        agent_state: Any,
        rng: np.random.Generator,
    ) -> DecideResult:
        actions = self.action_space()
        shared_cfg = self._config.prediction.shared
        hunger_cfg = self._config.prediction.hunger
        curiosity_cfg = self._config.prediction.curiosity

        observation = self._sensor.observe(world_view, world_view.agent_position)
        hunger_output = self._hunger_drive.compute(agent_state, observation)
        curiosity_output = self._curiosity_drive.compute(
            observation,
            agent_state.observation_buffer,
            agent_state.world_model,
        )

        features = extract_predictive_features_cw(observation, curiosity_output)
        context = encode_context_cw(
            features,
            resource_threshold=shared_cfg.resource_threshold,
            novelty_threshold=shared_cfg.novelty_threshold,
            novelty_contrast_threshold=shared_cfg.novelty_contrast_threshold,
        )

        hunger_modulation = describe_action_modulation(
            hunger_output.action_contributions,
            context,
            actions,
            agent_state.hunger_trace_state,
            positive_sensitivity=hunger_cfg.positive_sensitivity,
            negative_sensitivity=hunger_cfg.negative_sensitivity,
            modulation_min=hunger_cfg.modulation_min,
            modulation_max=hunger_cfg.modulation_max,
            modulation_mode=hunger_cfg.modulation_mode,
            prediction_bias_scale=hunger_cfg.prediction_bias_scale,
            prediction_bias_clip=hunger_cfg.prediction_bias_clip,
        )
        curiosity_modulation = describe_action_modulation(
            curiosity_output.action_contributions,
            context,
            actions,
            agent_state.curiosity_trace_state,
            positive_sensitivity=curiosity_cfg.positive_sensitivity,
            negative_sensitivity=curiosity_cfg.negative_sensitivity,
            modulation_min=curiosity_cfg.modulation_min,
            modulation_max=curiosity_cfg.modulation_max,
            modulation_mode=curiosity_cfg.modulation_mode,
            prediction_bias_scale=curiosity_cfg.prediction_bias_scale,
            prediction_bias_clip=curiosity_cfg.prediction_bias_clip,
        )

        weights = compute_maslow_weights(
            hunger_output.activation,
            primary_weight_base=self._config.arbitration.hunger_weight_base,
            secondary_weight_base=self._config.arbitration.curiosity_weight_base,
            gating_sharpness=self._config.arbitration.gating_sharpness,
        )

        combined_scores = combine_drive_scores(
            drive_contributions=[
                hunger_modulation.final_scores,
                curiosity_modulation.final_scores,
            ],
            drive_activations=[
                hunger_output.activation,
                curiosity_output.activation,
            ],
            drive_weights=[
                weights.hunger_weight,
                weights.curiosity_weight,
            ],
        )
        counterfactual_combined_scores = combine_drive_scores(
            drive_contributions=[
                hunger_output.action_contributions,
                curiosity_output.action_contributions,
            ],
            drive_activations=[
                hunger_output.activation,
                curiosity_output.activation,
            ],
            drive_weights=[
                weights.hunger_weight,
                weights.curiosity_weight,
            ],
        )
        counterfactual_combined_scores_without_hunger_prediction = combine_drive_scores(
            drive_contributions=[
                hunger_output.action_contributions,
                curiosity_modulation.final_scores,
            ],
            drive_activations=[
                hunger_output.activation,
                curiosity_output.activation,
            ],
            drive_weights=[
                weights.hunger_weight,
                weights.curiosity_weight,
            ],
        )
        counterfactual_combined_scores_without_curiosity_prediction = combine_drive_scores(
            drive_contributions=[
                hunger_modulation.final_scores,
                curiosity_output.action_contributions,
            ],
            drive_activations=[
                hunger_output.activation,
                curiosity_output.activation,
            ],
            drive_weights=[
                weights.hunger_weight,
                weights.curiosity_weight,
            ],
        )
        policy_result = self._policy.select(combined_scores, observation, rng)

        decision_data = {
            "_pre_observation": observation,
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
            "prediction": {
                "context": context,
                "features": features,
                "hunger_modulation": {
                    "modulation_mode": hunger_cfg.modulation_mode,
                    "raw_scores": hunger_output.action_contributions,
                    "reliability_factors": hunger_modulation.modulation_factors,
                    "prediction_biases": hunger_modulation.prediction_biases,
                    "confidence_by_action": dict(zip(actions, hunger_modulation.confidences)),
                    "frustration_by_action": dict(zip(actions, hunger_modulation.frustrations)),
                    "final_scores": hunger_modulation.final_scores,
                    "modulated_scores": hunger_modulation.final_scores,
                },
                "curiosity_modulation": {
                    "modulation_mode": curiosity_cfg.modulation_mode,
                    "raw_scores": curiosity_output.action_contributions,
                    "reliability_factors": curiosity_modulation.modulation_factors,
                    "prediction_biases": curiosity_modulation.prediction_biases,
                    "confidence_by_action": dict(zip(actions, curiosity_modulation.confidences)),
                    "frustration_by_action": dict(zip(actions, curiosity_modulation.frustrations)),
                    "final_scores": curiosity_modulation.final_scores,
                    "modulated_scores": curiosity_modulation.final_scores,
                },
                "counterfactual_hunger_scores": hunger_output.action_contributions,
                "counterfactual_curiosity_scores": curiosity_output.action_contributions,
                "counterfactual_combined_scores": counterfactual_combined_scores,
                "counterfactual_combined_scores_without_hunger_prediction": (
                    counterfactual_combined_scores_without_hunger_prediction
                ),
                "counterfactual_combined_scores_without_curiosity_prediction": (
                    counterfactual_combined_scores_without_curiosity_prediction
                ),
                "counterfactual_top_action": actions[
                    max(range(len(counterfactual_combined_scores)), key=counterfactual_combined_scores.__getitem__)
                ],
                "counterfactual_top_action_without_hunger_prediction": actions[
                    max(
                        range(len(counterfactual_combined_scores_without_hunger_prediction)),
                        key=counterfactual_combined_scores_without_hunger_prediction.__getitem__,
                    )
                ],
                "counterfactual_top_action_without_curiosity_prediction": actions[
                    max(
                        range(len(counterfactual_combined_scores_without_curiosity_prediction)),
                        key=counterfactual_combined_scores_without_curiosity_prediction.__getitem__,
                    )
                ],
            },
            "arbitration": {
                "hunger_weight": weights.hunger_weight,
                "curiosity_weight": weights.curiosity_weight,
            },
            "combined_scores": combined_scores,
            "policy": policy_result.policy_data,
        }

        return DecideResult(action=policy_result.action, decision_data=decision_data)

    def transition(
        self,
        agent_state: Any,
        action_outcome: Any,
        new_observation: Any,
    ) -> TransitionResult:
        return self._transition.transition(agent_state, action_outcome, new_observation)

    def action_handlers(self) -> dict[str, Any]:
        from axis.systems.construction_kit.types.actions import handle_consume

        return {"consume": handle_consume}

    def observe(self, world_view: Any, position: Any) -> Any:
        return self._sensor.observe(world_view, position)

    def action_context(self) -> dict[str, Any]:
        return {"max_consume": self._config.transition.max_consume}

    @property
    def config(self) -> SystemCWConfig:
        return self._config
