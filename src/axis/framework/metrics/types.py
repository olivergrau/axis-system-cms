"""Typed models for run-level behavioral metrics."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MetricSummaryStats(BaseModel):
    """Aggregate statistics for one scalar metric across episodes."""

    model_config = ConfigDict(frozen=True)

    mean: float = 0.0
    std: float = Field(0.0, ge=0.0)
    min: float = 0.0
    max: float = 0.0
    n: int = Field(0, ge=0)


class EpisodeBehaviorMetrics(BaseModel):
    """Internal per-episode standard behavioral metrics."""

    model_config = ConfigDict(frozen=True)

    total_steps: int = Field(..., ge=0)
    final_vitality: float
    died: bool
    resource_gain_per_step: float
    net_energy_efficiency: float
    successful_consume_rate: float
    consume_on_empty_rate: float
    failed_movement_rate: float
    action_entropy: float
    policy_sharpness: float
    action_inertia: float
    unique_cells_visited: float
    coverage_efficiency: float
    revisit_rate: float


class StandardBehaviorMetrics(BaseModel):
    """Framework-standard run-level behavioral metrics."""

    model_config = ConfigDict(frozen=True)

    mean_steps: float
    death_rate: float = Field(..., ge=0.0, le=1.0)
    mean_final_vitality: float
    resource_gain_per_step: MetricSummaryStats
    net_energy_efficiency: MetricSummaryStats
    successful_consume_rate: MetricSummaryStats
    consume_on_empty_rate: MetricSummaryStats
    failed_movement_rate: MetricSummaryStats
    action_entropy: MetricSummaryStats
    policy_sharpness: MetricSummaryStats
    action_inertia: MetricSummaryStats
    unique_cells_visited: MetricSummaryStats
    coverage_efficiency: MetricSummaryStats
    revisit_rate: MetricSummaryStats


class RunBehaviorMetrics(BaseModel):
    """Persisted run-level behavioral metrics artifact."""

    model_config = ConfigDict(frozen=True)

    artifact_type: str = "behavior_metrics"
    experiment_id: str
    run_id: str
    system_type: str
    trace_mode: str
    num_episodes: int = Field(..., ge=0)
    standard_metrics: StandardBehaviorMetrics
    system_specific_metrics: dict[str, Any] = Field(default_factory=dict)
