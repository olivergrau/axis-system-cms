"""System A+W behavioral metric extension."""

from __future__ import annotations

from typing import Any

from axis.framework.metrics.extensions import register_metric_extension
from axis.framework.metrics.types import StandardBehaviorMetrics
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace


def _decision_data(step: BaseStepTrace) -> dict[str, Any]:
    system_data = step.system_data or {}
    data = system_data.get("decision_data", {})
    return data if isinstance(data, dict) else {}


def _trace_data(step: BaseStepTrace) -> dict[str, Any]:
    system_data = step.system_data or {}
    data = system_data.get("trace_data", {})
    return data if isinstance(data, dict) else {}


def _to_float_list(value: Any) -> list[float]:
    if isinstance(value, (list, tuple)):
        return [float(v) for v in value]
    return []


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


@register_metric_extension("system_aw")
def system_aw_behavior_metrics(
    episode_traces: tuple[BaseEpisodeTrace, ...],
    standard_metrics: StandardBehaviorMetrics,
) -> dict[str, Any]:
    del standard_metrics

    hunger_weights: list[float] = []
    curiosity_weights: list[float] = []
    curiosity_activations: list[float] = []
    mean_spatial_novelties: list[float] = []
    mean_sensory_novelties: list[float] = []
    mean_composite_novelties: list[float] = []
    visit_count_current_values: list[float] = []
    episode_unique_cells: list[float] = []
    episode_revisit_ratios: list[float] = []

    arbitrated_steps = 0
    curiosity_dominance_steps = 0
    curiosity_pressure_steps = 0
    curiosity_led_move_steps = 0
    movement_steps = 0
    consume_under_curiosity_pressure_steps = 0
    consume_steps = 0

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

        for step in steps:
            decision = _decision_data(step)
            trace_data = _trace_data(step)
            arbitration = decision.get("arbitration", {}) or {}
            curiosity_drive = decision.get("curiosity_drive", {}) or {}
            hunger_drive = decision.get("hunger_drive", {}) or {}

            if isinstance(arbitration, dict):
                hunger = float(arbitration.get("hunger_weight", 0.0))
                curiosity = float(arbitration.get("curiosity_weight", 0.0))
                hunger_weights.append(hunger)
                curiosity_weights.append(curiosity)
                arbitrated_steps += 1
                if curiosity > hunger:
                    curiosity_dominance_steps += 1

            if isinstance(hunger_drive, dict):
                hunger_activation = float(hunger_drive.get("activation", 0.0))
            else:
                hunger_activation = 0.0

            if isinstance(curiosity_drive, dict):
                activation = float(curiosity_drive.get("activation", 0.0))
                curiosity_activations.append(activation)

                spatial = _to_float_list(curiosity_drive.get("spatial_novelty", ()))
                sensory = _to_float_list(curiosity_drive.get("sensory_novelty", ()))
                composite = _to_float_list(curiosity_drive.get("composite_novelty", ()))
                if spatial:
                    mean_spatial_novelties.append(sum(spatial) / len(spatial))
                if sensory:
                    mean_sensory_novelties.append(sum(sensory) / len(sensory))
                if composite:
                    mean_composite_novelties.append(sum(composite) / len(composite))

                curiosity_weight = float(arbitration.get("curiosity_weight", 0.0))
                hunger_weight = float(arbitration.get("hunger_weight", 0.0))
                curiosity_pressure = curiosity_weight * activation
                hunger_pressure = hunger_weight * hunger_activation
                if curiosity_pressure > hunger_pressure:
                    curiosity_pressure_steps += 1
                    if step.action in {"up", "down", "left", "right"}:
                        curiosity_led_move_steps += 1
                    if step.action == "consume":
                        consume_under_curiosity_pressure_steps += 1

            if step.action in {"up", "down", "left", "right"}:
                movement_steps += 1
            if step.action == "consume":
                consume_steps += 1

            if "visit_count_at_current" in trace_data:
                visit_count_current_values.append(
                    float(trace_data.get("visit_count_at_current", 0.0))
                )

    return {
        "system_aw_arbitration": {
            "curiosity_dominance_rate": (
                curiosity_dominance_steps / arbitrated_steps
                if arbitrated_steps > 0 else None
            ),
            "mean_curiosity_weight": _mean(curiosity_weights),
            "mean_hunger_weight": _mean(hunger_weights),
            "arbitrated_step_count": arbitrated_steps,
        },
        "system_aw_curiosity": {
            "mean_curiosity_activation": _mean(curiosity_activations),
            "mean_spatial_novelty": _mean(mean_spatial_novelties),
            "mean_sensory_novelty": _mean(mean_sensory_novelties),
            "mean_composite_novelty": _mean(mean_composite_novelties),
            "curiosity_pressure_rate": (
                curiosity_pressure_steps / arbitrated_steps
                if arbitrated_steps > 0 else None
            ),
        },
        "system_aw_behavior": {
            "curiosity_led_move_rate": (
                curiosity_led_move_steps / arbitrated_steps
                if arbitrated_steps > 0 else None
            ),
            "consume_under_curiosity_pressure_rate": (
                consume_under_curiosity_pressure_steps / curiosity_pressure_steps
                if curiosity_pressure_steps > 0 else None
            ),
            "movement_step_rate": (
                movement_steps / arbitrated_steps
                if arbitrated_steps > 0 else None
            ),
            "consume_step_rate": (
                consume_steps / arbitrated_steps
                if arbitrated_steps > 0 else None
            ),
        },
        "system_aw_world_model": {
            "world_model_unique_cells": _mean(episode_unique_cells),
            "mean_visit_count_at_current": _mean(visit_count_current_values),
            "world_model_revisit_ratio": _mean(episode_revisit_ratios),
        },
    }
