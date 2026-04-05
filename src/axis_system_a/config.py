"""Configuration models for AXIS System A runtime."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axis_system_a.enums import RegenerationMode, SelectionMode


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
    obstacle_density: float = Field(default=0.0, ge=0, lt=1)
    regeneration_mode: RegenerationMode = RegenerationMode.ALL_TRAVERSABLE
    regen_eligible_ratio: float | None = Field(default=None, gt=0, le=1)

    @model_validator(mode="after")
    def check_sparse_ratio_required(self) -> WorldConfig:
        if (
            self.regeneration_mode == RegenerationMode.SPARSE_FIXED_RATIO
            and self.regen_eligible_ratio is None
        ):
            raise ValueError(
                "regen_eligible_ratio is required when "
                "regeneration_mode is 'sparse_fixed_ratio'"
            )
        return self


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


class LoggingConfig(BaseModel):
    """Logging and observability configuration."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    console_enabled: bool = True
    jsonl_enabled: bool = False
    jsonl_path: str | None = None
    include_decision_trace: bool = True
    include_transition_trace: bool = True
    verbosity: str = "compact"  # "compact" | "verbose"

    @model_validator(mode="after")
    def check_jsonl_path_required(self) -> LoggingConfig:
        if self.jsonl_enabled and self.jsonl_path is None:
            raise ValueError(
                "jsonl_path must be provided when jsonl_enabled is True"
            )
        return self


class SimulationConfig(BaseModel):
    """Top-level simulation configuration. Single source of truth for all runtime parameters."""

    model_config = ConfigDict(frozen=True)

    general: GeneralConfig
    world: WorldConfig
    agent: AgentConfig
    policy: PolicyConfig
    transition: TransitionConfig
    execution: ExecutionConfig
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
