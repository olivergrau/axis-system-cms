"""Fluent builder for System C config dicts."""

from __future__ import annotations

from tests.builders.system_config_builder import SystemAConfigBuilder
from tests.constants import (
    DEFAULT_CONFIDENCE_RATE,
    DEFAULT_CONTEXT_THRESHOLD,
    DEFAULT_FRUSTRATION_RATE,
    DEFAULT_MEMORY_LEARNING_RATE,
    DEFAULT_MODULATION_MAX,
    DEFAULT_MODULATION_MIN,
    DEFAULT_MODULATION_MODE,
    DEFAULT_NEGATIVE_SENSITIVITY,
    DEFAULT_NEGATIVE_WEIGHTS,
    DEFAULT_PREDICTION_BIAS_CLIP,
    DEFAULT_PREDICTION_BIAS_SCALE,
    DEFAULT_POSITIVE_SENSITIVITY,
    DEFAULT_POSITIVE_WEIGHTS,
)


class SystemCConfigBuilder(SystemAConfigBuilder):
    """Fluent builder for System C config dicts.

    Extends SystemAConfigBuilder with a prediction section.
    """

    def __init__(self) -> None:
        super().__init__()
        self._prediction: dict = {
            "memory_learning_rate": DEFAULT_MEMORY_LEARNING_RATE,
            "context_threshold": DEFAULT_CONTEXT_THRESHOLD,
            "frustration_rate": DEFAULT_FRUSTRATION_RATE,
            "confidence_rate": DEFAULT_CONFIDENCE_RATE,
            "positive_sensitivity": DEFAULT_POSITIVE_SENSITIVITY,
            "negative_sensitivity": DEFAULT_NEGATIVE_SENSITIVITY,
            "modulation_min": DEFAULT_MODULATION_MIN,
            "modulation_max": DEFAULT_MODULATION_MAX,
            "modulation_mode": DEFAULT_MODULATION_MODE,
            "prediction_bias_scale": DEFAULT_PREDICTION_BIAS_SCALE,
            "prediction_bias_clip": DEFAULT_PREDICTION_BIAS_CLIP,
            "positive_weights": DEFAULT_POSITIVE_WEIGHTS,
            "negative_weights": DEFAULT_NEGATIVE_WEIGHTS,
        }

    def with_memory_learning_rate(self, value: float) -> SystemCConfigBuilder:
        self._prediction["memory_learning_rate"] = value
        return self

    def with_context_threshold(self, value: float) -> SystemCConfigBuilder:
        self._prediction["context_threshold"] = value
        return self

    def with_frustration_rate(self, value: float) -> SystemCConfigBuilder:
        self._prediction["frustration_rate"] = value
        return self

    def with_confidence_rate(self, value: float) -> SystemCConfigBuilder:
        self._prediction["confidence_rate"] = value
        return self

    def with_positive_sensitivity(self, value: float) -> SystemCConfigBuilder:
        self._prediction["positive_sensitivity"] = value
        return self

    def with_negative_sensitivity(self, value: float) -> SystemCConfigBuilder:
        self._prediction["negative_sensitivity"] = value
        return self

    def with_modulation_min(self, value: float) -> SystemCConfigBuilder:
        self._prediction["modulation_min"] = value
        return self

    def with_modulation_max(self, value: float) -> SystemCConfigBuilder:
        self._prediction["modulation_max"] = value
        return self

    def with_modulation_mode(self, value: str) -> SystemCConfigBuilder:
        self._prediction["modulation_mode"] = value
        return self

    def with_prediction_bias_scale(self, value: float) -> SystemCConfigBuilder:
        self._prediction["prediction_bias_scale"] = value
        return self

    def with_prediction_bias_clip(self, value: float) -> SystemCConfigBuilder:
        self._prediction["prediction_bias_clip"] = value
        return self

    def with_positive_weights(self, value: tuple[float, ...]) -> SystemCConfigBuilder:
        self._prediction["positive_weights"] = value
        return self

    def with_negative_weights(self, value: tuple[float, ...]) -> SystemCConfigBuilder:
        self._prediction["negative_weights"] = value
        return self

    def build(self) -> dict:
        base = super().build()
        base["prediction"] = dict(self._prediction)
        return base
