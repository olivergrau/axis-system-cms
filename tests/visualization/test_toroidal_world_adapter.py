"""Tests for WP-V.2.2: Toroidal World Visualization Adapter."""

from __future__ import annotations

import pytest

from axis.visualization.registry import resolve_world_adapter
from axis.visualization.types import CellShape
from axis.world.toroidal.visualization import ToroidalWorldVisualizationAdapter


import axis.world.grid_2d.visualization  # noqa: F401 -- trigger registration
import axis.world.toroidal.visualization  # noqa: F401


def _make_layout(gw: int, gh: int, cw: float, ch: float):
    adapter = ToroidalWorldVisualizationAdapter()
    return adapter.cell_layout(gw, gh, cw, ch)


class TestToroidalWorldAdapter:

    def test_toroidal_inherits_grid2d_behavior(self) -> None:
        adapter = ToroidalWorldVisualizationAdapter()
        assert adapter.cell_shape() == CellShape.RECTANGULAR
        cfg = adapter.cell_color_config()
        assert cfg.obstacle_color == (0, 0, 0)
        assert cfg.empty_color == (224, 224, 224)

    def test_toroidal_topology_indicators_count(self) -> None:
        adapter = ToroidalWorldVisualizationAdapter()
        layout = _make_layout(3, 3, 300.0, 300.0)
        from tests.sdk.test_replay_contract import _make_snapshot
        indicators = adapter.topology_indicators(_make_snapshot(), {}, layout)
        assert len(indicators) == 4

    def test_toroidal_topology_indicator_types(self) -> None:
        adapter = ToroidalWorldVisualizationAdapter()
        layout = _make_layout(3, 3, 300.0, 300.0)
        from tests.sdk.test_replay_contract import _make_snapshot
        indicators = adapter.topology_indicators(_make_snapshot(), {}, layout)
        for ind in indicators:
            assert ind.indicator_type == "wrap_edge"

    def test_toroidal_topology_indicator_edges(self) -> None:
        adapter = ToroidalWorldVisualizationAdapter()
        layout = _make_layout(3, 3, 300.0, 300.0)
        from tests.sdk.test_replay_contract import _make_snapshot
        indicators = adapter.topology_indicators(_make_snapshot(), {}, layout)
        edges = {ind.data["edge"] for ind in indicators}
        assert edges == {"left", "right", "top", "bottom"}

    def test_toroidal_topology_indicator_positions(self) -> None:
        adapter = ToroidalWorldVisualizationAdapter()
        layout = _make_layout(3, 2, 300.0, 200.0)
        from tests.sdk.test_replay_contract import _make_snapshot
        indicators = adapter.topology_indicators(
            _make_snapshot(), {}, layout)
        by_edge = {ind.data["edge"]: ind.position for ind in indicators}
        assert by_edge["left"] == (0.0, 100.0)
        assert by_edge["right"] == (300.0, 100.0)
        assert by_edge["top"] == (150.0, 0.0)
        assert by_edge["bottom"] == (150.0, 200.0)

    def test_toroidal_format_world_info(self) -> None:
        adapter = ToroidalWorldVisualizationAdapter()
        assert adapter.format_world_info(
            {}) == "Toroidal topology (edges wrap)"

    def test_toroidal_metadata_sections_empty(self) -> None:
        adapter = ToroidalWorldVisualizationAdapter()
        assert adapter.world_metadata_sections({}) == []

    def test_toroidal_registration(self) -> None:
        from axis.visualization.registry import (
            _clear_registries,
            register_world_visualization,
        )
        from axis.world.grid_2d.visualization import _grid_2d_vis_factory
        from axis.world.toroidal.visualization import _toroidal_vis_factory
        _clear_registries()
        register_world_visualization("grid_2d", _grid_2d_vis_factory)
        register_world_visualization("toroidal", _toroidal_vis_factory)
        result = resolve_world_adapter("toroidal", {})
        assert type(result).__name__ == "ToroidalWorldVisualizationAdapter"
