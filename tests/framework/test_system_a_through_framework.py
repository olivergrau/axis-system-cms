"""System A through the framework pipeline -- capstone tests (WP-3.6).

These tests verify that running System A through the full framework
(registry -> RunExecutor -> runner) produces correct results.
"""

from __future__ import annotations

from axis.framework.config import (
    ExperimentConfig,
    ExperimentType,
    ExecutionConfig,
    GeneralConfig,
    LoggingConfig,
)
from axis.framework.experiment import ExperimentExecutor, ExperimentResult
from axis.framework.persistence import ExperimentRepository, ExperimentStatus
from axis.framework.registry import create_system, registered_system_types
from axis.framework.run import RunConfig, RunExecutor, RunResult
from axis.framework.runner import run_episode, setup_episode
from axis.sdk.position import Position
from axis.sdk.trace import BaseEpisodeTrace
from axis.sdk.world_types import BaseWorldConfig
from tests.builders.system_config_builder import SystemAConfigBuilder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _system_a_experiment_config(
    *,
    max_steps: int = 10,
    num_episodes: int = 2,
    seed: int = 42,
    system_overrides: dict | None = None,
) -> ExperimentConfig:
    builder = SystemAConfigBuilder()
    system_dict = system_overrides or builder.build()
    return ExperimentConfig(
        system_type="system_a",
        experiment_type=ExperimentType.SINGLE_RUN,
        general=GeneralConfig(seed=seed),
        execution=ExecutionConfig(max_steps=max_steps),
        world=BaseWorldConfig(grid_width=5, grid_height=5),
        logging=LoggingConfig(enabled=False),
        system=system_dict,
        num_episodes_per_run=num_episodes,
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestSystemARegistered:
    def test_system_a_registered(self) -> None:
        assert "system_a" in registered_system_types()

    def test_create_system_a(self) -> None:
        system = create_system("system_a", SystemAConfigBuilder().build())
        assert system.system_type() == "system_a"


# ---------------------------------------------------------------------------
# Through runner
# ---------------------------------------------------------------------------


class TestSystemAViaRunner:
    def test_run_episode(self) -> None:
        system = create_system("system_a", SystemAConfigBuilder().build())
        world, registry = setup_episode(
            system,
            BaseWorldConfig(grid_width=5, grid_height=5),
            Position(x=0, y=0),
            seed=42,
        )
        trace = run_episode(
            system, world, registry, max_steps=10, seed=42,
        )
        assert isinstance(trace, BaseEpisodeTrace)
        assert trace.system_type == "system_a"
        assert trace.total_steps > 0


# ---------------------------------------------------------------------------
# Through executor
# ---------------------------------------------------------------------------


class TestSystemAViaExecutor:
    def test_run_executor(self) -> None:
        from axis.framework.config import FrameworkConfig

        config = RunConfig(
            system_type="system_a",
            system_config=SystemAConfigBuilder().build(),
            framework_config=FrameworkConfig(
                general=GeneralConfig(seed=42),
                execution=ExecutionConfig(max_steps=10),
                world=BaseWorldConfig(grid_width=5, grid_height=5),
                logging=LoggingConfig(enabled=False),
            ),
            num_episodes=2,
            base_seed=42,
        )
        result = RunExecutor().execute(config)
        assert isinstance(result, RunResult)
        assert result.num_episodes == 2


# ---------------------------------------------------------------------------
# Behavioral equivalence via framework pipeline
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# Full experiment
# ---------------------------------------------------------------------------


class TestSystemAExperiment:
    def test_single_run(self) -> None:
        config = _system_a_experiment_config()
        result = ExperimentExecutor().execute(config)
        assert isinstance(result, ExperimentResult)
        assert result.summary.num_runs == 1
        assert len(result.run_results) == 1
        assert result.run_results[0].num_episodes == 2

    def test_ofat_temperature(self) -> None:
        config = ExperimentConfig(
            system_type="system_a",
            experiment_type=ExperimentType.OFAT,
            general=GeneralConfig(seed=42),
            execution=ExecutionConfig(max_steps=10),
            world=BaseWorldConfig(grid_width=5, grid_height=5),
            logging=LoggingConfig(enabled=False),
            system=SystemAConfigBuilder().build(),
            num_episodes_per_run=2,
            parameter_path="system.policy.temperature",
            parameter_values=(0.5, 1.0, 2.0),
        )
        result = ExperimentExecutor().execute(config)
        assert result.summary.num_runs == 3
        # Each run should have different temperature applied
        for i, entry in enumerate(result.summary.run_entries):
            expected = f"system.policy.temperature={[0.5, 1.0, 2.0][i]}"
            assert entry.variation_description == expected
