"""Top-level trace comparison entry point (WP-07)."""

from __future__ import annotations

import os
import pickle
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from axis.framework.comparison.alignment import compute_alignment
from axis.framework.comparison.extensions import build_system_specific_analysis
from axis.framework.comparison.metrics import (
    compute_generic_comparison_metrics,
)
from axis.framework.comparison.outcome import compute_outcome
from axis.framework.comparison.summary import compute_run_summary
from axis.framework.comparison.types import (
    PairedTraceComparisonResult,
    PairIdentity,
    PairingMode,
    ResultMode,
    RunComparisonResult,
)
from axis.framework.comparison.validation import validate_trace_pair
from axis.framework.persistence import ExperimentRepository, RunMetadata
from axis.framework.progress import NullProgressReporter
from axis.framework.run import RunConfig
from axis.sdk.trace import BaseEpisodeTrace


@dataclass(frozen=True)
class _EpisodeComparisonContext:
    repo_root: Path
    reference_experiment_id: str
    reference_run_id: str
    candidate_experiment_id: str
    candidate_run_id: str
    reference_run_config: RunConfig | None = None
    candidate_run_config: RunConfig | None = None
    reference_run_metadata: RunMetadata | None = None
    candidate_run_metadata: RunMetadata | None = None
    extension_catalog: object | None = None


@dataclass(frozen=True)
class _EpisodeComparisonJob:
    episode_index: int


def _load_and_compare_episode_pair(
    repo: ExperimentRepository,
    reference_experiment_id: str,
    reference_run_id: str,
    candidate_experiment_id: str,
    candidate_run_id: str,
    episode_index: int,
    *,
    reference_run_config: RunConfig | None = None,
    candidate_run_config: RunConfig | None = None,
    reference_run_metadata: RunMetadata | None = None,
    candidate_run_metadata: RunMetadata | None = None,
    extension_catalog: object | None = None,
) -> tuple[str, str, PairedTraceComparisonResult]:
    """Compatibility wrapper around the structured episode comparison worker."""
    return _execute_episode_comparison_job(
        _EpisodeComparisonContext(
            repo_root=repo.root,
            reference_experiment_id=reference_experiment_id,
            reference_run_id=reference_run_id,
            candidate_experiment_id=candidate_experiment_id,
            candidate_run_id=candidate_run_id,
            reference_run_config=reference_run_config,
            candidate_run_config=candidate_run_config,
            reference_run_metadata=reference_run_metadata,
            candidate_run_metadata=candidate_run_metadata,
            extension_catalog=extension_catalog,
        ),
        _EpisodeComparisonJob(episode_index=episode_index),
    )


def _execute_episode_comparison_job(
    context: _EpisodeComparisonContext,
    job: _EpisodeComparisonJob,
) -> tuple[str, str, PairedTraceComparisonResult]:
    """Load one episode pair from repository storage and compare it."""
    from axis.plugins import discover_plugins

    discover_plugins()
    repo = ExperimentRepository(context.repo_root)
    episode_index = job.episode_index
    ref_trace = repo.load_episode_trace(
        context.reference_experiment_id,
        context.reference_run_id,
        episode_index,
    )
    cand_trace = repo.load_episode_trace(
        context.candidate_experiment_id,
        context.candidate_run_id,
        episode_index,
    )
    result = compare_episode_traces(
        ref_trace,
        cand_trace,
        reference_run_config=context.reference_run_config,
        candidate_run_config=context.candidate_run_config,
        reference_run_metadata=context.reference_run_metadata,
        candidate_run_metadata=context.candidate_run_metadata,
        reference_episode_index=episode_index,
        candidate_episode_index=episode_index,
        extension_catalog=context.extension_catalog,
    )
    return ref_trace.system_type, cand_trace.system_type, result


def _load_optional_run_context(
    repo: ExperimentRepository,
    reference_experiment_id: str,
    reference_run_id: str,
    candidate_experiment_id: str,
    candidate_run_id: str,
) -> tuple[RunConfig | None, RunConfig | None, RunMetadata | None, RunMetadata | None]:
    """Load run configs and metadata opportunistically for comparison context."""
    reference_run_config: RunConfig | None = None
    candidate_run_config: RunConfig | None = None
    reference_run_metadata: RunMetadata | None = None
    candidate_run_metadata: RunMetadata | None = None
    try:
        reference_run_config = repo.load_run_config(reference_experiment_id, reference_run_id)
    except Exception:
        pass
    try:
        candidate_run_config = repo.load_run_config(candidate_experiment_id, candidate_run_id)
    except Exception:
        pass
    try:
        reference_run_metadata = repo.load_run_metadata(reference_experiment_id, reference_run_id)
    except Exception:
        pass
    try:
        candidate_run_metadata = repo.load_run_metadata(candidate_experiment_id, candidate_run_id)
    except Exception:
        pass

    return (
        reference_run_config,
        candidate_run_config,
        reference_run_metadata,
        candidate_run_metadata,
    )


def _can_use_process_pool(
    repo: object,
    context: _EpisodeComparisonContext | None,
) -> bool:
    """Return True when the comparison context is safe to ship to worker processes."""
    if not isinstance(repo, ExperimentRepository) or context is None:
        return False
    try:
        pickle.dumps(context)
    except Exception:
        return False
    return True


def _resolve_comparison_max_workers(
    n_pairs: int,
    *,
    reference_run_config: RunConfig | None,
    candidate_run_config: RunConfig | None,
    requested_max_workers: int | None = None,
) -> int:
    """Resolve comparison worker budget conservatively.

    Preference order:
    1. Explicit comparison override, when provided.
    2. The minimum configured execution.max_workers across the two runs.
    3. The single available execution.max_workers if only one config is present.
    4. Host CPU count as final fallback.

    The result is always clamped to ``[1, n_pairs]``.
    """
    if n_pairs <= 0:
        return 1

    if requested_max_workers is not None:
        return min(n_pairs, max(1, requested_max_workers))

    configured_limits: list[int] = []
    for run_config in (reference_run_config, candidate_run_config):
        if run_config is None:
            continue
        framework_config = getattr(run_config, "framework_config", None)
        execution = getattr(framework_config, "execution", None)
        max_workers = getattr(execution, "max_workers", None)
        if isinstance(max_workers, int) and max_workers >= 1:
            configured_limits.append(max_workers)

    if configured_limits:
        return min(n_pairs, min(configured_limits))

    return min(n_pairs, max(1, os.cpu_count() or 1))


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
    extension_catalog: object | None = None,
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

    metrics = compute_generic_comparison_metrics(
        reference_trace,
        candidate_trace,
        validation.shared_action_labels,
    )

    outcome = compute_outcome(reference_trace, candidate_trace)

    sys_analysis = build_system_specific_analysis(
        reference_trace, candidate_trace, alignment,
        extension_catalog=extension_catalog,
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
    *,
    extension_catalog: object | None = None,
    progress: object | None = None,
    progress_description: str | None = None,
    max_workers: int | None = None,
) -> RunComparisonResult:
    """Compare all matched episodes across two runs.

    Episodes are paired by index (1, 2, ..., min(n_ref, n_cand)).
    """
    ref_config, cand_config, ref_meta, cand_meta = _load_optional_run_context(
        repo,
        reference_experiment_id,
        reference_run_id,
        candidate_experiment_id,
        candidate_run_id,
    )

    ref_episodes = repo.list_episode_files(reference_experiment_id, reference_run_id)
    cand_episodes = repo.list_episode_files(candidate_experiment_id, candidate_run_id)
    n_pairs = min(len(ref_episodes), len(cand_episodes))
    reporter = progress or NullProgressReporter()
    task_id = reporter.add_task(
        progress_description or "Episode comparisons",
        total=n_pairs,
    )

    results: list[PairedTraceComparisonResult] = []
    ref_system_type = ""
    cand_system_type = ""
    context = None
    if isinstance(repo, ExperimentRepository):
        context = _EpisodeComparisonContext(
            repo_root=repo.root,
            reference_experiment_id=reference_experiment_id,
            reference_run_id=reference_run_id,
            candidate_experiment_id=candidate_experiment_id,
            candidate_run_id=candidate_run_id,
            reference_run_config=ref_config,
            candidate_run_config=cand_config,
            reference_run_metadata=ref_meta,
            candidate_run_metadata=cand_meta,
            extension_catalog=extension_catalog,
        )

    can_parallelize = n_pairs > 1
    resolved_max_workers = _resolve_comparison_max_workers(
        n_pairs,
        reference_run_config=ref_config,
        candidate_run_config=cand_config,
        requested_max_workers=max_workers,
    )
    can_use_process_pool = (
        can_parallelize
        and resolved_max_workers > 1
        and _can_use_process_pool(repo, context)
    )

    if can_use_process_pool:
        indexed_results: list[PairedTraceComparisonResult | None] = [None] * n_pairs
        with ProcessPoolExecutor(max_workers=resolved_max_workers) as executor:
            future_to_index = {
                executor.submit(
                    _execute_episode_comparison_job,
                    context,
                    _EpisodeComparisonJob(episode_index=episode_index),
                ): episode_index - 1
                for episode_index in range(1, n_pairs + 1)
            }
            for future in as_completed(future_to_index):
                result_index = future_to_index[future]
                episode_ref_system_type, episode_cand_system_type, result = future.result()
                if not ref_system_type:
                    ref_system_type = episode_ref_system_type
                    cand_system_type = episode_cand_system_type
                indexed_results[result_index] = result
                reporter.advance(task_id)
        results = [result for result in indexed_results if result is not None]
    elif can_parallelize and resolved_max_workers > 1:
        indexed_results: list[PairedTraceComparisonResult | None] = [None] * n_pairs
        with ThreadPoolExecutor(max_workers=resolved_max_workers) as executor:
            future_to_index = {
                executor.submit(
                    _load_and_compare_episode_pair,
                    repo,
                    reference_experiment_id,
                    reference_run_id,
                    candidate_experiment_id,
                    candidate_run_id,
                    episode_index,
                    reference_run_config=ref_config,
                    candidate_run_config=cand_config,
                    reference_run_metadata=ref_meta,
                    candidate_run_metadata=cand_meta,
                    extension_catalog=extension_catalog,
                ): episode_index - 1
                for episode_index in range(1, n_pairs + 1)
            }
            for future in as_completed(future_to_index):
                result_index = future_to_index[future]
                episode_ref_system_type, episode_cand_system_type, result = future.result()
                if not ref_system_type:
                    ref_system_type = episode_ref_system_type
                    cand_system_type = episode_cand_system_type
                indexed_results[result_index] = result
                reporter.advance(task_id)
        results = [result for result in indexed_results if result is not None]
    else:
        for i in range(n_pairs):
            ep_idx = i + 1  # episodes are 1-based on disk
            episode_ref_system_type, episode_cand_system_type, result = _load_and_compare_episode_pair(
                repo,
                reference_experiment_id,
                reference_run_id,
                candidate_experiment_id,
                candidate_run_id,
                ep_idx,
                reference_run_config=ref_config,
                candidate_run_config=cand_config,
                reference_run_metadata=ref_meta,
                candidate_run_metadata=cand_meta,
                extension_catalog=extension_catalog,
            )
            if not ref_system_type:
                ref_system_type = episode_ref_system_type
                cand_system_type = episode_cand_system_type
            results.append(result)
            reporter.advance(task_id)

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
