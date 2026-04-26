from __future__ import annotations

from axis.framework.comparison.extensions import registered_extensions
from axis.framework.metrics.extensions import registered_metric_extensions
from axis.framework.registry import create_system, registered_system_types
from axis.systems.system_cw import register
from axis.systems.system_cw.system import SystemCW
from tests.builders.system_cw_config_builder import SystemCWConfigBuilder


def test_register_adds_system_cw() -> None:
    register()
    assert "system_cw" in registered_system_types()
    assert "system_cw" in registered_metric_extensions()
    assert "system_cw" in registered_extensions()


def test_factory_creates_system_cw() -> None:
    register()
    system = create_system("system_cw", SystemCWConfigBuilder().build())
    assert isinstance(system, SystemCW)
