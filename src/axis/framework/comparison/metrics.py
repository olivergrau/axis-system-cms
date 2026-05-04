"""Divergence metrics: action, position, vitality (WP-05)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from axis.framework.comparison.actions import compute_action_usage

from axis.framework.comparison.alignment import iter_aligned_steps
from axis.framework.comparison.types import (
    ActionDivergence,
    GenericComparisonMetrics,
    PositionDivergence,
    VitalityDivergence,
)
from axis.sdk.trace import BaseEpisodeTrace


@dataclass(frozen=True)
class _AlignedMetricScan:
    first_action_divergence_step: int | None
    action_mismatch_count: int
    aligned_step_count: int
    distance_series: tuple[int, ...]
    vitality_difference_series: tuple[float, ...]


def _scan_aligned_metrics(
    reference: BaseEpisodeTrace,
    candidate: BaseEpisodeTrace,
) -> _AlignedMetricScan:
    first_div: int | None = None
    mismatch = 0
    total = 0
    distances: list[int] = []
    vitality_diffs: list[float] = []

    for ref_step, cand_step in iter_aligned_steps(reference, candidate):
        if ref_step.action != cand_step.action:
            mismatch += 1
            if first_div is None:
                first_div = ref_step.timestep

        rp = ref_step.agent_position_after
        cp = cand_step.agent_position_after
        distances.append(abs(rp.x - cp.x) + abs(rp.y - cp.y))
        vitality_diffs.append(cand_step.vitality_after - ref_step.vitality_after)
        total += 1

    return _AlignedMetricScan(
        first_action_divergence_step=first_div,
        action_mismatch_count=mismatch,
        aligned_step_count=total,
        distance_series=tuple(distances),
        vitality_difference_series=tuple(vitality_diffs),
    )


def _build_action_divergence(scan: _AlignedMetricScan) -> ActionDivergence:
    total = scan.aligned_step_count
    rate = scan.action_mismatch_count / total if total > 0 else 0.0
    return ActionDivergence(
        first_action_divergence_step=scan.first_action_divergence_step,
        action_mismatch_count=scan.action_mismatch_count,
        action_mismatch_rate=rate,
    )


def _build_position_divergence(scan: _AlignedMetricScan) -> PositionDivergence:
    distances = scan.distance_series
    if not distances:
        return PositionDivergence()
    return PositionDivergence(
        distance_series=distances,
        mean_trajectory_distance=sum(distances) / len(distances),
        max_trajectory_distance=max(distances),
    )


def _build_vitality_divergence(scan: _AlignedMetricScan) -> VitalityDivergence:
    diffs = scan.vitality_difference_series
    if not diffs:
        return VitalityDivergence()
    abs_diffs = [abs(d) for d in diffs]
    return VitalityDivergence(
        difference_series=diffs,
        mean_absolute_difference=sum(abs_diffs) / len(abs_diffs),
        max_absolute_difference=max(abs_diffs),
    )


def compute_action_divergence(
    reference: BaseEpisodeTrace, candidate: BaseEpisodeTrace,
) -> ActionDivergence:
    return _build_action_divergence(_scan_aligned_metrics(reference, candidate))


def compute_position_divergence(
    reference: BaseEpisodeTrace, candidate: BaseEpisodeTrace,
) -> PositionDivergence:
    return _build_position_divergence(_scan_aligned_metrics(reference, candidate))


def compute_vitality_divergence(
    reference: BaseEpisodeTrace, candidate: BaseEpisodeTrace,
) -> VitalityDivergence:
    return _build_vitality_divergence(_scan_aligned_metrics(reference, candidate))


def compute_generic_comparison_metrics(
    reference: BaseEpisodeTrace,
    candidate: BaseEpisodeTrace,
    shared_action_labels: Sequence[str],
) -> GenericComparisonMetrics:
    """Compute all generic comparison metrics with a single aligned-step scan."""
    scan = _scan_aligned_metrics(reference, candidate)
    return GenericComparisonMetrics(
        action_divergence=_build_action_divergence(scan),
        position_divergence=_build_position_divergence(scan),
        vitality_divergence=_build_vitality_divergence(scan),
        action_usage=compute_action_usage(reference, candidate, tuple(shared_action_labels)),
    )
