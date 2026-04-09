"""Grid2D world visualization adapter -- rectangular grid with default behavior."""

from __future__ import annotations

from typing import Any

from axis.visualization.adapters.default_world import DefaultWorldVisualizationAdapter
from axis.visualization.registry import register_world_visualization


class Grid2DWorldVisualizationAdapter(DefaultWorldVisualizationAdapter):
    """Visualization adapter for the built-in grid_2d world type.

    Inherits all behavior from DefaultWorldVisualizationAdapter.
    """

    pass


def _grid_2d_vis_factory(world_config: dict[str, Any]) -> Grid2DWorldVisualizationAdapter:
    return Grid2DWorldVisualizationAdapter()


register_world_visualization("grid_2d", _grid_2d_vis_factory)
