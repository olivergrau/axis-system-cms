"""Predictive memory and prediction error processing.

Provides:
- extract_predictive_features: Omega(u_t) -> y_t
- encode_context: C(y_t) -> s_t
- PredictiveMemory: q_t(s, a) expectation store
- compute_prediction_error: signed error with aggregation
"""

from axis.systems.construction_kit.prediction.context import encode_context
from axis.systems.construction_kit.prediction.error import (
    PredictionError,
    compute_prediction_error,
)
from axis.systems.construction_kit.prediction.features import (
    extract_predictive_features,
)
from axis.systems.construction_kit.prediction.memory import (
    PredictiveMemory,
    create_predictive_memory,
    get_prediction,
    update_predictive_memory,
)

__all__ = [
    "PredictionError",
    "PredictiveMemory",
    "compute_prediction_error",
    "create_predictive_memory",
    "encode_context",
    "extract_predictive_features",
    "get_prediction",
    "update_predictive_memory",
]
