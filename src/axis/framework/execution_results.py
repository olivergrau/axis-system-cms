"""Lightweight and delta execution result models."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from axis.sdk.position import Position
from axis.sdk.trace import DeltaEpisodeTrace


@runtime_checkable
class EpisodeSummaryLike(Protocol):
    """Protocol for episode outputs that can contribute to run summaries."""

    total_steps: int
    final_vitality: float
    termination_reason: str


class LightEpisodeResult(BaseModel):
    """Minimal per-episode result for summary-oriented execution."""

    model_config = ConfigDict(frozen=True)

    result_type: str = "light_episode"
    episode_index: int = Field(..., ge=0)
    episode_seed: int
    total_steps: int = Field(..., ge=0)
    final_vitality: float
    termination_reason: str
    final_position: Position


class LightRunResult(BaseModel):
    """Run-level result carrying lightweight episode outputs."""

    model_config = ConfigDict(frozen=True)

    result_type: str = "light_run"
    run_id: str
    num_episodes: int = Field(..., gt=0)
    episode_results: tuple[LightEpisodeResult, ...]
    summary: object
    seeds: tuple[int, ...]
    config: object


class DeltaRunResult(BaseModel):
    """Run-level result carrying delta episode traces."""

    model_config = ConfigDict(frozen=True)

    result_type: str = "delta_run"
    run_id: str
    num_episodes: int = Field(..., gt=0)
    episode_traces: tuple[DeltaEpisodeTrace, ...]
    summary: object
    seeds: tuple[int, ...]
    config: object
