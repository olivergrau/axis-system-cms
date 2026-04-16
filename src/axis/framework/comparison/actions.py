"""Action-space intersection and usage comparison (WP-04)."""

from __future__ import annotations

from collections import Counter

from axis.framework.comparison.types import (
    ActionUsageComparison,
    ActionUsageEntry,
    AmbiguityState,
)
from axis.sdk.trace import BaseEpisodeTrace


def _most_used(counts: Counter[str]) -> tuple[str | None, AmbiguityState | None]:
    if not counts:
        return None, AmbiguityState.NOT_APPLICABLE
    top = counts.most_common()
    if len(top) > 1 and top[0][1] == top[1][1]:
        return top[0][0], AmbiguityState.AMBIGUOUS_DUE_TO_TIE
    return top[0][0], None


def compute_action_usage(
    reference: BaseEpisodeTrace,
    candidate: BaseEpisodeTrace,
    shared_labels: tuple[str, ...],
) -> ActionUsageComparison:
    ref_counts: Counter[str] = Counter(s.action for s in reference.steps)
    cand_counts: Counter[str] = Counter(s.action for s in candidate.steps)

    ref_most, ref_amb = _most_used(ref_counts)
    cand_most, cand_amb = _most_used(cand_counts)

    shared_set = set(shared_labels)
    ref_only = sorted(set(ref_counts) - shared_set)
    cand_only = sorted(set(cand_counts) - shared_set)

    entries = tuple(
        ActionUsageEntry(
            action=a,
            reference_count=ref_counts.get(a, 0),
            candidate_count=cand_counts.get(a, 0),
            delta=cand_counts.get(a, 0) - ref_counts.get(a, 0),
        )
        for a in sorted(shared_set)
    )

    return ActionUsageComparison(
        reference_most_used=ref_most,
        reference_most_used_ambiguity=ref_amb,
        candidate_most_used=cand_most,
        candidate_most_used_ambiguity=cand_amb,
        shared_action_usage=entries,
        reference_only_actions=tuple(ref_only),
        candidate_only_actions=tuple(cand_only),
    )
