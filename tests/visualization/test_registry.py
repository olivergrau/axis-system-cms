"""Tests for WP-V.1.4: Visualization Registry."""

from __future__ import annotations

from typing import Any

import pytest

from axis.visualization.adapters.default_world import DefaultWorldVisualizationAdapter
from axis.visualization.adapters.null_system import NullSystemVisualizationAdapter
from axis.visualization.registry import (
    _clear_registries,
    register_system_visualization,
    register_world_visualization,
    registered_system_visualizations,
    registered_world_visualizations,
    resolve_system_adapter,
    resolve_world_adapter,
)


@pytest.fixture(autouse=True)
def _clean_registries() -> None:
    _clear_registries()


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestRegistration:

    def test_register_world_visualization(self) -> None:
        register_world_visualization("test_world", lambda cfg: None)
        assert "test_world" in registered_world_visualizations()

    def test_register_system_visualization(self) -> None:
        register_system_visualization("test_system", lambda: None)
        assert "test_system" in registered_system_visualizations()

    def test_register_world_duplicate_raises(self) -> None:
        register_world_visualization("dup", lambda cfg: None)
        with pytest.raises(ValueError, match="already registered"):
            register_world_visualization("dup", lambda cfg: None)

    def test_register_system_duplicate_raises(self) -> None:
        register_system_visualization("dup", lambda: None)
        with pytest.raises(ValueError, match="already registered"):
            register_system_visualization("dup", lambda: None)


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


class TestResolution:

    def test_resolve_world_adapter_registered(self) -> None:
        sentinel = object()
        register_world_visualization("custom", lambda cfg: sentinel)
        result = resolve_world_adapter("custom", {})
        assert result is sentinel

    def test_resolve_world_adapter_unknown_falls_back(self) -> None:
        result = resolve_world_adapter("unknown_world", {})
        assert isinstance(result, DefaultWorldVisualizationAdapter)

    def test_resolve_system_adapter_registered(self) -> None:
        sentinel = object()
        register_system_visualization("custom_sys", lambda: sentinel)
        result = resolve_system_adapter("custom_sys")
        assert result is sentinel

    def test_resolve_system_adapter_unknown_falls_back(self) -> None:
        result = resolve_system_adapter("unknown_system")
        assert isinstance(result, NullSystemVisualizationAdapter)


# ---------------------------------------------------------------------------
# Factory arguments
# ---------------------------------------------------------------------------


class TestFactoryArguments:

    def test_world_vis_factory_receives_world_config(self) -> None:
        captured: list[dict[str, Any]] = []
        register_world_visualization("probe", lambda cfg: captured.append(cfg))
        resolve_world_adapter("probe", {"grid_width": 10})
        assert len(captured) == 1
        assert captured[0] == {"grid_width": 10}

    def test_system_vis_factory_called_without_args(self) -> None:
        calls: list[bool] = []
        register_system_visualization("probe_sys", lambda: calls.append(True))
        resolve_system_adapter("probe_sys")
        assert len(calls) == 1


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------


class TestQuery:

    def test_registered_world_visualizations_empty(self) -> None:
        assert registered_world_visualizations() == ()

    def test_registered_world_visualizations_sorted(self) -> None:
        register_world_visualization("beta", lambda cfg: None)
        register_world_visualization("alpha", lambda cfg: None)
        assert registered_world_visualizations() == ("alpha", "beta")

    def test_registered_system_visualizations_sorted(self) -> None:
        register_system_visualization("sys_b", lambda: None)
        register_system_visualization("sys_a", lambda: None)
        assert registered_system_visualizations() == ("sys_a", "sys_b")


# ---------------------------------------------------------------------------
# Clear / Import
# ---------------------------------------------------------------------------


class TestClearAndImport:

    def test_clear_registries(self) -> None:
        register_world_visualization("w", lambda cfg: None)
        register_system_visualization("s", lambda: None)
        _clear_registries()
        assert registered_world_visualizations() == ()
        assert registered_system_visualizations() == ()

    def test_import_registry_functions(self) -> None:
        from axis.visualization.registry import (  # noqa: F401
            _clear_registries,
            register_system_visualization,
            register_world_visualization,
            registered_system_visualizations,
            registered_world_visualizations,
            resolve_system_adapter,
            resolve_world_adapter,
        )
