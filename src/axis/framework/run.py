"""Run executor: multi-episode execution and result aggregation."""

from __future__ import annotations

import uuid
from math import sqrt
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from axis.framework.config import FrameworkConfig
from axis.framework.registry import create_system
from axis.framework.runner import run_episode, setup_episode
from axis.sdk.position import Position
from axis.sdk.trace import BaseEpisodeTrace


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
    episode_traces: tuple[BaseEpisodeTrace, ...],
) -> RunSummary:
    """Compute run-level summary from episode traces."""
    n = len(episode_traces)
    if n == 0:
        return RunSummary(
            num_episodes=0,
            mean_steps=0.0,
            std_steps=0.0,
            mean_final_vitality=0.0,
            std_final_vitality=0.0,
            death_rate=0.0,
        )

    steps = [t.total_steps for t in episode_traces]
    vitalities = [t.final_vitality for t in episode_traces]
    deaths = sum(1 for t in episode_traces if t.final_vitality <= 0.0)

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

    def execute(self, config: RunConfig) -> RunResult:
        """Execute a complete run: N episodes, aggregate results."""
        from axis.framework.logging import EpisodeLogger

        run_id = config.run_id or str(uuid.uuid4())
        seeds = resolve_episode_seeds(config.num_episodes, config.base_seed)
        system = create_system(config.system_type, config.system_config)

        traces: list[BaseEpisodeTrace] = []
        with EpisodeLogger(config.framework_config.logging) as logger:
            for ep_idx, episode_seed in enumerate(seeds, start=1):
                trace = self._run_single_episode(system, config, episode_seed)
                logger.log_episode(trace, ep_idx)
                traces.append(trace)

        episode_traces = tuple(traces)
        summary = compute_run_summary(episode_traces)

        return RunResult(
            run_id=run_id,
            num_episodes=config.num_episodes,
            episode_traces=episode_traces,
            summary=summary,
            seeds=seeds,
            config=config,
        )

    def _run_single_episode(
        self,
        system: Any,
        config: RunConfig,
        episode_seed: int,
    ) -> BaseEpisodeTrace:
        """Run one episode and return its trace."""
        world_config = config.framework_config.world

        world, registry = setup_episode(
            system,
            world_config,
            config.agent_start_position,
            seed=episode_seed,
        )

        return run_episode(
            system,
            world,
            registry,
            max_steps=config.framework_config.execution.max_steps,
            seed=episode_seed,
            world_config=world_config,
        )
