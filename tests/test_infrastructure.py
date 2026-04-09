"""Verification tests for the v0.2.0 test infrastructure.

Tests that the builders, fixtures, assertion helpers, and constants
work correctly. This is infrastructure testing, not domain testing.
"""

from __future__ import annotations

import pytest

from axis.framework.config import ExperimentConfig, FrameworkConfig
from tests.builders.config_builder import FrameworkConfigBuilder
from tests.builders.system_config_builder import SystemAConfigBuilder
from tests.constants import (
    DEFAULT_GRID_HEIGHT,
    DEFAULT_GRID_WIDTH,
    DEFAULT_INITIAL_ENERGY,
    DEFAULT_MAX_ENERGY,
    DEFAULT_MAX_STEPS,
    DEFAULT_OBSTACLE_DENSITY,
    DEFAULT_SEED,
    DEFAULT_TEMPERATURE,
)
from tests.utils.assertions import assert_dict_has_keys, assert_normalized_metric


# ---------------------------------------------------------------------------
# 1. Builder smoke tests
# ---------------------------------------------------------------------------


class TestFrameworkConfigBuilder:
    def test_build_returns_framework_config(self) -> None:
        result = FrameworkConfigBuilder().build()
        assert isinstance(result, FrameworkConfig)

    def test_build_has_expected_sections(self) -> None:
        result = FrameworkConfigBuilder().build()
        assert result.general is not None
        assert result.execution is not None
        assert result.world is not None
        assert result.logging is not None

    def test_default_seed(self) -> None:
        result = FrameworkConfigBuilder().build()
        assert result.general.seed == DEFAULT_SEED

    def test_with_seed_override(self) -> None:
        result = FrameworkConfigBuilder().with_seed(99).build()
        assert result.general.seed == 99

    def test_with_max_steps_override(self) -> None:
        result = FrameworkConfigBuilder().with_max_steps(500).build()
        assert result.execution.max_steps == 500

    def test_chaining(self) -> None:
        result = FrameworkConfigBuilder().with_seed(99).with_max_steps(500).build()
        assert result.general.seed == 99
        assert result.execution.max_steps == 500

    def test_with_world_size(self) -> None:
        result = FrameworkConfigBuilder().with_world_size(20, 30).build()
        assert result.world.grid_width == 20
        assert result.world.grid_height == 30

    def test_with_obstacle_density(self) -> None:
        result = FrameworkConfigBuilder().with_obstacle_density(0.3).build()
        assert result.world.obstacle_density == 0.3

    def test_default_constants_match(self) -> None:
        result = FrameworkConfigBuilder().build()
        assert result.general.seed == DEFAULT_SEED
        assert result.execution.max_steps == DEFAULT_MAX_STEPS
        assert result.world.grid_width == DEFAULT_GRID_WIDTH
        assert result.world.grid_height == DEFAULT_GRID_HEIGHT
        assert result.world.obstacle_density == DEFAULT_OBSTACLE_DENSITY


class TestSystemAConfigBuilder:
    def test_build_has_expected_keys(self) -> None:
        result = SystemAConfigBuilder().build()
        assert set(result.keys()) == {"agent", "policy", "transition"}

    def test_default_initial_energy(self) -> None:
        result = SystemAConfigBuilder().build()
        assert result["agent"]["initial_energy"] == DEFAULT_INITIAL_ENERGY

    def test_with_initial_energy_override(self) -> None:
        result = SystemAConfigBuilder().with_initial_energy(75.0).build()
        assert result["agent"]["initial_energy"] == 75.0

    def test_with_max_energy_override(self) -> None:
        result = SystemAConfigBuilder().with_max_energy(200.0).build()
        assert result["agent"]["max_energy"] == 200.0

    def test_with_temperature_override(self) -> None:
        result = SystemAConfigBuilder().with_temperature(0.5).build()
        assert result["policy"]["temperature"] == 0.5


# ---------------------------------------------------------------------------
# 2. Fixture smoke tests
# ---------------------------------------------------------------------------


class TestFixtures:
    def test_framework_config_is_typed(self, framework_config: FrameworkConfig) -> None:
        assert isinstance(framework_config, FrameworkConfig)
        assert framework_config.general is not None
        assert framework_config.execution is not None

    def test_framework_config_dict_is_valid(self, framework_config_dict: dict) -> None:
        assert isinstance(framework_config_dict, dict)
        assert "general" in framework_config_dict
        assert "execution" in framework_config_dict

    def test_system_a_config_dict_is_valid(self, system_a_config_dict: dict) -> None:
        assert isinstance(system_a_config_dict, dict)
        assert "agent" in system_a_config_dict
        assert "policy" in system_a_config_dict

    def test_experiment_config_is_typed(
        self, experiment_config: ExperimentConfig
    ) -> None:
        assert isinstance(experiment_config, ExperimentConfig)
        assert experiment_config.system_type == "system_a"

    def test_experiment_config_dict_structure(
        self, experiment_config_dict: dict
    ) -> None:
        expected_keys = {
            "system_type",
            "experiment_type",
            "general",
            "execution",
            "world",
            "logging",
            "system",
            "num_episodes_per_run",
            "agent_start_position",
            "parameter_path",
            "parameter_values",
        }
        assert set(experiment_config_dict.keys()) == expected_keys

    def test_experiment_config_system_type(
        self, experiment_config_dict: dict
    ) -> None:
        assert experiment_config_dict["system_type"] == "system_a"

    def test_experiment_config_system_matches(
        self,
        experiment_config_dict: dict,
        system_a_config_dict: dict,
    ) -> None:
        assert experiment_config_dict["system"] == system_a_config_dict


# ---------------------------------------------------------------------------
# 3. Assertion helper tests
# ---------------------------------------------------------------------------


class TestAssertionHelpers:
    def test_normalized_metric_zero(self) -> None:
        assert_normalized_metric(0.0)

    def test_normalized_metric_one(self) -> None:
        assert_normalized_metric(1.0)

    def test_normalized_metric_mid(self) -> None:
        assert_normalized_metric(0.5)

    def test_normalized_metric_below_range(self) -> None:
        with pytest.raises(AssertionError):
            assert_normalized_metric(-0.1)

    def test_normalized_metric_above_range(self) -> None:
        with pytest.raises(AssertionError):
            assert_normalized_metric(1.1)

    def test_dict_has_keys_present(self) -> None:
        assert_dict_has_keys({"a": 1, "b": 2}, "a", "b")

    def test_dict_has_keys_missing(self) -> None:
        with pytest.raises(AssertionError):
            assert_dict_has_keys({"a": 1}, "b")

    def test_dict_has_keys_partial_missing(self) -> None:
        with pytest.raises(AssertionError):
            assert_dict_has_keys({"a": 1}, "a", "b")


# ---------------------------------------------------------------------------
# 4. Constants self-consistency tests
# ---------------------------------------------------------------------------


class TestConstants:
    def test_initial_energy_positive(self) -> None:
        assert DEFAULT_INITIAL_ENERGY > 0

    def test_initial_energy_within_max(self) -> None:
        assert DEFAULT_INITIAL_ENERGY <= DEFAULT_MAX_ENERGY

    def test_grid_dimensions_positive(self) -> None:
        assert DEFAULT_GRID_WIDTH > 0
        assert DEFAULT_GRID_HEIGHT > 0

    def test_max_steps_positive(self) -> None:
        assert DEFAULT_MAX_STEPS > 0

    def test_temperature_positive(self) -> None:
        assert DEFAULT_TEMPERATURE > 0
