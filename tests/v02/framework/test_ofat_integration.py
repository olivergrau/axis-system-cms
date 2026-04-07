"""OFAT integration tests with end-to-end path resolution (WP-3.6)."""

from __future__ import annotations

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
    resolve_run_configs,
    variation_description,
)
from axis.framework.registry import _SYSTEM_REGISTRY, register_system
from axis.sdk.world_types import BaseWorldConfig
from tests.v02.framework.mock_system import MockSystem


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _mock_system_registered():
    def mock_factory(config):
        return MockSystem(config)

    if "mock" not in _SYSTEM_REGISTRY:
        register_system("mock", mock_factory)
    yield
    _SYSTEM_REGISTRY.pop("mock", None)


def _ofat_config(
    *, parameter_path: str, parameter_values: tuple, max_steps: int = 15
) -> ExperimentConfig:
    return ExperimentConfig(
        system_type="mock",
        experiment_type=ExperimentType.OFAT,
        general=GeneralConfig(seed=42),
        execution=ExecutionConfig(max_steps=max_steps),
        world=BaseWorldConfig(grid_width=5, grid_height=5),
        logging=LoggingConfig(enabled=False),
        system={"initial_energy": 10.0, "max_energy": 10.0},
        num_episodes_per_run=1,
        parameter_path=parameter_path,
        parameter_values=parameter_values,
    )


# ---------------------------------------------------------------------------
# OFAT framework path resolution
# ---------------------------------------------------------------------------


class TestOfatFrameworkPath:
    """OFAT with framework.execution.max_steps."""

    def test_run_count(self) -> None:
        config = _ofat_config(
            parameter_path="framework.execution.max_steps",
            parameter_values=(5, 10, 20),
        )
        run_configs = resolve_run_configs(config)
        assert len(run_configs) == 3

    def test_max_steps_varies(self) -> None:
        config = _ofat_config(
            parameter_path="framework.execution.max_steps",
            parameter_values=(3, 8, 15),
        )
        run_configs = resolve_run_configs(config)
        assert run_configs[0].framework_config.execution.max_steps == 3
        assert run_configs[1].framework_config.execution.max_steps == 8
        assert run_configs[2].framework_config.execution.max_steps == 15

    def test_different_step_counts_in_results(self) -> None:
        config = _ofat_config(
            parameter_path="framework.execution.max_steps",
            parameter_values=(3, 15),
        )
        result = ExperimentExecutor().execute(config)
        # With 3 max_steps, agent survives (energy 10 - 3 = 7)
        # With 15 max_steps, agent dies at step 10
        r0 = result.run_results[0]
        r1 = result.run_results[1]
        assert r0.summary.mean_steps < r1.summary.mean_steps


# ---------------------------------------------------------------------------
# OFAT system path resolution
# ---------------------------------------------------------------------------


class TestOfatSystemPath:
    """OFAT with system config parameter."""

    def test_system_parameter_varies(self) -> None:
        config = ExperimentConfig(
            system_type="mock",
            experiment_type=ExperimentType.OFAT,
            general=GeneralConfig(seed=42),
            execution=ExecutionConfig(max_steps=15),
            world=BaseWorldConfig(grid_width=5, grid_height=5),
            logging=LoggingConfig(enabled=False),
            system={
                "initial_energy": 10.0,
                "max_energy": 10.0,
                "options": {"param": 1},
            },
            num_episodes_per_run=1,
            parameter_path="system.options.param",
            parameter_values=(10, 20, 30),
        )
        run_configs = resolve_run_configs(config)
        assert run_configs[0].system_config["options"]["param"] == 10
        assert run_configs[1].system_config["options"]["param"] == 20
        assert run_configs[2].system_config["options"]["param"] == 30


# ---------------------------------------------------------------------------
# OFAT seed spacing
# ---------------------------------------------------------------------------


class TestOfatSeedSpacing:
    """Verify run seeds are spaced by 1000."""

    def test_seed_spacing(self) -> None:
        config = _ofat_config(
            parameter_path="framework.execution.max_steps",
            parameter_values=(5, 10, 15),
        )
        run_configs = resolve_run_configs(config)
        assert run_configs[0].base_seed == 42
        assert run_configs[1].base_seed == 1042
        assert run_configs[2].base_seed == 2042


# ---------------------------------------------------------------------------
# Variation descriptions
# ---------------------------------------------------------------------------


class TestOfatVariationDescriptions:
    """Correct variation descriptions in summary."""

    def test_variation_descriptions(self) -> None:
        config = _ofat_config(
            parameter_path="framework.execution.max_steps",
            parameter_values=(5, 10),
        )
        assert variation_description(config, 0) == "framework.execution.max_steps=5"
        assert variation_description(config, 1) == "framework.execution.max_steps=10"

    def test_descriptions_in_result(self) -> None:
        config = _ofat_config(
            parameter_path="framework.execution.max_steps",
            parameter_values=(5, 10),
        )
        result = ExperimentExecutor().execute(config)
        entries = result.summary.run_entries
        assert entries[0].variation_description == "framework.execution.max_steps=5"
        assert entries[1].variation_description == "framework.execution.max_steps=10"


# ---------------------------------------------------------------------------
# OFAT deltas
# ---------------------------------------------------------------------------


class TestOfatDeltas:
    """Delta values relative to first run."""

    def test_deltas_computed(self) -> None:
        config = _ofat_config(
            parameter_path="framework.execution.max_steps",
            parameter_values=(3, 15),
        )
        result = ExperimentExecutor().execute(config)
        entries = result.summary.run_entries
        # First run is baseline => deltas are 0
        assert entries[0].delta_mean_steps == pytest.approx(0.0)
        # Second run has different step count => delta is nonzero
        assert entries[1].delta_mean_steps is not None


# ---------------------------------------------------------------------------
# Invalid OFAT path
# ---------------------------------------------------------------------------


class TestOfatInvalidPath:
    """Bad OFAT paths rejected at config validation."""

    def test_invalid_path_rejected(self) -> None:
        with pytest.raises(ValueError):
            ExperimentConfig(
                system_type="mock",
                experiment_type=ExperimentType.OFAT,
                general=GeneralConfig(seed=42),
                execution=ExecutionConfig(max_steps=15),
                world=BaseWorldConfig(grid_width=5, grid_height=5),
                logging=LoggingConfig(enabled=False),
                system={"initial_energy": 10.0},
                num_episodes_per_run=1,
                parameter_path=None,  # Missing required for OFAT
                parameter_values=None,
            )

    def test_empty_values_rejected(self) -> None:
        with pytest.raises(ValueError):
            ExperimentConfig(
                system_type="mock",
                experiment_type=ExperimentType.OFAT,
                general=GeneralConfig(seed=42),
                execution=ExecutionConfig(max_steps=15),
                world=BaseWorldConfig(grid_width=5, grid_height=5),
                logging=LoggingConfig(enabled=False),
                system={"initial_energy": 10.0},
                num_episodes_per_run=1,
                parameter_path="framework.execution.max_steps",
                parameter_values=(),  # Empty
            )
