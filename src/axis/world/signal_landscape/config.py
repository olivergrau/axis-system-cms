"""Signal landscape configuration -- validated by the factory."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SignalLandscapeConfig(BaseModel):
    """Validated config for the signal landscape world type.

    Parsed from BaseWorldConfig extras by the factory.
    """

    model_config = ConfigDict(frozen=True)

    grid_width: int = Field(..., gt=0)
    grid_height: int = Field(..., gt=0)
    num_hotspots: int = Field(default=3, ge=1)
    hotspot_radius: float = Field(default=3.0, gt=0)
    drift_speed: float = Field(default=0.5, ge=0)
    decay_rate: float = Field(default=0.02, ge=0, le=1.0)
    obstacle_density: float = Field(default=0.0, ge=0.0, lt=1.0)
    signal_intensity: float = Field(default=1.0, gt=0, le=1.0)
