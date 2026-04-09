"""Shared fixture helpers for WP-V.5.2 replay infrastructure test suites.

Provides factory functions for multi-phase episodes, episode handles,
viewer states, and phase-name constants.
"""

from __future__ import annotations

from typing import Any

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
from axis.sdk.world_types import CellView
from axis.visualization.replay_models import (
    ReplayEpisodeHandle,
    ReplayStepDescriptor,
    ReplayValidationResult,
)
from axis.visualization.viewer_state import ViewerState, create_initial_state


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SYSTEM_A_PHASES: list[str] = ["BEFORE", "AFTER_REGEN", "AFTER_ACTION"]
SYSTEM_B_PHASES: list[str] = ["BEFORE", "AFTER_ACTION"]


# ---------------------------------------------------------------------------
# Snapshot helpers
# ---------------------------------------------------------------------------


def _make_cell(resource: float = 0.0) -> CellView:
    ct = "resource" if resource > 0 else "empty"
    return CellView(cell_type=ct, resource_value=resource)


def _make_snapshot(
    width: int = 5,
    height: int = 5,
    agent_pos: Position | None = None,
    marker_resource: float = 0.0,
) -> WorldSnapshot:
    """Build a WorldSnapshot with an optional marker resource at (0,0)."""
    pos = agent_pos or Position(x=1, y=1)
    rows = []
    for r in range(height):
        row = []
        for c in range(width):
            if r == 0 and c == 0:
                row.append(_make_cell(marker_resource))
            else:
                row.append(_make_cell())
        rows.append(tuple(row))
    return WorldSnapshot(
        grid=tuple(rows), agent_position=pos, width=width, height=height,
    )


# ---------------------------------------------------------------------------
# Step / Episode builders
# ---------------------------------------------------------------------------


def make_step_trace(
    timestep: int = 0,
    action: str = "stay",
    vitality_before: float = 0.8,
    vitality_after: float = 0.75,
    terminated: bool = False,
    termination_reason: str | None = None,
    system_data: dict[str, Any] | None = None,
    world_data: dict[str, Any] | None = None,
    include_intermediate: bool = False,
    intermediate_name: str = "AFTER_REGEN",
    width: int = 5,
    height: int = 5,
) -> BaseStepTrace:
    """Build a BaseStepTrace.

    If include_intermediate=True, adds an intermediate snapshot with a
    distinct marker resource value (0.5) for verifiable resolution.
    """
    pos_b = Position(x=1, y=1)
    pos_a = Position(x=2, y=1)

    snap_before = _make_snapshot(width, height, pos_b, marker_resource=0.1)
    snap_after = _make_snapshot(width, height, pos_a, marker_resource=0.9)

    intermediates: dict[str, WorldSnapshot] = {}
    if include_intermediate:
        intermediates[intermediate_name] = _make_snapshot(
            width, height, pos_b, marker_resource=0.5,
        )

    return BaseStepTrace(
        timestep=timestep,
        action=action,
        world_before=snap_before,
        world_after=snap_after,
        intermediate_snapshots=intermediates,
        agent_position_before=pos_b,
        agent_position_after=pos_a,
        vitality_before=vitality_before,
        vitality_after=vitality_after,
        terminated=terminated,
        termination_reason=termination_reason,
        system_data=system_data or {},
        world_data=world_data or {},
    )


def make_3phase_episode(
    num_steps: int = 5,
    width: int = 5,
    height: int = 5,
) -> BaseEpisodeTrace:
    """Build an episode with intermediate snapshots for 3-phase systems."""
    steps = []
    for i in range(num_steps):
        is_last = i == num_steps - 1
        steps.append(make_step_trace(
            timestep=i,
            include_intermediate=True,
            terminated=is_last,
            termination_reason="max_steps" if is_last else None,
            width=width,
            height=height,
        ))
    return BaseEpisodeTrace(
        system_type="system_a",
        steps=tuple(steps),
        total_steps=num_steps,
        termination_reason="max_steps",
        final_vitality=steps[-1].vitality_after,
        final_position=steps[-1].agent_position_after,
    )


def make_2phase_episode(
    num_steps: int = 5,
    width: int = 5,
    height: int = 5,
) -> BaseEpisodeTrace:
    """Build an episode without intermediate snapshots for 2-phase systems."""
    steps = []
    for i in range(num_steps):
        is_last = i == num_steps - 1
        steps.append(make_step_trace(
            timestep=i,
            include_intermediate=False,
            terminated=is_last,
            termination_reason="max_steps" if is_last else None,
            width=width,
            height=height,
        ))
    return BaseEpisodeTrace(
        system_type="system_b",
        steps=tuple(steps),
        total_steps=num_steps,
        termination_reason="max_steps",
        final_vitality=steps[-1].vitality_after,
        final_position=steps[-1].agent_position_after,
    )


def make_episode_handle_for_viewer(
    num_steps: int = 5,
    grid_width: int = 5,
    grid_height: int = 5,
    include_intermediate: bool = False,
) -> ReplayEpisodeHandle:
    """Build an episode handle suitable for ViewerState construction."""
    if include_intermediate:
        episode = make_3phase_episode(num_steps, grid_width, grid_height)
    else:
        episode = make_2phase_episode(num_steps, grid_width, grid_height)

    descriptors = tuple(
        ReplayStepDescriptor(
            step_index=i,
            has_world_before=True,
            has_world_after=True,
            has_intermediate_snapshots=tuple(
                sorted(episode.steps[i].intermediate_snapshots.keys()),
            ),
            has_agent_position=True,
            has_vitality=True,
            has_world_state=True,
        )
        for i in range(num_steps)
    )

    validation = ReplayValidationResult(
        valid=True,
        total_steps=num_steps,
        grid_width=grid_width,
        grid_height=grid_height,
        step_descriptors=descriptors,
    )

    return ReplayEpisodeHandle(
        experiment_id="test_exp",
        run_id="run-0000",
        episode_index=0,
        episode_trace=episode,
        validation=validation,
    )


def make_viewer_state(
    num_phases: int = 2,
    num_steps: int = 5,
    include_intermediate: bool = False,
) -> ViewerState:
    """Build a ViewerState at the initial coordinate."""
    handle = make_episode_handle_for_viewer(
        num_steps=num_steps,
        include_intermediate=include_intermediate,
    )
    return create_initial_state(handle, num_phases)
