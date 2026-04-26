"""System C+W visualization adapter."""

from __future__ import annotations

from typing import Any

from axis.sdk.actions import MOVEMENT_DELTAS
from axis.sdk.trace import BaseStepTrace
from axis.visualization.registry import register_system_visualization
from axis.visualization.types import (
    AnalysisRow,
    AnalysisSection,
    OverlayData,
    OverlayItem,
    OverlayTypeDeclaration,
)

ACTION_NAMES: tuple[str, ...] = ("up", "down", "left", "right", "consume", "stay")
DIRECTION_ACTIONS: tuple[str, ...] = ("up", "down", "left", "right")


def _fmt(value: Any, digits: int = 4) -> str:
    """Format numeric values defensively for text panels."""
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _score_bar_data(*value_groups: tuple[float, ...] | list[float]) -> tuple[list[list[float]], float]:
    """Shift score groups onto a shared relative-width scale."""
    groups = [list(values) for values in value_groups]
    flat = [value for group in groups for value in group]
    if not flat:
        return [[] for _ in groups], 1.0
    minimum = min(flat)
    shifted = [[value - minimum for value in group] for group in groups]
    max_value = max((value for group in shifted for value in group), default=0.0) or 1.0
    return shifted, max_value


def _action_dict(values: Any) -> dict[str, float]:
    """Coerce an action-keyed mapping or sequence into a normalized dict."""
    if isinstance(values, dict):
        return {action: float(values.get(action, 0.0)) for action in ACTION_NAMES}
    seq = list(values or ())
    return {
        action: float(seq[index]) if index < len(seq) else 0.0
        for index, action in enumerate(ACTION_NAMES)
    }


def _join_action_values(values: dict[str, float], *, digits: int = 3) -> str:
    """Render action-value maps in stable action order."""
    return ", ".join(f"{action}:{values[action]:.{digits}f}" for action in ACTION_NAMES)


def _relative_neighbor(action: str, agent_pos: tuple[int, int]) -> tuple[int, int]:
    """Return neighbor grid position for a movement action."""
    dx, dy = MOVEMENT_DELTAS[action]
    return (agent_pos[0] + dx, agent_pos[1] + dy)


class SystemCWVisualizationAdapter:
    """Visualization adapter for System C+W."""

    def __init__(self, max_energy: float) -> None:
        self._max_energy = max_energy

    def phase_names(self) -> list[str]:
        return ["BEFORE", "AFTER_REGEN", "AFTER_ACTION"]

    def vitality_label(self) -> str:
        return "Energy"

    def format_vitality(self, value: float, system_data: dict[str, Any]) -> str:
        del system_data
        energy = value * self._max_energy
        return f"{energy:.2f} / {self._max_energy:.2f}"

    def build_step_analysis(self, step_trace: BaseStepTrace) -> list[AnalysisSection]:
        dd = step_trace.system_data.get("decision_data", {})
        td = step_trace.system_data.get("trace_data", {})
        sections = [
            self._section_step_overview(step_trace, dd, td),
            self._section_observation(dd),
            self._section_curiosity_world_context(dd, td),
            self._section_raw_drive_outputs(dd),
            self._section_arbitration(dd),
            self._section_shared_prediction(dd),
            self._section_hunger_modulation(dd),
            self._section_curiosity_modulation(dd),
            self._section_decision_pipeline(dd),
        ]
        if td.get("prediction"):
            sections.extend([
                self._section_predictive_update(td),
                self._section_drive_specific_traces(td),
            ])
        sections.append(self._section_outcome(step_trace, td))
        return sections

    def build_overlays(self, step_trace: BaseStepTrace) -> list[OverlayData]:
        dd = step_trace.system_data.get("decision_data", {})
        td = step_trace.system_data.get("trace_data", {})
        before = (step_trace.agent_position_before.x, step_trace.agent_position_before.y)
        after = (step_trace.agent_position_after.x, step_trace.agent_position_after.y)
        return [
            self._overlay_action_preference(dd, before),
            self._overlay_visit_count_heatmap(td),
            self._overlay_novelty_field(dd, before),
            self._overlay_modulation_factor(dd, before),
            self._overlay_dual_modulation_split(dd, before),
            self._overlay_consumption_opportunity(dd, before),
        ]

    def available_overlay_types(self) -> list[OverlayTypeDeclaration]:
        return [
            OverlayTypeDeclaration(
                key="action_preference",
                label="Action Preference",
                description="Arrows showing policy preferences, plus consume/stay markers.",
                legend_html=(
                    "<span style='color:#FFC800'>→</span>=selected "
                    "<span style='color:#C8C8C8'>→</span>=candidate "
                    "<span style='color:#FFC800'>●</span>=consume "
                    "<span style='color:#C8C8C8'>○</span>=stay"
                ),
            ),
            OverlayTypeDeclaration(
                key="visit_count_heatmap",
                label="Visit Count Map",
                description="Heatmap of the minimal world model visit counts.",
                legend_html="cold=few visits warm=many visits",
            ),
            OverlayTypeDeclaration(
                key="novelty_field",
                label="Novelty Field",
                description="Per-direction composite novelty around the agent.",
                legend_html="arrow length=composite novelty, X=blocked",
            ),
            OverlayTypeDeclaration(
                key="modulation_factor",
                label="Effective Movement Modulation",
                description="Weighted net prediction effect on each movement direction.",
                legend_html=(
                    "<span style='color:#32DC50'>■</span>=reinforced "
                    "<span style='color:#DC3232'>■</span>=suppressed"
                ),
            ),
            OverlayTypeDeclaration(
                key="dual_modulation_split",
                label="Dual Modulation Split",
                description="Per-action split of hunger-side and curiosity-side predictive modulation.",
                legend_html=(
                    "<span style='color:#64B4FF'>■</span>=hunger-side "
                    "<span style='color:#64FF64'>■</span>=curiosity-side "
                    "alpha=reinforce vs suppress"
                ),
            ),
            OverlayTypeDeclaration(
                key="consumption_opportunity",
                label="Consumption Opportunity",
                description="Current-cell resource and blocked neighbors.",
                legend_html=(
                    "<span style='color:#FFDC00'>◆</span>=resource "
                    "<span style='color:#FF5050'>✕</span>=blocked"
                ),
            ),
        ]

    def build_system_widget_data(self, step_trace: BaseStepTrace) -> dict[str, Any] | None:
        """Build structured data for the generalized prediction summary widget."""
        dd = step_trace.system_data.get("decision_data", {})
        td = step_trace.system_data.get("trace_data", {})
        prediction = dd.get("prediction", {}) or {}
        prediction_trace = td.get("prediction", {}) or {}

        hunger_mod = prediction.get("hunger_modulation", {}) or {}
        curiosity_mod = prediction.get("curiosity_modulation", {}) or {}
        hunger_trace = prediction_trace.get("hunger", {}) or {}
        curiosity_trace = prediction_trace.get("curiosity", {}) or {}

        return {
            "widget_mode": "dual_prediction",
            "context": int(prediction.get("context", 0) or 0),
            "features": tuple(prediction.get("features", ()) or ()),
            "selected_action": ((dd.get("policy", {}) or {}).get("selected_action", "")),
            "counterfactual_top_action": prediction.get("counterfactual_top_action", ""),
            "hunger": {
                "modulation_factors": _action_dict(hunger_mod.get("reliability_factors", {})),
                "prediction_biases": _action_dict(hunger_mod.get("prediction_biases", {})),
                "final_scores": _action_dict(hunger_mod.get("final_scores", {})),
                "confidences": _action_dict(
                    prediction_trace.get("hunger_confidence_by_action", {})
                    or hunger_mod.get("confidence_by_action", {})
                ),
                "frustrations": _action_dict(
                    prediction_trace.get("hunger_frustration_by_action", {})
                    or hunger_mod.get("frustration_by_action", {})
                ),
                "error_positive": float(hunger_trace.get("error_positive", 0.0)),
                "error_negative": float(hunger_trace.get("error_negative", 0.0)),
                "actual": float(hunger_trace.get("actual", 0.0)),
                "predicted": float(hunger_trace.get("predicted", 0.0)),
            },
            "curiosity": {
                "modulation_factors": _action_dict(curiosity_mod.get("reliability_factors", {})),
                "prediction_biases": _action_dict(curiosity_mod.get("prediction_biases", {})),
                "final_scores": _action_dict(curiosity_mod.get("final_scores", {})),
                "confidences": _action_dict(
                    prediction_trace.get("curiosity_confidence_by_action", {})
                    or curiosity_mod.get("confidence_by_action", {})
                ),
                "frustrations": _action_dict(
                    prediction_trace.get("curiosity_frustration_by_action", {})
                    or curiosity_mod.get("frustration_by_action", {})
                ),
                "error_positive": float(curiosity_trace.get("error_positive", 0.0)),
                "error_negative": float(curiosity_trace.get("error_negative", 0.0)),
                "actual": float(curiosity_trace.get("actual", 0.0)),
                "predicted": float(curiosity_trace.get("predicted", 0.0)),
                "novelty_weight": float(curiosity_trace.get("novelty_weight", 0.0)),
                "used_nonmove_penalty_rule": bool(curiosity_trace.get("used_nonmove_penalty_rule", False)),
            },
        }

    def _section_step_overview(
        self,
        step_trace: BaseStepTrace,
        decision_data: dict[str, Any],
        trace_data: dict[str, Any],
    ) -> AnalysisSection:
        prediction = decision_data.get("prediction", {}) or {}
        policy = decision_data.get("policy", {}) or {}
        rel_pos = trace_data.get("relative_position", (0, 0))
        return AnalysisSection(
            title="Step Overview",
            rows=(
                AnalysisRow(label="Timestep", value=str(step_trace.timestep)),
                AnalysisRow(label="Action", value=step_trace.action),
                AnalysisRow(label="Energy Before", value=_fmt(trace_data.get("energy_before", 0.0), 2)),
                AnalysisRow(label="Energy After", value=_fmt(trace_data.get("energy_after", 0.0), 2)),
                AnalysisRow(label="Energy Delta", value=f"{float(trace_data.get('energy_delta', 0.0)):+.2f}"),
                AnalysisRow(label="Relative Position", value=f"({rel_pos[0]}, {rel_pos[1]})"),
                AnalysisRow(label="Visit Count", value=str(trace_data.get("visit_count_at_current", 0))),
                AnalysisRow(label="Context", value=f"{int(prediction.get('context', 0) or 0)}"),
                AnalysisRow(label="Selected Action", value=str(policy.get("selected_action", ""))),
                AnalysisRow(label="Counterfactual Winner", value=str(prediction.get("counterfactual_top_action", ""))),
            ),
        )

    def _section_observation(self, decision_data: dict[str, Any]) -> AnalysisSection:
        observation = decision_data.get("observation", {}) or {}
        rows: list[AnalysisRow] = [
            AnalysisRow(
                label="Current",
                value=(
                    f"resource={float(((observation.get('current', {}) or {}).get('resource', 0.0))):.3f}, "
                    f"trav={float(((observation.get('current', {}) or {}).get('traversability', 0.0))):.1f}"
                ),
            ),
        ]
        for direction in DIRECTION_ACTIONS:
            data = observation.get(direction, {}) or {}
            traversable = "traversable" if float(data.get("traversability", 0.0)) > 0 else "blocked"
            rows.append(
                AnalysisRow(
                    label=direction.capitalize(),
                    value=f"resource={float(data.get('resource', 0.0)):.3f}, {traversable}",
                ),
            )
        return AnalysisSection(title="Observation", rows=tuple(rows))

    def _section_curiosity_world_context(
        self,
        decision_data: dict[str, Any],
        trace_data: dict[str, Any],
    ) -> AnalysisSection:
        curiosity = decision_data.get("curiosity_drive", {}) or {}
        return AnalysisSection(
            title="Curiosity & World Context",
            rows=(
                AnalysisRow(
                    label="Spatial Novelty",
                    value=", ".join(_fmt(value, 3) for value in (curiosity.get("spatial_novelty", ()) or ())),
                ),
                AnalysisRow(
                    label="Sensory Novelty",
                    value=", ".join(_fmt(value, 3) for value in (curiosity.get("sensory_novelty", ()) or ())),
                ),
                AnalysisRow(
                    label="Composite Novelty",
                    value=", ".join(_fmt(value, 3) for value in (curiosity.get("composite_novelty", ()) or ())),
                ),
                AnalysisRow(label="Visit Count", value=str(trace_data.get("visit_count_at_current", 0))),
                AnalysisRow(label="Known Cells", value=str(len(trace_data.get("visit_counts_map", ()) or ()))),
            ),
        )

    def _section_raw_drive_outputs(self, decision_data: dict[str, Any]) -> AnalysisSection:
        hunger = decision_data.get("hunger_drive", {}) or {}
        curiosity = decision_data.get("curiosity_drive", {}) or {}
        hunger_scores = list(hunger.get("action_contributions", ()) or ())
        curiosity_scores = list(curiosity.get("action_contributions", ()) or ())
        rows: list[AnalysisRow] = [
            AnalysisRow(
                label="Hunger Activation",
                value=_fmt(hunger.get("activation", 0.0)),
                sub_rows=tuple(
                    AnalysisRow(
                        label=action.capitalize(),
                        value=_fmt(hunger_scores[index] if index < len(hunger_scores) else 0.0),
                    )
                    for index, action in enumerate(ACTION_NAMES)
                ),
            ),
            AnalysisRow(
                label="Curiosity Activation",
                value=_fmt(curiosity.get("activation", 0.0)),
                sub_rows=tuple(
                    AnalysisRow(
                        label=action.capitalize(),
                        value=_fmt(curiosity_scores[index] if index < len(curiosity_scores) else 0.0),
                    )
                    for index, action in enumerate(ACTION_NAMES)
                ),
            ),
        ]
        return AnalysisSection(title="Raw Drive Outputs", rows=tuple(rows))

    def _section_arbitration(self, decision_data: dict[str, Any]) -> AnalysisSection:
        arbitration = decision_data.get("arbitration", {}) or {}
        hunger_weight = float(arbitration.get("hunger_weight", 0.0))
        curiosity_weight = float(arbitration.get("curiosity_weight", 0.0))
        if hunger_weight > curiosity_weight:
            dominant = "hunger"
        elif curiosity_weight > hunger_weight:
            dominant = "curiosity"
        else:
            dominant = "tie"
        return AnalysisSection(
            title="Arbitration",
            rows=(
                AnalysisRow(label="Hunger Weight", value=_fmt(hunger_weight)),
                AnalysisRow(label="Curiosity Weight", value=_fmt(curiosity_weight)),
                AnalysisRow(label="Dominant Drive", value=dominant),
            ),
        )

    def _section_shared_prediction(self, decision_data: dict[str, Any]) -> AnalysisSection:
        prediction = decision_data.get("prediction", {}) or {}
        features = tuple(prediction.get("features", ()) or ())
        return AnalysisSection(
            title="Shared Predictive Representation",
            rows=(
                AnalysisRow(
                    label="Context",
                    value=f"{int(prediction.get('context', 0) or 0)} (0b{int(prediction.get('context', 0) or 0):05b})",
                ),
                AnalysisRow(
                    label="Features",
                    value=", ".join(_fmt(value, 3) for value in features),
                ),
                AnalysisRow(
                    label="Feature Count",
                    value=str(len(features)),
                ),
            ),
        )

    def _section_hunger_modulation(self, decision_data: dict[str, Any]) -> AnalysisSection:
        modulation = (decision_data.get("prediction", {}) or {}).get("hunger_modulation", {}) or {}
        return AnalysisSection(
            title="Hunger-side Predictive Modulation",
            rows=self._modulation_rows(modulation),
        )

    def _section_curiosity_modulation(self, decision_data: dict[str, Any]) -> AnalysisSection:
        modulation = (decision_data.get("prediction", {}) or {}).get("curiosity_modulation", {}) or {}
        return AnalysisSection(
            title="Curiosity-side Predictive Modulation",
            rows=self._modulation_rows(modulation),
        )

    def _section_decision_pipeline(self, decision_data: dict[str, Any]) -> AnalysisSection:
        hunger = decision_data.get("hunger_drive", {}) or {}
        curiosity = decision_data.get("curiosity_drive", {}) or {}
        arbitration = decision_data.get("arbitration", {}) or {}
        prediction = decision_data.get("prediction", {}) or {}
        hunger_final = list(((prediction.get("hunger_modulation", {}) or {}).get("final_scores", ()) or ()))
        curiosity_final = list(((prediction.get("curiosity_modulation", {}) or {}).get("final_scores", ()) or ()))
        combined = list(decision_data.get("combined_scores", ()) or ())
        hunger_weight = float(arbitration.get("hunger_weight", 0.0))
        curiosity_weight = float(arbitration.get("curiosity_weight", 0.0))

        rows: list[AnalysisRow] = []
        for index, action in enumerate(ACTION_NAMES):
            hunger_score = hunger_final[index] if index < len(hunger_final) else 0.0
            curiosity_score = curiosity_final[index] if index < len(curiosity_final) else 0.0
            combined_score = combined[index] if index < len(combined) else 0.0
            weighted_hunger = hunger_weight * float(hunger.get("activation", 0.0)) * hunger_score
            weighted_curiosity = curiosity_weight * float(curiosity.get("activation", 0.0)) * curiosity_score
            rows.append(
                AnalysisRow(
                    label=action.capitalize(),
                    value=_fmt(combined_score),
                    sub_rows=(
                        AnalysisRow(label="Weighted Hunger", value=_fmt(weighted_hunger)),
                        AnalysisRow(label="Weighted Curiosity", value=_fmt(weighted_curiosity)),
                    ),
                ),
            )
        return AnalysisSection(title="Decision Pipeline", rows=tuple(rows))

    def _section_predictive_update(self, trace_data: dict[str, Any]) -> AnalysisSection:
        prediction = trace_data.get("prediction", {}) or {}
        hunger = prediction.get("hunger", {}) or {}
        curiosity = prediction.get("curiosity", {}) or {}
        return AnalysisSection(
            title="Predictive Update",
            rows=(
                AnalysisRow(label="Observed Features", value=", ".join(_fmt(value, 3) for value in (prediction.get("observed_features", ()) or ()))),
                AnalysisRow(label="Predicted Features", value=", ".join(_fmt(value, 3) for value in (prediction.get("predicted_features", ()) or ()))),
                AnalysisRow(label="Feature Error +", value=_fmt(prediction.get("feature_error_positive", 0.0))),
                AnalysisRow(label="Feature Error -", value=_fmt(prediction.get("feature_error_negative", 0.0))),
                AnalysisRow(
                    label="Hunger Outcome",
                    value=f"actual={_fmt(hunger.get('actual', 0.0), 3)}, pred={_fmt(hunger.get('predicted', 0.0), 3)}",
                ),
                AnalysisRow(
                    label="Curiosity Outcome",
                    value=f"actual={_fmt(curiosity.get('actual', 0.0), 3)}, pred={_fmt(curiosity.get('predicted', 0.0), 3)}",
                ),
            ),
        )

    def _section_drive_specific_traces(self, trace_data: dict[str, Any]) -> AnalysisSection:
        prediction = trace_data.get("prediction", {}) or {}
        hunger = prediction.get("hunger", {}) or {}
        curiosity = prediction.get("curiosity", {}) or {}
        return AnalysisSection(
            title="Drive-Specific Trace Update",
            rows=(
                AnalysisRow(
                    label="Hunger Trace Pair",
                    value=f"f={_fmt(hunger.get('frustration_value', 0.0), 3)}, c={_fmt(hunger.get('confidence_value', 0.0), 3)}",
                    sub_rows=(
                        AnalysisRow(label="Error +", value=_fmt(hunger.get("error_positive", 0.0), 3)),
                        AnalysisRow(label="Error -", value=_fmt(hunger.get("error_negative", 0.0), 3)),
                    ),
                ),
                AnalysisRow(
                    label="Curiosity Trace Pair",
                    value=f"f={_fmt(curiosity.get('frustration_value', 0.0), 3)}, c={_fmt(curiosity.get('confidence_value', 0.0), 3)}",
                    sub_rows=(
                        AnalysisRow(label="Error +", value=_fmt(curiosity.get("error_positive", 0.0), 3)),
                        AnalysisRow(label="Error -", value=_fmt(curiosity.get("error_negative", 0.0), 3)),
                        AnalysisRow(label="Novelty Weight", value=_fmt(curiosity.get("novelty_weight", 0.0), 3)),
                    ),
                ),
            ),
        )

    def _section_outcome(self, step_trace: BaseStepTrace, trace_data: dict[str, Any]) -> AnalysisSection:
        return AnalysisSection(
            title="Outcome",
            rows=(
                AnalysisRow(label="Action", value=step_trace.action),
                AnalysisRow(label="Action Cost", value=_fmt(trace_data.get("action_cost", 0.0), 2)),
                AnalysisRow(label="Energy Gain", value=_fmt(trace_data.get("energy_gain", 0.0), 2)),
                AnalysisRow(label="Energy Delta", value=f"{float(trace_data.get('energy_delta', 0.0)):+.2f}"),
                AnalysisRow(label="Terminated", value="yes" if step_trace.terminated else "no"),
            ),
        )

    def _modulation_rows(self, modulation: dict[str, Any]) -> tuple[AnalysisRow, ...]:
        raw_scores = _action_dict(modulation.get("raw_scores", {}))
        reliability = _action_dict(modulation.get("reliability_factors", {}))
        biases = _action_dict(modulation.get("prediction_biases", {}))
        final_scores = _action_dict(modulation.get("final_scores", {}))
        confidence = _action_dict(modulation.get("confidence_by_action", {}))
        frustration = _action_dict(modulation.get("frustration_by_action", {}))
        rows: list[AnalysisRow] = [
            AnalysisRow(label="Mode", value=str(modulation.get("modulation_mode", ""))),
        ]
        for action in ACTION_NAMES:
            rows.append(
                AnalysisRow(
                    label=action.capitalize(),
                    value=_fmt(final_scores[action]),
                    sub_rows=(
                        AnalysisRow(label="Raw", value=_fmt(raw_scores[action])),
                        AnalysisRow(label="μ", value=_fmt(reliability[action])),
                        AnalysisRow(label="Bias", value=_fmt(biases[action])),
                        AnalysisRow(label="f", value=_fmt(frustration[action], 3)),
                        AnalysisRow(label="c", value=_fmt(confidence[action], 3)),
                    ),
                ),
            )
        return tuple(rows)

    def _overlay_action_preference(
        self,
        decision_data: dict[str, Any],
        agent_pos: tuple[int, int],
    ) -> OverlayData:
        policy = decision_data.get("policy", {}) or {}
        probabilities = list(policy.get("probabilities", ()) or ())
        selected = str(policy.get("selected_action", ""))
        items: list[OverlayItem] = []
        for index, action in enumerate(ACTION_NAMES):
            probability = probabilities[index] if index < len(probabilities) else 0.0
            if action in DIRECTION_ACTIONS:
                items.append(
                    OverlayItem(
                        item_type="direction_arrow",
                        grid_position=agent_pos,
                        data={
                            "direction": action,
                            "length": min(max(float(probability), 0.0), 1.0),
                            "is_selected": action == selected,
                        },
                    ),
                )
            elif action == "consume":
                items.append(
                    OverlayItem(
                        item_type="center_dot",
                        grid_position=agent_pos,
                        data={"radius": float(probability), "is_selected": action == selected},
                    ),
                )
            else:
                items.append(
                    OverlayItem(
                        item_type="center_ring",
                        grid_position=agent_pos,
                        data={"radius": float(probability), "is_selected": action == selected},
                    ),
                )
        return OverlayData(overlay_type="action_preference", items=tuple(items))

    def _overlay_visit_count_heatmap(self, trace_data: dict[str, Any]) -> OverlayData:
        items = [
            OverlayItem(
                item_type="heatmap_cell",
                grid_position=(int(entry[0][0]), int(entry[0][1])),
                data={"visit_count": int(entry[1])},
            )
            for entry in (trace_data.get("visit_counts_map", ()) or ())
            if isinstance(entry, (list, tuple)) and len(entry) == 2 and isinstance(entry[0], (list, tuple))
        ]
        return OverlayData(overlay_type="visit_count_heatmap", items=tuple(items))

    def _overlay_novelty_field(
        self,
        decision_data: dict[str, Any],
        agent_pos: tuple[int, int],
    ) -> OverlayData:
        curiosity = decision_data.get("curiosity_drive", {}) or {}
        observation = decision_data.get("observation", {}) or {}
        novelty = list(curiosity.get("composite_novelty", ()) or ())
        items: list[OverlayItem] = []
        for index, action in enumerate(DIRECTION_ACTIONS):
            amount = float(novelty[index]) if index < len(novelty) else 0.0
            items.append(
                OverlayItem(
                    item_type="novelty_arrow",
                    grid_position=agent_pos,
                    data={"direction": action, "length": min(max(amount, 0.0), 1.0)},
                ),
            )
            traversability = float(((observation.get(action, {}) or {}).get("traversability", 0.0)))
            if traversability <= 0.0:
                items.append(
                    OverlayItem(
                        item_type="x_marker",
                        grid_position=_relative_neighbor(action, agent_pos),
                        data={},
                    ),
                )
        return OverlayData(overlay_type="novelty_field", items=tuple(items))

    def _overlay_modulation_factor(
        self,
        decision_data: dict[str, Any],
        agent_pos: tuple[int, int],
    ) -> OverlayData:
        arbitration = decision_data.get("arbitration", {}) or {}
        hunger_weight = float(arbitration.get("hunger_weight", 0.0))
        curiosity_weight = float(arbitration.get("curiosity_weight", 0.0))
        prediction = decision_data.get("prediction", {}) or {}
        hunger = _action_dict(
            ((prediction.get("hunger_modulation", {}) or {}).get("reliability_factors", {})),
        )
        curiosity = _action_dict(
            ((prediction.get("curiosity_modulation", {}) or {}).get("reliability_factors", {})),
        )
        weight_total = hunger_weight + curiosity_weight
        items: list[OverlayItem] = []
        for action in DIRECTION_ACTIONS:
            if weight_total > 1e-9:
                net_mu = ((hunger[action] * hunger_weight) + (curiosity[action] * curiosity_weight)) / weight_total
            else:
                net_mu = 1.0
            items.append(
                OverlayItem(
                    item_type="modulation_cell",
                    grid_position=_relative_neighbor(action, agent_pos),
                    data={"modulation_factor": net_mu},
                ),
            )
        return OverlayData(overlay_type="modulation_factor", items=tuple(items))

    def _overlay_dual_modulation_split(
        self,
        decision_data: dict[str, Any],
        agent_pos: tuple[int, int],
    ) -> OverlayData:
        prediction = decision_data.get("prediction", {}) or {}
        hunger = _action_dict(
            ((prediction.get("hunger_modulation", {}) or {}).get("reliability_factors", {})),
        )
        curiosity = _action_dict(
            ((prediction.get("curiosity_modulation", {}) or {}).get("reliability_factors", {})),
        )

        values: list[float] = []
        segments: list[list[dict[str, Any]]] = []
        for action in ACTION_NAMES:
            hunger_delta = hunger[action] - 1.0
            curiosity_delta = curiosity[action] - 1.0
            values.append(abs(hunger_delta) + abs(curiosity_delta))
            segments.append([
                {
                    "value": abs(hunger_delta),
                    "color": [100, 180, 255, 210 if hunger_delta >= 0 else 110],
                },
                {
                    "value": abs(curiosity_delta),
                    "color": [100, 255, 100, 210 if curiosity_delta >= 0 else 110],
                },
            ])

        return OverlayData(
            overlay_type="dual_modulation_split",
            items=(
                OverlayItem(
                    item_type="bar_chart",
                    grid_position=agent_pos,
                    data={
                        "labels": list(ACTION_NAMES),
                        "values": values,
                        "segments": segments,
                        "max_value": max(values, default=1.0) or 1.0,
                        "layout_mode": "stack",
                    },
                ),
            ),
        )

    def _overlay_consumption_opportunity(
        self,
        decision_data: dict[str, Any],
        agent_pos: tuple[int, int],
    ) -> OverlayData:
        observation = decision_data.get("observation", {}) or {}
        current = observation.get("current", {}) or {}
        items: list[OverlayItem] = []
        if float(current.get("resource", 0.0)) > 0.0:
            items.append(
                OverlayItem(
                    item_type="diamond_marker",
                    grid_position=agent_pos,
                    data={"opacity": min(max(float(current.get("resource", 0.0)), 0.1), 1.0)},
                ),
            )
        for action in DIRECTION_ACTIONS:
            cell = observation.get(action, {}) or {}
            if float(cell.get("traversability", 0.0)) <= 0.0:
                items.append(
                    OverlayItem(
                        item_type="x_marker",
                        grid_position=_relative_neighbor(action, agent_pos),
                        data={},
                    ),
                )
        return OverlayData(overlay_type="consumption_opportunity", items=tuple(items))


def _system_cw_vis_factory() -> SystemCWVisualizationAdapter:
    return SystemCWVisualizationAdapter(max_energy=100.0)


register_system_visualization("system_cw", _system_cw_vis_factory)
