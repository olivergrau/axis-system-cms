"""Paired trace comparison – analysis layer for comparing two episode traces."""

from axis.framework.comparison.compare import compare_episode_traces, compare_runs
from axis.framework.comparison.types import (
    ActionDivergence,
    ActionUsageComparison,
    AlignmentSummary,
    AmbiguityState,
    GenericComparisonMetrics,
    MetricSummaryStats,
    OutcomeComparison,
    PairedTraceComparisonResult,
    PairValidationResult,
    PairingMode,
    PositionDivergence,
    ResultMode,
    RunComparisonResult,
    RunComparisonSummary,
    VitalityDivergence,
)

__all__ = [
    "compare_episode_traces",
    "compare_runs",
    "ActionDivergence",
    "ActionUsageComparison",
    "AlignmentSummary",
    "AmbiguityState",
    "GenericComparisonMetrics",
    "MetricSummaryStats",
    "OutcomeComparison",
    "PairedTraceComparisonResult",
    "PairValidationResult",
    "PairingMode",
    "PositionDivergence",
    "ResultMode",
    "RunComparisonResult",
    "RunComparisonSummary",
    "VitalityDivergence",
]
