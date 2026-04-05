"""Tests for VWP4 Playback and Navigation Controller."""

from __future__ import annotations

import sys

import pytest

from axis_system_a.visualization.errors import StepOutOfBoundsError
from axis_system_a.visualization.playback_controller import (
    PlaybackController,
    get_final_coordinate,
    get_initial_coordinate,
    is_at_final,
    is_at_initial,
)
from axis_system_a.visualization.replay_models import ReplayEpisodeHandle
from axis_system_a.visualization.snapshot_models import (
    ReplayCoordinate,
    ReplayPhase,
)
from axis_system_a.visualization.viewer_state import (
    PlaybackMode,
    ViewerState,
)
from axis_system_a.visualization.viewer_state_transitions import (
    seek,
    select_cell,
    set_phase,
    set_playback_mode,
)


@pytest.fixture
def controller() -> PlaybackController:
    return PlaybackController()


# ---------------------------------------------------------------------------
# Helpers — shortcuts for building states at specific coordinates
# ---------------------------------------------------------------------------


def _at(state: ViewerState, step: int, phase: ReplayPhase) -> ViewerState:
    """Move *state* to the given coordinate."""
    return seek(state, ReplayCoordinate(step_index=step, phase=phase))


def _at_final(state: ViewerState) -> ViewerState:
    """Move *state* to the final replay coordinate."""
    coord = get_final_coordinate(state.episode_handle)
    return seek(state, coord)


# ---------------------------------------------------------------------------
# step_forward
# ---------------------------------------------------------------------------


class TestStepForward:
    def test_from_before_goes_to_after_regen(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        result = controller.step_forward(initial_viewer_state)
        assert result.coordinate.step_index == 0
        assert result.coordinate.phase is ReplayPhase.AFTER_REGEN

    def test_from_after_regen_goes_to_after_action(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = _at(initial_viewer_state, 0, ReplayPhase.AFTER_REGEN)
        result = controller.step_forward(state)
        assert result.coordinate.step_index == 0
        assert result.coordinate.phase is ReplayPhase.AFTER_ACTION

    def test_from_after_action_goes_to_next_before(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = _at(initial_viewer_state, 0, ReplayPhase.AFTER_ACTION)
        result = controller.step_forward(state)
        assert result.coordinate.step_index == 1
        assert result.coordinate.phase is ReplayPhase.BEFORE

    def test_full_phase_cycle(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        s = initial_viewer_state  # (0, BEFORE)
        s = controller.step_forward(s)  # (0, AFTER_REGEN)
        s = controller.step_forward(s)  # (0, AFTER_ACTION)
        s = controller.step_forward(s)  # (1, BEFORE)
        assert s.coordinate.step_index == 1
        assert s.coordinate.phase is ReplayPhase.BEFORE

    def test_clamp_at_final_position(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = _at_final(initial_viewer_state)
        result = controller.step_forward(state)
        assert result is state

    def test_returns_new_instance(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        result = controller.step_forward(initial_viewer_state)
        assert result is not initial_viewer_state

    def test_selection_preserved(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = select_cell(initial_viewer_state, 0, 0)
        result = controller.step_forward(state)
        assert result.selected_cell == (0, 0)

    def test_playback_mode_preserved(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = set_playback_mode(initial_viewer_state, PlaybackMode.PLAYING)
        result = controller.step_forward(state)
        assert result.playback_mode is PlaybackMode.PLAYING


# ---------------------------------------------------------------------------
# step_backward
# ---------------------------------------------------------------------------


class TestStepBackward:
    def test_from_after_action_goes_to_after_regen(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = _at(initial_viewer_state, 0, ReplayPhase.AFTER_ACTION)
        result = controller.step_backward(state)
        assert result.coordinate.step_index == 0
        assert result.coordinate.phase is ReplayPhase.AFTER_REGEN

    def test_from_after_regen_goes_to_before(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = _at(initial_viewer_state, 0, ReplayPhase.AFTER_REGEN)
        result = controller.step_backward(state)
        assert result.coordinate.step_index == 0
        assert result.coordinate.phase is ReplayPhase.BEFORE

    def test_from_before_goes_to_prev_after_action(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = _at(initial_viewer_state, 1, ReplayPhase.BEFORE)
        result = controller.step_backward(state)
        assert result.coordinate.step_index == 0
        assert result.coordinate.phase is ReplayPhase.AFTER_ACTION

    def test_full_phase_cycle_backward(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        s = _at(initial_viewer_state, 1, ReplayPhase.BEFORE)
        s = controller.step_backward(s)  # (0, AFTER_ACTION)
        s = controller.step_backward(s)  # (0, AFTER_REGEN)
        s = controller.step_backward(s)  # (0, BEFORE)
        assert s.coordinate.step_index == 0
        assert s.coordinate.phase is ReplayPhase.BEFORE

    def test_clamp_at_initial_position(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        result = controller.step_backward(initial_viewer_state)
        assert result is initial_viewer_state

    def test_returns_new_instance(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = _at(initial_viewer_state, 0, ReplayPhase.AFTER_REGEN)
        result = controller.step_backward(state)
        assert result is not state

    def test_selection_preserved(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = select_cell(
            _at(initial_viewer_state, 0, ReplayPhase.AFTER_REGEN), 0, 0,
        )
        result = controller.step_backward(state)
        assert result.selected_cell == (0, 0)

    def test_playback_mode_preserved(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = set_playback_mode(
            _at(initial_viewer_state, 0, ReplayPhase.AFTER_REGEN),
            PlaybackMode.PAUSED,
        )
        result = controller.step_backward(state)
        assert result.playback_mode is PlaybackMode.PAUSED


# ---------------------------------------------------------------------------
# seek_to_step
# ---------------------------------------------------------------------------


class TestSeekToStep:
    def test_seek_to_valid_step(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        result = controller.seek_to_step(initial_viewer_state, 2)
        assert result.coordinate.step_index == 2
        assert result.coordinate.phase is ReplayPhase.BEFORE

    def test_seek_to_first_step(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = _at(initial_viewer_state, 2, ReplayPhase.AFTER_ACTION)
        result = controller.seek_to_step(state, 0)
        assert result.coordinate.step_index == 0
        assert result.coordinate.phase is ReplayPhase.BEFORE

    def test_seek_to_last_step(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        total = initial_viewer_state.episode_handle.validation.total_steps
        result = controller.seek_to_step(initial_viewer_state, total - 1)
        assert result.coordinate.step_index == total - 1
        assert result.coordinate.phase is ReplayPhase.BEFORE

    def test_seek_out_of_bounds_raises(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        total = initial_viewer_state.episode_handle.validation.total_steps
        with pytest.raises(StepOutOfBoundsError):
            controller.seek_to_step(initial_viewer_state, total)

    def test_preserves_selection(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = select_cell(initial_viewer_state, 0, 0)
        result = controller.seek_to_step(state, 1)
        assert result.selected_cell == (0, 0)


# ---------------------------------------------------------------------------
# seek_to_coordinate
# ---------------------------------------------------------------------------


class TestSeekToCoordinate:
    def test_seek_to_valid_coordinate(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        coord = ReplayCoordinate(
            step_index=1, phase=ReplayPhase.AFTER_REGEN,
        )
        result = controller.seek_to_coordinate(initial_viewer_state, coord)
        assert result.coordinate == coord

    def test_out_of_bounds_raises(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        total = initial_viewer_state.episode_handle.validation.total_steps
        coord = ReplayCoordinate(
            step_index=total, phase=ReplayPhase.BEFORE,
        )
        with pytest.raises(StepOutOfBoundsError):
            controller.seek_to_coordinate(initial_viewer_state, coord)

    def test_preserves_selection(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = select_cell(initial_viewer_state, 1, 1)
        coord = ReplayCoordinate(
            step_index=1, phase=ReplayPhase.BEFORE,
        )
        result = controller.seek_to_coordinate(state, coord)
        assert result.selected_cell == (1, 1)

    def test_preserves_playback_mode(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = set_playback_mode(initial_viewer_state, PlaybackMode.PLAYING)
        coord = ReplayCoordinate(
            step_index=1, phase=ReplayPhase.BEFORE,
        )
        result = controller.seek_to_coordinate(state, coord)
        assert result.playback_mode is PlaybackMode.PLAYING


# ---------------------------------------------------------------------------
# set_phase
# ---------------------------------------------------------------------------


class TestSetPhase:
    def test_change_phase(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        result = controller.set_phase(
            initial_viewer_state, ReplayPhase.AFTER_ACTION,
        )
        assert result.coordinate.phase is ReplayPhase.AFTER_ACTION

    def test_step_index_preserved(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = _at(initial_viewer_state, 2, ReplayPhase.BEFORE)
        result = controller.set_phase(state, ReplayPhase.AFTER_REGEN)
        assert result.coordinate.step_index == 2

    def test_delegates_correctly(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        expected = set_phase(initial_viewer_state, ReplayPhase.AFTER_REGEN)
        result = controller.set_phase(
            initial_viewer_state, ReplayPhase.AFTER_REGEN,
        )
        assert result == expected


# ---------------------------------------------------------------------------
# tick
# ---------------------------------------------------------------------------


class TestTick:
    def test_tick_playing_advances(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = set_playback_mode(initial_viewer_state, PlaybackMode.PLAYING)
        result = controller.tick(state)
        assert result.coordinate != state.coordinate

    def test_tick_paused_noop(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = set_playback_mode(initial_viewer_state, PlaybackMode.PAUSED)
        result = controller.tick(state)
        assert result is state

    def test_tick_stopped_noop(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        result = controller.tick(initial_viewer_state)
        assert result is initial_viewer_state

    def test_tick_at_final_auto_stops(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = set_playback_mode(
            _at_final(initial_viewer_state), PlaybackMode.PLAYING,
        )
        result = controller.tick(state)
        assert result.playback_mode is PlaybackMode.STOPPED
        assert result.coordinate == state.coordinate

    def test_repeated_ticks_reach_final(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = set_playback_mode(initial_viewer_state, PlaybackMode.PLAYING)
        final_coord = get_final_coordinate(state.episode_handle)
        # total_steps * 3 phases is an upper bound
        total = state.episode_handle.validation.total_steps
        max_ticks = total * 3 + 1
        for _ in range(max_ticks):
            state = controller.tick(state)
            if state.playback_mode is not PlaybackMode.PLAYING:
                break
        assert state.playback_mode is PlaybackMode.STOPPED
        assert state.coordinate == final_coord

    def test_auto_stop_is_stopped_not_paused(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = set_playback_mode(
            _at_final(initial_viewer_state), PlaybackMode.PLAYING,
        )
        result = controller.tick(state)
        assert result.playback_mode is PlaybackMode.STOPPED
        assert result.playback_mode is not PlaybackMode.PAUSED

    def test_tick_advances_through_phases(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = set_playback_mode(initial_viewer_state, PlaybackMode.PLAYING)
        # First tick: (0, BEFORE) -> (0, AFTER_REGEN)
        s1 = controller.tick(state)
        assert s1.coordinate.phase is ReplayPhase.AFTER_REGEN
        # Second tick: (0, AFTER_REGEN) -> (0, AFTER_ACTION)
        s2 = controller.tick(s1)
        assert s2.coordinate.phase is ReplayPhase.AFTER_ACTION
        # Third tick: (0, AFTER_ACTION) -> (1, BEFORE)
        s3 = controller.tick(s2)
        assert s3.coordinate.step_index == 1
        assert s3.coordinate.phase is ReplayPhase.BEFORE

    def test_tick_preserves_selection(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = set_playback_mode(
            select_cell(initial_viewer_state, 0, 0),
            PlaybackMode.PLAYING,
        )
        result = controller.tick(state)
        assert result.selected_cell == (0, 0)


# ---------------------------------------------------------------------------
# Boundary helpers
# ---------------------------------------------------------------------------


class TestBoundaryHelpers:
    def test_get_initial_coordinate(
        self, replay_episode_handle: ReplayEpisodeHandle,
    ):
        coord = get_initial_coordinate(replay_episode_handle)
        assert coord.step_index == 0
        assert coord.phase is ReplayPhase.BEFORE

    def test_get_final_coordinate(
        self, replay_episode_handle: ReplayEpisodeHandle,
    ):
        total = replay_episode_handle.validation.total_steps
        coord = get_final_coordinate(replay_episode_handle)
        assert coord.step_index == total - 1
        assert coord.phase is ReplayPhase.AFTER_ACTION

    def test_is_at_initial_true(self, initial_viewer_state: ViewerState):
        assert is_at_initial(initial_viewer_state) is True

    def test_is_at_initial_false(self, initial_viewer_state: ViewerState):
        state = _at(initial_viewer_state, 1, ReplayPhase.BEFORE)
        assert is_at_initial(state) is False

    def test_is_at_final_true(self, initial_viewer_state: ViewerState):
        state = _at_final(initial_viewer_state)
        assert is_at_final(state) is True

    def test_is_at_final_false(self, initial_viewer_state: ViewerState):
        assert is_at_final(initial_viewer_state) is False


# ---------------------------------------------------------------------------
# Transition purity
# ---------------------------------------------------------------------------


class TestPurity:
    def test_step_forward_does_not_mutate_input(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        original_coord = initial_viewer_state.coordinate
        _ = controller.step_forward(initial_viewer_state)
        assert initial_viewer_state.coordinate is original_coord

    def test_step_backward_does_not_mutate_input(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = _at(initial_viewer_state, 1, ReplayPhase.AFTER_REGEN)
        original_coord = state.coordinate
        _ = controller.step_backward(state)
        assert state.coordinate is original_coord

    def test_tick_does_not_mutate_input(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = set_playback_mode(initial_viewer_state, PlaybackMode.PLAYING)
        original_coord = state.coordinate
        _ = controller.tick(state)
        assert state.coordinate is original_coord


# ---------------------------------------------------------------------------
# Transition determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_step_forward_deterministic(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        a = controller.step_forward(initial_viewer_state)
        b = controller.step_forward(initial_viewer_state)
        assert a == b

    def test_step_backward_deterministic(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = _at(initial_viewer_state, 1, ReplayPhase.AFTER_ACTION)
        a = controller.step_backward(state)
        b = controller.step_backward(state)
        assert a == b

    def test_tick_deterministic(
        self,
        controller: PlaybackController,
        initial_viewer_state: ViewerState,
    ):
        state = set_playback_mode(initial_viewer_state, PlaybackMode.PLAYING)
        a = controller.tick(state)
        b = controller.tick(state)
        assert a == b


# ---------------------------------------------------------------------------
# UI independence
# ---------------------------------------------------------------------------


class TestUIIndependence:
    def test_no_qt_imports(self):
        """Importing playback_controller must not pull in Qt."""
        import inspect

        import axis_system_a.visualization.playback_controller as mod

        src = inspect.getsource(mod)
        assert "PySide" not in src, "playback_controller contains PySide import"
