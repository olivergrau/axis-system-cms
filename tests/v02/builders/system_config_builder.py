"""Fluent builder for System A config dicts."""

from __future__ import annotations

from tests.v02.constants import (
    DEFAULT_CONSUME_COST,
    DEFAULT_CONSUME_WEIGHT,
    DEFAULT_ENERGY_GAIN_FACTOR,
    DEFAULT_INITIAL_ENERGY,
    DEFAULT_MAX_CONSUME,
    DEFAULT_MAX_ENERGY,
    DEFAULT_MEMORY_CAPACITY,
    DEFAULT_MOVE_COST,
    DEFAULT_REGEN_RATE,
    DEFAULT_SELECTION_MODE,
    DEFAULT_STAY_COST,
    DEFAULT_STAY_SUPPRESSION,
    DEFAULT_TEMPERATURE,
)


class SystemAConfigBuilder:
    """Fluent builder for System A config dicts.

    Produces a dict matching the anticipated SystemAConfig structure.
    Will be updated to produce SystemAConfig once WP-2.3 defines the type.
    """

    def __init__(self) -> None:
        self._agent = {
            "initial_energy": DEFAULT_INITIAL_ENERGY,
            "max_energy": DEFAULT_MAX_ENERGY,
            "memory_capacity": DEFAULT_MEMORY_CAPACITY,
        }
        self._policy = {
            "selection_mode": DEFAULT_SELECTION_MODE,
            "temperature": DEFAULT_TEMPERATURE,
            "stay_suppression": DEFAULT_STAY_SUPPRESSION,
            "consume_weight": DEFAULT_CONSUME_WEIGHT,
        }
        self._transition = {
            "move_cost": DEFAULT_MOVE_COST,
            "consume_cost": DEFAULT_CONSUME_COST,
            "stay_cost": DEFAULT_STAY_COST,
            "max_consume": DEFAULT_MAX_CONSUME,
            "energy_gain_factor": DEFAULT_ENERGY_GAIN_FACTOR,
        }
        self._world_dynamics = {
            "resource_regen_rate": DEFAULT_REGEN_RATE,
            "regeneration_mode": "all_traversable",
            "regen_eligible_ratio": None,
        }

    def with_initial_energy(self, energy: float) -> SystemAConfigBuilder:
        self._agent["initial_energy"] = energy
        return self

    def with_max_energy(self, energy: float) -> SystemAConfigBuilder:
        self._agent["max_energy"] = energy
        return self

    def with_temperature(self, temp: float) -> SystemAConfigBuilder:
        self._policy["temperature"] = temp
        return self

    def with_regen_rate(self, rate: float) -> SystemAConfigBuilder:
        self._world_dynamics["resource_regen_rate"] = rate
        return self

    def build(self) -> dict:
        return {
            "agent": dict(self._agent),
            "policy": dict(self._policy),
            "transition": dict(self._transition),
            "world_dynamics": dict(self._world_dynamics),
        }
