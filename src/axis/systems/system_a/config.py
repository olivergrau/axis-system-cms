"""System A configuration models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AgentConfig(BaseModel):
    """Agent initialization parameters."""

    model_config = ConfigDict(frozen=True)

    initial_energy: float = Field(..., gt=0)
    max_energy: float = Field(..., gt=0)
    memory_capacity: int = Field(..., gt=0)

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

    selection_mode: str  # "sample" or "argmax"
    temperature: float = Field(..., gt=0)
    stay_suppression: float = Field(..., ge=0)
    consume_weight: float = Field(..., gt=0)


class TransitionConfig(BaseModel):
    """Transition engine cost and energy parameters."""

    model_config = ConfigDict(frozen=True)

    move_cost: float = Field(..., gt=0)
    consume_cost: float = Field(..., gt=0)
    stay_cost: float = Field(..., ge=0)
    max_consume: float = Field(..., gt=0)
    energy_gain_factor: float = Field(..., ge=0)


class WorldDynamicsConfig(BaseModel):
    """System A world dynamics parameters (system-owned per Q12)."""

    model_config = ConfigDict(frozen=True)

    resource_regen_rate: float = Field(default=0.0, ge=0, le=1)
    regeneration_mode: str = "all_traversable"
    regen_eligible_ratio: float | None = Field(default=None, gt=0, le=1)


class SystemAConfig(BaseModel):
    """Complete System A configuration.

    Parsed from the opaque ``system: dict[str, Any]`` in ExperimentConfig.
    """

    model_config = ConfigDict(frozen=True)

    agent: AgentConfig
    policy: PolicyConfig
    transition: TransitionConfig
    world_dynamics: WorldDynamicsConfig = Field(
        default_factory=WorldDynamicsConfig,
    )
