"""Top-level trace comparison entry point (WP-07)."""

from __future__ import annotations

from axis.framework.comparison.actions import compute_action_usage
from axis.framework.comparison.alignment import compute_alignment
from axis.framework.comparison.extensions import build_system_specific_analysis
from axis.framework.comparison.metrics import (
    compute_action_divergence,
    compute_position_divergence,
    compute_vitality_divergence,
)
from axis.framework.comparison.outcome import compute_outcome
from axis.framework.comparison.types import (
    GenericComparisonMetrics,
    PairedTraceComparisonResult,
    PairIdentity,
    PairingMode,
    ResultMode,
)
from axis.framework.comparison.validation import validate_trace_pair
from axis.framework.persistence import RunMetadata
from axis.framework.run import RunConfig
from axis.sdk.trace import BaseEpisodeTrace

# Ensure System C extension is registered on import.
import axis.framework.comparison.system_c_extension as _  # noqa: F401


def compare_episode_traces(
    reference_trace: BaseEpisodeTrace,
    candidate_trace: BaseEpisodeTrace,
    *,
    reference_run_config: RunConfig | None = None,
    candidate_run_config: RunConfig | None = None,
    reference_run_metadata: RunMetadata | None = None,
    candidate_run_metadata: RunMetadata | None = None,
    reference_episode_index: int | None = None,
    candidate_episode_index: int | None = None,
) -> PairedTraceComparisonResult:
    """Compare two episode traces and return a structured result."""
    validation, pairing_mode, episode_seed = validate_trace_pair(
        reference_trace,
        candidate_trace,
        reference_run_config=reference_run_config,
        candidate_run_config=candidate_run_config,
        reference_run_metadata=reference_run_metadata,
        candidate_run_metadata=candidate_run_metadata,
        reference_episode_index=reference_episode_index,
        candidate_episode_index=candidate_episode_index,
    )

    identity = PairIdentity(
        reference_system_type=reference_trace.system_type,
        candidate_system_type=candidate_trace.system_type,
        reference_run_id=(
            reference_run_metadata.run_id if reference_run_metadata else None
        ),
        candidate_run_id=(
            candidate_run_metadata.run_id if candidate_run_metadata else None
        ),
        reference_episode_index=reference_episode_index,
        candidate_episode_index=candidate_episode_index,
        episode_seed=episode_seed,
        pairing_mode=pairing_mode,
    )

    if not validation.is_valid_pair:
        return PairedTraceComparisonResult(
            result_mode=ResultMode.COMPARISON_FAILED_VALIDATION,
            identity=identity,
            validation=validation,
        )

    alignment = compute_alignment(reference_trace, candidate_trace)

    action_div = compute_action_divergence(reference_trace, candidate_trace)
    pos_div = compute_position_divergence(reference_trace, candidate_trace)
    vit_div = compute_vitality_divergence(reference_trace, candidate_trace)
    action_usage = compute_action_usage(
        reference_trace, candidate_trace, validation.shared_action_labels,
    )

    metrics = GenericComparisonMetrics(
        action_divergence=action_div,
        position_divergence=pos_div,
        vitality_divergence=vit_div,
        action_usage=action_usage,
    )

    outcome = compute_outcome(reference_trace, candidate_trace)

    sys_analysis = build_system_specific_analysis(
        reference_trace, candidate_trace, alignment,
    )

    return PairedTraceComparisonResult(
        result_mode=ResultMode.COMPARISON_SUCCEEDED,
        identity=identity,
        validation=validation,
        alignment=alignment,
        metrics=metrics,
        outcome=outcome,
        system_specific_analysis=sys_analysis,
    )
