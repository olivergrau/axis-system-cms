from __future__ import annotations

from pathlib import Path

import yaml

from axis.systems.system_cw.config import SystemCWConfig


def test_system_cw_baseline_yaml_parses() -> None:
    path = Path("experiments/configs/system-cw-baseline.yaml")
    data = yaml.safe_load(path.read_text())
    assert data["system_type"] == "system_cw"
    cfg = SystemCWConfig(**data["system"])
    assert cfg.prediction.shared.context_cardinality == 64
