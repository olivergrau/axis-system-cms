"""Strict replay contract validation for episode artifacts.

Validates that an EpisodeResult satisfies all requirements for
deterministic replay: step ordering, phase availability, world state
presence, agent state, and grid dimension consistency.

Validation collects all violations rather than failing on the first one,
providing complete diagnostics for invalid artifacts.
"""

from __future__ import annotations

from axis_system_a.results import EpisodeResult
from axis_system_a.snapshots import WorldSnapshot

from axis_system_a.visualization.replay_models import (
    ReplayPhaseAvailability,
    ReplayStepDescriptor,
    ReplayValidationResult,
)


def _is_valid_snapshot(snapshot: WorldSnapshot) -> bool:
    """Check that a WorldSnapshot has a non-empty, well-dimensioned grid."""
    return (
        snapshot.width > 0
        and snapshot.height > 0
        and len(snapshot.grid) > 0
        and len(snapshot.grid[0]) > 0
    )


def validate_episode_for_replay(
    episode: EpisodeResult,
) -> ReplayValidationResult:
    """Validate an episode against the replay contract.

    Returns a ReplayValidationResult with valid=True if all checks pass,
    or valid=False with a tuple of human-readable violation descriptions.
    """
    violations: list[str] = []
    step_descriptors: list[ReplayStepDescriptor] = []
    grid_width: int | None = None
    grid_height: int | None = None

    steps = episode.steps

    # 1. Non-empty steps
    if len(steps) == 0:
        return ReplayValidationResult(
            valid=False,
            total_steps=0,
            violations=("Episode contains no steps",),
        )

    # 2 + 3 + 4. Step ordering, contiguity, and duplicate checks
    seen_timesteps: set[int] = set()
    base_timestep = steps[0].timestep

    for i, step in enumerate(steps):
        t = step.timestep

        # Duplicate check
        if t in seen_timesteps:
            violations.append(f"Duplicate timestep {t}")
        seen_timesteps.add(t)

        # Monotonic ordering
        if i > 0 and t <= steps[i - 1].timestep:
            violations.append(
                f"Step ordering violation at index {i}: "
                f"timestep {t} is not greater than {steps[i - 1].timestep}"
            )

        # Contiguity
        expected = base_timestep + i
        if t != expected:
            violations.append(
                f"Step index gap: expected timestep {expected} "
                f"at index {i}, got {t}"
            )

    # 5-9. Per-step validation
    for i, step in enumerate(steps):
        tt = step.transition_trace

        # Phase availability
        before_ok = _is_valid_snapshot(tt.world_before)
        after_regen_ok = _is_valid_snapshot(tt.world_after_regen)
        after_action_ok = _is_valid_snapshot(tt.world_after_action)

        phase_avail = ReplayPhaseAvailability(
            before=before_ok,
            after_regen=after_regen_ok,
            after_action=after_action_ok,
        )

        if not before_ok:
            violations.append(
                f"Missing or invalid world_before at step {i}"
            )
        if not after_regen_ok:
            violations.append(
                f"Missing or invalid world_after_regen at step {i}"
            )
        if not after_action_ok:
            violations.append(
                f"Missing or invalid world_after_action at step {i}"
            )

        # Agent energy
        has_energy = step.energy_before >= 0 and step.energy_after >= 0
        if not has_energy:
            violations.append(
                f"Invalid agent energy at step {i}: "
                f"before={step.energy_before}, after={step.energy_after}"
            )

        # Agent position (always present by model, but explicit check)
        has_position = (
            tt.position_before is not None and tt.position_after is not None
        )

        # World state present (at least one valid phase)
        has_world = before_ok or after_regen_ok or after_action_ok

        step_descriptors.append(
            ReplayStepDescriptor(
                step_index=step.timestep,
                phase_availability=phase_avail,
                has_agent_position=has_position,
                has_agent_energy=has_energy,
                has_world_state=has_world,
            )
        )

        # Grid dimension consistency
        for phase_name, snapshot, phase_ok in [
            ("world_before", tt.world_before, before_ok),
            ("world_after_regen", tt.world_after_regen, after_regen_ok),
            ("world_after_action", tt.world_after_action, after_action_ok),
        ]:
            if not phase_ok:
                continue
            w, h = snapshot.width, snapshot.height
            if grid_width is None:
                grid_width = w
                grid_height = h
            elif (w, h) != (grid_width, grid_height):
                violations.append(
                    f"Inconsistent grid dimensions: expected "
                    f"{grid_width}x{grid_height}, got {w}x{h} "
                    f"at step {i}, phase {phase_name}"
                )

    return ReplayValidationResult(
        valid=len(violations) == 0,
        total_steps=len(steps),
        grid_width=grid_width,
        grid_height=grid_height,
        violations=tuple(violations),
        step_descriptors=tuple(step_descriptors),
    )
