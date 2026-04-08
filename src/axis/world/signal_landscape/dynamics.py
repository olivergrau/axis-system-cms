"""Signal landscape dynamics: hotspot drift and signal recomputation."""

from __future__ import annotations

import math

import numpy as np

from axis.world.signal_landscape.model import SignalCell, SignalCellType


class Hotspot:
    """A signal source with a center position, radius, and intensity."""

    __slots__ = ("cx", "cy", "radius", "intensity")

    def __init__(self, cx: float, cy: float, radius: float, intensity: float) -> None:
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.intensity = intensity


def drift_hotspots(
    hotspots: list[Hotspot],
    drift_speed: float,
    width: int,
    height: int,
    rng: np.random.Generator,
) -> None:
    """Move each hotspot center by a random delta, wrapping at grid edges."""
    for h in hotspots:
        h.cx = (h.cx + rng.uniform(-drift_speed, drift_speed)) % width
        h.cy = (h.cy + rng.uniform(-drift_speed, drift_speed)) % height


def compute_signal(
    x: int,
    y: int,
    hotspots: list[Hotspot],
    width: int,
    height: int,
    decay_rate: float,
) -> float:
    """Compute the total signal at cell (x, y) from all hotspots."""
    total = 0.0
    for h in hotspots:
        # Use toroidal distance (shortest path wrapping around edges)
        dx = min(abs(x - h.cx), width - abs(x - h.cx))
        dy = min(abs(y - h.cy), height - abs(y - h.cy))
        dist_sq = dx * dx + dy * dy
        total += h.intensity * math.exp(-dist_sq / (2.0 * h.radius * h.radius))
    # Apply decay and clamp
    return min(1.0, total * (1.0 - decay_rate))


def recompute_signals(
    grid: list[list[SignalCell]],
    hotspots: list[Hotspot],
    width: int,
    height: int,
    decay_rate: float,
) -> None:
    """Recompute signal field across all non-obstacle cells."""
    for y in range(height):
        for x in range(width):
            cell = grid[y][x]
            if cell.cell_type == SignalCellType.OBSTACLE:
                continue
            signal = compute_signal(x, y, hotspots, width, height, decay_rate)
            if signal > 0:
                new_cell = SignalCell(
                    cell_type=SignalCellType.RESOURCE,
                    resource_value=round(signal, 10),
                )
            else:
                new_cell = SignalCell(
                    cell_type=SignalCellType.EMPTY,
                    resource_value=0.0,
                )
            grid[y][x] = new_cell
