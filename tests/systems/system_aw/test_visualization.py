"""WP-12 tests -- SystemAW Visualization Adapter."""

from __future__ import annotations

from typing import Any

import pytest

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseStepTrace
from axis.sdk.world_types import CellView
from axis.visualization.registry import resolve_system_adapter


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
            "hunger_drive": {
                "activation": 0.5000,
                "action_contributions": (0.15, 0.0, 0.0, 0.4, 0.625, -0.05),
            },
            "curiosity_drive": {
                "activation": 0.85,
                "spatial_novelty": (1.0, 0.5, 0.333, 1.0),
                "sensory_novelty": (0.1, 0.4, 0.2, 0.0),
                "composite_novelty": (0.55, 0.45, 0.267, 0.50),
                "action_contributions": (0.55, 0.45, 0.267, 0.50, -0.3, -0.3),
            },
            "arbitration": {
                "hunger_weight": 0.475,
                "curiosity_weight": 0.250,
            },
            "combined_scores": (0.153, 0.192, 0.057, 0.296, 0.233, -0.088),
            "policy": {
                "raw_scores": (0.153, 0.192, 0.057, 0.296, 0.233, -0.088),
                "admissibility_mask": (True, False, True, True, True, True),
                "masked_scores": (
                    0.153, float("-inf"), 0.057, 0.296, 0.233, -0.088),
                "probabilities": (0.18, 0.0, 0.14, 0.28, 0.25, 0.15),
                "selected_action": "right",
                "temperature": 2.00,
                "selection_mode": "sample",
            },
        },
        "trace_data": {
            "energy_before": 50.00,
            "energy_after": 49.00,
            "energy_delta": -1.00,
            "action_cost": 1.00,
            "energy_gain": 0.00,
            "memory_entries_before": 2,
            "memory_entries_after": 3,
            "relative_position": (3, 1),
            "visit_count_at_current": 2,
            "visit_counts_map": [
                [[0, 0], 3], [[1, 0], 2], [[2, 0], 1], [[3, 1], 2],
            ],
        },
    }


def _sample_step_trace() -> BaseStepTrace:
    snap = _make_snapshot()
    return BaseStepTrace(
        timestep=5,
        action="right",
        world_before=snap,
        world_after=snap,
        agent_position_before=Position(x=2, y=2),
        agent_position_after=Position(x=3, y=2),
        vitality_before=0.50,
        vitality_after=0.49,
        terminated=False,
        system_data=_sample_system_data(),
    )


def _curiosity_zero_system_data() -> dict[str, Any]:
    """System data with all curiosity outputs zeroed."""
    return {
        "decision_data": {
            "observation": {
                "current": {"traversability": 1.0, "resource": 0.5},
                "up":      {"traversability": 1.0, "resource": 0.0},
                "down":    {"traversability": 1.0, "resource": 0.0},
                "left":    {"traversability": 1.0, "resource": 0.0},
                "right":   {"traversability": 1.0, "resource": 0.0},
            },
            "hunger_drive": {
                "activation": 0.5000,
                "action_contributions": (0.0, 0.0, 0.0, 0.0, 0.625, -0.05),
            },
            "curiosity_drive": {
                "activation": 0.0,
                "spatial_novelty": (0.0, 0.0, 0.0, 0.0),
                "sensory_novelty": (0.0, 0.0, 0.0, 0.0),
                "composite_novelty": (0.0, 0.0, 0.0, 0.0),
                "action_contributions": (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            },
            "arbitration": {
                "hunger_weight": 0.475,
                "curiosity_weight": 0.0,
            },
            "combined_scores": (0.0, 0.0, 0.0, 0.0, 0.625, -0.05),
            "policy": {
                "raw_scores": (0.0, 0.0, 0.0, 0.0, 0.625, -0.05),
                "admissibility_mask": (True, True, True, True, True, True),
                "masked_scores": (0.0, 0.0, 0.0, 0.0, 0.625, -0.05),
                "probabilities": (0.12, 0.12, 0.12, 0.12, 0.40, 0.12),
                "selected_action": "consume",
                "temperature": 2.00,
                "selection_mode": "sample",
            },
        },
        "trace_data": {
            "energy_before": 50.00,
            "energy_after": 54.00,
            "energy_delta": 4.00,
            "action_cost": 1.00,
            "energy_gain": 5.00,
            "memory_entries_before": 0,
            "memory_entries_after": 1,
            "relative_position": (0, 0),
            "visit_count_at_current": 1,
        },
    }


import axis.systems.system_aw.visualization  # noqa: F401, E402


def _adapter():
    from axis.systems.system_aw.visualization import (
        SystemAWVisualizationAdapter,
    )
    return SystemAWVisualizationAdapter(max_energy=100.0)


# ---------------------------------------------------------------------------
# Analysis section tests
# ---------------------------------------------------------------------------


class TestAnalysisSections:

    def test_build_step_analysis_returns_8_sections(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        assert len(sections) == 8

    def test_section_titles(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        titles = [s.title for s in sections]
        assert titles == [
            "Step Overview",
            "Observation",
            "Hunger Drive",
            "Curiosity Drive",
            "Drive Arbitration",
            "Decision Pipeline",
            "World Model",
            "Outcome",
        ]

    def test_curiosity_drive_section_rows(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        cd_section = sections[3]
        assert cd_section.title == "Curiosity Drive"
        labels = [r.label for r in cd_section.rows]
        assert "Activation" in labels
        assert "Spatial Novelty" in labels
        assert "Sensory Novelty" in labels
        assert "Composite Novelty" in labels

    def test_arbitration_section_rows(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        arb_section = sections[4]
        assert arb_section.title == "Drive Arbitration"
        labels = [r.label for r in arb_section.rows]
        assert "Hunger Weight" in labels
        assert "Curiosity Weight" in labels
        assert "Dominant Drive" in labels

    def test_step_overview_has_relative_position(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        overview = sections[0]
        labels = [r.label for r in overview.rows]
        assert "Relative Position" in labels
        by_label = {r.label: r.value for r in overview.rows}
        assert by_label["Relative Position"] == "(3, 1)"

    def test_outcome_has_world_model_info(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        outcome = sections[7]
        labels = [r.label for r in outcome.rows]
        assert "Relative Position" in labels


# ---------------------------------------------------------------------------
# Overlay tests
# ---------------------------------------------------------------------------


class TestOverlays:

    def test_available_overlay_types_count(self) -> None:
        decls = _adapter().available_overlay_types()
        assert len(decls) == 5

    def test_overlay_keys(self) -> None:
        decls = _adapter().available_overlay_types()
        keys = {d.key for d in decls}
        assert keys == {
            "action_preference",
            "drive_contribution",
            "consumption_opportunity",
            "visit_count_heatmap",
            "novelty_field",
        }

    def test_build_overlays_returns_5(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        assert len(overlays) == 5

    def test_drive_contribution_has_both_drives(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        dc = [o for o in overlays if o.overlay_type == "drive_contribution"][0]
        assert len(dc.items) == 2
        drives = {item.data["drive"] for item in dc.items}
        assert drives == {"hunger", "curiosity"}

    def test_visit_count_heatmap_items(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        hm = [o for o in overlays if o.overlay_type == "visit_count_heatmap"][0]
        assert len(hm.items) == 4
        assert all(item.item_type == "heatmap_cell" for item in hm.items)

    def test_novelty_field_has_4_directions(self) -> None:
        overlays = _adapter().build_overlays(_sample_step_trace())
        nf = [o for o in overlays if o.overlay_type == "novelty_field"][0]
        assert len(nf.items) == 4
        directions = {item.data["direction"] for item in nf.items}
        assert directions == {"up", "down", "left", "right"}


# ---------------------------------------------------------------------------
# Registration test
# ---------------------------------------------------------------------------


class TestRegistration:

    def test_visualization_registered(self) -> None:
        result = resolve_system_adapter("system_aw")
        assert hasattr(result, "phase_names")
        assert hasattr(result, "build_step_analysis")
        assert hasattr(result, "build_overlays")


# ---------------------------------------------------------------------------
# Degradation tests
# ---------------------------------------------------------------------------


class TestDegradation:

    def test_curiosity_zero_no_crash(self) -> None:
        """With all curiosity outputs zeroed, no crash."""
        snap = _make_snapshot()
        step_trace = BaseStepTrace(
            timestep=0,
            action="consume",
            world_before=snap,
            world_after=snap,
            agent_position_before=Position(x=2, y=2),
            agent_position_after=Position(x=2, y=2),
            vitality_before=0.50,
            vitality_after=0.54,
            terminated=False,
            system_data=_curiosity_zero_system_data(),
        )
        adapter = _adapter()
        sections = adapter.build_step_analysis(step_trace)
        assert len(sections) == 8
        overlays = adapter.build_overlays(step_trace)
        assert len(overlays) == 5

    def test_empty_world_model_heatmap(self) -> None:
        """Single visit at origin: heatmap has 1 item."""
        data = _curiosity_zero_system_data()
        data["trace_data"]["visit_count_at_current"] = 1
        data["trace_data"]["visit_counts_map"] = [[[0, 0], 1]]
        snap = _make_snapshot()
        step_trace = BaseStepTrace(
            timestep=0,
            action="stay",
            world_before=snap,
            world_after=snap,
            agent_position_before=Position(x=2, y=2),
            agent_position_after=Position(x=2, y=2),
            vitality_before=0.50,
            vitality_after=0.495,
            terminated=False,
            system_data=data,
        )
        adapter = _adapter()
        overlays = adapter.build_overlays(step_trace)
        hm = [o for o in overlays if o.overlay_type == "visit_count_heatmap"][0]
        assert len(hm.items) == 1
        assert hm.items[0].data["visit_count"] == 1


# ---------------------------------------------------------------------------
# World Model section tests
# ---------------------------------------------------------------------------


class TestWorldModelSection:

    def test_world_model_section_present(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        titles = [s.title for s in sections]
        assert "World Model" in titles

    def test_world_model_section_position(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        titles = [s.title for s in sections]
        assert titles.index("World Model") == 6
        assert titles.index("Outcome") == 7

    def test_world_model_stats_rows(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        wm = [s for s in sections if s.title == "World Model"][0]
        labels = [r.label for r in wm.rows]
        assert "Position (rel)" in labels
        assert "Visits Here" in labels
        assert "Cells Visited" in labels
        assert "Total Visits" in labels
        assert "Max Visits" in labels

    def test_world_model_cells_visited_value(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        wm = [s for s in sections if s.title == "World Model"][0]
        by_label = {r.label: r.value for r in wm.rows}
        assert by_label["Cells Visited"] == "4"
        assert by_label["Total Visits"] == "8"

    def test_world_model_text_map_present(self) -> None:
        sections = _adapter().build_step_analysis(_sample_step_trace())
        wm = [s for s in sections if s.title == "World Model"][0]
        map_rows = [r for r in wm.rows if r.label == "Map"]
        assert len(map_rows) == 1
        assert map_rows[0].sub_rows is not None
        assert len(map_rows[0].sub_rows) > 0

    def test_world_model_no_map_key_graceful(self) -> None:
        """Without visit_counts_map, section still renders with stats."""
        data = _curiosity_zero_system_data()
        # No visit_counts_map key
        snap = _make_snapshot()
        step_trace = BaseStepTrace(
            timestep=0, action="stay",
            world_before=snap, world_after=snap,
            agent_position_before=Position(x=2, y=2),
            agent_position_after=Position(x=2, y=2),
            vitality_before=0.50, vitality_after=0.495,
            terminated=False, system_data=data,
        )
        sections = _adapter().build_step_analysis(step_trace)
        wm = [s for s in sections if s.title == "World Model"][0]
        by_label = {r.label: r.value for r in wm.rows}
        assert by_label["Cells Visited"] == "0"
        # No "Map" row when map is empty
        map_rows = [r for r in wm.rows if r.label == "Map"]
        assert len(map_rows) == 0


# ---------------------------------------------------------------------------
# Full-map heatmap tests
# ---------------------------------------------------------------------------


class TestHeatmapFullMap:

    def test_heatmap_coordinate_conversion(self) -> None:
        """Verify relative→absolute coordinate conversion with y-flip.

        Sample data: agent_position_after=(3,2), relative_position=(3,1).
        Relative (0,0) → abs (3+(0-3), 2-(0-1)) = (0, 3)
        Relative (1,0) → abs (3+(1-3), 2-(0-1)) = (1, 3)
        Relative (2,0) → abs (3+(2-3), 2-(0-1)) = (2, 3)
        Relative (3,1) → abs (3+(3-3), 2-(1-1)) = (3, 2)  # agent pos after
        """
        overlays = _adapter().build_overlays(_sample_step_trace())
        hm = [o for o in overlays if o.overlay_type == "visit_count_heatmap"][0]
        positions = {item.grid_position for item in hm.items}
        assert (0, 3) in positions
        assert (1, 3) in positions
        assert (2, 3) in positions
        assert (3, 2) in positions

    def test_heatmap_fallback_no_map(self) -> None:
        """Without visit_counts_map key, falls back to single cell at pos_after."""
        data = _curiosity_zero_system_data()
        # No visit_counts_map key — fallback
        snap = _make_snapshot()
        step_trace = BaseStepTrace(
            timestep=0, action="stay",
            world_before=snap, world_after=snap,
            agent_position_before=Position(x=2, y=2),
            agent_position_after=Position(x=2, y=2),
            vitality_before=0.50, vitality_after=0.495,
            terminated=False, system_data=data,
        )
        adapter = _adapter()
        overlays = adapter.build_overlays(step_trace)
        hm = [o for o in overlays if o.overlay_type == "visit_count_heatmap"][0]
        assert len(hm.items) == 1
        assert hm.items[0].grid_position == (2, 2)
