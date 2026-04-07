"""World dynamics: regeneration and other per-step world updates."""

from __future__ import annotations

from axis.sdk.position import Position
from axis.world.model import Cell, CellType, World


def apply_regeneration(world: World, *, regen_rate: float) -> int:
    """Apply deterministic cell regeneration to all eligible cells.

    For each non-obstacle, regen-eligible cell:
        r_next = min(1.0, r_current + regen_rate)
    EMPTY cells that gain resource become RESOURCE cells.

    Returns the number of cells updated.
    """
    if regen_rate == 0.0:
        return 0

    count = 0
    for y in range(world.height):
        for x in range(world.width):
            pos = Position(x=x, y=y)
            cell = world.get_internal_cell(pos)

            if cell.cell_type is CellType.OBSTACLE:
                continue
            if not cell.regen_eligible:
                continue

            new_resource = min(1.0, cell.resource_value + regen_rate)
            if new_resource == cell.resource_value:
                continue

            count += 1
            if new_resource > 0:
                new_cell = Cell(
                    cell_type=CellType.RESOURCE,
                    resource_value=new_resource,
                    regen_eligible=cell.regen_eligible,
                )
            else:
                new_cell = Cell(
                    cell_type=CellType.EMPTY,
                    resource_value=0.0,
                    regen_eligible=cell.regen_eligible,
                )
            world.set_cell(pos, new_cell)

    return count
