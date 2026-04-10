"""System A+W visualization adapter.

Extends the System A visualization pattern with curiosity-specific
analysis sections and overlay types. Reads system_data from BaseStepTrace.
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


class SystemAWVisualizationAdapter:
    """Visualization adapter for System A+W.

    Produces 7 analysis sections and 5 overlay types, extending
    System A's adapter with curiosity drive, drive arbitration,
    visit count heatmap, and novelty field overlays.
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

    # ── Step analysis (7 sections) ───────────────────────────

    def build_step_analysis(
        self, step_trace: BaseStepTrace,
    ) -> list[AnalysisSection]:
        dd = step_trace.system_data.get("decision_data", {})
        td = step_trace.system_data.get("trace_data", {})
        return [
            self._section_step_overview(step_trace, td),
            self._section_observation(dd),
            self._section_hunger_drive(dd),
            self._section_curiosity_drive(dd),
            self._section_drive_arbitration(dd),
            self._section_decision_pipeline(dd),
            self._section_outcome(step_trace, td),
        ]

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
            self._overlay_consumption_opportunity(dd, pos),
            self._overlay_visit_count_heatmap(td, pos),
            self._overlay_novelty_field(dd, pos),
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
                description="Stacked bars: hunger (blue) + curiosity "
                            "(green) per action.",
                legend_html=(
                    "<span style='color:#64B4FF'>\u25a0</span>=hunger "
                    "<span style='color:#64FF64'>\u25a0</span>=curiosity "
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
                key="visit_count_heatmap",
                label="Visit Count Map",
                description="Heatmap showing visit count at the "
                            "agent's current position.",
                legend_html=(
                    "intensity=visit count"
                ),
            ),
            OverlayTypeDeclaration(
                key="novelty_field",
                label="Novelty Field",
                description="Per-direction composite novelty as "
                            "directional indicators.",
                legend_html=(
                    "arrow length=novelty intensity"
                ),
            ),
        ]

    # ── Private: analysis section helpers ────────────────────

    def _section_step_overview(
        self, step_trace: BaseStepTrace, trace_data: dict[str, Any],
    ) -> AnalysisSection:
        rel_pos = trace_data.get("relative_position", (0, 0))
        visit_count = trace_data.get("visit_count_at_current", 0)
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
                AnalysisRow(
                    label="Relative Position",
                    value=f"({rel_pos[0]}, {rel_pos[1]})"),
                AnalysisRow(
                    label="Visit Count",
                    value=str(visit_count)),
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

    def _section_hunger_drive(
        self, decision_data: dict[str, Any],
    ) -> AnalysisSection:
        drive = decision_data.get("hunger_drive", {})
        contributions = drive.get("action_contributions", ())
        rows: list[AnalysisRow] = [
            AnalysisRow(
                label="Activation",
                value=f"{drive.get('activation', 0.0):.4f}"),
        ]
        for i, name in enumerate(ACTION_NAMES):
            val = contributions[i] if i < len(contributions) else 0.0
            rows.append(AnalysisRow(
                label=name.capitalize(),
                value=f"{val:.4f}",
            ))
        return AnalysisSection(title="Hunger Drive", rows=tuple(rows))

    def _section_curiosity_drive(
        self, decision_data: dict[str, Any],
    ) -> AnalysisSection:
        cd = decision_data.get("curiosity_drive", {})
        rows: list[AnalysisRow] = [
            AnalysisRow(
                label="Activation",
                value=f"{cd.get('activation', 0.0):.4f}"),
        ]

        # Spatial novelty
        spatial = cd.get("spatial_novelty", (0, 0, 0, 0))
        spatial_sub = tuple(
            AnalysisRow(label=d.capitalize(), value=f"{spatial[i]:.4f}")
            for i, d in enumerate(DIRECTION_ACTIONS)
        )
        rows.append(AnalysisRow(
            label="Spatial Novelty", value="", sub_rows=spatial_sub))

        # Sensory novelty
        sensory = cd.get("sensory_novelty", (0, 0, 0, 0))
        sensory_sub = tuple(
            AnalysisRow(label=d.capitalize(), value=f"{sensory[i]:.4f}")
            for i, d in enumerate(DIRECTION_ACTIONS)
        )
        rows.append(AnalysisRow(
            label="Sensory Novelty", value="", sub_rows=sensory_sub))

        # Composite novelty
        composite = cd.get("composite_novelty", (0, 0, 0, 0))
        composite_sub = tuple(
            AnalysisRow(label=d.capitalize(), value=f"{composite[i]:.4f}")
            for i, d in enumerate(DIRECTION_ACTIONS)
        )
        rows.append(AnalysisRow(
            label="Composite Novelty", value="", sub_rows=composite_sub))

        # Action contributions
        contributions = cd.get("action_contributions", ())
        for i, name in enumerate(ACTION_NAMES):
            val = contributions[i] if i < len(contributions) else 0.0
            rows.append(AnalysisRow(
                label=name.capitalize(),
                value=f"{val:.4f}",
            ))

        return AnalysisSection(title="Curiosity Drive", rows=tuple(rows))

    def _section_drive_arbitration(
        self, decision_data: dict[str, Any],
    ) -> AnalysisSection:
        arb = decision_data.get("arbitration", {})
        hd = decision_data.get("hunger_drive", {})
        cd = decision_data.get("curiosity_drive", {})

        w_h = arb.get("hunger_weight", 0.0)
        w_c = arb.get("curiosity_weight", 0.0)
        d_h = hd.get("activation", 0.0)
        d_c = cd.get("activation", 0.0)

        hunger_influence = w_h * d_h
        curiosity_influence = w_c * d_c
        dominant = "Hunger" if hunger_influence >= curiosity_influence \
            else "Curiosity"

        ratio = f"{w_c / w_h:.3f}" if w_h > 0 else "\u221e"

        return AnalysisSection(
            title="Drive Arbitration",
            rows=(
                AnalysisRow(
                    label="Hunger Weight",
                    value=f"{w_h:.4f}"),
                AnalysisRow(
                    label="Curiosity Weight",
                    value=f"{w_c:.4f}"),
                AnalysisRow(
                    label="Dominant Drive",
                    value=dominant),
                AnalysisRow(
                    label="Weight Ratio (wC/wH)",
                    value=ratio),
            ),
        )

    def _section_decision_pipeline(
        self, decision_data: dict[str, Any],
    ) -> AnalysisSection:
        policy = decision_data.get("policy", {})
        raw = policy.get("raw_scores", ())
        mask = policy.get("admissibility_mask", ())
        masked = tuple(
            v if v is not None else float("-inf")
            for v in policy.get("masked_scores", ())
        )
        probs = policy.get("probabilities", ())

        rows: list[AnalysisRow] = [
            AnalysisRow(
                label="Temperature",
                value=f"{policy.get('temperature', 0.0):.2f}"),
            AnalysisRow(
                label="Selection Mode",
                value=policy.get("selection_mode", "")),
        ]

        for i, name in enumerate(ACTION_NAMES):
            raw_val = raw[i] if i < len(raw) else 0.0
            masked_val = (f"{masked[i]:.4f}"
                          if i < len(masked) and masked[i] != float("-inf")
                          else "-inf")
            mask_val = mask[i] if i < len(mask) else True
            prob_val = probs[i] if i < len(probs) else 0.0
            sub = (
                AnalysisRow(label="Raw", value=f"{raw_val:.4f}"),
                AnalysisRow(label="Admissible",
                            value="Yes" if mask_val else "No"),
                AnalysisRow(label="Masked", value=masked_val),
            )
            rows.append(AnalysisRow(
                label=name.capitalize(),
                value=f"p={prob_val:.4f}",
                sub_rows=sub,
            ))

        rows.append(AnalysisRow(
            label="Selected",
            value=policy.get("selected_action", "")))

        return AnalysisSection(title="Decision Pipeline", rows=tuple(rows))

    def _section_outcome(
        self, step_trace: BaseStepTrace, trace_data: dict[str, Any],
    ) -> AnalysisSection:
        moved = (step_trace.agent_position_before
                 != step_trace.agent_position_after)
        pos = step_trace.agent_position_after
        rel_pos = trace_data.get("relative_position", (0, 0))
        return AnalysisSection(
            title="Outcome",
            rows=(
                AnalysisRow(label="Moved",
                            value="Yes" if moved else "No"),
                AnalysisRow(label="Position",
                            value=f"({pos.x}, {pos.y})"),
                AnalysisRow(label="Relative Position",
                            value=f"({rel_pos[0]}, {rel_pos[1]})"),
                AnalysisRow(label="Action Cost",
                            value=f"{trace_data.get('action_cost', 0.0):.2f}"),
                AnalysisRow(label="Energy Gain",
                            value=f"{trace_data.get('energy_gain', 0.0):.2f}"),
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
        hunger = decision_data.get("hunger_drive", {})
        curiosity = decision_data.get("curiosity_drive", {})
        return OverlayData(
            overlay_type="drive_contribution",
            items=(
                OverlayItem(
                    item_type="bar_chart",
                    grid_position=agent_pos,
                    data={
                        "drive": "hunger",
                        "activation": hunger.get("activation", 0.0),
                        "values": list(
                            hunger.get("action_contributions", ())),
                        "labels": list(ACTION_NAMES),
                    },
                ),
                OverlayItem(
                    item_type="bar_chart",
                    grid_position=agent_pos,
                    data={
                        "drive": "curiosity",
                        "activation": curiosity.get("activation", 0.0),
                        "values": list(
                            curiosity.get("action_contributions", ())),
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
            overlay_type="consumption_opportunity",
            items=tuple(items),
        )

    def _overlay_visit_count_heatmap(
        self, trace_data: dict[str, Any],
        agent_pos: tuple[int, int],
    ) -> OverlayData:
        visit_count = trace_data.get("visit_count_at_current", 0)
        return OverlayData(
            overlay_type="visit_count_heatmap",
            items=(
                OverlayItem(
                    item_type="heatmap_cell",
                    grid_position=agent_pos,
                    data={
                        "visit_count": visit_count,
                        "intensity": 1.0 / (1 + visit_count)
                        if visit_count > 0 else 1.0,
                    },
                ),
            ),
        )

    def _overlay_novelty_field(
        self, decision_data: dict[str, Any],
        agent_pos: tuple[int, int],
    ) -> OverlayData:
        cd = decision_data.get("curiosity_drive", {})
        composite = cd.get("composite_novelty", (0, 0, 0, 0))

        items: list[OverlayItem] = []
        for i, direction in enumerate(DIRECTION_ACTIONS):
            val = composite[i] if i < len(composite) else 0.0
            items.append(OverlayItem(
                item_type="novelty_arrow",
                grid_position=agent_pos,
                data={
                    "direction": direction,
                    "length": val,
                    "intensity": val,
                },
            ))

        return OverlayData(
            overlay_type="novelty_field",
            items=tuple(items),
        )


def _system_aw_vis_factory() -> SystemAWVisualizationAdapter:
    return SystemAWVisualizationAdapter(max_energy=100.0)


register_system_visualization("system_aw", _system_aw_vis_factory)
