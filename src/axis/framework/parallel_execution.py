"""Parallel execution helpers for AXIS framework workloads."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed
from pathlib import Path
from typing import Any

from axis.framework.execution_policy import TraceMode


def execute_episodes_parallel(
    config,
    *,
    trace_mode: TraceMode,
    max_workers: int,
    progress_callback: Callable[[int], None] | None = None,
    result_callback: Callable[[int, Any], None] | None = None,
    retain_results: bool = True,
) -> tuple[Any, ...]:
    """Execute episodes for *config* in worker processes."""
    from axis.framework.run import resolve_episode_seeds

    seeds = resolve_episode_seeds(config.num_episodes, config.base_seed)
    payloads = [
        (config.model_dump(mode="json"), seed, index, trace_mode.value)
        for index, seed in enumerate(seeds)
    ]
    results: list[tuple[int, Any]] = []
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_run_episode_worker, payload) for payload in payloads]
        for future in as_completed(futures):
            result = future.result()
            if result_callback is not None:
                result_callback(result[0], result[1])
            if retain_results:
                results.append(result)
            if progress_callback is not None:
                progress_callback(result[0])
    if not retain_results:
        return ()
    results.sort(key=lambda item: item[0])
    return tuple(result for _, result in results)


def execute_runs_parallel(
    run_configs,
    *,
    trace_mode: TraceMode,
    max_workers: int,
    progress_callback: Callable[[int], None] | None = None,
) -> tuple[Any, ...]:
    """Execute runs in worker processes with deterministic ordering."""
    payloads = [
        (index, run_config.model_dump(mode="json"), trace_mode.value)
        for index, run_config in enumerate(run_configs)
    ]
    results: list[tuple[int, Any]] = []
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_run_config_worker, payload) for payload in payloads]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            if progress_callback is not None:
                progress_callback(result[0])
    results.sort(key=lambda item: item[0])
    return tuple(result for _, result in results)


def execute_runs_parallel_persisted(
    run_configs,
    *,
    experiment_id: str,
    experiment_config,
    repository_root: str,
    trace_mode: TraceMode,
    max_workers: int,
    progress_callback: Callable[[int], None] | None = None,
) -> tuple[Any, ...]:
    """Execute and persist runs inside worker processes."""
    payloads = [
        (
            index,
            experiment_id,
            repository_root,
            experiment_config.model_dump(mode="json"),
            run_config.model_dump(mode="json"),
            trace_mode.value,
        )
        for index, run_config in enumerate(run_configs)
    ]
    results: list[tuple[int, Any]] = []
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = [
            pool.submit(_run_config_persisting_worker, payload)
            for payload in payloads
        ]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            if progress_callback is not None:
                progress_callback(result[0])
    results.sort(key=lambda item: item[0])
    return tuple(result for _, result in results)


def _run_episode_worker(payload: tuple[dict[str, Any], int, int, str]) -> tuple[int, Any]:
    """Worker entry point for one episode."""
    from axis.framework.execution_policy import TraceMode
    from axis.framework.run import RunConfig, _execute_episode_from_config
    from axis.plugins import discover_plugins

    config_data, episode_seed, episode_index, trace_mode_value = payload
    discover_plugins()
    config = RunConfig.model_validate(config_data)
    result = _execute_episode_from_config(
        config,
        episode_seed,
        episode_index=episode_index,
        trace_mode=TraceMode(trace_mode_value),
    )
    return episode_index, result


def _run_config_worker(payload: tuple[int, dict[str, Any], str]) -> tuple[int, Any]:
    """Worker entry point for one run."""
    from axis.framework.execution_policy import TraceMode
    from axis.framework.run import RunConfig, RunExecutor
    from axis.plugins import discover_plugins

    run_index, config_data, trace_mode_value = payload
    discover_plugins()
    config = RunConfig.model_validate(config_data)
    executor = RunExecutor()
    result = executor.execute(
        config,
        trace_mode_override=TraceMode(trace_mode_value),
    )
    return run_index, result


def _persist_episode_result_worker(
    repo,
    experiment_id: str,
    run_id: str,
    episode_index: int,
    episode_result: Any,
) -> None:
    from axis.framework.execution_results import LightEpisodeResult
    from axis.sdk.trace import FullEpisodeTrace

    episode_number = episode_index + 1
    if isinstance(episode_result, LightEpisodeResult):
        repo.save_light_episode_result(
            experiment_id, run_id, episode_number, episode_result, overwrite=True,
        )
        return
    if isinstance(episode_result, FullEpisodeTrace):
        repo.save_full_episode_trace(
            experiment_id, run_id, episode_number, episode_result, overwrite=True,
        )
        return
    raise TypeError(
        f"Unsupported episode result type for worker persistence: {type(episode_result)!r}"
    )


def _run_config_persisting_worker(
    payload: tuple[int, str, str, dict[str, Any], dict[str, Any], str],
) -> tuple[int, Any]:
    """Worker entry point for one persisted run."""
    from axis.framework.config import ExperimentConfig
    from axis.framework.execution_policy import TraceMode
    from axis.framework.experiment import _build_run_metadata
    from axis.framework.persistence import ExperimentRepository, RunStatus
    from axis.framework.run import RunConfig, RunExecutor
    from axis.plugins import discover_plugins

    (
        run_index,
        experiment_id,
        repository_root,
        experiment_config_data,
        run_config_data,
        trace_mode_value,
    ) = payload
    discover_plugins()

    repo = ExperimentRepository(Path(repository_root))
    experiment_config = ExperimentConfig.model_validate(experiment_config_data)
    run_config = RunConfig.model_validate(run_config_data)
    run_id = run_config.run_id or f"run-{run_index:04d}"

    repo.create_run_dir(experiment_id, run_id)
    repo.save_run_config(experiment_id, run_id, run_config, overwrite=True)
    repo.save_run_metadata(
        experiment_id,
        run_id,
        _build_run_metadata(
            experiment_id, run_id, run_config, experiment_config, run_index,
        ),
    )
    repo.save_run_status(experiment_id, run_id, RunStatus.RUNNING)

    executor = RunExecutor()
    try:
        result = executor.execute(
            run_config,
            trace_mode_override=TraceMode(trace_mode_value),
            on_episode_complete=lambda episode_index, episode_result: _persist_episode_result_worker(
                repo,
                experiment_id,
                run_id,
                episode_index,
                episode_result,
            ),
            retain_episode_payloads=False,
        )
        repo.save_run_result(experiment_id, run_id, result, overwrite=True)
        repo.save_run_summary(experiment_id, run_id, result.summary, overwrite=True)
        repo.save_run_status(experiment_id, run_id, RunStatus.COMPLETED)
        return run_index, result
    except Exception:
        repo.save_run_status(experiment_id, run_id, RunStatus.FAILED)
        raise
