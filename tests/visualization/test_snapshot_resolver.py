"""Tests for the VWP2 SnapshotResolver."""

from __future__ import annotations

import pytest

from axis_system_a.visualization.errors import (
    PhaseNotAvailableError,
    StepOutOfBoundsError,
)
from axis_system_a.visualization.replay_models import ReplayEpisodeHandle
from axis_system_a.visualization.snapshot_models import ReplayPhase
from axis_system_a.visualization.snapshot_resolver import SnapshotResolver


# ---------------------------------------------------------------------------
# Happy-path resolution
# ---------------------------------------------------------------------------


class TestHappyPath:
    def test_resolve_first_step_before(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        snap = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.BEFORE,
        )
        step = replay_episode_handle.episode_result.steps[0]
        assert snap.grid == step.transition_trace.world_before.grid

    def test_resolve_first_step_after_regen(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        snap = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.AFTER_REGEN,
        )
        step = replay_episode_handle.episode_result.steps[0]
        assert snap.grid == step.transition_trace.world_after_regen.grid

    def test_resolve_first_step_after_action(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        snap = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.AFTER_ACTION,
        )
        step = replay_episode_handle.episode_result.steps[0]
        assert snap.grid == step.transition_trace.world_after_action.grid

    def test_resolve_last_step(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        last = len(replay_episode_handle.episode_result.steps) - 1
        for phase in ReplayPhase:
            snap = snapshot_resolver.resolve(
                replay_episode_handle, last, phase,
            )
            assert snap.step_index == last


# ---------------------------------------------------------------------------
# Phase-to-field mapping (critical correctness)
# ---------------------------------------------------------------------------


class TestPhaseMapping:
    def test_before_uses_position_before(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        snap = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.BEFORE,
        )
        tt = replay_episode_handle.episode_result.steps[0].transition_trace
        assert snap.agent_position == tt.position_before

    def test_before_uses_energy_before(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        snap = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.BEFORE,
        )
        step = replay_episode_handle.episode_result.steps[0]
        assert snap.agent_energy == step.energy_before

    def test_after_regen_uses_position_before(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        snap = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.AFTER_REGEN,
        )
        tt = replay_episode_handle.episode_result.steps[0].transition_trace
        assert snap.agent_position == tt.position_before

    def test_after_regen_uses_energy_before(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        snap = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.AFTER_REGEN,
        )
        step = replay_episode_handle.episode_result.steps[0]
        assert snap.agent_energy == step.energy_before

    def test_after_action_uses_position_after(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        snap = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.AFTER_ACTION,
        )
        tt = replay_episode_handle.episode_result.steps[0].transition_trace
        assert snap.agent_position == tt.position_after

    def test_after_action_uses_energy_after(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        snap = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.AFTER_ACTION,
        )
        step = replay_episode_handle.episode_result.steps[0]
        assert snap.agent_energy == step.energy_after


# ---------------------------------------------------------------------------
# Action context
# ---------------------------------------------------------------------------


class TestActionContext:
    def test_action_matches_step(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        snap = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.BEFORE,
        )
        tt = replay_episode_handle.episode_result.steps[0].transition_trace
        assert snap.action == tt.action

    def test_moved_flag_matches(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        snap = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.BEFORE,
        )
        tt = replay_episode_handle.episode_result.steps[0].transition_trace
        assert snap.moved == tt.moved

    def test_consumed_flag_matches(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        snap = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.BEFORE,
        )
        tt = replay_episode_handle.episode_result.steps[0].transition_trace
        assert snap.consumed == tt.consumed

    def test_energy_delta_matches(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        snap = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.BEFORE,
        )
        tt = replay_episode_handle.episode_result.steps[0].transition_trace
        assert snap.energy_delta == tt.energy_delta

    def test_terminated_matches(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        snap = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.BEFORE,
        )
        step = replay_episode_handle.episode_result.steps[0]
        assert snap.terminated == step.terminated

    def test_termination_reason_matches(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        snap = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.BEFORE,
        )
        tt = replay_episode_handle.episode_result.steps[0].transition_trace
        assert snap.termination_reason == tt.termination_reason


# ---------------------------------------------------------------------------
# Boundary conditions
# ---------------------------------------------------------------------------


class TestBoundaryConditions:
    def test_step_negative_raises(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        with pytest.raises(StepOutOfBoundsError):
            snapshot_resolver.resolve(
                replay_episode_handle, -1, ReplayPhase.BEFORE,
            )

    def test_step_equal_total_raises(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        total = len(replay_episode_handle.episode_result.steps)
        with pytest.raises(StepOutOfBoundsError):
            snapshot_resolver.resolve(
                replay_episode_handle, total, ReplayPhase.BEFORE,
            )

    def test_step_far_out_of_range_raises(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        with pytest.raises(StepOutOfBoundsError):
            snapshot_resolver.resolve(
                replay_episode_handle, 9999, ReplayPhase.BEFORE,
            )

    def test_error_carries_context(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        total = len(replay_episode_handle.episode_result.steps)
        with pytest.raises(StepOutOfBoundsError) as exc_info:
            snapshot_resolver.resolve(
                replay_episode_handle, total, ReplayPhase.BEFORE,
            )
        assert exc_info.value.step_index == total
        assert exc_info.value.total_steps == total


# ---------------------------------------------------------------------------
# Phase not available
# ---------------------------------------------------------------------------


class TestPhaseNotAvailable:
    def test_broken_phase_raises(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        """Corrupt a world snapshot, then resolve — must raise."""
        episode = replay_episode_handle.episode_result
        steps = list(episode.steps)
        tt = steps[0].transition_trace
        broken = tt.world_before.model_copy(
            update={"grid": (), "width": 0, "height": 0},
        )
        bad_tt = tt.model_copy(update={"world_before": broken})
        steps[0] = steps[0].model_copy(update={"transition_trace": bad_tt})
        bad_episode = episode.model_copy(update={"steps": tuple(steps)})

        from axis_system_a.visualization.replay_validation import (
            validate_episode_for_replay,
        )
        bad_handle = ReplayEpisodeHandle(
            experiment_id=replay_episode_handle.experiment_id,
            run_id=replay_episode_handle.run_id,
            episode_index=replay_episode_handle.episode_index,
            episode_result=bad_episode,
            validation=validate_episode_for_replay(bad_episode),
        )
        with pytest.raises(PhaseNotAvailableError):
            snapshot_resolver.resolve(bad_handle, 0, ReplayPhase.BEFORE)

    def test_error_carries_context(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        episode = replay_episode_handle.episode_result
        steps = list(episode.steps)
        tt = steps[0].transition_trace
        broken = tt.world_after_regen.model_copy(
            update={"grid": (), "width": 0, "height": 0},
        )
        bad_tt = tt.model_copy(update={"world_after_regen": broken})
        steps[0] = steps[0].model_copy(update={"transition_trace": bad_tt})
        bad_episode = episode.model_copy(update={"steps": tuple(steps)})

        from axis_system_a.visualization.replay_validation import (
            validate_episode_for_replay,
        )
        bad_handle = ReplayEpisodeHandle(
            experiment_id=replay_episode_handle.experiment_id,
            run_id=replay_episode_handle.run_id,
            episode_index=replay_episode_handle.episode_index,
            episode_result=bad_episode,
            validation=validate_episode_for_replay(bad_episode),
        )
        with pytest.raises(PhaseNotAvailableError) as exc_info:
            snapshot_resolver.resolve(
                bad_handle, 0, ReplayPhase.AFTER_REGEN,
            )
        assert exc_info.value.step_index == 0
        assert exc_info.value.phase is ReplayPhase.AFTER_REGEN


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_identical_output_on_repeated_calls(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        a = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.BEFORE,
        )
        b = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.BEFORE,
        )
        assert a == b


# ---------------------------------------------------------------------------
# Integrity — no transformation drift
# ---------------------------------------------------------------------------


class TestIntegrity:
    def test_grid_exact_match(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        snap = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.BEFORE,
        )
        source_grid = (
            replay_episode_handle
            .episode_result.steps[0]
            .transition_trace.world_before.grid
        )
        assert snap.grid == source_grid

    def test_dimensions_match_source(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        snap = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.BEFORE,
        )
        ws = (
            replay_episode_handle
            .episode_result.steps[0]
            .transition_trace.world_before
        )
        assert snap.grid_width == ws.width
        assert snap.grid_height == ws.height

    def test_step_index_matches_request(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        snap = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.AFTER_ACTION,
        )
        assert snap.step_index == 0

    def test_phase_matches_request(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        snap = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.AFTER_ACTION,
        )
        assert snap.phase is ReplayPhase.AFTER_ACTION

    def test_timestep_matches_step_result(
        self, snapshot_resolver: SnapshotResolver,
        replay_episode_handle: ReplayEpisodeHandle,
    ):
        snap = snapshot_resolver.resolve(
            replay_episode_handle, 0, ReplayPhase.BEFORE,
        )
        step = replay_episode_handle.episode_result.steps[0]
        assert snap.timestep == step.timestep
