"""Compact synthetic trace builders for comparison tests (WP-11)."""

from __future__ import annotations

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
from axis.sdk.world_types import CellView


def _make_world_snapshot(width: int = 5, height: int = 5) -> WorldSnapshot:
    """Minimal world snapshot for test traces."""
    grid = tuple(
        tuple(
            CellView(cell_type="empty", resource_value=0.0)
            for _ in range(width)
        )
        for _ in range(height)
    )
    return WorldSnapshot(
        grid=grid,
        agent_position=Position(x=0, y=0),
        width=width,
        height=height,
    )


def make_step(
    timestep: int,
    action: str = "move_north",
    pos_before: tuple[int, int] = (0, 0),
    pos_after: tuple[int, int] = (0, 1),
    vitality_before: float = 1.0,
    vitality_after: float = 0.95,
    terminated: bool = False,
    termination_reason: str | None = None,
    system_data: dict | None = None,
) -> BaseStepTrace:
    ws = _make_world_snapshot()
    return BaseStepTrace(
        timestep=timestep,
        action=action,
        world_before=ws,
        world_after=ws,
        agent_position_before=Position(x=pos_before[0], y=pos_before[1]),
        agent_position_after=Position(x=pos_after[0], y=pos_after[1]),
        vitality_before=vitality_before,
        vitality_after=vitality_after,
        terminated=terminated,
        termination_reason=termination_reason,
        system_data=system_data or {},
    )


def make_episode(
    steps: list[BaseStepTrace],
    system_type: str = "system_a",
    world_type: str = "grid_2d",
    world_config: dict | None = None,
    termination_reason: str = "max_steps",
) -> BaseEpisodeTrace:
    last = steps[-1] if steps else None
    return BaseEpisodeTrace(
        system_type=system_type,
        steps=tuple(steps),
        total_steps=len(steps),
        termination_reason=termination_reason,
        final_vitality=last.vitality_after if last else 0.0,
        final_position=last.agent_position_after if last else Position(
            x=0, y=0),
        world_type=world_type,
        world_config=world_config or {},
    )


def make_identical_pair(
    n_steps: int = 5,
    system_type_ref: str = "system_a",
    system_type_cand: str = "system_c",
) -> tuple[BaseEpisodeTrace, BaseEpisodeTrace]:
    """Two traces with identical actions/positions/vitality."""
    steps = [
        make_step(
            timestep=i,
            action="move_north",
            pos_before=(0, i),
            pos_after=(0, i + 1),
            vitality_before=1.0 - i * 0.05,
            vitality_after=1.0 - (i + 1) * 0.05,
        )
        for i in range(n_steps)
    ]
    return (
        make_episode(steps, system_type=system_type_ref),
        make_episode(steps, system_type=system_type_cand),
    )


def make_divergent_pair(
    n_steps: int = 5,
    diverge_at: int = 2,
) -> tuple[BaseEpisodeTrace, BaseEpisodeTrace]:
    """Two traces that diverge in action at `diverge_at`."""
    ref_steps = []
    cand_steps = []
    for i in range(n_steps):
        ref_steps.append(make_step(
            timestep=i,
            action="move_north",
            pos_before=(0, i), pos_after=(0, i + 1),
            vitality_before=1.0 - i * 0.05,
            vitality_after=1.0 - (i + 1) * 0.05,
        ))
        if i < diverge_at:
            cand_steps.append(make_step(
                timestep=i,
                action="move_north",
                pos_before=(0, i), pos_after=(0, i + 1),
                vitality_before=1.0 - i * 0.05,
                vitality_after=1.0 - (i + 1) * 0.05,
            ))
        else:
            cand_steps.append(make_step(
                timestep=i,
                action="move_east",
                pos_before=(i - diverge_at, diverge_at),
                pos_after=(i - diverge_at + 1, diverge_at),
                vitality_before=1.0 - i * 0.04,
                vitality_after=1.0 - (i + 1) * 0.04,
            ))
    return (
        make_episode(ref_steps, system_type="system_a"),
        make_episode(cand_steps, system_type="system_c"),
    )


def make_system_c_step(
    timestep: int,
    action: str = "move_north",
    raw_contributions: dict[str, float] | None = None,
    modulated_scores: dict[str, float] | None = None,
    **kwargs,
) -> BaseStepTrace:
    """Step with System C decision_data in system_data."""
    raw = raw_contributions or {"move_north": 1.0, "consume": 0.5}
    mod = modulated_scores or {"move_north": 1.2, "consume": 0.4}
    system_data = {
        "drive": {"action_contributions": raw, "activation": 0.8},
        "prediction": {"modulated_scores": mod, "context": 0, "features": {}},
    }
    return make_step(timestep=timestep, action=action, system_data=system_data, **kwargs)
