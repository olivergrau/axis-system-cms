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
from axis.framework.comparison.summary import compute_run_summary
from axis.framework.comparison.types import (
    GenericComparisonMetrics,
    PairedTraceComparisonResult,
    PairIdentity,
    PairingMode,
    ResultMode,
    RunComparisonResult,
)
from axis.framework.comparison.validation import validate_trace_pair
from axis.framework.persistence import ExperimentRepository, RunMetadata
from axis.framework.run import RunConfig
from axis.sdk.trace import BaseEpisodeTrace


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


def compare_runs(
    repo: ExperimentRepository,
    reference_experiment_id: str,
    reference_run_id: str,
    candidate_experiment_id: str,
    candidate_run_id: str,
) -> RunComparisonResult:
    """Compare all matched episodes across two runs.

    Episodes are paired by index (1, 2, ..., min(n_ref, n_cand)).
    """
    ref_config: RunConfig | None = None
    cand_config: RunConfig | None = None
    ref_meta: RunMetadata | None = None
    cand_meta: RunMetadata | None = None

    try:
        ref_config = repo.load_run_config(reference_experiment_id, reference_run_id)
    except Exception:
        pass
    try:
        cand_config = repo.load_run_config(candidate_experiment_id, candidate_run_id)
    except Exception:
        pass
    try:
        ref_meta = repo.load_run_metadata(reference_experiment_id, reference_run_id)
    except Exception:
        pass
    try:
        cand_meta = repo.load_run_metadata(candidate_experiment_id, candidate_run_id)
    except Exception:
        pass

    ref_episodes = repo.list_episode_files(reference_experiment_id, reference_run_id)
    cand_episodes = repo.list_episode_files(candidate_experiment_id, candidate_run_id)
    n_pairs = min(len(ref_episodes), len(cand_episodes))

    results: list[PairedTraceComparisonResult] = []
    ref_system_type = ""
    cand_system_type = ""

    for i in range(n_pairs):
        ep_idx = i + 1  # episodes are 1-based on disk
        ref_trace = repo.load_episode_trace(
            reference_experiment_id, reference_run_id, ep_idx,
        )
        cand_trace = repo.load_episode_trace(
            candidate_experiment_id, candidate_run_id, ep_idx,
        )
        if not ref_system_type:
            ref_system_type = ref_trace.system_type
            cand_system_type = cand_trace.system_type

        result = compare_episode_traces(
            ref_trace,
            cand_trace,
            reference_run_config=ref_config,
            candidate_run_config=cand_config,
            reference_run_metadata=ref_meta,
            candidate_run_metadata=cand_meta,
            reference_episode_index=ep_idx,
            candidate_episode_index=ep_idx,
        )
        results.append(result)

    summary = compute_run_summary(results)

    return RunComparisonResult(
        reference_experiment_id=reference_experiment_id,
        candidate_experiment_id=candidate_experiment_id,
        reference_run_id=reference_run_id,
        candidate_run_id=candidate_run_id,
        reference_system_type=ref_system_type,
        candidate_system_type=cand_system_type,
        episode_results=tuple(results),
        summary=summary,
    )
