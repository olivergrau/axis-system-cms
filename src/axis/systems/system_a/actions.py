"""System A consume action handler."""

from __future__ import annotations

from typing import Any

from axis.sdk.world_types import ActionOutcome
from axis.world.model import Cell, CellType, World


def handle_consume(
    world: World,
    *,
    context: dict[str, Any],
) -> ActionOutcome:
    """System A consume action handler.

    Extracts resource from the agent's current cell.
    context must contain {"max_consume": float}.
    """
    max_consume: float = context["max_consume"]
    pos = world.agent_position
    cell = world.get_internal_cell(pos)

    if cell.resource_value <= 0:
        return ActionOutcome(
            action="consume",
            moved=False,
            new_position=pos,
            consumed=False,
            resource_consumed=0.0,
        )

    delta_r = min(cell.resource_value, max_consume)
    remainder = cell.resource_value - delta_r

    if remainder <= 0:
        new_cell = Cell(
            cell_type=CellType.EMPTY,
            resource_value=0.0,
            regen_eligible=cell.regen_eligible,
        )
    else:
        new_cell = Cell(
            cell_type=CellType.RESOURCE,
            resource_value=remainder,
            regen_eligible=cell.regen_eligible,
        )
    world.set_cell(pos, new_cell)

    return ActionOutcome(
        action="consume",
        moved=False,
        new_position=pos,
        consumed=True,
        resource_consumed=delta_r,
    )
