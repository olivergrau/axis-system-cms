"""System C configuration models."""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict, Field
from pydantic import model_validator

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

    @model_validator(mode="after")
    def validate_prediction_parameters(self) -> PredictionConfig:
        """Validate cross-field constraints from the System C model."""
        if self.modulation_min > self.modulation_max:
            raise ValueError("modulation_min must be <= modulation_max")

        if len(self.positive_weights) != 5:
            raise ValueError("positive_weights must have exactly 5 elements")
        if len(self.negative_weights) != 5:
            raise ValueError("negative_weights must have exactly 5 elements")

        if any(w < 0 for w in self.positive_weights):
            raise ValueError("positive_weights must be non-negative")
        if any(w < 0 for w in self.negative_weights):
            raise ValueError("negative_weights must be non-negative")

        if not math.isclose(sum(self.positive_weights), 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError("positive_weights must sum to 1.0")
        if not math.isclose(sum(self.negative_weights), 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError("negative_weights must sum to 1.0")

        return self


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
