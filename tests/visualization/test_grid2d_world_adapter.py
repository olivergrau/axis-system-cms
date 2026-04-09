"""Tests for WP-V.2.1: Grid2D World Visualization Adapter."""

from __future__ import annotations

import pytest

from axis.sdk.position import Position
from axis.visualization.adapters.default_world import DefaultWorldVisualizationAdapter
from axis.visualization.registry import resolve_world_adapter
from axis.visualization.types import CellShape
from axis.world.grid_2d.visualization import Grid2DWorldVisualizationAdapter


import axis.world.grid_2d.visualization  # noqa: F401 -- trigger registration


class TestGrid2DWorldAdapter:

    def test_grid2d_adapter_is_default_subclass(self) -> None:
        adapter = Grid2DWorldVisualizationAdapter()
        assert isinstance(adapter, DefaultWorldVisualizationAdapter)

    def test_grid2d_adapter_cell_shape(self) -> None:
        adapter = Grid2DWorldVisualizationAdapter()
        assert adapter.cell_shape() == CellShape.RECTANGULAR

    def test_grid2d_adapter_cell_layout(self) -> None:
        adapter = Grid2DWorldVisualizationAdapter()
        layout = adapter.cell_layout(3, 3, 300.0, 300.0)
        assert len(layout.cell_centers) == 9
        assert layout.cell_centers[(1, 1)] == (150.0, 150.0)

    def test_grid2d_adapter_color_config(self) -> None:
        adapter = Grid2DWorldVisualizationAdapter()
        cfg = adapter.cell_color_config()
        assert cfg.obstacle_color == (0, 0, 0)
        assert cfg.empty_color == (224, 224, 224)
        assert cfg.resource_color_min == (232, 245, 233)
        assert cfg.resource_color_max == (46, 125, 50)
        assert cfg.agent_color == (33, 150, 243)
        assert cfg.grid_line_color == (158, 158, 158)
        assert cfg.selection_border_color == (255, 160, 0)

    def test_grid2d_adapter_topology_empty(self) -> None:
        adapter = Grid2DWorldVisualizationAdapter()
        layout = adapter.cell_layout(2, 2, 200.0, 200.0)
        from tests.sdk.test_replay_contract import _make_snapshot
        result = adapter.topology_indicators(_make_snapshot(), {}, layout)
        assert result == []

    def test_grid2d_adapter_pixel_to_grid(self) -> None:
        adapter = Grid2DWorldVisualizationAdapter()
        layout = adapter.cell_layout(3, 2, 300.0, 200.0)
        assert adapter.pixel_to_grid(150.0, 50.0, layout) == Position(x=1, y=0)
        assert adapter.pixel_to_grid(-10.0, 50.0, layout) is None

    def test_grid2d_adapter_format_world_info_none(self) -> None:
        adapter = Grid2DWorldVisualizationAdapter()
        assert adapter.format_world_info({}) is None

    def test_grid2d_adapter_metadata_sections_empty(self) -> None:
        adapter = Grid2DWorldVisualizationAdapter()
        assert adapter.world_metadata_sections({}) == []

    def test_grid2d_registration(self) -> None:
        from axis.visualization.registry import (
            _clear_registries,
            register_world_visualization,
        )
        from axis.world.grid_2d.visualization import _grid_2d_vis_factory
        _clear_registries()
        register_world_visualization("grid_2d", _grid_2d_vis_factory)
        result = resolve_world_adapter("grid_2d", {})
        assert type(result).__name__ == "Grid2DWorldVisualizationAdapter"
