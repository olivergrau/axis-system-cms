"""Statistical summary across multiple episode comparison results (WP-run)."""

from __future__ import annotations

import statistics
from collections.abc import Sequence

from axis.framework.comparison.types import (
    MetricSummaryStats,
    PairedTraceComparisonResult,
    ResultMode,
    RunComparisonSummary,
)


def _stats(values: Sequence[float]) -> MetricSummaryStats:
    if not values:
        return MetricSummaryStats()
    n = len(values)
    m = statistics.mean(values)
    s = statistics.stdev(values) if n >= 2 else 0.0
    return MetricSummaryStats(
        mean=m, std=s, min=min(values), max=max(values), n=n,
    )


def compute_run_summary(
    results: Sequence[PairedTraceComparisonResult],
) -> RunComparisonSummary:
    valid = [r for r in results if r.result_mode ==
             ResultMode.COMPARISON_SUCCEEDED]
    n_total = len(results)
    n_valid = len(valid)
    n_invalid = n_total - n_valid

    if not valid:
        return RunComparisonSummary(
            num_episodes_compared=n_total,
            num_valid_pairs=0,
            num_invalid_pairs=n_invalid,
        )

    mismatch_rates = []
    traj_distances = []
    vit_diffs = []
    vit_deltas = []
    step_deltas = []
    ref_survived = 0
    cand_survived = 0
    cand_longer = 0
    ref_longer = 0
    equal = 0

    for r in valid:
        m = r.metrics
        o = r.outcome
        assert m is not None and o is not None

        mismatch_rates.append(m.action_divergence.action_mismatch_rate)
        traj_distances.append(m.position_divergence.mean_trajectory_distance)
        vit_diffs.append(m.vitality_divergence.mean_absolute_difference)
        vit_deltas.append(o.final_vitality_delta)
        step_deltas.append(float(o.total_steps_delta))

        if o.reference_termination_reason == "max_steps_reached":
            ref_survived += 1
        if o.candidate_termination_reason == "max_steps_reached":
            cand_survived += 1

        if o.longer_survivor == "candidate":
            cand_longer += 1
        elif o.longer_survivor == "reference":
            ref_longer += 1
        else:
            equal += 1

    return RunComparisonSummary(
        num_episodes_compared=n_total,
        num_valid_pairs=n_valid,
        num_invalid_pairs=n_invalid,
        action_mismatch_rate=_stats(mismatch_rates),
        mean_trajectory_distance=_stats(traj_distances),
        mean_vitality_difference=_stats(vit_diffs),
        final_vitality_delta=_stats(vit_deltas),
        total_steps_delta=_stats(step_deltas),
        reference_survival_rate=ref_survived / n_valid,
        candidate_survival_rate=cand_survived / n_valid,
        candidate_longer_count=cand_longer,
        reference_longer_count=ref_longer,
        equal_count=equal,
    )
