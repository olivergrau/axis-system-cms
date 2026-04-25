"""Tests for System A+W plugin registration."""

from __future__ import annotations

from axis.framework.metrics.extensions import registered_metric_extensions
from axis.framework.registry import registered_system_types
from axis.systems.system_aw import register


class TestRegistration:
    def test_register_adds_system_aw(self) -> None:
        register()
        assert "system_aw" in registered_system_types()
        assert "system_aw" in registered_metric_extensions()

    def test_double_registration_idempotent(self) -> None:
        register()
        register()
        assert "system_aw" in registered_system_types()
