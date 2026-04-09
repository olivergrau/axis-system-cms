"""Tests for WP-V.5.1: World Adapter Suite.

Cross-cutting protocol compliance for all world visualization adapters,
adapter-specific behaviour, and edge cases.
"""

from __future__ import annotations

import pytest

from axis.sdk.position import Position
from axis.visualization.types import (
    CellColorConfig,
    CellLayout,
    CellShape,
    TopologyIndicator,
)

from tests.v02.visualization.adapter_fixtures import (
    ALL_WORLD_ADAPTERS,
    make_snapshot,
    sample_signal_landscape_world_data,
)


# ---------------------------------------------------------------------------
# Protocol compliance (parametrized over all 4 world adapters)
# ---------------------------------------------------------------------------

_ADAPTER_IDS = [a[0] for a in ALL_WORLD_ADAPTERS]
_ADAPTERS = [a[1] for a in ALL_WORLD_ADAPTERS]


@pytest.fixture(params=_ADAPTERS, ids=_ADAPTER_IDS)
def world_adapter(request):
    return request.param


class TestWorldAdapterProtocol:

    def test_cell_shape_returns_enum(self, world_adapter) -> None:
        result = world_adapter.cell_shape()
        assert isinstance(result, CellShape)

    def test_cell_shape_is_rectangular(self, world_adapter) -> None:
        assert world_adapter.cell_shape() == CellShape.RECTANGULAR

    def test_cell_layout_returns_cell_layout(self, world_adapter) -> None:
        layout = world_adapter.cell_layout(5, 5, 500.0, 500.0)
        assert isinstance(layout, CellLayout)
        assert layout.grid_width == 5
        assert layout.grid_height == 5

    def test_cell_layout_has_all_cells(self, world_adapter) -> None:
        layout = world_adapter.cell_layout(3, 4, 300.0, 400.0)
        expected = {(x, y) for x in range(3) for y in range(4)}
        assert set(layout.cell_centers.keys()) == expected

    def test_cell_layout_centers_within_canvas(self, world_adapter) -> None:
        cw, ch = 600.0, 400.0
        layout = world_adapter.cell_layout(5, 5, cw, ch)
        for (_, _), (cx, cy) in layout.cell_centers.items():
            assert 0 <= cx <= cw
            assert 0 <= cy <= ch

    def test_cell_layout_polygons_have_4_vertices(self, world_adapter) -> None:
        layout = world_adapter.cell_layout(3, 3, 300.0, 300.0)
        for poly in layout.cell_polygons.values():
            assert len(poly) == 4

    def test_cell_layout_bounding_boxes_positive(self, world_adapter) -> None:
        layout = world_adapter.cell_layout(3, 3, 300.0, 300.0)
        for x0, y0, w, h in layout.cell_bounding_boxes.values():
            assert w > 0
            assert h > 0

    def test_cell_color_config_returns_config(self, world_adapter) -> None:
        cfg = world_adapter.cell_color_config()
        assert isinstance(cfg, CellColorConfig)
        assert len(cfg.obstacle_color) == 3
        assert len(cfg.empty_color) == 3
        assert len(cfg.resource_color_min) == 3
        assert len(cfg.resource_color_max) == 3

    def test_topology_indicators_returns_list(self, world_adapter) -> None:
        snap = make_snapshot()
        layout = world_adapter.cell_layout(5, 5, 500.0, 500.0)
        result = world_adapter.topology_indicators(snap, {}, layout)
        assert isinstance(result, list)

    def test_pixel_to_grid_valid_pixel(self, world_adapter) -> None:
        layout = world_adapter.cell_layout(5, 5, 500.0, 500.0)
        center = layout.cell_centers[(0, 0)]
        result = world_adapter.pixel_to_grid(center[0], center[1], layout)
        assert result == Position(x=0, y=0)

    def test_pixel_to_grid_negative_returns_none(self, world_adapter) -> None:
        layout = world_adapter.cell_layout(5, 5, 500.0, 500.0)
        assert world_adapter.pixel_to_grid(-10.0, 50.0, layout) is None

    def test_pixel_to_grid_outside_canvas_returns_none(self, world_adapter) -> None:
        layout = world_adapter.cell_layout(5, 5, 500.0, 500.0)
        assert world_adapter.pixel_to_grid(999.0, 999.0, layout) is None

    def test_pixel_to_grid_center_roundtrips(self, world_adapter) -> None:
        layout = world_adapter.cell_layout(5, 5, 500.0, 500.0)
        center = layout.cell_centers[(2, 3)]
        result = world_adapter.pixel_to_grid(center[0], center[1], layout)
        assert result == Position(x=2, y=3)

    def test_agent_marker_center_returns_tuple(self, world_adapter) -> None:
        layout = world_adapter.cell_layout(5, 5, 500.0, 500.0)
        result = world_adapter.agent_marker_center(
            Position(x=1, y=1), layout)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_world_metadata_sections_returns_list(self, world_adapter) -> None:
        result = world_adapter.world_metadata_sections({})
        assert isinstance(result, list)

    def test_format_world_info_returns_string_or_none(self, world_adapter) -> None:
        result = world_adapter.format_world_info({})
        assert result is None or isinstance(result, str)


# ---------------------------------------------------------------------------
# Toroidal-specific tests
# ---------------------------------------------------------------------------


class TestToroidalAdapterSpecific:

    def _adapter(self):
        from axis.world.toroidal.visualization import (
            ToroidalWorldVisualizationAdapter,
        )
        return ToroidalWorldVisualizationAdapter()

    def test_topology_indicators_count(self) -> None:
        adapter = self._adapter()
        snap = make_snapshot()
        layout = adapter.cell_layout(5, 5, 500.0, 500.0)
        indicators = adapter.topology_indicators(snap, {}, layout)
        assert len(indicators) == 4

    def test_topology_indicator_types(self) -> None:
        adapter = self._adapter()
        snap = make_snapshot()
        layout = adapter.cell_layout(5, 5, 500.0, 500.0)
        indicators = adapter.topology_indicators(snap, {}, layout)
        for ind in indicators:
            assert ind.indicator_type == "wrap_edge"

    def test_all_edges_covered(self) -> None:
        adapter = self._adapter()
        snap = make_snapshot()
        layout = adapter.cell_layout(5, 5, 500.0, 500.0)
        indicators = adapter.topology_indicators(snap, {}, layout)
        edges = {ind.data["edge"] for ind in indicators}
        assert edges == {"left", "right", "top", "bottom"}

    def test_format_world_info(self) -> None:
        adapter = self._adapter()
        result = adapter.format_world_info({})
        assert result is not None
        assert "Toroidal" in result

    def test_inherits_default_color_config(self) -> None:
        from axis.visualization.adapters.default_world import (
            DefaultWorldVisualizationAdapter,
        )
        adapter = self._adapter()
        default = DefaultWorldVisualizationAdapter()
        assert adapter.cell_color_config() == default.cell_color_config()


# ---------------------------------------------------------------------------
# Signal landscape-specific tests
# ---------------------------------------------------------------------------


class TestSignalLandscapeAdapterSpecific:

    def _adapter(self):
        from axis.world.signal_landscape.visualization import (
            SignalLandscapeWorldVisualizationAdapter,
        )
        return SignalLandscapeWorldVisualizationAdapter()

    def test_heatmap_color_config(self) -> None:
        adapter = self._adapter()
        cfg = adapter.cell_color_config()
        assert cfg.resource_color_max == (255, 100, 0)
        assert cfg.empty_color == (40, 40, 60)

    def test_hotspot_topology_indicators(self) -> None:
        adapter = self._adapter()
        snap = make_snapshot(width=10, height=10)
        layout = adapter.cell_layout(10, 10, 500.0, 500.0)
        world_data = sample_signal_landscape_world_data()
        indicators = adapter.topology_indicators(snap, world_data, layout)
        assert len(indicators) == 2
        for ind in indicators:
            assert ind.indicator_type == "hotspot_center"

    def test_no_hotspots_empty_indicators(self) -> None:
        adapter = self._adapter()
        snap = make_snapshot(width=10, height=10)
        layout = adapter.cell_layout(10, 10, 500.0, 500.0)
        indicators = adapter.topology_indicators(snap, {}, layout)
        assert indicators == []

    def test_world_metadata_sections_with_hotspots(self) -> None:
        adapter = self._adapter()
        world_data = sample_signal_landscape_world_data()
        sections = adapter.world_metadata_sections(world_data)
        assert len(sections) == 1
        assert sections[0].title == "Hotspots"
        assert len(sections[0].rows) == 2

    def test_format_world_info_with_hotspots(self) -> None:
        adapter = self._adapter()
        world_data = sample_signal_landscape_world_data()
        result = adapter.format_world_info(world_data)
        assert result is not None
        assert "hotspot" in result.lower()
        assert "2" in result


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestWorldAdapterEdgeCases:

    def test_1x1_grid_layout(self) -> None:
        from axis.visualization.adapters.default_world import (
            DefaultWorldVisualizationAdapter,
        )
        adapter = DefaultWorldVisualizationAdapter()
        layout = adapter.cell_layout(1, 1, 100.0, 100.0)
        assert len(layout.cell_centers) == 1
        assert (0, 0) in layout.cell_centers

    def test_large_50x50_grid_layout(self) -> None:
        from axis.visualization.adapters.default_world import (
            DefaultWorldVisualizationAdapter,
        )
        adapter = DefaultWorldVisualizationAdapter()
        layout = adapter.cell_layout(50, 50, 1000.0, 1000.0)
        assert len(layout.cell_centers) == 2500

    def test_pixel_to_grid_at_cell_boundary(self) -> None:
        from axis.visualization.adapters.default_world import (
            DefaultWorldVisualizationAdapter,
        )
        adapter = DefaultWorldVisualizationAdapter()
        layout = adapter.cell_layout(5, 5, 500.0, 500.0)
        # Exact boundary between cells (0,0) and (1,0) at x=100
        result = adapter.pixel_to_grid(100.0, 50.0, layout)
        assert result is not None
        assert result.x in (0, 1)
