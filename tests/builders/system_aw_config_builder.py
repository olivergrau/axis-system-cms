"""Fluent builder for System A+W config dicts."""

from __future__ import annotations

from tests.builders.system_config_builder import SystemAConfigBuilder
from tests.constants import (
    DEFAULT_BASE_CURIOSITY,
    DEFAULT_CURIOSITY_WEIGHT_BASE,
    DEFAULT_EXPLORE_SUPPRESSION,
    DEFAULT_GATING_SHARPNESS,
    DEFAULT_HUNGER_WEIGHT_BASE,
    DEFAULT_SPATIAL_SENSORY_BALANCE,
)


class SystemAWConfigBuilder(SystemAConfigBuilder):
    """Fluent builder for System A+W config dicts.

    Extends SystemAConfigBuilder with curiosity and arbitration sections.
    """

    def __init__(self) -> None:
        super().__init__()
        self._curiosity = {
            "base_curiosity": DEFAULT_BASE_CURIOSITY,
            "spatial_sensory_balance": DEFAULT_SPATIAL_SENSORY_BALANCE,
            "explore_suppression": DEFAULT_EXPLORE_SUPPRESSION,
        }
        self._arbitration = {
            "hunger_weight_base": DEFAULT_HUNGER_WEIGHT_BASE,
            "curiosity_weight_base": DEFAULT_CURIOSITY_WEIGHT_BASE,
            "gating_sharpness": DEFAULT_GATING_SHARPNESS,
        }

    def with_base_curiosity(self, value: float) -> SystemAWConfigBuilder:
        self._curiosity["base_curiosity"] = value
        return self

    def with_spatial_sensory_balance(self, value: float) -> SystemAWConfigBuilder:
        self._curiosity["spatial_sensory_balance"] = value
        return self

    def with_explore_suppression(self, value: float) -> SystemAWConfigBuilder:
        self._curiosity["explore_suppression"] = value
        return self

    def with_hunger_weight_base(self, value: float) -> SystemAWConfigBuilder:
        self._arbitration["hunger_weight_base"] = value
        return self

    def with_curiosity_weight_base(self, value: float) -> SystemAWConfigBuilder:
        self._arbitration["curiosity_weight_base"] = value
        return self

    def with_gating_sharpness(self, value: float) -> SystemAWConfigBuilder:
        self._arbitration["gating_sharpness"] = value
        return self

    def build(self) -> dict:
        base = super().build()
        base["curiosity"] = dict(self._curiosity)
        base["arbitration"] = dict(self._arbitration)
        return base
