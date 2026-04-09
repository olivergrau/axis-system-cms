"""Tests for WP-V.2.3: Signal Landscape World Visualization Adapter."""

from __future__ import annotations

import pytest

from axis.visualization.registry import resolve_world_adapter
from axis.visualization.types import CellShape
from axis.world.signal_landscape.visualization import (
    SignalLandscapeWorldVisualizationAdapter,
)


import axis.world.grid_2d.visualization  # noqa: F401 -- trigger registration
import axis.world.signal_landscape.visualization  # noqa: F401


def _hotspot(cx: float = 5.0, cy: float = 3.0,
             radius: float = 2.0, intensity: float = 0.8) -> dict:
    return {"cx": cx, "cy": cy, "radius": radius, "intensity": intensity}


class TestSignalLandscapeColors:

    def test_signal_landscape_heatmap_colors(self) -> None:
        adapter = SignalLandscapeWorldVisualizationAdapter()
        cfg = adapter.cell_color_config()
        assert cfg.obstacle_color == (0, 0, 0)
        assert cfg.empty_color == (40, 40, 60)
        assert cfg.resource_color_min == (40, 40, 60)
        assert cfg.resource_color_max == (255, 100, 0)

    def test_signal_landscape_grid_line_color(self) -> None:
        adapter = SignalLandscapeWorldVisualizationAdapter()
        cfg = adapter.cell_color_config()
        assert cfg.grid_line_color == (80, 80, 100)


class TestSignalLandscapeTopology:

    def test_signal_landscape_topology_with_hotspots(self) -> None:
        adapter = SignalLandscapeWorldVisualizationAdapter()
        layout = adapter.cell_layout(10, 10, 200.0, 200.0)
        from tests.v02.sdk.test_replay_contract import _make_snapshot
        world_data = {"hotspots": [_hotspot()]}
        indicators = adapter.topology_indicators(
            _make_snapshot(), world_data, layout)
        assert len(indicators) == 1
        assert indicators[0].indicator_type == "hotspot_center"

    def test_signal_landscape_topology_indicator_position(self) -> None:
        adapter = SignalLandscapeWorldVisualizationAdapter()
        layout = adapter.cell_layout(10, 10, 200.0, 200.0)
        from tests.v02.sdk.test_replay_contract import _make_snapshot
        world_data = {"hotspots": [_hotspot(cx=5.0, cy=3.0)]}
        indicators = adapter.topology_indicators(
            _make_snapshot(), world_data, layout)
        # pixel_x = (5.0 + 0.5) * 200 / 10 = 110.0
        # pixel_y = (3.0 + 0.5) * 200 / 10 = 70.0
        assert indicators[0].position == (110.0, 70.0)

    def test_signal_landscape_topology_indicator_data(self) -> None:
        adapter = SignalLandscapeWorldVisualizationAdapter()
        layout = adapter.cell_layout(10, 10, 200.0, 200.0)
        from tests.v02.sdk.test_replay_contract import _make_snapshot
        world_data = {"hotspots": [_hotspot(
            cx=5.0, cy=3.0, radius=2.0, intensity=0.8)]}
        indicators = adapter.topology_indicators(
            _make_snapshot(), world_data, layout)
        data = indicators[0].data
        # radius_pixels = 2.0 * (200.0 / 10) = 40.0
        assert data["radius_pixels"] == 40.0
        assert data["intensity"] == 0.8
        assert "2.0" in data["label"]

    def test_signal_landscape_topology_no_hotspots(self) -> None:
        adapter = SignalLandscapeWorldVisualizationAdapter()
        layout = adapter.cell_layout(5, 5, 100.0, 100.0)
        from tests.v02.sdk.test_replay_contract import _make_snapshot
        indicators = adapter.topology_indicators(
            _make_snapshot(), {}, layout)
        assert indicators == []

    def test_signal_landscape_topology_multiple_hotspots(self) -> None:
        adapter = SignalLandscapeWorldVisualizationAdapter()
        layout = adapter.cell_layout(10, 10, 200.0, 200.0)
        from tests.v02.sdk.test_replay_contract import _make_snapshot
        world_data = {"hotspots": [
            _hotspot(), _hotspot(cx=1.0), _hotspot(cx=8.0)]}
        indicators = adapter.topology_indicators(
            _make_snapshot(), world_data, layout)
        assert len(indicators) == 3


class TestSignalLandscapeMetadata:

    def test_signal_landscape_metadata_sections(self) -> None:
        adapter = SignalLandscapeWorldVisualizationAdapter()
        world_data = {"hotspots": [_hotspot(), _hotspot(cx=1.0)]}
        sections = adapter.world_metadata_sections(world_data)
        assert len(sections) == 1
        assert sections[0].title == "Hotspots"
        assert len(sections[0].rows) == 2

    def test_signal_landscape_metadata_row_content(self) -> None:
        adapter = SignalLandscapeWorldVisualizationAdapter()
        world_data = {"hotspots": [_hotspot(
            cx=5.0, cy=3.0, radius=2.0, intensity=0.80)]}
        sections = adapter.world_metadata_sections(world_data)
        row = sections[0].rows[0]
        assert row.label == "Hotspot 1"
        assert "5.0" in row.value
        assert "3.0" in row.value
        assert "r=2.0" in row.value
        assert "I=0.80" in row.value

    def test_signal_landscape_metadata_empty_when_no_hotspots(self) -> None:
        adapter = SignalLandscapeWorldVisualizationAdapter()
        assert adapter.world_metadata_sections({}) == []


class TestSignalLandscapeFormatWorldInfo:

    def test_signal_landscape_format_world_info(self) -> None:
        adapter = SignalLandscapeWorldVisualizationAdapter()
        assert adapter.format_world_info(
            {"hotspots": [_hotspot()] * 3}) == "3 hotspots active"
        assert adapter.format_world_info(
            {"hotspots": [_hotspot()]}) == "1 hotspot active"

    def test_signal_landscape_format_world_info_no_hotspots(self) -> None:
        adapter = SignalLandscapeWorldVisualizationAdapter()
        assert adapter.format_world_info({}) == "0 hotspots active"


class TestSignalLandscapeInheritance:

    def test_signal_landscape_inherits_rectangular_layout(self) -> None:
        adapter = SignalLandscapeWorldVisualizationAdapter()
        assert adapter.cell_shape() == CellShape.RECTANGULAR
        layout = adapter.cell_layout(3, 3, 300.0, 300.0)
        assert len(layout.cell_centers) == 9

    def test_signal_landscape_registration(self) -> None:
        from axis.visualization.registry import (
            _clear_registries,
            register_world_visualization,
        )
        from axis.world.grid_2d.visualization import _grid_2d_vis_factory
        from axis.world.signal_landscape.visualization import (
            _signal_landscape_vis_factory,
        )
        _clear_registries()
        register_world_visualization("grid_2d", _grid_2d_vis_factory)
        register_world_visualization(
            "signal_landscape", _signal_landscape_vis_factory)
        result = resolve_world_adapter("signal_landscape", {})
        assert type(result).__name__ == \
            "SignalLandscapeWorldVisualizationAdapter"
