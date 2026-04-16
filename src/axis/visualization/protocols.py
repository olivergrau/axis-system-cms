"""Visualization adapter protocols -- structural contracts for world and system adapters."""

from __future__ import annotations

from typing import Any, Protocol

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseStepTrace
from axis.visualization.types import (
    AnalysisSection,
    CellColorConfig,
    CellLayout,
    CellShape,
    MetadataSection,
    OverlayData,
    OverlayTypeDeclaration,
    TopologyIndicator,
)


class WorldVisualizationAdapter(Protocol):
    """Structural protocol for world-type-specific visualization logic.

    One adapter per world type. Handles geometry, colors, topology,
    and world metadata display.
    """

    def cell_shape(self) -> CellShape: ...

    def cell_layout(
        self, grid_width: int, grid_height: int,
        canvas_width: float, canvas_height: float,
    ) -> CellLayout: ...

    def cell_color_config(self) -> CellColorConfig: ...

    def topology_indicators(
        self, world_snapshot: WorldSnapshot,
        world_data: dict[str, Any], cell_layout: CellLayout,
    ) -> list[TopologyIndicator]: ...

    def pixel_to_grid(
        self, pixel_x: float, pixel_y: float, cell_layout: CellLayout,
    ) -> Position | None: ...

    def agent_marker_center(
        self, grid_position: Position, cell_layout: CellLayout,
    ) -> tuple[float, float]: ...

    def world_metadata_sections(
        self, world_data: dict[str, Any],
    ) -> list[MetadataSection]: ...

    def format_world_info(
        self, world_data: dict[str, Any],
    ) -> str | None: ...


class SystemVisualizationAdapter(Protocol):
    """Structural protocol for system-type-specific visualization logic.

    One adapter per system type. Handles phase naming, vitality
    formatting, analysis panels, and overlay generation.
    """

    def phase_names(self) -> list[str]: ...

    def vitality_label(self) -> str: ...

    def format_vitality(
        self, value: float, system_data: dict[str, Any],
    ) -> str: ...

    def build_step_analysis(
        self, step_trace: BaseStepTrace,
    ) -> list[AnalysisSection]: ...

    def build_overlays(
        self, step_trace: BaseStepTrace,
    ) -> list[OverlayData]: ...

    def available_overlay_types(self) -> list[OverlayTypeDeclaration]: ...

    def build_system_widget_data(
        self, step_trace: BaseStepTrace,
    ) -> dict[str, Any] | None: ...
