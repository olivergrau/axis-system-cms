"""Shared fixture helpers for WP-V.5.1 adapter test suites.

Provides factory functions for constructing WorldSnapshots, step/episode
traces, system_data dicts, and adapter parametrize lists.
"""

from __future__ import annotations

from typing import Any

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
from axis.sdk.world_types import CellView
from axis.visualization.adapters.default_world import DefaultWorldVisualizationAdapter
from axis.visualization.adapters.null_system import NullSystemVisualizationAdapter
from axis.visualization.replay_models import (
    ReplayEpisodeHandle,
    ReplayStepDescriptor,
    ReplayValidationResult,
)

# Trigger adapter registration side-effects
import axis.world.grid_2d.visualization  # noqa: F401
import axis.world.toroidal.visualization  # noqa: F401
import axis.world.signal_landscape.visualization  # noqa: F401
import axis.systems.system_a.visualization  # noqa: F401
import axis.systems.system_b.visualization  # noqa: F401

from axis.world.grid_2d.visualization import Grid2DWorldVisualizationAdapter
from axis.world.toroidal.visualization import ToroidalWorldVisualizationAdapter
from axis.world.signal_landscape.visualization import (
    SignalLandscapeWorldVisualizationAdapter,
)
from axis.systems.system_a.visualization import SystemAVisualizationAdapter
from axis.systems.system_b.visualization import SystemBVisualizationAdapter


# ---------------------------------------------------------------------------
# Cell / Snapshot helpers
# ---------------------------------------------------------------------------


def make_cell(
    cell_type: str = "empty",
    resource_value: float = 0.0,
) -> CellView:
    """Build a CellView with the given type and resource value."""
    return CellView(cell_type=cell_type, resource_value=resource_value)


def make_snapshot(
    width: int = 5,
    height: int = 5,
    agent_pos: Position | None = None,
    obstacles: list[tuple[int, int]] | None = None,
    resources: dict[tuple[int, int], float] | None = None,
) -> WorldSnapshot:
    """Build a WorldSnapshot.

    Args:
        width: Grid width (columns).
        height: Grid height (rows).
        agent_pos: Agent position (x=col, y=row). Defaults to (0, 0).
        obstacles: List of (row, col) tuples to mark as obstacles.
        resources: Dict of {(row, col): value} to mark as resource cells.
    """
    pos = agent_pos or Position(x=0, y=0)
    obs = set(obstacles or [])
    res = resources or {}

    rows: list[tuple[CellView, ...]] = []
    for r in range(height):
        row: list[CellView] = []
        for c in range(width):
            if (r, c) in obs:
                row.append(make_cell(cell_type="obstacle", resource_value=0.0))
            elif (r, c) in res:
                row.append(make_cell(
                    cell_type="resource", resource_value=res[(r, c)]))
            else:
                row.append(make_cell())
        rows.append(tuple(row))

    return WorldSnapshot(
        grid=tuple(rows), agent_position=pos, width=width, height=height,
    )


# ---------------------------------------------------------------------------
# Step / Episode trace helpers
# ---------------------------------------------------------------------------


def make_step_trace(
    timestep: int = 0,
    action: str = "stay",
    width: int = 5,
    height: int = 5,
    agent_pos_before: Position | None = None,
    agent_pos_after: Position | None = None,
    vitality_before: float = 0.8,
    vitality_after: float = 0.75,
    terminated: bool = False,
    termination_reason: str | None = None,
    system_data: dict[str, Any] | None = None,
    world_data: dict[str, Any] | None = None,
    intermediate_snapshots: dict[str, WorldSnapshot] | None = None,
    obstacles: list[tuple[int, int]] | None = None,
    resources: dict[tuple[int, int], float] | None = None,
) -> BaseStepTrace:
    """Build a BaseStepTrace with configurable fields."""
    pos_b = agent_pos_before or Position(x=1, y=1)
    pos_a = agent_pos_after or Position(x=1, y=1)
    snap_b = make_snapshot(
        width, height, pos_b, obstacles=obstacles, resources=resources)
    snap_a = make_snapshot(
        width, height, pos_a, obstacles=obstacles, resources=resources)

    return BaseStepTrace(
        timestep=timestep,
        action=action,
        world_before=snap_b,
        world_after=snap_a,
        intermediate_snapshots=intermediate_snapshots or {},
        agent_position_before=pos_b,
        agent_position_after=pos_a,
        vitality_before=vitality_before,
        vitality_after=vitality_after,
        terminated=terminated,
        termination_reason=termination_reason,
        system_data=system_data or {},
        world_data=world_data or {},
    )


def make_episode_trace(
    system_type: str = "test",
    num_steps: int = 5,
    world_type: str = "grid_2d",
    world_config: dict[str, Any] | None = None,
    width: int = 5,
    height: int = 5,
    system_data: dict[str, Any] | None = None,
    world_data: dict[str, Any] | None = None,
    intermediate_snapshots: dict[str, WorldSnapshot] | None = None,
    obstacles: list[tuple[int, int]] | None = None,
    resources: dict[tuple[int, int], float] | None = None,
) -> BaseEpisodeTrace:
    """Build a BaseEpisodeTrace with the given number of steps."""
    steps = tuple(
        make_step_trace(
            timestep=i,
            width=width,
            height=height,
            system_data=system_data,
            world_data=world_data,
            intermediate_snapshots=intermediate_snapshots,
            obstacles=obstacles,
            resources=resources,
        )
        for i in range(num_steps)
    )
    last_step = steps[-1] if steps else None
    return BaseEpisodeTrace(
        system_type=system_type,
        steps=steps,
        total_steps=num_steps,
        termination_reason="max_steps",
        final_vitality=last_step.vitality_after if last_step else 0.0,
        final_position=last_step.agent_position_after if last_step else Position(
            x=0, y=0),
        world_type=world_type,
        world_config=world_config or {},
    )


def make_episode_handle(
    episode: BaseEpisodeTrace | None = None,
    grid_width: int = 5,
    grid_height: int = 5,
) -> ReplayEpisodeHandle:
    """Wrap an episode trace in a ReplayEpisodeHandle with validation."""
    if episode is None:
        episode = make_episode_trace(width=grid_width, height=grid_height)

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
        for i in range(episode.total_steps)
    )

    validation = ReplayValidationResult(
        valid=True,
        total_steps=episode.total_steps,
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


# ---------------------------------------------------------------------------
# System data helpers
# ---------------------------------------------------------------------------


def sample_system_a_data() -> dict[str, Any]:
    """Return canonical System A system_data dict."""
    return {
        "decision_data": {
            "observation": {
                "current": {"traversability": 1.0, "resource": 0.5},
                "up": {"traversability": 1.0, "resource": 0.3},
                "down": {"traversability": 0.0, "resource": 0.0},
                "left": {"traversability": 1.0, "resource": 0.0},
                "right": {"traversability": 1.0, "resource": 0.8},
            },
            "drive": {
                "activation": 0.7500,
                "action_contributions": (0.1, 0.05, 0.02, 0.3, 0.5, 0.03),
            },
            "policy": {
                "raw_contributions": (0.2, 0.1, 0.05, 0.35, 0.6, 0.1),
                "admissibility_mask": (True, False, True, True, True, True),
                "masked_contributions": (
                    0.2, float("-inf"), 0.05, 0.35, 0.6, 0.1),
                "probabilities": (0.12, 0.0, 0.08, 0.25, 0.45, 0.10),
                "selected_action": "consume",
                "temperature": 1.50,
                "selection_mode": "sample",
            },
        },
        "trace_data": {
            "energy_before": 45.00,
            "energy_after": 43.50,
            "energy_delta": -1.50,
            "action_cost": 2.00,
            "energy_gain": 0.50,
            "memory_entries_before": 3,
            "memory_entries_after": 4,
        },
    }


def sample_system_b_data() -> dict[str, Any]:
    """Return canonical System B system_data dict."""
    return {
        "decision_data": {
            "weights": [1.2, 0.8, 0.5, 1.5, 0.3, 0.2],
            "probabilities": [0.25, 0.15, 0.10, 0.35, 0.08, 0.07],
            "last_scan": {
                "total_resource": 2.750,
                "cell_count": 9,
            },
        },
        "trace_data": {
            "energy_before": 40.00,
            "energy_after": 38.50,
            "energy_delta": -1.50,
            "action_cost": 1.50,
            "scan_total": 2.750,
        },
    }


def sample_signal_landscape_world_data() -> dict[str, Any]:
    """Return canonical signal landscape world_data dict with hotspots."""
    return {
        "hotspots": [
            {"cx": 3, "cy": 2, "radius": 2.0, "intensity": 0.8},
            {"cx": 7, "cy": 6, "radius": 3.0, "intensity": 0.5},
        ],
    }


# ---------------------------------------------------------------------------
# Parametrize lists
# ---------------------------------------------------------------------------

ALL_WORLD_ADAPTERS: list[tuple[str, object]] = [
    ("default", DefaultWorldVisualizationAdapter()),
    ("grid_2d", Grid2DWorldVisualizationAdapter()),
    ("toroidal", ToroidalWorldVisualizationAdapter()),
    ("signal_landscape", SignalLandscapeWorldVisualizationAdapter()),
]

ALL_SYSTEM_ADAPTERS: list[tuple[str, object]] = [
    ("null", NullSystemVisualizationAdapter()),
    ("system_a", SystemAVisualizationAdapter(max_energy=100.0)),
    ("system_b", SystemBVisualizationAdapter(max_energy=100.0)),
]
