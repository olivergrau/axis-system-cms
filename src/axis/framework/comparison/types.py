"""Frozen Pydantic result models for paired trace comparison (WP-01)."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

# ---------------------------------------------------------------------------
# Tolerance constants
# ---------------------------------------------------------------------------

EQUALITY_EPSILON: float = 1e-9
RANKING_EPSILON: float = 1e-6

# ---------------------------------------------------------------------------
# Enums / Literals
# ---------------------------------------------------------------------------


class ResultMode(str, Enum):
    COMPARISON_SUCCEEDED = "comparison_succeeded"
    COMPARISON_FAILED_VALIDATION = "comparison_failed_validation"


class PairingMode(str, Enum):
    EXPLICIT_SEED = "explicit_seed"
    DERIVED_SEED = "derived_seed"


class AmbiguityState(str, Enum):
    NOT_APPLICABLE = "not_applicable"
    AMBIGUOUS_DUE_TO_TIE = "ambiguous_due_to_tie"
    MISSING_REQUIRED_SIGNAL = "missing_required_signal"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

_FROZEN = ConfigDict(frozen=True)


class PairIdentity(BaseModel):
    model_config = _FROZEN

    reference_system_type: str
    candidate_system_type: str
    reference_run_id: str | None = None
    candidate_run_id: str | None = None
    reference_episode_index: int | None = None
    candidate_episode_index: int | None = None
    episode_seed: int | None = None
    pairing_mode: PairingMode | None = None


class PairValidationResult(BaseModel):
    model_config = _FROZEN

    is_valid_pair: bool
    errors: tuple[str, ...] = ()
    world_type_match: bool = False
    world_config_match: bool = False
    start_position_match: bool = False
    episode_seed_match: bool | None = None
    shared_action_labels: tuple[str, ...] = ()


class AlignmentSummary(BaseModel):
    model_config = _FROZEN

    reference_total_steps: int
    candidate_total_steps: int
    aligned_steps: int
    reference_extra_steps: int = 0
    candidate_extra_steps: int = 0


class ActionDivergence(BaseModel):
    model_config = _FROZEN

    first_action_divergence_step: int | None = None
    action_mismatch_count: int = 0
    action_mismatch_rate: float = 0.0


class PositionDivergence(BaseModel):
    model_config = _FROZEN

    distance_series: tuple[int, ...] = ()
    mean_trajectory_distance: float = 0.0
    max_trajectory_distance: int = 0


class VitalityDivergence(BaseModel):
    model_config = _FROZEN

    difference_series: tuple[float, ...] = ()
    mean_absolute_difference: float = 0.0
    max_absolute_difference: float = 0.0


class ActionUsageEntry(BaseModel):
    model_config = _FROZEN

    action: str
    reference_count: int = 0
    candidate_count: int = 0
    delta: int = 0


class ActionUsageComparison(BaseModel):
    model_config = _FROZEN

    reference_most_used: str | None = None
    reference_most_used_ambiguity: AmbiguityState | None = None
    candidate_most_used: str | None = None
    candidate_most_used_ambiguity: AmbiguityState | None = None
    shared_action_usage: tuple[ActionUsageEntry, ...] = ()
    reference_only_actions: tuple[str, ...] = ()
    candidate_only_actions: tuple[str, ...] = ()


class GenericComparisonMetrics(BaseModel):
    model_config = _FROZEN

    action_divergence: ActionDivergence
    position_divergence: PositionDivergence
    vitality_divergence: VitalityDivergence
    action_usage: ActionUsageComparison


class OutcomeComparison(BaseModel):
    model_config = _FROZEN

    reference_termination_reason: str
    candidate_termination_reason: str
    reference_final_vitality: float
    candidate_final_vitality: float
    final_vitality_delta: float = 0.0
    reference_total_steps: int
    candidate_total_steps: int
    total_steps_delta: int = 0
    longer_survivor: Literal["reference", "candidate", "equal"] = "equal"


# ---------------------------------------------------------------------------
# Top-level result
# ---------------------------------------------------------------------------


class PairedTraceComparisonResult(BaseModel):
    model_config = _FROZEN

    result_mode: ResultMode
    identity: PairIdentity
    validation: PairValidationResult
    alignment: AlignmentSummary | None = None
    metrics: GenericComparisonMetrics | None = None
    outcome: OutcomeComparison | None = None
    system_specific_analysis: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Run-level models
# ---------------------------------------------------------------------------


class MetricSummaryStats(BaseModel):
    """Descriptive statistics over N episode values."""

    model_config = _FROZEN

    mean: float = 0.0
    std: float = 0.0
    min: float = 0.0
    max: float = 0.0
    n: int = 0


class RunComparisonSummary(BaseModel):
    """Statistical summary across all paired episodes in a run."""

    model_config = _FROZEN

    num_episodes_compared: int = 0
    num_valid_pairs: int = 0
    num_invalid_pairs: int = 0

    action_mismatch_rate: MetricSummaryStats = MetricSummaryStats()
    mean_trajectory_distance: MetricSummaryStats = MetricSummaryStats()
    mean_vitality_difference: MetricSummaryStats = MetricSummaryStats()
    final_vitality_delta: MetricSummaryStats = MetricSummaryStats()
    total_steps_delta: MetricSummaryStats = MetricSummaryStats()

    reference_survival_rate: float = 0.0
    candidate_survival_rate: float = 0.0
    candidate_longer_count: int = 0
    reference_longer_count: int = 0
    equal_count: int = 0


class RunComparisonResult(BaseModel):
    """Full run-level comparison: per-episode results + summary."""

    model_config = _FROZEN

    reference_experiment_id: str | None = None
    candidate_experiment_id: str | None = None
    reference_run_id: str
    candidate_run_id: str
    reference_system_type: str
    candidate_system_type: str
    episode_results: tuple[PairedTraceComparisonResult, ...] = ()
    summary: RunComparisonSummary = RunComparisonSummary()
