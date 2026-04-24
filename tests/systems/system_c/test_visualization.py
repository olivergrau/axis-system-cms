"""Tests for System C visualization adapter."""

from __future__ import annotations

from typing import Any

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseStepTrace
from axis.sdk.world_types import CellView
from axis.visualization.registry import resolve_system_adapter

import axis.systems.system_c.visualization  # noqa: F401, E402


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
                "activation": 0.5,
                "action_contributions": (0.15, 0.0, 0.0, 0.4, 0.625, -0.05),
            },
            "prediction": {
                "context": 19,
                "features": (0.5, 0.3, 0.0, 0.0, 0.8),
                "modulated_scores": (0.12, 0.0, 0.0, 0.48, 0.625, -0.05),
            },
            "policy": {
                "raw_contributions": (0.12, 0.0, 0.0, 0.48, 0.625, -0.05),
                "admissibility_mask": (True, False, True, True, True, True),
                "masked_contributions": (
                    0.12, float("-inf"), 0.0, 0.48, 0.625, -0.05),
                "probabilities": (0.12, 0.0, 0.10, 0.30, 0.35, 0.13),
                "selected_action": "consume",
                "temperature": 1.0,
                "selection_mode": "sample",
            },
        },
        "trace_data": {
            "energy_before": 50.0,
            "energy_after": 49.0,
            "energy_delta": -1.0,
            "action_cost": 1.0,
            "energy_gain": 0.0,
            "buffer_entries_after": 3,
            "prediction": {
                "context": 19,
                "predicted_features": (0.4, 0.2, 0.0, 0.0, 0.6),
                "observed_features": (0.5, 0.3, 0.0, 0.0, 0.8),
                "error_positive": 0.075,
                "error_negative": 0.0,
                "confidence_by_action": {
                    "up": 0.2,
                    "down": 0.0,
                    "left": 0.0,
                    "right": 0.1,
                    "consume": 0.0,
                    "stay": 0.0,
                },
                "frustration_by_action": {
                    "up": 0.0,
                    "down": 0.05,
                    "left": 0.0,
                    "right": 0.0,
                    "consume": 0.0,
                    "stay": 0.02,
                },
            },
        },
    }


def _make_step_trace(system_data: dict[str, Any] | None = None) -> BaseStepTrace:
    snap = _make_snapshot()
    return BaseStepTrace(
        timestep=5,
        action="consume",
        world_before=snap,
        world_after=snap,
        agent_position_before=Position(x=2, y=2),
        agent_position_after=Position(x=2, y=2),
        vitality_before=0.50,
        vitality_after=0.49,
        terminated=False,
        system_data=system_data or _sample_system_data(),
    )


class TestRegistration:

    def test_adapter_resolves(self) -> None:
        adapter = resolve_system_adapter("system_c")
        assert hasattr(adapter, "phase_names")
        assert hasattr(adapter, "build_step_analysis")
        assert hasattr(adapter, "build_overlays")

    def test_phase_names(self) -> None:
        adapter = resolve_system_adapter("system_c")
        assert adapter.phase_names() == [
            "BEFORE", "AFTER_REGEN", "AFTER_ACTION"]


class TestAnalysisSections:

    def test_section_count(self) -> None:
        adapter = resolve_system_adapter("system_c")
        sections = adapter.build_step_analysis(_make_step_trace())
        # With prediction update present: 7 sections
        assert len(sections) >= 6

    def test_section_titles(self) -> None:
        adapter = resolve_system_adapter("system_c")
        sections = adapter.build_step_analysis(_make_step_trace())
        titles = [s.title for s in sections]
        assert "Step Overview" in titles
        assert "Observation" in titles
        assert "Drive Output" in titles
        assert "Prediction & Modulation" in titles
        assert "Decision Pipeline" in titles
        assert "Outcome" in titles

    def test_prediction_section_has_context(self) -> None:
        adapter = resolve_system_adapter("system_c")
        sections = adapter.build_step_analysis(_make_step_trace())
        pred_section = [
            s for s in sections
            if s.title == "Prediction & Modulation"
        ][0]
        labels = [r.label for r in pred_section.rows]
        assert "Context" in labels
        assert "Features" in labels

    def test_predictive_update_section_present(self) -> None:
        adapter = resolve_system_adapter("system_c")
        sections = adapter.build_step_analysis(_make_step_trace())
        titles = [s.title for s in sections]
        assert "Predictive Update" in titles

    def test_no_update_section_without_prediction_trace(self) -> None:
        """When trace_data has no prediction key, no update section."""
        data = _sample_system_data()
        del data["trace_data"]["prediction"]
        adapter = resolve_system_adapter("system_c")
        sections = adapter.build_step_analysis(_make_step_trace(data))
        titles = [s.title for s in sections]
        assert "Predictive Update" not in titles


class TestOverlays:

    def test_overlay_count(self) -> None:
        adapter = resolve_system_adapter("system_c")
        overlays = adapter.build_overlays(_make_step_trace())
        assert len(overlays) == 6

    def test_overlay_types(self) -> None:
        adapter = resolve_system_adapter("system_c")
        overlays = adapter.build_overlays(_make_step_trace())
        types = {o.overlay_type for o in overlays}
        assert "action_preference" in types
        assert "drive_contribution" in types
        assert "modulated_contribution" in types
        assert "consumption_opportunity" in types
        assert "modulation_factor" in types
        assert "neighbor_modulation" in types

    def test_available_overlay_types(self) -> None:
        adapter = resolve_system_adapter("system_c")
        decls = adapter.available_overlay_types()
        assert len(decls) == 6
        keys = {d.key for d in decls}
        assert "modulation_factor" in keys
        assert "modulated_contribution" in keys
        assert "neighbor_modulation" in keys

    def test_neighbor_modulation_items(self) -> None:
        adapter = resolve_system_adapter("system_c")
        overlays = adapter.build_overlays(_make_step_trace())
        nm = [o for o in overlays if o.overlay_type == "neighbor_modulation"][0]
        assert len(nm.items) == 4
        for item in nm.items:
            assert item.item_type == "modulation_cell"
            assert "modulation_factor" in item.data


class TestDegradation:

    def test_no_crash_empty_system_data(self) -> None:
        adapter = resolve_system_adapter("system_c")
        trace = _make_step_trace({"decision_data": {}, "trace_data": {}})
        sections = adapter.build_step_analysis(trace)
        assert len(sections) >= 5
        overlays = adapter.build_overlays(trace)
        assert len(overlays) == 6


class TestSystemWidgetData:

    def test_widget_data_returns_dict(self) -> None:
        adapter = resolve_system_adapter("system_c")
        data = adapter.build_system_widget_data(_make_step_trace())
        assert isinstance(data, dict)
        assert "context" in data
        assert "features" in data
        assert "modulation_factors" in data
        assert "frustrations" in data
        assert "confidences" in data

    def test_widget_data_context_value(self) -> None:
        adapter = resolve_system_adapter("system_c")
        data = adapter.build_system_widget_data(_make_step_trace())
        assert data["context"] == 19

    def test_widget_data_modulation_factors(self) -> None:
        adapter = resolve_system_adapter("system_c")
        data = adapter.build_system_widget_data(_make_step_trace())
        mf = data["modulation_factors"]
        assert isinstance(mf, dict)
        assert "up" in mf
        # up: raw=0.15, mod=0.12, mu=0.8
        assert abs(mf["up"] - 0.8) < 0.01

    def test_widget_data_uses_persisted_per_action_traces(self) -> None:
        adapter = resolve_system_adapter("system_c")
        data = adapter.build_system_widget_data(_make_step_trace())
        assert data["confidences"]["up"] == 0.2
        assert data["frustrations"]["down"] == 0.05

    def test_widget_data_empty_system_data(self) -> None:
        adapter = resolve_system_adapter("system_c")
        trace = _make_step_trace({"decision_data": {}, "trace_data": {}})
        data = adapter.build_system_widget_data(trace)
        assert isinstance(data, dict)
        assert data["context"] == 0
