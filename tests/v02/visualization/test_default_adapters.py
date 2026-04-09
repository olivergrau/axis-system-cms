"""Tests for WP-V.1.3: Default and Null Adapters."""

from __future__ import annotations

from typing import Any

import pytest

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseStepTrace
from axis.sdk.world_types import CellView
from axis.visualization.adapters.default_world import DefaultWorldVisualizationAdapter
from axis.visualization.adapters.null_system import NullSystemVisualizationAdapter
from axis.visualization.types import CellColorConfig, CellLayout, CellShape


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_snapshot(width: int = 2, height: int = 2) -> WorldSnapshot:
    cell = CellView(cell_type="empty", resource_value=0.0)
    grid = tuple(tuple(cell for _ in range(width)) for _ in range(height))
    return WorldSnapshot(
        grid=grid, agent_position=Position(x=0, y=0),
        width=width, height=height,
    )


def _make_step_trace() -> BaseStepTrace:
    snap = _make_snapshot()
    return BaseStepTrace(
        timestep=0, action="stay",
        world_before=snap, world_after=snap,
        agent_position_before=Position(x=0, y=0),
        agent_position_after=Position(x=0, y=0),
        vitality_before=1.0, vitality_after=0.9,
        terminated=False,
    )


# ---------------------------------------------------------------------------
# DefaultWorldVisualizationAdapter
# ---------------------------------------------------------------------------


class TestDefaultWorldCellShape:

    def test_default_world_cell_shape(self) -> None:
        adapter = DefaultWorldVisualizationAdapter()
        assert adapter.cell_shape() == CellShape.RECTANGULAR


class TestDefaultWorldCellLayout:

    def test_default_world_cell_layout_dimensions(self) -> None:
        adapter = DefaultWorldVisualizationAdapter()
        layout = adapter.cell_layout(3, 2, 300.0, 200.0)
        assert layout.grid_width == 3
        assert layout.grid_height == 2
        assert layout.canvas_width == 300.0
        assert layout.canvas_height == 200.0

    def test_default_world_cell_layout_all_positions_present(self) -> None:
        adapter = DefaultWorldVisualizationAdapter()
        layout = adapter.cell_layout(3, 2, 300.0, 200.0)
        for y in range(2):
            for x in range(3):
                assert (x, y) in layout.cell_polygons
                assert (x, y) in layout.cell_centers
                assert (x, y) in layout.cell_bounding_boxes

    def test_default_world_cell_layout_center_values(self) -> None:
        adapter = DefaultWorldVisualizationAdapter()
        layout = adapter.cell_layout(2, 2, 200.0, 200.0)
        assert layout.cell_centers[(0, 0)] == (50.0, 50.0)
        assert layout.cell_centers[(1, 1)] == (150.0, 150.0)

    def test_default_world_cell_layout_polygon_vertices(self) -> None:
        adapter = DefaultWorldVisualizationAdapter()
        layout = adapter.cell_layout(2, 2, 200.0, 200.0)
        poly = layout.cell_polygons[(0, 0)]
        assert len(poly) == 4
        assert poly == ((0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0))

    def test_default_world_cell_layout_bounding_box(self) -> None:
        adapter = DefaultWorldVisualizationAdapter()
        layout = adapter.cell_layout(2, 2, 200.0, 200.0)
        bbox = layout.cell_bounding_boxes[(1, 0)]
        assert bbox == (100.0, 0.0, 100.0, 100.0)


class TestDefaultWorldColors:

    def test_default_world_cell_color_config_values(self) -> None:
        adapter = DefaultWorldVisualizationAdapter()
        cfg = adapter.cell_color_config()
        assert cfg.obstacle_color == (0, 0, 0)
        assert cfg.empty_color == (224, 224, 224)
        assert cfg.resource_color_min == (232, 245, 233)
        assert cfg.resource_color_max == (46, 125, 50)
        assert cfg.agent_color == (33, 150, 243)
        assert cfg.agent_selected_color == (33, 150, 243)
        assert cfg.selection_border_color == (255, 160, 0)
        assert cfg.grid_line_color == (158, 158, 158)


class TestDefaultWorldTopology:

    def test_default_world_topology_indicators_empty(self) -> None:
        adapter = DefaultWorldVisualizationAdapter()
        layout = adapter.cell_layout(2, 2, 200.0, 200.0)
        result = adapter.topology_indicators(_make_snapshot(), {}, layout)
        assert result == []


class TestDefaultWorldPixelToGrid:

    def test_default_world_pixel_to_grid_inside(self) -> None:
        adapter = DefaultWorldVisualizationAdapter()
        layout = adapter.cell_layout(3, 2, 300.0, 200.0)
        pos = adapter.pixel_to_grid(150.0, 50.0, layout)
        assert pos == Position(x=1, y=0)

    def test_default_world_pixel_to_grid_outside(self) -> None:
        adapter = DefaultWorldVisualizationAdapter()
        layout = adapter.cell_layout(3, 2, 300.0, 200.0)
        assert adapter.pixel_to_grid(-10.0, 50.0, layout) is None
        assert adapter.pixel_to_grid(350.0, 50.0, layout) is None

    def test_default_world_pixel_to_grid_corner(self) -> None:
        adapter = DefaultWorldVisualizationAdapter()
        layout = adapter.cell_layout(3, 2, 300.0, 200.0)
        pos = adapter.pixel_to_grid(0.0, 0.0, layout)
        assert pos == Position(x=0, y=0)


class TestDefaultWorldAgentMarker:

    def test_default_world_agent_marker_center(self) -> None:
        adapter = DefaultWorldVisualizationAdapter()
        layout = adapter.cell_layout(2, 2, 200.0, 200.0)
        center = adapter.agent_marker_center(Position(x=1, y=0), layout)
        assert center == (150.0, 50.0)


class TestDefaultWorldMetadata:

    def test_default_world_metadata_sections_empty(self) -> None:
        adapter = DefaultWorldVisualizationAdapter()
        assert adapter.world_metadata_sections({}) == []

    def test_default_world_format_world_info_none(self) -> None:
        adapter = DefaultWorldVisualizationAdapter()
        assert adapter.format_world_info({}) is None


# ---------------------------------------------------------------------------
# NullSystemVisualizationAdapter
# ---------------------------------------------------------------------------


class TestNullSystemPhases:

    def test_null_system_phase_names(self) -> None:
        adapter = NullSystemVisualizationAdapter()
        assert adapter.phase_names() == ["BEFORE", "AFTER_ACTION"]


class TestNullSystemVitality:

    def test_null_system_vitality_label(self) -> None:
        adapter = NullSystemVisualizationAdapter()
        assert adapter.vitality_label() == "Vitality"

    def test_null_system_format_vitality(self) -> None:
        adapter = NullSystemVisualizationAdapter()
        assert adapter.format_vitality(0.75, {}) == "75%"
        assert adapter.format_vitality(1.0, {}) == "100%"
        assert adapter.format_vitality(0.0, {}) == "0%"


class TestNullSystemAnalysis:

    def test_null_system_build_step_analysis_empty(self) -> None:
        adapter = NullSystemVisualizationAdapter()
        assert adapter.build_step_analysis(_make_step_trace()) == []

    def test_null_system_build_overlays_empty(self) -> None:
        adapter = NullSystemVisualizationAdapter()
        assert adapter.build_overlays(_make_step_trace()) == []

    def test_null_system_available_overlay_types_empty(self) -> None:
        adapter = NullSystemVisualizationAdapter()
        assert adapter.available_overlay_types() == []


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


class TestProtocolConformance:

    def test_default_world_satisfies_protocol(self) -> None:
        adapter = DefaultWorldVisualizationAdapter()
        for method in (
            "cell_shape", "cell_layout", "cell_color_config",
            "topology_indicators", "pixel_to_grid", "agent_marker_center",
            "world_metadata_sections", "format_world_info",
        ):
            assert hasattr(adapter, method)

    def test_null_system_satisfies_protocol(self) -> None:
        adapter = NullSystemVisualizationAdapter()
        for method in (
            "phase_names", "vitality_label", "format_vitality",
            "build_step_analysis", "build_overlays", "available_overlay_types",
        ):
            assert hasattr(adapter, method)
