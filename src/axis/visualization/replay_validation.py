"""Replay contract validation for episode traces.

Validates that a BaseEpisodeTrace satisfies all requirements for
deterministic replay: step ordering, world state presence, agent
state, and grid dimension consistency.
"""

from __future__ import annotations

from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseEpisodeTrace

from axis.visualization.replay_models import (
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
    episode: BaseEpisodeTrace,
) -> ReplayValidationResult:
    """Validate an episode trace against the replay contract.

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

    # 2. Step ordering: monotonic, contiguous, no duplicates
    seen_timesteps: set[int] = set()
    base_timestep = steps[0].timestep

    for i, step in enumerate(steps):
        t = step.timestep

        if t in seen_timesteps:
            violations.append(f"Duplicate timestep {t}")
        seen_timesteps.add(t)

        if i > 0 and t <= steps[i - 1].timestep:
            violations.append(
                f"Step ordering violation at index {i}: "
                f"timestep {t} is not greater than {steps[i - 1].timestep}"
            )

        expected = base_timestep + i
        if t != expected:
            violations.append(
                f"Step index gap: expected timestep {expected} "
                f"at index {i}, got {t}"
            )

    # 3. Per-step validation
    for i, step in enumerate(steps):
        # World state validation
        before_ok = _is_valid_snapshot(step.world_before)
        after_ok = _is_valid_snapshot(step.world_after)

        if not before_ok:
            violations.append(
                f"Missing or invalid world_before at step {i}"
            )
        if not after_ok:
            violations.append(
                f"Missing or invalid world_after at step {i}"
            )

        # Intermediate snapshots (check each if present)
        intermediate_names: list[str] = []
        for name, snapshot in step.intermediate_snapshots.items():
            if _is_valid_snapshot(snapshot):
                intermediate_names.append(name)

        # Vitality validation
        has_vitality = (
            0.0 <= step.vitality_before <= 1.0
            and 0.0 <= step.vitality_after <= 1.0
        )
        if not has_vitality:
            violations.append(
                f"Invalid vitality at step {i}: "
                f"before={step.vitality_before}, after={step.vitality_after}"
            )

        # Agent position (always present by model constraint)
        has_position = True

        # World state present (at least one valid snapshot)
        has_world = before_ok or after_ok

        step_descriptors.append(
            ReplayStepDescriptor(
                step_index=i,
                has_world_before=before_ok,
                has_world_after=after_ok,
                has_intermediate_snapshots=tuple(sorted(intermediate_names)),
                has_agent_position=has_position,
                has_vitality=has_vitality,
                has_world_state=has_world,
            )
        )

        # Grid dimension consistency
        for phase_name, snapshot, phase_ok in [
            ("world_before", step.world_before, before_ok),
            ("world_after", step.world_after, after_ok),
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
