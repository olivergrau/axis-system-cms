"""Fluent builder for System C+W config dicts."""

from __future__ import annotations

from tests.builders.system_aw_config_builder import SystemAWConfigBuilder
from tests.constants import (
    DEFAULT_CONFIDENCE_RATE,
    DEFAULT_CW_CONTEXT_CARDINALITY,
    DEFAULT_CW_LOCAL_RESOURCE_CURRENT_WEIGHT,
    DEFAULT_CW_LOCAL_RESOURCE_NEIGHBOR_WEIGHT,
    DEFAULT_CW_NEGATIVE_WEIGHTS,
    DEFAULT_CW_NONMOVE_CURIOSITY_PENALTY,
    DEFAULT_CW_NOVELTY_CONTRAST_THRESHOLD,
    DEFAULT_CW_NOVELTY_THRESHOLD,
    DEFAULT_CW_POSITIVE_WEIGHTS,
    DEFAULT_CW_RESOURCE_THRESHOLD,
    DEFAULT_FRUSTRATION_RATE,
    DEFAULT_MEMORY_LEARNING_RATE,
    DEFAULT_MODULATION_MAX,
    DEFAULT_MODULATION_MIN,
    DEFAULT_MODULATION_MODE,
    DEFAULT_NEGATIVE_SENSITIVITY,
    DEFAULT_PREDICTION_BIAS_CLIP,
    DEFAULT_PREDICTION_BIAS_SCALE,
    DEFAULT_POSITIVE_SENSITIVITY,
)


class SystemCWConfigBuilder(SystemAWConfigBuilder):
    """Fluent builder for System C+W config dicts."""

    def __init__(self) -> None:
        super().__init__()
        drive_prediction = {
            "frustration_rate": DEFAULT_FRUSTRATION_RATE,
            "confidence_rate": DEFAULT_CONFIDENCE_RATE,
            "positive_sensitivity": DEFAULT_POSITIVE_SENSITIVITY,
            "negative_sensitivity": DEFAULT_NEGATIVE_SENSITIVITY,
            "modulation_min": DEFAULT_MODULATION_MIN,
            "modulation_max": DEFAULT_MODULATION_MAX,
            "modulation_mode": DEFAULT_MODULATION_MODE,
            "prediction_bias_scale": DEFAULT_PREDICTION_BIAS_SCALE,
            "prediction_bias_clip": DEFAULT_PREDICTION_BIAS_CLIP,
        }
        self._prediction: dict = {
            "shared": {
                "memory_learning_rate": DEFAULT_MEMORY_LEARNING_RATE,
                "resource_threshold": DEFAULT_CW_RESOURCE_THRESHOLD,
                "novelty_threshold": DEFAULT_CW_NOVELTY_THRESHOLD,
                "novelty_contrast_threshold": DEFAULT_CW_NOVELTY_CONTRAST_THRESHOLD,
                "context_cardinality": DEFAULT_CW_CONTEXT_CARDINALITY,
                "local_resource_current_weight": DEFAULT_CW_LOCAL_RESOURCE_CURRENT_WEIGHT,
                "local_resource_neighbor_weight": DEFAULT_CW_LOCAL_RESOURCE_NEIGHBOR_WEIGHT,
                "positive_weights": DEFAULT_CW_POSITIVE_WEIGHTS,
                "negative_weights": DEFAULT_CW_NEGATIVE_WEIGHTS,
            },
            "hunger": dict(drive_prediction),
            "curiosity": dict(drive_prediction),
            "outcomes": {
                "nonmove_curiosity_penalty": DEFAULT_CW_NONMOVE_CURIOSITY_PENALTY,
            },
        }

    def with_shared_prediction(self, **kwargs: float | int | tuple[float, ...]) -> SystemCWConfigBuilder:
        self._prediction["shared"].update(kwargs)
        return self

    def with_hunger_prediction(self, **kwargs: float | str) -> SystemCWConfigBuilder:
        self._prediction["hunger"].update(kwargs)
        return self

    def with_curiosity_prediction(self, **kwargs: float | str) -> SystemCWConfigBuilder:
        self._prediction["curiosity"].update(kwargs)
        return self

    def with_nonmove_curiosity_penalty(self, value: float) -> SystemCWConfigBuilder:
        self._prediction["outcomes"]["nonmove_curiosity_penalty"] = value
        return self

    def build(self) -> dict:
        base = super().build()
        base["prediction"] = {
            "shared": dict(self._prediction["shared"]),
            "hunger": dict(self._prediction["hunger"]),
            "curiosity": dict(self._prediction["curiosity"]),
            "outcomes": dict(self._prediction["outcomes"]),
        }
        return base
