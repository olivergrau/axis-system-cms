"""System B scan action handler."""

from __future__ import annotations

from typing import Any

from axis.sdk.position import Position
from axis.sdk.world_types import ActionOutcome
from axis.world.model import World


def handle_scan(
    world: World,
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
            target = Position(x=pos.x + dx, y=pos.y + dy)
            if world.is_within_bounds(target):
                cell = world.get_cell(target)
                total_resource += cell.resource_value
                cell_count += 1

    # Scan never moves the agent and never consumes resources.
    # We encode the scan result in resource_consumed for transport
    # to transition(). The framework does not interpret this field.
    return ActionOutcome(
        action="scan",
        moved=False,
        new_position=pos,
        consumed=False,
        resource_consumed=total_resource,
    )
