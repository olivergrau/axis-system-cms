"""Hunger drive module for baseline action scoring."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from axis_system_a.types import Observation


class HungerDriveOutput(BaseModel):
    """Output of the hunger drive computation.

    activation: scalar hunger level d_H(t) in [0, 1]
    action_contributions: 6-element tuple indexed by Action enum
        (UP, DOWN, LEFT, RIGHT, CONSUME, STAY)
    """

    model_config = ConfigDict(frozen=True)

    activation: float = Field(..., ge=0, le=1)
    action_contributions: tuple[
        float, float, float, float, float, float,
    ]


def compute_hunger_drive(
    energy: float,
    max_energy: float,
    observation: Observation,
    consume_weight: float,
    stay_suppression: float,
) -> HungerDriveOutput:
    """Compute hunger drive activation and per-action contributions.

    d_H(t) = 1 - E_t / E_max

    Movement:  s_dir     = d_H * r_dir
    Consume:   s_consume = d_H * w_consume * r_c
    Stay:      s_stay    = -lambda_stay * d_H
    """
    d_h = max(0.0, min(1.0, 1.0 - energy / max_energy))

    s_up = d_h * observation.up.resource
    s_down = d_h * observation.down.resource
    s_left = d_h * observation.left.resource
    s_right = d_h * observation.right.resource
    s_consume = d_h * consume_weight * observation.current.resource
    s_stay = -stay_suppression * d_h

    return HungerDriveOutput(
        activation=d_h,
        action_contributions=(s_up, s_down, s_left,
                              s_right, s_consume, s_stay),
    )
