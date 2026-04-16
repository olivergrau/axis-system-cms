"""Experiment config validation tests for System C."""

from __future__ import annotations

from pathlib import Path

import yaml

from axis.systems.system_c.config import PredictionConfig, SystemCConfig

CONFIGS_DIR = Path(__file__).resolve().parents[3] / "experiments" / "configs"


def _load_yaml(name: str) -> dict:
    path = CONFIGS_DIR / name
    with open(path) as f:
        return yaml.safe_load(f)


class TestConfigParsing:
    """Verify YAML config parses into valid SystemCConfig."""

    def test_baseline_config_loads(self) -> None:
        data = _load_yaml("system-c-baseline.yaml")
        assert data["system_type"] == "system_c"

    def test_baseline_config_parses(self) -> None:
        data = _load_yaml("system-c-baseline.yaml")
        config = SystemCConfig(**data["system"])
        assert config.prediction.memory_learning_rate == 0.3
        assert config.prediction.negative_sensitivity == 2.0
        assert config.agent.initial_energy == 50.0

    def test_prediction_section_types(self) -> None:
        data = _load_yaml("system-c-baseline.yaml")
        config = SystemCConfig(**data["system"])
        assert isinstance(config.prediction, PredictionConfig)
        assert isinstance(config.prediction.positive_weights, tuple)
        assert len(config.prediction.positive_weights) == 5

    def test_config_round_trips(self) -> None:
        data = _load_yaml("system-c-baseline.yaml")
        config = SystemCConfig(**data["system"])
        # Round-trip through model_dump
        dumped = config.model_dump()
        config2 = SystemCConfig(**dumped)
        assert config2.prediction.memory_learning_rate == config.prediction.memory_learning_rate
        assert config2.prediction.negative_sensitivity == config.prediction.negative_sensitivity
