"""Framework-owned episode execution loop."""

from __future__ import annotations

from typing import Any

import numpy as np

from axis.framework.execution_policy import TraceMode
from axis.framework.execution_results import LightEpisodeResult
from axis.sdk.interfaces import SystemInterface
from axis.sdk.position import Position
from axis.sdk.trace import (
    BaseEpisodeTrace,
    BaseStepTrace,
    DeltaEpisodeTrace,
    DeltaStepTrace,
    diff_world_snapshots,
)
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
    decision_data_for_trace = dict(decide_result.decision_data)
    pre_observation = decision_data_for_trace.pop("_pre_observation", None)

    # 3. World advances its own dynamics (e.g. regeneration)
    world.tick()

    # 3a. Capture AFTER_REGEN intermediate snapshot
    world_after_regen = world.snapshot()

    # 3b. Capture world metadata for replay visualization
    world_data = world.world_metadata()

    # 4. Framework applies action
    outcome = registry.apply(
        world, decide_result.action, context=action_context)
    if pre_observation is not None:
        outcome = outcome.model_copy(
            update={
                "data": {**outcome.data, "_pre_observation": pre_observation},
            },
        )

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
            "decision_data": decision_data_for_trace,
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
    episode_index: int = 0,
    trace_mode: TraceMode = TraceMode.FULL,
    world_config: BaseWorldConfig | None = None,
) -> BaseEpisodeTrace | LightEpisodeResult:
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
    if trace_mode is TraceMode.LIGHT:
        return _run_episode_light(
            system,
            world,
            registry,
            max_steps=max_steps,
            seed=seed,
            episode_index=episode_index,
        )
    if trace_mode is TraceMode.DELTA:
        return _run_episode_delta(
            system,
            world,
            registry,
            max_steps=max_steps,
            seed=seed,
            world_config=world_config,
        )
    return _run_episode_full(
        system,
        world,
        registry,
        max_steps=max_steps,
        seed=seed,
        world_config=world_config,
    )


def _run_episode_delta(
    system: SystemInterface,
    world: MutableWorldProtocol,
    registry: ActionRegistry,
    *,
    max_steps: int,
    seed: int,
    world_config: BaseWorldConfig | None = None,
) -> DeltaEpisodeTrace:
    """Run an episode while persisting a replay-capable delta trace."""
    rng = np.random.default_rng(seed)
    agent_state = system.initialize_state()
    ctx = system.action_context()
    initial_world = world.snapshot()
    current_world = initial_world
    steps: list[DeltaStepTrace] = []

    for timestep in range(max_steps):
        position_before = world.agent_position
        vitality_before = system.vitality(agent_state)

        decide_result = system.decide(world, agent_state, rng)
        decision_data_for_trace = dict(decide_result.decision_data)
        pre_observation = decision_data_for_trace.pop("_pre_observation", None)

        world.tick()
        world_after_regen = world.snapshot()
        world_data = world.world_metadata()

        outcome = registry.apply(
            world, decide_result.action, context=ctx,
        )
        if pre_observation is not None:
            outcome = outcome.model_copy(
                update={
                    "data": {**outcome.data, "_pre_observation": pre_observation},
                },
            )

        world_after = world.snapshot()
        new_observation = system.observe(world, world.agent_position)
        transition_result = system.transition(
            agent_state, outcome, new_observation,
        )
        agent_state = transition_result.new_state
        vitality_after = system.vitality(agent_state)
        position_after = world.agent_position

        steps.append(
            DeltaStepTrace(
                timestep=timestep,
                action=decide_result.action,
                regen_delta=diff_world_snapshots(current_world, world_after_regen),
                action_delta=diff_world_snapshots(world_after_regen, world_after),
                agent_position_before=position_before,
                agent_position_after=position_after,
                vitality_before=vitality_before,
                vitality_after=vitality_after,
                terminated=transition_result.terminated,
                termination_reason=transition_result.termination_reason,
                system_data={
                    "decision_data": decision_data_for_trace,
                    "trace_data": transition_result.trace_data,
                },
                world_data=world_data,
            )
        )
        current_world = world_after

        if transition_result.terminated:
            termination_reason = (
                transition_result.termination_reason or "system_terminated"
            )
            break
    else:
        termination_reason = "max_steps_reached"

    return DeltaEpisodeTrace(
        system_type=system.system_type(),
        initial_world=initial_world,
        steps=tuple(steps),
        total_steps=len(steps),
        termination_reason=termination_reason,
        final_vitality=system.vitality(agent_state),
        final_position=world.agent_position,
        world_type=world_config.world_type if world_config else "grid_2d",
        world_config=world_config.model_dump() if world_config else {},
    )


def _run_episode_full(
    system: SystemInterface,
    world: MutableWorldProtocol,
    registry: ActionRegistry,
    *,
    max_steps: int,
    seed: int,
    world_config: BaseWorldConfig | None = None,
) -> BaseEpisodeTrace:
    """Run a full replay-rich episode."""
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


def _run_episode_light(
    system: SystemInterface,
    world: MutableWorldProtocol,
    registry: ActionRegistry,
    *,
    max_steps: int,
    seed: int,
    episode_index: int,
) -> LightEpisodeResult:
    """Run an episode while collecting only summary-oriented outputs."""
    rng = np.random.default_rng(seed)
    agent_state = system.initialize_state()
    ctx = system.action_context()

    total_steps = 0
    termination_reason = "max_steps_reached"
    for timestep in range(max_steps):
        total_steps = timestep + 1
        decide_result = system.decide(world, agent_state, rng)
        decision_data_for_trace = dict(decide_result.decision_data)
        pre_observation = decision_data_for_trace.pop("_pre_observation", None)

        world.tick()
        outcome = registry.apply(world, decide_result.action, context=ctx)
        if pre_observation is not None:
            outcome = outcome.model_copy(
                update={
                    "data": {**outcome.data, "_pre_observation": pre_observation},
                },
            )

        new_observation = system.observe(world, world.agent_position)
        transition_result = system.transition(
            agent_state, outcome, new_observation,
        )
        agent_state = transition_result.new_state
        if transition_result.terminated:
            termination_reason = (
                transition_result.termination_reason or "system_terminated"
            )
            break

    return LightEpisodeResult(
        episode_index=episode_index,
        episode_seed=seed,
        total_steps=total_steps,
        final_vitality=system.vitality(agent_state),
        termination_reason=termination_reason,
        final_position=world.agent_position,
    )


def setup_episode(
    system: SystemInterface,
    world_config: BaseWorldConfig,
    start_position: Position,
    *,
    seed: int,
    world_catalog: Any | None = None,
) -> tuple[MutableWorldProtocol, ActionRegistry]:
    """Create a world and action registry for an episode.

    Uses the world registry to create the world based on world_config.world_type.
    If *world_catalog* is provided, uses catalog lookup instead of the global registry.

    Returns (world, registry) ready for run_episode().
    """
    world = create_world_from_config(
        world_config, start_position, seed,
        world_catalog=world_catalog,
    )

    registry = create_action_registry()
    for action_name, handler in system.action_handlers().items():
        registry.register(action_name, handler)

    return world, registry
