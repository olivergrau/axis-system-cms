"""Deterministic snapshot resolver for the Visualization Layer (VWP2).

Maps a validated episode + replay coordinate to a fully resolved
ReplaySnapshot.  Stateless and pure — same inputs always yield
identical output.
"""

from __future__ import annotations

from axis_system_a.results import StepResult
from axis_system_a.snapshots import WorldSnapshot
from axis_system_a.transition import TransitionTrace
from axis_system_a.types import Position

from axis_system_a.visualization.errors import (
    PhaseNotAvailableError,
    StepOutOfBoundsError,
)
from axis_system_a.visualization.replay_models import ReplayEpisodeHandle
from axis_system_a.visualization.snapshot_models import (
    ReplayPhase,
    ReplaySnapshot,
)


def _is_valid_snapshot(snapshot: WorldSnapshot) -> bool:
    """Check that a WorldSnapshot has a non-empty, well-dimensioned grid."""
    return (
        snapshot.width > 0
        and snapshot.height > 0
        and len(snapshot.grid) > 0
        and len(snapshot.grid[0]) > 0
    )


def _select_world_snapshot(
    tt: TransitionTrace, phase: ReplayPhase,
) -> WorldSnapshot:
    """Return the WorldSnapshot for *phase*."""
    if phase is ReplayPhase.BEFORE:
        return tt.world_before
    if phase is ReplayPhase.AFTER_REGEN:
        return tt.world_after_regen
    return tt.world_after_action


def _select_agent_state(
    step: StepResult, tt: TransitionTrace, phase: ReplayPhase,
) -> tuple[Position, float]:
    """Return (position, energy) appropriate for *phase*.

    BEFORE and AFTER_REGEN: agent has not acted yet → before values.
    AFTER_ACTION: agent has acted → after values.
    """
    if phase is ReplayPhase.AFTER_ACTION:
        return tt.position_after, step.energy_after
    return tt.position_before, step.energy_before


class SnapshotResolver:
    """Resolves (episode, step_index, phase) → ReplaySnapshot.

    Pure, stateless resolver.  No caching, no inference, no mutation.
    """

    def resolve(
        self,
        episode_handle: ReplayEpisodeHandle,
        step_index: int,
        phase: ReplayPhase,
    ) -> ReplaySnapshot:
        """Resolve a single replay coordinate to a snapshot.

        Raises StepOutOfBoundsError if *step_index* is invalid.
        Raises PhaseNotAvailableError if the requested phase has no
        valid world snapshot data.
        """
        steps = episode_handle.episode_result.steps
        total = len(steps)

        if step_index < 0 or step_index >= total:
            raise StepOutOfBoundsError(step_index, total)

        step = steps[step_index]
        tt = step.transition_trace

        # Resolve world snapshot for the requested phase.
        world = _select_world_snapshot(tt, phase)
        if not _is_valid_snapshot(world):
            raise PhaseNotAvailableError(step_index, phase)

        # Resolve agent state for the requested phase.
        position, energy = _select_agent_state(step, tt, phase)

        return ReplaySnapshot(
            step_index=step_index,
            phase=phase,
            timestep=step.timestep,
            grid=world.grid,
            grid_width=world.width,
            grid_height=world.height,
            agent_position=position,
            agent_energy=energy,
            action=tt.action,
            moved=tt.moved,
            consumed=tt.consumed,
            resource_consumed=tt.resource_consumed,
            energy_delta=tt.energy_delta,
            terminated=step.terminated,
            termination_reason=tt.termination_reason,
        )
