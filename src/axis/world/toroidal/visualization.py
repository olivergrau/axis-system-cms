"""Toroidal world visualization adapter -- wrap-edge topology indicators."""

from __future__ import annotations

from typing import Any

from axis.sdk.snapshot import WorldSnapshot
from axis.visualization.registry import register_world_visualization
from axis.visualization.types import CellLayout, TopologyIndicator
from axis.world.grid_2d.visualization import Grid2DWorldVisualizationAdapter


class ToroidalWorldVisualizationAdapter(Grid2DWorldVisualizationAdapter):
    """Visualization adapter for the toroidal world type.

    Inherits rectangular grid geometry from Grid2D, adds wrap-edge
    topology indicators and world info text.
    """

    def topology_indicators(
        self, world_snapshot: WorldSnapshot,
        world_data: dict[str, Any], cell_layout: CellLayout,
    ) -> list[TopologyIndicator]:
        cw = cell_layout.canvas_width
        ch = cell_layout.canvas_height
        return [
            TopologyIndicator(
                indicator_type="wrap_edge",
                position=(0.0, ch / 2),
                data={"edge": "left", "style": "dashed"},
            ),
            TopologyIndicator(
                indicator_type="wrap_edge",
                position=(cw, ch / 2),
                data={"edge": "right", "style": "dashed"},
            ),
            TopologyIndicator(
                indicator_type="wrap_edge",
                position=(cw / 2, 0.0),
                data={"edge": "top", "style": "dashed"},
            ),
            TopologyIndicator(
                indicator_type="wrap_edge",
                position=(cw / 2, ch),
                data={"edge": "bottom", "style": "dashed"},
            ),
        ]

    def format_world_info(
        self, world_data: dict[str, Any],
    ) -> str | None:
        return "Toroidal topology (edges wrap)"


def _toroidal_vis_factory(world_config: dict[str, Any]) -> ToroidalWorldVisualizationAdapter:
    return ToroidalWorldVisualizationAdapter()


register_world_visualization("toroidal", _toroidal_vis_factory)
