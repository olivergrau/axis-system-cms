"""Replay contract types for full, delta, and delta-opt episode traces."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.world_types import CellView

_MOVE_RELATIVE_DELTAS: dict[str, tuple[int, int]] = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


class BaseStepTrace(BaseModel):
    """The global replay contract for a single simulation step.

    Every system must produce data conforming to this schema.
    The framework assembles this from system outputs and world state.

    System-specific data (drive outputs, decision traces, detailed
    transition data) is packed into system_data as an opaque dict.
    Only the system's visualization adapter interprets it.
    """

    model_config = ConfigDict(frozen=True)

    # ── Step identification ──
    timestep: int = Field(..., ge=0)
    action: str

    # ── World snapshots (mandatory) ──
    world_before: WorldSnapshot
    world_after: WorldSnapshot

    # ── World snapshots (optional, system-declared) ──
    intermediate_snapshots: dict[str, WorldSnapshot] = Field(
        default_factory=dict)

    # ── Agent position ──
    agent_position_before: Position
    agent_position_after: Position

    # ── Vitality (normalized [0, 1]) ──
    vitality_before: float = Field(..., ge=0.0, le=1.0)
    vitality_after: float = Field(..., ge=0.0, le=1.0)

    # ── Termination ──
    terminated: bool
    termination_reason: str | None = None

    # ── System-specific trace data ──
    system_data: dict[str, Any] = Field(default_factory=dict)

    # ── World-specific trace data ──
    world_data: dict[str, Any] = Field(default_factory=dict)


class BaseEpisodeTrace(BaseModel):
    """The global replay contract for a complete episode.

    Contains the sequence of step traces and episode-level metadata.
    This is the top-level type serialized to disk per episode.
    """

    model_config = ConfigDict(frozen=True)

    system_type: str
    steps: tuple[BaseStepTrace, ...]
    total_steps: int = Field(..., ge=0)
    termination_reason: str
    final_vitality: float = Field(..., ge=0.0, le=1.0)
    final_position: Position

    # ── World identity (visualization pipeline) ──
    world_type: str = "grid_2d"
    world_config: dict[str, Any] = Field(default_factory=dict)


class DeltaCellUpdate(BaseModel):
    """One changed cell within a delta-applied world transition."""

    model_config = ConfigDict(frozen=True)

    position: Position
    cell: CellView


class WorldDelta(BaseModel):
    """Compact world-state delta relative to a previous snapshot."""

    model_config = ConfigDict(frozen=True)

    agent_position: Position
    changed_cells: tuple[DeltaCellUpdate, ...] = ()


class DeltaStepTrace(BaseModel):
    """Per-step delta representation for replay-capable persistence."""

    model_config = ConfigDict(frozen=True)

    timestep: int = Field(..., ge=0)
    action: str
    regen_delta: WorldDelta
    action_delta: WorldDelta
    agent_position_before: Position
    agent_position_after: Position
    vitality_before: float = Field(..., ge=0.0, le=1.0)
    vitality_after: float = Field(..., ge=0.0, le=1.0)
    terminated: bool
    termination_reason: str | None = None
    system_data: dict[str, Any] = Field(default_factory=dict)
    world_data: dict[str, Any] = Field(default_factory=dict)


class DeltaEpisodeTrace(BaseModel):
    """Compact replay-capable episode trace stored as initial state + deltas."""

    model_config = ConfigDict(frozen=True)

    result_type: str = "delta_episode"
    system_type: str
    initial_world: WorldSnapshot
    steps: tuple[DeltaStepTrace, ...]
    total_steps: int = Field(..., ge=0)
    termination_reason: str
    final_vitality: float = Field(..., ge=0.0, le=1.0)
    final_position: Position
    world_type: str = "grid_2d"
    world_config: dict[str, Any] = Field(default_factory=dict)


class InternalCellState(BaseModel):
    """Minimal hidden world state required for deterministic replay."""

    model_config = ConfigDict(frozen=True)

    regen_eligible: bool = True
    cooldown_remaining: int = Field(default=0, ge=0)


class DeltaOptStepTrace(BaseModel):
    """Per-step compact replay trace without persisted regen deltas."""

    model_config = ConfigDict(frozen=True)

    timestep: int = Field(..., ge=0)
    action: str
    action_delta: WorldDelta
    agent_position_before: Position
    agent_position_after: Position
    vitality_before: float = Field(..., ge=0.0, le=1.0)
    vitality_after: float = Field(..., ge=0.0, le=1.0)
    terminated: bool
    termination_reason: str | None = None
    system_data: dict[str, Any] = Field(default_factory=dict)
    world_data: dict[str, Any] = Field(default_factory=dict)


class DeltaOptEpisodeTrace(BaseModel):
    """Compact replay-capable trace using replay-state reconstruction."""

    model_config = ConfigDict(frozen=True)

    result_type: str = "delta_opt_episode"
    system_type: str
    initial_world: WorldSnapshot
    initial_internal_state: tuple[tuple[InternalCellState, ...], ...]
    steps: tuple[DeltaOptStepTrace, ...]
    total_steps: int = Field(..., ge=0)
    termination_reason: str
    final_vitality: float = Field(..., ge=0.0, le=1.0)
    final_position: Position
    world_type: str = "grid_2d"
    world_config: dict[str, Any] = Field(default_factory=dict)


def compact_delta_opt_system_payload(
    *,
    system_type: str,
    decision_data: dict[str, Any],
    trace_data: dict[str, Any],
    post_observation: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a slimmer system payload for delta-opt persistence."""
    compact_decision = dict(decision_data)
    compact_trace = dict(trace_data)

    if system_type in {"system_a", "system_aw"}:
        compact_trace.pop("buffer_snapshot", None)
        if post_observation is not None:
            compact_trace["_delta_opt_post_observation"] = post_observation

    if system_type in {"system_aw", "system_cw"}:
        compact_trace.pop("relative_position", None)
        compact_trace.pop("visit_count_at_current", None)
        compact_trace.pop("visit_counts_map", None)

    if system_type == "system_c":
        prediction = dict(compact_decision.get("prediction", {}) or {})
        if prediction.get("modulated_scores") == prediction.get("final_scores"):
            prediction.pop("modulated_scores", None)
        if prediction:
            compact_decision["prediction"] = prediction

    if system_type == "system_cw":
        prediction = dict(compact_decision.get("prediction", {}) or {})
        hunger = dict(prediction.get("hunger_modulation", {}) or {})
        curiosity = dict(prediction.get("curiosity_modulation", {}) or {})
        if hunger.get("modulated_scores") == hunger.get("final_scores"):
            hunger.pop("modulated_scores", None)
        if curiosity.get("modulated_scores") == curiosity.get("final_scores"):
            curiosity.pop("modulated_scores", None)
        if hunger:
            prediction["hunger_modulation"] = hunger
        if curiosity:
            prediction["curiosity_modulation"] = curiosity

        hunger_scores = (
            ((compact_decision.get("hunger_drive", {}) or {}).get("action_contributions"))
            or ((prediction.get("hunger_modulation", {}) or {}).get("raw_scores"))
        )
        curiosity_scores = (
            ((compact_decision.get("curiosity_drive", {}) or {}).get("action_contributions"))
            or ((prediction.get("curiosity_modulation", {}) or {}).get("raw_scores"))
        )
        if prediction.get("counterfactual_hunger_scores") == hunger_scores:
            prediction.pop("counterfactual_hunger_scores", None)
        if prediction.get("counterfactual_curiosity_scores") == curiosity_scores:
            prediction.pop("counterfactual_curiosity_scores", None)
        if prediction:
            compact_decision["prediction"] = prediction

    return compact_decision, compact_trace


def diff_world_snapshots(
    before: WorldSnapshot,
    after: WorldSnapshot,
) -> WorldDelta:
    """Build a compact delta from two full snapshots."""
    changed_cells: list[DeltaCellUpdate] = []
    for y in range(before.height):
        for x in range(before.width):
            if before.grid[y][x] != after.grid[y][x]:
                changed_cells.append(
                    DeltaCellUpdate(
                        position=Position(x=x, y=y),
                        cell=after.grid[y][x],
                    )
                )
    return WorldDelta(
        agent_position=after.agent_position,
        changed_cells=tuple(changed_cells),
    )


def apply_world_delta(
    snapshot: WorldSnapshot,
    delta: WorldDelta,
) -> WorldSnapshot:
    """Apply a compact delta to a snapshot and return a new snapshot."""
    mutable_grid = [list(row) for row in snapshot.grid]
    for update in delta.changed_cells:
        mutable_grid[update.position.y][update.position.x] = update.cell
    return WorldSnapshot(
        grid=tuple(tuple(row) for row in mutable_grid),
        agent_position=delta.agent_position,
        width=snapshot.width,
        height=snapshot.height,
    )


def _clone_internal_state(
    state: tuple[tuple[InternalCellState, ...], ...],
) -> list[list[InternalCellState]]:
    return [
        [cell_state.model_copy() for cell_state in row]
        for row in state
    ]


def _freeze_internal_state(
    state: list[list[InternalCellState]],
) -> tuple[tuple[InternalCellState, ...], ...]:
    return tuple(tuple(row) for row in state)


def _regen_rate(world_config: dict[str, Any]) -> float:
    return float(world_config.get("resource_regen_rate", 0.0) or 0.0)


def _regen_cooldown_steps(world_config: dict[str, Any]) -> int:
    return int(world_config.get("resource_regen_cooldown_steps", 0) or 0)


def _serialize_buffer_entry(
    observation: dict[str, Any],
    timestep: int,
) -> dict[str, Any]:
    current = observation.get("current", {}) or {}
    up = observation.get("up", {}) or {}
    down = observation.get("down", {}) or {}
    left = observation.get("left", {}) or {}
    right = observation.get("right", {}) or {}
    return {
        "timestep": timestep,
        "current_res": current.get("resource", 0.0),
        "up_res": up.get("resource", 0.0),
        "down_res": down.get("resource", 0.0),
        "left_res": left.get("resource", 0.0),
        "right_res": right.get("resource", 0.0),
        "current_trav": current.get("traversability", 0.0),
        "up_trav": up.get("traversability", 0.0),
        "down_trav": down.get("traversability", 0.0),
        "left_trav": left.get("traversability", 0.0),
        "right_trav": right.get("traversability", 0.0),
    }


def _restore_delta_opt_system_payloads(
    system_type: str,
    steps: list[BaseStepTrace],
) -> list[BaseStepTrace]:
    restored_steps = steps

    if system_type in {"system_a", "system_aw"}:
        buffer_entries: list[dict[str, Any]] = []
        next_steps: list[BaseStepTrace] = []
        for step in restored_steps:
            trace_data = dict(step.system_data.get("trace_data", {}) or {})
            post_observation = trace_data.pop("_delta_opt_post_observation", None)
            if post_observation is not None:
                buffer_entries.append(
                    _serialize_buffer_entry(post_observation, step.timestep)
                )
                capacity = int(trace_data.get("buffer_capacity", len(buffer_entries)) or len(buffer_entries))
                if len(buffer_entries) > capacity:
                    buffer_entries = buffer_entries[-capacity:]
            trace_data["buffer_snapshot"] = list(buffer_entries)
            system_data = dict(step.system_data)
            system_data["trace_data"] = trace_data
            next_steps.append(step.model_copy(update={"system_data": system_data}))
        restored_steps = next_steps

    if system_type in {"system_aw", "system_cw"}:
        relative_position = (0, 0)
        visit_counts: dict[tuple[int, int], int] = {(0, 0): 1}
        next_steps = []
        for step in restored_steps:
            if step.action in _MOVE_RELATIVE_DELTAS and step.agent_position_after != step.agent_position_before:
                dx, dy = _MOVE_RELATIVE_DELTAS[step.action]
                relative_position = (
                    relative_position[0] + dx,
                    relative_position[1] + dy,
                )
            visit_counts[relative_position] = visit_counts.get(relative_position, 0) + 1

            trace_data = dict(step.system_data.get("trace_data", {}) or {})
            trace_data["relative_position"] = relative_position
            trace_data["visit_count_at_current"] = visit_counts[relative_position]
            trace_data["visit_counts_map"] = [
                [[x, y], count]
                for (x, y), count in sorted(visit_counts.items())
            ]
            system_data = dict(step.system_data)
            system_data["trace_data"] = trace_data
            next_steps.append(step.model_copy(update={"system_data": system_data}))
        restored_steps = next_steps

    if system_type in {"system_c", "system_cw"}:
        next_steps = []
        for step in restored_steps:
            decision_data = dict(step.system_data.get("decision_data", {}) or {})
            prediction = dict(decision_data.get("prediction", {}) or {})

            if system_type == "system_c":
                if "modulated_scores" not in prediction and "final_scores" in prediction:
                    prediction["modulated_scores"] = prediction["final_scores"]

            if system_type == "system_cw":
                hunger = dict(prediction.get("hunger_modulation", {}) or {})
                curiosity = dict(prediction.get("curiosity_modulation", {}) or {})
                if "modulated_scores" not in hunger and "final_scores" in hunger:
                    hunger["modulated_scores"] = hunger["final_scores"]
                if "modulated_scores" not in curiosity and "final_scores" in curiosity:
                    curiosity["modulated_scores"] = curiosity["final_scores"]
                if hunger:
                    prediction["hunger_modulation"] = hunger
                if curiosity:
                    prediction["curiosity_modulation"] = curiosity

                if "counterfactual_hunger_scores" not in prediction:
                    hunger_scores = (
                        ((decision_data.get("hunger_drive", {}) or {}).get("action_contributions"))
                        or hunger.get("raw_scores")
                    )
                    if hunger_scores is not None:
                        prediction["counterfactual_hunger_scores"] = hunger_scores
                if "counterfactual_curiosity_scores" not in prediction:
                    curiosity_scores = (
                        ((decision_data.get("curiosity_drive", {}) or {}).get("action_contributions"))
                        or curiosity.get("raw_scores")
                    )
                    if curiosity_scores is not None:
                        prediction["counterfactual_curiosity_scores"] = curiosity_scores

            if prediction:
                decision_data["prediction"] = prediction
                system_data = dict(step.system_data)
                system_data["decision_data"] = decision_data
                next_steps.append(step.model_copy(update={"system_data": system_data}))
            else:
                next_steps.append(step)
        restored_steps = next_steps

    return restored_steps


def reconstruct_after_regen(
    snapshot: WorldSnapshot,
    internal_state: tuple[tuple[InternalCellState, ...], ...],
    *,
    world_type: str,
    world_config: dict[str, Any],
) -> tuple[WorldSnapshot, tuple[tuple[InternalCellState, ...], ...]]:
    """Reconstruct the deterministic AFTER_REGEN phase from replay state."""
    if world_type not in {"grid_2d", "toroidal"}:
        raise ValueError(
            f"delta-opt replay does not support deterministic regen for world_type={world_type!r}"
        )

    regen_rate = _regen_rate(world_config)
    if regen_rate == 0.0:
        return snapshot, internal_state

    mutable_grid = [list(row) for row in snapshot.grid]
    mutable_state = _clone_internal_state(internal_state)

    for y in range(snapshot.height):
        for x in range(snapshot.width):
            cell_view = snapshot.grid[y][x]
            cell_state = mutable_state[y][x]

            if cell_view.cell_type == "obstacle":
                mutable_state[y][x] = cell_state.model_copy(
                    update={"regen_eligible": False, "cooldown_remaining": 0},
                )
                continue
            if not cell_state.regen_eligible:
                continue
            if cell_state.cooldown_remaining > 0:
                mutable_state[y][x] = cell_state.model_copy(
                    update={"cooldown_remaining": cell_state.cooldown_remaining - 1},
                )
                continue

            new_resource = min(1.0, cell_view.resource_value + regen_rate)
            if new_resource == cell_view.resource_value:
                continue

            if new_resource > 0.0:
                mutable_grid[y][x] = CellView(
                    cell_type="resource",
                    resource_value=new_resource,
                )
            else:
                mutable_grid[y][x] = CellView(
                    cell_type="empty",
                    resource_value=0.0,
                )

    return (
        WorldSnapshot(
            grid=tuple(tuple(row) for row in mutable_grid),
            agent_position=snapshot.agent_position,
            width=snapshot.width,
            height=snapshot.height,
        ),
        _freeze_internal_state(mutable_state),
    )


def apply_action_delta_with_state(
    snapshot_after_regen: WorldSnapshot,
    internal_state_after_regen: tuple[tuple[InternalCellState, ...], ...],
    action_delta: WorldDelta,
    *,
    world_type: str,
    world_config: dict[str, Any],
) -> tuple[WorldSnapshot, tuple[tuple[InternalCellState, ...], ...]]:
    """Apply an action delta and advance the hidden replay-state contract."""
    world_after = apply_world_delta(snapshot_after_regen, action_delta)
    if world_type not in {"grid_2d", "toroidal"}:
        raise ValueError(
            f"delta-opt replay does not support action-state reconstruction for world_type={world_type!r}"
        )

    cooldown_steps = _regen_cooldown_steps(world_config)
    mutable_state = _clone_internal_state(internal_state_after_regen)

    for update in action_delta.changed_cells:
        x = update.position.x
        y = update.position.y
        before_cell = snapshot_after_regen.grid[y][x]
        after_cell = update.cell
        state_before = mutable_state[y][x]

        if not state_before.regen_eligible:
            mutable_state[y][x] = state_before.model_copy(
                update={"cooldown_remaining": 0},
            )
            continue

        consumed_to_empty = (
            before_cell.resource_value > 0.0
            and after_cell.cell_type == "empty"
            and after_cell.resource_value == 0.0
        )
        if consumed_to_empty:
            mutable_state[y][x] = state_before.model_copy(
                update={"cooldown_remaining": cooldown_steps},
            )
            continue

        if after_cell.cell_type in {"empty", "resource"}:
            mutable_state[y][x] = state_before.model_copy(
                update={"cooldown_remaining": 0},
            )

    return world_after, _freeze_internal_state(mutable_state)


def reconstruct_episode_trace(
    delta_episode: DeltaEpisodeTrace | DeltaOptEpisodeTrace,
) -> BaseEpisodeTrace:
    """Materialize a full replay trace from a delta episode."""
    current_world = delta_episode.initial_world
    current_internal_state = (
        delta_episode.initial_internal_state
        if isinstance(delta_episode, DeltaOptEpisodeTrace)
        else None
    )
    steps: list[BaseStepTrace] = []

    for step in delta_episode.steps:
        world_before = current_world
        if isinstance(delta_episode, DeltaOptEpisodeTrace):
            assert current_internal_state is not None
            world_after_regen, internal_after_regen = reconstruct_after_regen(
                world_before,
                current_internal_state,
                world_type=delta_episode.world_type,
                world_config=delta_episode.world_config,
            )
            world_after, current_internal_state = apply_action_delta_with_state(
                world_after_regen,
                internal_after_regen,
                step.action_delta,
                world_type=delta_episode.world_type,
                world_config=delta_episode.world_config,
            )
        else:
            world_after_regen = apply_world_delta(world_before, step.regen_delta)
            world_after = apply_world_delta(world_after_regen, step.action_delta)
        steps.append(
            BaseStepTrace(
                timestep=step.timestep,
                action=step.action,
                world_before=world_before,
                world_after=world_after,
                intermediate_snapshots={"AFTER_REGEN": world_after_regen},
                agent_position_before=step.agent_position_before,
                agent_position_after=step.agent_position_after,
                vitality_before=step.vitality_before,
                vitality_after=step.vitality_after,
                terminated=step.terminated,
                termination_reason=step.termination_reason,
                system_data=step.system_data,
                world_data=step.world_data,
            )
        )
        current_world = world_after

    if isinstance(delta_episode, DeltaOptEpisodeTrace):
        steps = _restore_delta_opt_system_payloads(
            delta_episode.system_type,
            steps,
        )

    return BaseEpisodeTrace(
        system_type=delta_episode.system_type,
        steps=tuple(steps),
        total_steps=delta_episode.total_steps,
        termination_reason=delta_episode.termination_reason,
        final_vitality=delta_episode.final_vitality,
        final_position=delta_episode.final_position,
        world_type=delta_episode.world_type,
        world_config=delta_episode.world_config,
    )
