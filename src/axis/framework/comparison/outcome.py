"""Outcome comparison for paired traces (WP-06)."""

from __future__ import annotations

from typing import Literal

from axis.framework.comparison.types import OutcomeComparison
from axis.sdk.trace import BaseEpisodeTrace


def compute_outcome(
    reference: BaseEpisodeTrace, candidate: BaseEpisodeTrace,
) -> OutcomeComparison:
    delta_v = candidate.final_vitality - reference.final_vitality
    delta_s = candidate.total_steps - reference.total_steps

    longer: Literal["reference", "candidate", "equal"]
    if reference.total_steps > candidate.total_steps:
        longer = "reference"
    elif candidate.total_steps > reference.total_steps:
        longer = "candidate"
    else:
        longer = "equal"

    return OutcomeComparison(
        reference_termination_reason=reference.termination_reason,
        candidate_termination_reason=candidate.termination_reason,
        reference_final_vitality=reference.final_vitality,
        candidate_final_vitality=candidate.final_vitality,
        final_vitality_delta=delta_v,
        reference_total_steps=reference.total_steps,
        candidate_total_steps=candidate.total_steps,
        total_steps_delta=delta_s,
        longer_survivor=longer,
    )
