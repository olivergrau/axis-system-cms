"""Run executor: multi-episode execution and result aggregation."""

from __future__ import annotations

import uuid
from collections.abc import Callable
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
    EpisodeSummaryLike,
    LightEpisodeResult,
    LightRunResult,
)
from axis.framework.progress import NullProgressReporter
from axis.framework.registry import create_system
from axis.framework.runner import run_episode, setup_episode
from axis.sdk.position import Position
from axis.sdk.trace import FullEpisodeTrace


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
    """Replay-capable full result of a multi-episode run."""

    model_config = ConfigDict(frozen=True)

    result_type: str = "full_run"
    run_id: str
    num_episodes: int = Field(..., gt=0)
    episode_traces: tuple[FullEpisodeTrace, ...]
    summary: RunSummary
    seeds: tuple[int, ...]
    config: RunConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


EpisodeResultLike = (
    FullEpisodeTrace
    | LightEpisodeResult
)
EpisodeCompletionCallback = Callable[[int, EpisodeResultLike], None]


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
    accumulator = RunSummaryAccumulator()
    for episode_result in episode_results:
        accumulator.add(episode_result)
    return accumulator.finalize()


class RunSummaryAccumulator:
    """Incrementally aggregate run-level statistics from episode summaries."""

    def __init__(self) -> None:
        self._count = 0
        self._sum_steps = 0.0
        self._sum_steps_sq = 0.0
        self._sum_vitality = 0.0
        self._sum_vitality_sq = 0.0
        self._deaths = 0

    def add(self, episode_result: EpisodeSummaryLike) -> None:
        steps = float(episode_result.total_steps)
        vitality = float(episode_result.final_vitality)
        self._count += 1
        self._sum_steps += steps
        self._sum_steps_sq += steps * steps
        self._sum_vitality += vitality
        self._sum_vitality_sq += vitality * vitality
        if vitality <= 0.0:
            self._deaths += 1

    def finalize(self) -> RunSummary:
        if self._count == 0:
            return RunSummary(
                num_episodes=0,
                mean_steps=0.0,
                std_steps=0.0,
                mean_final_vitality=0.0,
                std_final_vitality=0.0,
                death_rate=0.0,
            )

        mean_steps = self._sum_steps / self._count
        mean_vitality = self._sum_vitality / self._count
        step_variance = max(
            0.0,
            (self._sum_steps_sq / self._count) - (mean_steps * mean_steps),
        )
        vitality_variance = max(
            0.0,
            (self._sum_vitality_sq / self._count) - (mean_vitality * mean_vitality),
        )

        return RunSummary(
            num_episodes=self._count,
            mean_steps=mean_steps,
            std_steps=sqrt(step_variance),
            mean_final_vitality=mean_vitality,
            std_final_vitality=sqrt(vitality_variance),
            death_rate=self._deaths / self._count,
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
        on_episode_complete: EpisodeCompletionCallback | None = None,
        retain_episode_payloads: bool = True,
    ) -> RunResult | LightRunResult:
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

        summary_accumulator = RunSummaryAccumulator()

        with EpisodeLogger(
            config.framework_config.logging, trace_mode=policy.trace_mode,
        ) as logger:
            def _handle_episode_completion(
                episode_index: int,
                episode_result: EpisodeResultLike,
            ) -> None:
                summary_accumulator.add(episode_result)
                logger.log_episode(episode_result, episode_index + 1)
                if on_episode_complete is not None:
                    on_episode_complete(episode_index, episode_result)

            if policy.parallelism_mode is ParallelismMode.EPISODES and policy.max_workers > 1:
                episode_results = self._execute_parallel_episodes(
                    config,
                    policy,
                    reporter=reporter,
                    task_id=episode_task_id,
                    on_episode_complete=_handle_episode_completion,
                    retain_episode_payloads=retain_episode_payloads,
                )
            else:
                episode_results = self._execute_sequential(
                    config,
                    seeds,
                    policy,
                    reporter=reporter,
                    task_id=episode_task_id,
                    on_episode_complete=_handle_episode_completion,
                    retain_episode_payloads=retain_episode_payloads,
                )

        summary = summary_accumulator.finalize()

        if policy.trace_mode is TraceMode.LIGHT:
            return LightRunResult(
                run_id=run_id,
                num_episodes=config.num_episodes,
                episode_results=episode_results,  # type: ignore[arg-type]
                summary=summary,
                seeds=seeds,
                config=config,
            )

        return RunResult(
            run_id=run_id,
            num_episodes=config.num_episodes,
            episode_traces=episode_results,  # type: ignore[arg-type]
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
        on_episode_complete: EpisodeCompletionCallback | None = None,
        retain_episode_payloads: bool = True,
    ) -> tuple[
        FullEpisodeTrace | LightEpisodeResult,
        ...
    ]:
        """Execute episodes sequentially under the given policy."""
        results: list[EpisodeResultLike] = []
        for episode_index, episode_seed in enumerate(seeds):
            episode_result = _execute_episode_from_config(
                config,
                episode_seed,
                episode_index=episode_index,
                trace_mode=policy.trace_mode,
                system_catalog=self._system_catalog,
                world_catalog=self._world_catalog,
            )
            if on_episode_complete is not None:
                on_episode_complete(episode_index, episode_result)
            if retain_episode_payloads:
                results.append(episode_result)
            reporter.advance(task_id)
        return tuple(results)

    def _execute_parallel_episodes(
        self,
        config: RunConfig,
        policy: ExecutionPolicy,
        *,
        reporter: object,
        task_id: int,
        on_episode_complete: EpisodeCompletionCallback | None = None,
        retain_episode_payloads: bool = True,
    ) -> tuple[
        FullEpisodeTrace | LightEpisodeResult,
        ...
    ]:
        """Execute episodes in parallel worker processes."""
        from axis.framework.parallel_execution import execute_episodes_parallel

        return execute_episodes_parallel(
            config,
            trace_mode=policy.trace_mode,
            max_workers=policy.max_workers,
            progress_callback=lambda _index: reporter.advance(task_id),
            result_callback=on_episode_complete,
            retain_results=retain_episode_payloads,
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
) -> FullEpisodeTrace | LightEpisodeResult:
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
