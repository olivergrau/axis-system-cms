"""Tests for WP-V.3.3: Playback Controller."""

from __future__ import annotations

import pytest

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
from axis.sdk.world_types import CellView

from axis.visualization.errors import StepOutOfBoundsError
from axis.visualization.playback_controller import (
    PlaybackController,
    get_final_coordinate,
    get_initial_coordinate,
    is_at_final,
    is_at_initial,
)
from axis.visualization.replay_models import (
    ReplayEpisodeHandle,
    ReplayStepDescriptor,
    ReplayValidationResult,
)
from axis.visualization.snapshot_models import ReplayCoordinate
from axis.visualization.viewer_state import (
    PlaybackMode,
    ViewerState,
    create_initial_state,
)
from axis.visualization.viewer_state_transitions import (
    seek,
    set_playback_mode,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_snapshot() -> WorldSnapshot:
    cell = CellView(cell_type="empty", resource_value=0.0)
    grid = tuple(
        tuple(cell for _ in range(5))
        for _ in range(5)
    )
    return WorldSnapshot(
        grid=grid, agent_position=Position(x=0, y=0), width=5, height=5,
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


def _sample_episode_handle(num_steps: int = 5) -> ReplayEpisodeHandle:
    steps = tuple(_make_step(timestep=i) for i in range(num_steps))
    episode = BaseEpisodeTrace(
        system_type="test", steps=steps, total_steps=num_steps,
        termination_reason="max_steps", final_vitality=0.9,
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
        grid_width=5, grid_height=5,
        step_descriptors=descriptors,
    )
    return ReplayEpisodeHandle(
        experiment_id="exp", run_id="run", episode_index=0,
        episode_trace=episode, validation=validation,
    )


def _state(num_phases: int = 3, num_steps: int = 5) -> ViewerState:
    return create_initial_state(_sample_episode_handle(num_steps), num_phases)


def _at(state: ViewerState, step: int, phase: int) -> ViewerState:
    return seek(state, ReplayCoordinate(step_index=step, phase_index=phase))


# ---------------------------------------------------------------------------
# 3-phase traversal
# ---------------------------------------------------------------------------


class TestTraversal3Phase:

    def test_step_forward_within_step(self) -> None:
        ctrl = PlaybackController()
        s = _state(num_phases=3)
        s1 = ctrl.step_forward(s)
        assert s1.coordinate == ReplayCoordinate(step_index=0, phase_index=1)
        s2 = ctrl.step_forward(s1)
        assert s2.coordinate == ReplayCoordinate(step_index=0, phase_index=2)

    def test_step_forward_cross_step(self) -> None:
        ctrl = PlaybackController()
        s = _at(_state(num_phases=3), 0, 2)
        new = ctrl.step_forward(s)
        assert new.coordinate == ReplayCoordinate(step_index=1, phase_index=0)

    def test_step_forward_at_final(self) -> None:
        ctrl = PlaybackController()
        s = _at(_state(num_phases=3), 4, 2)
        new = ctrl.step_forward(s)
        assert new.coordinate == ReplayCoordinate(step_index=4, phase_index=2)

    def test_step_backward_within_step(self) -> None:
        ctrl = PlaybackController()
        s = _at(_state(num_phases=3), 0, 2)
        s1 = ctrl.step_backward(s)
        assert s1.coordinate == ReplayCoordinate(step_index=0, phase_index=1)
        s2 = ctrl.step_backward(s1)
        assert s2.coordinate == ReplayCoordinate(step_index=0, phase_index=0)

    def test_step_backward_cross_step(self) -> None:
        ctrl = PlaybackController()
        s = _at(_state(num_phases=3), 1, 0)
        new = ctrl.step_backward(s)
        assert new.coordinate == ReplayCoordinate(step_index=0, phase_index=2)

    def test_step_backward_at_initial(self) -> None:
        ctrl = PlaybackController()
        s = _state(num_phases=3)
        new = ctrl.step_backward(s)
        assert new.coordinate == ReplayCoordinate(step_index=0, phase_index=0)


# ---------------------------------------------------------------------------
# 2-phase traversal
# ---------------------------------------------------------------------------


class TestTraversal2Phase:

    def test_step_forward_2phase(self) -> None:
        ctrl = PlaybackController()
        s = _state(num_phases=2)
        s1 = ctrl.step_forward(s)
        assert s1.coordinate == ReplayCoordinate(step_index=0, phase_index=1)
        s2 = ctrl.step_forward(s1)
        assert s2.coordinate == ReplayCoordinate(step_index=1, phase_index=0)

    def test_step_backward_2phase(self) -> None:
        ctrl = PlaybackController()
        s = _at(_state(num_phases=2), 1, 0)
        new = ctrl.step_backward(s)
        assert new.coordinate == ReplayCoordinate(step_index=0, phase_index=1)


# ---------------------------------------------------------------------------
# Seek and boundary
# ---------------------------------------------------------------------------


class TestSeekAndBoundary:

    def test_seek_to_step(self) -> None:
        ctrl = PlaybackController()
        s = _state(num_phases=3)
        new = ctrl.seek_to_step(s, 3)
        assert new.coordinate == ReplayCoordinate(step_index=3, phase_index=0)

    def test_seek_to_coordinate(self) -> None:
        ctrl = PlaybackController()
        s = _state(num_phases=3)
        coord = ReplayCoordinate(step_index=2, phase_index=1)
        new = ctrl.seek_to_coordinate(s, coord)
        assert new.coordinate == coord

    def test_is_at_initial(self) -> None:
        s = _state(num_phases=3)
        assert is_at_initial(s) is True
        s2 = _at(s, 1, 0)
        assert is_at_initial(s2) is False

    def test_is_at_final_3phase(self) -> None:
        s = _at(_state(num_phases=3), 4, 2)
        assert is_at_final(s) is True
        s2 = _at(_state(num_phases=3), 4, 1)
        assert is_at_final(s2) is False

    def test_is_at_final_2phase(self) -> None:
        s = _at(_state(num_phases=2), 4, 1)
        assert is_at_final(s) is True
        s2 = _at(_state(num_phases=2), 4, 0)
        assert is_at_final(s2) is False


# ---------------------------------------------------------------------------
# Tick / playback
# ---------------------------------------------------------------------------


class TestTick:

    def test_tick_stopped(self) -> None:
        ctrl = PlaybackController()
        s = _state()
        assert s.playback_mode == PlaybackMode.STOPPED
        new = ctrl.tick(s)
        assert new.coordinate == s.coordinate

    def test_tick_paused(self) -> None:
        ctrl = PlaybackController()
        s = set_playback_mode(_state(), PlaybackMode.PAUSED)
        new = ctrl.tick(s)
        assert new.coordinate == s.coordinate

    def test_tick_playing(self) -> None:
        ctrl = PlaybackController()
        s = set_playback_mode(_state(num_phases=3), PlaybackMode.PLAYING)
        new = ctrl.tick(s)
        assert new.coordinate == ReplayCoordinate(step_index=0, phase_index=1)

    def test_tick_playing_at_final(self) -> None:
        ctrl = PlaybackController()
        s = _at(_state(num_phases=3), 4, 2)
        s = set_playback_mode(s, PlaybackMode.PLAYING)
        new = ctrl.tick(s)
        assert new.playback_mode == PlaybackMode.STOPPED
        assert new.coordinate == ReplayCoordinate(step_index=4, phase_index=2)
