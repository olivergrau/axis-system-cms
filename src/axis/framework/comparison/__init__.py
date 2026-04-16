"""Paired trace comparison – analysis layer for comparing two episode traces."""

from axis.framework.comparison.compare import compare_episode_traces
from axis.framework.comparison.types import (
    ActionDivergence,
    ActionUsageComparison,
    AlignmentSummary,
    AmbiguityState,
    GenericComparisonMetrics,
    OutcomeComparison,
    PairedTraceComparisonResult,
    PairValidationResult,
    PairingMode,
    PositionDivergence,
    ResultMode,
    VitalityDivergence,
)

__all__ = [
    "compare_episode_traces",
    "ActionDivergence",
    "ActionUsageComparison",
    "AlignmentSummary",
    "AmbiguityState",
    "GenericComparisonMetrics",
    "OutcomeComparison",
    "PairedTraceComparisonResult",
    "PairValidationResult",
    "PairingMode",
    "PositionDivergence",
    "ResultMode",
    "VitalityDivergence",
]
