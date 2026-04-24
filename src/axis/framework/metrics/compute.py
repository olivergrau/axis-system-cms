"""Top-level orchestration for run-level behavioral metrics."""

from __future__ import annotations

from axis.framework.metrics.loader import load_run_episode_traces
from axis.framework.metrics.types import RunBehaviorMetrics
from axis.framework.metrics.extensions import build_system_behavior_metrics
from axis.framework.metrics.standard import (
    aggregate_run_behavior_metrics,
    compute_episode_behavior_metrics,
)


def compute_run_behavior_metrics(
    repo,
    experiment_id: str,
    run_id: str,
    *,
    extension_catalog=None,
) -> RunBehaviorMetrics:
    """Compute and persist standard behavioral metrics for one run."""
    run_meta = repo.load_run_metadata(experiment_id, run_id)
    trace_mode = run_meta.trace_mode or "full"
    if trace_mode == "light":
        raise ValueError(
            f"Run '{run_id}' in experiment '{experiment_id}' was executed in "
            "light trace mode. Behavioral metrics require replay-capable traces."
        )

    traces = load_run_episode_traces(repo, experiment_id, run_id)
    system_type = traces[0].system_type if traces else repo.load_experiment_metadata(
        experiment_id,
    ).system_type
    episode_metrics = tuple(
        compute_episode_behavior_metrics(trace)
        for trace in traces
    )
    standard_metrics = aggregate_run_behavior_metrics(episode_metrics)
    system_specific_metrics = build_system_behavior_metrics(
        system_type,
        traces,
        standard_metrics,
        extension_catalog=extension_catalog,
    ) or {}
    result = RunBehaviorMetrics(
        experiment_id=experiment_id,
        run_id=run_id,
        system_type=system_type,
        trace_mode=trace_mode,
        num_episodes=len(traces),
        standard_metrics=standard_metrics,
        system_specific_metrics=system_specific_metrics,
    )
    repo.save_behavior_metrics(
        experiment_id,
        run_id,
        result,
        overwrite=True,
    )
    return result


def load_or_compute_run_behavior_metrics(
    repo,
    experiment_id: str,
    run_id: str,
    *,
    extension_catalog=None,
) -> RunBehaviorMetrics:
    """Return persisted behavioral metrics or compute them lazily."""
    try:
        loaded = repo.load_behavior_metrics(experiment_id, run_id)
        if loaded.system_specific_metrics:
            return loaded
        refreshed = build_system_behavior_metrics(
            loaded.system_type,
            load_run_episode_traces(repo, experiment_id, run_id),
            loaded.standard_metrics,
            extension_catalog=extension_catalog,
        )
        if not refreshed:
            return loaded
        updated = loaded.model_copy(update={"system_specific_metrics": refreshed})
        repo.save_behavior_metrics(experiment_id, run_id, updated, overwrite=True)
        return updated
    except FileNotFoundError:
        return compute_run_behavior_metrics(
            repo,
            experiment_id,
            run_id,
            extension_catalog=extension_catalog,
        )
