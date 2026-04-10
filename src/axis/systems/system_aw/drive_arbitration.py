"""System A+W drive arbitration -- dynamic weight functions and score combination."""

from __future__ import annotations

from axis.systems.system_a.types import HungerDriveOutput
from axis.systems.system_aw.config import ArbitrationConfig
from axis.systems.system_aw.types import CuriosityDriveOutput, DriveWeights


def compute_drive_weights(
    hunger_activation: float,
    config: ArbitrationConfig,
) -> DriveWeights:
    """Compute dynamic drive weights from hunger activation.

    Enforces Maslow-like hierarchy: hunger gates curiosity.

    w_H(t) = w_H_base + (1 - w_H_base) * d_H(t)^gamma
    w_C(t) = w_C_base * (1 - d_H(t))^gamma

    Model reference: Section 6.4.
    """
    d_h = hunger_activation
    gamma = config.gating_sharpness

    w_h = config.hunger_weight_base + \
        (1 - config.hunger_weight_base) * (d_h ** gamma)
    w_c = config.curiosity_weight_base * ((1 - d_h) ** gamma)

    return DriveWeights(hunger_weight=w_h, curiosity_weight=w_c)


def compute_action_scores(
    hunger: HungerDriveOutput,
    curiosity: CuriosityDriveOutput,
    weights: DriveWeights,
) -> tuple[float, float, float, float, float, float]:
    """Combine two drive outputs into final action scores.

    psi(a) = w_H * d_H * phi_H(a) + w_C * d_C * phi_C(a)

    Returns: 6-element tuple in action order (UP, DOWN, LEFT, RIGHT, CONSUME, STAY)

    Model reference: Section 6.5.
    """
    w_h = weights.hunger_weight
    w_c = weights.curiosity_weight
    d_h = hunger.activation
    d_c = curiosity.activation

    return tuple(  # type: ignore[return-value]
        w_h * d_h * phi_h + w_c * d_c * phi_c
        for phi_h, phi_c in zip(
            hunger.action_contributions,
            curiosity.action_contributions,
        )
    )
