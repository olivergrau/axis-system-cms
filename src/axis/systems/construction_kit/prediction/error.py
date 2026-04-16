"""Prediction error -- signed decomposition and scalar aggregation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PredictionError(BaseModel):
    """Signed prediction error decomposition."""

    model_config = ConfigDict(frozen=True)

    positive: tuple[float, ...]
    negative: tuple[float, ...]
    scalar_positive: float
    scalar_negative: float


def compute_prediction_error(
    predicted: tuple[float, ...],
    observed: tuple[float, ...],
    *,
    positive_weights: tuple[float, ...] = (0.5, 0.125, 0.125, 0.125, 0.125),
    negative_weights: tuple[float, ...] = (0.5, 0.125, 0.125, 0.125, 0.125),
) -> PredictionError:
    """Compute signed prediction error with scalar aggregation.

    Component-wise:
        delta_t^+ = max(y_{t+1} - y_hat_{t+1}, 0)
        delta_t^- = max(y_hat_{t+1} - y_{t+1}, 0)

    Scalar aggregation:
        epsilon_t^+ = sum_j(w_j^+ * delta_t_j^+)
        epsilon_t^- = sum_j(w_j^- * delta_t_j^-)

    Args:
        predicted: Expected feature vector y_hat_{t+1}.
        observed: Realized feature vector y_{t+1}.
        positive_weights: Aggregation weights w_j^+ (should sum to 1).
        negative_weights: Aggregation weights w_j^- (should sum to 1).

    Returns:
        PredictionError with component-wise and scalar errors.
    """
    pos = tuple(max(o - p, 0.0) for o, p in zip(observed, predicted))
    neg = tuple(max(p - o, 0.0) for o, p in zip(observed, predicted))

    scalar_pos = sum(w * d for w, d in zip(positive_weights, pos))
    scalar_neg = sum(w * d for w, d in zip(negative_weights, neg))

    return PredictionError(
        positive=pos,
        negative=neg,
        scalar_positive=scalar_pos,
        scalar_negative=scalar_neg,
    )
