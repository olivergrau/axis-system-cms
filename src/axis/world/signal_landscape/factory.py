"""Signal landscape factory: create_signal_landscape and helpers."""

from __future__ import annotations

import numpy as np

from axis.sdk.position import Position
from axis.sdk.world_types import BaseWorldConfig
from axis.world.signal_landscape.config import SignalLandscapeConfig
from axis.world.signal_landscape.dynamics import Hotspot, recompute_signals
from axis.world.signal_landscape.model import SignalCell, SignalCellType, SignalLandscapeWorld


def _parse_signal_config(config: BaseWorldConfig) -> SignalLandscapeConfig:
    """Extract and validate signal landscape fields from BaseWorldConfig extras."""
    extra_data = (
        {k: v for k, v in config.__pydantic_extra__.items()}
        if config.__pydantic_extra__
        else {}
    )
    return SignalLandscapeConfig(**extra_data)


def create_signal_landscape(
    config: BaseWorldConfig,
    agent_position: Position,
    seed: int | None = None,
) -> SignalLandscapeWorld:
    """Create a SignalLandscapeWorld from configuration."""
    sc = _parse_signal_config(config)
    rng = np.random.default_rng(seed)

    # Build empty grid
    empty_cell = SignalCell(
        cell_type=SignalCellType.EMPTY, resource_value=0.0)
    grid: list[list[SignalCell]] = [
        [empty_cell for _ in range(sc.grid_width)]
        for _ in range(sc.grid_height)
    ]

    # Place obstacles
    if sc.obstacle_density > 0:
        _apply_obstacles(grid, sc, agent_position, rng)

    # Generate hotspot positions
    hotspots: list[Hotspot] = []
    for _ in range(sc.num_hotspots):
        cx = float(rng.uniform(0, sc.grid_width))
        cy = float(rng.uniform(0, sc.grid_height))
        hotspots.append(
            Hotspot(cx, cy, sc.hotspot_radius, sc.signal_intensity))

    # Build world then compute initial signal field
    world = SignalLandscapeWorld(
        grid=grid,
        agent_position=agent_position,
        hotspots=hotspots,
        drift_speed=sc.drift_speed,
        decay_rate=sc.decay_rate,
        rng=rng,
    )
    recompute_signals(grid, hotspots, sc.grid_width,
                      sc.grid_height, sc.decay_rate)
    return world


def _apply_obstacles(
    grid: list[list[SignalCell]],
    config: SignalLandscapeConfig,
    agent_position: Position,
    rng: np.random.Generator,
) -> None:
    """Place obstacles deterministically, never on the agent start position."""
    obstacle_cell = SignalCell(
        cell_type=SignalCellType.OBSTACLE, resource_value=0.0)

    candidates: list[tuple[int, int]] = []
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell.is_traversable and (x, y) != (agent_position.x, agent_position.y):
                candidates.append((x, y))

    n_obstacles = round(config.obstacle_density * len(candidates))
    if n_obstacles == 0:
        return

    indices = rng.permutation(len(candidates))
    for idx in indices[:n_obstacles]:
        x, y = candidates[idx]
        grid[y][x] = obstacle_cell
