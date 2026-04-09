"""Tests for WP-V.3.3: Viewer State and State Transitions."""

from __future__ import annotations

import pytest

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
from axis.sdk.world_types import CellView

from axis.visualization.errors import CellOutOfBoundsError, StepOutOfBoundsError
from axis.visualization.replay_models import (
    ReplayEpisodeHandle,
    ReplayStepDescriptor,
    ReplayValidationResult,
)
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_snapshot(width: int = 5, height: int = 5) -> WorldSnapshot:
    cell = CellView(cell_type="empty", resource_value=0.0)
    grid = tuple(
        tuple(cell for _ in range(width))
        for _ in range(height)
    )
    return WorldSnapshot(
        grid=grid, agent_position=Position(x=0, y=0),
        width=width, height=height,
    )


def _make_step(timestep: int = 0) -> BaseStepTrace:
    snap = _make_snapshot()
    return BaseStepTrace(
        timestep=timestep, action="stay",
        world_before=snap, world_after=snap,
        agent_position_before=Position(x=0, y=0),
        agent_position_after=Position(x=0, y=0),
        vitality_before=1.0, vitality_after=0.9,
        terminated=False,
    )


def _sample_episode_handle(
    num_steps: int = 5, grid_width: int = 5, grid_height: int = 5,
) -> ReplayEpisodeHandle:
    steps = tuple(_make_step(timestep=i) for i in range(num_steps))
    episode = BaseEpisodeTrace(
        system_type="test",
        steps=steps,
        total_steps=num_steps,
        termination_reason="max_steps",
        final_vitality=0.9,
        final_position=Position(x=0, y=0),
    )
    descriptors = tuple(
        ReplayStepDescriptor(
            step_index=i, has_world_before=True, has_world_after=True,
            has_intermediate_snapshots=(), has_agent_position=True,
            has_vitality=True, has_world_state=True,
        )
        for i in range(num_steps)
    )
    validation = ReplayValidationResult(
        valid=True, total_steps=num_steps,
        grid_width=grid_width, grid_height=grid_height,
        step_descriptors=descriptors,
    )
    return ReplayEpisodeHandle(
        experiment_id="exp", run_id="run", episode_index=0,
        episode_trace=episode, validation=validation,
    )


def _initial_state(
    num_phases: int = 3, num_steps: int = 5,
) -> ViewerState:
    handle = _sample_episode_handle(num_steps)
    return create_initial_state(handle, num_phases)


# ---------------------------------------------------------------------------
# ViewerState tests
# ---------------------------------------------------------------------------


class TestViewerState:

    def test_create_initial_state(self) -> None:
        state = _initial_state()
        assert state.coordinate == ReplayCoordinate(
            step_index=0, phase_index=0)
        assert state.playback_mode == PlaybackMode.STOPPED
        assert state.selected_cell is None
        assert state.selected_agent is False

    def test_initial_state_num_phases(self) -> None:
        state = _initial_state(num_phases=3)
        assert state.num_phases == 3

    def test_step_index_out_of_bounds(self) -> None:
        handle = _sample_episode_handle(5)
        with pytest.raises(ValueError, match="step_index"):
            ViewerState(
                episode_handle=handle,
                coordinate=ReplayCoordinate(step_index=5, phase_index=0),
                playback_mode=PlaybackMode.STOPPED,
                num_phases=3,
            )

    def test_phase_index_out_of_bounds(self) -> None:
        handle = _sample_episode_handle(5)
        with pytest.raises(ValueError, match="phase_index"):
            ViewerState(
                episode_handle=handle,
                coordinate=ReplayCoordinate(step_index=0, phase_index=3),
                playback_mode=PlaybackMode.STOPPED,
                num_phases=3,
            )

    def test_selected_cell_out_of_bounds(self) -> None:
        handle = _sample_episode_handle(5, grid_width=5, grid_height=5)
        with pytest.raises(ValueError, match="selected_cell"):
            ViewerState(
                episode_handle=handle,
                coordinate=ReplayCoordinate(step_index=0, phase_index=0),
                playback_mode=PlaybackMode.STOPPED,
                num_phases=3,
                selected_cell=(10, 10),
            )

    def test_overlay_config_frozen(self) -> None:
        cfg = OverlayConfig()
        with pytest.raises(Exception):
            cfg.master_enabled = True  # type: ignore[misc]


# ---------------------------------------------------------------------------
# State transition tests
# ---------------------------------------------------------------------------


class TestTransitions:

    def test_next_step(self) -> None:
        state = _initial_state()
        new = next_step(state)
        assert new.coordinate.step_index == 1
        assert new.coordinate.phase_index == 0

    def test_next_step_at_last(self) -> None:
        state = _initial_state()
        state = seek(state, ReplayCoordinate(step_index=4, phase_index=0))
        new = next_step(state)
        assert new.coordinate.step_index == 4  # unchanged

    def test_previous_step(self) -> None:
        state = next_step(_initial_state())
        new = previous_step(state)
        assert new.coordinate.step_index == 0

    def test_previous_step_at_first(self) -> None:
        state = _initial_state()
        new = previous_step(state)
        assert new.coordinate.step_index == 0  # unchanged

    def test_set_phase(self) -> None:
        state = _initial_state()
        new = set_phase(state, 2)
        assert new.coordinate.phase_index == 2
        assert new.coordinate.step_index == 0  # step preserved

    def test_seek(self) -> None:
        state = _initial_state()
        coord = ReplayCoordinate(step_index=3, phase_index=1)
        new = seek(state, coord)
        assert new.coordinate == coord

    def test_seek_out_of_bounds(self) -> None:
        state = _initial_state()
        with pytest.raises(StepOutOfBoundsError):
            seek(state, ReplayCoordinate(step_index=10, phase_index=0))

    def test_select_cell(self) -> None:
        state = _initial_state()
        new = select_cell(state, 2, 3)
        assert new.selected_cell == (2, 3)
        assert new.selected_agent is False

    def test_select_cell_out_of_bounds(self) -> None:
        state = _initial_state()
        with pytest.raises(CellOutOfBoundsError):
            select_cell(state, 10, 10)

    def test_select_agent(self) -> None:
        state = select_cell(_initial_state(), 0, 0)
        new = select_agent(state)
        assert new.selected_agent is True
        assert new.selected_cell is None

    def test_clear_selection(self) -> None:
        state = select_cell(_initial_state(), 0, 0)
        new = clear_selection(state)
        assert new.selected_cell is None
        assert new.selected_agent is False

    def test_set_playback_mode(self) -> None:
        state = _initial_state()
        new = set_playback_mode(state, PlaybackMode.PLAYING)
        assert new.playback_mode == PlaybackMode.PLAYING

    def test_toggle_overlay_master(self) -> None:
        state = _initial_state()
        assert state.overlay_config.master_enabled is False
        new = toggle_overlay_master(state)
        assert new.overlay_config.master_enabled is True
        new2 = toggle_overlay_master(new)
        assert new2.overlay_config.master_enabled is False

    def test_set_overlay_enabled(self) -> None:
        state = _initial_state()
        new = set_overlay_enabled(state, "action_preference", True)
        assert "action_preference" in new.overlay_config.enabled_overlays

    def test_set_overlay_disabled(self) -> None:
        state = set_overlay_enabled(
            _initial_state(), "action_preference", True)
        new = set_overlay_enabled(state, "action_preference", False)
        assert "action_preference" not in new.overlay_config.enabled_overlays
