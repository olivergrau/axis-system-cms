"""Maslow-like drive weight computation."""

from __future__ import annotations

from axis.systems.construction_kit.arbitration.types import DriveWeights


def compute_maslow_weights(
    primary_activation: float,
    *,
    primary_weight_base: float,
    secondary_weight_base: float,
    gating_sharpness: float,
) -> DriveWeights:
    """Compute Maslow-like drive weights from primary drive activation.

    w_primary = primary_weight_base + (1 - primary_weight_base) * primary_activation^gamma
    w_secondary = secondary_weight_base * (1 - primary_activation)^gamma

    where gamma = gating_sharpness.
    """
    gamma = gating_sharpness
    w_primary = primary_weight_base + \
        (1 - primary_weight_base) * (primary_activation ** gamma)
    w_secondary = secondary_weight_base * ((1.0 - primary_activation) ** gamma)
    return DriveWeights(hunger_weight=w_primary, curiosity_weight=w_secondary)
