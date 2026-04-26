"""Tests for System C+W visualization adapter."""

from __future__ import annotations

from typing import Any

import axis.systems.system_cw.visualization  # noqa: F401, E402

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseStepTrace
from axis.sdk.world_types import CellView
from axis.visualization.registry import resolve_system_adapter


def _make_snapshot() -> WorldSnapshot:
    cell = CellView(cell_type="empty", resource_value=0.0)
    grid = tuple(tuple(cell for _ in range(5)) for _ in range(5))
    return WorldSnapshot(grid=grid, agent_position=Position(x=2, y=2), width=5, height=5)


def _sample_system_data() -> dict[str, Any]:
    return {
        "decision_data": {
            "observation": {
                "current": {"traversability": 1.0, "resource": 0.5},
                "up": {"traversability": 1.0, "resource": 0.2},
                "down": {"traversability": 0.0, "resource": 0.0},
                "left": {"traversability": 1.0, "resource": 0.1},
                "right": {"traversability": 1.0, "resource": 0.8},
            },
            "hunger_drive": {
                "activation": 0.55,
                "action_contributions": (0.2, -0.1, 0.05, 0.35, 0.6, -0.05),
            },
            "curiosity_drive": {
                "activation": 0.75,
                "spatial_novelty": (0.8, 0.1, 0.5, 0.9),
                "sensory_novelty": (0.4, 0.2, 0.2, 0.7),
                "composite_novelty": (0.62, 0.14, 0.35, 0.80),
                "action_contributions": (0.4, -0.2, 0.15, 0.55, -0.25, -0.15),
            },
            "prediction": {
                "context": 23,
                "features": (0.5, 0.2, 0.0, 0.1, 0.8, 0.62, 0.14, 0.35, 0.80),
                "hunger_modulation": {
                    "modulation_mode": "multiplicative",
                    "raw_scores": (0.2, -0.1, 0.05, 0.35, 0.6, -0.05),
                    "reliability_factors": (1.2, 0.8, 1.0, 1.3, 1.05, 0.9),
                    "prediction_biases": (0.02, -0.04, 0.0, 0.05, 0.03, -0.01),
                    "confidence_by_action": {
                        "up": 0.4, "down": 0.0, "left": 0.1, "right": 0.5, "consume": 0.2, "stay": 0.0,
                    },
                    "frustration_by_action": {
                        "up": 0.0, "down": 0.3, "left": 0.0, "right": 0.0, "consume": 0.0, "stay": 0.1,
                    },
                    "final_scores": (0.24, -0.08, 0.05, 0.455, 0.63, -0.045),
                    "modulated_scores": (0.24, -0.08, 0.05, 0.455, 0.63, -0.045),
                },
                "curiosity_modulation": {
                    "modulation_mode": "multiplicative",
                    "raw_scores": (0.4, -0.2, 0.15, 0.55, -0.25, -0.15),
                    "reliability_factors": (1.1, 0.7, 0.9, 1.25, 0.8, 0.75),
                    "prediction_biases": (0.03, -0.02, -0.01, 0.04, -0.03, -0.02),
                    "confidence_by_action": {
                        "up": 0.3, "down": 0.0, "left": 0.0, "right": 0.4, "consume": 0.0, "stay": 0.0,
                    },
                    "frustration_by_action": {
                        "up": 0.0, "down": 0.35, "left": 0.1, "right": 0.0, "consume": 0.2, "stay": 0.2,
                    },
                    "final_scores": (0.44, -0.14, 0.135, 0.6875, -0.20, -0.1125),
                    "modulated_scores": (0.44, -0.14, 0.135, 0.6875, -0.20, -0.1125),
                },
                "counterfactual_top_action": "consume",
            },
            "arbitration": {
                "hunger_weight": 0.45,
                "curiosity_weight": 0.55,
            },
            "combined_scores": (0.1452, -0.0757, 0.0619, 0.3840, 0.0919, -0.0569),
            "policy": {
                "probabilities": (0.17, 0.05, 0.11, 0.32, 0.23, 0.12),
                "selected_action": "right",
            },
        },
        "trace_data": {
            "energy_before": 50.0,
            "energy_after": 49.0,
            "energy_delta": -1.0,
            "action_cost": 1.0,
            "energy_gain": 0.0,
            "relative_position": (2, 1),
            "visit_count_at_current": 3,
            "visit_counts_map": (
                ((2, 2), 1),
                ((2, 1), 3),
                ((3, 1), 2),
            ),
            "prediction": {
                "predicted_features": (0.4, 0.1, 0.0, 0.2, 0.7, 0.50, 0.10, 0.30, 0.70),
                "observed_features": (0.5, 0.2, 0.0, 0.1, 0.8, 0.62, 0.14, 0.35, 0.80),
                "feature_error_positive": 0.14,
                "feature_error_negative": 0.03,
                "hunger": {
                    "actual": 0.72,
                    "predicted": 0.60,
                    "error_positive": 0.12,
                    "error_negative": 0.01,
                    "confidence_value": 0.55,
                    "frustration_value": 0.08,
                },
                "curiosity": {
                    "actual": 0.31,
                    "predicted": 0.22,
                    "error_positive": 0.09,
                    "error_negative": 0.02,
                    "novelty_weight": 0.80,
                    "used_nonmove_penalty_rule": False,
                    "confidence_value": 0.48,
                    "frustration_value": 0.11,
                },
                "hunger_confidence_by_action": {
                    "up": 0.4, "down": 0.0, "left": 0.1, "right": 0.5, "consume": 0.2, "stay": 0.0,
                },
                "hunger_frustration_by_action": {
                    "up": 0.0, "down": 0.3, "left": 0.0, "right": 0.0, "consume": 0.0, "stay": 0.1,
                },
                "curiosity_confidence_by_action": {
                    "up": 0.3, "down": 0.0, "left": 0.0, "right": 0.4, "consume": 0.0, "stay": 0.0,
                },
                "curiosity_frustration_by_action": {
                    "up": 0.0, "down": 0.35, "left": 0.1, "right": 0.0, "consume": 0.2, "stay": 0.2,
                },
            },
        },
    }


def _make_step_trace(system_data: dict[str, Any] | None = None) -> BaseStepTrace:
    snapshot = _make_snapshot()
    return BaseStepTrace(
        timestep=5,
        action="right",
        world_before=snapshot,
        world_after=snapshot,
        agent_position_before=Position(x=2, y=2),
        agent_position_after=Position(x=3, y=2),
        vitality_before=0.50,
        vitality_after=0.49,
        terminated=False,
        system_data=system_data or _sample_system_data(),
    )


class TestRegistration:

    def test_adapter_resolves(self) -> None:
        adapter = resolve_system_adapter("system_cw")
        assert hasattr(adapter, "phase_names")
        assert hasattr(adapter, "build_step_analysis")
        assert hasattr(adapter, "build_overlays")


class TestAnalysisSections:

    def test_section_titles_cover_dual_prediction_story(self) -> None:
        adapter = resolve_system_adapter("system_cw")
        sections = adapter.build_step_analysis(_make_step_trace())
        titles = [section.title for section in sections]
        assert "Step Overview" in titles
        assert "Observation" in titles
        assert "Curiosity & World Context" in titles
        assert "Raw Drive Outputs" in titles
        assert "Arbitration" in titles
        assert "Shared Predictive Representation" in titles
        assert "Hunger-side Predictive Modulation" in titles
        assert "Curiosity-side Predictive Modulation" in titles
        assert "Decision Pipeline" in titles
        assert "Predictive Update" in titles
        assert "Drive-Specific Trace Update" in titles
        assert "Outcome" in titles

    def test_sections_tolerate_empty_data(self) -> None:
        adapter = resolve_system_adapter("system_cw")
        sections = adapter.build_step_analysis(_make_step_trace({"decision_data": {}, "trace_data": {}}))
        assert len(sections) >= 8


class TestOverlays:

    def test_overlay_types_include_dual_split(self) -> None:
        adapter = resolve_system_adapter("system_cw")
        overlays = adapter.build_overlays(_make_step_trace())
        types = {overlay.overlay_type for overlay in overlays}
        assert "action_preference" in types
        assert "visit_count_heatmap" in types
        assert "novelty_field" in types
        assert "modulation_factor" in types
        assert "dual_modulation_split" in types
        assert "consumption_opportunity" in types

    def test_dual_modulation_split_renders_on_agent_cell(self) -> None:
        adapter = resolve_system_adapter("system_cw")
        overlays = adapter.build_overlays(_make_step_trace())
        split = [overlay for overlay in overlays if overlay.overlay_type == "dual_modulation_split"][0]
        assert len(split.items) == 1
        item = split.items[0]
        assert item.item_type == "bar_chart"
        assert item.grid_position == (2, 2)
        assert len(item.data["values"]) == 6
        assert len(item.data["segments"]) == 6

    def test_available_overlay_types_match_build_output(self) -> None:
        adapter = resolve_system_adapter("system_cw")
        built = {overlay.overlay_type for overlay in adapter.build_overlays(_make_step_trace())}
        declared = {decl.key for decl in adapter.available_overlay_types()}
        assert built <= declared


class TestSystemWidgetData:

    def test_widget_data_uses_dual_prediction_mode(self) -> None:
        adapter = resolve_system_adapter("system_cw")
        data = adapter.build_system_widget_data(_make_step_trace())
        assert isinstance(data, dict)
        assert data["widget_mode"] == "dual_prediction"
        assert "hunger" in data
        assert "curiosity" in data

    def test_widget_data_contains_shared_context_and_channel_details(self) -> None:
        adapter = resolve_system_adapter("system_cw")
        data = adapter.build_system_widget_data(_make_step_trace())
        assert data["context"] == 23
        assert len(data["features"]) == 9
        assert abs(data["hunger"]["modulation_factors"]["up"] - 1.2) < 0.001
        assert abs(data["curiosity"]["modulation_factors"]["right"] - 1.25) < 0.001
        assert data["hunger"]["confidences"]["right"] == 0.5
        assert data["curiosity"]["frustrations"]["down"] == 0.35

