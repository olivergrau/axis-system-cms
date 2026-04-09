"""Generalized snapshot resolver for the Visualization Layer.

Maps (episode, step_index, phase_index, phase_names) to a fully
resolved ReplaySnapshot. Supports variable phase counts per system.
"""

from __future__ import annotations

from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace

from axis.visualization.errors import (
    PhaseNotAvailableError,
    StepOutOfBoundsError,
)
from axis.visualization.snapshot_models import ReplaySnapshot


class SnapshotResolver:
    """Resolves (episode, step_index, phase_index) -> ReplaySnapshot.

    Pure, stateless resolver. The phase_names list determines how
    phase_index maps to world snapshots and agent state.
    """

    def resolve(
        self,
        episode: BaseEpisodeTrace,
        step_index: int,
        phase_index: int,
        phase_names: list[str],
    ) -> ReplaySnapshot:
        """Resolve a single replay coordinate to a snapshot.

        Args:
            episode: The loaded episode trace.
            step_index: Index into episode.steps.
            phase_index: 0-based phase index (0 to len(phase_names)-1).
            phase_names: System adapter's phase name list.

        Raises:
            StepOutOfBoundsError: step_index is invalid.
            PhaseNotAvailableError: phase has no valid snapshot.
        """
        total = len(episode.steps)
        if step_index < 0 or step_index >= total:
            raise StepOutOfBoundsError(step_index, total)

        num_phases = len(phase_names)
        if phase_index < 0 or phase_index >= num_phases:
            raise PhaseNotAvailableError(step_index, phase_index)

        step = episode.steps[step_index]

        # Phase mapping (Section 13.2 of architecture spec)
        world_snapshot, position, vitality = self._resolve_phase(
            step, phase_index, num_phases, phase_names, step_index,
        )

        return ReplaySnapshot(
            step_index=step_index,
            phase_index=phase_index,
            phase_name=phase_names[phase_index],
            timestep=step.timestep,
            world_snapshot=world_snapshot,
            agent_position=position,
            vitality=vitality,
            action=step.action,
            terminated=step.terminated,
            termination_reason=step.termination_reason,
        )

    @staticmethod
    def _resolve_phase(
        step: BaseStepTrace,
        phase_index: int,
        num_phases: int,
        phase_names: list[str],
        step_index: int,
    ) -> tuple:
        """Map phase_index to (WorldSnapshot, Position, vitality).

        Phase 0 (first): world_before, position_before, vitality_before
        Phase N-1 (last): world_after, position_after, vitality_after
        Phase 1..N-2 (intermediate): intermediate_snapshots[name],
            position_before, vitality_before
        """
        if phase_index == 0:
            # First phase: BEFORE
            return (
                step.world_before,
                step.agent_position_before,
                step.vitality_before,
            )

        if phase_index == num_phases - 1:
            # Last phase: AFTER_ACTION
            return (
                step.world_after,
                step.agent_position_after,
                step.vitality_after,
            )

        # Intermediate phase: lookup by name
        name = phase_names[phase_index]
        snapshot = step.intermediate_snapshots.get(name)
        if snapshot is None:
            raise PhaseNotAvailableError(step_index, phase_index)

        return (
            snapshot,
            step.agent_position_before,
            step.vitality_before,
        )
