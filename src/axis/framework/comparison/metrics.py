"""Divergence metrics: action, position, vitality (WP-05)."""

from __future__ import annotations

from collections.abc import Sequence

from axis.framework.comparison.alignment import iter_aligned_steps
from axis.framework.comparison.types import (
    ActionDivergence,
    PositionDivergence,
    VitalityDivergence,
)
from axis.sdk.trace import BaseEpisodeTrace


def compute_action_divergence(
    reference: BaseEpisodeTrace, candidate: BaseEpisodeTrace,
) -> ActionDivergence:
    first_div: int | None = None
    mismatch = 0
    total = 0
    for ref_step, cand_step in iter_aligned_steps(reference, candidate):
        if ref_step.action != cand_step.action:
            mismatch += 1
            if first_div is None:
                first_div = ref_step.timestep
        total += 1
    rate = mismatch / total if total > 0 else 0.0
    return ActionDivergence(
        first_action_divergence_step=first_div,
        action_mismatch_count=mismatch,
        action_mismatch_rate=rate,
    )


def compute_position_divergence(
    reference: BaseEpisodeTrace, candidate: BaseEpisodeTrace,
) -> PositionDivergence:
    distances: list[int] = []
    for ref_step, cand_step in iter_aligned_steps(reference, candidate):
        rp = ref_step.agent_position_after
        cp = cand_step.agent_position_after
        distances.append(abs(rp.x - cp.x) + abs(rp.y - cp.y))
    if not distances:
        return PositionDivergence()
    return PositionDivergence(
        distance_series=tuple(distances),
        mean_trajectory_distance=sum(distances) / len(distances),
        max_trajectory_distance=max(distances),
    )


def compute_vitality_divergence(
    reference: BaseEpisodeTrace, candidate: BaseEpisodeTrace,
) -> VitalityDivergence:
    diffs: list[float] = []
    for ref_step, cand_step in iter_aligned_steps(reference, candidate):
        diffs.append(cand_step.vitality_after - ref_step.vitality_after)
    if not diffs:
        return VitalityDivergence()
    abs_diffs = [abs(d) for d in diffs]
    return VitalityDivergence(
        difference_series=tuple(diffs),
        mean_absolute_difference=sum(abs_diffs) / len(abs_diffs),
        max_absolute_difference=max(abs_diffs),
    )
