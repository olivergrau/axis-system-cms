"""Default world visualization adapter -- rectangular grid geometry."""

from __future__ import annotations

from typing import Any

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.visualization.types import (
    CellColorConfig,
    CellLayout,
    CellShape,
    MetadataSection,
    TopologyIndicator,
)


class DefaultWorldVisualizationAdapter:
    """Default adapter for rectangular grid worlds.

    Provides basic rectangular cell geometry, standard color palette,
    and simple pixel-to-grid hit testing. Used as fallback when no
    world-type-specific adapter is registered.
    """

    def cell_shape(self) -> CellShape:
        return CellShape.RECTANGULAR

    def cell_layout(
        self, grid_width: int, grid_height: int,
        canvas_width: float, canvas_height: float,
    ) -> CellLayout:
        cell_w = canvas_width / grid_width
        cell_h = canvas_height / grid_height

        polygons: dict[tuple[int, int], tuple[tuple[float, float], ...]] = {}
        centers: dict[tuple[int, int], tuple[float, float]] = {}
        bboxes: dict[tuple[int, int], tuple[float, float, float, float]] = {}

        for y in range(grid_height):
            for x in range(grid_width):
                x0 = x * cell_w
                y0 = y * cell_h
                polygons[(x, y)] = (
                    (x0, y0),
                    (x0 + cell_w, y0),
                    (x0 + cell_w, y0 + cell_h),
                    (x0, y0 + cell_h),
                )
                centers[(x, y)] = (x0 + cell_w / 2, y0 + cell_h / 2)
                bboxes[(x, y)] = (x0, y0, cell_w, cell_h)

        return CellLayout(
            cell_shape=CellShape.RECTANGULAR,
            grid_width=grid_width,
            grid_height=grid_height,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            cell_polygons=polygons,
            cell_centers=centers,
            cell_bounding_boxes=bboxes,
        )

    def cell_color_config(self) -> CellColorConfig:
        return CellColorConfig(
            obstacle_color=(0, 0, 0),
            empty_color=(224, 224, 224),
            resource_color_min=(232, 245, 233),
            resource_color_max=(46, 125, 50),
            agent_color=(33, 150, 243),
            agent_selected_color=(33, 150, 243),
            selection_border_color=(255, 160, 0),
            grid_line_color=(158, 158, 158),
        )

    def topology_indicators(
        self, world_snapshot: WorldSnapshot,
        world_data: dict[str, Any], cell_layout: CellLayout,
    ) -> list[TopologyIndicator]:
        return []

    def pixel_to_grid(
        self, pixel_x: float, pixel_y: float, cell_layout: CellLayout,
    ) -> Position | None:
        if pixel_x < 0 or pixel_y < 0:
            return None
        if pixel_x >= cell_layout.canvas_width or pixel_y >= cell_layout.canvas_height:
            return None
        cell_w = cell_layout.canvas_width / cell_layout.grid_width
        cell_h = cell_layout.canvas_height / cell_layout.grid_height
        gx = int(pixel_x / cell_w)
        gy = int(pixel_y / cell_h)
        if gx >= cell_layout.grid_width or gy >= cell_layout.grid_height:
            return None
        return Position(x=gx, y=gy)

    def agent_marker_center(
        self, grid_position: Position, cell_layout: CellLayout,
    ) -> tuple[float, float]:
        return cell_layout.cell_centers[(grid_position.x, grid_position.y)]

    def world_metadata_sections(
        self, world_data: dict[str, Any],
    ) -> list[MetadataSection]:
        return []

    def format_world_info(
        self, world_data: dict[str, Any],
    ) -> str | None:
        return None
