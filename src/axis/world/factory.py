"""World factory: create_world and helpers."""

from __future__ import annotations

import numpy as np

from axis.sdk.position import Position
from axis.sdk.world_types import BaseWorldConfig
from axis.world.model import Cell, CellType, RegenerationMode, World


def create_world(
    config: BaseWorldConfig,
    agent_position: Position,
    grid: list[list[Cell]] | None = None,
    *,
    seed: int | None = None,
    regeneration_mode: RegenerationMode = RegenerationMode.ALL_TRAVERSABLE,
    regen_eligible_ratio: float | None = None,
) -> World:
    """Create a World from configuration.

    If grid is None, creates a grid of EMPTY cells.
    If grid is provided, validates dimensions against config.

    Regeneration parameters are system-provided (not part of
    BaseWorldConfig) since systems own their dynamics (Q12).

    When ``regeneration_mode`` is ``SPARSE_FIXED_RATIO``,
    a deterministic subset of traversable cells is marked as
    regeneration-eligible using the supplied *seed*.
    """
    if grid is None:
        empty_cell = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
        grid = [
            [empty_cell for _ in range(config.grid_width)]
            for _ in range(config.grid_height)
        ]
    else:
        if len(grid) != config.grid_height:
            raise ValueError(
                f"Grid height {len(grid)} does not match "
                f"config grid_height {config.grid_height}"
            )
        for y, row in enumerate(grid):
            if len(row) != config.grid_width:
                raise ValueError(
                    f"Row {y} width {len(row)} does not match "
                    f"config grid_width {config.grid_width}"
                )

    if config.obstacle_density > 0:
        _apply_obstacles(grid, config, agent_position, seed)

    if regeneration_mode == RegenerationMode.SPARSE_FIXED_RATIO:
        _apply_sparse_eligibility(grid, regen_eligible_ratio, seed)

    return World(grid=grid, agent_position=agent_position)


def _apply_obstacles(
    grid: list[list[Cell]],
    config: BaseWorldConfig,
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
