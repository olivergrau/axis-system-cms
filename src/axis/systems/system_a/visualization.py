"""System A visualization adapter.

Reproduces the full v0.1.0 analysis panel and debug overlay content
through structured data. Reads system_data from BaseStepTrace.
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


def _action_score_bar_data(
    values: tuple[float, ...] | list[float],
) -> tuple[list[float], float]:
    """Convert signed action scores into relative bar lengths.

    The overlay is meant to show behavioral dominance, not signed distance
    from zero. Shift scores so the minimum score maps to zero width and
    higher-scoring actions produce longer bars.
    """
    vals = list(values)
    if not vals:
        return [], 1.0
    min_value = min(vals)
    shifted = [v - min_value for v in vals]
    max_value = max(shifted, default=0.0) or 1.0
    return shifted, max_value


class SystemAVisualizationAdapter:
    """Visualization adapter for System A.

    Reads decision_data and trace_data from system_data to produce
    analysis sections and overlay data matching the v0.1.0 viewer.
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

    # ── Step analysis (6 sections) ───────────────────────────

    def build_step_analysis(
        self, step_trace: BaseStepTrace,
    ) -> list[AnalysisSection]:
        dd = step_trace.system_data.get("decision_data", {})
        td = step_trace.system_data.get("trace_data", {})
        return [
            self._section_step_overview(step_trace, td),
            self._section_observation(dd),
            self._section_observation_buffer(td),
            self._section_drive_output(dd),
            self._section_decision_pipeline(dd),
            self._section_outcome(step_trace, td),
        ]

    # ── Debug overlays (4 types) ─────────────────────────────

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
            self._overlay_consumption_opportunity(dd, pos),
            self._overlay_buffer_saturation(td, pos),
        ]

    def available_overlay_types(self) -> list[OverlayTypeDeclaration]:
        return [
            OverlayTypeDeclaration(
                key="action_preference",
                label="Action Preference",
                description="Arrows showing action probabilities, "
                            "dot for consume, ring for stay.",
                legend_html=(
                    "<span style='color:#FFC800'>\u2192</span>=selected "
                    "<span style='color:#C8C8C8'>\u2192</span>=candidate "
                    "<span style='color:#FFC800'>\u25cf</span>=consume "
                    "<span style='color:#C8C8C8'>\u25cb</span>=stay "
                    "length=probability"
                ),
            ),
            OverlayTypeDeclaration(
                key="drive_contribution",
                label="Drive Contribution",
                description="Bar chart showing hunger drive activation "
                            "and per-action contributions.",
                legend_html=(
                    "<span style='color:#64B4FF'>\u25a0</span>=contribution "
                    "U/D/L/R/C/S"
                ),
            ),
            OverlayTypeDeclaration(
                key="consumption_opportunity",
                label="Consumption Opportunity",
                description="Diamond on current cell if resource > 0, "
                            "neighbor resource dots, X for blocked.",
                legend_html=(
                    "<span style='color:#FFDC00'>\u25c6</span>=resource "
                    "<span style='color:#64FF64'>\u25cf</span>=neighbor "
                    "<span style='color:#FF5050'>\u2715</span>=blocked"
                ),
            ),
            OverlayTypeDeclaration(
                key="buffer_saturation",
                label="Buffer Saturation",
                description="Ring around agent showing average resource "
                            "richness across the observation buffer.",
                legend_html=(
                    "<span style='color:#5050FF'>\u25cb</span>=low resource "
                    "<span style='color:#50FF50'>\u25cb</span>=high resource "
                    "thickness=fill level"
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
                    value=f"{trace_data['energy_before']:.2f}"),
                AnalysisRow(
                    label="Energy After",
                    value=f"{trace_data['energy_after']:.2f}"),
                AnalysisRow(
                    label="Energy Delta",
                    value=f"{trace_data['energy_delta']:+.2f}"),
            ),
        )

    def _section_observation(
        self, decision_data: dict[str, Any],
    ) -> AnalysisSection:
        obs = decision_data.get("observation", {})
        rows: list[AnalysisRow] = [
            AnalysisRow(
                label="Current",
                value=f"resource={obs['current']['resource']:.3f}"),
        ]
        for direction in DIRECTION_ACTIONS:
            d = obs[direction]
            trav = "traversable" if d["traversability"] > 0 else "blocked"
            rows.append(AnalysisRow(
                label=direction.capitalize(),
                value=f"resource={d['resource']:.3f}, {trav}",
            ))
        return AnalysisSection(title="Observation", rows=tuple(rows))

    def _section_observation_buffer(
        self, trace_data: dict[str, Any],
    ) -> AnalysisSection:
        snapshot = trace_data.get("buffer_snapshot", [])
        capacity = trace_data.get("buffer_capacity", len(snapshot))
        title = f"Observation Buffer ({len(snapshot)}/{capacity})"
        rows: list[AnalysisRow] = []
        for entry in reversed(snapshot):
            ts = entry["timestep"]
            res = (f"[{entry['current_res']:.2f}, {entry['up_res']:.2f}, "
                   f"{entry['down_res']:.2f}, {entry['left_res']:.2f}, "
                   f"{entry['right_res']:.2f}]")
            trav = (f"[{int(entry['current_trav'])}, {int(entry['up_trav'])}, "
                    f"{int(entry['down_trav'])}, {int(entry['left_trav'])}, "
                    f"{int(entry['right_trav'])}]")
            rows.append(AnalysisRow(
                label=f"t={ts}",
                value=f"res={res}",
                sub_rows=(
                    AnalysisRow(label="Traversability", value=trav),
                ),
            ))
        if not rows:
            rows.append(AnalysisRow(label="(empty)", value="\u2014"))
        return AnalysisSection(title=title, rows=tuple(rows))

    def _section_drive_output(
        self, decision_data: dict[str, Any],
    ) -> AnalysisSection:
        drive = decision_data.get("drive", {})
        contributions = drive.get("action_contributions", ())
        rows: list[AnalysisRow] = [
            AnalysisRow(
                label="Activation",
                value=f"{drive['activation']:.4f}"),
        ]
        for i, name in enumerate(ACTION_NAMES):
            rows.append(AnalysisRow(
                label=name.capitalize(),
                value=f"{contributions[i]:.4f}",
            ))
        return AnalysisSection(title="Drive Output", rows=tuple(rows))

    def _section_decision_pipeline(
        self, decision_data: dict[str, Any],
    ) -> AnalysisSection:
        policy = decision_data.get("policy", {})
        raw = policy.get("raw_contributions", ())
        mask = policy.get("admissibility_mask", ())
        masked = tuple(
            v if v is not None else float("-inf")
            for v in policy.get("masked_contributions", ())
        )
        probs = policy.get("probabilities", ())

        rows: list[AnalysisRow] = [
            AnalysisRow(
                label="Temperature",
                value=f"{policy['temperature']:.2f}"),
            AnalysisRow(
                label="Selection Mode",
                value=policy["selection_mode"]),
        ]

        for i, name in enumerate(ACTION_NAMES):
            masked_val = (f"{masked[i]:.4f}"
                          if masked[i] != float("-inf") else "-inf")
            sub = (
                AnalysisRow(label="Raw", value=f"{raw[i]:.4f}"),
                AnalysisRow(label="Admissible",
                            value="Yes" if mask[i] else "No"),
                AnalysisRow(label="Masked", value=masked_val),
            )
            rows.append(AnalysisRow(
                label=name.capitalize(),
                value=f"p={probs[i]:.4f}",
                sub_rows=sub,
            ))

        rows.append(AnalysisRow(
            label="Selected",
            value=policy["selected_action"]))

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
                            value=f"{trace_data['action_cost']:.2f}"),
                AnalysisRow(label="Energy Gain",
                            value=f"{trace_data['energy_gain']:.2f}"),
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
                    "length": probs[i],
                    "is_selected": is_sel,
                    "color": "selected" if is_sel else "default",
                },
            ))

        consume_prob = probs[4] if len(probs) > 4 else 0.0
        if consume_prob > 0:
            items.append(OverlayItem(
                item_type="center_dot",
                grid_position=agent_pos,
                data={
                    "radius": consume_prob,
                    "is_selected": "consume" == selected,
                },
            ))

        stay_prob = probs[5] if len(probs) > 5 else 0.0
        if stay_prob > 0:
            items.append(OverlayItem(
                item_type="center_ring",
                grid_position=agent_pos,
                data={
                    "radius": stay_prob,
                    "is_selected": "stay" == selected,
                },
            ))

        return OverlayData(
            overlay_type="action_preference",
            items=tuple(items),
        )

    def _overlay_drive_contribution(
        self, decision_data: dict[str, Any],
        agent_pos: tuple[int, int],
    ) -> OverlayData:
        drive = decision_data.get("drive", {})
        display_values, display_max = _action_score_bar_data(
            drive.get("action_contributions", ()),
        )
        return OverlayData(
            overlay_type="drive_contribution",
            items=(
                OverlayItem(
                    item_type="bar_chart",
                    grid_position=agent_pos,
                    data={
                        "activation": drive.get("activation", 0.0),
                        "values": display_values,
                        "labels": list(ACTION_NAMES),
                        "max_value": display_max,
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
            overlay_type="consumption_opportunity",
            items=tuple(items),
        )

    def _overlay_buffer_saturation(
        self, trace_data: dict[str, Any],
        agent_pos: tuple[int, int],
    ) -> OverlayData:
        snapshot = trace_data.get("buffer_snapshot", [])
        capacity = trace_data.get("buffer_capacity", 1)
        if snapshot:
            total = sum(
                e["current_res"] + e["up_res"] + e["down_res"]
                + e["left_res"] + e["right_res"]
                for e in snapshot
            )
            saturation = total / (len(snapshot) * 5)
        else:
            saturation = 0.0
        fill_ratio = len(snapshot) / max(capacity, 1)
        return OverlayData(
            overlay_type="buffer_saturation",
            items=(
                OverlayItem(
                    item_type="saturation_ring",
                    grid_position=agent_pos,
                    data={
                        "saturation": saturation,
                        "fill_ratio": fill_ratio,
                    },
                ),
            ),
        )


def _system_a_vis_factory() -> SystemAVisualizationAdapter:
    return SystemAVisualizationAdapter(max_energy=100.0)


register_system_visualization("system_a", _system_a_vis_factory)
