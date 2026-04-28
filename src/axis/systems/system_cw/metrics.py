"""System C+W behavioral metric extension."""

from __future__ import annotations

from typing import Any

from axis.framework.metrics.extensions import register_metric_extension
from axis.framework.metrics.types import StandardBehaviorMetrics
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace

MOVEMENT_ACTIONS = {"up", "down", "left", "right"}


def _decision_data(step: BaseStepTrace) -> dict[str, Any]:
    system_data = step.system_data or {}
    data = system_data.get("decision_data", {})
    return data if isinstance(data, dict) else {}


def _trace_data(step: BaseStepTrace) -> dict[str, Any]:
    system_data = step.system_data or {}
    data = system_data.get("trace_data", {})
    return data if isinstance(data, dict) else {}


def _to_float_list(value: Any) -> list[float]:
    if isinstance(value, dict):
        return [float(v) for v in value.values()]
    if isinstance(value, (list, tuple)):
        return [float(v) for v in value]
    return []


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _mean_of_sequence(values: Any) -> float | None:
    floats = _to_float_list(values)
    if not floats:
        return None
    return sum(floats) / len(floats)


def _top_index(values: list[float]) -> int | None:
    if not values:
        return None
    return max(range(len(values)), key=values.__getitem__)


def _top_margin(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    ordered = sorted(values, reverse=True)
    return ordered[0] - ordered[1]


def _rank_order(values: list[float]) -> tuple[int, ...]:
    return tuple(sorted(range(len(values)), key=lambda i: (-values[i], i)))


@register_metric_extension("system_cw")
def system_cw_behavior_metrics(
    episode_traces: tuple[BaseEpisodeTrace, ...],
    standard_metrics: StandardBehaviorMetrics,
) -> dict[str, Any]:
    del standard_metrics

    feature_errors: list[float] = []
    hunger_modulation_strengths: list[float] = []
    curiosity_modulation_strengths: list[float] = []
    modulation_divergences: list[float] = []
    hunger_confidence_values: list[float] = []
    hunger_frustration_values: list[float] = []
    curiosity_confidence_values: list[float] = []
    curiosity_frustration_values: list[float] = []
    hunger_trace_balances: list[float] = []
    curiosity_trace_balances: list[float] = []
    trace_divergences: list[float] = []
    hunger_errors: list[float] = []
    curiosity_errors: list[float] = []
    hunger_signed_errors: list[float] = []
    curiosity_signed_errors: list[float] = []
    novelty_weights: list[float] = []
    curiosity_activations: list[float] = []
    hunger_activations: list[float] = []
    hunger_weights: list[float] = []
    curiosity_weights: list[float] = []
    weighted_curiosity_pressures: list[float] = []
    weighted_hunger_pressures: list[float] = []
    mean_spatial_novelties: list[float] = []
    mean_sensory_novelties: list[float] = []
    mean_composite_novelties: list[float] = []
    visit_count_current_values: list[float] = []
    episode_unique_cells: list[float] = []
    episode_revisit_ratios: list[float] = []
    hunger_reinforcements = 0
    hunger_suppressions = 0
    hunger_factor_count = 0
    curiosity_reinforcements = 0
    curiosity_suppressions = 0
    curiosity_factor_count = 0
    curiosity_dominance_steps = 0
    curiosity_pressure_steps = 0
    curiosity_led_move_steps = 0
    consume_under_curiosity_pressure_steps = 0
    nonzero_hunger_trace_steps = 0
    nonzero_curiosity_trace_steps = 0
    movement_prediction_steps = 0
    novel_move_yields: list[float] = []
    novel_move_success_steps = 0
    prediction_changed_top_action_steps = 0
    prediction_changed_top_action_eligible_steps = 0
    behavioral_prediction_impact_steps = 0
    behavioral_prediction_impact_eligible_steps = 0
    prediction_changed_arbitrated_margins: list[float] = []
    nonmove_curiosity_penalty_steps = 0
    nonmove_curiosity_penalty_eligible_steps = 0
    hunger_counterfactual_impacts: list[float] = []
    curiosity_counterfactual_impacts: list[float] = []
    prediction_steps = 0
    arbitrated_steps = 0

    for trace in episode_traces:
        steps = trace.steps
        if not steps:
            continue

        final_visit_map = _trace_data(steps[-1]).get("visit_counts_map", [])
        if isinstance(final_visit_map, list):
            episode_unique_cells.append(float(len(final_visit_map)))
            total_visits = 0
            for entry in final_visit_map:
                if (
                    isinstance(entry, list)
                    and len(entry) == 2
                    and isinstance(entry[1], (int, float))
                ):
                    total_visits += int(entry[1])
            if total_visits > 0:
                episode_revisit_ratios.append(
                    max(0.0, 1.0 - (len(final_visit_map) / total_visits))
                )

        for step in trace.steps:
            decision = _decision_data(step)
            trace_data = _trace_data(step)
            prediction = decision.get("prediction", {}) or {}
            arbitration = decision.get("arbitration", {}) or {}
            prediction_trace = trace_data.get("prediction", {}) or {}

            hunger_drive = decision.get("hunger_drive", {}) or {}
            curiosity_drive = decision.get("curiosity_drive", {}) or {}
            hunger_mod = prediction.get("hunger_modulation", {}) or {}
            curiosity_mod = prediction.get("curiosity_modulation", {}) or {}
            counterfactual_combined = _to_float_list(
                prediction.get("counterfactual_combined_scores", ())
            )
            counterfactual_without_hunger = _to_float_list(
                prediction.get("counterfactual_combined_scores_without_hunger_prediction", ())
            )
            counterfactual_without_curiosity = _to_float_list(
                prediction.get("counterfactual_combined_scores_without_curiosity_prediction", ())
            )
            combined_scores = _to_float_list(decision.get("combined_scores", ()))
            hunger_raw = _to_float_list(hunger_mod.get("raw_scores", ()))
            hunger_final = _to_float_list(hunger_mod.get("final_scores", ()))
            curiosity_raw = _to_float_list(curiosity_mod.get("raw_scores", ()))
            curiosity_final = _to_float_list(curiosity_mod.get("final_scores", ()))
            hunger_factors = _to_float_list(hunger_mod.get("reliability_factors", ()))
            curiosity_factors = _to_float_list(curiosity_mod.get("reliability_factors", ()))
            spatial_mean = _mean_of_sequence(curiosity_drive.get("spatial_novelty", ()))
            sensory_mean = _mean_of_sequence(curiosity_drive.get("sensory_novelty", ()))
            composite_mean = _mean_of_sequence(curiosity_drive.get("composite_novelty", ()))
            if spatial_mean is not None:
                mean_spatial_novelties.append(spatial_mean)
            if sensory_mean is not None:
                mean_sensory_novelties.append(sensory_mean)
            if composite_mean is not None:
                mean_composite_novelties.append(composite_mean)

            if hunger_raw and hunger_final:
                n = min(len(hunger_raw), len(hunger_final))
                hunger_strength = (
                    sum(abs(hunger_final[i] - hunger_raw[i]) for i in range(n)) / n
                )
                hunger_modulation_strengths.append(hunger_strength)
            else:
                hunger_strength = None
            if curiosity_raw and curiosity_final:
                n = min(len(curiosity_raw), len(curiosity_final))
                curiosity_strength = (
                    sum(abs(curiosity_final[i] - curiosity_raw[i]) for i in range(n)) / n
                )
                curiosity_modulation_strengths.append(curiosity_strength)
            else:
                curiosity_strength = None

            if hunger_strength is not None and curiosity_strength is not None:
                modulation_divergences.append(abs(hunger_strength - curiosity_strength))

            for factor in hunger_factors:
                hunger_factor_count += 1
                if factor > 1.0:
                    hunger_reinforcements += 1
                elif factor < 1.0:
                    hunger_suppressions += 1
            for factor in curiosity_factors:
                curiosity_factor_count += 1
                if factor > 1.0:
                    curiosity_reinforcements += 1
                elif factor < 1.0:
                    curiosity_suppressions += 1

            if isinstance(arbitration, dict):
                hunger_weight = float(arbitration.get("hunger_weight", 0.0))
                curiosity_weight = float(arbitration.get("curiosity_weight", 0.0))
                hunger_weights.append(hunger_weight)
                curiosity_weights.append(curiosity_weight)
                arbitrated_steps += 1
                if curiosity_weight > hunger_weight:
                    curiosity_dominance_steps += 1
            else:
                hunger_weight = 0.0
                curiosity_weight = 0.0

            if isinstance(hunger_drive, dict):
                hunger_activation = float(hunger_drive.get("activation", 0.0))
                hunger_activations.append(hunger_activation)
            else:
                hunger_activation = 0.0
            if isinstance(curiosity_drive, dict):
                curiosity_activation = float(curiosity_drive.get("activation", 0.0))
                curiosity_activations.append(curiosity_activation)
            else:
                curiosity_activation = 0.0

            curiosity_pressure = curiosity_weight * curiosity_activation
            hunger_pressure = hunger_weight * hunger_activation
            if curiosity_pressure > hunger_pressure:
                curiosity_pressure_steps += 1
                if step.action in MOVEMENT_ACTIONS:
                    curiosity_led_move_steps += 1
                if step.action == "consume":
                    consume_under_curiosity_pressure_steps += 1

            weighted_hunger_pressures.append(hunger_weight * hunger_activation)

            top_actual = _top_index(combined_scores)
            top_counterfactual = _top_index(counterfactual_combined)
            if top_actual is not None and top_counterfactual is not None:
                behavioral_prediction_impact_eligible_steps += 1
                if _rank_order(combined_scores) != _rank_order(counterfactual_combined):
                    behavioral_prediction_impact_steps += 1
            if top_actual is not None and top_counterfactual is not None:
                prediction_changed_top_action_eligible_steps += 1
                if top_actual != top_counterfactual:
                    prediction_changed_top_action_steps += 1
                actual_margin = _top_margin(combined_scores)
                counterfactual_margin = _top_margin(counterfactual_combined)
                if actual_margin is not None and counterfactual_margin is not None:
                    prediction_changed_arbitrated_margins.append(
                        actual_margin - counterfactual_margin
                    )

            if top_actual is not None:
                if counterfactual_without_hunger:
                    top_without_hunger = _top_index(counterfactual_without_hunger)
                    if top_without_hunger is not None and top_without_hunger != top_actual:
                        hunger_counterfactual_impacts.append(1.0)
                    else:
                        hunger_counterfactual_impacts.append(0.0)
                if counterfactual_without_curiosity:
                    top_without_curiosity = _top_index(counterfactual_without_curiosity)
                    if top_without_curiosity is not None and top_without_curiosity != top_actual:
                        curiosity_counterfactual_impacts.append(1.0)
                    else:
                        curiosity_counterfactual_impacts.append(0.0)

            if isinstance(prediction_trace, dict) and prediction_trace:
                prediction_steps += 1
                hunger_trace = prediction_trace.get("hunger", {}) or {}
                curiosity_trace = prediction_trace.get("curiosity", {}) or {}
                feature_errors.append(
                    float(prediction_trace.get("feature_error_positive", 0.0))
                    + float(prediction_trace.get("feature_error_negative", 0.0))
                )

                hunger_positive = float(hunger_trace.get("error_positive", 0.0))
                hunger_negative = float(hunger_trace.get("error_negative", 0.0))
                curiosity_positive = float(curiosity_trace.get("error_positive", 0.0))
                curiosity_negative = float(curiosity_trace.get("error_negative", 0.0))
                hunger_errors.append(
                    hunger_positive + hunger_negative
                )
                curiosity_errors.append(
                    curiosity_positive + curiosity_negative
                )
                hunger_signed_errors.append(hunger_positive - hunger_negative)
                curiosity_signed_errors.append(curiosity_positive - curiosity_negative)

                hunger_confidence = float(hunger_trace.get("confidence_value", 0.0))
                hunger_frustration = float(hunger_trace.get("frustration_value", 0.0))
                curiosity_confidence = float(curiosity_trace.get("confidence_value", 0.0))
                curiosity_frustration = float(curiosity_trace.get("frustration_value", 0.0))
                hunger_confidence_values.append(hunger_confidence)
                hunger_frustration_values.append(hunger_frustration)
                curiosity_confidence_values.append(curiosity_confidence)
                curiosity_frustration_values.append(curiosity_frustration)

                hunger_balance = hunger_confidence - hunger_frustration
                curiosity_balance = curiosity_confidence - curiosity_frustration
                hunger_trace_balances.append(hunger_balance)
                curiosity_trace_balances.append(curiosity_balance)
                trace_divergences.append(abs(hunger_balance - curiosity_balance))
                if hunger_confidence > 0.0 or hunger_frustration > 0.0:
                    nonzero_hunger_trace_steps += 1
                if curiosity_confidence > 0.0 or curiosity_frustration > 0.0:
                    nonzero_curiosity_trace_steps += 1

                novelty_weight = float(curiosity_trace.get("novelty_weight", 0.0))
                novelty_weights.append(novelty_weight)
                weighted_curiosity_pressures.append(
                    curiosity_weight * curiosity_activation * novelty_weight
                )

                if step.action in MOVEMENT_ACTIONS:
                    movement_prediction_steps += 1
                    actual_curiosity_yield = float(curiosity_trace.get("actual", 0.0))
                    novel_move_yields.append(actual_curiosity_yield)
                    if actual_curiosity_yield > 0.0:
                        novel_move_success_steps += 1
                else:
                    nonmove_curiosity_penalty_eligible_steps += 1
                    if bool(curiosity_trace.get("used_nonmove_penalty_rule", False)):
                        nonmove_curiosity_penalty_steps += 1

            if "visit_count_at_current" in trace_data:
                visit_count_current_values.append(
                    float(trace_data.get("visit_count_at_current", 0.0))
                )

    return {
        "system_cw_prediction": {
            "prediction_step_count": prediction_steps,
            "feature_prediction_error_mean": _mean(feature_errors),
            "hunger_prediction_error_mean": _mean(hunger_errors),
            "curiosity_prediction_error_mean": _mean(curiosity_errors),
            "hunger_signed_prediction_error": _mean(hunger_signed_errors),
            "curiosity_signed_prediction_error": _mean(curiosity_signed_errors),
            "mean_novelty_weight": _mean(novelty_weights),
            "movement_prediction_step_rate": (
                movement_prediction_steps / prediction_steps
                if prediction_steps > 0 else None
            ),
        },
        "system_cw_traces": {
            "hunger_confidence_trace_mean": _mean(hunger_confidence_values),
            "hunger_frustration_trace_mean": _mean(hunger_frustration_values),
            "curiosity_confidence_trace_mean": _mean(curiosity_confidence_values),
            "curiosity_frustration_trace_mean": _mean(curiosity_frustration_values),
            "hunger_trace_balance": _mean(hunger_trace_balances),
            "curiosity_trace_balance": _mean(curiosity_trace_balances),
            "trace_divergence_mean": _mean(trace_divergences),
            "nonzero_hunger_trace_rate": (
                nonzero_hunger_trace_steps / prediction_steps
                if prediction_steps > 0 else None
            ),
            "nonzero_curiosity_trace_rate": (
                nonzero_curiosity_trace_steps / prediction_steps
                if prediction_steps > 0 else None
            ),
        },
        "system_cw_modulation": {
            "hunger_modulation_strength": _mean(hunger_modulation_strengths),
            "curiosity_modulation_strength": _mean(curiosity_modulation_strengths),
            "mean_modulation_divergence": _mean(modulation_divergences),
            "hunger_reinforcement_rate": (
                hunger_reinforcements / hunger_factor_count
                if hunger_factor_count > 0 else None
            ),
            "hunger_suppression_rate": (
                hunger_suppressions / hunger_factor_count
                if hunger_factor_count > 0 else None
            ),
            "curiosity_reinforcement_rate": (
                curiosity_reinforcements / curiosity_factor_count
                if curiosity_factor_count > 0 else None
            ),
            "curiosity_suppression_rate": (
                curiosity_suppressions / curiosity_factor_count
                if curiosity_factor_count > 0 else None
            ),
        },
        "system_cw_arbitration": {
            "mean_hunger_weight": _mean(hunger_weights),
            "mean_curiosity_weight": _mean(curiosity_weights),
            "curiosity_dominance_rate": (
                curiosity_dominance_steps / arbitrated_steps
                if arbitrated_steps > 0 else None
            ),
            "mean_curiosity_activation": _mean(curiosity_activations),
            "curiosity_pressure_rate": (
                curiosity_pressure_steps / arbitrated_steps
                if arbitrated_steps > 0 else None
            ),
            "prediction_weighted_curiosity_pressure": _mean(weighted_curiosity_pressures),
            "prediction_weighted_hunger_pressure": _mean(weighted_hunger_pressures),
        },
        "system_cw_curiosity": {
            "mean_spatial_novelty": _mean(mean_spatial_novelties),
            "mean_sensory_novelty": _mean(mean_sensory_novelties),
            "mean_composite_novelty": _mean(mean_composite_novelties),
            "curiosity_led_move_rate": (
                curiosity_led_move_steps / arbitrated_steps
                if arbitrated_steps > 0 else None
            ),
            "consume_under_curiosity_pressure_rate": (
                consume_under_curiosity_pressure_steps / curiosity_pressure_steps
                if curiosity_pressure_steps > 0 else None
            ),
            "novel_move_yield_mean": _mean(novel_move_yields),
            "novel_move_success_rate": (
                novel_move_success_steps / movement_prediction_steps
                if movement_prediction_steps > 0 else None
            ),
        },
        "system_cw_world_model": {
            "world_model_unique_cells": _mean(episode_unique_cells),
            "mean_visit_count_at_current": _mean(visit_count_current_values),
            "world_model_revisit_ratio": _mean(episode_revisit_ratios),
        },
        "system_cw_prediction_impact": {
            "behavioral_prediction_impact_rate": (
                behavioral_prediction_impact_steps / behavioral_prediction_impact_eligible_steps
                if behavioral_prediction_impact_eligible_steps > 0 else None
            ),
            "prediction_changed_top_action_rate": (
                prediction_changed_top_action_steps / prediction_changed_top_action_eligible_steps
                if prediction_changed_top_action_eligible_steps > 0 else None
            ),
            "prediction_changed_arbitrated_margin": _mean(
                prediction_changed_arbitrated_margins
            ),
            "nonmove_curiosity_penalty_rate": (
                nonmove_curiosity_penalty_steps / nonmove_curiosity_penalty_eligible_steps
                if nonmove_curiosity_penalty_eligible_steps > 0 else None
            ),
            "counterfactual_hunger_modulation_impact": _mean(
                hunger_counterfactual_impacts
            ),
            "counterfactual_curiosity_modulation_impact": _mean(
                curiosity_counterfactual_impacts
            ),
        },
    }
