"""Toroidal world configuration -- validated by the toroidal factory.

Shares the same config schema as grid_2d since the toroidal world
is a topology variant with the same cell model.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ToroidalWorldConfig(BaseModel):
    """Configuration for the toroidal grid world."""

    model_config = ConfigDict(frozen=True)

    grid_width: int = Field(..., gt=0)
    grid_height: int = Field(..., gt=0)
    obstacle_density: float = Field(default=0.0, ge=0.0, lt=1.0)
    resource_regen_rate: float = Field(default=0.0, ge=0, le=1)
    regeneration_mode: str = "all_traversable"
    regen_eligible_ratio: float | None = Field(default=None, gt=0, le=1)
