"""Tests for WP-V.1.1: Visualization Supporting Types."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from axis.visualization.types import (
    AnalysisRow,
    AnalysisSection,
    CellColorConfig,
    CellLayout,
    CellShape,
    MetadataSection,
    OverlayData,
    OverlayItem,
    OverlayTypeDeclaration,
    TopologyIndicator,
)


# ---------------------------------------------------------------------------
# CellShape
# ---------------------------------------------------------------------------


class TestCellShape:

    def test_cell_shape_values(self) -> None:
        assert CellShape.RECTANGULAR.value == "rectangular"
        assert CellShape.HEXAGONAL.value == "hexagonal"


# ---------------------------------------------------------------------------
# CellLayout
# ---------------------------------------------------------------------------


def _make_cell_layout_2x2() -> CellLayout:
    """Build a 2x2 rectangular layout at 200x200 canvas."""
    polygons: dict[tuple[int, int], tuple[tuple[float, float], ...]] = {}
    centers: dict[tuple[int, int], tuple[float, float]] = {}
    bboxes: dict[tuple[int, int], tuple[float, float, float, float]] = {}
    for y in range(2):
        for x in range(2):
            x0, y0 = x * 100.0, y * 100.0
            polygons[(x, y)] = ((x0, y0), (x0 + 100, y0),
                                (x0 + 100, y0 + 100), (x0, y0 + 100))
            centers[(x, y)] = (x0 + 50, y0 + 50)
            bboxes[(x, y)] = (x0, y0, 100.0, 100.0)
    return CellLayout(
        cell_shape=CellShape.RECTANGULAR,
        grid_width=2,
        grid_height=2,
        canvas_width=200.0,
        canvas_height=200.0,
        cell_polygons=polygons,
        cell_centers=centers,
        cell_bounding_boxes=bboxes,
    )


class TestCellLayout:

    def test_cell_layout_construction(self) -> None:
        layout = _make_cell_layout_2x2()
        assert layout.grid_width == 2
        assert layout.grid_height == 2
        assert len(layout.cell_centers) == 4
        assert layout.cell_centers[(0, 0)] == (50.0, 50.0)

    def test_cell_layout_frozen(self) -> None:
        layout = _make_cell_layout_2x2()
        with pytest.raises(ValidationError):
            layout.grid_width = 5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# CellColorConfig
# ---------------------------------------------------------------------------


class TestCellColorConfig:

    def test_cell_color_config_construction(self) -> None:
        cfg = CellColorConfig(
            obstacle_color=(0, 0, 0),
            empty_color=(224, 224, 224),
            resource_color_min=(232, 245, 233),
            resource_color_max=(46, 125, 50),
            agent_color=(33, 150, 243),
            agent_selected_color=(33, 150, 243),
            selection_border_color=(255, 160, 0),
            grid_line_color=(158, 158, 158),
        )
        assert cfg.obstacle_color == (0, 0, 0)
        assert cfg.agent_color == (33, 150, 243)
        assert cfg.grid_line_color == (158, 158, 158)

    def test_cell_color_config_round_trip(self) -> None:
        cfg = CellColorConfig(
            obstacle_color=(0, 0, 0),
            empty_color=(224, 224, 224),
            resource_color_min=(232, 245, 233),
            resource_color_max=(46, 125, 50),
            agent_color=(33, 150, 243),
            agent_selected_color=(33, 150, 243),
            selection_border_color=(255, 160, 0),
            grid_line_color=(158, 158, 158),
        )
        dumped = cfg.model_dump()
        reconstructed = CellColorConfig(**dumped)
        assert reconstructed == cfg


# ---------------------------------------------------------------------------
# TopologyIndicator
# ---------------------------------------------------------------------------


class TestTopologyIndicator:

    def test_topology_indicator_construction(self) -> None:
        ti = TopologyIndicator(
            indicator_type="wrap_edge",
            position=(10.0, 20.0),
            data={"direction": "horizontal"},
        )
        assert ti.indicator_type == "wrap_edge"
        assert ti.position == (10.0, 20.0)
        assert ti.data["direction"] == "horizontal"

    def test_topology_indicator_round_trip(self) -> None:
        ti = TopologyIndicator(
            indicator_type="wrap_edge",
            position=(10.0, 20.0),
            data={"side": "left"},
        )
        dumped = ti.model_dump()
        reconstructed = TopologyIndicator(**dumped)
        assert reconstructed == ti


# ---------------------------------------------------------------------------
# AnalysisRow / AnalysisSection / MetadataSection
# ---------------------------------------------------------------------------


class TestAnalysisRow:

    def test_analysis_row_simple(self) -> None:
        row = AnalysisRow(label="Energy", value="45.0")
        assert row.label == "Energy"
        assert row.sub_rows is None

    def test_analysis_row_nested(self) -> None:
        children = (
            AnalysisRow(label="Sub1", value="a"),
            AnalysisRow(label="Sub2", value="b"),
        )
        row = AnalysisRow(label="Parent", value="summary", sub_rows=children)
        assert len(row.sub_rows) == 2  # type: ignore[arg-type]
        assert row.sub_rows[1].value == "b"  # type: ignore[index]


class TestAnalysisSection:

    def test_analysis_section_construction(self) -> None:
        rows = tuple(AnalysisRow(
            label=f"R{i}", value=str(i)) for i in range(3))
        section = AnalysisSection(title="Decision", rows=rows)
        assert section.title == "Decision"
        assert len(section.rows) == 3

    def test_analysis_section_round_trip(self) -> None:
        child = AnalysisRow(label="Sub", value="1")
        parent = AnalysisRow(label="Top", value="x", sub_rows=(child,))
        section = AnalysisSection(title="Test", rows=(parent,))
        dumped = section.model_dump()
        reconstructed = AnalysisSection(**dumped)
        assert reconstructed == section


class TestMetadataSection:

    def test_metadata_section_construction(self) -> None:
        rows = (AnalysisRow(label="Hotspots", value="3"),)
        ms = MetadataSection(title="World Info", rows=rows)
        assert ms.title == "World Info"
        assert len(ms.rows) == 1


# ---------------------------------------------------------------------------
# Overlay types
# ---------------------------------------------------------------------------


class TestOverlayTypeDeclaration:

    def test_overlay_type_declaration_construction(self) -> None:
        decl = OverlayTypeDeclaration(
            key="action_weights",
            label="Action Weights",
            description="Shows action probability distribution",
        )
        assert decl.key == "action_weights"
        assert decl.label == "Action Weights"


class TestOverlayItem:

    def test_overlay_item_construction(self) -> None:
        item = OverlayItem(
            item_type="direction_arrow",
            grid_position=(3, 2),
            data={"angle": 90, "weight": 0.5},
        )
        assert item.item_type == "direction_arrow"
        assert item.grid_position == (3, 2)


class TestOverlayData:

    def test_overlay_data_construction(self) -> None:
        items = (
            OverlayItem(item_type="arrow", grid_position=(0, 0), data={}),
            OverlayItem(item_type="arrow", grid_position=(1, 0), data={}),
        )
        od = OverlayData(overlay_type="action_weights", items=items)
        assert od.overlay_type == "action_weights"
        assert len(od.items) == 2

    def test_overlay_data_round_trip(self) -> None:
        items = (OverlayItem(item_type="dot",
                 grid_position=(0, 0), data={"v": 1}),)
        od = OverlayData(overlay_type="signals", items=items)
        dumped = od.model_dump()
        reconstructed = OverlayData(**dumped)
        assert reconstructed == od


# ---------------------------------------------------------------------------
# Import verification
# ---------------------------------------------------------------------------


class TestImports:

    def test_import_from_types_module(self) -> None:
        from axis.visualization.types import (  # noqa: F401
            AnalysisRow,
            AnalysisSection,
            CellColorConfig,
            CellLayout,
            CellShape,
            MetadataSection,
            OverlayData,
            OverlayItem,
            OverlayTypeDeclaration,
            TopologyIndicator,
        )
