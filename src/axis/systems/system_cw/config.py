"""System C+W configuration models."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axis.systems.construction_kit.types.config import (
    AgentConfig,
    PolicyConfig,
    TransitionConfig,
)


class CuriosityConfig(BaseModel):
    """Curiosity drive parameters for System C+W."""

    model_config = ConfigDict(frozen=True)

    base_curiosity: float = Field(default=1.0, ge=0, le=1)
    spatial_sensory_balance: float = Field(default=0.5, ge=0, le=1)
    explore_suppression: float = Field(default=0.3, ge=0)
    novelty_sharpness: float = Field(default=1.0, gt=0)


class ArbitrationConfig(BaseModel):
    """Drive arbitration parameters for System C+W."""

    model_config = ConfigDict(frozen=True)

    hunger_weight_base: float = Field(default=0.3, gt=0, le=1)
    curiosity_weight_base: float = Field(default=1.0, gt=0)
    gating_sharpness: float = Field(default=2.0, gt=0)


class PredictionSharedConfig(BaseModel):
    """Shared predictive-memory and context parameters for System C+W."""

    model_config = ConfigDict(frozen=True)

    memory_learning_rate: float = Field(default=0.3, gt=0, le=1)
    resource_threshold: float = Field(default=0.5, ge=0, le=1)
    novelty_threshold: float = Field(default=0.35, ge=0, le=1)
    novelty_contrast_threshold: float = Field(default=0.15, ge=0, le=1)
    context_cardinality: int = Field(default=64, ge=1)
    local_resource_current_weight: float = Field(default=0.7, ge=0, le=1)
    local_resource_neighbor_weight: float = Field(default=0.3, ge=0, le=1)
    positive_weights: tuple[float, ...] = (
        0.25, 0.10, 0.10, 0.10, 0.10, 0.0875, 0.0875, 0.0875, 0.0875, 0.0,
    )
    negative_weights: tuple[float, ...] = (
        0.25, 0.10, 0.10, 0.10, 0.10, 0.0875, 0.0875, 0.0875, 0.0875, 0.0,
    )

    @model_validator(mode="after")
    def validate_shared_prediction_parameters(self) -> PredictionSharedConfig:
        """Validate cross-field constraints for shared prediction state."""
        if len(self.positive_weights) != 10:
            raise ValueError("positive_weights must have exactly 10 elements")
        if len(self.negative_weights) != 10:
            raise ValueError("negative_weights must have exactly 10 elements")

        if any(w < 0 for w in self.positive_weights):
            raise ValueError("positive_weights must be non-negative")
        if any(w < 0 for w in self.negative_weights):
            raise ValueError("negative_weights must be non-negative")

        if not math.isclose(sum(self.positive_weights), 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError("positive_weights must sum to 1.0")
        if not math.isclose(sum(self.negative_weights), 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError("negative_weights must sum to 1.0")

        total_resource_weight = (
            self.local_resource_current_weight + self.local_resource_neighbor_weight
        )
        if total_resource_weight > 1.0:
            raise ValueError(
                "local_resource_current_weight + local_resource_neighbor_weight "
                "must be <= 1.0"
            )

        return self


class DrivePredictionConfig(BaseModel):
    """Drive-specific predictive modulation and trace parameters."""

    model_config = ConfigDict(frozen=True)

    frustration_rate: float = Field(default=0.2, gt=0, le=1)
    confidence_rate: float = Field(default=0.15, gt=0, le=1)
    positive_sensitivity: float = Field(default=1.0, ge=0)
    negative_sensitivity: float = Field(default=1.5, ge=0)
    modulation_min: float = Field(default=0.3, gt=0, le=1)
    modulation_max: float = Field(default=2.0, ge=1)
    modulation_mode: Literal["multiplicative", "additive", "hybrid"] = "multiplicative"
    prediction_bias_scale: float = Field(default=0.2, ge=0)
    prediction_bias_clip: float = Field(default=1.0, gt=0, le=1)

    @model_validator(mode="after")
    def validate_drive_prediction_parameters(self) -> DrivePredictionConfig:
        """Validate cross-field modulation constraints."""
        if self.modulation_min > self.modulation_max:
            raise ValueError("modulation_min must be <= modulation_max")
        return self


class PredictionOutcomeConfig(BaseModel):
    """Outcome-specific prediction parameters."""

    model_config = ConfigDict(frozen=True)

    nonmove_curiosity_penalty: float = Field(default=0.2, ge=0)


class SystemCWPredictionConfig(BaseModel):
    """Full prediction subtree for System C+W."""

    model_config = ConfigDict(frozen=True)

    shared: PredictionSharedConfig = Field(default_factory=PredictionSharedConfig)
    hunger: DrivePredictionConfig = Field(default_factory=DrivePredictionConfig)
    curiosity: DrivePredictionConfig = Field(default_factory=DrivePredictionConfig)
    outcomes: PredictionOutcomeConfig = Field(default_factory=PredictionOutcomeConfig)


class SystemCWConfig(BaseModel):
    """Complete System C+W configuration."""

    model_config = ConfigDict(frozen=True)

    agent: AgentConfig
    policy: PolicyConfig
    transition: TransitionConfig
    curiosity: CuriosityConfig = Field(default_factory=CuriosityConfig)
    arbitration: ArbitrationConfig = Field(default_factory=ArbitrationConfig)
    prediction: SystemCWPredictionConfig = Field(default_factory=SystemCWPredictionConfig)
