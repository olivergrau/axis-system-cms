"""Drive output types for the System Construction Kit."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class HungerDriveOutput(BaseModel):
    """Output of the hunger drive computation.

    activation: scalar hunger level d_H(t) in [0, 1]
    action_contributions: 6-element tuple indexed by action order
        (UP, DOWN, LEFT, RIGHT, CONSUME, STAY)
    """

    model_config = ConfigDict(frozen=True)

    activation: float = Field(..., ge=0, le=1)
    action_contributions: tuple[
        float, float, float, float, float, float,
    ]


class CuriosityDriveOutput(BaseModel):
    """Output of the curiosity drive computation.

    activation: scalar curiosity level d_C(t) in [0, mu_C]
    spatial_novelty: per-direction spatial novelty (up, down, left, right)
    sensory_novelty: per-direction sensory novelty (up, down, left, right)
    composite_novelty: per-direction composite novelty (up, down, left, right)
    action_contributions: 6-element tuple indexed by action order
        (UP, DOWN, LEFT, RIGHT, CONSUME, STAY)

    Model reference: Sections 5.2, 6.3.
    """

    model_config = ConfigDict(frozen=True)

    activation: float = Field(..., ge=0, le=1)

    spatial_novelty: tuple[float, float, float, float] = Field(
        ..., description="(up, down, left, right)",
    )
    sensory_novelty: tuple[float, float, float, float] = Field(
        ..., description="(up, down, left, right)",
    )
    composite_novelty: tuple[float, float, float, float] = Field(
        ..., description="(up, down, left, right)",
    )

    action_contributions: tuple[
        float, float, float, float, float, float,
    ] = Field(..., description="(UP, DOWN, LEFT, RIGHT, CONSUME, STAY)")
