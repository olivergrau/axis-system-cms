"""System B configuration models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AgentConfig(BaseModel):
    """Agent initialization parameters."""

    model_config = ConfigDict(frozen=True)

    initial_energy: float = Field(..., gt=0)
    max_energy: float = Field(..., gt=0)

    @model_validator(mode="after")
    def check_energy_bounds(self) -> AgentConfig:
        if self.initial_energy > self.max_energy:
            raise ValueError(
                f"initial_energy ({self.initial_energy}) must be "
                f"<= max_energy ({self.max_energy})"
            )
        return self


class PolicyConfig(BaseModel):
    """Policy and action selection parameters."""

    model_config = ConfigDict(frozen=True)

    selection_mode: str = "sample"  # "sample" or "argmax"
    temperature: float = Field(default=1.0, gt=0)
    scan_bonus: float = Field(default=2.0, ge=0)


class TransitionConfig(BaseModel):
    """Transition engine cost parameters."""

    model_config = ConfigDict(frozen=True)

    move_cost: float = Field(default=1.0, gt=0)
    scan_cost: float = Field(default=0.5, gt=0)
    stay_cost: float = Field(default=0.5, ge=0)


class WorldDynamicsConfig(BaseModel):
    """System B world dynamics parameters."""

    model_config = ConfigDict(frozen=True)

    resource_regen_rate: float = Field(default=0.0, ge=0, le=1)
    regeneration_mode: str = "all_traversable"
    regen_eligible_ratio: float | None = Field(default=None, gt=0, le=1)


class SystemBConfig(BaseModel):
    """Complete System B configuration."""

    model_config = ConfigDict(frozen=True)

    agent: AgentConfig
    policy: PolicyConfig = Field(default_factory=PolicyConfig)
    transition: TransitionConfig = Field(default_factory=TransitionConfig)
    world_dynamics: WorldDynamicsConfig = Field(
        default_factory=WorldDynamicsConfig,
    )
