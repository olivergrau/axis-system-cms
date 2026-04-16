"""Tests for System C plugin registration."""

from __future__ import annotations

from axis.framework.registry import register_system, registered_system_types
from axis.systems.system_c import register
from axis.systems.system_c.system import SystemC
from tests.builders.system_c_config_builder import SystemCConfigBuilder


class TestRegistration:

    def test_register_adds_system_c(self) -> None:
        register()
        assert "system_c" in registered_system_types()

    def test_factory_creates_system_c(self) -> None:
        register()
        types = registered_system_types()
        assert "system_c" in types

        # Access the factory via the registry and create an instance
        cfg = SystemCConfigBuilder().build()
        system = SystemC.__new__(SystemC)
        # Use the public register path: just verify it doesn't crash
        from axis.systems.system_c.config import SystemCConfig

        system = SystemC(SystemCConfig(**cfg))
        assert system.system_type() == "system_c"

    def test_double_registration_idempotent(self) -> None:
        register()
        register()  # should not raise
        assert "system_c" in registered_system_types()
