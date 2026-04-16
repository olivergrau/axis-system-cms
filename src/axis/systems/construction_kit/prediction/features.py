"""Predictive feature extraction -- Omega(u_t) -> y_t."""

from __future__ import annotations

from axis.systems.construction_kit.observation.types import Observation


def extract_predictive_features(observation: Observation) -> tuple[float, ...]:
    """Extract predictive feature vector y_t from observation u_t.

    For the hunger-centered instantiation, y_t contains the 5 local
    resource values in canonical order: (center, up, down, left, right).

    Args:
        observation: Von Neumann neighborhood observation.

    Returns:
        5-element tuple of resource values in [0, 1].
    """
    return (
        observation.current.resource,
        observation.up.resource,
        observation.down.resource,
        observation.left.resource,
        observation.right.resource,
    )
