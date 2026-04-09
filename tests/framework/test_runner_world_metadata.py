"""Integration tests: world_metadata wiring for non-grid_2d worlds (WP-V.0.3)."""

from __future__ import annotations

from typing import Any

import pytest

from axis.framework.registry import create_system
from axis.framework.runner import run_episode, setup_episode
from axis.sdk.position import Position
from axis.sdk.trace import BaseEpisodeTrace
from axis.sdk.world_types import BaseWorldConfig
from tests.builders.system_config_builder import SystemAConfigBuilder


def _run_episode_with_world(
    world_type: str,
    max_steps: int = 5,
    seed: int = 42,
    **world_extras: Any,
) -> BaseEpisodeTrace:
    """Run a short System A episode on the given world type."""
    cfg = SystemAConfigBuilder().build()
    system = create_system("system_a", cfg)
    wc = BaseWorldConfig(world_type=world_type, **world_extras)
    world, registry = setup_episode(
        system, wc, Position(x=0, y=0), seed=seed,
    )
    return run_episode(
        system, world, registry,
        max_steps=max_steps, seed=seed, world_config=wc,
    )


class TestSignalLandscapeWorldData:
    """Signal landscape world_data appears in step traces."""

    def test_world_data_contains_hotspots(self) -> None:
        trace = _run_episode_with_world(
            "signal_landscape", grid_width=5, grid_height=5,
            num_hotspots=2,
        )
        for step in trace.steps:
            assert "hotspots" in step.world_data
            assert len(step.world_data["hotspots"]) == 2

    def test_hotspot_keys(self) -> None:
        trace = _run_episode_with_world(
            "signal_landscape", grid_width=5, grid_height=5,
            num_hotspots=1,
        )
        hotspot = trace.steps[0].world_data["hotspots"][0]
        assert set(hotspot.keys()) == {"cx", "cy", "radius", "intensity"}

    def test_episode_world_type(self) -> None:
        trace = _run_episode_with_world(
            "signal_landscape", grid_width=5, grid_height=5,
        )
        assert trace.world_type == "signal_landscape"


class TestToroidalWorldData:
    """Toroidal world_data appears in step traces."""

    def test_world_data_is_topology(self) -> None:
        trace = _run_episode_with_world(
            "toroidal", grid_width=5, grid_height=5,
        )
        for step in trace.steps:
            assert step.world_data == {"topology": "toroidal"}

    def test_episode_world_type(self) -> None:
        trace = _run_episode_with_world(
            "toroidal", grid_width=5, grid_height=5,
        )
        assert trace.world_type == "toroidal"
