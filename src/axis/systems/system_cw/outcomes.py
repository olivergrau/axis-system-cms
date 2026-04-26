"""System C+W predictive outcome semantics."""

from __future__ import annotations

from dataclasses import dataclass

from axis.sdk.actions import MOVEMENT_DELTAS
from axis.systems.construction_kit.observation.types import Observation


@dataclass(frozen=True)
class DriveOutcomeEvaluation:
    """Actual vs predicted scalar drive outcome for one action."""

    actual: float
    predicted: float
    error_positive: float
    error_negative: float


def compute_local_resource_value(
    observation: Observation,
    *,
    current_weight: float,
    neighbor_weight: float,
) -> float:
    """Compute the bounded local resource-value functional from observation."""
    neighbor_mean = (
        observation.up.resource
        + observation.down.resource
        + observation.left.resource
        + observation.right.resource
    ) / 4.0
    return (
        current_weight * observation.current.resource
        + neighbor_weight * neighbor_mean
    )


def compute_predicted_local_resource_value(
    predicted_features: tuple[float, ...],
    *,
    current_weight: float,
    neighbor_weight: float,
) -> float:
    """Compute the predicted local resource value from a C+W feature vector."""
    neighbor_mean = sum(predicted_features[1:5]) / 4.0
    return (
        current_weight * predicted_features[0]
        + neighbor_weight * neighbor_mean
    )


def compute_hunger_outcome(
    pre_observation: Observation,
    post_observation: Observation,
    predicted_features: tuple[float, ...],
    *,
    current_weight: float,
    neighbor_weight: float,
) -> DriveOutcomeEvaluation:
    """Compute hunger-side opportunity outcome and signed deviations."""
    pre_value = compute_local_resource_value(
        pre_observation,
        current_weight=current_weight,
        neighbor_weight=neighbor_weight,
    )
    post_value = compute_local_resource_value(
        post_observation,
        current_weight=current_weight,
        neighbor_weight=neighbor_weight,
    )
    predicted_value = compute_predicted_local_resource_value(
        predicted_features,
        current_weight=current_weight,
        neighbor_weight=neighbor_weight,
    )

    actual = post_value - pre_value
    predicted = predicted_value - pre_value
    return DriveOutcomeEvaluation(
        actual=actual,
        predicted=predicted,
        error_positive=max(actual - predicted, 0.0),
        error_negative=max(predicted - actual, 0.0),
    )


def novelty_weight_for_action(
    action: str,
    directional_novelty: tuple[float, float, float, float],
) -> float:
    """Return the pre-action novelty weight for the chosen action."""
    if action == "up":
        return directional_novelty[0]
    if action == "down":
        return directional_novelty[1]
    if action == "left":
        return directional_novelty[2]
    if action == "right":
        return directional_novelty[3]
    return 0.0


def compute_curiosity_outcome(
    *,
    action: str,
    pre_observation: Observation,
    post_observation: Observation,
    predicted_features: tuple[float, ...],
    curiosity_activation: float,
    novelty_weight: float,
    nonmove_penalty: float,
    current_weight: float,
    neighbor_weight: float,
) -> DriveOutcomeEvaluation:
    """Compute curiosity-side novelty-weighted yield and signed deviations."""
    if action not in MOVEMENT_DELTAS:
        suppressive = -nonmove_penalty * curiosity_activation
        return DriveOutcomeEvaluation(
            actual=suppressive,
            predicted=suppressive,
            error_positive=0.0,
            error_negative=0.0,
        )

    hunger_eval = compute_hunger_outcome(
        pre_observation,
        post_observation,
        predicted_features,
        current_weight=current_weight,
        neighbor_weight=neighbor_weight,
    )
    actual = novelty_weight * hunger_eval.actual
    predicted = novelty_weight * hunger_eval.predicted
    return DriveOutcomeEvaluation(
        actual=actual,
        predicted=predicted,
        error_positive=max(actual - predicted, 0.0),
        error_negative=max(predicted - actual, 0.0),
    )
