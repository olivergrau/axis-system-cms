"""Shared-prefix alignment for paired traces (WP-03)."""

from __future__ import annotations

from collections.abc import Iterator

from axis.framework.comparison.types import AlignmentSummary
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace


def compute_alignment(
    reference: BaseEpisodeTrace, candidate: BaseEpisodeTrace,
) -> AlignmentSummary:
    n_ref = len(reference.steps)
    n_cand = len(candidate.steps)
    n_align = min(n_ref, n_cand)
    return AlignmentSummary(
        reference_total_steps=n_ref,
        candidate_total_steps=n_cand,
        aligned_steps=n_align,
        reference_extra_steps=n_ref - n_align,
        candidate_extra_steps=n_cand - n_align,
    )


def iter_aligned_steps(
    reference: BaseEpisodeTrace, candidate: BaseEpisodeTrace,
) -> Iterator[tuple[BaseStepTrace, BaseStepTrace]]:
    n = min(len(reference.steps), len(candidate.steps))
    for i in range(n):
        yield reference.steps[i], candidate.steps[i]
