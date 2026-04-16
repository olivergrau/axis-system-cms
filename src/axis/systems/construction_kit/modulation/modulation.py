"""Action score modulation from prediction-derived traces."""

from __future__ import annotations

import math

from axis.systems.construction_kit.traces.state import (
    TraceState,
    get_confidence,
    get_frustration,
)


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
        Modulated action scores, same length as input.
    """
    result = []
    for score, action in zip(action_scores, actions):
        f = get_frustration(trace_state, context, action)
        c = get_confidence(trace_state, context, action)
        mu = compute_modulation(
            f, c,
            positive_sensitivity=positive_sensitivity,
            negative_sensitivity=negative_sensitivity,
            modulation_min=modulation_min,
            modulation_max=modulation_max,
        )
        if score >= 0.0:
            result.append(score * mu)
        else:
            result.append(score / mu)
    return tuple(result)
