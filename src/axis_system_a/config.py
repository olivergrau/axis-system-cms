"""Configuration models for AXIS System A runtime."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axis_system_a.enums import SelectionMode


class GeneralConfig(BaseModel):
    """General simulation configuration."""

    model_config = ConfigDict(frozen=True)

    seed: int


class WorldConfig(BaseModel):
    """World grid configuration."""

    model_config = ConfigDict(frozen=True)

    grid_width: int = Field(..., gt=0)
    grid_height: int = Field(..., gt=0)
    resource_regen_rate: float = Field(default=0.0, ge=0, le=1)


class AgentConfig(BaseModel):
    """Agent initialization configuration."""

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
    """Policy and action selection configuration."""

    model_config = ConfigDict(frozen=True)

    selection_mode: SelectionMode
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


class ExecutionConfig(BaseModel):
    """Execution constraints configuration."""

    model_config = ConfigDict(frozen=True)

    max_steps: int = Field(..., gt=0)


class SimulationConfig(BaseModel):
    """Top-level simulation configuration. Single source of truth for all runtime parameters."""

    model_config = ConfigDict(frozen=True)

    general: GeneralConfig
    world: WorldConfig
    agent: AgentConfig
    policy: PolicyConfig
    transition: TransitionConfig
    execution: ExecutionConfig
