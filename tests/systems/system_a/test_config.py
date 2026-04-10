"""WP-2.4 unit tests -- SystemAConfig."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from axis.systems.system_a.config import (
    AgentConfig,
    PolicyConfig,
    SystemAConfig,
    TransitionConfig,
)
from tests.builders.system_config_builder import SystemAConfigBuilder


class TestConfig:
    """SystemAConfig validation tests."""

    def test_valid_construction(self) -> None:
        config = SystemAConfig(
            agent=AgentConfig(initial_energy=50,
                              max_energy=100, buffer_capacity=5),
            policy=PolicyConfig(
                selection_mode="sample", temperature=1.0,
                stay_suppression=0.1, consume_weight=1.5,
            ),
            transition=TransitionConfig(
                move_cost=1.0, consume_cost=1.0, stay_cost=0.5,
                max_consume=1.0, energy_gain_factor=10.0,
            ),
        )
        assert config.agent.initial_energy == 50.0

    def test_from_builder_dict(self) -> None:
        d = SystemAConfigBuilder().build()
        config = SystemAConfig(**d)
        assert config.agent.initial_energy == 50.0
        assert config.policy.selection_mode == "sample"
        assert config.transition.move_cost == 1.0

    def test_agent_energy_bounds(self) -> None:
        with pytest.raises(ValidationError, match="initial_energy"):
            AgentConfig(initial_energy=200.0,
                        max_energy=100.0, buffer_capacity=5)

    def test_policy_config_values(self) -> None:
        d = SystemAConfigBuilder().build()
        config = SystemAConfig(**d)
        assert config.policy.selection_mode == "sample"
        assert config.policy.temperature == 1.0
        assert config.policy.stay_suppression == 0.1
        assert config.policy.consume_weight == 1.5

    def test_transition_config_values(self) -> None:
        d = SystemAConfigBuilder().build()
        config = SystemAConfig(**d)
        assert config.transition.move_cost == 1.0
        assert config.transition.consume_cost == 1.0
        assert config.transition.stay_cost == 0.5
        assert config.transition.max_consume == 1.0
        assert config.transition.energy_gain_factor == 10.0

    def test_frozen(self) -> None:
        d = SystemAConfigBuilder().build()
        config = SystemAConfig(**d)
        with pytest.raises(ValidationError):
            config.agent.initial_energy = 999.0  # type: ignore[misc]
