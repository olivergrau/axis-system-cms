from __future__ import annotations

import pytest

from axis.systems.system_cw.config import SystemCWConfig
from tests.builders.system_cw_config_builder import SystemCWConfigBuilder


def test_system_cw_config_parses_defaults() -> None:
    cfg = SystemCWConfig(**SystemCWConfigBuilder().build())
    assert cfg.prediction.shared.context_cardinality == 64
    assert cfg.prediction.outcomes.nonmove_curiosity_penalty == pytest.approx(0.2)
    assert len(cfg.prediction.shared.positive_weights) == 10
    assert len(cfg.prediction.shared.negative_weights) == 10


def test_system_cw_config_rejects_bad_weight_length() -> None:
    bad = SystemCWConfigBuilder().build()
    bad["prediction"]["shared"]["positive_weights"] = [1.0]
    with pytest.raises(ValueError):
        SystemCWConfig(**bad)
