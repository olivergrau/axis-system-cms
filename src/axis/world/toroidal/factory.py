"""Toroidal world factory: create_toroidal_world and helpers."""

from __future__ import annotations

import numpy as np

from axis.sdk.position import Position
from axis.sdk.world_types import BaseWorldConfig
from axis.world.grid_2d.eligibility import (
    apply_clustered_eligibility,
    apply_sparse_eligibility,
)
from axis.world.grid_2d.model import Cell, CellType, RegenerationMode
from axis.world.toroidal.config import ToroidalWorldConfig
from axis.world.toroidal.model import ToroidalWorld


def _parse_toroidal_config(config: BaseWorldConfig) -> ToroidalWorldConfig:
    """Extract and validate toroidal fields from BaseWorldConfig extras."""
    extra_data = (
        {k: v for k, v in config.__pydantic_extra__.items()}
        if config.__pydantic_extra__
        else {}
    )
    return ToroidalWorldConfig(**extra_data)


def create_toroidal_world(
    config: BaseWorldConfig,
    agent_position: Position,
    seed: int | None = None,
) -> ToroidalWorld:
    """Create a toroidal grid world from configuration."""
    tc = _parse_toroidal_config(config)

    empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    grid: list[list[Cell]] = [
        [empty for _ in range(tc.grid_width)]
        for _ in range(tc.grid_height)
    ]

    # Place obstacles
    if tc.obstacle_density > 0:
        _apply_obstacles(grid, tc, agent_position, seed)

    # Handle sparse regeneration eligibility
    regeneration_mode = RegenerationMode(tc.regeneration_mode)
    if regeneration_mode == RegenerationMode.SPARSE_FIXED_RATIO:
        apply_sparse_eligibility(grid, tc.regen_eligible_ratio, seed)
    elif regeneration_mode == RegenerationMode.CLUSTERED:
        apply_clustered_eligibility(
            grid, tc.regen_eligible_ratio, tc.num_clusters, seed,
        )

    return ToroidalWorld(
        grid=grid, agent_position=agent_position,
        regen_rate=tc.resource_regen_rate,
    )


def _apply_obstacles(
    grid: list[list[Cell]],
    config: ToroidalWorldConfig,
    agent_position: Position,
    seed: int | None,
) -> None:
    """Place obstacles deterministically, never on the agent start position."""
    obstacle = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)

    candidates: list[tuple[int, int]] = []
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell.is_traversable and (x, y) != (agent_position.x, agent_position.y):
                candidates.append((x, y))

    n_obstacles = round(config.obstacle_density * len(candidates))
    if n_obstacles == 0:
        return

    rng = np.random.default_rng(seed)
    indices = rng.permutation(len(candidates))
    for idx in indices[:n_obstacles]:
        x, y = candidates[idx]
        grid[y][x] = obstacle
