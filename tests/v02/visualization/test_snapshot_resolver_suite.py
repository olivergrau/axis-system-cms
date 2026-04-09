"""Tests for WP-V.5.2: Snapshot Resolver Suite.

Cross-system snapshot resolution with real system adapter phase names.
"""

from __future__ import annotations

import pytest

from axis.visualization.errors import PhaseNotAvailableError, StepOutOfBoundsError
from axis.visualization.snapshot_resolver import SnapshotResolver

from tests.v02.visualization.replay_fixtures import (
    SYSTEM_A_PHASES,
    SYSTEM_B_PHASES,
    make_2phase_episode,
    make_3phase_episode,
)


# ---------------------------------------------------------------------------
# With System A phases (3-phase)
# ---------------------------------------------------------------------------


class TestResolverWithSystemAPhases:

    def test_phase_0_resolves_world_before(self) -> None:
        ep = make_3phase_episode(num_steps=3)
        snap = SnapshotResolver().resolve(ep, 0, 0, SYSTEM_A_PHASES)
        # world_before has marker_resource=0.1
        assert snap.world_snapshot.grid[0][0].resource_value == pytest.approx(
            0.1)

    def test_phase_1_resolves_intermediate(self) -> None:
        ep = make_3phase_episode(num_steps=3)
        snap = SnapshotResolver().resolve(ep, 0, 1, SYSTEM_A_PHASES)
        # intermediate has marker_resource=0.5
        assert snap.world_snapshot.grid[0][0].resource_value == pytest.approx(
            0.5)

    def test_phase_2_resolves_world_after(self) -> None:
        ep = make_3phase_episode(num_steps=3)
        snap = SnapshotResolver().resolve(ep, 0, 2, SYSTEM_A_PHASES)
        # world_after has marker_resource=0.9
        assert snap.world_snapshot.grid[0][0].resource_value == pytest.approx(
            0.9)

    def test_vitality_before_for_phase_0(self) -> None:
        ep = make_3phase_episode(num_steps=3)
        snap = SnapshotResolver().resolve(ep, 0, 0, SYSTEM_A_PHASES)
        assert snap.vitality == ep.steps[0].vitality_before

    def test_vitality_after_for_last_phase(self) -> None:
        ep = make_3phase_episode(num_steps=3)
        snap = SnapshotResolver().resolve(ep, 0, 2, SYSTEM_A_PHASES)
        assert snap.vitality == ep.steps[0].vitality_after

    def test_all_steps_all_phases_resolve(self) -> None:
        ep = make_3phase_episode(num_steps=5)
        resolver = SnapshotResolver()
        for step_idx in range(5):
            for phase_idx in range(3):
                snap = resolver.resolve(
                    ep, step_idx, phase_idx, SYSTEM_A_PHASES)
                assert snap is not None

    def test_phase_name_matches(self) -> None:
        ep = make_3phase_episode(num_steps=3)
        for phase_idx, name in enumerate(SYSTEM_A_PHASES):
            snap = SnapshotResolver().resolve(ep, 0, phase_idx, SYSTEM_A_PHASES)
            assert snap.phase_name == name


# ---------------------------------------------------------------------------
# With System B phases (2-phase)
# ---------------------------------------------------------------------------


class TestResolverWithSystemBPhases:

    def test_phase_0_resolves_world_before(self) -> None:
        ep = make_2phase_episode(num_steps=3)
        snap = SnapshotResolver().resolve(ep, 0, 0, SYSTEM_B_PHASES)
        assert snap.world_snapshot.grid[0][0].resource_value == pytest.approx(
            0.1)

    def test_phase_1_resolves_world_after(self) -> None:
        ep = make_2phase_episode(num_steps=3)
        snap = SnapshotResolver().resolve(ep, 0, 1, SYSTEM_B_PHASES)
        assert snap.world_snapshot.grid[0][0].resource_value == pytest.approx(
            0.9)

    def test_no_intermediate_phase(self) -> None:
        ep = make_2phase_episode(num_steps=3)
        with pytest.raises(PhaseNotAvailableError):
            SnapshotResolver().resolve(ep, 0, 2, SYSTEM_B_PHASES)

    def test_all_steps_resolve_both_phases(self) -> None:
        ep = make_2phase_episode(num_steps=5)
        resolver = SnapshotResolver()
        for step_idx in range(5):
            for phase_idx in range(2):
                snap = resolver.resolve(
                    ep, step_idx, phase_idx, SYSTEM_B_PHASES)
                assert snap is not None

    def test_phase_names_match(self) -> None:
        ep = make_2phase_episode(num_steps=3)
        for phase_idx, name in enumerate(SYSTEM_B_PHASES):
            snap = SnapshotResolver().resolve(ep, 0, phase_idx, SYSTEM_B_PHASES)
            assert snap.phase_name == name


# ---------------------------------------------------------------------------
# Cross-system tests
# ---------------------------------------------------------------------------


class TestResolverCrossSystem:

    def test_step_out_of_bounds_consistent(self) -> None:
        ep = make_3phase_episode(num_steps=3)
        with pytest.raises(StepOutOfBoundsError):
            SnapshotResolver().resolve(ep, 10, 0, SYSTEM_A_PHASES)
        with pytest.raises(StepOutOfBoundsError):
            SnapshotResolver().resolve(ep, 10, 0, SYSTEM_B_PHASES)

    def test_invalid_phase_for_3phase(self) -> None:
        ep = make_3phase_episode(num_steps=3)
        with pytest.raises(PhaseNotAvailableError):
            SnapshotResolver().resolve(ep, 0, 3, SYSTEM_A_PHASES)

    def test_invalid_phase_for_2phase(self) -> None:
        ep = make_2phase_episode(num_steps=3)
        with pytest.raises(PhaseNotAvailableError):
            SnapshotResolver().resolve(ep, 0, 2, SYSTEM_B_PHASES)

    def test_null_adapter_same_as_system_b(self) -> None:
        null_phases = ["BEFORE", "AFTER_ACTION"]
        ep = make_2phase_episode(num_steps=3)
        snap_b = SnapshotResolver().resolve(ep, 0, 0, SYSTEM_B_PHASES)
        snap_n = SnapshotResolver().resolve(ep, 0, 0, null_phases)
        assert snap_b.world_snapshot == snap_n.world_snapshot

    def test_same_episode_different_phases(self) -> None:
        ep = make_3phase_episode(num_steps=3)
        # 3-phase: phase 2 gives world_after
        snap_3 = SnapshotResolver().resolve(ep, 0, 2, SYSTEM_A_PHASES)
        # 2-phase: phase 1 gives world_after
        snap_2 = SnapshotResolver().resolve(ep, 0, 1, SYSTEM_B_PHASES)
        assert snap_3.world_snapshot == snap_2.world_snapshot


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestResolverEdgeCases:

    def test_single_step_episode(self) -> None:
        ep = make_2phase_episode(num_steps=1)
        snap = SnapshotResolver().resolve(ep, 0, 0, SYSTEM_B_PHASES)
        assert snap.step_index == 0

    def test_terminated_step(self) -> None:
        ep = make_2phase_episode(num_steps=1)
        snap = SnapshotResolver().resolve(ep, 0, 1, SYSTEM_B_PHASES)
        assert snap.terminated is True

    def test_action_from_step(self) -> None:
        ep = make_2phase_episode(num_steps=3)
        snap = SnapshotResolver().resolve(ep, 0, 0, SYSTEM_B_PHASES)
        assert snap.action == "stay"
