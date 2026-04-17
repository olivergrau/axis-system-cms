"""System C prediction-specific comparison extension (WP-10).

This module is imported as a side effect from ``system_c.register()``
so that the extension is available whenever the system_c plugin is loaded.
"""

from __future__ import annotations

from typing import Any

from axis.framework.comparison.alignment import iter_aligned_steps
from axis.framework.comparison.extensions import register_extension
from axis.framework.comparison.types import (
    AlignmentSummary,
    RANKING_EPSILON,
)
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace


def _get_decision_data(step: BaseStepTrace) -> dict[str, Any] | None:
    sd = step.system_data
    if not sd:
        return None
    # Persisted traces nest under "decision_data"; in-memory may be flat.
    dd = sd.get("decision_data", sd)
    return dd


def _get_prediction_data(step: BaseStepTrace) -> dict[str, Any] | None:
    dd = _get_decision_data(step)
    if not dd:
        return None
    return dd.get("prediction")


def _get_drive_data(step: BaseStepTrace) -> dict[str, Any] | None:
    dd = _get_decision_data(step)
    if not dd:
        return None
    return dd.get("drive")


def _to_list(val: Any) -> list[float]:
    """Normalize scores to a list of floats (handles both dict and list)."""
    if isinstance(val, dict):
        return list(val.values())
    if isinstance(val, (list, tuple)):
        return list(val)
    return []


def _top_index_changed(raw: list[float], mod: list[float]) -> bool | None:
    """Check if modulation changed the top-ranked index.

    Returns None when a tie makes the answer ambiguous.
    """
    if not raw or not mod or len(raw) != len(mod):
        return None
    raw_top = max(range(len(raw)), key=lambda i: raw[i])
    mod_top = max(range(len(mod)), key=lambda i: mod[i])
    if raw_top == mod_top:
        return False
    mod_sorted = sorted(mod, reverse=True)
    if len(mod_sorted) > 1 and abs(mod_sorted[0] - mod_sorted[1]) <= RANKING_EPSILON:
        return None  # ambiguous
    return True


@register_extension("system_c")
def system_c_prediction_analysis(
    reference: BaseEpisodeTrace,
    candidate: BaseEpisodeTrace,
    alignment: AlignmentSummary,
) -> dict[str, Any]:
    prediction_active_count = 0
    top_action_changed_count = 0
    modulation_deltas: list[float] = []
    total_aligned = alignment.aligned_steps
    ambiguous_count = 0

    for ref_step, cand_step in iter_aligned_steps(reference, candidate):
        pred = _get_prediction_data(cand_step)
        drive = _get_drive_data(cand_step)
        if pred is None or drive is None:
            continue

        raw_list = _to_list(drive.get("action_contributions", []))
        mod_list = _to_list(pred.get("modulated_scores", []))

        if not raw_list or not mod_list:
            continue

        n = min(len(raw_list), len(mod_list))

        # Prediction is active if any modulated score differs from raw
        is_active = any(
            abs(mod_list[i] - raw_list[i]) > RANKING_EPSILON
            for i in range(n)
        )
        if is_active:
            prediction_active_count += 1

        changed = _top_index_changed(raw_list[:n], mod_list[:n])
        if changed is True:
            top_action_changed_count += 1
        elif changed is None:
            ambiguous_count += 1

        # Mean modulation delta across actions for this step
        step_delta = sum(abs(mod_list[i] - raw_list[i]) for i in range(n)) / n
        modulation_deltas.append(step_delta)

    return {
        "system_c_prediction": {
            "prediction_active_step_count": prediction_active_count,
            "prediction_active_step_rate": (
                prediction_active_count / total_aligned if total_aligned > 0 else 0.0
            ),
            "top_action_changed_by_modulation_count": top_action_changed_count,
            "top_action_changed_by_modulation_rate": (
                top_action_changed_count / total_aligned if total_aligned > 0 else 0.0
            ),
            "ambiguous_top_action_count": ambiguous_count,
            "mean_modulation_delta": (
                sum(modulation_deltas) / len(modulation_deltas)
                if modulation_deltas else 0.0
            ),
        },
    }
