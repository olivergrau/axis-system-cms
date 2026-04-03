"""Episode execution loop for AXIS System A."""

from __future__ import annotations

import numpy as np

from axis_system_a.config import SimulationConfig
from axis_system_a.drives import compute_hunger_drive
from axis_system_a.enums import TerminationReason
from axis_system_a.observation import build_observation
from axis_system_a.policy import select_action
from axis_system_a.results import EpisodeResult, EpisodeStepRecord
from axis_system_a.transition import step as transition_step
from axis_system_a.types import AgentState, MemoryState, Observation
from axis_system_a.world import World


def episode_step(
    world: World,
    agent_state: AgentState,
    observation: Observation,
    timestep: int,
    config: SimulationConfig,
    rng: np.random.Generator,
) -> tuple[AgentState, Observation, EpisodeStepRecord]:
    """Execute one full orchestration cycle.

    Chain: observation -> drive -> policy -> transition.

    Parameters
    ----------
    world : Mutable world state. Mutated in place by the transition engine.
    agent_state : Current frozen agent state.
    observation : Pre-step observation (input to drive and policy).
    timestep : Current timestep index.
    config : Full simulation configuration.
    rng : Seeded numpy Generator for stochastic policy.

    Returns
    -------
    tuple of (new_agent_state, new_observation, record)
        new_observation comes from the transition engine output.
    """
    # Drive
    drive_output = compute_hunger_drive(
        energy=agent_state.energy,
        max_energy=config.agent.max_energy,
        observation=observation,
        consume_weight=config.policy.consume_weight,
        stay_suppression=config.policy.stay_suppression,
    )

    # Policy
    decision_result = select_action(
        contributions=drive_output.action_contributions,
        observation=observation,
        selection_mode=config.policy.selection_mode,
        temperature=config.policy.temperature,
        rng=rng,
    )

    # Transition
    result = transition_step(
        world,
        agent_state,
        decision_result.selected_action,
        timestep,
        max_energy=config.agent.max_energy,
        move_cost=config.transition.move_cost,
        consume_cost=config.transition.consume_cost,
        stay_cost=config.transition.stay_cost,
        max_consume=config.transition.max_consume,
        energy_gain_factor=config.transition.energy_gain_factor,
        resource_regen_rate=config.world.resource_regen_rate,
    )

    # Build record
    record = EpisodeStepRecord(
        timestep=timestep,
        observation=observation,
        action=decision_result.selected_action,
        drive_output=drive_output,
        decision_result=decision_result,
        transition_trace=result.trace,
        energy_after=result.agent_state.energy,
        terminated=result.terminated,
    )

    return result.agent_state, result.observation, record


def run_episode(config: SimulationConfig, world: World) -> EpisodeResult:
    """Run a complete episode from initialization to termination.

    Parameters
    ----------
    config : Full simulation configuration.
    world : Pre-built world state. Will be mutated in place.

    Returns
    -------
    EpisodeResult with the full step-by-step trajectory.
    """
    # Initialize
    rng = np.random.default_rng(config.general.seed)
    agent_state = AgentState(
        energy=config.agent.initial_energy,
        memory_state=MemoryState(
            entries=(), capacity=config.agent.memory_capacity),
    )
    observation = build_observation(world, world.agent_position)

    # Execute
    records: list[EpisodeStepRecord] = []

    for timestep in range(config.execution.max_steps):
        agent_state, observation, record = episode_step(
            world, agent_state, observation, timestep, config, rng,
        )
        records.append(record)

        if record.terminated:
            termination_reason = TerminationReason.ENERGY_DEPLETED
            break
    else:
        termination_reason = TerminationReason.MAX_STEPS_REACHED

    return EpisodeResult(
        steps=tuple(records),
        total_steps=len(records),
        termination_reason=termination_reason,
        final_agent_state=agent_state,
        final_position=world.agent_position,
        final_observation=observation,
    )
