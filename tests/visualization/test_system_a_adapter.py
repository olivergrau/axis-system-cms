"""Tests for WP-V.2.4: System A Visualization Adapter."""

from __future__ import annotations

from typing import Any

import pytest

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseStepTrace
from axis.sdk.world_types import CellView
from axis.visualization.registry import _clear_registries, resolve_system_adapter


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
            "observation": {
                "current": {"traversability": 1.0, "resource": 0.5},
                "up":      {"traversability": 1.0, "resource": 0.3},
                "down":    {"traversability": 0.0, "resource": 0.0},
                "left":    {"traversability": 1.0, "resource": 0.0},
                "right":   {"traversability": 1.0, "resource": 0.8},
            },
            "drive": {
                "activation": 0.7500,
                "action_contributions": (0.1, 0.05, 0.02, 0.3, 0.5, 0.03),
            },
            "policy": {
                "raw_contributions": (0.2, 0.1, 0.05, 0.35, 0.6, 0.1),
                "admissibility_mask": (True, False, True, True, True, True),
                "masked_contributions": (
                    0.2, float("-inf"), 0.05, 0.35, 0.6, 0.1),
                "probabilities": (0.12, 0.0, 0.08, 0.25, 0.45, 0.10),
                "selected_action": "consume",
                "temperature": 1.50,
                "selection_mode": "sample",
            },
        },
        "trace_data": {
            "energy_before": 45.00,
            "energy_after": 43.50,
            "energy_delta": -1.50,
            "action_cost": 2.00,
            "energy_gain": 0.50,
            "buffer_entries_before": 3,
            "buffer_entries_after": 4,
            "buffer_capacity": 5,
            "buffer_snapshot": [
                {
                    "timestep": 2, "current_res": 0.0, "up_res": 0.0,
                    "down_res": 0.0, "left_res": 0.0, "right_res": 0.0,
                    "current_trav": 1.0, "up_trav": 1.0,
                    "down_trav": 0.0, "left_trav": 1.0, "right_trav": 1.0,
                },
                {
                    "timestep": 3, "current_res": 0.3, "up_res": 0.0,
                    "down_res": 0.0, "left_res": 0.0, "right_res": 0.5,
                    "current_trav": 1.0, "up_trav": 1.0,
                    "down_trav": 0.0, "left_trav": 1.0, "right_trav": 1.0,
                },
                {
                    "timestep": 4, "current_res": 0.5, "up_res": 0.3,
                    "down_res": 0.0, "left_res": 0.0, "right_res": 0.8,
                    "current_trav": 1.0, "up_trav": 1.0,
                    "down_trav": 0.0, "left_trav": 1.0, "right_trav": 1.0,
                },
                {
                    "timestep": 5, "current_res": 0.5, "up_res": 0.3,
                    "down_res": 0.0, "left_res": 0.0, "right_res": 0.8,
                    "current_trav": 1.0, "up_trav": 1.0,
                    "down_trav": 0.0, "left_trav": 1.0, "right_trav": 1.0,
                },
            ],
        },
    }


def _sample_step_trace() -> BaseStepTrace:
    snap = _make_snapshot()
    return BaseStepTrace(
        timestep=5,
        action="consume",
        world_before=snap,
        world_after=snap,
        agent_position_before=Position(x=2, y=2),
        agent_position_after=Position(x=2, y=2),
        vitality_before=0.45,
        vitality_after=0.435,
        terminated=False,
        system_data=_sample_system_data(),
    )


import axis.systems.system_a.visualization  # noqa: F401 -- trigger registration


def _adapter():
    from axis.systems.system_a.visualization import SystemAVisualizationAdapter
    return SystemAVisualizationAdapter(max_energy=100.0)


# ---------------------------------------------------------------------------
# Phase and vitality tests
# ---------------------------------------------------------------------------


class TestPhaseAndVitality:

    def test_phase_names(self) -> None:
        assert _adapter().phase_names() == [
            "BEFORE", "AFTER_REGEN", "AFTER_ACTION"]

    def test_vitality_label(self) -> None:
        assert _adapter().vitality_label() == "Energy"

    def test_format_vitality(self) -> None:
        assert _adapter().format_vitality(0.5, {}) == "50.00 / 100.00"

    def test_format_vitality_full(self) -> None:
        assert _adapter().format_vitality(1.0, {}) == "100.00 / 100.00"


# ---------------------------------------------------------------------------
# Analysis section tests
# ---------------------------------------------------------------------------


class TestAnalysisSections:

    def test_build_step_analysis_section_count(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        assert len(sections) == 6

    def test_step_overview_section(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        s = sections[0]
        assert s.title == "Step Overview"
        labels = [r.label for r in s.rows]
        assert "Timestep" in labels
        assert "Energy Before" in labels
        assert "Energy After" in labels
        assert "Energy Delta" in labels
        # Check formatted values
        by_label = {r.label: r.value for r in s.rows}
        assert by_label["Energy Before"] == "45.00"
        assert by_label["Energy Delta"] == "-1.50"

    def test_observation_section(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        s = sections[1]
        assert s.title == "Observation"
        assert len(s.rows) == 5

    def test_observation_traversability_labels(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        s = sections[1]
        by_label = {r.label: r.value for r in s.rows}
        assert "traversable" in by_label["Up"]
        assert "blocked" in by_label["Down"]

    def test_observation_buffer_section(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        s = sections[2]
        assert s.title == "Observation Buffer (4/5)"
        # 4 buffer entries → 4 rows
        assert len(s.rows) == 4

    def test_observation_buffer_row_labels(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        s = sections[2]
        labels = [r.label for r in s.rows]
        # Most recent first
        assert labels[0] == "t=5"
        assert labels[-1] == "t=2"

    def test_observation_buffer_row_values(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        s = sections[2]
        # Most recent entry (t=5) has resource values
        assert "res=" in s.rows[0].value
        assert "0.50" in s.rows[0].value  # current_res

    def test_observation_buffer_traversability_sub_rows(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        s = sections[2]
        assert s.rows[0].sub_rows is not None
        assert len(s.rows[0].sub_rows) == 1
        assert s.rows[0].sub_rows[0].label == "Traversability"

    def test_observation_buffer_empty(self) -> None:
        data = _sample_system_data()
        data["trace_data"]["buffer_snapshot"] = []
        data["trace_data"]["buffer_capacity"] = 5
        snap = _make_snapshot()
        step_trace = BaseStepTrace(
            timestep=0, action="stay",
            world_before=snap, world_after=snap,
            agent_position_before=Position(x=2, y=2),
            agent_position_after=Position(x=2, y=2),
            vitality_before=0.45, vitality_after=0.435,
            terminated=False, system_data=data,
        )
        sections = _adapter().build_step_analysis(step_trace)
        s = sections[2]
        assert s.title == "Observation Buffer (0/5)"
        assert len(s.rows) == 1
        assert s.rows[0].label == "(empty)"

    def test_drive_output_section(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        s = sections[3]
        assert s.title == "Drive Output"
        by_label = {r.label: r.value for r in s.rows}
        assert by_label["Activation"] == "0.7500"
        # 6 action contributions + 1 activation = 7 rows
        assert len(s.rows) == 7

    def test_decision_pipeline_section(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        s = sections[4]
        assert s.title == "Decision Pipeline"
        labels = [r.label for r in s.rows]
        assert "Temperature" in labels
        assert "Selection Mode" in labels
        assert "Selected" in labels
        # Check sub_rows on action rows
        action_rows = [r for r in s.rows if r.sub_rows is not None]
        assert len(action_rows) == 6

    def test_outcome_section(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        s = sections[5]
        assert s.title == "Outcome"
        by_label = {r.label: r.value for r in s.rows}
        assert by_label["Moved"] == "No"
        assert by_label["Position"] == "(2, 2)"
        assert by_label["Action Cost"] == "2.00"
        assert by_label["Energy Gain"] == "0.50"
        assert by_label["Terminated"] == "No"


# ---------------------------------------------------------------------------
# Overlay tests
# ---------------------------------------------------------------------------


class TestOverlays:

    def test_build_overlays_count(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        assert len(overlays) == 4

    def test_action_preference_overlay_type(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        assert overlays[0].overlay_type == "action_preference"

    def test_action_preference_has_direction_arrows(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        arrows = [i for i in overlays[0].items
                  if i.item_type == "direction_arrow"]
        assert len(arrows) == 4

    def test_action_preference_selected_action_marked(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        items = overlays[0].items
        # selected_action is "consume", not a direction, so no arrow is_selected
        # but center_dot should have is_selected=True
        dot = [i for i in items if i.item_type == "center_dot"]
        assert len(dot) == 1
        assert dot[0].data["is_selected"] is True

    def test_action_preference_consume_dot(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        dots = [i for i in overlays[0].items
                if i.item_type == "center_dot"]
        assert len(dots) == 1
        assert dots[0].data["radius"] == 0.45

    def test_action_preference_stay_ring(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        rings = [i for i in overlays[0].items
                 if i.item_type == "center_ring"]
        assert len(rings) == 1
        assert rings[0].data["radius"] == 0.10

    def test_drive_contribution_overlay(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        assert overlays[1].overlay_type == "drive_contribution"
        assert len(overlays[1].items) == 1
        assert overlays[1].items[0].item_type == "bar_chart"

    def test_drive_contribution_bar_chart_data(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        data = overlays[1].items[0].data
        assert data["activation"] == 0.75
        assert len(data["values"]) == 6
        assert len(data["labels"]) == 6

    def test_consumption_opportunity_overlay(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        assert overlays[2].overlay_type == "consumption_opportunity"

    def test_consumption_opportunity_diamond_on_resource(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        diamonds = [i for i in overlays[2].items
                    if i.item_type == "diamond_marker"]
        assert len(diamonds) == 1
        assert diamonds[0].data["opacity"] == 0.5

    def test_consumption_opportunity_neighbor_dots(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        dots = [i for i in overlays[2].items
                if i.item_type == "neighbor_dot"]
        # up, left, right are traversable
        assert len(dots) == 3

    def test_consumption_opportunity_x_marker_for_blocked(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        markers = [i for i in overlays[2].items
                   if i.item_type == "x_marker"]
        # down is blocked
        assert len(markers) == 1

    def test_buffer_saturation_overlay(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        bs = [o for o in overlays if o.overlay_type == "buffer_saturation"][0]
        assert len(bs.items) == 1
        assert bs.items[0].item_type == "saturation_ring"

    def test_buffer_saturation_data_keys(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        bs = [o for o in overlays if o.overlay_type == "buffer_saturation"][0]
        data = bs.items[0].data
        assert "saturation" in data
        assert "fill_ratio" in data
        assert 0.0 <= data["saturation"] <= 1.0
        assert 0.0 <= data["fill_ratio"] <= 1.0

    def test_buffer_saturation_fill_ratio(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        bs = [o for o in overlays if o.overlay_type == "buffer_saturation"][0]
        # 4 entries / 5 capacity = 0.8
        assert bs.items[0].data["fill_ratio"] == pytest.approx(0.8)


# ---------------------------------------------------------------------------
# Overlay declaration tests
# ---------------------------------------------------------------------------


class TestOverlayDeclarations:

    def test_available_overlay_types(self) -> None:
        decls = _adapter().available_overlay_types()
        assert len(decls) == 4
        keys = {d.key for d in decls}
        assert keys == {
            "action_preference",
            "drive_contribution",
            "consumption_opportunity",
            "buffer_saturation",
        }

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

    def test_system_a_registration(self) -> None:
        result = resolve_system_adapter("system_a")
        assert hasattr(result, "phase_names")
        assert hasattr(result, "build_step_analysis")
        assert hasattr(result, "build_overlays")
