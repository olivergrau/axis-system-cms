"""Grid-2D world configuration -- validated by the grid_2d factory."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Grid2DWorldConfig(BaseModel):
    """Configuration for the built-in 2D grid world.

    This is the world-type-specific config. The framework carries these
    values inside ``BaseWorldConfig`` extras and the grid-2D factory
    validates them by constructing this model.
    """

    model_config = ConfigDict(frozen=True)

    grid_width: int = Field(..., gt=0)
    grid_height: int = Field(..., gt=0)
    obstacle_density: float = Field(default=0.0, ge=0.0, lt=1.0)
    resource_regen_rate: float = Field(default=0.0, ge=0, le=1)
    regeneration_mode: str = "all_traversable"
    regen_eligible_ratio: float | None = Field(default=None, gt=0, le=1)
