"""System C+W transition pipeline."""

from __future__ import annotations

from axis.sdk.actions import MOVEMENT_DELTAS, STAY
from axis.sdk.types import TransitionResult
from axis.sdk.world_types import ActionOutcome
from axis.systems.construction_kit.drives.curiosity import CuriosityDrive
from axis.systems.construction_kit.energy.functions import clip_energy
from axis.systems.construction_kit.memory.observation_buffer import update_observation_buffer
from axis.systems.construction_kit.memory.world_model import update_world_model
from axis.systems.construction_kit.observation.types import Observation
from axis.systems.construction_kit.prediction.error import compute_prediction_error
from axis.systems.construction_kit.prediction.memory import (
    get_prediction,
    update_predictive_memory,
)
from axis.systems.construction_kit.traces.state import get_confidence, get_frustration
from axis.systems.construction_kit.traces.update import update_traces
from axis.systems.system_cw.config import SystemCWConfig
from axis.systems.system_cw.context import encode_context_cw
from axis.systems.system_cw.features import extract_predictive_features_cw
from axis.systems.system_cw.outcomes import (
    compute_curiosity_outcome,
    compute_hunger_outcome,
    novelty_weight_for_action,
)
from axis.systems.system_cw.types import AgentStateCW

ACTION_NAMES: tuple[str, ...] = (
    "up", "down", "left", "right", "consume", "stay",
)


class SystemCWTransition:
    """Transition function for System C+W."""

    def __init__(self, *, config: SystemCWConfig) -> None:
        self._config = config
        self._max_energy = config.agent.max_energy
        self._move_cost = config.transition.move_cost
        self._consume_cost = config.transition.consume_cost
        self._stay_cost = config.transition.stay_cost
        self._energy_gain_factor = config.transition.energy_gain_factor
        self._curiosity_drive = CuriosityDrive(
            base_curiosity=config.curiosity.base_curiosity,
            spatial_sensory_balance=config.curiosity.spatial_sensory_balance,
            explore_suppression=config.curiosity.explore_suppression,
            novelty_sharpness=config.curiosity.novelty_sharpness,
        )

    def transition(
        self,
        agent_state: AgentStateCW,
        action_outcome: ActionOutcome,
        observation: Observation,
        *,
        timestep: int = 0,
    ) -> TransitionResult:
        shared_cfg = self._config.prediction.shared
        hunger_cfg = self._config.prediction.hunger
        curiosity_cfg = self._config.prediction.curiosity
        outcomes_cfg = self._config.prediction.outcomes

        cost = self._get_action_cost(action_outcome.action)
        energy_gain = self._energy_gain_factor * action_outcome.data.get(
            "resource_consumed", 0.0,
        )
        new_energy = clip_energy(
            agent_state.energy - cost + energy_gain,
            self._max_energy,
        )

        new_buffer = update_observation_buffer(
            agent_state.observation_buffer, observation, timestep,
        )
        new_world_model = update_world_model(
            agent_state.world_model,
            action_outcome.action,
            action_outcome.moved,
        )

        new_memory = agent_state.predictive_memory
        new_hunger_traces = agent_state.hunger_trace_state
        new_curiosity_traces = agent_state.curiosity_trace_state
        prediction_trace: dict[str, object] = {}

        pre_observation = action_outcome.data.get(
            "_pre_observation", agent_state.last_observation,
        )

        if pre_observation is not None:
            pre_curiosity_output = self._curiosity_drive.compute(
                pre_observation,
                agent_state.observation_buffer,
                agent_state.world_model,
            )
            post_curiosity_output = self._curiosity_drive.compute(
                observation,
                new_buffer,
                new_world_model,
            )
            pre_features = extract_predictive_features_cw(
                pre_observation, pre_curiosity_output,
            )
            post_features = extract_predictive_features_cw(
                observation, post_curiosity_output,
            )
            context = encode_context_cw(
                pre_features,
                resource_threshold=shared_cfg.resource_threshold,
                novelty_threshold=shared_cfg.novelty_threshold,
                novelty_contrast_threshold=shared_cfg.novelty_contrast_threshold,
            )
            predicted = get_prediction(
                agent_state.predictive_memory,
                context,
                action_outcome.action,
            )
            feature_error = compute_prediction_error(
                predicted,
                post_features,
                positive_weights=shared_cfg.positive_weights,
                negative_weights=shared_cfg.negative_weights,
            )

            hunger_eval = compute_hunger_outcome(
                pre_observation,
                observation,
                predicted,
                current_weight=shared_cfg.local_resource_current_weight,
                neighbor_weight=shared_cfg.local_resource_neighbor_weight,
            )
            novelty_weight = novelty_weight_for_action(
                action_outcome.action,
                pre_curiosity_output.composite_novelty,
            )
            curiosity_eval = compute_curiosity_outcome(
                action=action_outcome.action,
                pre_observation=pre_observation,
                post_observation=observation,
                predicted_features=predicted,
                curiosity_activation=pre_curiosity_output.activation,
                novelty_weight=novelty_weight,
                nonmove_penalty=outcomes_cfg.nonmove_curiosity_penalty,
                current_weight=shared_cfg.local_resource_current_weight,
                neighbor_weight=shared_cfg.local_resource_neighbor_weight,
            )

            new_hunger_traces = update_traces(
                agent_state.hunger_trace_state,
                context,
                action_outcome.action,
                hunger_eval.error_positive,
                hunger_eval.error_negative,
                frustration_rate=hunger_cfg.frustration_rate,
                confidence_rate=hunger_cfg.confidence_rate,
            )
            new_curiosity_traces = update_traces(
                agent_state.curiosity_trace_state,
                context,
                action_outcome.action,
                curiosity_eval.error_positive,
                curiosity_eval.error_negative,
                frustration_rate=curiosity_cfg.frustration_rate,
                confidence_rate=curiosity_cfg.confidence_rate,
            )
            new_memory = update_predictive_memory(
                agent_state.predictive_memory,
                context,
                action_outcome.action,
                post_features,
                learning_rate=shared_cfg.memory_learning_rate,
            )

            prediction_trace = {
                "context": context,
                "predicted_features": predicted,
                "observed_features": post_features,
                "feature_error_positive": feature_error.scalar_positive,
                "feature_error_negative": feature_error.scalar_negative,
                "hunger": {
                    "actual": hunger_eval.actual,
                    "predicted": hunger_eval.predicted,
                    "error_positive": hunger_eval.error_positive,
                    "error_negative": hunger_eval.error_negative,
                    "confidence_value": get_confidence(
                        new_hunger_traces, context, action_outcome.action,
                    ),
                    "frustration_value": get_frustration(
                        new_hunger_traces, context, action_outcome.action,
                    ),
                },
                "curiosity": {
                    "actual": curiosity_eval.actual,
                    "predicted": curiosity_eval.predicted,
                    "error_positive": curiosity_eval.error_positive,
                    "error_negative": curiosity_eval.error_negative,
                    "novelty_weight": novelty_weight,
                    "curiosity_activation": pre_curiosity_output.activation,
                    "used_nonmove_penalty_rule": action_outcome.action not in MOVEMENT_DELTAS,
                    "is_movement_action": action_outcome.action in MOVEMENT_DELTAS,
                    "confidence_value": get_confidence(
                        new_curiosity_traces, context, action_outcome.action,
                    ),
                    "frustration_value": get_frustration(
                        new_curiosity_traces, context, action_outcome.action,
                    ),
                },
                "hunger_confidence_by_action": {
                    action: get_confidence(new_hunger_traces, context, action)
                    for action in ACTION_NAMES
                },
                "hunger_frustration_by_action": {
                    action: get_frustration(new_hunger_traces, context, action)
                    for action in ACTION_NAMES
                },
                "curiosity_confidence_by_action": {
                    action: get_confidence(new_curiosity_traces, context, action)
                    for action in ACTION_NAMES
                },
                "curiosity_frustration_by_action": {
                    action: get_frustration(new_curiosity_traces, context, action)
                    for action in ACTION_NAMES
                },
            }

        new_state = AgentStateCW(
            energy=new_energy,
            observation_buffer=new_buffer,
            world_model=new_world_model,
            predictive_memory=new_memory,
            hunger_trace_state=new_hunger_traces,
            curiosity_trace_state=new_curiosity_traces,
            last_observation=observation,
        )

        terminated = new_energy <= 0.0
        termination_reason = "energy_depleted" if terminated else None

        trace_data: dict[str, object] = {
            "energy_before": agent_state.energy,
            "energy_after": new_energy,
            "energy_delta": new_energy - agent_state.energy,
            "action_cost": cost,
            "energy_gain": energy_gain,
            "buffer_entries_before": len(agent_state.observation_buffer.entries),
            "buffer_entries_after": len(new_buffer.entries),
            "buffer_capacity": new_buffer.capacity,
            "relative_position": new_world_model.relative_position,
            "visit_count_at_current": dict(new_world_model.visit_counts).get(
                new_world_model.relative_position, 0,
            ),
            "visit_counts_map": [
                [[x, y], count]
                for (x, y), count in new_world_model.visit_counts
            ],
        }
        if prediction_trace:
            trace_data["prediction"] = prediction_trace

        return TransitionResult(
            new_state=new_state,
            trace_data=trace_data,
            terminated=terminated,
            termination_reason=termination_reason,
        )

    def _get_action_cost(self, action: str) -> float:
        if action in MOVEMENT_DELTAS:
            return self._move_cost
        if action == "consume":
            return self._consume_cost
        if action == STAY:
            return self._stay_cost
        return self._stay_cost
