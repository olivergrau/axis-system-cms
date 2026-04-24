"""Tests for System C configuration models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from axis.systems.construction_kit.types.config import (
    AgentConfig,
    PolicyConfig,
    TransitionConfig,
)
from axis.systems.system_c.config import PredictionConfig, SystemCConfig
from tests.builders.system_c_config_builder import SystemCConfigBuilder


class TestPredictionConfig:
    """PredictionConfig default values and validation."""

    def test_defaults_match_spec(self) -> None:
        cfg = PredictionConfig()
        assert cfg.memory_learning_rate == 0.3
        assert cfg.context_threshold == 0.5
        assert cfg.frustration_rate == 0.2
        assert cfg.confidence_rate == 0.15
        assert cfg.positive_sensitivity == 1.0
        assert cfg.negative_sensitivity == 1.5
        assert cfg.modulation_min == 0.3
        assert cfg.modulation_max == 2.0
        assert cfg.modulation_mode == "multiplicative"
        assert cfg.prediction_bias_scale == 0.2
        assert cfg.prediction_bias_clip == 1.0
        assert cfg.positive_weights == (0.5, 0.125, 0.125, 0.125, 0.125)
        assert cfg.negative_weights == (0.5, 0.125, 0.125, 0.125, 0.125)

    def test_frozen(self) -> None:
        cfg = PredictionConfig()
        with pytest.raises(ValidationError):
            cfg.memory_learning_rate = 0.5  # type: ignore[misc]

    def test_custom_values(self) -> None:
        cfg = PredictionConfig(
            memory_learning_rate=0.1,
            frustration_rate=0.3,
            positive_sensitivity=2.0,
            modulation_mode="hybrid",
        )
        assert cfg.memory_learning_rate == 0.1
        assert cfg.frustration_rate == 0.3
        assert cfg.positive_sensitivity == 2.0
        assert cfg.modulation_mode == "hybrid"

    def test_rejects_wrong_positive_weight_length(self) -> None:
        with pytest.raises(ValidationError):
            PredictionConfig(positive_weights=(1.0, 0.0))

    def test_rejects_wrong_negative_weight_length(self) -> None:
        with pytest.raises(ValidationError):
            PredictionConfig(negative_weights=(1.0, 0.0))

    def test_rejects_negative_weights(self) -> None:
        with pytest.raises(ValidationError):
            PredictionConfig(
                positive_weights=(0.5, 0.125, 0.125, -0.125, 0.375),
            )

    def test_rejects_non_normalized_positive_weights(self) -> None:
        with pytest.raises(ValidationError):
            PredictionConfig(
                positive_weights=(0.5, 0.125, 0.125, 0.125, 0.100),
            )

    def test_rejects_non_normalized_negative_weights(self) -> None:
        with pytest.raises(ValidationError):
            PredictionConfig(
                negative_weights=(0.5, 0.125, 0.125, 0.125, 0.100),
            )

    def test_rejects_inverted_modulation_bounds(self) -> None:
        with pytest.raises(ValidationError):
            PredictionConfig(modulation_min=1.2, modulation_max=1.1)

    def test_rejects_invalid_modulation_mode(self) -> None:
        with pytest.raises(ValidationError):
            PredictionConfig(modulation_mode="unknown")  # type: ignore[arg-type]


class TestSystemCConfig:
    """SystemCConfig parsing and validation."""

    def test_from_builder_dict(self) -> None:
        d = SystemCConfigBuilder().build()
        config = SystemCConfig(**d)
        assert config.agent.initial_energy == 50.0
        assert config.policy.selection_mode == "sample"
        assert config.transition.move_cost == 1.0
        assert config.prediction.memory_learning_rate == 0.3

    def test_prediction_defaults_when_omitted(self) -> None:
        config = SystemCConfig(
            agent=AgentConfig(
                initial_energy=50, max_energy=100, buffer_capacity=5,
            ),
            policy=PolicyConfig(
                selection_mode="sample", temperature=1.0,
                stay_suppression=0.1, consume_weight=1.5,
            ),
            transition=TransitionConfig(
                move_cost=1.0, consume_cost=1.0, stay_cost=0.5,
                max_consume=1.0, energy_gain_factor=10.0,
            ),
        )
        assert config.prediction.memory_learning_rate == 0.3
        assert config.prediction.negative_sensitivity == 1.5

    def test_sub_configs_accessible(self) -> None:
        d = SystemCConfigBuilder().build()
        config = SystemCConfig(**d)
        assert isinstance(config.agent, AgentConfig)
        assert isinstance(config.policy, PolicyConfig)
        assert isinstance(config.transition, TransitionConfig)
        assert isinstance(config.prediction, PredictionConfig)

    def test_frozen(self) -> None:
        d = SystemCConfigBuilder().build()
        config = SystemCConfig(**d)
        with pytest.raises(ValidationError):
            config.agent.initial_energy = 999.0  # type: ignore[misc]
