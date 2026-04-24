"""System C transition -- energy, buffer, predictive update, and termination."""

from __future__ import annotations

from axis.sdk.actions import MOVEMENT_DELTAS, STAY
from axis.sdk.types import TransitionResult
from axis.sdk.world_types import ActionOutcome
from axis.systems.construction_kit.energy.functions import clip_energy
from axis.systems.construction_kit.memory.observation_buffer import update_observation_buffer
from axis.systems.construction_kit.observation.types import Observation
from axis.systems.construction_kit.prediction.context import encode_context
from axis.systems.construction_kit.prediction.error import compute_prediction_error
from axis.systems.construction_kit.prediction.features import extract_predictive_features
from axis.systems.construction_kit.prediction.memory import (
    get_prediction,
    update_predictive_memory,
)
from axis.systems.construction_kit.traces.state import (
    get_confidence,
    get_frustration,
)
from axis.systems.construction_kit.traces.update import update_traces
from axis.systems.system_c.config import SystemCConfig
from axis.systems.system_c.types import AgentStateC

ACTION_NAMES: tuple[str, ...] = (
    "up", "down", "left", "right", "consume", "stay",
)


class SystemCTransition:
    """Transition function for System C.

    Extends System A's transition with the predictive update cycle
    (phases 6a-6e). Constructor takes the full SystemCConfig to access
    prediction parameters.
    """

    def __init__(self, *, config: SystemCConfig) -> None:
        self._config = config
        self._max_energy = config.agent.max_energy
        self._move_cost = config.transition.move_cost
        self._consume_cost = config.transition.consume_cost
        self._stay_cost = config.transition.stay_cost
        self._energy_gain_factor = config.transition.energy_gain_factor

    def transition(
        self,
        agent_state: AgentStateC,
        action_outcome: ActionOutcome,
        observation: Observation,
        *,
        timestep: int = 0,
    ) -> TransitionResult:
        """Process action outcome: energy, buffer, predictive update, termination.

        Phases 4-5 (energy + buffer) identical to System A.
        Phase 6 (predictive update cycle) retrospectively updates
        memory and traces using pre-action vs post-action features.
        """
        pred_cfg = self._config.prediction

        # Phase 4: Energy update
        cost = self._get_action_cost(action_outcome.action)
        energy_gain = self._energy_gain_factor * action_outcome.data.get(
            "resource_consumed", 0.0,
        )
        new_energy = clip_energy(
            agent_state.energy - cost + energy_gain,
            self._max_energy,
        )

        # Phase 5: Observation buffer update
        new_buffer = update_observation_buffer(
            agent_state.observation_buffer, observation, timestep,
        )

        # Phase 6: Predictive update cycle
        new_memory = agent_state.predictive_memory
        new_traces = agent_state.trace_state
        prediction_trace: dict = {}

        pre_observation = action_outcome.data.get(
            "_pre_observation", agent_state.last_observation,
        )

        if pre_observation is not None:
            # 6a: Extract post-action features from current observation
            post_features = extract_predictive_features(observation)

            # 6b: Extract pre-action context from pre_observation
            pre_features = extract_predictive_features(
                pre_observation,
            )
            context = encode_context(
                pre_features, threshold=pred_cfg.context_threshold,
            )
            predicted = get_prediction(
                agent_state.predictive_memory,
                context,
                action_outcome.action,
            )

            # 6c: Compute prediction error
            error = compute_prediction_error(
                predicted,
                post_features,
                positive_weights=pred_cfg.positive_weights,
                negative_weights=pred_cfg.negative_weights,
            )

            # 6d: Update traces
            new_traces = update_traces(
                agent_state.trace_state,
                context,
                action_outcome.action,
                error.scalar_positive,
                error.scalar_negative,
                frustration_rate=pred_cfg.frustration_rate,
                confidence_rate=pred_cfg.confidence_rate,
            )

            # 6e: Update predictive memory
            new_memory = update_predictive_memory(
                agent_state.predictive_memory,
                context,
                action_outcome.action,
                post_features,
                learning_rate=pred_cfg.memory_learning_rate,
            )

            prediction_trace = {
                "context": context,
                "predicted_features": predicted,
                "observed_features": post_features,
                "error_positive": error.scalar_positive,
                "error_negative": error.scalar_negative,
                "confidence_value": get_confidence(
                    new_traces, context, action_outcome.action,
                ),
                "frustration_value": get_frustration(
                    new_traces, context, action_outcome.action,
                ),
                "confidence_by_action": {
                    action: get_confidence(new_traces, context, action)
                    for action in ACTION_NAMES
                },
                "frustration_by_action": {
                    action: get_frustration(new_traces, context, action)
                    for action in ACTION_NAMES
                },
            }

        # Phase 7: Build new state
        new_state = AgentStateC(
            energy=new_energy,
            observation_buffer=new_buffer,
            predictive_memory=new_memory,
            trace_state=new_traces,
            last_observation=observation,
        )

        # Phase 8: Termination check
        terminated = new_energy <= 0.0
        termination_reason = "energy_depleted" if terminated else None

        trace_data: dict = {
            "energy_before": agent_state.energy,
            "energy_after": new_energy,
            "energy_delta": new_energy - agent_state.energy,
            "action_cost": cost,
            "energy_gain": energy_gain,
            "buffer_entries_after": len(new_buffer.entries),
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
        """Return the energy cost for a given action."""
        if action in MOVEMENT_DELTAS:
            return self._move_cost
        if action == "consume":
            return self._consume_cost
        if action == STAY:
            return self._stay_cost
        return self._stay_cost
