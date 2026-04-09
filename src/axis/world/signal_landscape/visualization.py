"""Signal landscape world visualization adapter -- heatmap colors and hotspot indicators."""

from __future__ import annotations

from typing import Any

from axis.sdk.snapshot import WorldSnapshot
from axis.visualization.adapters.default_world import DefaultWorldVisualizationAdapter
from axis.visualization.registry import register_world_visualization
from axis.visualization.types import (
    AnalysisRow,
    CellColorConfig,
    CellLayout,
    MetadataSection,
    TopologyIndicator,
)


class SignalLandscapeWorldVisualizationAdapter(DefaultWorldVisualizationAdapter):
    """Visualization adapter for the signal_landscape world type.

    Overrides colors with a dark heatmap palette, converts hotspot
    positions to topology indicators, and provides metadata sections.
    """

    def cell_color_config(self) -> CellColorConfig:
        return CellColorConfig(
            obstacle_color=(0, 0, 0),
            empty_color=(40, 40, 60),
            resource_color_min=(40, 40, 60),
            resource_color_max=(255, 100, 0),
            agent_color=(33, 150, 243),
            agent_selected_color=(33, 150, 243),
            selection_border_color=(255, 160, 0),
            grid_line_color=(80, 80, 100),
        )

    def topology_indicators(
        self, world_snapshot: WorldSnapshot,
        world_data: dict[str, Any], cell_layout: CellLayout,
    ) -> list[TopologyIndicator]:
        hotspots = world_data.get("hotspots", [])
        indicators: list[TopologyIndicator] = []
        cell_w = cell_layout.canvas_width / cell_layout.grid_width
        for hs in hotspots:
            pixel_x = (hs["cx"] + 0.5) * \
                cell_layout.canvas_width / cell_layout.grid_width
            pixel_y = (hs["cy"] + 0.5) * \
                cell_layout.canvas_height / cell_layout.grid_height
            radius_pixels = hs["radius"] * cell_w
            indicators.append(TopologyIndicator(
                indicator_type="hotspot_center",
                position=(pixel_x, pixel_y),
                data={
                    "radius_pixels": radius_pixels,
                    "intensity": hs["intensity"],
                    "label": f"r={hs['radius']:.1f}",
                },
            ))
        return indicators

    def world_metadata_sections(
        self, world_data: dict[str, Any],
    ) -> list[MetadataSection]:
        hotspots = world_data.get("hotspots", [])
        if not hotspots:
            return []
        rows = tuple(
            AnalysisRow(
                label=f"Hotspot {i + 1}",
                value=(
                    f"({h['cx']:.1f}, {h['cy']:.1f}) "
                    f"r={h['radius']:.1f} I={h['intensity']:.2f}"
                ),
            )
            for i, h in enumerate(hotspots)
        )
        return [MetadataSection(title="Hotspots", rows=rows)]

    def format_world_info(
        self, world_data: dict[str, Any],
    ) -> str | None:
        n = len(world_data.get("hotspots", []))
        return f"{n} hotspot{'s' if n != 1 else ''} active"


def _signal_landscape_vis_factory(
    world_config: dict[str, Any],
) -> SignalLandscapeWorldVisualizationAdapter:
    return SignalLandscapeWorldVisualizationAdapter()


register_world_visualization("signal_landscape", _signal_landscape_vis_factory)
