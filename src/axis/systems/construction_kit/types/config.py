"""Shared configuration types used across systems."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AgentConfig(BaseModel):
    """Shared agent configuration: energy and buffer settings."""

    model_config = ConfigDict(frozen=True)

    initial_energy: float = Field(..., gt=0)
    max_energy: float = Field(..., gt=0)
    buffer_capacity: int = Field(..., gt=0)

    @model_validator(mode="after")
    def check_energy_bounds(self) -> AgentConfig:
        if self.initial_energy > self.max_energy:
            raise ValueError(
                f"initial_energy ({self.initial_energy}) "
                f"exceeds max_energy ({self.max_energy})"
            )
        return self


class PolicyConfig(BaseModel):
    """Shared policy configuration."""

    model_config = ConfigDict(frozen=True)

    selection_mode: str
    temperature: float = Field(..., gt=0)
    stay_suppression: float = Field(..., ge=0)
    consume_weight: float = Field(..., gt=0)


class TransitionConfig(BaseModel):
    """Shared transition configuration."""

    model_config = ConfigDict(frozen=True)

    move_cost: float = Field(..., gt=0)
    consume_cost: float = Field(..., gt=0)
    stay_cost: float = Field(..., ge=0)
    max_consume: float = Field(..., gt=0)
    energy_gain_factor: float = Field(..., ge=0)
