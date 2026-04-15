"""System A+W configuration models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from axis.systems.construction_kit.types.config import AgentConfig, PolicyConfig, TransitionConfig


class CuriosityConfig(BaseModel):
    """Curiosity drive parameters (Model Section 11.2)."""

    model_config = ConfigDict(frozen=True)

    base_curiosity: float = Field(default=1.0, ge=0, le=1)
    spatial_sensory_balance: float = Field(default=0.5, ge=0, le=1)
    explore_suppression: float = Field(default=0.3, ge=0)
    novelty_sharpness: float = Field(default=1.0, gt=0)


class ArbitrationConfig(BaseModel):
    """Drive arbitration parameters (Model Section 6.4)."""

    model_config = ConfigDict(frozen=True)

    hunger_weight_base: float = Field(default=0.3, gt=0, le=1)
    curiosity_weight_base: float = Field(default=1.0, gt=0)
    gating_sharpness: float = Field(default=2.0, gt=0)


class SystemAWConfig(BaseModel):
    """Complete System A+W configuration.

    Extends SystemAConfig with curiosity drive and
    drive arbitration parameters.
    """

    model_config = ConfigDict(frozen=True)

    agent: AgentConfig
    policy: PolicyConfig
    transition: TransitionConfig
    curiosity: CuriosityConfig = Field(default_factory=CuriosityConfig)
    arbitration: ArbitrationConfig = Field(default_factory=ArbitrationConfig)
