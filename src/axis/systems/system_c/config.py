"""System C configuration models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from axis.systems.construction_kit.types.config import (
    AgentConfig,
    PolicyConfig,
    TransitionConfig,
)


class PredictionConfig(BaseModel):
    """System C prediction parameters.

    Controls the predictive action modulation pipeline:
    context encoding, predictive memory learning, dual-trace
    accumulation, and exponential modulation.
    """

    model_config = ConfigDict(frozen=True)

    memory_learning_rate: float = Field(default=0.3, gt=0, le=1)
    context_threshold: float = Field(default=0.5, gt=0, le=1)
    frustration_rate: float = Field(default=0.2, gt=0, le=1)
    confidence_rate: float = Field(default=0.15, gt=0, le=1)
    positive_sensitivity: float = Field(default=1.0, ge=0)
    negative_sensitivity: float = Field(default=1.5, ge=0)
    modulation_min: float = Field(default=0.3, gt=0, le=1)
    modulation_max: float = Field(default=2.0, ge=1)
    positive_weights: tuple[float, ...] = (0.5, 0.125, 0.125, 0.125, 0.125)
    negative_weights: tuple[float, ...] = (0.5, 0.125, 0.125, 0.125, 0.125)


class SystemCConfig(BaseModel):
    """Complete System C configuration.

    Extends the System A config structure with a prediction section.
    When prediction is omitted, spec defaults apply (loss-averse
    parameterization).
    """

    model_config = ConfigDict(frozen=True)

    agent: AgentConfig
    policy: PolicyConfig
    transition: TransitionConfig
    prediction: PredictionConfig = Field(default_factory=PredictionConfig)
