"""Null system visualization adapter -- minimal fallback for unknown systems."""

from __future__ import annotations

from axis.sdk.trace import BaseStepTrace
from axis.visualization.types import (
    AnalysisSection,
    OverlayData,
    OverlayTypeDeclaration,
)


class NullSystemVisualizationAdapter:
    """Fallback adapter for system types with no registered visualization.

    Provides minimal defaults: two standard phases, percentage vitality,
    and empty analysis/overlay data.
    """

    def phase_names(self) -> list[str]:
        return ["BEFORE", "AFTER_ACTION"]

    def vitality_label(self) -> str:
        return "Vitality"

    def format_vitality(self, value: float, system_data: dict[str, object]) -> str:
        return f"{value:.0%}"

    def build_step_analysis(self, step_trace: BaseStepTrace) -> list[AnalysisSection]:
        return []

    def build_overlays(self, step_trace: BaseStepTrace) -> list[OverlayData]:
        return []

    def available_overlay_types(self) -> list[OverlayTypeDeclaration]:
        return []
