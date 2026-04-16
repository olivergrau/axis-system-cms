"""System C visualization adapter.

Extends the System A analysis panel with prediction-specific
sections: context encoding, prediction error, dual traces,
and modulation factor.
"""

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

ACTION_NAMES: tuple[str, ...] = (
    "up", "down", "left", "right", "consume", "stay")
DIRECTION_ACTIONS: tuple[str, ...] = ("up", "down", "left", "right")


class SystemCVisualizationAdapter:
    """Visualization adapter for System C.

    Reads decision_data and trace_data from system_data to produce
    analysis sections and overlay data. Adds prediction-specific
    sections beyond System A's baseline.
    """

    def __init__(self, max_energy: float) -> None:
        self._max_energy = max_energy

    # ── Phase navigation ─────────────────────────────────────

    def phase_names(self) -> list[str]:
        return ["BEFORE", "AFTER_REGEN", "AFTER_ACTION"]

    # ── Vitality display ─────────────────────────────────────

    def vitality_label(self) -> str:
        return "Energy"

    def format_vitality(
        self, value: float, system_data: dict[str, Any],
    ) -> str:
        energy = value * self._max_energy
        return f"{energy:.2f} / {self._max_energy:.2f}"

    # ── Step analysis (8 sections) ───────────────────────────

    def build_step_analysis(
        self, step_trace: BaseStepTrace,
    ) -> list[AnalysisSection]:
        dd = step_trace.system_data.get("decision_data", {})
        td = step_trace.system_data.get("trace_data", {})
        sections = [
            self._section_step_overview(step_trace, td),
            self._section_observation(dd),
            self._section_drive_output(dd),
            self._section_prediction(dd),
            self._section_decision_pipeline(dd),
        ]
        if td.get("prediction"):
            sections.append(self._section_prediction_update(td))
        sections.append(self._section_outcome(step_trace, td))
        return sections

    # ── Debug overlays (5 types) ─────────────────────────────

    def build_overlays(
        self, step_trace: BaseStepTrace,
    ) -> list[OverlayData]:
        dd = step_trace.system_data.get("decision_data", {})
        td = step_trace.system_data.get("trace_data", {})
        pos = (step_trace.agent_position_before.x,
               step_trace.agent_position_before.y)
        return [
            self._overlay_action_preference(dd, pos),
            self._overlay_drive_contribution(dd, pos),
            self._overlay_modulated_contribution(dd, pos),
            self._overlay_consumption_opportunity(dd, pos),
            self._overlay_modulation_factor(dd, pos),
        ]

    def available_overlay_types(self) -> list[OverlayTypeDeclaration]:
        return [
            OverlayTypeDeclaration(
                key="action_preference",
                label="Action Preference",
                description="Arrows showing action probabilities.",
                legend_html=(
                    "<span style='color:#FFC800'>\u2192</span>=selected "
                    "<span style='color:#C8C8C8'>\u2192</span>=candidate "
                    "length=probability"
                ),
            ),
            OverlayTypeDeclaration(
                key="drive_contribution",
                label="Raw Drive Contribution",
                description="Bar chart of raw hunger drive action scores.",
                legend_html=(
                    "<span style='color:#64B4FF'>\u25a0</span>=raw "
                    "U/D/L/R/C/S"
                ),
            ),
            OverlayTypeDeclaration(
                key="modulated_contribution",
                label="Modulated Scores",
                description="Bar chart of modulated action scores "
                            "after prediction adjustment.",
                legend_html=(
                    "<span style='color:#FF9632'>\u25a0</span>=modulated "
                    "U/D/L/R/C/S"
                ),
            ),
            OverlayTypeDeclaration(
                key="consumption_opportunity",
                label="Consumption Opportunity",
                description="Diamond on current cell if resource > 0.",
                legend_html=(
                    "<span style='color:#FFDC00'>\u25c6</span>=resource "
                    "<span style='color:#FF5050'>\u2715</span>=blocked"
                ),
            ),
            OverlayTypeDeclaration(
                key="modulation_factor",
                label="Modulation Factor",
                description="Per-action modulation factor mu(s,a). "
                            "Values <1 suppress, >1 reinforce.",
                legend_html=(
                    "<span style='color:#FF5050'>\u25a0</span>=suppress "
                    "<span style='color:#50FF50'>\u25a0</span>=reinforce "
                    "height=magnitude"
                ),
            ),
        ]

    # ── Private: analysis section helpers ────────────────────

    def _section_step_overview(
        self, step_trace: BaseStepTrace, trace_data: dict[str, Any],
    ) -> AnalysisSection:
        return AnalysisSection(
            title="Step Overview",
            rows=(
                AnalysisRow(label="Timestep", value=str(step_trace.timestep)),
                AnalysisRow(label="Action", value=step_trace.action),
                AnalysisRow(
                    label="Energy Before",
                    value=f"{trace_data.get('energy_before', 0):.2f}"),
                AnalysisRow(
                    label="Energy After",
                    value=f"{trace_data.get('energy_after', 0):.2f}"),
                AnalysisRow(
                    label="Energy Delta",
                    value=f"{trace_data.get('energy_delta', 0):+.2f}"),
            ),
        )

    def _section_observation(
        self, decision_data: dict[str, Any],
    ) -> AnalysisSection:
        obs = decision_data.get("observation", {})
        rows: list[AnalysisRow] = [
            AnalysisRow(
                label="Current",
                value=f"resource={obs.get('current', {}).get('resource', 0):.3f}"),
        ]
        for direction in DIRECTION_ACTIONS:
            d = obs.get(direction, {})
            trav = "traversable" if d.get(
                "traversability", 0) > 0 else "blocked"
            rows.append(AnalysisRow(
                label=direction.capitalize(),
                value=f"resource={d.get('resource', 0):.3f}, {trav}",
            ))
        return AnalysisSection(title="Observation", rows=tuple(rows))

    def _section_drive_output(
        self, decision_data: dict[str, Any],
    ) -> AnalysisSection:
        drive = decision_data.get("drive", {})
        contributions = drive.get("action_contributions", ())
        rows: list[AnalysisRow] = [
            AnalysisRow(
                label="Activation",
                value=f"{drive.get('activation', 0):.4f}"),
        ]
        for i, name in enumerate(ACTION_NAMES):
            val = contributions[i] if i < len(contributions) else 0.0
            rows.append(AnalysisRow(
                label=name.capitalize(), value=f"{val:.4f}"))
        return AnalysisSection(title="Drive Output", rows=tuple(rows))

    def _section_prediction(
        self, decision_data: dict[str, Any],
    ) -> AnalysisSection:
        pred = decision_data.get("prediction", {})
        context = pred.get("context", "?")
        features = pred.get("features", ())
        modulated = pred.get("modulated_scores", ())
        drive = decision_data.get("drive", {})
        raw = drive.get("action_contributions", ())

        rows: list[AnalysisRow] = [
            AnalysisRow(
                label="Context",
                value=f"{context} (0b{context:05b})" if isinstance(context, int) else str(context)),
            AnalysisRow(
                label="Features",
                value=", ".join(f"{f:.3f}" for f in features)),
        ]

        for i, name in enumerate(ACTION_NAMES):
            raw_val = raw[i] if i < len(raw) else 0.0
            mod_val = modulated[i] if i < len(modulated) else 0.0
            if raw_val != 0:
                ratio = mod_val / raw_val
                rows.append(AnalysisRow(
                    label=name.capitalize(),
                    value=f"{mod_val:.4f}",
                    sub_rows=(
                        AnalysisRow(label="Raw", value=f"{raw_val:.4f}"),
                        AnalysisRow(label="\u03bc", value=f"{ratio:.4f}"),
                    ),
                ))
            else:
                rows.append(AnalysisRow(
                    label=name.capitalize(),
                    value=f"{mod_val:.4f}",
                ))

        return AnalysisSection(
            title="Prediction & Modulation", rows=tuple(rows))

    def _section_prediction_update(
        self, trace_data: dict[str, Any],
    ) -> AnalysisSection:
        pred = trace_data.get("prediction", {})
        context = pred.get("context", "?")
        predicted = pred.get("predicted_features", ())
        observed = pred.get("observed_features", ())
        err_pos = pred.get("error_positive", 0.0)
        err_neg = pred.get("error_negative", 0.0)

        return AnalysisSection(
            title="Predictive Update",
            rows=(
                AnalysisRow(
                    label="Pre-action Context",
                    value=str(context)),
                AnalysisRow(
                    label="Predicted",
                    value=", ".join(f"{v:.3f}" for v in predicted)),
                AnalysisRow(
                    label="Observed",
                    value=", ".join(f"{v:.3f}" for v in observed)),
                AnalysisRow(
                    label="\u03b5\u207a (positive)",
                    value=f"{err_pos:.4f}"),
                AnalysisRow(
                    label="\u03b5\u207b (negative)",
                    value=f"{err_neg:.4f}"),
            ),
        )

    def _section_decision_pipeline(
        self, decision_data: dict[str, Any],
    ) -> AnalysisSection:
        policy = decision_data.get("policy", {})
        probs = policy.get("probabilities", ())
        rows: list[AnalysisRow] = [
            AnalysisRow(
                label="Temperature",
                value=f"{policy.get('temperature', 0):.2f}"),
            AnalysisRow(
                label="Selection Mode",
                value=policy.get("selection_mode", "?")),
        ]
        for i, name in enumerate(ACTION_NAMES):
            p = probs[i] if i < len(probs) else 0.0
            rows.append(AnalysisRow(
                label=name.capitalize(), value=f"p={p:.4f}"))
        rows.append(AnalysisRow(
            label="Selected",
            value=policy.get("selected_action", "?")))
        return AnalysisSection(title="Decision Pipeline", rows=tuple(rows))

    def _section_outcome(
        self, step_trace: BaseStepTrace, trace_data: dict[str, Any],
    ) -> AnalysisSection:
        moved = (step_trace.agent_position_before
                 != step_trace.agent_position_after)
        pos = step_trace.agent_position_after
        return AnalysisSection(
            title="Outcome",
            rows=(
                AnalysisRow(label="Moved",
                            value="Yes" if moved else "No"),
                AnalysisRow(label="Position",
                            value=f"({pos.x}, {pos.y})"),
                AnalysisRow(label="Action Cost",
                            value=f"{trace_data.get('action_cost', 0):.2f}"),
                AnalysisRow(label="Energy Gain",
                            value=f"{trace_data.get('energy_gain', 0):.2f}"),
                AnalysisRow(label="Terminated",
                            value="Yes" if step_trace.terminated else "No"),
                AnalysisRow(label="Reason",
                            value=step_trace.termination_reason or "\u2014"),
            ),
        )

    # ── Private: overlay helpers ─────────────────────────────

    def _overlay_action_preference(
        self, decision_data: dict[str, Any],
        agent_pos: tuple[int, int],
    ) -> OverlayData:
        policy = decision_data.get("policy", {})
        probs = policy.get("probabilities", ())
        selected = policy.get("selected_action", "")

        items: list[OverlayItem] = []
        for i, action in enumerate(DIRECTION_ACTIONS):
            is_sel = action == selected
            items.append(OverlayItem(
                item_type="direction_arrow",
                grid_position=agent_pos,
                data={
                    "direction": action,
                    "length": probs[i] if i < len(probs) else 0.0,
                    "is_selected": is_sel,
                    "color": "selected" if is_sel else "default",
                },
            ))
        return OverlayData(
            overlay_type="action_preference", items=tuple(items))

    def _overlay_drive_contribution(
        self, decision_data: dict[str, Any],
        agent_pos: tuple[int, int],
    ) -> OverlayData:
        drive = decision_data.get("drive", {})
        return OverlayData(
            overlay_type="drive_contribution",
            items=(
                OverlayItem(
                    item_type="bar_chart",
                    grid_position=agent_pos,
                    data={
                        "activation": drive.get("activation", 0.0),
                        "values": list(
                            drive.get("action_contributions", ())),
                        "labels": list(ACTION_NAMES),
                    },
                ),
            ),
        )

    def _overlay_modulated_contribution(
        self, decision_data: dict[str, Any],
        agent_pos: tuple[int, int],
    ) -> OverlayData:
        pred = decision_data.get("prediction", {})
        return OverlayData(
            overlay_type="modulated_contribution",
            items=(
                OverlayItem(
                    item_type="bar_chart",
                    grid_position=agent_pos,
                    data={
                        "values": list(
                            pred.get("modulated_scores", ())),
                        "labels": list(ACTION_NAMES),
                    },
                ),
            ),
        )

    def _overlay_consumption_opportunity(
        self, decision_data: dict[str, Any],
        agent_pos: tuple[int, int],
    ) -> OverlayData:
        obs = decision_data.get("observation", {})
        items: list[OverlayItem] = []

        current_resource = obs.get("current", {}).get("resource", 0.0)
        if current_resource > 0:
            items.append(OverlayItem(
                item_type="diamond_marker",
                grid_position=agent_pos,
                data={"opacity": current_resource},
            ))

        for direction in DIRECTION_ACTIONS:
            dx, dy = MOVEMENT_DELTAS[direction]
            neighbor = (agent_pos[0] + dx, agent_pos[1] + dy)
            d = obs.get(direction, {})
            if d.get("traversability", 0) > 0:
                items.append(OverlayItem(
                    item_type="neighbor_dot",
                    grid_position=neighbor,
                    data={
                        "resource_value": d.get("resource", 0.0),
                        "is_traversable": True,
                    },
                ))
            else:
                items.append(OverlayItem(
                    item_type="x_marker",
                    grid_position=neighbor,
                    data={},
                ))

        return OverlayData(
            overlay_type="consumption_opportunity", items=tuple(items))

    def _overlay_modulation_factor(
        self, decision_data: dict[str, Any],
        agent_pos: tuple[int, int],
    ) -> OverlayData:
        pred = decision_data.get("prediction", {})
        drive = decision_data.get("drive", {})
        modulated = pred.get("modulated_scores", ())
        raw = drive.get("action_contributions", ())

        values: list[float] = []
        for i in range(len(ACTION_NAMES)):
            raw_val = raw[i] if i < len(raw) else 0.0
            mod_val = modulated[i] if i < len(modulated) else 0.0
            if raw_val != 0:
                values.append(mod_val / raw_val)
            else:
                values.append(1.0)

        return OverlayData(
            overlay_type="modulation_factor",
            items=(
                OverlayItem(
                    item_type="bar_chart",
                    grid_position=agent_pos,
                    data={
                        "values": values,
                        "labels": list(ACTION_NAMES),
                        "baseline": 1.0,
                    },
                ),
            ),
        )


def _system_c_vis_factory() -> SystemCVisualizationAdapter:
    return SystemCVisualizationAdapter(max_energy=100.0)


register_system_visualization("system_c", _system_c_vis_factory)
