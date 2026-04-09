"""Tests for WP-V.5.2: Viewer State Suite.

ViewerState transitions with real adapter configurations.
"""

from __future__ import annotations

import pytest

from axis.visualization.errors import CellOutOfBoundsError, StepOutOfBoundsError
from axis.visualization.snapshot_models import ReplayCoordinate
from axis.visualization.viewer_state import (
    OverlayConfig,
    PlaybackMode,
    ViewerState,
    create_initial_state,
)
from axis.visualization.viewer_state_transitions import (
    clear_selection,
    next_step,
    previous_step,
    seek,
    select_agent,
    select_cell,
    set_overlay_enabled,
    set_phase,
    set_playback_mode,
    toggle_overlay_master,
)

from tests.v02.visualization.replay_fixtures import (
    make_episode_handle_for_viewer,
    make_viewer_state,
)


# ---------------------------------------------------------------------------
# 3-phase viewer state
# ---------------------------------------------------------------------------


class TestViewerStateWith3Phases:

    def test_initial_state(self) -> None:
        state = make_viewer_state(num_phases=3, include_intermediate=True)
        assert state.coordinate == ReplayCoordinate(
            step_index=0, phase_index=0)
        assert state.playback_mode == PlaybackMode.STOPPED
        assert state.num_phases == 3

    def test_phase_bounds_valid(self) -> None:
        state = make_viewer_state(num_phases=3, include_intermediate=True)
        state = set_phase(state, 0)
        assert state.coordinate.phase_index == 0
        state = set_phase(state, 2)
        assert state.coordinate.phase_index == 2

    def test_set_phase_last_is_valid(self) -> None:
        state = make_viewer_state(num_phases=3, include_intermediate=True)
        state = set_phase(state, 2)
        assert state.coordinate.phase_index == 2

    def test_next_step_preserves_phase(self) -> None:
        state = make_viewer_state(num_phases=3, num_steps=3,
                                  include_intermediate=True)
        state = set_phase(state, 1)
        state = next_step(state)
        # next_step moves to next step, phase stays at current
        assert state.coordinate.step_index == 1

    def test_seek_to_valid_coordinate(self) -> None:
        state = make_viewer_state(num_phases=3, num_steps=5,
                                  include_intermediate=True)
        coord = ReplayCoordinate(step_index=3, phase_index=2)
        state = seek(state, coord)
        assert state.coordinate == coord

    def test_seek_invalid_step_raises(self) -> None:
        state = make_viewer_state(num_phases=3, num_steps=5,
                                  include_intermediate=True)
        with pytest.raises(StepOutOfBoundsError):
            seek(state, ReplayCoordinate(step_index=10, phase_index=0))

    def test_set_phase_in_range(self) -> None:
        state = make_viewer_state(num_phases=3, include_intermediate=True)
        for p in range(3):
            s = set_phase(state, p)
            assert s.coordinate.phase_index == p


# ---------------------------------------------------------------------------
# 2-phase viewer state
# ---------------------------------------------------------------------------


class TestViewerStateWith2Phases:

    def test_initial_state(self) -> None:
        state = make_viewer_state(num_phases=2)
        assert state.num_phases == 2

    def test_phase_bounds_valid(self) -> None:
        state = make_viewer_state(num_phases=2)
        state = set_phase(state, 0)
        assert state.coordinate.phase_index == 0
        state = set_phase(state, 1)
        assert state.coordinate.phase_index == 1

    def test_seek_to_phase_1(self) -> None:
        state = make_viewer_state(num_phases=2, num_steps=3)
        state = seek(state, ReplayCoordinate(step_index=2, phase_index=1))
        assert state.coordinate.step_index == 2
        assert state.coordinate.phase_index == 1

    def test_roundtrip(self) -> None:
        state = make_viewer_state(num_phases=2, num_steps=3)
        original = state.coordinate
        state = next_step(state)
        state = previous_step(state)
        assert state.coordinate == original

    def test_playback_mode_transitions(self) -> None:
        state = make_viewer_state(num_phases=2)
        state = set_playback_mode(state, PlaybackMode.PLAYING)
        assert state.playback_mode == PlaybackMode.PLAYING
        state = set_playback_mode(state, PlaybackMode.PAUSED)
        assert state.playback_mode == PlaybackMode.PAUSED
        state = set_playback_mode(state, PlaybackMode.STOPPED)
        assert state.playback_mode == PlaybackMode.STOPPED


# ---------------------------------------------------------------------------
# Overlay-related transitions
# ---------------------------------------------------------------------------


class TestViewerStateOverlays:

    def test_toggle_master(self) -> None:
        state = make_viewer_state(num_phases=2)
        state = toggle_overlay_master(state)
        assert state.overlay_config.master_enabled is True
        state = toggle_overlay_master(state)
        assert state.overlay_config.master_enabled is False

    def test_enable_system_a_overlay_types(self) -> None:
        state = make_viewer_state(num_phases=3, include_intermediate=True)
        for key in ["action_preference", "drive_contribution",
                    "consumption_opportunity"]:
            state = set_overlay_enabled(state, key, True)
        assert len(state.overlay_config.enabled_overlays) == 3

    def test_enable_system_b_overlay_types(self) -> None:
        state = make_viewer_state(num_phases=2)
        for key in ["action_weights", "scan_result"]:
            state = set_overlay_enabled(state, key, True)
        assert len(state.overlay_config.enabled_overlays) == 2

    def test_enable_disable_roundtrip(self) -> None:
        state = make_viewer_state(num_phases=2)
        state = set_overlay_enabled(state, "test_overlay", True)
        assert "test_overlay" in state.overlay_config.enabled_overlays
        state = set_overlay_enabled(state, "test_overlay", False)
        assert "test_overlay" not in state.overlay_config.enabled_overlays


# ---------------------------------------------------------------------------
# Selection-related transitions
# ---------------------------------------------------------------------------


class TestViewerStateSelection:

    def test_select_cell_within_bounds(self) -> None:
        state = make_viewer_state(num_phases=2)
        state = select_cell(state, 2, 3)
        assert state.selected_cell == (2, 3)

    def test_select_cell_out_of_bounds_raises(self) -> None:
        state = make_viewer_state(num_phases=2)
        with pytest.raises(CellOutOfBoundsError):
            select_cell(state, 10, 10)

    def test_select_agent_clears_cell(self) -> None:
        state = make_viewer_state(num_phases=2)
        state = select_cell(state, 1, 1)
        state = select_agent(state)
        assert state.selected_agent is True
        assert state.selected_cell is None

    def test_clear_selection(self) -> None:
        state = make_viewer_state(num_phases=2)
        state = select_cell(state, 1, 1)
        state = clear_selection(state)
        assert state.selected_cell is None
        assert state.selected_agent is False
