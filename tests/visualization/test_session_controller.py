"""Tests for VisualizationSessionController (VWP7)."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from axis_system_a.visualization.playback_controller import (  # noqa: E402
    is_at_final,
    is_at_initial,
)
from axis_system_a.visualization.replay_models import (  # noqa: E402
    ReplayEpisodeHandle,
)
from axis_system_a.visualization.snapshot_models import (  # noqa: E402
    ReplayPhase,
)
from axis_system_a.visualization.snapshot_resolver import SnapshotResolver  # noqa: E402
from axis_system_a.visualization.viewer_state import PlaybackMode  # noqa: E402
from axis_system_a.visualization.ui.session_controller import (  # noqa: E402
    VisualizationSessionController,
)


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def controller(
    qapp,
    replay_episode_handle: ReplayEpisodeHandle,
    snapshot_resolver: SnapshotResolver,
) -> VisualizationSessionController:
    return VisualizationSessionController(replay_episode_handle, snapshot_resolver)


def _collect_frames(ctrl):
    received = []
    ctrl.frame_changed.connect(lambda f: received.append(f))
    return received


class TestConstruction:
    def test_initial_coordinate(self, controller):
        state = controller.current_state
        assert state.coordinate.step_index == 0
        assert state.coordinate.phase == ReplayPhase.BEFORE

    def test_initial_playback_mode(self, controller):
        assert controller.current_state.playback_mode == PlaybackMode.STOPPED

    def test_frame_not_none(self, controller):
        assert controller.current_frame is not None

    def test_timer_not_running(self, controller):
        assert not controller._timer.isActive()


class TestNavigation:
    def test_step_forward(self, controller):
        controller.step_forward()
        assert controller.current_state.coordinate.phase == ReplayPhase.AFTER_REGEN

    def test_step_backward_at_start_noop(self, controller):
        frames = _collect_frames(controller)
        controller.step_backward()
        assert len(frames) == 0  # identity skip

    def test_step_forward_emits_frame_changed(self, controller):
        frames = _collect_frames(controller)
        controller.step_forward()
        assert len(frames) == 1

    def test_round_trip(self, controller):
        controller.step_forward()
        controller.step_backward()
        state = controller.current_state
        assert state.coordinate.step_index == 0
        assert state.coordinate.phase == ReplayPhase.BEFORE


class TestPlayback:
    def test_play_sets_playing_and_starts_timer(self, controller):
        controller.play()
        assert controller.current_state.playback_mode == PlaybackMode.PLAYING
        assert controller._timer.isActive()

    def test_pause_sets_paused_and_stops_timer(self, controller):
        controller.play()
        controller.pause()
        assert controller.current_state.playback_mode == PlaybackMode.PAUSED
        assert not controller._timer.isActive()

    def test_stop_resets_coordinate_and_mode(self, controller):
        controller.step_forward()
        controller.step_forward()
        controller.stop()
        state = controller.current_state
        assert state.coordinate.step_index == 0
        assert state.coordinate.phase == ReplayPhase.BEFORE
        assert state.playback_mode == PlaybackMode.STOPPED

    def test_stop_stops_timer(self, controller):
        controller.play()
        controller.stop()
        assert not controller._timer.isActive()

    def test_play_then_pause(self, controller):
        controller.play()
        controller.pause()
        assert controller.current_state.playback_mode == PlaybackMode.PAUSED

    def test_play_then_stop(self, controller):
        controller.play()
        controller.stop()
        assert controller.current_state.playback_mode == PlaybackMode.STOPPED

    def test_stop_emits_single_frame_changed(self, controller):
        controller.step_forward()
        frames = _collect_frames(controller)
        controller.stop()
        assert len(frames) == 1


class TestTick:
    def test_tick_while_playing_advances(self, controller):
        controller.play()
        coord_before = controller.current_state.coordinate
        controller.tick()
        assert controller.current_state.coordinate != coord_before

    def test_tick_while_stopped_noop(self, controller):
        frames = _collect_frames(controller)
        controller.tick()
        assert len(frames) == 0

    def test_auto_stop_at_final(self, controller):
        controller.play()
        # Advance past final — tick auto-stops when at final while PLAYING
        for _ in range(200):
            controller.tick()
            if controller.current_state.playback_mode == PlaybackMode.STOPPED:
                break
        assert controller.current_state.playback_mode == PlaybackMode.STOPPED

    def test_timer_stopped_on_auto_stop(self, controller):
        controller.play()
        for _ in range(200):
            controller.tick()
            if controller.current_state.playback_mode != PlaybackMode.PLAYING:
                break
        assert not controller._timer.isActive()

    def test_tick_emits_frame_changed(self, controller):
        controller.play()
        frames = _collect_frames(controller)
        controller.tick()
        assert len(frames) == 1


class TestPhase:
    def test_set_phase_changes_phase(self, controller):
        controller.set_phase(ReplayPhase.AFTER_ACTION)
        assert controller.current_state.coordinate.phase == ReplayPhase.AFTER_ACTION

    def test_set_phase_preserves_step(self, controller):
        controller.step_forward()  # to AFTER_REGEN
        controller.set_phase(ReplayPhase.AFTER_ACTION)
        assert controller.current_state.coordinate.step_index == 0


class TestSelection:
    def test_select_cell(self, controller):
        controller.select_cell(1, 1)
        assert controller.current_state.selected_cell == (1, 1)

    def test_select_agent(self, controller):
        controller.select_agent()
        assert controller.current_state.selected_agent is True

    def test_clear_selection(self, controller):
        controller.select_cell(0, 0)
        controller.clear_selection()
        assert controller.current_state.selected_cell is None
        assert controller.current_state.selected_agent is False

    def test_select_cell_emits_frame_changed(self, controller):
        frames = _collect_frames(controller)
        controller.select_cell(0, 0)
        assert len(frames) == 1


class TestRefreshPipeline:
    def test_frame_matches_state_after_action(self, controller):
        controller.step_forward()
        frame = controller.current_frame
        assert frame.status.phase == controller.current_state.coordinate.phase

    def test_identity_skip_at_start(self, controller):
        frames = _collect_frames(controller)
        controller.step_backward()
        assert len(frames) == 0
