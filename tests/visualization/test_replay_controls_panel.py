"""Tests for ReplayControlsPanel (VWP7)."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QComboBox, QPushButton  # noqa: E402

from axis_system_a.visualization.snapshot_models import ReplayPhase  # noqa: E402
from axis_system_a.visualization.view_models import StatusBarViewModel  # noqa: E402
from axis_system_a.visualization.viewer_state import PlaybackMode  # noqa: E402
from axis_system_a.visualization.ui.replay_controls_panel import (  # noqa: E402
    ReplayControlsPanel,
)


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _make_status(
    *,
    phase: ReplayPhase = ReplayPhase.BEFORE,
    playback_mode: PlaybackMode = PlaybackMode.STOPPED,
    at_start: bool = False,
    at_end: bool = False,
) -> StatusBarViewModel:
    return StatusBarViewModel(
        step_index=2, total_steps=5, phase=phase,
        playback_mode=playback_mode, energy=42.5,
        at_start=at_start, at_end=at_end,
    )


class TestPanelConstruction:
    def test_has_step_back_button(self, qapp):
        panel = ReplayControlsPanel()
        assert panel._step_back_btn is not None

    def test_has_step_fwd_button(self, qapp):
        panel = ReplayControlsPanel()
        assert panel._step_fwd_btn is not None

    def test_has_play_button(self, qapp):
        panel = ReplayControlsPanel()
        assert panel._play_btn is not None

    def test_has_pause_button(self, qapp):
        panel = ReplayControlsPanel()
        assert panel._pause_btn is not None

    def test_has_stop_button(self, qapp):
        panel = ReplayControlsPanel()
        assert panel._stop_btn is not None

    def test_has_phase_combo(self, qapp):
        panel = ReplayControlsPanel()
        assert isinstance(panel._phase_combo, QComboBox)
        assert panel._phase_combo.count() == 3


class TestSignalEmission:
    def test_step_back_emits(self, qapp):
        panel = ReplayControlsPanel()
        received = []
        panel.step_backward_requested.connect(lambda: received.append(True))
        panel._step_back_btn.click()
        assert received

    def test_step_fwd_emits(self, qapp):
        panel = ReplayControlsPanel()
        received = []
        panel.step_forward_requested.connect(lambda: received.append(True))
        panel._step_fwd_btn.click()
        assert received

    def test_play_emits(self, qapp):
        panel = ReplayControlsPanel()
        received = []
        panel.play_requested.connect(lambda: received.append(True))
        panel._play_btn.click()
        assert received

    def test_pause_emits(self, qapp):
        panel = ReplayControlsPanel()
        received = []
        panel.pause_requested.connect(lambda: received.append(True))
        panel._pause_btn.click()
        assert received

    def test_stop_emits(self, qapp):
        panel = ReplayControlsPanel()
        received = []
        panel.stop_requested.connect(lambda: received.append(True))
        panel._stop_btn.click()
        assert received

    def test_phase_combo_emits(self, qapp):
        panel = ReplayControlsPanel()
        received = []
        panel.phase_selected.connect(lambda idx: received.append(idx))
        panel._phase_combo.setCurrentIndex(2)
        assert received == [2]


class TestButtonStates:
    def test_step_back_disabled_at_start(self, qapp):
        panel = ReplayControlsPanel()
        panel.set_frame(_make_status(at_start=True))
        assert not panel._step_back_btn.isEnabled()

    def test_step_fwd_disabled_at_end(self, qapp):
        panel = ReplayControlsPanel()
        panel.set_frame(_make_status(at_end=True))
        assert not panel._step_fwd_btn.isEnabled()

    def test_play_enabled_when_stopped(self, qapp):
        panel = ReplayControlsPanel()
        panel.set_frame(_make_status(playback_mode=PlaybackMode.STOPPED))
        assert panel._play_btn.isEnabled()

    def test_play_disabled_when_playing(self, qapp):
        panel = ReplayControlsPanel()
        panel.set_frame(_make_status(playback_mode=PlaybackMode.PLAYING))
        assert not panel._play_btn.isEnabled()

    def test_pause_enabled_when_playing(self, qapp):
        panel = ReplayControlsPanel()
        panel.set_frame(_make_status(playback_mode=PlaybackMode.PLAYING))
        assert panel._pause_btn.isEnabled()

    def test_pause_disabled_when_stopped(self, qapp):
        panel = ReplayControlsPanel()
        panel.set_frame(_make_status(playback_mode=PlaybackMode.STOPPED))
        assert not panel._pause_btn.isEnabled()

    def test_stop_disabled_when_stopped(self, qapp):
        panel = ReplayControlsPanel()
        panel.set_frame(_make_status(playback_mode=PlaybackMode.STOPPED))
        assert not panel._stop_btn.isEnabled()

    def test_phase_reflects_current(self, qapp):
        panel = ReplayControlsPanel()
        panel.set_frame(_make_status(phase=ReplayPhase.AFTER_REGEN))
        assert panel._phase_combo.currentIndex() == 1


class TestReentrancy:
    def test_programmatic_phase_update_no_signal(self, qapp):
        panel = ReplayControlsPanel()
        received = []
        panel.phase_selected.connect(lambda idx: received.append(idx))
        panel.set_frame(_make_status(phase=ReplayPhase.AFTER_ACTION))
        assert received == []
