"""Run-level orchestration for AXIS System A.

Introduces the Run abstraction — executing multiple episodes under a shared
configuration for statistical evaluation. This is the minimal unit for
comparing configurations.
"""

from __future__ import annotations

import uuid

import math

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from axis_system_a.config import SimulationConfig
from axis_system_a.enums import TerminationReason
from axis_system_a.results import EpisodeResult
from axis_system_a.runner import run_episode
from axis_system_a.types import Position
from axis_system_a.world import create_world


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class RunConfig(BaseModel):
    """Configuration for a multi-episode run."""

    model_config = ConfigDict(frozen=True)

    simulation: SimulationConfig
    num_episodes: int = Field(..., gt=0)
    base_seed: int | None = None
    agent_start_position: Position = Field(
        default_factory=lambda: Position(x=0, y=0),
    )
    run_id: str | None = None
    description: str | None = None


# ---------------------------------------------------------------------------
# Runtime context
# ---------------------------------------------------------------------------


class RunContext(BaseModel):
    """Resolved runtime context for a run. Internal to RunExecutor."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    run_config: RunConfig
    episode_seeds: tuple[int, ...]


# ---------------------------------------------------------------------------
# Seed resolution
# ---------------------------------------------------------------------------


def resolve_episode_seeds(
    num_episodes: int, base_seed: int | None,
) -> tuple[int, ...]:
    """Derive deterministic episode seeds from a base seed, or generate random ones.

    If *base_seed* is provided, seeds are ``base_seed + i`` for each episode i.
    If *base_seed* is ``None``, seeds are drawn from system entropy but still
    captured for after-the-fact reproducibility.
    """
    if base_seed is not None:
        return tuple(base_seed + i for i in range(num_episodes))
    rng = np.random.default_rng()
    return tuple(int(rng.integers(0, 2**31)) for _ in range(num_episodes))


# ---------------------------------------------------------------------------
# Summary and result
# ---------------------------------------------------------------------------


class RunSummary(BaseModel):
    """Aggregated statistics for a run."""

    model_config = ConfigDict(frozen=True)

    num_episodes: int = Field(..., ge=0)
    mean_steps: float
    std_steps: float = Field(..., ge=0.0)
    mean_final_energy: float
    std_final_energy: float = Field(..., ge=0.0)
    death_rate: float = Field(..., ge=0.0, le=1.0)
    mean_consumption_count: float
    std_consumption_count: float = Field(..., ge=0.0)


class RunResult(BaseModel):
    """Complete result of a multi-episode run."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    num_episodes: int = Field(..., gt=0)
    episode_results: tuple[EpisodeResult, ...]
    summary: RunSummary
    seeds: tuple[int, ...]
    config: RunConfig


def compute_run_summary(
    episode_results: tuple[EpisodeResult, ...],
) -> RunSummary:
    """Compute run-level summary from episode results.

    Uses population standard deviation (all episodes are present, not a sample).
    """
    n = len(episode_results)
    if n == 0:
        return RunSummary(
            num_episodes=0, mean_steps=0.0, std_steps=0.0,
            mean_final_energy=0.0, std_final_energy=0.0,
            death_rate=0.0, mean_consumption_count=0.0,
            std_consumption_count=0.0,
        )

    steps = [er.total_steps for er in episode_results]
    energies = [er.final_agent_state.energy for er in episode_results]
    consumes = [er.summary.total_consume_events for er in episode_results]
    deaths = sum(
        1
        for er in episode_results
        if er.termination_reason == TerminationReason.ENERGY_DEPLETED
    )

    mean_s = sum(steps) / n
    mean_e = sum(energies) / n
    mean_c = sum(consumes) / n

    std_s = math.sqrt(sum((x - mean_s) ** 2 for x in steps) / n)
    std_e = math.sqrt(sum((x - mean_e) ** 2 for x in energies) / n)
    std_c = math.sqrt(sum((x - mean_c) ** 2 for x in consumes) / n)

    return RunSummary(
        num_episodes=n,
        mean_steps=mean_s,
        std_steps=std_s,
        mean_final_energy=mean_e,
        std_final_energy=std_e,
        death_rate=deaths / n,
        mean_consumption_count=mean_c,
        std_consumption_count=std_c,
    )


# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------


class RunExecutor:
    """Orchestrates execution of multiple episodes under a shared configuration."""

    def execute(self, config: RunConfig) -> RunResult:
        """Execute a complete run: N episodes, aggregate results."""
        run_id = config.run_id or uuid.uuid4().hex
        seeds = resolve_episode_seeds(config.num_episodes, config.base_seed)

        episode_results: list[EpisodeResult] = []
        for seed in seeds:
            episode_config = self._make_episode_config(config.simulation, seed)
            world = create_world(
                config.simulation.world, config.agent_start_position,
            )
            result = run_episode(episode_config, world)
            episode_results.append(result)

        results_tuple = tuple(episode_results)
        summary = compute_run_summary(results_tuple)

        return RunResult(
            run_id=run_id,
            num_episodes=config.num_episodes,
            episode_results=results_tuple,
            summary=summary,
            seeds=seeds,
            config=config,
        )

    @staticmethod
    def _make_episode_config(
        simulation: SimulationConfig, seed: int,
    ) -> SimulationConfig:
        """Create a per-episode SimulationConfig with the episode seed."""
        new_general = simulation.general.model_copy(update={"seed": seed})
        return simulation.model_copy(
            update={"general": new_general},
        )


def execute_run(config: RunConfig) -> RunResult:
    """Execute a run using the default RunExecutor. Convenience wrapper."""
    return RunExecutor().execute(config)
