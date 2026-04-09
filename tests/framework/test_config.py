"""Verification tests for WP-1.4: Framework Config Types."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from axis.framework.config import (
    ExperimentConfig,
    ExperimentType,
    ExecutionConfig,
    FrameworkConfig,
    GeneralConfig,
    LoggingConfig,
    extract_framework_config,
    get_config_value,
    parse_parameter_path,
    set_config_value,
)
from axis.sdk.position import Position
from axis.sdk.world_types import BaseWorldConfig
from tests.builders.config_builder import FrameworkConfigBuilder
from tests.constants import (
    DEFAULT_GRID_HEIGHT,
    DEFAULT_GRID_WIDTH,
    DEFAULT_MAX_STEPS,
    DEFAULT_OBSTACLE_DENSITY,
    DEFAULT_SEED,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_experiment_config(
    *,
    experiment_type: ExperimentType = ExperimentType.SINGLE_RUN,
    parameter_path: str | None = None,
    parameter_values: tuple | None = None,
    system: dict | None = None,
) -> ExperimentConfig:
    return ExperimentConfig(
        system_type="system_a",
        experiment_type=experiment_type,
        general=GeneralConfig(seed=42),
        execution=ExecutionConfig(max_steps=200),
        world=BaseWorldConfig(grid_width=10, grid_height=10),
        system=system or {"agent": {"initial_energy": 50.0}, "policy": {"temperature": 1.0}},
        num_episodes_per_run=3,
        parameter_path=parameter_path,
        parameter_values=parameter_values,
    )


# ---------------------------------------------------------------------------
# GeneralConfig
# ---------------------------------------------------------------------------


class TestGeneralConfig:
    def test_construction(self) -> None:
        config = GeneralConfig(seed=42)
        assert config.seed == 42

    def test_frozen(self) -> None:
        config = GeneralConfig(seed=42)
        with pytest.raises(ValidationError):
            config.seed = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ExecutionConfig
# ---------------------------------------------------------------------------


class TestExecutionConfig:
    def test_construction(self) -> None:
        config = ExecutionConfig(max_steps=200)
        assert config.max_steps == 200

    def test_max_steps_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            ExecutionConfig(max_steps=0)

    def test_frozen(self) -> None:
        config = ExecutionConfig(max_steps=200)
        with pytest.raises(ValidationError):
            config.max_steps = 500  # type: ignore[misc]


# ---------------------------------------------------------------------------
# LoggingConfig
# ---------------------------------------------------------------------------


class TestLoggingConfig:
    def test_default_construction(self) -> None:
        config = LoggingConfig()
        assert config.enabled is True
        assert config.console_enabled is True
        assert config.jsonl_enabled is False
        assert config.jsonl_path is None
        assert config.include_decision_trace is True
        assert config.include_transition_trace is True
        assert config.verbosity == "compact"

    def test_jsonl_with_path(self) -> None:
        config = LoggingConfig(jsonl_enabled=True, jsonl_path="/tmp/x.jsonl")
        assert config.jsonl_enabled is True
        assert config.jsonl_path == "/tmp/x.jsonl"

    def test_jsonl_without_path_raises(self) -> None:
        with pytest.raises(ValidationError):
            LoggingConfig(jsonl_enabled=True)

    def test_frozen(self) -> None:
        config = LoggingConfig()
        with pytest.raises(ValidationError):
            config.enabled = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# FrameworkConfig
# ---------------------------------------------------------------------------


class TestFrameworkConfig:
    def test_full_construction(self) -> None:
        config = FrameworkConfig(
            general=GeneralConfig(seed=42),
            execution=ExecutionConfig(max_steps=200),
            world=BaseWorldConfig(grid_width=10, grid_height=10),
            logging=LoggingConfig(enabled=False),
        )
        assert config.general.seed == 42
        assert config.execution.max_steps == 200
        assert config.world.grid_width == 10
        assert config.logging.enabled is False

    def test_logging_defaults(self) -> None:
        config = FrameworkConfig(
            general=GeneralConfig(seed=42),
            execution=ExecutionConfig(max_steps=200),
            world=BaseWorldConfig(grid_width=10, grid_height=10),
        )
        assert config.logging.enabled is True

    def test_frozen(self) -> None:
        config = FrameworkConfig(
            general=GeneralConfig(seed=42),
            execution=ExecutionConfig(max_steps=200),
            world=BaseWorldConfig(grid_width=10, grid_height=10),
        )
        with pytest.raises(ValidationError):
            config.general = GeneralConfig(seed=99)  # type: ignore[misc]


# ---------------------------------------------------------------------------
# extract_framework_config
# ---------------------------------------------------------------------------


class TestExtractFrameworkConfig:
    def test_extracts_matching_config(self) -> None:
        exp = _make_experiment_config()
        fw = extract_framework_config(exp)
        assert isinstance(fw, FrameworkConfig)
        assert fw.general == exp.general
        assert fw.execution == exp.execution
        assert fw.world == exp.world
        assert fw.logging == exp.logging


# ---------------------------------------------------------------------------
# ExperimentConfig (single_run)
# ---------------------------------------------------------------------------


class TestExperimentConfigSingleRun:
    def test_minimal_construction(self) -> None:
        config = _make_experiment_config()
        assert config.system_type == "system_a"
        assert config.experiment_type == ExperimentType.SINGLE_RUN
        assert config.parameter_path is None
        assert config.parameter_values is None

    def test_default_start_position(self) -> None:
        config = _make_experiment_config()
        assert config.agent_start_position == Position(x=0, y=0)

    def test_system_is_dict(self) -> None:
        config = _make_experiment_config()
        assert isinstance(config.system, dict)

    def test_parameter_path_provided_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_experiment_config(parameter_path="framework.execution.max_steps")

    def test_parameter_values_provided_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_experiment_config(parameter_values=(100, 200))


# ---------------------------------------------------------------------------
# ExperimentConfig (ofat)
# ---------------------------------------------------------------------------


class TestExperimentConfigOfat:
    def test_construction(self) -> None:
        config = _make_experiment_config(
            experiment_type=ExperimentType.OFAT,
            parameter_path="framework.execution.max_steps",
            parameter_values=(100, 200, 300),
        )
        assert config.experiment_type == ExperimentType.OFAT
        assert config.parameter_path == "framework.execution.max_steps"
        assert config.parameter_values == (100, 200, 300)

    def test_system_parameter_path(self) -> None:
        config = _make_experiment_config(
            experiment_type=ExperimentType.OFAT,
            parameter_path="system.policy.temperature",
            parameter_values=(0.5, 1.0, 2.0),
        )
        assert config.parameter_path == "system.policy.temperature"

    def test_missing_parameter_path_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_experiment_config(
                experiment_type=ExperimentType.OFAT,
                parameter_values=(100, 200),
            )

    def test_missing_parameter_values_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_experiment_config(
                experiment_type=ExperimentType.OFAT,
                parameter_path="framework.execution.max_steps",
            )

    def test_empty_parameter_values_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_experiment_config(
                experiment_type=ExperimentType.OFAT,
                parameter_path="framework.execution.max_steps",
                parameter_values=(),
            )


# ---------------------------------------------------------------------------
# parse_parameter_path
# ---------------------------------------------------------------------------


class TestParseParameterPath:
    def test_framework_path(self) -> None:
        assert parse_parameter_path("framework.execution.max_steps") == (
            "framework", "execution", "max_steps"
        )

    def test_system_path(self) -> None:
        assert parse_parameter_path("system.policy.temperature") == (
            "system", "policy", "temperature"
        )

    def test_invalid_domain_raises(self) -> None:
        with pytest.raises(ValueError, match="domain"):
            parse_parameter_path("invalid.a.b")

    def test_invalid_framework_section_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid framework section"):
            parse_parameter_path("framework.invalid.x")

    def test_too_few_segments_raises(self) -> None:
        with pytest.raises(ValueError, match="3 segments"):
            parse_parameter_path("a.b")

    def test_too_many_segments_raises(self) -> None:
        with pytest.raises(ValueError, match="3 segments"):
            parse_parameter_path("a.b.c.d")

    def test_all_framework_sections_valid(self) -> None:
        for section in ("general", "execution", "world", "logging"):
            domain, sec, field = parse_parameter_path(f"framework.{section}.x")
            assert domain == "framework"
            assert sec == section

    def test_system_section_any_name_accepted(self) -> None:
        domain, section, field = parse_parameter_path("system.custom_section.field")
        assert domain == "system"
        assert section == "custom_section"


# ---------------------------------------------------------------------------
# get_config_value
# ---------------------------------------------------------------------------


class TestGetConfigValue:
    def test_framework_execution_max_steps(self) -> None:
        config = _make_experiment_config()
        assert get_config_value(config, "framework.execution.max_steps") == 200

    def test_framework_general_seed(self) -> None:
        config = _make_experiment_config()
        assert get_config_value(config, "framework.general.seed") == 42

    def test_framework_world_grid_width(self) -> None:
        config = _make_experiment_config()
        assert get_config_value(config, "framework.world.grid_width") == 10

    def test_system_agent_initial_energy(self) -> None:
        config = _make_experiment_config()
        assert get_config_value(config, "system.agent.initial_energy") == 50.0

    def test_system_policy_temperature(self) -> None:
        config = _make_experiment_config()
        assert get_config_value(config, "system.policy.temperature") == 1.0

    def test_system_nonexistent_section_raises(self) -> None:
        config = _make_experiment_config()
        with pytest.raises(KeyError):
            get_config_value(config, "system.nonexistent.field")

    def test_framework_nonexistent_field_raises(self) -> None:
        config = _make_experiment_config()
        with pytest.raises(KeyError):
            get_config_value(config, "framework.execution.nonexistent")

    def test_system_nonexistent_field_raises(self) -> None:
        config = _make_experiment_config()
        with pytest.raises(KeyError):
            get_config_value(config, "system.agent.nonexistent")


# ---------------------------------------------------------------------------
# set_config_value
# ---------------------------------------------------------------------------


class TestSetConfigValue:
    def test_framework_execution_max_steps(self) -> None:
        config = _make_experiment_config()
        new_config = set_config_value(config, "framework.execution.max_steps", 500)
        assert new_config.execution.max_steps == 500
        # Original unchanged
        assert config.execution.max_steps == 200

    def test_framework_general_seed(self) -> None:
        config = _make_experiment_config()
        new_config = set_config_value(config, "framework.general.seed", 99)
        assert new_config.general.seed == 99
        assert config.general.seed == 42

    def test_system_policy_temperature(self) -> None:
        config = _make_experiment_config()
        new_config = set_config_value(config, "system.policy.temperature", 2.0)
        assert new_config.system["policy"]["temperature"] == 2.0
        # Original unchanged
        assert config.system["policy"]["temperature"] == 1.0

    def test_system_new_section_field(self) -> None:
        config = _make_experiment_config()
        new_config = set_config_value(config, "system.new_section.new_field", 42)
        assert new_config.system["new_section"]["new_field"] == 42
        assert "new_section" not in config.system

    def test_returns_new_instance(self) -> None:
        config = _make_experiment_config()
        new_config = set_config_value(config, "framework.general.seed", 99)
        assert new_config is not config


# ---------------------------------------------------------------------------
# Constants consistency with builder
# ---------------------------------------------------------------------------


class TestConstantsConsistency:
    def test_builder_defaults_match_constants(self) -> None:
        config = FrameworkConfigBuilder().build()
        assert config.general.seed == DEFAULT_SEED
        assert config.execution.max_steps == DEFAULT_MAX_STEPS
        assert config.world.grid_width == DEFAULT_GRID_WIDTH
        assert config.world.grid_height == DEFAULT_GRID_HEIGHT
        assert config.world.obstacle_density == DEFAULT_OBSTACLE_DENSITY


# ---------------------------------------------------------------------------
# Import verification
# ---------------------------------------------------------------------------


class TestImports:
    def test_import_from_framework_package(self) -> None:
        from axis.framework import (  # noqa: F401
            ExperimentConfig,
            ExperimentType,
            ExecutionConfig,
            FrameworkConfig,
            GeneralConfig,
            LoggingConfig,
            extract_framework_config,
            get_config_value,
            parse_parameter_path,
            set_config_value,
        )

    def test_import_from_config_module(self) -> None:
        from axis.framework.config import (  # noqa: F401
            ExperimentConfig,
            FrameworkConfig,
        )
