"""System C behavioral metric extension."""

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


def _prediction_decision(step: BaseStepTrace) -> dict[str, Any]:
    return _decision_data(step).get("prediction", {}) or {}


def _prediction_trace(step: BaseStepTrace) -> dict[str, Any]:
    return _trace_data(step).get("prediction", {}) or {}


def _to_float_list(value: Any) -> list[float]:
    if isinstance(value, dict):
        return [float(v) for v in value.values()]
    if isinstance(value, (list, tuple)):
        return [float(v) for v in value]
    return []


@register_metric_extension("system_c")
def system_c_behavior_metrics(
    episode_traces: tuple[BaseEpisodeTrace, ...],
    standard_metrics: StandardBehaviorMetrics,
) -> dict[str, Any]:
    del standard_metrics

    absolute_errors: list[float] = []
    signed_errors: list[float] = []
    confidence_values: list[float] = []
    frustration_values: list[float] = []
    modulation_strengths: list[float] = []
    prediction_steps = 0

    for trace in episode_traces:
        for step in trace.steps:
            pred_decision = _prediction_decision(step)
            pred_trace = _prediction_trace(step)
            if not pred_decision and not pred_trace:
                continue

            error_positive = float(pred_trace.get("error_positive", 0.0))
            error_negative = float(pred_trace.get("error_negative", 0.0))
            absolute_errors.append(error_positive + error_negative)
            signed_errors.append(error_positive - error_negative)

            if "confidence_value" in pred_trace:
                confidence_values.append(float(pred_trace.get("confidence_value", 0.0)))
            if "frustration_value" in pred_trace:
                frustration_values.append(float(pred_trace.get("frustration_value", 0.0)))

            decision = _decision_data(step)
            drive = decision.get("drive", {}) or {}
            raw = _to_float_list(drive.get("action_contributions", ()))
            modulated = _to_float_list(pred_decision.get("modulated_scores", ()))
            n = min(len(raw), len(modulated))
            if n > 0:
                prediction_steps += 1
                modulation_strengths.append(
                    sum(abs(modulated[i] - raw[i]) for i in range(n)) / n
                )

    def _mean(values: list[float]) -> float | None:
        if not values:
            return None
        return sum(values) / len(values)

    return {
        "system_c_prediction": {
            "mean_prediction_error": _mean(absolute_errors),
            "signed_prediction_error": _mean(signed_errors),
            "confidence_trace_mean": _mean(confidence_values),
            "frustration_trace_mean": _mean(frustration_values),
            "prediction_modulation_strength": _mean(modulation_strengths),
            "prediction_step_count": prediction_steps,
        },
    }
