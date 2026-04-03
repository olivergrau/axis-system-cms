"""Transition engine for baseline state evolution."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from axis_system_a.enums import Action, CellType
from axis_system_a.memory import update_memory
from axis_system_a.observation import build_observation
from axis_system_a.types import AgentState, Observation, Position, clip_energy
from axis_system_a.world import Cell, World

_MOVEMENT_DELTAS: dict[Action, tuple[int, int]] = {
    Action.UP: (0, -1),
    Action.DOWN: (0, +1),
    Action.LEFT: (-1, 0),
    Action.RIGHT: (+1, 0),
}


class TransitionTrace(BaseModel):
    """Full trace of a single transition step.

    Captures pre/post state summaries and outcomes for debugging,
    test assertions, and later observability.
    """

    model_config = ConfigDict(frozen=True)

    action: Action
    position_before: Position
    position_after: Position
    moved: bool
    consumed: bool
    resource_consumed: float
    energy_before: float
    energy_after: float
    energy_delta: float
    memory_entries_before: int
    memory_entries_after: int
    terminated: bool


class StepResult(BaseModel):
    """Aggregated output of a single transition step."""

    model_config = ConfigDict(frozen=True)

    agent_state: AgentState
    observation: Observation
    terminated: bool
    trace: TransitionTrace


def _get_action_cost(
    action: Action,
    *,
    move_cost: float,
    consume_cost: float,
    stay_cost: float,
) -> float:
    """Return the energy cost for a given action type."""
    if action in _MOVEMENT_DELTAS:
        return move_cost
    if action is Action.CONSUME:
        return consume_cost
    return stay_cost


def _apply_movement(world: World, action: Action) -> bool:
    """Attempt movement. Returns True if position changed.

    Mutates ``world.agent_position`` on success.
    """
    delta = _MOVEMENT_DELTAS[action]
    pos = world.agent_position
    target = Position(x=pos.x + delta[0], y=pos.y + delta[1])

    if world.is_within_bounds(target) and world.is_traversable(target):
        world.agent_position = target
        return True
    return False


def _apply_consume(
    world: World,
    *,
    max_consume: float,
) -> tuple[bool, float]:
    """Attempt consume on current cell.

    Returns ``(consumed, delta_R)``.  Mutates the world grid on success.
    """
    pos = world.agent_position
    cell = world.get_cell(pos)

    if cell.resource_value <= 0:
        return False, 0.0

    delta_r = min(cell.resource_value, max_consume)
    if delta_r <= 0:
        return False, 0.0

    remainder = cell.resource_value - delta_r
    if remainder <= 0:
        new_cell = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    else:
        new_cell = Cell(cell_type=CellType.RESOURCE, resource_value=remainder)
    world.set_cell(pos, new_cell)
    return True, delta_r


def step(
    world: World,
    agent_state: AgentState,
    action: Action,
    timestep: int,
    *,
    max_energy: float,
    move_cost: float,
    consume_cost: float,
    stay_cost: float,
    max_consume: float,
    energy_gain_factor: float,
) -> StepResult:
    """Execute one complete transition step.

    Follows the strict 6-phase pipeline:

    1. World regeneration (no-op in baseline)
    2. Action application (movement / consume / stay)
    3. Next observation construction
    4. Agent energy update
    5. Memory update (with *new* observation)
    6. Termination evaluation

    Parameters
    ----------
    world : Mutable world state.  Mutated in place (position, cells).
    agent_state : Current frozen agent state (energy + memory).
    action : The action selected by the policy pipeline.
    timestep : Integer timestep for the new memory entry.
    max_energy : Upper bound for energy clipping (E_max).
    move_cost : Energy cost for UP / DOWN / LEFT / RIGHT.
    consume_cost : Energy cost for CONSUME.
    stay_cost : Energy cost for STAY.
    max_consume : Maximum resource extractable per consume (c_max).
    energy_gain_factor : Resource-to-energy conversion factor (kappa).
    """
    # --- Pre-state capture ---
    position_before = world.agent_position
    energy_before = agent_state.energy
    memory_entries_before = len(agent_state.memory_state.entries)

    # --- Phase 1: World Regeneration (no-op) ---
    # Current Cell model lacks regeneration_rate / max_resource fields.
    # Baseline worked examples use alpha=0 everywhere.

    # --- Phase 2: Action Application ---
    moved = False
    consumed = False
    resource_consumed = 0.0

    if action in _MOVEMENT_DELTAS:
        moved = _apply_movement(world, action)
    elif action is Action.CONSUME:
        consumed, resource_consumed = _apply_consume(
            world, max_consume=max_consume,
        )
    # STAY: no world effect

    # --- Phase 3: Next Observation ---
    new_observation = build_observation(world, world.agent_position)

    # --- Phase 4: Agent Energy Update ---
    cost = _get_action_cost(
        action,
        move_cost=move_cost,
        consume_cost=consume_cost,
        stay_cost=stay_cost,
    )
    energy_gain = energy_gain_factor * resource_consumed
    new_energy = clip_energy(energy_before - cost + energy_gain, max_energy)

    # --- Phase 5: Memory Update ---
    new_memory = update_memory(
        agent_state.memory_state, new_observation, timestep,
    )

    new_agent_state = AgentState(energy=new_energy, memory_state=new_memory)

    # --- Phase 6: Termination ---
    terminated = new_energy <= 0.0

    # --- Build trace ---
    trace = TransitionTrace(
        action=action,
        position_before=position_before,
        position_after=world.agent_position,
        moved=moved,
        consumed=consumed,
        resource_consumed=resource_consumed,
        energy_before=energy_before,
        energy_after=new_energy,
        energy_delta=new_energy - energy_before,
        memory_entries_before=memory_entries_before,
        memory_entries_after=len(new_memory.entries),
        terminated=terminated,
    )

    return StepResult(
        agent_state=new_agent_state,
        observation=new_observation,
        terminated=terminated,
        trace=trace,
    )
