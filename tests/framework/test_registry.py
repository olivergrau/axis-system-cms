"""Tests for the system registry (WP-3.1)."""

from __future__ import annotations

from typing import Any

import pytest

from axis.framework.registry import (
    SystemFactory,
    _SYSTEM_REGISTRY,
    create_system,
    get_system_factory,
    register_system,
    registered_system_types,
)
from axis.sdk.actions import BASE_ACTIONS
from axis.sdk.interfaces import SystemInterface
from tests.builders.system_config_builder import SystemAConfigBuilder


def _default_config() -> dict[str, Any]:
    """Build a default System A config dict."""
    return SystemAConfigBuilder().build()


# ── Auto-registration ───────────────────────────────────────────────


def test_system_a_auto_registered() -> None:
    """system_a is registered on import."""
    assert "system_a" in registered_system_types()


# ── create_system ────────────────────────────────────────────────────


def test_create_system_a() -> None:
    """create_system returns a valid SystemInterface instance."""
    system = create_system("system_a", _default_config())
    assert isinstance(system, SystemInterface)


def test_created_system_type() -> None:
    """Created system reports correct type."""
    system = create_system("system_a", _default_config())
    assert system.system_type() == "system_a"


def test_created_system_action_space() -> None:
    """Created system action space includes base actions + consume."""
    system = create_system("system_a", _default_config())
    actions = system.action_space()
    for base in BASE_ACTIONS:
        assert base in actions
    assert "consume" in actions


# ── Error handling ───────────────────────────────────────────────────


def test_unknown_system_type_raises() -> None:
    """get_system_factory raises KeyError for unknown type."""
    with pytest.raises(KeyError):
        get_system_factory("nonexistent")


def test_unknown_system_error_message() -> None:
    """Error message includes available types."""
    with pytest.raises(KeyError, match="system_a"):
        get_system_factory("nonexistent")


def test_duplicate_registration_raises() -> None:
    """Registering the same type twice raises ValueError."""
    with pytest.raises(ValueError, match="already registered"):
        register_system("system_a", lambda cfg: None)  # type: ignore[arg-type]


# ── Custom registration ─────────────────────────────────────────────


def test_register_custom_system() -> None:
    """Register a mock factory, then create_system returns its output."""
    sentinel = object()

    def mock_factory(config: dict[str, Any]) -> Any:
        return sentinel

    type_name = "_test_custom_system"
    try:
        register_system(type_name, mock_factory)  # type: ignore[arg-type]
        result = create_system(type_name, {})
        assert result is sentinel
    finally:
        _SYSTEM_REGISTRY.pop(type_name, None)


def test_registered_system_types_sorted() -> None:
    """registered_system_types returns a sorted tuple."""
    types = registered_system_types()
    assert isinstance(types, tuple)
    assert types == tuple(sorted(types))


def test_factory_receives_config() -> None:
    """Factory function is called with the config dict."""
    received: list[dict[str, Any]] = []

    def capturing_factory(config: dict[str, Any]) -> Any:
        received.append(config)
        return object()

    type_name = "_test_capture_config"
    test_config = {"key": "value"}
    try:
        register_system(type_name, capturing_factory)  # type: ignore[arg-type]
        create_system(type_name, test_config)
        assert len(received) == 1
        assert received[0] is test_config
    finally:
        _SYSTEM_REGISTRY.pop(type_name, None)


# ── action_handlers ─────────────────────────────────────────────────


def test_action_handlers_system_a() -> None:
    """System A action_handlers returns consume handler."""
    system = create_system("system_a", _default_config())
    handlers = system.action_handlers()
    assert "consume" in handlers
    assert callable(handlers["consume"])


def test_action_handlers_contract() -> None:
    """All non-base actions in action_space have handlers."""
    system = create_system("system_a", _default_config())
    handlers = system.action_handlers()
    base = set(BASE_ACTIONS)
    custom_actions = set(system.action_space()) - base
    for action in custom_actions:
        assert action in handlers, f"Missing handler for '{action}'"
