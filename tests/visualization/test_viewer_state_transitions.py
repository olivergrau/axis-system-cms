"""Tests for VWP3 viewer state transition functions."""

from __future__ import annotations

import pytest

from axis_system_a.visualization.errors import (
    CellOutOfBoundsError,
    StepOutOfBoundsError,
)
from axis_system_a.visualization.snapshot_models import (
    ReplayCoordinate,
    ReplayPhase,
)
from axis_system_a.visualization.viewer_state import (
    PlaybackMode,
    ViewerState,
)
from axis_system_a.visualization.viewer_state_transitions import (
    clear_selection,
    next_step,
    previous_step,
    seek,
    select_agent,
    select_cell,
    set_phase,
    set_playback_mode,
)


# ---------------------------------------------------------------------------
# next_step
# ---------------------------------------------------------------------------


class TestNextStep:
    def test_advance_from_zero(self, initial_viewer_state: ViewerState):
        result = next_step(initial_viewer_state)
        assert result.coordinate.step_index == 1

    def test_phase_preserved(self, initial_viewer_state: ViewerState):
        state = set_phase(initial_viewer_state, ReplayPhase.AFTER_ACTION)
        result = next_step(state)
        assert result.coordinate.phase is ReplayPhase.AFTER_ACTION

    def test_clamp_at_last_step(self, initial_viewer_state: ViewerState):
        total = initial_viewer_state.episode_handle.validation.total_steps
        last_coord = ReplayCoordinate(
            step_index=total - 1, phase=ReplayPhase.BEFORE,
        )
        state = seek(initial_viewer_state, last_coord)
        result = next_step(state)
        assert result is state  # identity — clamped

    def test_returns_new_instance(self, initial_viewer_state: ViewerState):
        result = next_step(initial_viewer_state)
        assert result is not initial_viewer_state

    def test_selection_preserved(self, initial_viewer_state: ViewerState):
        state = select_cell(initial_viewer_state, 0, 0)
        result = next_step(state)
        assert result.selected_cell == (0, 0)

    def test_playback_mode_preserved(self, initial_viewer_state: ViewerState):
        state = set_playback_mode(initial_viewer_state, PlaybackMode.PLAYING)
        result = next_step(state)
        assert result.playback_mode is PlaybackMode.PLAYING


# ---------------------------------------------------------------------------
# previous_step
# ---------------------------------------------------------------------------


class TestPreviousStep:
    def test_decrement_from_one(self, initial_viewer_state: ViewerState):
        state = next_step(initial_viewer_state)
        result = previous_step(state)
        assert result.coordinate.step_index == 0

    def test_phase_preserved(self, initial_viewer_state: ViewerState):
        state = set_phase(
            next_step(initial_viewer_state), ReplayPhase.AFTER_REGEN,
        )
        result = previous_step(state)
        assert result.coordinate.phase is ReplayPhase.AFTER_REGEN

    def test_clamp_at_zero(self, initial_viewer_state: ViewerState):
        result = previous_step(initial_viewer_state)
        assert result is initial_viewer_state  # identity — clamped

    def test_returns_new_instance(self, initial_viewer_state: ViewerState):
        state = next_step(initial_viewer_state)
        result = previous_step(state)
        assert result is not state

    def test_selection_preserved(self, initial_viewer_state: ViewerState):
        state = select_agent(next_step(initial_viewer_state))
        result = previous_step(state)
        assert result.selected_agent is True

    def test_playback_mode_preserved(self, initial_viewer_state: ViewerState):
        state = set_playback_mode(
            next_step(initial_viewer_state), PlaybackMode.PAUSED,
        )
        result = previous_step(state)
        assert result.playback_mode is PlaybackMode.PAUSED


# ---------------------------------------------------------------------------
# set_phase
# ---------------------------------------------------------------------------


class TestSetPhase:
    def test_change_to_after_regen(self, initial_viewer_state: ViewerState):
        result = set_phase(initial_viewer_state, ReplayPhase.AFTER_REGEN)
        assert result.coordinate.phase is ReplayPhase.AFTER_REGEN

    def test_change_to_after_action(self, initial_viewer_state: ViewerState):
        result = set_phase(initial_viewer_state, ReplayPhase.AFTER_ACTION)
        assert result.coordinate.phase is ReplayPhase.AFTER_ACTION

    def test_change_to_before(self, initial_viewer_state: ViewerState):
        state = set_phase(initial_viewer_state, ReplayPhase.AFTER_ACTION)
        result = set_phase(state, ReplayPhase.BEFORE)
        assert result.coordinate.phase is ReplayPhase.BEFORE

    def test_step_index_preserved(self, initial_viewer_state: ViewerState):
        state = next_step(initial_viewer_state)
        result = set_phase(state, ReplayPhase.AFTER_ACTION)
        assert result.coordinate.step_index == 1

    def test_same_phase_returns_equal_state(
        self, initial_viewer_state: ViewerState,
    ):
        result = set_phase(initial_viewer_state, ReplayPhase.BEFORE)
        assert result == initial_viewer_state


# ---------------------------------------------------------------------------
# seek
# ---------------------------------------------------------------------------


class TestSeek:
    def test_seek_to_valid_coordinate(self, initial_viewer_state: ViewerState):
        coord = ReplayCoordinate(
            step_index=1, phase=ReplayPhase.AFTER_REGEN,
        )
        result = seek(initial_viewer_state, coord)
        assert result.coordinate == coord

    def test_seek_to_first_step(self, initial_viewer_state: ViewerState):
        state = next_step(initial_viewer_state)
        coord = ReplayCoordinate(
            step_index=0, phase=ReplayPhase.BEFORE,
        )
        result = seek(state, coord)
        assert result.coordinate.step_index == 0

    def test_seek_to_last_step(self, initial_viewer_state: ViewerState):
        total = initial_viewer_state.episode_handle.validation.total_steps
        coord = ReplayCoordinate(
            step_index=total - 1, phase=ReplayPhase.AFTER_ACTION,
        )
        result = seek(initial_viewer_state, coord)
        assert result.coordinate.step_index == total - 1
        assert result.coordinate.phase is ReplayPhase.AFTER_ACTION

    def test_seek_out_of_bounds_raises(
        self, initial_viewer_state: ViewerState,
    ):
        total = initial_viewer_state.episode_handle.validation.total_steps
        coord = ReplayCoordinate(
            step_index=total, phase=ReplayPhase.BEFORE,
        )
        with pytest.raises(StepOutOfBoundsError):
            seek(initial_viewer_state, coord)

    def test_seek_far_out_of_range_raises(
        self, initial_viewer_state: ViewerState,
    ):
        coord = ReplayCoordinate(
            step_index=9999, phase=ReplayPhase.BEFORE,
        )
        with pytest.raises(StepOutOfBoundsError):
            seek(initial_viewer_state, coord)

    def test_seek_error_carries_context(
        self, initial_viewer_state: ViewerState,
    ):
        total = initial_viewer_state.episode_handle.validation.total_steps
        coord = ReplayCoordinate(
            step_index=total, phase=ReplayPhase.BEFORE,
        )
        with pytest.raises(StepOutOfBoundsError) as exc_info:
            seek(initial_viewer_state, coord)
        assert exc_info.value.step_index == total
        assert exc_info.value.total_steps == total

    def test_seek_preserves_selection(
        self, initial_viewer_state: ViewerState,
    ):
        state = select_cell(initial_viewer_state, 0, 0)
        coord = ReplayCoordinate(
            step_index=1, phase=ReplayPhase.BEFORE,
        )
        result = seek(state, coord)
        assert result.selected_cell == (0, 0)

    def test_seek_preserves_playback_mode(
        self, initial_viewer_state: ViewerState,
    ):
        state = set_playback_mode(initial_viewer_state, PlaybackMode.PLAYING)
        coord = ReplayCoordinate(
            step_index=1, phase=ReplayPhase.BEFORE,
        )
        result = seek(state, coord)
        assert result.playback_mode is PlaybackMode.PLAYING


# ---------------------------------------------------------------------------
# select_cell
# ---------------------------------------------------------------------------


class TestSelectCell:
    def test_select_valid_cell(self, initial_viewer_state: ViewerState):
        result = select_cell(initial_viewer_state, 1, 2)
        assert result.selected_cell == (1, 2)

    def test_select_cell_clears_agent(self, initial_viewer_state: ViewerState):
        state = select_agent(initial_viewer_state)
        result = select_cell(state, 0, 0)
        assert result.selected_agent is False

    def test_select_origin(self, initial_viewer_state: ViewerState):
        result = select_cell(initial_viewer_state, 0, 0)
        assert result.selected_cell == (0, 0)

    def test_select_max_corner(self, initial_viewer_state: ViewerState):
        gw = initial_viewer_state.episode_handle.validation.grid_width
        gh = initial_viewer_state.episode_handle.validation.grid_height
        assert gw is not None and gh is not None
        result = select_cell(initial_viewer_state, gh - 1, gw - 1)
        assert result.selected_cell == (gh - 1, gw - 1)

    def test_select_cell_out_of_bounds_raises(
        self, initial_viewer_state: ViewerState,
    ):
        with pytest.raises(CellOutOfBoundsError):
            select_cell(initial_viewer_state, 999, 0)

    def test_select_cell_negative_raises(
        self, initial_viewer_state: ViewerState,
    ):
        with pytest.raises(CellOutOfBoundsError):
            select_cell(initial_viewer_state, -1, 0)

    def test_error_carries_context(self, initial_viewer_state: ViewerState):
        with pytest.raises(CellOutOfBoundsError) as exc_info:
            select_cell(initial_viewer_state, 999, 888)
        assert exc_info.value.row == 999
        assert exc_info.value.col == 888

    def test_coordinate_preserved(self, initial_viewer_state: ViewerState):
        state = next_step(initial_viewer_state)
        result = select_cell(state, 0, 0)
        assert result.coordinate.step_index == 1

    def test_playback_mode_preserved(self, initial_viewer_state: ViewerState):
        state = set_playback_mode(initial_viewer_state, PlaybackMode.PLAYING)
        result = select_cell(state, 0, 0)
        assert result.playback_mode is PlaybackMode.PLAYING


# ---------------------------------------------------------------------------
# select_agent
# ---------------------------------------------------------------------------


class TestSelectAgent:
    def test_select_agent_sets_flag(self, initial_viewer_state: ViewerState):
        result = select_agent(initial_viewer_state)
        assert result.selected_agent is True

    def test_select_agent_clears_cell(self, initial_viewer_state: ViewerState):
        state = select_cell(initial_viewer_state, 0, 0)
        result = select_agent(state)
        assert result.selected_cell is None

    def test_coordinate_preserved(self, initial_viewer_state: ViewerState):
        state = next_step(initial_viewer_state)
        result = select_agent(state)
        assert result.coordinate.step_index == 1

    def test_playback_mode_preserved(self, initial_viewer_state: ViewerState):
        state = set_playback_mode(initial_viewer_state, PlaybackMode.PAUSED)
        result = select_agent(state)
        assert result.playback_mode is PlaybackMode.PAUSED


# ---------------------------------------------------------------------------
# clear_selection
# ---------------------------------------------------------------------------


class TestClearSelection:
    def test_clears_cell(self, initial_viewer_state: ViewerState):
        state = select_cell(initial_viewer_state, 0, 0)
        result = clear_selection(state)
        assert result.selected_cell is None

    def test_clears_agent(self, initial_viewer_state: ViewerState):
        state = select_agent(initial_viewer_state)
        result = clear_selection(state)
        assert result.selected_agent is False

    def test_from_cell_selected(self, initial_viewer_state: ViewerState):
        state = select_cell(initial_viewer_state, 1, 1)
        result = clear_selection(state)
        assert result.selected_cell is None
        assert result.selected_agent is False

    def test_from_agent_selected(self, initial_viewer_state: ViewerState):
        state = select_agent(initial_viewer_state)
        result = clear_selection(state)
        assert result.selected_cell is None
        assert result.selected_agent is False

    def test_from_nothing_selected(self, initial_viewer_state: ViewerState):
        result = clear_selection(initial_viewer_state)
        assert result.selected_cell is None
        assert result.selected_agent is False

    def test_coordinate_preserved(self, initial_viewer_state: ViewerState):
        state = select_cell(next_step(initial_viewer_state), 0, 0)
        result = clear_selection(state)
        assert result.coordinate.step_index == 1

    def test_playback_mode_preserved(self, initial_viewer_state: ViewerState):
        state = set_playback_mode(
            select_agent(initial_viewer_state), PlaybackMode.PLAYING,
        )
        result = clear_selection(state)
        assert result.playback_mode is PlaybackMode.PLAYING


# ---------------------------------------------------------------------------
# set_playback_mode
# ---------------------------------------------------------------------------


class TestSetPlaybackMode:
    def test_set_playing(self, initial_viewer_state: ViewerState):
        result = set_playback_mode(initial_viewer_state, PlaybackMode.PLAYING)
        assert result.playback_mode is PlaybackMode.PLAYING

    def test_set_paused(self, initial_viewer_state: ViewerState):
        result = set_playback_mode(initial_viewer_state, PlaybackMode.PAUSED)
        assert result.playback_mode is PlaybackMode.PAUSED

    def test_set_stopped(self, initial_viewer_state: ViewerState):
        state = set_playback_mode(initial_viewer_state, PlaybackMode.PLAYING)
        result = set_playback_mode(state, PlaybackMode.STOPPED)
        assert result.playback_mode is PlaybackMode.STOPPED

    def test_coordinate_preserved(self, initial_viewer_state: ViewerState):
        state = next_step(initial_viewer_state)
        result = set_playback_mode(state, PlaybackMode.PLAYING)
        assert result.coordinate.step_index == 1

    def test_selection_preserved(self, initial_viewer_state: ViewerState):
        state = select_cell(initial_viewer_state, 0, 0)
        result = set_playback_mode(state, PlaybackMode.PLAYING)
        assert result.selected_cell == (0, 0)


# ---------------------------------------------------------------------------
# Transition purity
# ---------------------------------------------------------------------------


class TestTransitionPurity:
    def test_original_state_unchanged_after_next_step(
        self, initial_viewer_state: ViewerState,
    ):
        original_coord = initial_viewer_state.coordinate
        _ = next_step(initial_viewer_state)
        assert initial_viewer_state.coordinate is original_coord

    def test_original_state_unchanged_after_seek(
        self, initial_viewer_state: ViewerState,
    ):
        original_coord = initial_viewer_state.coordinate
        coord = ReplayCoordinate(
            step_index=1, phase=ReplayPhase.AFTER_ACTION,
        )
        _ = seek(initial_viewer_state, coord)
        assert initial_viewer_state.coordinate is original_coord

    def test_original_state_unchanged_after_select_cell(
        self, initial_viewer_state: ViewerState,
    ):
        assert initial_viewer_state.selected_cell is None
        _ = select_cell(initial_viewer_state, 0, 0)
        assert initial_viewer_state.selected_cell is None


# ---------------------------------------------------------------------------
# Transition determinism
# ---------------------------------------------------------------------------


class TestTransitionDeterminism:
    def test_same_input_same_output_next_step(
        self, initial_viewer_state: ViewerState,
    ):
        a = next_step(initial_viewer_state)
        b = next_step(initial_viewer_state)
        assert a == b

    def test_same_input_same_output_seek(
        self, initial_viewer_state: ViewerState,
    ):
        coord = ReplayCoordinate(
            step_index=1, phase=ReplayPhase.AFTER_REGEN,
        )
        a = seek(initial_viewer_state, coord)
        b = seek(initial_viewer_state, coord)
        assert a == b
