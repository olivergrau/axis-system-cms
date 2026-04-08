"""System A consume action handler."""

from __future__ import annotations

from typing import Any

from axis.sdk.world_types import ActionOutcome, MutableWorldProtocol


def handle_consume(
    world: MutableWorldProtocol,
    *,
    context: dict[str, Any],
) -> ActionOutcome:
    """System A consume action handler.

    Extracts resource from the agent's current cell.
    context must contain {"max_consume": float}.
    """
    max_consume: float = context["max_consume"]
    pos = world.agent_position
    extracted = world.extract_resource(pos, max_consume)

    return ActionOutcome(
        action="consume",
        moved=False,
        new_position=pos,
        data={
            "consumed": extracted > 0,
            "resource_consumed": extracted,
        },
    )
