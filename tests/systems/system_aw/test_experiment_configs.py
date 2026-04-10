"""WP-13 experiment config validation tests."""

from __future__ import annotations

from pathlib import Path

import yaml
import pytest

from axis.framework.config import (
    ExecutionConfig,
    FrameworkConfig,
    GeneralConfig,
)
from axis.framework.run import RunConfig, RunExecutor
from axis.sdk.world_types import BaseWorldConfig
from axis.systems.system_aw.config import SystemAWConfig

CONFIGS_DIR = Path(__file__).resolve().parents[3] / "experiments" / "configs"


def _load_yaml(name: str) -> dict:
    path = CONFIGS_DIR / name
    with open(path) as f:
        return yaml.safe_load(f)


class TestConfigParsing:
    """Verify YAML configs parse into valid SystemAWConfig objects."""

    def test_baseline_config_parses(self) -> None:
        data = _load_yaml("system-aw-baseline.yaml")
        config = SystemAWConfig(**data["system"])
        assert config.curiosity.base_curiosity == 1.0
        assert config.arbitration.gating_sharpness == 2.0

    def test_sweep_config_parses(self) -> None:
        data = _load_yaml("system-aw-curiosity-sweep.yaml")
        config = SystemAWConfig(**data["system"])
        assert data["parameter_path"] == "system.curiosity.base_curiosity"
        assert data["parameter_values"] == [0.0, 0.25, 0.5, 0.75, 1.0]
        assert len(data["parameter_values"]) == 5

    def test_exploration_config_parses(self) -> None:
        data = _load_yaml("system-aw-exploration-demo.yaml")
        config = SystemAWConfig(**data["system"])
        assert config.curiosity.spatial_sensory_balance == 0.7
        assert config.arbitration.curiosity_weight_base == 1.5
        assert config.arbitration.gating_sharpness == 3.0


class TestConfigExecution:
    """Integration: configs produce valid runs."""

    def test_baseline_runs_to_completion(self) -> None:
        data = _load_yaml("system-aw-baseline.yaml")
        framework_config = FrameworkConfig(
            general=GeneralConfig(seed=data["general"]["seed"]),
            execution=ExecutionConfig(max_steps=10),  # short for test
            world=BaseWorldConfig(
                world_type=data["world"]["world_type"],
                grid_width=data["world"]["grid_width"],
                grid_height=data["world"]["grid_height"],
            ),
        )
        run_config = RunConfig(
            system_type=data["system_type"],
            system_config=data["system"],
            framework_config=framework_config,
            num_episodes=1,
            base_seed=42,
        )
        executor = RunExecutor()
        result = executor.execute(run_config)
        assert result.num_episodes == 1
        assert len(result.episode_traces) == 1

    def test_sweep_produces_multiple_runs(self) -> None:
        """Sweep has 5 parameter values, each producing a valid config."""
        data = _load_yaml("system-aw-curiosity-sweep.yaml")
        values = data["parameter_values"]
        assert len(values) == 5

        # Verify each value produces a valid config
        for val in values:
            system_cfg = dict(data["system"])
            system_cfg["curiosity"] = dict(system_cfg["curiosity"])
            system_cfg["curiosity"]["base_curiosity"] = val
            config = SystemAWConfig(**system_cfg)
            assert config.curiosity.base_curiosity == val
