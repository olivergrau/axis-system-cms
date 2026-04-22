"""Grid2D world visualization adapter."""

from __future__ import annotations

from typing import Any

from axis.sdk.snapshot import WorldSnapshot
from axis.visualization.adapters.default_world import DefaultWorldVisualizationAdapter
from axis.visualization.registry import register_world_visualization
from axis.visualization.types import CellLayout, TopologyIndicator


class Grid2DWorldVisualizationAdapter(DefaultWorldVisualizationAdapter):
    """Visualization adapter for the built-in grid_2d world type.

    Uses the default rectangular grid behavior for bounded worlds and
    exposes toroidal wrap indicators when ``topology`` is configured as
    ``"toroidal"``.
    """

    def __init__(self, *, topology: str = "bounded") -> None:
        self._topology = topology

    def _is_toroidal(self, world_data: dict[str, Any]) -> bool:
        return (
            self._topology == "toroidal"
            or world_data.get("topology") == "toroidal"
        )

    def topology_indicators(
        self,
        world_snapshot: WorldSnapshot,
        world_data: dict[str, Any],
        cell_layout: CellLayout,
    ) -> list[TopologyIndicator]:
        if not self._is_toroidal(world_data):
            return []

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

    def format_world_info(self, world_data: dict[str, Any]) -> str | None:
        if self._is_toroidal(world_data):
            return "Toroidal topology (edges wrap)"
        return None


def _grid_2d_vis_factory(world_config: dict[str, Any]) -> Grid2DWorldVisualizationAdapter:
    topology = world_config.get("topology", "bounded")
    return Grid2DWorldVisualizationAdapter(topology=topology)


register_world_visualization("grid_2d", _grid_2d_vis_factory)
