"""Run executor: multi-episode execution and result aggregation."""

from __future__ import annotations

import uuid
from math import sqrt
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from axis.framework.config import FrameworkConfig
from axis.framework.execution_policy import (
    ExecutionPolicy,
    ParallelismMode,
    TraceMode,
)
from axis.framework.execution_results import (
    DeltaRunResult,
    EpisodeSummaryLike,
    LightEpisodeResult,
    LightRunResult,
)
from axis.framework.progress import NullProgressReporter
from axis.framework.registry import create_system
from axis.framework.runner import run_episode, setup_episode
from axis.sdk.position import Position
from axis.sdk.trace import BaseEpisodeTrace, DeltaEpisodeTrace


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


class RunConfig(BaseModel):
    """Configuration for a multi-episode run."""

    model_config = ConfigDict(frozen=True)

    system_type: str
    system_config: dict[str, Any]
    framework_config: FrameworkConfig
    num_episodes: int = Field(..., gt=0)
    base_seed: int | None = None
    agent_start_position: Position = Field(
        default_factory=lambda: Position(x=0, y=0)
    )
    run_id: str | None = None
    description: str | None = None


class RunSummary(BaseModel):
    """Aggregated statistics for a run. System-agnostic."""

    model_config = ConfigDict(frozen=True)

    num_episodes: int = Field(..., ge=0)
    mean_steps: float
    std_steps: float = Field(..., ge=0.0)
    mean_final_vitality: float
    std_final_vitality: float = Field(..., ge=0.0)
    death_rate: float = Field(..., ge=0.0, le=1.0)


class RunResult(BaseModel):
    """Complete result of a multi-episode run."""

    model_config = ConfigDict(frozen=True)

    result_type: str = "full_run"
    run_id: str
    num_episodes: int = Field(..., gt=0)
    episode_traces: tuple[BaseEpisodeTrace, ...]
    summary: RunSummary
    seeds: tuple[int, ...]
    config: RunConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def resolve_episode_seeds(
    num_episodes: int, base_seed: int | None
) -> tuple[int, ...]:
    """Derive deterministic episode seeds from a base seed."""
    if base_seed is not None:
        return tuple(base_seed + i for i in range(num_episodes))
    rng = np.random.default_rng()
    return tuple(int(rng.integers(0, 2**31)) for _ in range(num_episodes))


def compute_run_summary(
    episode_results: tuple[EpisodeSummaryLike, ...],
) -> RunSummary:
    """Compute run-level summary from episode traces."""
    n = len(episode_results)
    if n == 0:
        return RunSummary(
            num_episodes=0,
            mean_steps=0.0,
            std_steps=0.0,
            mean_final_vitality=0.0,
            std_final_vitality=0.0,
            death_rate=0.0,
        )

    steps = [t.total_steps for t in episode_results]
    vitalities = [t.final_vitality for t in episode_results]
    deaths = sum(1 for t in episode_results if t.final_vitality <= 0.0)

    mean_s = sum(steps) / n
    mean_v = sum(vitalities) / n

    std_s = sqrt(sum((x - mean_s) ** 2 for x in steps) / n)
    std_v = sqrt(sum((x - mean_v) ** 2 for x in vitalities) / n)

    return RunSummary(
        num_episodes=n,
        mean_steps=mean_s,
        std_steps=std_s,
        mean_final_vitality=mean_v,
        std_final_vitality=std_v,
        death_rate=deaths / n,
    )


# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------


class RunExecutor:
    """Execute multiple episodes under a shared configuration."""

    def __init__(
        self,
        system_catalog: Any | None = None,
        world_catalog: Any | None = None,
    ) -> None:
        self._system_catalog = system_catalog
        self._world_catalog = world_catalog

    def execute(
        self,
        config: RunConfig,
        *,
        trace_mode_override: TraceMode | None = None,
        progress: object | None = None,
        progress_description: str | None = None,
    ) -> RunResult | LightRunResult | DeltaRunResult:
        """Execute a complete run: N episodes, aggregate results."""
        from axis.framework.logging import EpisodeLogger

        run_id = config.run_id or str(uuid.uuid4())
        seeds = resolve_episode_seeds(config.num_episodes, config.base_seed)
        policy = _resolve_execution_policy(
            config.framework_config,
            trace_mode_override=trace_mode_override,
        )

        if (
            policy.parallelism_mode is not ParallelismMode.SEQUENTIAL
            and (self._system_catalog is not None or self._world_catalog is not None)
        ):
            # Catalog objects may not be process-safe; keep these paths deterministic.
            policy = policy.model_copy(update={"parallelism_mode": ParallelismMode.SEQUENTIAL})

        reporter = progress or NullProgressReporter()
        episode_task_id = reporter.add_task(
            progress_description or f"Run {run_id}: episodes",
            total=config.num_episodes,
        )

        if policy.parallelism_mode is ParallelismMode.EPISODES and policy.max_workers > 1:
            episode_results = self._execute_parallel_episodes(
                config, policy, reporter=reporter, task_id=episode_task_id,
            )
        else:
            episode_results = self._execute_sequential(
                config, seeds, policy, reporter=reporter, task_id=episode_task_id,
            )

        summary = compute_run_summary(episode_results)
        with EpisodeLogger(config.framework_config.logging, trace_mode=policy.trace_mode) as logger:
            for ep_idx, episode_result in enumerate(episode_results, start=1):
                logger.log_episode(episode_result, ep_idx)

        if policy.trace_mode is TraceMode.LIGHT:
            light_results = tuple(episode_results)
            return LightRunResult(
                run_id=run_id,
                num_episodes=config.num_episodes,
                episode_results=light_results,  # type: ignore[arg-type]
                summary=summary,
                seeds=seeds,
                config=config,
            )

        if policy.trace_mode is TraceMode.DELTA:
            delta_results = tuple(episode_results)
            return DeltaRunResult(
                run_id=run_id,
                num_episodes=config.num_episodes,
                episode_traces=delta_results,  # type: ignore[arg-type]
                summary=summary,
                seeds=seeds,
                config=config,
            )

        full_results = tuple(episode_results)
        return RunResult(
            run_id=run_id,
            num_episodes=config.num_episodes,
            episode_traces=full_results,  # type: ignore[arg-type]
            summary=summary,
            seeds=seeds,
            config=config,
        )

    def _execute_sequential(
        self,
        config: RunConfig,
        seeds: tuple[int, ...],
        policy: ExecutionPolicy,
        *,
        reporter: object,
        task_id: int,
    ) -> tuple[BaseEpisodeTrace | LightEpisodeResult, ...]:
        """Execute episodes sequentially under the given policy."""
        results: list[BaseEpisodeTrace | LightEpisodeResult | DeltaEpisodeTrace] = []
        for episode_index, episode_seed in enumerate(seeds):
            results.append(
                _execute_episode_from_config(
                    config,
                    episode_seed,
                    episode_index=episode_index,
                    trace_mode=policy.trace_mode,
                    system_catalog=self._system_catalog,
                    world_catalog=self._world_catalog,
                )
            )
            reporter.advance(task_id)
        return tuple(results)

    def _execute_parallel_episodes(
        self,
        config: RunConfig,
        policy: ExecutionPolicy,
        *,
        reporter: object,
        task_id: int,
    ) -> tuple[BaseEpisodeTrace | LightEpisodeResult | DeltaEpisodeTrace, ...]:
        """Execute episodes in parallel worker processes."""
        from axis.framework.parallel_execution import execute_episodes_parallel

        return execute_episodes_parallel(
            config,
            trace_mode=policy.trace_mode,
            max_workers=policy.max_workers,
            progress_callback=lambda _index: reporter.advance(task_id),
        )


def _resolve_execution_policy(
    framework_config: FrameworkConfig,
    *,
    trace_mode_override: TraceMode | None = None,
) -> ExecutionPolicy:
    """Normalize execution policy from framework config."""
    trace_mode = trace_mode_override or TraceMode(
        framework_config.execution.trace_mode,
    )
    return ExecutionPolicy(
        trace_mode=trace_mode,
        parallelism_mode=ParallelismMode(
            framework_config.execution.parallelism_mode,
        ),
        max_workers=framework_config.execution.max_workers,
    )


def _execute_episode_from_config(
    config: RunConfig,
    episode_seed: int,
    *,
    episode_index: int,
    trace_mode: TraceMode,
    system_catalog: Any | None = None,
    world_catalog: Any | None = None,
) -> BaseEpisodeTrace | LightEpisodeResult | DeltaEpisodeTrace:
    """Run one episode from config and return either full or light output."""
    system = create_system(
        config.system_type,
        config.system_config,
        system_catalog=system_catalog,
    )
    world_config = config.framework_config.world
    world, registry = setup_episode(
        system,
        world_config,
        config.agent_start_position,
        seed=episode_seed,
        world_catalog=world_catalog,
    )
    return run_episode(
        system,
        world,
        registry,
        max_steps=config.framework_config.execution.max_steps,
        seed=episode_seed,
        episode_index=episode_index,
        trace_mode=trace_mode,
        world_config=world_config,
    )
