"""Arbitration types -- drive weight tuples."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DriveWeights(BaseModel):
    """Drive weights from the arbitration layer."""

    model_config = ConfigDict(frozen=True)

    hunger_weight: float = Field(..., ge=0)
    curiosity_weight: float = Field(..., ge=0)
