"""Action score modulation from prediction-derived traces."""

from __future__ import annotations

import math
from dataclasses import dataclass

from axis.systems.construction_kit.traces.state import (
    TraceState,
    get_confidence,
    get_frustration,
)


@dataclass(frozen=True)
class PredictionModulationDetails:
    """Structured result for prediction-based action score adjustment."""

    final_scores: tuple[float, ...]
    modulation_factors: tuple[float, ...]
    prediction_biases: tuple[float, ...]
    frustrations: tuple[float, ...]
    confidences: tuple[float, ...]


def compute_modulation(
    frustration: float,
    confidence: float,
    *,
    positive_sensitivity: float,
    negative_sensitivity: float,
    modulation_min: float,
    modulation_max: float,
) -> float:
    """Compute action modulation factor from frustration and confidence.

    mu_tilde = exp(lambda_+ * c - lambda_- * f)
    mu = clip(mu_tilde, mu_min, mu_max)

    Args:
        frustration: f_t(s, a) for this context-action pair.
        confidence: c_t(s, a) for this context-action pair.
        positive_sensitivity: lambda_+ (>= 0).
        negative_sensitivity: lambda_- (>= 0).
        modulation_min: mu_min (> 0, <= 1).
        modulation_max: mu_max (>= 1).

    Returns:
        Modulation factor mu in [mu_min, mu_max].
    """
    exponent = positive_sensitivity * confidence - negative_sensitivity * frustration
    mu_tilde = math.exp(exponent)
    return max(modulation_min, min(modulation_max, mu_tilde))


def compute_prediction_bias(
    frustration: float,
    confidence: float,
    *,
    positive_sensitivity: float,
    negative_sensitivity: float,
    prediction_bias_clip: float,
) -> float:
    """Compute a bounded additive prediction correction.

    The bias uses the same signed evidence as multiplicative modulation,
    but compresses it into a small symmetric interval so prediction can
    gently reshape action preference without acting like a full drive.
    """
    signed_signal = (
        positive_sensitivity * confidence
        - negative_sensitivity * frustration
    )
    bounded = math.tanh(signed_signal)
    return max(-prediction_bias_clip, min(prediction_bias_clip, bounded))


def describe_action_modulation(
    action_scores: tuple[float, ...],
    context: int,
    actions: tuple[str, ...],
    trace_state: TraceState,
    *,
    positive_sensitivity: float,
    negative_sensitivity: float,
    modulation_min: float,
    modulation_max: float,
    modulation_mode: str = "multiplicative",
    prediction_bias_scale: float = 0.2,
    prediction_bias_clip: float = 1.0,
) -> PredictionModulationDetails:
    """Return the full prediction-based action adjustment details."""
    final_scores: list[float] = []
    modulation_factors: list[float] = []
    prediction_biases: list[float] = []
    frustrations: list[float] = []
    confidences: list[float] = []

    for score, action in zip(action_scores, actions):
        frustration = get_frustration(trace_state, context, action)
        confidence = get_confidence(trace_state, context, action)
        mu = compute_modulation(
            frustration,
            confidence,
            positive_sensitivity=positive_sensitivity,
            negative_sensitivity=negative_sensitivity,
            modulation_min=modulation_min,
            modulation_max=modulation_max,
        )
        delta = compute_prediction_bias(
            frustration,
            confidence,
            positive_sensitivity=positive_sensitivity,
            negative_sensitivity=negative_sensitivity,
            prediction_bias_clip=prediction_bias_clip,
        )
        additive_term = prediction_bias_scale * delta

        if modulation_mode == "additive":
            final_score = score + additive_term
        else:
            multiplicative_score = score * mu if score >= 0.0 else score / mu
            if modulation_mode == "hybrid":
                final_score = multiplicative_score + additive_term
            else:
                final_score = multiplicative_score

        final_scores.append(final_score)
        modulation_factors.append(mu)
        prediction_biases.append(additive_term)
        frustrations.append(frustration)
        confidences.append(confidence)

    return PredictionModulationDetails(
        final_scores=tuple(final_scores),
        modulation_factors=tuple(modulation_factors),
        prediction_biases=tuple(prediction_biases),
        frustrations=tuple(frustrations),
        confidences=tuple(confidences),
    )


def modulate_action_scores(
    action_scores: tuple[float, ...],
    context: int,
    actions: tuple[str, ...],
    trace_state: TraceState,
    *,
    positive_sensitivity: float,
    negative_sensitivity: float,
    modulation_min: float,
    modulation_max: float,
    modulation_mode: str = "multiplicative",
    prediction_bias_scale: float = 0.2,
    prediction_bias_clip: float = 1.0,
) -> tuple[float, ...]:
    """Apply prediction-based modulation to all action scores.

    For each action a, modulation changes action preference while
    preserving sign semantics:

    - if base_score >= 0: modulated_score = base_score * mu
    - if base_score < 0:  modulated_score = base_score / mu

    This ensures that positive surprise strengthens action preference
    and negative surprise weakens it, even for actions represented by
    negative baseline penalties (e.g. stay suppression).

    Args:
        action_scores: Baseline scores from the drive, one per action.
        context: Current context index s_t.
        actions: Action names in the same order as action_scores.
        trace_state: Current trace state z_t.
        positive_sensitivity: lambda_+.
        negative_sensitivity: lambda_-.
        modulation_min: mu_min.
        modulation_max: mu_max.

    Returns:
        Final action scores, same length as input.
    """
    return describe_action_modulation(
        action_scores,
        context,
        actions,
        trace_state,
        positive_sensitivity=positive_sensitivity,
        negative_sensitivity=negative_sensitivity,
        modulation_min=modulation_min,
        modulation_max=modulation_max,
        modulation_mode=modulation_mode,
        prediction_bias_scale=prediction_bias_scale,
        prediction_bias_clip=prediction_bias_clip,
    ).final_scores
