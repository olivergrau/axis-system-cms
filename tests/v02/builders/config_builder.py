"""Fluent builder for FrameworkConfig instances."""

from __future__ import annotations

from axis.framework.config import (
    ExecutionConfig,
    FrameworkConfig,
    GeneralConfig,
    LoggingConfig,
)
from axis.sdk.world_types import BaseWorldConfig
from tests.v02.constants import (
    DEFAULT_GRID_HEIGHT,
    DEFAULT_GRID_WIDTH,
    DEFAULT_MAX_STEPS,
    DEFAULT_OBSTACLE_DENSITY,
    DEFAULT_SEED,
)


class FrameworkConfigBuilder:
    """Fluent builder for FrameworkConfig instances.

    Produces a typed FrameworkConfig with sensible defaults
    matching the v0.1.0 test scenario constants.
    """

    def __init__(self) -> None:
        self._seed = DEFAULT_SEED
        self._max_steps = DEFAULT_MAX_STEPS
        self._grid_width = DEFAULT_GRID_WIDTH
        self._grid_height = DEFAULT_GRID_HEIGHT
        self._obstacle_density = DEFAULT_OBSTACLE_DENSITY
        self._logging_enabled = False

    def with_seed(self, seed: int) -> FrameworkConfigBuilder:
        self._seed = seed
        return self

    def with_max_steps(self, max_steps: int) -> FrameworkConfigBuilder:
        self._max_steps = max_steps
        return self

    def with_world_size(self, width: int, height: int) -> FrameworkConfigBuilder:
        self._grid_width = width
        self._grid_height = height
        return self

    def with_obstacle_density(self, density: float) -> FrameworkConfigBuilder:
        self._obstacle_density = density
        return self

    def build(self) -> FrameworkConfig:
        return FrameworkConfig(
            general=GeneralConfig(seed=self._seed),
            execution=ExecutionConfig(max_steps=self._max_steps),
            world=BaseWorldConfig(
                grid_width=self._grid_width,
                grid_height=self._grid_height,
                obstacle_density=self._obstacle_density,
            ),
            logging=LoggingConfig(enabled=self._logging_enabled),
        )
