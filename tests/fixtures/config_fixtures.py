"""Config fixtures using the builder pattern."""

from __future__ import annotations

import pytest

from axis.framework.config import ExperimentConfig, ExperimentType, FrameworkConfig
from axis.sdk.position import Position
from tests.builders.config_builder import FrameworkConfigBuilder
from tests.builders.system_config_builder import SystemAConfigBuilder


@pytest.fixture
def framework_config() -> FrameworkConfig:
    """Default framework config as typed FrameworkConfig."""
    return FrameworkConfigBuilder().build()


@pytest.fixture
def framework_config_dict(framework_config: FrameworkConfig) -> dict:
    """Default framework config as dict (backward compat)."""
    return framework_config.model_dump()


@pytest.fixture
def system_a_config_dict() -> dict:
    """Default System A config as dict."""
    return SystemAConfigBuilder().build()


@pytest.fixture
def experiment_config(
    framework_config: FrameworkConfig, system_a_config_dict: dict
) -> ExperimentConfig:
    """Complete experiment config as typed ExperimentConfig."""
    return ExperimentConfig(
        system_type="system_a",
        experiment_type=ExperimentType.SINGLE_RUN,
        general=framework_config.general,
        execution=framework_config.execution,
        world=framework_config.world,
        logging=framework_config.logging,
        system=system_a_config_dict,
        num_episodes_per_run=3,
        agent_start_position=Position(x=0, y=0),
    )


@pytest.fixture
def experiment_config_dict(experiment_config: ExperimentConfig) -> dict:
    """Complete experiment config as dict (backward compat)."""
    return experiment_config.model_dump()
