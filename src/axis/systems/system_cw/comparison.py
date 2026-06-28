"""System C+W comparison extension."""

from __future__ import annotations

from typing import Any

from axis.framework.comparison.alignment import iter_aligned_steps
from axis.framework.comparison.extensions import register_extension
from axis.framework.comparison.types import AlignmentSummary, RANKING_EPSILON
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace


def _decision_data(step: BaseStepTrace) -> dict[str, Any]:
    system_data = step.system_data or {}
    data = system_data.get("decision_data", system_data)
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


def _mean_sequence(value: Any) -> float | None:
    floats = _to_float_list(value)
    if not floats:
        return None
    return sum(floats) / len(floats)


def _top_index(scores: list[float]) -> int | None:
    if not scores:
        return None
    return max(range(len(scores)), key=scores.__getitem__)


def _top_ambiguous(scores: list[float]) -> bool:
    if len(scores) < 2:
        return False
    ordered = sorted(scores, reverse=True)
    return abs(ordered[0] - ordered[1]) <= RANKING_EPSILON


def _top_change_state(raw_scores: list[float], final_scores: list[float]) -> bool | None:
    if not raw_scores or not final_scores:
        return None
    n = min(len(raw_scores), len(final_scores))
    raw = raw_scores[:n]
    final = final_scores[:n]
    if _top_ambiguous(raw) or _top_ambiguous(final):
        return None
    raw_top = _top_index(raw)
    final_top = _top_index(final)
    if raw_top is None or final_top is None:
        return None
    return raw_top != final_top


def _prediction_signature_system_c(step: BaseStepTrace) -> dict[str, float | bool | None] | None:
    decision = _decision_data(step)
    prediction = decision.get("prediction", {}) or {}
    drive = decision.get("drive", {}) or {}
    raw_scores = _to_float_list(drive.get("action_contributions", ()))
    final_scores = _to_float_list(prediction.get("modulated_scores", ()))
    if not raw_scores or not final_scores:
        return None
    n = min(len(raw_scores), len(final_scores))
    raw = raw_scores[:n]
    final = final_scores[:n]
    mean_delta = sum(abs(final[i] - raw[i]) for i in range(n)) / n
    active = any(abs(final[i] - raw[i]) > RANKING_EPSILON for i in range(n))
    top_changed = _top_change_state(raw, final)
    return {
        "prediction_active": active,
        "top_action_changed": top_changed,
        "mean_modulation_delta": mean_delta,
    }


def _prediction_signature_system_cw(step: BaseStepTrace) -> dict[str, float | bool | None] | None:
    decision = _decision_data(step)
    prediction = decision.get("prediction", {}) or {}
    final_scores = _to_float_list(decision.get("combined_scores", ()))
    counterfactual_scores = _to_float_list(
        prediction.get("counterfactual_combined_scores", ()),
    )
    if not final_scores or not counterfactual_scores:
        return None
    n = min(len(final_scores), len(counterfactual_scores))
    final = final_scores[:n]
    counterfactual = counterfactual_scores[:n]
    mean_delta = sum(abs(final[i] - counterfactual[i]) for i in range(n)) / n
    active = any(
        abs(final[i] - counterfactual[i]) > RANKING_EPSILON
        for i in range(n)
    )
    top_changed = _top_change_state(counterfactual, final)
    return {
        "prediction_active": active,
        "top_action_changed": top_changed,
        "mean_modulation_delta": mean_delta,
    }


def _prediction_signature(step: BaseStepTrace, system_type: str) -> dict[str, float | bool | None] | None:
    if system_type == "system_c":
        return _prediction_signature_system_c(step)
    if system_type == "system_cw":
        return _prediction_signature_system_cw(step)
    return None


def _shared_aw_signature(step: BaseStepTrace) -> dict[str, float] | None:
    decision = _decision_data(step)
    trace = _trace_data(step)
    arbitration = decision.get("arbitration", {}) or {}
    curiosity = decision.get("curiosity_drive", {}) or {}
    if not isinstance(arbitration, dict) or not isinstance(curiosity, dict):
        return None
    composite_novelty = _mean_sequence(curiosity.get("composite_novelty", ()))
    if composite_novelty is None:
        return None
    return {
        "hunger_weight": float(arbitration.get("hunger_weight", 0.0)),
        "curiosity_weight": float(arbitration.get("curiosity_weight", 0.0)),
        "curiosity_activation": float(curiosity.get("activation", 0.0)),
        "composite_novelty": composite_novelty,
        "visit_count_at_current": float(trace.get("visit_count_at_current", 0.0)),
    }


def _cw_full_signature(step: BaseStepTrace) -> dict[str, float] | None:
    trace = _trace_data(step)
    prediction = trace.get("prediction", {}) or {}
    hunger = prediction.get("hunger", {}) or {}
    curiosity = prediction.get("curiosity", {}) or {}
    if not isinstance(prediction, dict) or not isinstance(hunger, dict) or not isinstance(curiosity, dict):
        return None
    pred_sig = _prediction_signature_system_cw(step)
    return {
        "feature_prediction_error": float(prediction.get("feature_error_positive", 0.0))
        + float(prediction.get("feature_error_negative", 0.0)),
        "hunger_prediction_error": float(hunger.get("error_positive", 0.0))
        + float(hunger.get("error_negative", 0.0)),
        "curiosity_prediction_error": float(curiosity.get("error_positive", 0.0))
        + float(curiosity.get("error_negative", 0.0)),
        "hunger_trace_balance": float(hunger.get("confidence_value", 0.0))
        - float(hunger.get("frustration_value", 0.0)),
        "curiosity_trace_balance": float(curiosity.get("confidence_value", 0.0))
        - float(curiosity.get("frustration_value", 0.0)),
        "behavioral_prediction_impact": 1.0
        if pred_sig and pred_sig.get("top_action_changed") is True
        else 0.0,
        "nonmove_curiosity_penalty": 1.0
        if bool(curiosity.get("used_nonmove_penalty_rule", False))
        else 0.0,
    }


def _collect_cw_analysis(
    reference: BaseEpisodeTrace,
    candidate: BaseEpisodeTrace,
) -> dict[str, Any] | None:
    ref_type = reference.system_type
    cand_type = candidate.system_type

    collect_shared = ref_type in {"system_aw", "system_cw"}
    collect_prediction = ref_type in {"system_c", "system_cw"}
    collect_full = ref_type == "system_cw"

    reference_active: list[float] = []
    candidate_active: list[float] = []
    reference_top_changed: list[float] = []
    candidate_top_changed: list[float] = []
    reference_delta: list[float] = []
    candidate_delta: list[float] = []

    hunger_weight_deltas: list[float] = []
    curiosity_weight_deltas: list[float] = []
    curiosity_activation_deltas: list[float] = []
    composite_novelty_deltas: list[float] = []
    visit_count_deltas: list[float] = []

    feature_error_deltas: list[float] = []
    hunger_error_deltas: list[float] = []
    curiosity_error_deltas: list[float] = []
    hunger_trace_balance_deltas: list[float] = []
    curiosity_trace_balance_deltas: list[float] = []
    behavioral_impact_deltas: list[float] = []
    nonmove_penalty_deltas: list[float] = []

    for ref_step, cand_step in iter_aligned_steps(reference, candidate):
        if collect_prediction:
            ref_pred = _prediction_signature(ref_step, ref_type)
            cand_pred = _prediction_signature(cand_step, cand_type)
            if ref_pred is not None and cand_pred is not None:
                reference_active.append(1.0 if ref_pred["prediction_active"] else 0.0)
                candidate_active.append(1.0 if cand_pred["prediction_active"] else 0.0)
                reference_delta.append(float(ref_pred["mean_modulation_delta"] or 0.0))
                candidate_delta.append(float(cand_pred["mean_modulation_delta"] or 0.0))

                ref_top = ref_pred["top_action_changed"]
                cand_top = cand_pred["top_action_changed"]
                if ref_top is not None and cand_top is not None:
                    reference_top_changed.append(1.0 if ref_top else 0.0)
                    candidate_top_changed.append(1.0 if cand_top else 0.0)

        if collect_shared:
            ref_shared = _shared_aw_signature(ref_step)
            cand_shared = _shared_aw_signature(cand_step)
            if ref_shared is not None and cand_shared is not None:
                hunger_weight_deltas.append(
                    cand_shared["hunger_weight"] - ref_shared["hunger_weight"],
                )
                curiosity_weight_deltas.append(
                    cand_shared["curiosity_weight"] - ref_shared["curiosity_weight"],
                )
                curiosity_activation_deltas.append(
                    cand_shared["curiosity_activation"] - ref_shared["curiosity_activation"],
                )
                composite_novelty_deltas.append(
                    cand_shared["composite_novelty"] - ref_shared["composite_novelty"],
                )
                visit_count_deltas.append(
                    cand_shared["visit_count_at_current"] - ref_shared["visit_count_at_current"],
                )

        if collect_full:
            ref_full = _cw_full_signature(ref_step)
            cand_full = _cw_full_signature(cand_step)
            if ref_full is not None and cand_full is not None:
                feature_error_deltas.append(
                    cand_full["feature_prediction_error"] - ref_full["feature_prediction_error"],
                )
                hunger_error_deltas.append(
                    cand_full["hunger_prediction_error"] - ref_full["hunger_prediction_error"],
                )
                curiosity_error_deltas.append(
                    cand_full["curiosity_prediction_error"] - ref_full["curiosity_prediction_error"],
                )
                hunger_trace_balance_deltas.append(
                    cand_full["hunger_trace_balance"] - ref_full["hunger_trace_balance"],
                )
                curiosity_trace_balance_deltas.append(
                    cand_full["curiosity_trace_balance"] - ref_full["curiosity_trace_balance"],
                )
                behavioral_impact_deltas.append(
                    cand_full["behavioral_prediction_impact"] - ref_full["behavioral_prediction_impact"],
                )
                nonmove_penalty_deltas.append(
                    cand_full["nonmove_curiosity_penalty"] - ref_full["nonmove_curiosity_penalty"],
                )

    analysis: dict[str, Any] = {}

    if collect_shared:
        if not hunger_weight_deltas:
            return None
        analysis.update(
            {
                "mean_hunger_weight_delta": _mean(hunger_weight_deltas),
                "mean_curiosity_weight_delta": _mean(curiosity_weight_deltas),
                "mean_curiosity_activation_delta": _mean(curiosity_activation_deltas),
                "mean_composite_novelty_delta": _mean(composite_novelty_deltas),
                "mean_visit_count_delta": _mean(visit_count_deltas),
            }
        )

    if collect_prediction:
        if not reference_active or not candidate_active:
            return None
        ref_active_rate = _mean(reference_active)
        cand_active_rate = _mean(candidate_active)
        ref_top_rate = _mean(reference_top_changed)
        cand_top_rate = _mean(candidate_top_changed)
        ref_mod_delta = _mean(reference_delta)
        cand_mod_delta = _mean(candidate_delta)
        analysis.update(
            {
                "reference_prediction_active_step_rate": ref_active_rate,
                "candidate_prediction_active_step_rate": cand_active_rate,
                "prediction_active_step_rate_delta": (
                    cand_active_rate - ref_active_rate
                    if ref_active_rate is not None and cand_active_rate is not None
                    else None
                ),
                "reference_top_action_changed_rate": ref_top_rate,
                "candidate_top_action_changed_rate": cand_top_rate,
                "top_action_changed_rate_delta": (
                    cand_top_rate - ref_top_rate
                    if ref_top_rate is not None and cand_top_rate is not None
                    else None
                ),
                "reference_mean_prediction_modulation_delta": ref_mod_delta,
                "candidate_mean_prediction_modulation_delta": cand_mod_delta,
                "prediction_modulation_delta_shift": (
                    cand_mod_delta - ref_mod_delta
                    if ref_mod_delta is not None and cand_mod_delta is not None
                    else None
                ),
            }
        )

    if collect_full:
        if not feature_error_deltas:
            return None
        analysis.update(
            {
                "mean_feature_prediction_error_delta": _mean(feature_error_deltas),
                "mean_hunger_prediction_error_delta": _mean(hunger_error_deltas),
                "mean_curiosity_prediction_error_delta": _mean(curiosity_error_deltas),
                "mean_hunger_trace_balance_delta": _mean(hunger_trace_balance_deltas),
                "mean_curiosity_trace_balance_delta": _mean(curiosity_trace_balance_deltas),
                "behavioral_prediction_impact_rate_delta": _mean(behavioral_impact_deltas),
                "nonmove_curiosity_penalty_rate_delta": _mean(nonmove_penalty_deltas),
            }
        )

    return analysis or None


@register_extension("system_cw")
def system_cw_comparison_analysis(
    reference: BaseEpisodeTrace,
    candidate: BaseEpisodeTrace,
    alignment: AlignmentSummary,
) -> dict[str, Any] | None:
    ref_type = reference.system_type
    cand_type = candidate.system_type

    analysis: dict[str, Any] = {
        "reference_system_type": ref_type,
        "candidate_system_type": cand_type,
        "aligned_steps": alignment.aligned_steps,
    }

    if ref_type == "system_cw":
        analysis["comparison_scope"] = "cw_full"
        combined = _collect_cw_analysis(reference, candidate)
        if combined is None:
            return None
        analysis.update(combined)
    elif ref_type == "system_aw":
        analysis["comparison_scope"] = "aw_cw_intersection"
        combined = _collect_cw_analysis(reference, candidate)
        if combined is None:
            return None
        analysis.update(combined)
    elif ref_type == "system_c":
        analysis["comparison_scope"] = "c_cw_prediction_intersection"
        combined = _collect_cw_analysis(reference, candidate)
        if combined is None:
            return None
        analysis.update(combined)
    else:
        return None

    return {"system_cw_comparison": analysis}
