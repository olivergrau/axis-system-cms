"""Scenario fixtures: configuration and transition step kwargs."""

from __future__ import annotations

import copy

import pytest

from axis_system_a import SimulationConfig


_BASE_CONFIG_DICT: dict = {
    "general": {"seed": 42},
    "world": {"grid_width": 10, "grid_height": 10},
    "agent": {
        "initial_energy": 50.0,
        "max_energy": 100.0,
        "memory_capacity": 5,
    },
    "policy": {
        "selection_mode": "sample",
        "temperature": 1.0,
        "stay_suppression": 0.1,
        "consume_weight": 1.5,
    },
    "transition": {
        "move_cost": 1.0,
        "consume_cost": 1.0,
        "stay_cost": 0.5,
        "max_consume": 1.0,
        "energy_gain_factor": 10.0,
    },
    "execution": {"max_steps": 1000},
}


def make_config(overrides: dict | None = None) -> SimulationConfig:
    """Build a SimulationConfig from defaults with optional section-level overrides."""
    d = copy.deepcopy(_BASE_CONFIG_DICT)
    if overrides:
        for section, vals in overrides.items():
            if section in d and isinstance(d[section], dict):
                d[section].update(vals)
            else:
                d[section] = vals
    return SimulationConfig(**d)


@pytest.fixture
def valid_config_dict() -> dict:
    """Minimal valid configuration dictionary."""
    return copy.deepcopy(_BASE_CONFIG_DICT)


@pytest.fixture
def valid_config() -> SimulationConfig:
    """Valid SimulationConfig instance."""
    return make_config()


_DEFAULT_STEP_KWARGS: dict = dict(
    move_cost=1.0,
    consume_cost=1.0,
    stay_cost=0.5,
    max_consume=1.0,
    energy_gain_factor=10.0,
    max_energy=100.0,
    resource_regen_rate=0.0,
)


@pytest.fixture
def default_step_kwargs() -> dict:
    """Standard cost parameters for transition step() tests."""
    return dict(**_DEFAULT_STEP_KWARGS)
