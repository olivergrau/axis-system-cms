"""Tests for StepAnalysisPanel (VWP11)."""

from __future__ import annotations
from axis_system_a.visualization.view_models import (
    NeighborObservationViewModel,
    StepAnalysisViewModel,
)
from axis_system_a.visualization.ui.step_analysis_panel import StepAnalysisPanel
from PySide6.QtWidgets import QApplication
import pytest

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def panel(qapp) -> StepAnalysisPanel:
    return StepAnalysisPanel()


def _make_vm(**overrides) -> StepAnalysisViewModel:
    defaults = dict(
        timestep=3,
        energy_before=50.0,
        energy_after=49.0,
        energy_delta=-1.0,
        current_resource=0.65,
        neighbor_observations=(
            NeighborObservationViewModel(resource=0.30, traversable=True),
            NeighborObservationViewModel(resource=0.00, traversable=False),
            NeighborObservationViewModel(resource=0.45, traversable=True),
            NeighborObservationViewModel(resource=0.10, traversable=True),
        ),
        drive_activation=0.73,
        drive_contributions=(0.42, -0.18, 0.05, 0.31, -0.02, 0.12),
        raw_contributions=(0.42, -0.18, 0.05, 0.31, -0.02, 0.12),
        admissibility_mask=(True, False, True, True, True, True),
        masked_contributions=(0.42, float("-inf"), 0.05, 0.31, -0.02, 0.12),
        probabilities=(0.25, 0.00, 0.10, 0.30, 0.15, 0.20),
        temperature=1.0,
        selection_mode="SAMPLE",
        selected_action="RIGHT",
        moved=True,
        consumed=False,
        resource_consumed=0.0,
        position_before=(1, 2),
        position_after=(1, 3),
        terminated=False,
        termination_reason=None,
    )
    defaults.update(overrides)
    return StepAnalysisViewModel(**defaults)


class TestConstruction:
    def test_creates_successfully(self, panel: StepAnalysisPanel):
        assert panel is not None

    def test_has_title_label(self, panel: StepAnalysisPanel):
        assert panel._title_label.text() == "Step Analysis"

    def test_starts_hidden(self, panel: StepAnalysisPanel):
        assert panel.isHidden()


class TestSetFrameNone:
    def test_hides_when_vm_none(self, panel: StepAnalysisPanel):
        panel.set_frame(None)
        assert panel.isHidden()

    def test_hides_after_showing(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm())
        panel.set_frame(None)
        assert panel.isHidden()


class TestStepOverview:
    def test_shows_timestep(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm())
        text = panel._content_label.text()
        assert "3" in text

    def test_shows_energy_before(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm())
        text = panel._content_label.text()
        assert "50.00" in text

    def test_shows_energy_after(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm())
        text = panel._content_label.text()
        assert "49.00" in text

    def test_shows_energy_delta(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm())
        text = panel._content_label.text()
        assert "-1.00" in text


class TestObservationSection:
    def test_shows_current_resource(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm())
        text = panel._content_label.text()
        assert "0.65" in text

    def test_shows_neighbor_resources(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm())
        text = panel._content_label.text()
        assert "0.30" in text
        assert "0.45" in text

    def test_shows_traversability(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm())
        text = panel._content_label.text()
        assert "traversable" in text
        assert "blocked" in text


class TestDriveSection:
    def test_shows_activation(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm())
        text = panel._content_label.text()
        assert "0.73" in text

    def test_shows_contributions(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm())
        text = panel._content_label.text()
        assert "+0.420" in text
        assert "-0.180" in text

    def test_shows_all_six_actions(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm())
        text = panel._content_label.text()
        for label in ("UP", "DOWN", "LEFT", "RIGHT", "CONSUME", "STAY"):
            assert label in text


class TestDecisionSection:
    def test_shows_temperature(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm())
        text = panel._content_label.text()
        assert "1.0000" in text

    def test_shows_selection_mode(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm())
        text = panel._content_label.text()
        assert "SAMPLE" in text

    def test_shows_selected_action(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm())
        text = panel._content_label.text()
        assert "RIGHT" in text

    def test_shows_probabilities(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm())
        text = panel._content_label.text()
        assert "0.250" in text
        assert "0.300" in text

    def test_shows_raw_contributions(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm())
        text = panel._content_label.text()
        assert "+0.420" in text

    def test_shows_admissibility(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm())
        text = panel._content_label.text()
        assert "Adm" in text
        assert "   Y" in text
        assert "   N" in text

    def test_selected_action_highlighted(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm())
        text = panel._content_label.text()
        for line in text.split("\n"):
            if "RIGHT" in line and "Prob" not in line and "Selected" not in line:
                if "0.300" in line:
                    assert "*" in line
                    break
        else:
            pytest.fail("No highlighted RIGHT line found in decision table")


class TestOutcomeSection:
    def test_shows_moved(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm())
        text = panel._content_label.text()
        assert "Moved:" in text
        assert "yes" in text

    def test_shows_consumed(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm(consumed=True, resource_consumed=0.65))
        text = panel._content_label.text()
        lines = text.split("\n")
        consumed_lines = [l for l in lines if "Consumed:" in l]
        assert consumed_lines
        assert "yes" in consumed_lines[0]

    def test_shows_position(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm())
        text = panel._content_label.text()
        assert "(1,2)" in text
        assert "(1,3)" in text

    def test_shows_terminated(self, panel: StepAnalysisPanel):
        panel.set_frame(
            _make_vm(terminated=True, termination_reason="ENERGY_DEPLETED"))
        text = panel._content_label.text()
        assert "ENERGY_DEPLETED" in text

    def test_panel_visible_with_data(self, panel: StepAnalysisPanel):
        panel.set_frame(_make_vm())
        assert not panel.isHidden()
