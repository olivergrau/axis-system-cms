"""System B visualization adapter.

Simpler decision pipeline than System A. Features scan-area overlay
using the radius_circle item type.
"""

from __future__ import annotations

from typing import Any

from axis.sdk.trace import BaseStepTrace
from axis.visualization.registry import register_system_visualization
from axis.visualization.types import (
    AnalysisRow,
    AnalysisSection,
    OverlayData,
    OverlayItem,
    OverlayTypeDeclaration,
)

ACTION_NAMES: tuple[str, ...] = ("up", "down", "left", "right", "scan", "stay")
DIRECTION_ACTIONS: tuple[str, ...] = ("up", "down", "left", "right")


class SystemBVisualizationAdapter:
    """Visualization adapter for System B."""

    def __init__(self, max_energy: float) -> None:
        self._max_energy = max_energy

    def phase_names(self) -> list[str]:
        return ["BEFORE", "AFTER_ACTION"]

    def vitality_label(self) -> str:
        return "Energy"

    def format_vitality(
        self, value: float, system_data: dict[str, Any],
    ) -> str:
        energy = value * self._max_energy
        return f"{energy:.2f} / {self._max_energy:.2f}"

    def build_step_analysis(
        self, step_trace: BaseStepTrace,
    ) -> list[AnalysisSection]:
        dd = step_trace.system_data.get("decision_data", {})
        td = step_trace.system_data.get("trace_data", {})
        return [
            self._section_step_overview(step_trace, td),
            self._section_decision_weights(dd),
            self._section_probabilities(dd),
            self._section_last_scan(dd),
            self._section_outcome(step_trace, td),
        ]

    def build_overlays(
        self, step_trace: BaseStepTrace,
    ) -> list[OverlayData]:
        dd = step_trace.system_data.get("decision_data", {})
        td = step_trace.system_data.get("trace_data", {})
        pos = (step_trace.agent_position_before.x,
               step_trace.agent_position_before.y)
        return [
            self._overlay_action_weights(dd, pos, step_trace.action),
            self._overlay_scan_result(dd, td, pos),
        ]

    def available_overlay_types(self) -> list[OverlayTypeDeclaration]:
        return [
            OverlayTypeDeclaration(
                key="action_weights",
                label="Action Weights",
                description="Arrows showing action probabilities, "
                            "highlighting selected action.",
                legend_html=(
                    "<span style='color:#FFC800'>\u2192</span>=selected "
                    "<span style='color:#C8C8C8'>\u2192</span>=candidate "
                    "length=probability"
                ),
            ),
            OverlayTypeDeclaration(
                key="scan_result",
                label="Scan Result",
                description="Circle showing scan area around agent "
                            "with total resource label.",
                legend_html=(
                    "<span style='color:#64C8FF'>\u25cb</span>=scan radius "
                    "\u03a3=total resource"
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
                AnalysisRow(label="Timestep",
                            value=str(step_trace.timestep)),
                AnalysisRow(label="Action",
                            value=step_trace.action),
                AnalysisRow(label="Energy Before",
                            value=f"{trace_data['energy_before']:.2f}"),
                AnalysisRow(label="Energy After",
                            value=f"{trace_data['energy_after']:.2f}"),
                AnalysisRow(label="Energy Delta",
                            value=f"{trace_data['energy_delta']:+.2f}"),
                AnalysisRow(label="Action Cost",
                            value=f"{trace_data['action_cost']:.2f}"),
            ),
        )

    def _section_decision_weights(
        self, decision_data: dict[str, Any],
    ) -> AnalysisSection:
        weights = decision_data.get("weights", [0.0] * 6)
        rows = tuple(
            AnalysisRow(label=name.capitalize(),
                        value=f"{weights[i]:.4f}")
            for i, name in enumerate(ACTION_NAMES)
        )
        return AnalysisSection(title="Decision Weights", rows=rows)

    def _section_probabilities(
        self, decision_data: dict[str, Any],
    ) -> AnalysisSection:
        probs = decision_data.get("probabilities", [0.0] * 6)
        rows = tuple(
            AnalysisRow(label=name.capitalize(),
                        value=f"{probs[i]:.4f}")
            for i, name in enumerate(ACTION_NAMES)
        )
        return AnalysisSection(title="Probabilities", rows=rows)

    def _section_last_scan(
        self, decision_data: dict[str, Any],
    ) -> AnalysisSection:
        last_scan = decision_data.get("last_scan")
        if last_scan is None:
            return AnalysisSection(
                title="Last Scan",
                rows=(AnalysisRow(
                    label="Status", value="No scan performed"),),
            )
        return AnalysisSection(
            title="Last Scan",
            rows=(
                AnalysisRow(
                    label="Total Resource",
                    value=f"{last_scan['total_resource']:.3f}"),
                AnalysisRow(
                    label="Cell Count",
                    value=str(last_scan["cell_count"])),
            ),
        )

    def _section_outcome(
        self, step_trace: BaseStepTrace, trace_data: dict[str, Any],
    ) -> AnalysisSection:
        return AnalysisSection(
            title="Outcome",
            rows=(
                AnalysisRow(label="Action",
                            value=step_trace.action),
                AnalysisRow(label="Energy Delta",
                            value=f"{trace_data['energy_delta']:+.2f}"),
                AnalysisRow(label="Scan Total",
                            value=f"{trace_data['scan_total']:.3f}"),
                AnalysisRow(label="Terminated",
                            value="Yes" if step_trace.terminated else "No"),
                AnalysisRow(label="Reason",
                            value=step_trace.termination_reason or "\u2014"),
            ),
        )

    # ── Private: overlay helpers ─────────────────────────────

    def _overlay_action_weights(
        self, decision_data: dict[str, Any],
        agent_pos: tuple[int, int],
        selected_action: str,
    ) -> OverlayData:
        probs = decision_data.get("probabilities", [0.0] * 6)
        items: list[OverlayItem] = []
        for i, action in enumerate(DIRECTION_ACTIONS):
            is_sel = action == selected_action
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
        return OverlayData(
            overlay_type="action_weights",
            items=tuple(items),
        )

    def _overlay_scan_result(
        self, decision_data: dict[str, Any],
        trace_data: dict[str, Any],
        agent_pos: tuple[int, int],
    ) -> OverlayData:
        scan_total = trace_data.get("scan_total", 0.0)
        return OverlayData(
            overlay_type="scan_result",
            items=(
                OverlayItem(
                    item_type="radius_circle",
                    grid_position=agent_pos,
                    data={
                        "radius_cells": 1,
                        "label": f"\u03a3={scan_total:.2f}",
                    },
                ),
            ),
        )


def _system_b_vis_factory() -> SystemBVisualizationAdapter:
    return SystemBVisualizationAdapter(max_energy=100.0)


register_system_visualization("system_b", _system_b_vis_factory)
