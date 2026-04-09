"""Tests for WP-V.2.5: System B Visualization Adapter."""

from __future__ import annotations

from typing import Any

import pytest

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseStepTrace
from axis.sdk.world_types import CellView
from axis.visualization.registry import _clear_registries, resolve_system_adapter

import axis.systems.system_b.visualization  # noqa: F401 -- trigger registration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_snapshot() -> WorldSnapshot:
    cell = CellView(cell_type="empty", resource_value=0.0)
    grid = tuple(tuple(cell for _ in range(5)) for _ in range(5))
    return WorldSnapshot(
        grid=grid, agent_position=Position(x=2, y=2), width=5, height=5)


def _sample_system_data() -> dict[str, Any]:
    return {
        "decision_data": {
            "weights": [1.2, 0.8, 0.5, 1.5, 0.3, 0.2],
            "probabilities": [0.25, 0.15, 0.10, 0.35, 0.08, 0.07],
            "last_scan": {
                "total_resource": 2.750,
                "cell_count": 9,
            },
        },
        "trace_data": {
            "energy_before": 40.00,
            "energy_after": 38.50,
            "energy_delta": -1.50,
            "action_cost": 1.50,
            "scan_total": 2.750,
        },
    }


def _sample_step_trace() -> BaseStepTrace:
    snap = _make_snapshot()
    return BaseStepTrace(
        timestep=3,
        action="right",
        world_before=snap,
        world_after=snap,
        agent_position_before=Position(x=2, y=2),
        agent_position_after=Position(x=3, y=2),
        vitality_before=0.80,
        vitality_after=0.77,
        terminated=False,
        system_data=_sample_system_data(),
    )


def _adapter(max_energy: float = 100.0):
    from axis.systems.system_b.visualization import SystemBVisualizationAdapter
    return SystemBVisualizationAdapter(max_energy=max_energy)


# ---------------------------------------------------------------------------
# Phase and vitality tests
# ---------------------------------------------------------------------------


class TestPhaseAndVitality:

    def test_phase_names(self) -> None:
        assert _adapter().phase_names() == ["BEFORE", "AFTER_ACTION"]

    def test_vitality_label(self) -> None:
        assert _adapter().vitality_label() == "Energy"

    def test_format_vitality(self) -> None:
        a = _adapter(max_energy=50.0)
        assert a.format_vitality(0.8, {}) == "40.00 / 50.00"


# ---------------------------------------------------------------------------
# Analysis section tests
# ---------------------------------------------------------------------------


class TestAnalysisSections:

    def test_build_step_analysis_section_count(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        assert len(sections) == 5

    def test_step_overview_section(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        s = sections[0]
        assert s.title == "Step Overview"
        by_label = {r.label: r.value for r in s.rows}
        assert by_label["Energy Before"] == "40.00"
        assert by_label["Energy After"] == "38.50"
        assert by_label["Action Cost"] == "1.50"

    def test_decision_weights_section(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        s = sections[1]
        assert s.title == "Decision Weights"
        assert len(s.rows) == 6
        assert s.rows[0].label == "Up"

    def test_probabilities_section(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        s = sections[2]
        assert s.title == "Probabilities"
        assert len(s.rows) == 6

    def test_last_scan_section(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        s = sections[3]
        assert s.title == "Last Scan"
        by_label = {r.label: r.value for r in s.rows}
        assert "2.750" in by_label["Total Resource"]
        assert by_label["Cell Count"] == "9"

    def test_last_scan_section_no_scan(self) -> None:
        # Build a trace without last_scan
        sd = _sample_system_data()
        del sd["decision_data"]["last_scan"]
        snap = _make_snapshot()
        trace = BaseStepTrace(
            timestep=0, action="stay",
            world_before=snap, world_after=snap,
            agent_position_before=Position(x=2, y=2),
            agent_position_after=Position(x=2, y=2),
            vitality_before=1.0, vitality_after=0.9,
            terminated=False, system_data=sd,
        )
        sections = _adapter().build_step_analysis(trace)
        s = sections[3]
        assert s.title == "Last Scan"
        assert any("No scan" in r.value for r in s.rows)

    def test_outcome_section(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        s = sections[4]
        assert s.title == "Outcome"
        by_label = {r.label: r.value for r in s.rows}
        assert by_label["Action"] == "right"
        assert "2.750" in by_label["Scan Total"]
        assert by_label["Terminated"] == "No"


# ---------------------------------------------------------------------------
# Overlay tests
# ---------------------------------------------------------------------------


class TestOverlays:

    def test_build_overlays_count(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        assert len(overlays) == 2

    def test_action_weights_overlay(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        assert overlays[0].overlay_type == "action_weights"

    def test_action_weights_direction_arrows(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        arrows = [i for i in overlays[0].items
                  if i.item_type == "direction_arrow"]
        assert len(arrows) == 4

    def test_action_weights_selected_marked(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        arrows = [i for i in overlays[0].items
                  if i.item_type == "direction_arrow"]
        selected = [a for a in arrows if a.data["is_selected"]]
        assert len(selected) == 1
        assert selected[0].data["direction"] == "right"

    def test_scan_result_overlay(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        assert overlays[1].overlay_type == "scan_result"

    def test_scan_result_radius_circle(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        circles = [i for i in overlays[1].items
                   if i.item_type == "radius_circle"]
        assert len(circles) == 1
        assert circles[0].data["radius_cells"] == 1

    def test_scan_result_label(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        circle = overlays[1].items[0]
        assert "2.75" in circle.data["label"]


# ---------------------------------------------------------------------------
# Overlay declaration tests
# ---------------------------------------------------------------------------


class TestOverlayDeclarations:

    def test_available_overlay_types(self) -> None:
        decls = _adapter().available_overlay_types()
        assert len(decls) == 2
        keys = {d.key for d in decls}
        assert keys == {"action_weights", "scan_result"}

    def test_overlay_keys_match_data(self) -> None:
        adapter = _adapter()
        decl_keys = {d.key for d in adapter.available_overlay_types()}
        overlay_types = {
            o.overlay_type
            for o in adapter.build_overlays(_sample_step_trace())
        }
        assert decl_keys == overlay_types


# ---------------------------------------------------------------------------
# Registration test
# ---------------------------------------------------------------------------


class TestRegistration:

    def test_system_b_registration(self) -> None:
        result = resolve_system_adapter("system_b")
        assert hasattr(result, "phase_names")
        assert hasattr(result, "build_overlays")
