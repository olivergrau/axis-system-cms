"""Tests for WP-V.4.2: OverlayRenderer (data-driven overlay dispatch)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest.mock import MagicMock, patch  # noqa: E402

import pytest  # noqa: E402

from PySide6.QtGui import QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from axis.visualization.types import (  # noqa: E402
    CellLayout,
    CellShape,
    OverlayData,
    OverlayItem,
)
from axis.visualization.ui.overlay_renderer import OverlayRenderer  # noqa: E402


# ---------------------------------------------------------------------------
# QApplication fixture (session-scoped)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_layout(width: int = 5, height: int = 5) -> CellLayout:
    """Create a simple rectangular CellLayout for testing."""
    cw = 400.0 / width
    ch = 400.0 / height
    centers = {}
    polygons = {}
    bboxes = {}
    for r in range(height):
        for c in range(width):
            x0 = c * cw
            y0 = r * ch
            centers[(c, r)] = (x0 + cw / 2, y0 + ch / 2)
            polygons[(c, r)] = (
                (x0, y0), (x0 + cw, y0),
                (x0 + cw, y0 + ch), (x0, y0 + ch),
            )
            bboxes[(c, r)] = (x0, y0, cw, ch)
    return CellLayout(
        cell_shape=CellShape.RECTANGULAR,
        grid_width=width, grid_height=height,
        canvas_width=400.0, canvas_height=400.0,
        cell_polygons=polygons,
        cell_centers=centers,
        cell_bounding_boxes=bboxes,
    )


def _make_item(
    item_type: str = "direction_arrow",
    position: tuple[int, int] = (1, 1),
    data: dict | None = None,
) -> OverlayItem:
    return OverlayItem(
        item_type=item_type,
        grid_position=position,
        data=data or {},
    )


def _make_overlay(
    overlay_type: str = "test",
    items: tuple[OverlayItem, ...] = (),
) -> OverlayData:
    return OverlayData(overlay_type=overlay_type, items=items)


def _qpainter_on_image(qapp) -> tuple[QImage, QPainter]:
    """Create a QImage and QPainter for testing."""
    img = QImage(400, 400, QImage.Format.Format_ARGB32)
    painter = QPainter(img)
    return img, painter


# ---------------------------------------------------------------------------
# Dispatch tests
# ---------------------------------------------------------------------------


class TestDispatch:

    def test_render_dispatches_direction_arrow(self, qapp) -> None:
        renderer = OverlayRenderer()
        layout = _make_layout()
        item = _make_item("direction_arrow", data={
                          "direction": "up", "length": 0.5})
        overlay = _make_overlay(items=(item,))

        # Track that _render_item dispatches correctly by verifying
        # the dispatch table lookup returns the expected method
        assert "direction_arrow" in renderer._RENDERERS
        # Verify actual rendering doesn't crash
        img, painter = _qpainter_on_image(qapp)
        try:
            renderer.render(painter, (overlay,), layout)
        finally:
            painter.end()

    def test_render_dispatches_all_known_types(self, qapp) -> None:
        renderer = OverlayRenderer()
        layout = _make_layout()
        known_types = [
            "direction_arrow", "center_dot", "center_ring", "bar_chart",
            "diamond_marker", "neighbor_dot", "x_marker", "radius_circle",
        ]
        # Verify all types are in the dispatch table
        for t in known_types:
            assert t in renderer._RENDERERS, f"{t} not in dispatch table"

    def test_render_skips_unknown_type(self, qapp) -> None:
        renderer = OverlayRenderer()
        layout = _make_layout()
        item = _make_item("unknown_future_type")
        overlay = _make_overlay(items=(item,))

        img, painter = _qpainter_on_image(qapp)
        try:
            # Should not crash
            renderer.render(painter, (overlay,), layout)
        finally:
            painter.end()


# ---------------------------------------------------------------------------
# Position resolution tests
# ---------------------------------------------------------------------------


class TestPositionResolution:

    def test_renderer_reads_cell_centers(self, qapp) -> None:
        renderer = OverlayRenderer()
        layout = _make_layout()
        # Position (1, 1) should map to a known center
        expected_center = layout.cell_centers[(1, 1)]
        assert expected_center is not None

        item = _make_item(
            "direction_arrow",
            position=(1, 1),
            data={"direction": "up", "length": 0.5},
        )
        img, painter = _qpainter_on_image(qapp)
        try:
            # Should not crash -- center exists
            renderer._render_item(painter, item, layout)
        finally:
            painter.end()

    def test_renderer_skips_missing_position(self, qapp) -> None:
        renderer = OverlayRenderer()
        layout = _make_layout()
        # Position (99, 99) is outside the grid
        item = _make_item(
            "direction_arrow",
            position=(99, 99),
            data={"direction": "up", "length": 0.5},
        )
        img, painter = _qpainter_on_image(qapp)
        try:
            # Should not crash -- position missing is gracefully handled
            renderer._render_item(painter, item, layout)
        finally:
            painter.end()


# ---------------------------------------------------------------------------
# Integration tests (with QImage-based QPainter)
# ---------------------------------------------------------------------------


class TestIntegration:

    def test_render_direction_arrow_no_crash(self, qapp) -> None:
        renderer = OverlayRenderer()
        layout = _make_layout()
        item = _make_item(
            "direction_arrow",
            data={"direction": "right", "length": 0.8},
        )
        img, painter = _qpainter_on_image(qapp)
        try:
            renderer.render(painter, (_make_overlay(items=(item,)),), layout)
        finally:
            painter.end()

    def test_render_center_dot_no_crash(self, qapp) -> None:
        renderer = OverlayRenderer()
        layout = _make_layout()
        item = _make_item("center_dot", data={"radius": 0.3})
        img, painter = _qpainter_on_image(qapp)
        try:
            renderer.render(painter, (_make_overlay(items=(item,)),), layout)
        finally:
            painter.end()

    def test_render_bar_chart_no_crash(self, qapp) -> None:
        renderer = OverlayRenderer()
        layout = _make_layout()
        item = _make_item(
            "bar_chart",
            data={
                "values": [0.3, 0.7, 0.1, 0.5, 0.9, 0.2],
                "labels": ["H", "F", "C", "S", "E", "R"],
            },
        )
        img, painter = _qpainter_on_image(qapp)
        try:
            renderer.render(painter, (_make_overlay(items=(item,)),), layout)
        finally:
            painter.end()

    def test_render_radius_circle_no_crash(self, qapp) -> None:
        renderer = OverlayRenderer()
        layout = _make_layout()
        item = _make_item(
            "radius_circle",
            data={"radius_cells": 2, "label": "Scan"},
        )
        img, painter = _qpainter_on_image(qapp)
        try:
            renderer.render(painter, (_make_overlay(items=(item,)),), layout)
        finally:
            painter.end()

    def test_render_x_marker_no_crash(self, qapp) -> None:
        renderer = OverlayRenderer()
        layout = _make_layout()
        item = _make_item("x_marker")
        img, painter = _qpainter_on_image(qapp)
        try:
            renderer.render(painter, (_make_overlay(items=(item,)),), layout)
        finally:
            painter.end()

    def test_render_diamond_marker_no_crash(self, qapp) -> None:
        renderer = OverlayRenderer()
        layout = _make_layout()
        item = _make_item("diamond_marker", data={"opacity": 0.7})
        img, painter = _qpainter_on_image(qapp)
        try:
            renderer.render(painter, (_make_overlay(items=(item,)),), layout)
        finally:
            painter.end()


# ---------------------------------------------------------------------------
# Overlay filtering tests
# ---------------------------------------------------------------------------


class TestOverlayFiltering:

    def test_render_multiple_overlays(self, qapp) -> None:
        renderer = OverlayRenderer()
        layout = _make_layout()
        overlay_a = _make_overlay(
            "type_a",
            items=(
                _make_item("direction_arrow", data={
                           "direction": "up", "length": 0.3}),
                _make_item("center_dot", data={"radius": 0.2}),
            ),
        )
        overlay_b = _make_overlay(
            "type_b",
            items=(
                _make_item("x_marker", position=(2, 2)),
                _make_item("center_ring", position=(
                    3, 3), data={"radius": 0.4}),
            ),
        )
        img, painter = _qpainter_on_image(qapp)
        try:
            renderer.render(painter, (overlay_a, overlay_b), layout)
        finally:
            painter.end()

    def test_render_empty_overlay_list(self, qapp) -> None:
        renderer = OverlayRenderer()
        layout = _make_layout()
        img, painter = _qpainter_on_image(qapp)
        try:
            renderer.render(painter, (), layout)
        finally:
            painter.end()


# ---------------------------------------------------------------------------
# Selected action highlight tests
# ---------------------------------------------------------------------------


class TestSelectedHighlight:

    def test_direction_arrow_selected_color(self, qapp) -> None:
        renderer = OverlayRenderer()
        layout = _make_layout()
        item = _make_item(
            "direction_arrow",
            data={"direction": "up", "length": 0.5, "is_selected": True},
        )
        img, painter = _qpainter_on_image(qapp)
        try:
            # Should not crash; we can't easily validate color but verify execution
            renderer._render_item(painter, item, layout)
        finally:
            painter.end()

    def test_center_dot_selected(self, qapp) -> None:
        renderer = OverlayRenderer()
        layout = _make_layout()
        item = _make_item(
            "center_dot",
            data={"radius": 0.2, "is_selected": True},
        )
        img, painter = _qpainter_on_image(qapp)
        try:
            renderer._render_item(painter, item, layout)
        finally:
            painter.end()
