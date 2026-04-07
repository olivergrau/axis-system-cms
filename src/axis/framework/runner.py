"""Framework-owned episode execution loop."""

from __future__ import annotations

from typing import Any

import numpy as np

from axis.sdk.interfaces import SystemInterface
from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot, snapshot_world
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
from axis.sdk.world_types import BaseWorldConfig
from axis.world.actions import ActionRegistry, create_action_registry
from axis.world.dynamics import apply_regeneration
from axis.world.model import RegenerationMode, World


def _run_step(
    system: SystemInterface,
    world: World,
    registry: ActionRegistry,
    agent_state: Any,
    rng: np.random.Generator,
    timestep: int,
    *,
    regen_rate: float,
    action_context: dict[str, Any],
) -> tuple[Any, BaseStepTrace]:
    """Execute one step of the episode loop.

    Returns (new_agent_state, step_trace).
    """
    # 1. Capture BEFORE snapshot
    world_before = snapshot_world(world, world.width, world.height)
    position_before = world.agent_position
    vitality_before = system.vitality(agent_state)

    # 2. System decides
    decide_result = system.decide(world, agent_state, rng)

    # 3. Framework applies regeneration
    apply_regeneration(world, regen_rate=regen_rate)

    # 4. Framework applies action
    outcome = registry.apply(world, decide_result.action, context=action_context)

    # 5. Capture AFTER_ACTION snapshot
    world_after = snapshot_world(world, world.width, world.height)
    position_after = world.agent_position

    # 6. System observes post-action world
    new_observation = system.observe(world, world.agent_position)

    # 7. System transitions
    transition_result = system.transition(agent_state, outcome, new_observation)
    new_state = transition_result.new_state
    vitality_after = system.vitality(new_state)

    # 8. Build step trace
    step_trace = BaseStepTrace(
        timestep=timestep,
        action=decide_result.action,
        world_before=world_before,
        world_after=world_after,
        intermediate_snapshots={},
        agent_position_before=position_before,
        agent_position_after=position_after,
        vitality_before=vitality_before,
        vitality_after=vitality_after,
        terminated=transition_result.terminated,
        termination_reason=transition_result.termination_reason,
        system_data={
            "decision_data": decide_result.decision_data,
            "trace_data": transition_result.trace_data,
        },
    )

    return new_state, step_trace


def run_episode(
    system: SystemInterface,
    world: World,
    registry: ActionRegistry,
    *,
    max_steps: int,
    regen_rate: float,
    seed: int,
) -> BaseEpisodeTrace:
    """Run a complete episode from initialization to termination.

    Parameters
    ----------
    system : A SystemInterface implementation (already constructed).
    world : A mutable World (already created with correct grid layout).
    registry : ActionRegistry with all actions registered (base + system-specific).
    max_steps : Maximum step count (framework termination).
    regen_rate : Per-step resource regeneration rate.
    seed : RNG seed for this episode.

    Returns
    -------
    BaseEpisodeTrace with step-by-step traces.
    """
    rng = np.random.default_rng(seed)
    agent_state = system.initialize_state()
    ctx = system.action_context()
    steps: list[BaseStepTrace] = []

    for timestep in range(max_steps):
        agent_state, step_trace = _run_step(
            system, world, registry, agent_state, rng, timestep,
            regen_rate=regen_rate, action_context=ctx,
        )
        steps.append(step_trace)

        if step_trace.terminated:
            termination_reason = step_trace.termination_reason or "system_terminated"
            break
    else:
        termination_reason = "max_steps_reached"

    return BaseEpisodeTrace(
        system_type=system.system_type(),
        steps=tuple(steps),
        total_steps=len(steps),
        termination_reason=termination_reason,
        final_vitality=system.vitality(agent_state),
        final_position=world.agent_position,
    )


def setup_episode(
    system: SystemInterface,
    world_config: BaseWorldConfig,
    start_position: Position,
    *,
    seed: int,
    regen_rate: float = 0.0,
    regeneration_mode: str = "all_traversable",
    regen_eligible_ratio: float | None = None,
) -> tuple[World, ActionRegistry]:
    """Create a world and action registry for an episode.

    Returns (world, registry) ready for run_episode().
    """
    from axis.world.factory import create_world

    world = create_world(
        world_config, start_position, seed=seed,
        regeneration_mode=RegenerationMode(regeneration_mode),
        regen_eligible_ratio=regen_eligible_ratio,
    )

    registry = create_action_registry()
    for action_name, handler in system.action_handlers().items():
        registry.register(action_name, handler)

    return world, registry
