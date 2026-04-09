"""Tests for WP-V.5.2: Overlay Rendering Suite.

Render overlays from real system adapter output through OverlayRenderer.
Requires PySide6 (QApplication, QImage, QPainter).
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from axis.sdk.position import Position  # noqa: E402
from axis.visualization.types import CellLayout, CellShape  # noqa: E402
from axis.visualization.ui.overlay_renderer import OverlayRenderer  # noqa: E402

from tests.visualization.adapter_fixtures import (  # noqa: E402
    make_step_trace,
    sample_system_a_data,
    sample_system_b_data,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _make_layout(width: int = 5, height: int = 5) -> CellLayout:
    """Build a simple rectangular CellLayout."""
    cw, ch = 500.0, 500.0
    cell_w = cw / width
    cell_h = ch / height
    polygons = {}
    centers = {}
    bboxes = {}
    for x in range(width):
        for y in range(height):
            x0 = x * cell_w
            y0 = y * cell_h
            polygons[(x, y)] = (
                (x0, y0), (x0 + cell_w, y0),
                (x0 + cell_w, y0 + cell_h), (x0, y0 + cell_h),
            )
            centers[(x, y)] = (x0 + cell_w / 2, y0 + cell_h / 2)
            bboxes[(x, y)] = (x0, y0, cell_w, cell_h)
    return CellLayout(
        cell_shape=CellShape.RECTANGULAR,
        grid_width=width, grid_height=height,
        canvas_width=cw, canvas_height=ch,
        cell_polygons=polygons,
        cell_centers=centers,
        cell_bounding_boxes=bboxes,
    )


def _render_overlays(overlays, layout, qapp):
    """Render overlay data onto a QImage and return success."""
    renderer = OverlayRenderer()
    image = QImage(500, 500, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.white)
    painter = QPainter(image)
    try:
        renderer.render(painter, tuple(overlays), layout)
    finally:
        painter.end()
    return True


# ---------------------------------------------------------------------------
# System A overlay rendering
# ---------------------------------------------------------------------------


class TestSystemAOverlayRendering:

    def _overlays(self):
        from axis.systems.system_a.visualization import (
            SystemAVisualizationAdapter,
        )
        adapter = SystemAVisualizationAdapter(max_energy=100.0)
        step = make_step_trace(
            action="consume",
            agent_pos_before=Position(x=2, y=2),
            agent_pos_after=Position(x=2, y=2),
            system_data=sample_system_a_data(),
        )
        return adapter.build_overlays(step)

    def test_render_all_overlays(self, qapp) -> None:
        assert _render_overlays(self._overlays(), _make_layout(), qapp)

    def test_render_action_preference(self, qapp) -> None:
        overlays = [o for o in self._overlays()
                    if o.overlay_type == "action_preference"]
        assert _render_overlays(overlays, _make_layout(), qapp)

    def test_render_drive_contribution(self, qapp) -> None:
        overlays = [o for o in self._overlays()
                    if o.overlay_type == "drive_contribution"]
        assert _render_overlays(overlays, _make_layout(), qapp)

    def test_render_consumption_opportunity(self, qapp) -> None:
        overlays = [o for o in self._overlays()
                    if o.overlay_type == "consumption_opportunity"]
        assert _render_overlays(overlays, _make_layout(), qapp)

    def test_direction_arrow_items_rendered(self, qapp) -> None:
        overlays = self._overlays()
        arrows = [i for o in overlays for i in o.items
                  if i.item_type == "direction_arrow"]
        assert len(arrows) >= 4

    def test_center_dot_items_rendered(self, qapp) -> None:
        overlays = self._overlays()
        dots = [i for o in overlays for i in o.items
                if i.item_type == "center_dot"]
        assert len(dots) >= 1

    def test_bar_chart_item_rendered(self, qapp) -> None:
        overlays = self._overlays()
        bars = [i for o in overlays for i in o.items
                if i.item_type == "bar_chart"]
        assert len(bars) == 1


# ---------------------------------------------------------------------------
# System B overlay rendering
# ---------------------------------------------------------------------------


class TestSystemBOverlayRendering:

    def _overlays(self):
        from axis.systems.system_b.visualization import (
            SystemBVisualizationAdapter,
        )
        adapter = SystemBVisualizationAdapter(max_energy=100.0)
        step = make_step_trace(
            action="right",
            agent_pos_before=Position(x=2, y=2),
            agent_pos_after=Position(x=3, y=2),
            system_data=sample_system_b_data(),
        )
        return adapter.build_overlays(step)

    def test_render_all_overlays(self, qapp) -> None:
        assert _render_overlays(self._overlays(), _make_layout(), qapp)

    def test_render_action_weights(self, qapp) -> None:
        overlays = [o for o in self._overlays()
                    if o.overlay_type == "action_weights"]
        assert _render_overlays(overlays, _make_layout(), qapp)

    def test_render_scan_result(self, qapp) -> None:
        overlays = [o for o in self._overlays()
                    if o.overlay_type == "scan_result"]
        assert _render_overlays(overlays, _make_layout(), qapp)

    def test_radius_circle_present(self, qapp) -> None:
        overlays = self._overlays()
        circles = [i for o in overlays for i in o.items
                   if i.item_type == "radius_circle"]
        assert len(circles) == 1

    def test_direction_arrows_present(self, qapp) -> None:
        overlays = self._overlays()
        arrows = [i for o in overlays for i in o.items
                  if i.item_type == "direction_arrow"]
        assert len(arrows) == 4


# ---------------------------------------------------------------------------
# Cross-cutting rendering
# ---------------------------------------------------------------------------


class TestOverlayRenderingCrossCutting:

    def test_all_dispatch_item_types_exist(self, qapp) -> None:
        expected = {
            "direction_arrow", "center_dot", "center_ring",
            "bar_chart", "diamond_marker", "neighbor_dot",
            "x_marker", "radius_circle",
        }
        assert expected == set(OverlayRenderer._RENDERERS.keys())

    def test_unknown_type_skipped(self, qapp) -> None:
        from axis.visualization.types import OverlayData, OverlayItem
        overlay = OverlayData(
            overlay_type="test",
            items=(OverlayItem(
                item_type="nonexistent_type",
                grid_position=(0, 0),
                data={},
            ),),
        )
        assert _render_overlays([overlay], _make_layout(), qapp)

    def test_out_of_bounds_position_skipped(self, qapp) -> None:
        from axis.visualization.types import OverlayData, OverlayItem
        overlay = OverlayData(
            overlay_type="test",
            items=(OverlayItem(
                item_type="center_dot",
                grid_position=(99, 99),
                data={"radius": 0.5, "is_selected": False},
            ),),
        )
        assert _render_overlays([overlay], _make_layout(), qapp)

    def test_empty_overlay_list(self, qapp) -> None:
        assert _render_overlays([], _make_layout(), qapp)

    def test_mixed_system_overlays(self, qapp) -> None:
        from axis.systems.system_a.visualization import (
            SystemAVisualizationAdapter,
        )
        from axis.systems.system_b.visualization import (
            SystemBVisualizationAdapter,
        )
        step_a = make_step_trace(
            action="consume",
            agent_pos_before=Position(x=2, y=2),
            agent_pos_after=Position(x=2, y=2),
            system_data=sample_system_a_data(),
        )
        step_b = make_step_trace(
            action="right",
            agent_pos_before=Position(x=2, y=2),
            agent_pos_after=Position(x=3, y=2),
            system_data=sample_system_b_data(),
        )
        overlays_a = SystemAVisualizationAdapter(
            max_energy=100.0).build_overlays(step_a)
        overlays_b = SystemBVisualizationAdapter(
            max_energy=100.0).build_overlays(step_b)
        combined = list(overlays_a) + list(overlays_b)
        assert _render_overlays(combined, _make_layout(), qapp)
