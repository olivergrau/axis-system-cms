"""Tests for WP-V.3.2: Generalized Snapshot Resolver."""

from __future__ import annotations

import pytest

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
from axis.sdk.world_types import CellView

from axis.visualization.errors import (
    PhaseNotAvailableError,
    StepOutOfBoundsError,
)
from axis.visualization.snapshot_models import ReplayCoordinate, ReplaySnapshot
from axis.visualization.snapshot_resolver import SnapshotResolver


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_snapshot(
    width: int = 5, height: int = 5, marker: float = 0.0,
) -> WorldSnapshot:
    cell = CellView(cell_type="empty", resource_value=marker)
    grid = tuple(
        tuple(cell for _ in range(width))
        for _ in range(height)
    )
    return WorldSnapshot(
        grid=grid, agent_position=Position(x=0, y=0),
        width=width, height=height,
    )


def _make_step(
    timestep: int = 0,
    *,
    world_before: WorldSnapshot | None = None,
    world_after: WorldSnapshot | None = None,
    pos_before: Position | None = None,
    pos_after: Position | None = None,
    vitality_before: float = 1.0,
    vitality_after: float = 0.8,
    intermediate_snapshots: dict[str, WorldSnapshot] | None = None,
    action: str = "stay",
    terminated: bool = False,
    termination_reason: str | None = None,
) -> BaseStepTrace:
    return BaseStepTrace(
        timestep=timestep,
        action=action,
        world_before=world_before or _make_snapshot(marker=0.1),
        world_after=world_after or _make_snapshot(marker=0.9),
        intermediate_snapshots=intermediate_snapshots or {},
        agent_position_before=pos_before or Position(x=1, y=1),
        agent_position_after=pos_after or Position(x=2, y=1),
        vitality_before=vitality_before,
        vitality_after=vitality_after,
        terminated=terminated,
        termination_reason=termination_reason,
    )


def _make_episode(steps: list[BaseStepTrace]) -> BaseEpisodeTrace:
    return BaseEpisodeTrace(
        system_type="test",
        steps=tuple(steps),
        total_steps=len(steps),
        termination_reason="max_steps",
        final_vitality=0.8,
        final_position=Position(x=0, y=0),
    )


def _sample_episode_2phase(num_steps: int = 5) -> BaseEpisodeTrace:
    """Episode for 2-phase system (System B pattern)."""
    steps = [_make_step(timestep=i) for i in range(num_steps)]
    return _make_episode(steps)


def _sample_episode_3phase(num_steps: int = 5) -> BaseEpisodeTrace:
    """Episode for 3-phase system (System A pattern) with intermediates."""
    steps = []
    for i in range(num_steps):
        intermediate = _make_snapshot(marker=0.5)
        steps.append(_make_step(
            timestep=i,
            intermediate_snapshots={"AFTER_REGEN": intermediate},
        ))
    return _make_episode(steps)


PHASES_2 = ["BEFORE", "AFTER_ACTION"]
PHASES_3 = ["BEFORE", "AFTER_REGEN", "AFTER_ACTION"]


# ---------------------------------------------------------------------------
# Coordinate model tests
# ---------------------------------------------------------------------------


class TestReplayCoordinate:

    def test_creation(self) -> None:
        coord = ReplayCoordinate(step_index=0, phase_index=0)
        assert coord.step_index == 0
        assert coord.phase_index == 0

    def test_frozen(self) -> None:
        coord = ReplayCoordinate(step_index=0, phase_index=0)
        with pytest.raises(Exception):
            coord.step_index = 1  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Snapshot model tests
# ---------------------------------------------------------------------------


class TestReplaySnapshot:

    def test_fields(self) -> None:
        snap = ReplaySnapshot(
            step_index=2,
            phase_index=1,
            phase_name="AFTER_REGEN",
            timestep=2,
            world_snapshot=_make_snapshot(),
            agent_position=Position(x=1, y=1),
            vitality=0.9,
            action="right",
            terminated=False,
            termination_reason=None,
        )
        assert snap.step_index == 2
        assert snap.phase_index == 1
        assert snap.phase_name == "AFTER_REGEN"
        assert snap.agent_position == Position(x=1, y=1)
        assert snap.vitality == 0.9

    def test_has_phase_name(self) -> None:
        snap = ReplaySnapshot(
            step_index=0,
            phase_index=0,
            phase_name="BEFORE",
            timestep=0,
            world_snapshot=_make_snapshot(),
            agent_position=Position(x=0, y=0),
            vitality=1.0,
            action="stay",
            terminated=False,
            termination_reason=None,
        )
        assert snap.phase_name == "BEFORE"


# ---------------------------------------------------------------------------
# 2-phase resolver tests (System B pattern)
# ---------------------------------------------------------------------------


class TestResolver2Phase:

    def test_resolve_before(self) -> None:
        episode = _sample_episode_2phase()
        resolver = SnapshotResolver()
        snap = resolver.resolve(episode, 0, 0, PHASES_2)
        # Phase 0 → world_before, position_before, vitality_before
        assert snap.world_snapshot == episode.steps[0].world_before
        assert snap.agent_position == episode.steps[0].agent_position_before
        assert snap.vitality == episode.steps[0].vitality_before

    def test_resolve_after_action(self) -> None:
        episode = _sample_episode_2phase()
        resolver = SnapshotResolver()
        snap = resolver.resolve(episode, 0, 1, PHASES_2)
        # Phase 1 (N-1) → world_after, position_after, vitality_after
        assert snap.world_snapshot == episode.steps[0].world_after
        assert snap.agent_position == episode.steps[0].agent_position_after
        assert snap.vitality == episode.steps[0].vitality_after

    def test_resolve_invalid_phase(self) -> None:
        episode = _sample_episode_2phase()
        resolver = SnapshotResolver()
        with pytest.raises(PhaseNotAvailableError):
            resolver.resolve(episode, 0, 2, PHASES_2)


# ---------------------------------------------------------------------------
# 3-phase resolver tests (System A pattern)
# ---------------------------------------------------------------------------


class TestResolver3Phase:

    def test_resolve_before(self) -> None:
        episode = _sample_episode_3phase()
        resolver = SnapshotResolver()
        snap = resolver.resolve(episode, 0, 0, PHASES_3)
        assert snap.world_snapshot == episode.steps[0].world_before
        assert snap.agent_position == episode.steps[0].agent_position_before

    def test_resolve_intermediate(self) -> None:
        episode = _sample_episode_3phase()
        resolver = SnapshotResolver()
        snap = resolver.resolve(episode, 0, 1, PHASES_3)
        # Intermediate → intermediate_snapshots["AFTER_REGEN"]
        expected = episode.steps[0].intermediate_snapshots["AFTER_REGEN"]
        assert snap.world_snapshot == expected
        # Intermediate uses "before" agent state
        assert snap.agent_position == episode.steps[0].agent_position_before
        assert snap.vitality == episode.steps[0].vitality_before

    def test_resolve_after_action(self) -> None:
        episode = _sample_episode_3phase()
        resolver = SnapshotResolver()
        snap = resolver.resolve(episode, 0, 2, PHASES_3)
        assert snap.world_snapshot == episode.steps[0].world_after
        assert snap.agent_position == episode.steps[0].agent_position_after

    def test_missing_intermediate(self) -> None:
        # Episode without intermediate snapshots
        episode = _sample_episode_2phase()  # no intermediates in these steps
        resolver = SnapshotResolver()
        with pytest.raises(PhaseNotAvailableError):
            resolver.resolve(episode, 0, 1, PHASES_3)


# ---------------------------------------------------------------------------
# Boundary tests
# ---------------------------------------------------------------------------


class TestBoundary:

    def test_step_out_of_bounds_negative(self) -> None:
        resolver = SnapshotResolver()
        with pytest.raises(StepOutOfBoundsError):
            resolver.resolve(_sample_episode_2phase(), -1, 0, PHASES_2)

    def test_step_out_of_bounds_too_large(self) -> None:
        episode = _sample_episode_2phase(num_steps=5)
        resolver = SnapshotResolver()
        with pytest.raises(StepOutOfBoundsError):
            resolver.resolve(episode, 5, 0, PHASES_2)

    def test_resolve_first_step(self) -> None:
        resolver = SnapshotResolver()
        snap = resolver.resolve(_sample_episode_2phase(), 0, 0, PHASES_2)
        assert snap.step_index == 0

    def test_resolve_last_step(self) -> None:
        episode = _sample_episode_2phase(num_steps=5)
        resolver = SnapshotResolver()
        snap = resolver.resolve(episode, 4, 0, PHASES_2)
        assert snap.step_index == 4


# ---------------------------------------------------------------------------
# Phase name passthrough tests
# ---------------------------------------------------------------------------


class TestPhaseNamePassthrough:

    def test_phase_name_before(self) -> None:
        resolver = SnapshotResolver()
        snap = resolver.resolve(_sample_episode_3phase(), 0, 0, PHASES_3)
        assert snap.phase_name == "BEFORE"

    def test_phase_name_intermediate(self) -> None:
        resolver = SnapshotResolver()
        snap = resolver.resolve(_sample_episode_3phase(), 0, 1, PHASES_3)
        assert snap.phase_name == "AFTER_REGEN"

    def test_phase_name_after_action(self) -> None:
        resolver = SnapshotResolver()
        snap = resolver.resolve(_sample_episode_3phase(), 0, 2, PHASES_3)
        assert snap.phase_name == "AFTER_ACTION"


# ---------------------------------------------------------------------------
# Action context tests
# ---------------------------------------------------------------------------


class TestActionContext:

    def test_action_from_step(self) -> None:
        steps = [_make_step(timestep=0, action="right")]
        episode = _make_episode(steps)
        resolver = SnapshotResolver()
        snap = resolver.resolve(episode, 0, 0, PHASES_2)
        assert snap.action == "right"

    def test_terminated_from_step(self) -> None:
        steps = [_make_step(timestep=0, terminated=True)]
        episode = _make_episode(steps)
        resolver = SnapshotResolver()
        snap = resolver.resolve(episode, 0, 0, PHASES_2)
        assert snap.terminated is True

    def test_termination_reason_from_step(self) -> None:
        steps = [_make_step(
            timestep=0, terminated=True,
            termination_reason="starvation",
        )]
        episode = _make_episode(steps)
        resolver = SnapshotResolver()
        snap = resolver.resolve(episode, 0, 0, PHASES_2)
        assert snap.termination_reason == "starvation"
