"""Tests for WP-V.5.2: Playback Controller Suite.

Phase-aware navigation with real system adapter phase counts.
"""

from __future__ import annotations

import pytest

from axis.visualization.playback_controller import (
    PlaybackController,
    get_final_coordinate,
    get_initial_coordinate,
    is_at_final,
    is_at_initial,
)
from axis.visualization.snapshot_models import ReplayCoordinate
from axis.visualization.viewer_state import PlaybackMode
from axis.visualization.viewer_state_transitions import (
    seek,
    set_playback_mode,
)

from tests.v02.visualization.replay_fixtures import (
    make_episode_handle_for_viewer,
    make_viewer_state,
)


# ---------------------------------------------------------------------------
# 3-phase playback
# ---------------------------------------------------------------------------


class TestPlaybackWith3Phases:

    def test_full_forward_traversal(self) -> None:
        state = make_viewer_state(num_phases=3, num_steps=3,
                                  include_intermediate=True)
        ctrl = PlaybackController()
        positions = [(state.coordinate.step_index,
                      state.coordinate.phase_index)]
        while not is_at_final(state):
            state = ctrl.step_forward(state)
            positions.append(
                (state.coordinate.step_index, state.coordinate.phase_index))
        # 3 steps × 3 phases = 9 positions
        assert len(positions) == 9

    def test_full_backward_traversal(self) -> None:
        state = make_viewer_state(num_phases=3, num_steps=3,
                                  include_intermediate=True)
        final = get_final_coordinate(state.episode_handle, 3)
        state = seek(state, final)
        ctrl = PlaybackController()
        count = 1
        while not is_at_initial(state):
            state = ctrl.step_backward(state)
            count += 1
        assert count == 9

    def test_forward_backward_roundtrip(self) -> None:
        state = make_viewer_state(num_phases=3, num_steps=3,
                                  include_intermediate=True)
        ctrl = PlaybackController()
        original = state.coordinate
        state = ctrl.step_forward(state)
        state = ctrl.step_backward(state)
        assert state.coordinate == original

    def test_tick_playing_advances(self) -> None:
        state = make_viewer_state(num_phases=3, num_steps=3,
                                  include_intermediate=True)
        state = set_playback_mode(state, PlaybackMode.PLAYING)
        ctrl = PlaybackController()
        new_state = ctrl.tick(state)
        assert new_state.coordinate != state.coordinate

    def test_tick_auto_stops_at_end(self) -> None:
        state = make_viewer_state(num_phases=3, num_steps=1,
                                  include_intermediate=True)
        final = get_final_coordinate(state.episode_handle, 3)
        state = seek(state, final)
        state = set_playback_mode(state, PlaybackMode.PLAYING)
        ctrl = PlaybackController()
        state = ctrl.tick(state)
        assert state.playback_mode == PlaybackMode.STOPPED

    def test_seek_then_forward(self) -> None:
        state = make_viewer_state(num_phases=3, num_steps=5,
                                  include_intermediate=True)
        ctrl = PlaybackController()
        state = ctrl.seek_to_step(state, 2)
        assert state.coordinate.step_index == 2
        state = ctrl.step_forward(state)
        assert state.coordinate.phase_index == 1


# ---------------------------------------------------------------------------
# 2-phase playback
# ---------------------------------------------------------------------------


class TestPlaybackWith2Phases:

    def test_forward_crosses_step_at_2_phases(self) -> None:
        state = make_viewer_state(num_phases=2, num_steps=3)
        ctrl = PlaybackController()
        # Phase 0 -> Phase 1
        state = ctrl.step_forward(state)
        assert state.coordinate == ReplayCoordinate(
            step_index=0, phase_index=1)
        # Phase 1 -> next step phase 0
        state = ctrl.step_forward(state)
        assert state.coordinate == ReplayCoordinate(
            step_index=1, phase_index=0)

    def test_backward_crosses_step(self) -> None:
        state = make_viewer_state(num_phases=2, num_steps=3)
        ctrl = PlaybackController()
        state = ctrl.seek_to_step(state, 1)
        state = ctrl.step_backward(state)
        assert state.coordinate == ReplayCoordinate(
            step_index=0, phase_index=1)

    def test_final_coordinate(self) -> None:
        handle = make_episode_handle_for_viewer(num_steps=3)
        final = get_final_coordinate(handle, 2)
        assert final == ReplayCoordinate(step_index=2, phase_index=1)

    def test_full_forward_traversal(self) -> None:
        state = make_viewer_state(num_phases=2, num_steps=3)
        ctrl = PlaybackController()
        count = 1
        while not is_at_final(state):
            state = ctrl.step_forward(state)
            count += 1
        assert count == 6  # 3 steps × 2 phases

    def test_forward_at_final_unchanged(self) -> None:
        state = make_viewer_state(num_phases=2, num_steps=2)
        final = get_final_coordinate(state.episode_handle, 2)
        state = seek(state, final)
        ctrl = PlaybackController()
        new_state = ctrl.step_forward(state)
        assert new_state is state


# ---------------------------------------------------------------------------
# Cross-phase tests
# ---------------------------------------------------------------------------


class TestPlaybackCrossPhase:

    def test_total_positions_3phase(self) -> None:
        state = make_viewer_state(num_phases=3, num_steps=4,
                                  include_intermediate=True)
        ctrl = PlaybackController()
        count = 1
        while not is_at_final(state):
            state = ctrl.step_forward(state)
            count += 1
        assert count == 12  # 4 × 3

    def test_total_positions_2phase(self) -> None:
        state = make_viewer_state(num_phases=2, num_steps=4)
        ctrl = PlaybackController()
        count = 1
        while not is_at_final(state):
            state = ctrl.step_forward(state)
            count += 1
        assert count == 8  # 4 × 2

    def test_is_at_initial_correct(self) -> None:
        state_2 = make_viewer_state(num_phases=2, num_steps=3)
        state_3 = make_viewer_state(num_phases=3, num_steps=3,
                                    include_intermediate=True)
        assert is_at_initial(state_2)
        assert is_at_initial(state_3)

    def test_is_at_final_correct(self) -> None:
        state = make_viewer_state(num_phases=2, num_steps=3)
        final = get_final_coordinate(state.episode_handle, 2)
        state = seek(state, final)
        assert is_at_final(state)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestPlaybackEdgeCases:

    def test_single_step_forward_backward(self) -> None:
        state = make_viewer_state(num_phases=2, num_steps=1)
        ctrl = PlaybackController()
        state = ctrl.step_forward(state)
        assert state.coordinate.phase_index == 1
        state = ctrl.step_forward(state)  # at final, no change
        assert is_at_final(state)
        state = ctrl.step_backward(state)
        assert state.coordinate.phase_index == 0
        state = ctrl.step_backward(state)  # at initial, no change
        assert is_at_initial(state)

    def test_seek_to_last_step(self) -> None:
        state = make_viewer_state(num_phases=2, num_steps=5)
        ctrl = PlaybackController()
        state = ctrl.seek_to_step(state, 4)
        assert state.coordinate.step_index == 4
        state = ctrl.step_forward(state)
        assert state.coordinate.phase_index == 1
        assert is_at_final(state)

    def test_paused_tick_noop(self) -> None:
        state = make_viewer_state(num_phases=2, num_steps=3)
        state = set_playback_mode(state, PlaybackMode.PAUSED)
        ctrl = PlaybackController()
        new_state = ctrl.tick(state)
        assert new_state is state
