"""Tests for WP-V.5.1: System Adapter Suite.

Cross-cutting protocol compliance for all system visualization adapters,
system-specific integration tests, and edge cases.
"""

from __future__ import annotations

import pytest

from axis.sdk.position import Position
from axis.sdk.trace import BaseStepTrace
from axis.visualization.adapters.null_system import NullSystemVisualizationAdapter
from axis.visualization.types import AnalysisSection, OverlayData

from tests.visualization.adapter_fixtures import (
    ALL_SYSTEM_ADAPTERS,
    make_snapshot,
    make_step_trace,
    sample_system_a_data,
    sample_system_b_data,
)


def _step_for_adapter(adapter_id: str) -> BaseStepTrace:
    """Build a step trace with the correct system_data for the adapter."""
    if adapter_id == "system_a":
        return make_step_trace(
            action="consume",
            agent_pos_before=Position(x=2, y=2),
            agent_pos_after=Position(x=2, y=2),
            system_data=sample_system_a_data(),
        )
    elif adapter_id == "system_b":
        return make_step_trace(
            action="right",
            agent_pos_before=Position(x=2, y=2),
            agent_pos_after=Position(x=3, y=2),
            system_data=sample_system_b_data(),
        )
    return make_step_trace()


# ---------------------------------------------------------------------------
# Protocol compliance (parametrized over all 3 system adapters)
# ---------------------------------------------------------------------------

_ADAPTER_PAIRS = [(a[0], a[1]) for a in ALL_SYSTEM_ADAPTERS]
_ADAPTER_IDS = [a[0] for a in ALL_SYSTEM_ADAPTERS]


@pytest.fixture(params=_ADAPTER_PAIRS, ids=_ADAPTER_IDS)
def system_adapter_pair(request):
    """Return (adapter_id, adapter_instance)."""
    return request.param


class TestSystemAdapterProtocol:

    def test_phase_names_returns_list(self, system_adapter_pair) -> None:
        _, adapter = system_adapter_pair
        result = adapter.phase_names()
        assert isinstance(result, list)
        assert all(isinstance(n, str) for n in result)

    def test_phase_names_starts_with_before(self, system_adapter_pair) -> None:
        _, adapter = system_adapter_pair
        assert adapter.phase_names()[0] == "BEFORE"

    def test_phase_names_ends_with_after_action(self, system_adapter_pair) -> None:
        _, adapter = system_adapter_pair
        assert adapter.phase_names()[-1] == "AFTER_ACTION"

    def test_phase_names_at_least_two(self, system_adapter_pair) -> None:
        _, adapter = system_adapter_pair
        assert len(adapter.phase_names()) >= 2

    def test_vitality_label_returns_string(self, system_adapter_pair) -> None:
        _, adapter = system_adapter_pair
        result = adapter.vitality_label()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_format_vitality_returns_string(self, system_adapter_pair) -> None:
        _, adapter = system_adapter_pair
        result = adapter.format_vitality(0.5, {})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_build_step_analysis_returns_list(self, system_adapter_pair) -> None:
        aid, adapter = system_adapter_pair
        step = _step_for_adapter(aid)
        result = adapter.build_step_analysis(step)
        assert isinstance(result, list)

    def test_build_step_analysis_items_are_sections(self, system_adapter_pair) -> None:
        aid, adapter = system_adapter_pair
        step = _step_for_adapter(aid)
        result = adapter.build_step_analysis(step)
        for item in result:
            assert isinstance(item, AnalysisSection)

    def test_build_overlays_returns_list(self, system_adapter_pair) -> None:
        aid, adapter = system_adapter_pair
        step = _step_for_adapter(aid)
        result = adapter.build_overlays(step)
        assert isinstance(result, list)

    def test_build_overlays_items_are_overlay_data(self, system_adapter_pair) -> None:
        aid, adapter = system_adapter_pair
        step = _step_for_adapter(aid)
        result = adapter.build_overlays(step)
        for item in result:
            assert isinstance(item, OverlayData)

    def test_available_overlay_types_returns_list(self, system_adapter_pair) -> None:
        _, adapter = system_adapter_pair
        result = adapter.available_overlay_types()
        assert isinstance(result, list)

    def test_overlay_keys_are_unique(self, system_adapter_pair) -> None:
        _, adapter = system_adapter_pair
        decls = adapter.available_overlay_types()
        keys = [d.key for d in decls]
        assert len(keys) == len(set(keys))

    def test_format_vitality_zero(self, system_adapter_pair) -> None:
        _, adapter = system_adapter_pair
        result = adapter.format_vitality(0.0, {})
        assert isinstance(result, str)

    def test_format_vitality_one(self, system_adapter_pair) -> None:
        _, adapter = system_adapter_pair
        result = adapter.format_vitality(1.0, {})
        assert isinstance(result, str)

    def test_phase_names_no_empty_strings(self, system_adapter_pair) -> None:
        _, adapter = system_adapter_pair
        for name in adapter.phase_names():
            assert len(name) > 0

    def test_overlay_declarations_match_built_overlays(self, system_adapter_pair) -> None:
        aid, adapter = system_adapter_pair
        step = _step_for_adapter(aid)
        decl_keys = {d.key for d in adapter.available_overlay_types()}
        overlay_types = {o.overlay_type
                         for o in adapter.build_overlays(step)}
        assert overlay_types <= decl_keys

    def test_build_step_analysis_with_empty_data(self, system_adapter_pair) -> None:
        _, adapter = system_adapter_pair
        step = make_step_trace(system_data={})
        # Some adapters require specific data keys; KeyError is acceptable
        try:
            adapter.build_step_analysis(step)
        except (KeyError, IndexError, TypeError):
            pass

    def test_build_overlays_with_empty_data(self, system_adapter_pair) -> None:
        _, adapter = system_adapter_pair
        step = make_step_trace(system_data={})
        try:
            adapter.build_overlays(step)
        except (KeyError, IndexError, TypeError):
            pass


# ---------------------------------------------------------------------------
# System A integration tests
# ---------------------------------------------------------------------------


class TestSystemAAdapterIntegration:

    def _adapter(self):
        from axis.systems.system_a.visualization import (
            SystemAVisualizationAdapter,
        )
        return SystemAVisualizationAdapter(max_energy=100.0)

    def _step(self):
        return make_step_trace(
            action="consume",
            agent_pos_before=Position(x=2, y=2),
            agent_pos_after=Position(x=2, y=2),
            vitality_before=0.45,
            vitality_after=0.435,
            system_data=sample_system_a_data(),
        )

    def test_three_phases(self) -> None:
        phases = self._adapter().phase_names()
        assert len(phases) == 3
        assert phases[1] == "AFTER_REGEN"

    def test_six_analysis_sections(self) -> None:
        sections = self._adapter().build_step_analysis(self._step())
        assert len(sections) == 6

    def test_section_titles(self) -> None:
        sections = self._adapter().build_step_analysis(self._step())
        titles = [s.title for s in sections]
        assert titles[0] == "Step Overview"
        assert titles[1] == "Observation"
        assert titles[2].startswith("Observation Buffer")
        assert titles[3] == "Drive Output"
        assert titles[4] == "Decision Pipeline"
        assert titles[5] == "Outcome"

    def test_four_overlay_types(self) -> None:
        overlays = self._adapter().build_overlays(self._step())
        assert len(overlays) == 4
        types = {o.overlay_type for o in overlays}
        assert types == {
            "action_preference", "drive_contribution",
            "consumption_opportunity", "buffer_saturation",
        }

    def test_action_preference_items(self) -> None:
        overlays = self._adapter().build_overlays(self._step())
        ap = [o for o in overlays if o.overlay_type == "action_preference"][0]
        item_types = {i.item_type for i in ap.items}
        assert "direction_arrow" in item_types
        assert "center_dot" in item_types
        assert "center_ring" in item_types

    def test_decision_pipeline_sub_rows(self) -> None:
        sections = self._adapter().build_step_analysis(self._step())
        dp = [s for s in sections if s.title == "Decision Pipeline"][0]
        action_rows = [r for r in dp.rows if r.sub_rows is not None]
        assert len(action_rows) == 6

    def test_vitality_format(self) -> None:
        result = self._adapter().format_vitality(0.75, {})
        assert result == "75.00 / 100.00"

    def test_observation_section_directions(self) -> None:
        sections = self._adapter().build_step_analysis(self._step())
        obs = [s for s in sections if s.title == "Observation"][0]
        labels = {r.label for r in obs.rows}
        assert {"Current", "Up", "Down", "Left", "Right"} <= labels

    def test_consumption_opportunity_markers(self) -> None:
        overlays = self._adapter().build_overlays(self._step())
        co = [o for o in overlays
              if o.overlay_type == "consumption_opportunity"][0]
        item_types = {i.item_type for i in co.items}
        assert "diamond_marker" in item_types or "neighbor_dot" in item_types

    def test_drive_contribution_bar_chart(self) -> None:
        overlays = self._adapter().build_overlays(self._step())
        dc = [o for o in overlays
              if o.overlay_type == "drive_contribution"][0]
        assert len(dc.items) == 1
        assert dc.items[0].item_type == "bar_chart"
        assert len(dc.items[0].data["values"]) == 6


# ---------------------------------------------------------------------------
# System B integration tests
# ---------------------------------------------------------------------------


class TestSystemBAdapterIntegration:

    def _adapter(self):
        from axis.systems.system_b.visualization import (
            SystemBVisualizationAdapter,
        )
        return SystemBVisualizationAdapter(max_energy=100.0)

    def _step(self):
        return make_step_trace(
            action="right",
            agent_pos_before=Position(x=2, y=2),
            agent_pos_after=Position(x=3, y=2),
            vitality_before=0.80,
            vitality_after=0.77,
            system_data=sample_system_b_data(),
        )

    def test_two_phases(self) -> None:
        assert len(self._adapter().phase_names()) == 2

    def test_five_analysis_sections(self) -> None:
        sections = self._adapter().build_step_analysis(self._step())
        assert len(sections) == 5

    def test_section_titles(self) -> None:
        sections = self._adapter().build_step_analysis(self._step())
        titles = [s.title for s in sections]
        assert titles == [
            "Step Overview", "Decision Weights", "Probabilities",
            "Last Scan", "Outcome",
        ]

    def test_two_overlays(self) -> None:
        overlays = self._adapter().build_overlays(self._step())
        assert len(overlays) == 2
        types = {o.overlay_type for o in overlays}
        assert types == {"action_weights", "scan_result"}

    def test_scan_result_radius_circle(self) -> None:
        overlays = self._adapter().build_overlays(self._step())
        sr = [o for o in overlays if o.overlay_type == "scan_result"][0]
        circles = [i for i in sr.items if i.item_type == "radius_circle"]
        assert len(circles) == 1

    def test_no_scan_section(self) -> None:
        sd = sample_system_b_data()
        del sd["decision_data"]["last_scan"]
        step = make_step_trace(
            action="stay", system_data=sd,
            vitality_before=1.0, vitality_after=0.9,
        )
        sections = self._adapter().build_step_analysis(step)
        scan_section = [s for s in sections if s.title == "Last Scan"][0]
        assert any("No scan" in r.value for r in scan_section.rows)

    def test_vitality_format_custom_max(self) -> None:
        from axis.systems.system_b.visualization import (
            SystemBVisualizationAdapter,
        )
        adapter = SystemBVisualizationAdapter(max_energy=50.0)
        result = adapter.format_vitality(0.8, {})
        assert result == "40.00 / 50.00"


# ---------------------------------------------------------------------------
# Null adapter integration tests
# ---------------------------------------------------------------------------


class TestNullAdapterIntegration:

    def test_two_phases(self) -> None:
        adapter = NullSystemVisualizationAdapter()
        assert adapter.phase_names() == ["BEFORE", "AFTER_ACTION"]

    def test_empty_analysis(self) -> None:
        adapter = NullSystemVisualizationAdapter()
        step = make_step_trace()
        assert adapter.build_step_analysis(step) == []

    def test_empty_overlays(self) -> None:
        adapter = NullSystemVisualizationAdapter()
        step = make_step_trace()
        assert adapter.build_overlays(step) == []


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestSystemAdapterEdgeCases:

    def test_system_a_custom_max_energy(self) -> None:
        from axis.systems.system_a.visualization import (
            SystemAVisualizationAdapter,
        )
        adapter = SystemAVisualizationAdapter(max_energy=200.0)
        assert adapter.format_vitality(0.5, {}) == "100.00 / 200.00"

    def test_null_adapter_vitality_format(self) -> None:
        adapter = NullSystemVisualizationAdapter()
        result = adapter.format_vitality(0.75, {})
        assert "75" in result

    def test_overlay_declarations_have_descriptions(self) -> None:
        from axis.systems.system_a.visualization import (
            SystemAVisualizationAdapter,
        )
        adapter = SystemAVisualizationAdapter(max_energy=100.0)
        for decl in adapter.available_overlay_types():
            assert len(decl.key) > 0
            assert len(decl.label) > 0
            assert len(decl.description) > 0
