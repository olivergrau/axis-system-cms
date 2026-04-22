"""System B scan action handler."""

from __future__ import annotations

from typing import Any

from axis.sdk.position import Position
from axis.sdk.world_types import ActionOutcome, MutableWorldProtocol


def _canonicalize_position(
    world: MutableWorldProtocol,
    position: Position,
) -> Position:
    """Return a world-canonical position when the world exposes one."""
    canonicalize = getattr(world, "canonicalize_position", None)
    if callable(canonicalize):
        return canonicalize(position)
    return position


def handle_scan(
    world: MutableWorldProtocol,
    *,
    context: dict[str, Any],
) -> ActionOutcome:
    """Scan a neighborhood around the agent.

    Reads resource values in a (2*radius+1)x(2*radius+1) area.
    Does NOT modify the world -- purely informational.
    context must contain {"scan_radius": int}.
    """
    pos = world.agent_position
    scan_radius: int = context.get("scan_radius", 1)

    total_resource = 0.0
    cell_count = 0

    for dy in range(-scan_radius, scan_radius + 1):
        for dx in range(-scan_radius, scan_radius + 1):
            target = _canonicalize_position(
                world,
                Position(x=pos.x + dx, y=pos.y + dy),
            )
            if world.is_within_bounds(target):
                cell = world.get_cell(target)
                total_resource += cell.resource_value
                cell_count += 1

    # Scan never moves the agent and never consumes resources.
    # Scan results are passed to transition() via the data dict.
    return ActionOutcome(
        action="scan",
        moved=False,
        new_position=pos,
        data={"scan_total": total_resource, "cell_count": cell_count},
    )
