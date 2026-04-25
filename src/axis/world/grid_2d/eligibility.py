"""Helpers for deterministic regeneration-eligibility layouts."""

from __future__ import annotations

import math

import numpy as np

from axis.world.grid_2d.model import Cell


def apply_sparse_eligibility(
    grid: list[list[Cell]],
    regen_eligible_ratio: float | None,
    seed: int | None,
) -> None:
    """Mark a deterministic random subset of traversable cells as eligible."""
    if regen_eligible_ratio is None:
        raise ValueError(
            "regen_eligible_ratio is required when "
            "regeneration_mode is 'sparse_fixed_ratio'"
        )

    traversable = _collect_traversable_positions(grid)
    eligible_set = _sample_uniform_positions(
        traversable, regen_eligible_ratio, seed,
    )
    _apply_eligibility_set(grid, traversable, eligible_set)


def apply_clustered_eligibility(
    grid: list[list[Cell]],
    regen_eligible_ratio: float | None,
    num_clusters: int | None,
    seed: int | None,
) -> None:
    """Mark a deterministic clustered subset of traversable cells as eligible.

    Clusters are soft rather than dense blocks: cells nearer to sampled cluster
    centers are more likely to become eligible, but the final subset is still
    sampled sparsely so holes remain possible inside a cluster footprint.
    """
    if regen_eligible_ratio is None:
        raise ValueError(
            "regen_eligible_ratio is required when "
            "regeneration_mode is 'clustered'"
        )
    if num_clusters is None:
        raise ValueError(
            "num_clusters is required when regeneration_mode is 'clustered'"
        )

    traversable = _collect_traversable_positions(grid)
    n_eligible = round(regen_eligible_ratio * len(traversable))
    if n_eligible == 0:
        _apply_eligibility_set(grid, traversable, set())
        return

    rng = np.random.default_rng(seed)
    n_centers = min(num_clusters, len(traversable), n_eligible)
    center_indices = rng.choice(
        len(traversable), size=n_centers, replace=False,
    )
    centers = [traversable[int(idx)] for idx in center_indices]

    expected_cluster_size = max(1.0, n_eligible / n_centers)
    sigma = max(1.0, math.sqrt(expected_cluster_size / math.pi))

    weights = np.array(
        [
            math.exp(-_min_squared_distance(position, centers) / (2.0 * sigma * sigma))
            + 1e-9
            for position in traversable
        ],
        dtype=float,
    )
    probabilities = weights / weights.sum()
    eligible_indices = rng.choice(
        len(traversable), size=n_eligible, replace=False, p=probabilities,
    )
    eligible_set = {traversable[int(idx)] for idx in eligible_indices}
    _apply_eligibility_set(grid, traversable, eligible_set)


def _collect_traversable_positions(
    grid: list[list[Cell]],
) -> list[tuple[int, int]]:
    traversable: list[tuple[int, int]] = []
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell.is_traversable:
                traversable.append((x, y))
    return traversable


def _sample_uniform_positions(
    traversable: list[tuple[int, int]],
    regen_eligible_ratio: float,
    seed: int | None,
) -> set[tuple[int, int]]:
    n_eligible = round(regen_eligible_ratio * len(traversable))
    rng = np.random.default_rng(seed)
    indices = rng.permutation(len(traversable))
    return {traversable[int(i)] for i in indices[:n_eligible]}


def _apply_eligibility_set(
    grid: list[list[Cell]],
    traversable: list[tuple[int, int]],
    eligible_set: set[tuple[int, int]],
) -> None:
    for x, y in traversable:
        cell = grid[y][x]
        is_eligible = (x, y) in eligible_set
        if cell.regen_eligible != is_eligible:
            grid[y][x] = cell.model_copy(
                update={"regen_eligible": is_eligible}
            )


def _min_squared_distance(
    position: tuple[int, int],
    centers: list[tuple[int, int]],
) -> float:
    px, py = position
    return min((px - cx) ** 2 + (py - cy) ** 2 for cx, cy in centers)
