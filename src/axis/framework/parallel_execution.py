"""Parallel execution helpers for AXIS framework workloads."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed
from typing import Any

from axis.framework.execution_policy import TraceMode


def execute_episodes_parallel(
    config,
    *,
    trace_mode: TraceMode,
    max_workers: int,
    progress_callback: Callable[[int], None] | None = None,
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
            results.append(result)
            if progress_callback is not None:
                progress_callback(result[0])
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
