"""Framework-owned episode execution loop."""

from __future__ import annotations

from typing import Any

import numpy as np

from axis.sdk.interfaces import SystemInterface
from axis.sdk.position import Position
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
from axis.sdk.world_types import BaseWorldConfig, MutableWorldProtocol
from axis.world.actions import ActionRegistry, create_action_registry
from axis.world.registry import create_world_from_config


def _run_step(
    system: SystemInterface,
    world: MutableWorldProtocol,
    registry: ActionRegistry,
    agent_state: Any,
    rng: np.random.Generator,
    timestep: int,
    *,
    action_context: dict[str, Any],
) -> tuple[Any, BaseStepTrace]:
    """Execute one step of the episode loop.

    Returns (new_agent_state, step_trace).
    """
    # 1. Capture BEFORE snapshot
    world_before = world.snapshot()
    position_before = world.agent_position
    vitality_before = system.vitality(agent_state)

    # 2. System decides
    decide_result = system.decide(world, agent_state, rng)

    # 3. World advances its own dynamics (e.g. regeneration)
    world.tick()

    # 3a. Capture AFTER_REGEN intermediate snapshot
    world_after_regen = world.snapshot()

    # 3b. Capture world metadata for replay visualization
    world_data = world.world_metadata()

    # 4. Framework applies action
    outcome = registry.apply(
        world, decide_result.action, context=action_context)

    # 5. Capture AFTER_ACTION snapshot
    world_after = world.snapshot()
    position_after = world.agent_position

    # 6. System observes post-action world
    new_observation = system.observe(world, world.agent_position)

    # 7. System transitions
    transition_result = system.transition(
        agent_state, outcome, new_observation)
    new_state = transition_result.new_state
    vitality_after = system.vitality(new_state)

    # 8. Build step trace
    step_trace = BaseStepTrace(
        timestep=timestep,
        action=decide_result.action,
        world_before=world_before,
        world_after=world_after,
        intermediate_snapshots={"AFTER_REGEN": world_after_regen},
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
        world_data=world_data,
    )

    return new_state, step_trace


def run_episode(
    system: SystemInterface,
    world: MutableWorldProtocol,
    registry: ActionRegistry,
    *,
    max_steps: int,
    seed: int,
    world_config: BaseWorldConfig | None = None,
) -> BaseEpisodeTrace:
    """Run a complete episode from initialization to termination.

    Parameters
    ----------
    system : A SystemInterface implementation (already constructed).
    world : A mutable World (already created with correct grid layout).
    registry : ActionRegistry with all actions registered (base + system-specific).
    max_steps : Maximum step count (framework termination).
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
            action_context=ctx,
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
        world_type=world_config.world_type if world_config else "grid_2d",
        world_config=world_config.model_dump() if world_config else {},
    )


def setup_episode(
    system: SystemInterface,
    world_config: BaseWorldConfig,
    start_position: Position,
    *,
    seed: int,
) -> tuple[MutableWorldProtocol, ActionRegistry]:
    """Create a world and action registry for an episode.

    Uses the world registry to create the world based on world_config.world_type.

    Returns (world, registry) ready for run_episode().
    """
    world = create_world_from_config(world_config, start_position, seed)

    registry = create_action_registry()
    for action_name, handler in system.action_handlers().items():
        registry.register(action_name, handler)

    return world, registry
