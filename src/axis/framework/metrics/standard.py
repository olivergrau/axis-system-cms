"""Framework-standard behavioral metrics derived from replay traces."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence
from math import sqrt
from typing import Any

from axis.framework.metrics.types import (
    EpisodeBehaviorMetrics,
    MetricSummaryStats,
    StandardBehaviorMetrics,
)
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace

_MOVEMENT_ACTIONS = {"up", "down", "left", "right"}


def _metric_stats(values: Sequence[float]) -> MetricSummaryStats:
    """Compute aggregate statistics for one scalar metric."""
    if not values:
        return MetricSummaryStats()

    n = len(values)
    mean = sum(values) / n
    std = sqrt(sum((v - mean) ** 2 for v in values) / n)
    return MetricSummaryStats(
        mean=mean,
        std=std,
        min=min(values),
        max=max(values),
        n=n,
    )


def _trace_data(step: BaseStepTrace) -> dict[str, Any]:
    data = step.system_data or {}
    value = data.get("trace_data")
    return value if isinstance(value, dict) else {}


def _decision_data(step: BaseStepTrace) -> dict[str, Any]:
    data = step.system_data or {}
    value = data.get("decision_data")
    return value if isinstance(value, dict) else {}


def _policy_probabilities(step: BaseStepTrace) -> tuple[float, ...]:
    decision = _decision_data(step)
    policy = decision.get("policy", {})
    probabilities = policy.get("probabilities", ())
    if isinstance(probabilities, (list, tuple)):
        return tuple(float(p) for p in probabilities)
    return ()


def _current_resource(step: BaseStepTrace) -> float | None:
    decision = _decision_data(step)
    observation = decision.get("observation", {})
    current = observation.get("current", {})
    value = current.get("resource")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compute_episode_behavior_metrics(
    trace: BaseEpisodeTrace,
) -> EpisodeBehaviorMetrics:
    """Compute first-wave standard metrics for one episode trace."""
    steps = trace.steps
    total_steps = trace.total_steps

    if not steps or total_steps == 0:
        return EpisodeBehaviorMetrics(
            total_steps=0,
            final_vitality=trace.final_vitality,
            died=trace.final_vitality <= 0.0,
            resource_gain_per_step=0.0,
            net_energy_efficiency=0.0,
            successful_consume_rate=0.0,
            consume_on_empty_rate=0.0,
            failed_movement_rate=0.0,
            action_entropy=0.0,
            policy_sharpness=0.0,
            action_inertia=0.0,
            unique_cells_visited=0.0,
            coverage_efficiency=0.0,
            revisit_rate=0.0,
        )

    total_energy_gain = 0.0
    total_action_cost = 0.0
    consume_actions = 0
    successful_consumes = 0
    consume_on_empty = 0
    movement_actions = 0
    failed_movements = 0
    sharpness_values: list[float] = []
    action_sequence: list[str] = []
    visited_cells: set[tuple[int, int]] = set()
    move_destinations: set[tuple[int, int]] = set()

    visited_cells.add((
        steps[0].agent_position_before.x,
        steps[0].agent_position_before.y,
    ))

    for step in steps:
        trace_data = _trace_data(step)
        total_energy_gain += float(trace_data.get("energy_gain", 0.0))
        total_action_cost += float(trace_data.get("action_cost", 0.0))

        action_sequence.append(step.action)
        probs = _policy_probabilities(step)
        if probs:
            sharpness_values.append(max(probs))

        visited_cells.add((
            step.agent_position_after.x,
            step.agent_position_after.y,
        ))

        if step.action == "consume":
            consume_actions += 1
            if float(trace_data.get("energy_gain", 0.0)) > 0.0:
                successful_consumes += 1
            current_resource = _current_resource(step)
            if current_resource is not None and current_resource <= 0.0:
                consume_on_empty += 1

        if step.action in _MOVEMENT_ACTIONS:
            movement_actions += 1
            if step.agent_position_before == step.agent_position_after:
                failed_movements += 1
            move_destinations.add((
                step.agent_position_after.x,
                step.agent_position_after.y,
            ))

    action_counts = Counter(action_sequence)
    entropy = 0.0
    for count in action_counts.values():
        p = count / total_steps
        if p > 0.0:
            entropy -= p * math.log(p)

    inertia_matches = sum(
        1 for prev, curr in zip(action_sequence, action_sequence[1:]) if prev == curr
    )
    inertia = inertia_matches / (len(action_sequence) - 1) if len(action_sequence) > 1 else 0.0

    successful_consume_rate = (
        successful_consumes / consume_actions if consume_actions > 0 else 0.0
    )
    consume_on_empty_rate = (
        consume_on_empty / consume_actions if consume_actions > 0 else 0.0
    )
    failed_movement_rate = (
        failed_movements / movement_actions if movement_actions > 0 else 0.0
    )
    revisit_rate = (
        1.0 - (len(move_destinations) / movement_actions)
        if movement_actions > 0 else 0.0
    )

    return EpisodeBehaviorMetrics(
        total_steps=total_steps,
        final_vitality=trace.final_vitality,
        died=trace.final_vitality <= 0.0,
        resource_gain_per_step=total_energy_gain / total_steps,
        net_energy_efficiency=(
            total_energy_gain / total_action_cost if total_action_cost > 0.0 else 0.0
        ),
        successful_consume_rate=successful_consume_rate,
        consume_on_empty_rate=consume_on_empty_rate,
        failed_movement_rate=failed_movement_rate,
        action_entropy=entropy,
        policy_sharpness=(
            sum(sharpness_values) / len(sharpness_values) if sharpness_values else 0.0
        ),
        action_inertia=inertia,
        unique_cells_visited=float(len(visited_cells)),
        coverage_efficiency=(
            len(visited_cells) / total_action_cost if total_action_cost > 0.0 else 0.0
        ),
        revisit_rate=revisit_rate,
    )


def aggregate_run_behavior_metrics(
    episode_metrics: Sequence[EpisodeBehaviorMetrics],
) -> StandardBehaviorMetrics:
    """Aggregate episode-level metrics into one standard run-level result."""
    n = len(episode_metrics)
    if n == 0:
        return StandardBehaviorMetrics(
            mean_steps=0.0,
            death_rate=0.0,
            mean_final_vitality=0.0,
            resource_gain_per_step=MetricSummaryStats(),
            net_energy_efficiency=MetricSummaryStats(),
            successful_consume_rate=MetricSummaryStats(),
            consume_on_empty_rate=MetricSummaryStats(),
            failed_movement_rate=MetricSummaryStats(),
            action_entropy=MetricSummaryStats(),
            policy_sharpness=MetricSummaryStats(),
            action_inertia=MetricSummaryStats(),
            unique_cells_visited=MetricSummaryStats(),
            coverage_efficiency=MetricSummaryStats(),
            revisit_rate=MetricSummaryStats(),
        )

    mean_steps = sum(m.total_steps for m in episode_metrics) / n
    mean_final_vitality = sum(m.final_vitality for m in episode_metrics) / n
    death_rate = sum(1 for m in episode_metrics if m.died) / n

    return StandardBehaviorMetrics(
        mean_steps=mean_steps,
        death_rate=death_rate,
        mean_final_vitality=mean_final_vitality,
        resource_gain_per_step=_metric_stats(
            [m.resource_gain_per_step for m in episode_metrics]
        ),
        net_energy_efficiency=_metric_stats(
            [m.net_energy_efficiency for m in episode_metrics]
        ),
        successful_consume_rate=_metric_stats(
            [m.successful_consume_rate for m in episode_metrics]
        ),
        consume_on_empty_rate=_metric_stats(
            [m.consume_on_empty_rate for m in episode_metrics]
        ),
        failed_movement_rate=_metric_stats(
            [m.failed_movement_rate for m in episode_metrics]
        ),
        action_entropy=_metric_stats([m.action_entropy for m in episode_metrics]),
        policy_sharpness=_metric_stats([m.policy_sharpness for m in episode_metrics]),
        action_inertia=_metric_stats([m.action_inertia for m in episode_metrics]),
        unique_cells_visited=_metric_stats(
            [m.unique_cells_visited for m in episode_metrics]
        ),
        coverage_efficiency=_metric_stats(
            [m.coverage_efficiency for m in episode_metrics]
        ),
        revisit_rate=_metric_stats([m.revisit_rate for m in episode_metrics]),
    )
