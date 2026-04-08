"""World factory: create_world and helpers."""

from __future__ import annotations

import numpy as np

from axis.sdk.position import Position
from axis.sdk.world_types import BaseWorldConfig
from axis.world.grid_2d.config import Grid2DWorldConfig
from axis.world.grid_2d.model import Cell, CellType, RegenerationMode, World


def _parse_grid_config(config: BaseWorldConfig) -> Grid2DWorldConfig:
    """Extract and validate Grid2D fields from BaseWorldConfig extras."""
    extra_data = {k: v for k, v in config.__pydantic_extra__.items(
    )} if config.__pydantic_extra__ else {}
    return Grid2DWorldConfig(**extra_data)


def create_world(
    config: BaseWorldConfig,
    agent_position: Position,
    grid: list[list[Cell]] | None = None,
    *,
    seed: int | None = None,
) -> World:
    """Create a World from configuration.

    If grid is None, creates a grid of EMPTY cells.
    If grid is provided, validates dimensions against config.

    Regeneration parameters are read from the world config.
    The world owns its dynamics (regeneration mode, rate, eligibility).

    When ``regeneration_mode`` is ``SPARSE_FIXED_RATIO``,
    a deterministic subset of traversable cells is marked as
    regeneration-eligible using the supplied *seed*.
    """
    gc = _parse_grid_config(config)

    if grid is None:
        empty_cell = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
        grid = [
            [empty_cell for _ in range(gc.grid_width)]
            for _ in range(gc.grid_height)
        ]
    else:
        if len(grid) != gc.grid_height:
            raise ValueError(
                f"Grid height {len(grid)} does not match "
                f"config grid_height {gc.grid_height}"
            )
        for y, row in enumerate(grid):
            if len(row) != gc.grid_width:
                raise ValueError(
                    f"Row {y} width {len(row)} does not match "
                    f"config grid_width {gc.grid_width}"
                )

    if gc.obstacle_density > 0:
        _apply_obstacles(grid, gc, agent_position, seed)

    regeneration_mode = RegenerationMode(gc.regeneration_mode)
    if regeneration_mode == RegenerationMode.SPARSE_FIXED_RATIO:
        _apply_sparse_eligibility(grid, gc.regen_eligible_ratio, seed)

    return World(grid=grid, agent_position=agent_position, regen_rate=gc.resource_regen_rate)


def _apply_obstacles(
    grid: list[list[Cell]],
    config: Grid2DWorldConfig,
    agent_position: Position,
    seed: int | None,
) -> None:
    """Place obstacles on a deterministic subset of empty cells.

    The agent's starting position is always excluded from obstacle
    placement. Runs before sparse eligibility so that obstacle cells
    are correctly excluded from regen-eligible selection.
    """
    obstacle_cell = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)

    candidates: list[tuple[int, int]] = []
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell.is_traversable and (x, y) != (
                agent_position.x, agent_position.y,
            ):
                candidates.append((x, y))

    n_obstacles = round(config.obstacle_density * len(candidates))
    if n_obstacles == 0:
        return

    rng = np.random.default_rng(seed)
    indices = rng.permutation(len(candidates))
    for idx in indices[:n_obstacles]:
        x, y = candidates[idx]
        grid[y][x] = obstacle_cell


def _apply_sparse_eligibility(
    grid: list[list[Cell]],
    regen_eligible_ratio: float | None,
    seed: int | None,
) -> None:
    """Mark a deterministic subset of traversable cells as regen-eligible.

    All other traversable cells are marked ineligible.
    Obstacle cells are always ineligible (enforced by Cell invariant).
    """
    if regen_eligible_ratio is None:
        raise ValueError(
            "regen_eligible_ratio is required when "
            "regeneration_mode is 'sparse_fixed_ratio'"
        )

    traversable: list[tuple[int, int]] = []
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell.is_traversable:
                traversable.append((x, y))

    n_eligible = round(regen_eligible_ratio * len(traversable))

    rng = np.random.default_rng(seed)
    indices = rng.permutation(len(traversable))
    eligible_set = set(traversable[i] for i in indices[:n_eligible])

    for x, y in traversable:
        cell = grid[y][x]
        is_eligible = (x, y) in eligible_set
        if cell.regen_eligible != is_eligible:
            grid[y][x] = cell.model_copy(
                update={"regen_eligible": is_eligible}
            )
