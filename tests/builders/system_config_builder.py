"""Fluent builder for System A config dicts."""

from __future__ import annotations

from tests.constants import (
    DEFAULT_CONSUME_COST,
    DEFAULT_CONSUME_WEIGHT,
    DEFAULT_ENERGY_GAIN_FACTOR,
    DEFAULT_INITIAL_ENERGY,
    DEFAULT_MAX_CONSUME,
    DEFAULT_MAX_ENERGY,
    DEFAULT_BUFFER_CAPACITY,
    DEFAULT_MOVE_COST,
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
            "buffer_capacity": DEFAULT_BUFFER_CAPACITY,
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

    def with_initial_energy(self, energy: float) -> SystemAConfigBuilder:
        self._agent["initial_energy"] = energy
        return self

    def with_max_energy(self, energy: float) -> SystemAConfigBuilder:
        self._agent["max_energy"] = energy
        return self

    def with_temperature(self, temp: float) -> SystemAConfigBuilder:
        self._policy["temperature"] = temp
        return self

    def with_buffer_capacity(self, capacity: int) -> SystemAConfigBuilder:
        self._agent["buffer_capacity"] = capacity
        return self

    def with_selection_mode(self, mode: str) -> SystemAConfigBuilder:
        self._policy["selection_mode"] = mode
        return self

    def with_stay_suppression(self, value: float) -> SystemAConfigBuilder:
        self._policy["stay_suppression"] = value
        return self

    def with_consume_weight(self, value: float) -> SystemAConfigBuilder:
        self._policy["consume_weight"] = value
        return self

    def with_move_cost(self, cost: float) -> SystemAConfigBuilder:
        self._transition["move_cost"] = cost
        return self

    def with_consume_cost(self, cost: float) -> SystemAConfigBuilder:
        self._transition["consume_cost"] = cost
        return self

    def with_stay_cost(self, cost: float) -> SystemAConfigBuilder:
        self._transition["stay_cost"] = cost
        return self

    def with_max_consume(self, value: float) -> SystemAConfigBuilder:
        self._transition["max_consume"] = value
        return self

    def with_energy_gain_factor(self, value: float) -> SystemAConfigBuilder:
        self._transition["energy_gain_factor"] = value
        return self

    def build(self) -> dict:
        return {
            "agent": dict(self._agent),
            "policy": dict(self._policy),
            "transition": dict(self._transition),
        }
