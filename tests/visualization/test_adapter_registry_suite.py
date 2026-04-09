"""Tests for WP-V.5.1: Adapter Registry Suite.

Integration tests for registry wiring with real adapter factories.
"""

from __future__ import annotations

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

from axis.world.grid_2d.visualization import (
    Grid2DWorldVisualizationAdapter,
    _grid_2d_vis_factory,
)
from axis.world.toroidal.visualization import (
    ToroidalWorldVisualizationAdapter,
    _toroidal_vis_factory,
)
from axis.world.signal_landscape.visualization import (
    SignalLandscapeWorldVisualizationAdapter,
    _signal_landscape_vis_factory,
)
from axis.systems.system_a.visualization import _system_a_vis_factory
from axis.systems.system_b.visualization import _system_b_vis_factory


@pytest.fixture(autouse=True)
def _clean_and_reregister():
    """Clear registries and re-register all real adapter factories."""
    _clear_registries()
    register_world_visualization("grid_2d", _grid_2d_vis_factory)
    register_world_visualization("toroidal", _toroidal_vis_factory)
    register_world_visualization(
        "signal_landscape", _signal_landscape_vis_factory)
    register_system_visualization("system_a", _system_a_vis_factory)
    register_system_visualization("system_b", _system_b_vis_factory)
    yield
    # Re-register after each test so later tests in other modules
    # still find the adapters (import-time registration is a one-shot
    # side-effect that won't re-fire).
    _clear_registries()
    register_world_visualization("grid_2d", _grid_2d_vis_factory)
    register_world_visualization("toroidal", _toroidal_vis_factory)
    register_world_visualization(
        "signal_landscape", _signal_landscape_vis_factory)
    register_system_visualization("system_a", _system_a_vis_factory)
    register_system_visualization("system_b", _system_b_vis_factory)


class TestAdapterRegistrySuite:

    def test_all_world_adapters_registered(self) -> None:
        registered = registered_world_visualizations()
        assert "grid_2d" in registered
        assert "toroidal" in registered
        assert "signal_landscape" in registered

    def test_all_system_adapters_registered(self) -> None:
        registered = registered_system_visualizations()
        assert "system_a" in registered
        assert "system_b" in registered

    def test_resolve_grid2d_returns_correct_type(self) -> None:
        result = resolve_world_adapter("grid_2d", {})
        assert isinstance(result, Grid2DWorldVisualizationAdapter)

    def test_resolve_toroidal_returns_correct_type(self) -> None:
        result = resolve_world_adapter("toroidal", {})
        assert isinstance(result, ToroidalWorldVisualizationAdapter)

    def test_resolve_signal_landscape_returns_correct_type(self) -> None:
        result = resolve_world_adapter("signal_landscape", {})
        assert isinstance(result, SignalLandscapeWorldVisualizationAdapter)

    def test_resolve_unknown_world_falls_back_to_default(self) -> None:
        result = resolve_world_adapter("unknown_world_type", {})
        assert isinstance(result, DefaultWorldVisualizationAdapter)

    def test_resolve_unknown_system_falls_back_to_null(self) -> None:
        result = resolve_system_adapter("unknown_system_type")
        assert isinstance(result, NullSystemVisualizationAdapter)

    def test_world_factory_receives_world_config(self) -> None:
        _clear_registries()
        captured: list[dict] = []

        def probe(cfg):
            captured.append(cfg)
            return DefaultWorldVisualizationAdapter()

        register_world_visualization("probe", probe)
        resolve_world_adapter("probe", {"grid_width": 10})
        assert len(captured) == 1
        assert captured[0] == {"grid_width": 10}
