"""Tests for WP-V.1.2: Adapter Protocols."""

from __future__ import annotations

from typing import Any

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseStepTrace
from axis.visualization.protocols import (
    SystemVisualizationAdapter,
    WorldVisualizationAdapter,
)
from axis.visualization.types import (
    AnalysisRow,
    AnalysisSection,
    CellColorConfig,
    CellLayout,
    CellShape,
    MetadataSection,
    OverlayData,
    OverlayTypeDeclaration,
    TopologyIndicator,
)


# ---------------------------------------------------------------------------
# Mock implementations
# ---------------------------------------------------------------------------


def _make_cell_layout() -> CellLayout:
    return CellLayout(
        cell_shape=CellShape.RECTANGULAR,
        grid_width=1, grid_height=1,
        canvas_width=100.0, canvas_height=100.0,
        cell_polygons={(0, 0): ((0, 0), (100, 0), (100, 100), (0, 100))},
        cell_centers={(0, 0): (50.0, 50.0)},
        cell_bounding_boxes={(0, 0): (0.0, 0.0, 100.0, 100.0)},
    )


class _MockWorldAdapter:
    """Mock that satisfies WorldVisualizationAdapter structurally."""

    def cell_shape(self) -> CellShape:
        return CellShape.RECTANGULAR

    def cell_layout(
        self, grid_width: int, grid_height: int,
        canvas_width: float, canvas_height: float,
    ) -> CellLayout:
        return _make_cell_layout()

    def cell_color_config(self) -> CellColorConfig:
        return CellColorConfig(
            obstacle_color=(0, 0, 0), empty_color=(200, 200, 200),
            resource_color_min=(200, 255, 200), resource_color_max=(0, 128, 0),
            agent_color=(0, 0, 255), agent_selected_color=(0, 0, 255),
            selection_border_color=(255, 165, 0), grid_line_color=(128, 128, 128),
        )

    def topology_indicators(
        self, world_snapshot: WorldSnapshot,
        world_data: dict[str, Any], cell_layout: CellLayout,
    ) -> list[TopologyIndicator]:
        return []

    def pixel_to_grid(
        self, pixel_x: float, pixel_y: float, cell_layout: CellLayout,
    ) -> Position | None:
        return Position(x=0, y=0)

    def agent_marker_center(
        self, grid_position: Position, cell_layout: CellLayout,
    ) -> tuple[float, float]:
        return (50.0, 50.0)

    def world_metadata_sections(
        self, world_data: dict[str, Any],
    ) -> list[MetadataSection]:
        return []

    def format_world_info(
        self, world_data: dict[str, Any],
    ) -> str | None:
        return None


class _MockSystemAdapter:
    """Mock that satisfies SystemVisualizationAdapter structurally."""

    def phase_names(self) -> list[str]:
        return ["BEFORE", "AFTER"]

    def vitality_label(self) -> str:
        return "Energy"

    def format_vitality(self, value: float, system_data: dict[str, Any]) -> str:
        return f"{value:.0%}"

    def build_step_analysis(self, step_trace: BaseStepTrace) -> list[AnalysisSection]:
        return []

    def build_overlays(self, step_trace: BaseStepTrace) -> list[OverlayData]:
        return []

    def available_overlay_types(self) -> list[OverlayTypeDeclaration]:
        return []


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestWorldAdapterProtocol:

    def test_mock_world_adapter_satisfies_protocol(self) -> None:
        adapter = _MockWorldAdapter()
        for method in (
            "cell_shape", "cell_layout", "cell_color_config",
            "topology_indicators", "pixel_to_grid", "agent_marker_center",
            "world_metadata_sections", "format_world_info",
        ):
            assert hasattr(adapter, method)

    def test_world_adapter_method_signatures(self) -> None:
        adapter = _MockWorldAdapter()
        layout = _make_cell_layout()
        from tests.sdk.test_replay_contract import _make_snapshot

        assert isinstance(adapter.cell_shape(), CellShape)
        assert isinstance(adapter.cell_layout(1, 1, 100.0, 100.0), CellLayout)
        assert isinstance(adapter.cell_color_config(), CellColorConfig)
        assert isinstance(adapter.topology_indicators(
            _make_snapshot(), {}, layout), list)
        result = adapter.pixel_to_grid(50.0, 50.0, layout)
        assert result is None or isinstance(result, Position)
        assert isinstance(adapter.agent_marker_center(
            Position(x=0, y=0), layout), tuple)
        assert isinstance(adapter.world_metadata_sections({}), list)
        info = adapter.format_world_info({})
        assert info is None or isinstance(info, str)

    def test_world_adapter_independence_from_system(self) -> None:
        import inspect
        src = inspect.getsource(WorldVisualizationAdapter)
        assert "SystemVisualizationAdapter" not in src


class TestSystemAdapterProtocol:

    def test_mock_system_adapter_satisfies_protocol(self) -> None:
        adapter = _MockSystemAdapter()
        for method in (
            "phase_names", "vitality_label", "format_vitality",
            "build_step_analysis", "build_overlays", "available_overlay_types",
        ):
            assert hasattr(adapter, method)

    def test_system_adapter_method_signatures(self) -> None:
        adapter = _MockSystemAdapter()
        assert isinstance(adapter.phase_names(), list)
        assert isinstance(adapter.vitality_label(), str)
        assert isinstance(adapter.format_vitality(0.5, {}), str)
        assert isinstance(adapter.available_overlay_types(), list)


class TestProtocolImports:

    def test_protocols_importable(self) -> None:
        from axis.visualization.protocols import (  # noqa: F401
            SystemVisualizationAdapter,
            WorldVisualizationAdapter,
        )
