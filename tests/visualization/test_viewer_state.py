"""Tests for VWP3 ViewerState model, PlaybackMode, and factory."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from axis_system_a.visualization.replay_models import ReplayEpisodeHandle
from axis_system_a.visualization.snapshot_models import (
    ReplayCoordinate,
    ReplayPhase,
)
from axis_system_a.visualization.viewer_state import (
    PlaybackMode,
    ViewerState,
    create_initial_state,
)


# ---------------------------------------------------------------------------
# PlaybackMode
# ---------------------------------------------------------------------------


class TestPlaybackMode:
    def test_values(self):
        assert PlaybackMode.STOPPED == "stopped"
        assert PlaybackMode.PLAYING == "playing"
        assert PlaybackMode.PAUSED == "paused"

    def test_member_count(self):
        assert len(PlaybackMode) == 3

    def test_names(self):
        assert PlaybackMode.STOPPED.name == "STOPPED"
        assert PlaybackMode.PLAYING.name == "PLAYING"
        assert PlaybackMode.PAUSED.name == "PAUSED"


# ---------------------------------------------------------------------------
# ViewerState construction
# ---------------------------------------------------------------------------


class TestViewerStateConstruction:
    def test_create_initial_state(
        self, replay_episode_handle: ReplayEpisodeHandle,
    ):
        state = create_initial_state(replay_episode_handle)
        assert state.coordinate.step_index == 0
        assert state.coordinate.phase is ReplayPhase.BEFORE
        assert state.playback_mode is PlaybackMode.STOPPED
        assert state.selected_cell is None
        assert state.selected_agent is False
        assert state.episode_handle is replay_episode_handle

    def test_frozen(self, initial_viewer_state: ViewerState):
        with pytest.raises(Exception):
            # type: ignore[misc]
            initial_viewer_state.playback_mode = PlaybackMode.PLAYING

    def test_equality(
        self, replay_episode_handle: ReplayEpisodeHandle,
    ):
        a = create_initial_state(replay_episode_handle)
        b = create_initial_state(replay_episode_handle)
        assert a == b


# ---------------------------------------------------------------------------
# ViewerState invariants
# ---------------------------------------------------------------------------


class TestViewerStateInvariants:
    def test_invalid_step_index_rejected(
        self, replay_episode_handle: ReplayEpisodeHandle,
    ):
        with pytest.raises(ValidationError):
            ViewerState(
                episode_handle=replay_episode_handle,
                coordinate=ReplayCoordinate(
                    step_index=9999, phase=ReplayPhase.BEFORE,
                ),
                playback_mode=PlaybackMode.STOPPED,
            )

    def test_step_index_at_total_rejected(
        self, replay_episode_handle: ReplayEpisodeHandle,
    ):
        total = replay_episode_handle.validation.total_steps
        with pytest.raises(ValidationError):
            ViewerState(
                episode_handle=replay_episode_handle,
                coordinate=ReplayCoordinate(
                    step_index=total, phase=ReplayPhase.BEFORE,
                ),
                playback_mode=PlaybackMode.STOPPED,
            )

    def test_selected_cell_out_of_bounds_rejected(
        self, replay_episode_handle: ReplayEpisodeHandle,
    ):
        with pytest.raises(ValidationError):
            ViewerState(
                episode_handle=replay_episode_handle,
                coordinate=ReplayCoordinate(
                    step_index=0, phase=ReplayPhase.BEFORE,
                ),
                playback_mode=PlaybackMode.STOPPED,
                selected_cell=(999, 0),
            )

    def test_selected_cell_negative_rejected(
        self, replay_episode_handle: ReplayEpisodeHandle,
    ):
        with pytest.raises(ValidationError):
            ViewerState(
                episode_handle=replay_episode_handle,
                coordinate=ReplayCoordinate(
                    step_index=0, phase=ReplayPhase.BEFORE,
                ),
                playback_mode=PlaybackMode.STOPPED,
                selected_cell=(-1, 0),
            )

    def test_valid_selected_cell_accepted(
        self, replay_episode_handle: ReplayEpisodeHandle,
    ):
        state = ViewerState(
            episode_handle=replay_episode_handle,
            coordinate=ReplayCoordinate(
                step_index=0, phase=ReplayPhase.BEFORE,
            ),
            playback_mode=PlaybackMode.STOPPED,
            selected_cell=(0, 0),
        )
        assert state.selected_cell == (0, 0)

    def test_valid_selected_cell_at_max_accepted(
        self, replay_episode_handle: ReplayEpisodeHandle,
    ):
        gw = replay_episode_handle.validation.grid_width
        gh = replay_episode_handle.validation.grid_height
        assert gw is not None and gh is not None
        state = ViewerState(
            episode_handle=replay_episode_handle,
            coordinate=ReplayCoordinate(
                step_index=0, phase=ReplayPhase.BEFORE,
            ),
            playback_mode=PlaybackMode.STOPPED,
            selected_cell=(gh - 1, gw - 1),
        )
        assert state.selected_cell == (gh - 1, gw - 1)


# ---------------------------------------------------------------------------
# ViewerState fields
# ---------------------------------------------------------------------------


class TestViewerStateFields:
    def test_all_fields_present(self):
        expected = {
            "episode_handle",
            "coordinate",
            "playback_mode",
            "selected_cell",
            "selected_agent",
            "debug_overlay_config",
        }
        assert set(ViewerState.model_fields.keys()) == expected

    def test_episode_handle_preserved(
        self, replay_episode_handle: ReplayEpisodeHandle,
    ):
        state = create_initial_state(replay_episode_handle)
        assert state.episode_handle is replay_episode_handle
