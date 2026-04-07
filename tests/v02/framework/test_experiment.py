"""Tests for the experiment executor (WP-3.3)."""

from __future__ import annotations

from typing import Any

import pytest

from axis.framework.config import (
    ExperimentConfig,
    ExperimentType,
    ExecutionConfig,
    GeneralConfig,
    LoggingConfig,
)
from axis.framework.experiment import (
    ExperimentExecutor,
    ExperimentResult,
    resolve_run_configs,
    variation_description,
)
from axis.framework.run import RunConfig, RunExecutor
from axis.sdk.world_types import BaseWorldConfig
from tests.v02.builders.system_config_builder import SystemAConfigBuilder
from tests.v02.constants import (
    DEFAULT_GRID_HEIGHT,
    DEFAULT_GRID_WIDTH,
    DEFAULT_SEED,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _default_system_config() -> dict[str, Any]:
    return SystemAConfigBuilder().build()


def _single_run_config(
    *,
    num_episodes: int = 2,
    max_steps: int = 30,
    seed: int = DEFAULT_SEED,
) -> ExperimentConfig:
    return ExperimentConfig(
        system_type="system_a",
        experiment_type=ExperimentType.SINGLE_RUN,
        general=GeneralConfig(seed=seed),
        execution=ExecutionConfig(max_steps=max_steps),
        world=BaseWorldConfig(
            grid_width=DEFAULT_GRID_WIDTH,
            grid_height=DEFAULT_GRID_HEIGHT,
        ),
        logging=LoggingConfig(enabled=False),
        system=_default_system_config(),
        num_episodes_per_run=num_episodes,
    )


def _ofat_config(
    *,
    parameter_path: str = "system.policy.temperature",
    parameter_values: tuple[Any, ...] = (0.5, 1.0, 2.0),
    num_episodes: int = 2,
    max_steps: int = 30,
    seed: int = DEFAULT_SEED,
) -> ExperimentConfig:
    return ExperimentConfig(
        system_type="system_a",
        experiment_type=ExperimentType.OFAT,
        general=GeneralConfig(seed=seed),
        execution=ExecutionConfig(max_steps=max_steps),
        world=BaseWorldConfig(
            grid_width=DEFAULT_GRID_WIDTH,
            grid_height=DEFAULT_GRID_HEIGHT,
        ),
        logging=LoggingConfig(enabled=False),
        system=_default_system_config(),
        num_episodes_per_run=num_episodes,
        parameter_path=parameter_path,
        parameter_values=parameter_values,
    )


# ---------------------------------------------------------------------------
# resolve_run_configs tests
# ---------------------------------------------------------------------------


class TestResolveRunConfigs:
    """Config resolution for SINGLE_RUN and OFAT."""

    def test_resolve_single_run(self) -> None:
        configs = resolve_run_configs(_single_run_config())
        assert len(configs) == 1
        assert isinstance(configs[0], RunConfig)

    def test_resolve_ofat(self) -> None:
        configs = resolve_run_configs(_ofat_config())
        assert len(configs) == 3

    def test_ofat_framework_path(self) -> None:
        cfg = _ofat_config(
            parameter_path="framework.execution.max_steps",
            parameter_values=(10, 20, 30),
        )
        configs = resolve_run_configs(cfg)
        assert configs[0].framework_config.execution.max_steps == 10
        assert configs[1].framework_config.execution.max_steps == 20
        assert configs[2].framework_config.execution.max_steps == 30

    def test_ofat_system_path(self) -> None:
        cfg = _ofat_config(
            parameter_path="system.policy.temperature",
            parameter_values=(0.5, 2.0),
        )
        configs = resolve_run_configs(cfg)
        assert configs[0].system_config["policy"]["temperature"] == 0.5
        assert configs[1].system_config["policy"]["temperature"] == 2.0

    def test_ofat_run_ids(self) -> None:
        configs = resolve_run_configs(_ofat_config())
        assert configs[0].run_id == "run-0000"
        assert configs[1].run_id == "run-0001"
        assert configs[2].run_id == "run-0002"

    def test_ofat_seed_spacing(self) -> None:
        cfg = _ofat_config(seed=100)
        configs = resolve_run_configs(cfg)
        assert configs[0].base_seed == 100
        assert configs[1].base_seed == 1100
        assert configs[2].base_seed == 2100


# ---------------------------------------------------------------------------
# variation_description tests
# ---------------------------------------------------------------------------


class TestVariationDescription:
    """Human-readable variation labels."""

    def test_single_run(self) -> None:
        cfg = _single_run_config()
        assert variation_description(cfg, 0) == "baseline"

    def test_ofat(self) -> None:
        cfg = _ofat_config(
            parameter_path="system.policy.temperature",
            parameter_values=(0.5, 1.0, 2.0),
        )
        assert variation_description(cfg, 1) == "system.policy.temperature=1.0"


# ---------------------------------------------------------------------------
# ExperimentExecutor tests
# ---------------------------------------------------------------------------


class TestExperimentExecutor:
    """Full experiment execution."""

    def test_single_run_execution(self) -> None:
        executor = ExperimentExecutor()
        result = executor.execute(_single_run_config())
        assert isinstance(result, ExperimentResult)

    def test_ofat_execution(self) -> None:
        cfg = _ofat_config(parameter_values=(0.5, 2.0), num_episodes=1)
        executor = ExperimentExecutor()
        result = executor.execute(cfg)
        assert len(result.run_results) == 2

    def test_result_structure(self) -> None:
        executor = ExperimentExecutor()
        result = executor.execute(_single_run_config())
        assert result.experiment_config is not None
        assert result.run_results is not None
        assert result.summary is not None

    def test_summary_num_runs(self) -> None:
        cfg = _ofat_config(parameter_values=(0.5, 1.0), num_episodes=1)
        executor = ExperimentExecutor()
        result = executor.execute(cfg)
        assert result.summary.num_runs == 2

    def test_summary_deltas_ofat(self) -> None:
        cfg = _ofat_config(parameter_values=(0.5, 2.0), num_episodes=1)
        executor = ExperimentExecutor()
        result = executor.execute(cfg)
        # First entry (baseline) should have delta = 0
        entry0 = result.summary.run_entries[0]
        assert entry0.delta_mean_steps == 0.0
        assert entry0.delta_mean_final_vitality == 0.0
        assert entry0.delta_death_rate == 0.0
        # Second entry should have non-None deltas
        entry1 = result.summary.run_entries[1]
        assert entry1.delta_mean_steps is not None
        assert entry1.delta_mean_final_vitality is not None

    def test_summary_no_deltas_single(self) -> None:
        executor = ExperimentExecutor()
        result = executor.execute(_single_run_config())
        entry = result.summary.run_entries[0]
        assert entry.delta_mean_steps is None
        assert entry.delta_mean_final_vitality is None
        assert entry.delta_death_rate is None
