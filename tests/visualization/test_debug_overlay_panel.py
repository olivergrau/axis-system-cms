"""Tests for DebugOverlayPanel (VWP9)."""

from __future__ import annotations
from axis_system_a.visualization.ui.debug_overlay_panel import DebugOverlayPanel
from PySide6.QtWidgets import QApplication, QCheckBox
import pytest

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def panel(qapp) -> DebugOverlayPanel:
    return DebugOverlayPanel()


class TestPanelConstruction:
    def test_creates_successfully(self, panel: DebugOverlayPanel):
        assert panel is not None

    def test_has_master_checkbox(self, panel: DebugOverlayPanel):
        assert panel._master_cb is not None
        assert isinstance(panel._master_cb, QCheckBox)

    def test_has_sub_checkboxes(self, panel: DebugOverlayPanel):
        assert isinstance(panel._action_pref_cb, QCheckBox)
        assert isinstance(panel._drive_contrib_cb, QCheckBox)
        assert isinstance(panel._consumption_cb, QCheckBox)

    def test_master_unchecked_by_default(self, panel: DebugOverlayPanel):
        assert not panel._master_cb.isChecked()

    def test_sub_checkboxes_disabled_by_default(self, panel: DebugOverlayPanel):
        assert not panel._action_pref_cb.isEnabled()
        assert not panel._drive_contrib_cb.isEnabled()
        assert not panel._consumption_cb.isEnabled()

    def test_max_height(self, panel: DebugOverlayPanel):
        assert panel.maximumHeight() == 70


class TestMasterToggle:
    def test_enables_sub_checkboxes(self, panel: DebugOverlayPanel):
        panel._master_cb.setChecked(True)
        assert panel._action_pref_cb.isEnabled()
        assert panel._drive_contrib_cb.isEnabled()
        assert panel._consumption_cb.isEnabled()

    def test_disables_sub_checkboxes(self, panel: DebugOverlayPanel):
        panel._master_cb.setChecked(True)
        panel._master_cb.setChecked(False)
        assert not panel._action_pref_cb.isEnabled()
        assert not panel._drive_contrib_cb.isEnabled()
        assert not panel._consumption_cb.isEnabled()

    def test_emits_master_toggled_on(self, panel: DebugOverlayPanel):
        received = []
        panel.master_toggled.connect(lambda v: received.append(v))
        panel._master_cb.setChecked(True)
        assert received == [True]

    def test_emits_master_toggled_off(self, panel: DebugOverlayPanel):
        panel._master_cb.setChecked(True)
        received = []
        panel.master_toggled.connect(lambda v: received.append(v))
        panel._master_cb.setChecked(False)
        assert received == [False]


class TestSubCheckboxSignals:
    def test_action_preference_signal(self, panel: DebugOverlayPanel):
        panel._master_cb.setChecked(True)
        received = []
        panel.action_preference_toggled.connect(lambda v: received.append(v))
        panel._action_pref_cb.setChecked(True)
        assert received == [True]

    def test_drive_contribution_signal(self, panel: DebugOverlayPanel):
        panel._master_cb.setChecked(True)
        received = []
        panel.drive_contribution_toggled.connect(lambda v: received.append(v))
        panel._drive_contrib_cb.setChecked(True)
        assert received == [True]

    def test_consumption_opportunity_signal(self, panel: DebugOverlayPanel):
        panel._master_cb.setChecked(True)
        received = []
        panel.consumption_opportunity_toggled.connect(
            lambda v: received.append(v))
        panel._consumption_cb.setChecked(True)
        assert received == [True]


class TestLegend:
    def test_legend_labels_hidden_by_default(self, panel: DebugOverlayPanel):
        assert panel._action_pref_legend.isHidden()
        assert panel._drive_contrib_legend.isHidden()
        assert panel._consumption_legend.isHidden()

    def test_action_pref_legend_visible_when_checked(self, panel: DebugOverlayPanel):
        panel._master_cb.setChecked(True)
        panel._action_pref_cb.setChecked(True)
        assert not panel._action_pref_legend.isHidden()

    def test_drive_contrib_legend_visible_when_checked(self, panel: DebugOverlayPanel):
        panel._master_cb.setChecked(True)
        panel._drive_contrib_cb.setChecked(True)
        assert not panel._drive_contrib_legend.isHidden()

    def test_consumption_legend_visible_when_checked(self, panel: DebugOverlayPanel):
        panel._master_cb.setChecked(True)
        panel._consumption_cb.setChecked(True)
        assert not panel._consumption_legend.isHidden()

    def test_all_legends_hide_when_master_off(self, panel: DebugOverlayPanel):
        panel._master_cb.setChecked(True)
        panel._action_pref_cb.setChecked(True)
        panel._drive_contrib_cb.setChecked(True)
        panel._consumption_cb.setChecked(True)
        panel._master_cb.setChecked(False)
        assert panel._action_pref_legend.isHidden()
        assert panel._drive_contrib_legend.isHidden()
        assert panel._consumption_legend.isHidden()
