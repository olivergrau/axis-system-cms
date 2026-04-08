"""WP-2.4 behavioral equivalence tests -- new vs legacy System A.

These tests verify that the extracted modular System A produces identical
results step-by-step to the legacy monolithic axis_system_a code. This is
the primary validation that the Phase 2 extraction is correct.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pytest

from axis.sdk.position import Position
from axis.sdk.world_types import BaseWorldConfig
from axis.systems.system_a.actions import handle_consume
from axis.systems.system_a.config import SystemAConfig
from axis.systems.system_a.system import SystemA
from axis.world.actions import create_action_registry
from axis.world.grid_2d.factory import create_world
from axis.world.grid_2d.factory import create_world
from axis_system_a.config import (
    AgentConfig as LegacyAgentConfig,
    ExecutionConfig as LegacyExecutionConfig,
    GeneralConfig as LegacyGeneralConfig,
    LoggingConfig as LegacyLoggingConfig,
    PolicyConfig as LegacyPolicyConfig,
    SimulationConfig,
    TransitionConfig as LegacyTransitionConfig,
    WorldConfig as LegacyWorldConfig,
)
from axis_system_a.runner import run_episode
from axis_system_a.types import Position as LegacyPosition
from axis_system_a.world import create_world as legacy_create_world
from tests.v02.constants import (
    DEFAULT_CONSUME_COST,
    DEFAULT_CONSUME_WEIGHT,
    DEFAULT_ENERGY_GAIN_FACTOR,
    DEFAULT_GRID_HEIGHT,
    DEFAULT_GRID_WIDTH,
    DEFAULT_INITIAL_ENERGY,
    DEFAULT_MAX_CONSUME,
    DEFAULT_MAX_ENERGY,
    DEFAULT_MAX_STEPS,
    DEFAULT_MEMORY_CAPACITY,
    DEFAULT_MOVE_COST,
    DEFAULT_OBSTACLE_DENSITY,
    DEFAULT_SEED,
    DEFAULT_SELECTION_MODE,
    DEFAULT_STAY_COST,
    DEFAULT_STAY_SUPPRESSION,
    DEFAULT_TEMPERATURE,
)


# ---------------------------------------------------------------------------
# Trajectory capture
# ---------------------------------------------------------------------------


@dataclass
class Trajectory:
    """Step-by-step trajectory for comparison."""

    actions: list[str] = field(default_factory=list)
    energies_after: list[float] = field(default_factory=list)
    positions_after: list[tuple[int, int]] = field(default_factory=list)
    total_steps: int = 0
    terminated: bool = False
    termination_reason: str | None = None


# ---------------------------------------------------------------------------
# Config builders for equivalence
# ---------------------------------------------------------------------------

FRAMEWORK_KEYS = {
    "seed", "max_steps", "grid_width", "grid_height", "obstacle_density",
}


def _build_legacy_config(overrides: dict | None = None) -> SimulationConfig:
    """Build a legacy SimulationConfig with optional overrides."""
    ov = overrides or {}

    # Extract framework and system overrides
    seed = ov.get("seed", DEFAULT_SEED)
    max_steps = ov.get("max_steps", DEFAULT_MAX_STEPS)
    grid_width = ov.get("grid_width", DEFAULT_GRID_WIDTH)
    grid_height = ov.get("grid_height", DEFAULT_GRID_HEIGHT)
    obstacle_density = ov.get("obstacle_density", DEFAULT_OBSTACLE_DENSITY)

    agent_ov = ov.get("agent", {})
    policy_ov = ov.get("policy", {})
    transition_ov = ov.get("transition", {})
    wd_ov = ov.get("world_dynamics", {})

    return SimulationConfig(
        general=LegacyGeneralConfig(seed=seed),
        world=LegacyWorldConfig(
            grid_width=grid_width,
            grid_height=grid_height,
            obstacle_density=obstacle_density,
            resource_regen_rate=wd_ov.get(
                "resource_regen_rate", 0.0),
        ),
        agent=LegacyAgentConfig(
            initial_energy=agent_ov.get(
                "initial_energy", DEFAULT_INITIAL_ENERGY),
            max_energy=agent_ov.get("max_energy", DEFAULT_MAX_ENERGY),
            memory_capacity=agent_ov.get(
                "memory_capacity", DEFAULT_MEMORY_CAPACITY),
        ),
        policy=LegacyPolicyConfig(
            selection_mode=policy_ov.get(
                "selection_mode", DEFAULT_SELECTION_MODE),
            temperature=policy_ov.get("temperature", DEFAULT_TEMPERATURE),
            stay_suppression=policy_ov.get(
                "stay_suppression", DEFAULT_STAY_SUPPRESSION),
            consume_weight=policy_ov.get(
                "consume_weight", DEFAULT_CONSUME_WEIGHT),
        ),
        transition=LegacyTransitionConfig(
            move_cost=transition_ov.get("move_cost", DEFAULT_MOVE_COST),
            consume_cost=transition_ov.get(
                "consume_cost", DEFAULT_CONSUME_COST),
            stay_cost=transition_ov.get("stay_cost", DEFAULT_STAY_COST),
            max_consume=transition_ov.get("max_consume", DEFAULT_MAX_CONSUME),
            energy_gain_factor=transition_ov.get(
                "energy_gain_factor", DEFAULT_ENERGY_GAIN_FACTOR),
        ),
        execution=LegacyExecutionConfig(max_steps=max_steps),
        logging=LegacyLoggingConfig(enabled=False),
    )


def _build_new_configs(
    overrides: dict | None = None,
) -> tuple[SystemAConfig, BaseWorldConfig, int, int]:
    """Build matching new SystemAConfig and BaseWorldConfig.

    Returns (system_config, world_config, seed, max_steps).
    """
    ov = overrides or {}

    seed = ov.get("seed", DEFAULT_SEED)
    max_steps = ov.get("max_steps", DEFAULT_MAX_STEPS)
    grid_width = ov.get("grid_width", DEFAULT_GRID_WIDTH)
    grid_height = ov.get("grid_height", DEFAULT_GRID_HEIGHT)
    obstacle_density = ov.get("obstacle_density", DEFAULT_OBSTACLE_DENSITY)

    agent_ov = ov.get("agent", {})
    policy_ov = ov.get("policy", {})
    transition_ov = ov.get("transition", {})
    wd_ov = ov.get("world_dynamics", {})

    system_config = SystemAConfig(
        **{
            "agent": {
                "initial_energy": agent_ov.get("initial_energy", DEFAULT_INITIAL_ENERGY),
                "max_energy": agent_ov.get("max_energy", DEFAULT_MAX_ENERGY),
                "memory_capacity": agent_ov.get("memory_capacity", DEFAULT_MEMORY_CAPACITY),
            },
            "policy": {
                "selection_mode": policy_ov.get("selection_mode", DEFAULT_SELECTION_MODE),
                "temperature": policy_ov.get("temperature", DEFAULT_TEMPERATURE),
                "stay_suppression": policy_ov.get("stay_suppression", DEFAULT_STAY_SUPPRESSION),
                "consume_weight": policy_ov.get("consume_weight", DEFAULT_CONSUME_WEIGHT),
            },
            "transition": {
                "move_cost": transition_ov.get("move_cost", DEFAULT_MOVE_COST),
                "consume_cost": transition_ov.get("consume_cost", DEFAULT_CONSUME_COST),
                "stay_cost": transition_ov.get("stay_cost", DEFAULT_STAY_COST),
                "max_consume": transition_ov.get("max_consume", DEFAULT_MAX_CONSUME),
                "energy_gain_factor": transition_ov.get("energy_gain_factor", DEFAULT_ENERGY_GAIN_FACTOR),
            },
        }
    )

    regen_rate = wd_ov.get("resource_regen_rate", 0.0)
    world_config = BaseWorldConfig(
        grid_width=grid_width,
        grid_height=grid_height,
        obstacle_density=obstacle_density,
        resource_regen_rate=regen_rate,
    )

    return system_config, world_config, seed, max_steps


# ---------------------------------------------------------------------------
# Episode runners
# ---------------------------------------------------------------------------


def _run_legacy_episode(overrides: dict | None = None) -> Trajectory:
    """Run an episode using the legacy axis_system_a code."""
    sim_config = _build_legacy_config(overrides)
    seed = sim_config.general.seed

    world = legacy_create_world(
        sim_config.world,
        LegacyPosition(x=0, y=0),
        seed=seed,
    )
    result = run_episode(sim_config, world)

    traj = Trajectory()
    for step in result.steps:
        traj.actions.append(step.selected_action.name.lower())
        traj.energies_after.append(step.energy_after)
        traj.positions_after.append(
            (step.transition_trace.position_after.x,
             step.transition_trace.position_after.y)
        )
    traj.total_steps = result.total_steps
    traj.terminated = result.termination_reason.value == "energy_depleted"
    traj.termination_reason = result.termination_reason.value
    return traj


def _run_new_episode(overrides: dict | None = None) -> Trajectory:
    """Run an episode using the new SystemA + axis.world code.

    Manually orchestrates the framework's role (regen, action application,
    new observation) to match the legacy step lifecycle.
    """
    system_config, world_config, seed, max_steps = _build_new_configs(
        overrides)

    system = SystemA(system_config)
    registry = create_action_registry()
    registry.register("consume", handle_consume)

    world = create_world(world_config, Position(x=0, y=0), seed=seed)

    agent_state = system.initialize_state()
    rng = np.random.default_rng(seed)
    max_consume = system_config.transition.max_consume

    traj = Trajectory()

    for _timestep in range(max_steps):
        # Phase 1: System decides (observes world in current state)
        decide_result = system.decide(world, agent_state, rng)
        traj.actions.append(decide_result.action)

        # Phase 2: World advances its dynamics
        world.tick()

        # Phase 3: Framework applies action
        context = {"max_consume": max_consume}
        outcome = registry.apply(world, decide_result.action, context=context)

        # Phase 4: Build new observation (for transition)
        new_obs = system.sensor.observe(world, world.agent_position)

        # Phase 5: System transition (energy, memory, termination)
        result = system.transition(agent_state, outcome, new_obs)
        agent_state = result.new_state

        traj.energies_after.append(agent_state.energy)
        traj.positions_after.append(
            (world.agent_position.x, world.agent_position.y)
        )

        if result.terminated:
            traj.terminated = True
            traj.termination_reason = "energy_depleted"
            break
    else:
        traj.termination_reason = "max_steps_reached"

    traj.total_steps = len(traj.actions)
    return traj


# ---------------------------------------------------------------------------
# Assertion helper
# ---------------------------------------------------------------------------


def _assert_trajectories_equal(
    legacy: Trajectory, new: Trajectory, scenario: str,
) -> None:
    """Assert step-by-step equivalence between legacy and new trajectories."""
    assert legacy.total_steps == new.total_steps, (
        f"[{scenario}] Step count mismatch: "
        f"legacy={legacy.total_steps}, new={new.total_steps}"
    )

    for i in range(legacy.total_steps):
        assert legacy.actions[i] == new.actions[i], (
            f"[{scenario}] Action mismatch at step {i}: "
            f"legacy={legacy.actions[i]}, new={new.actions[i]}"
        )
        assert legacy.energies_after[i] == new.energies_after[i], (
            f"[{scenario}] Energy mismatch at step {i}: "
            f"legacy={legacy.energies_after[i]}, new={new.energies_after[i]}"
        )
        assert legacy.positions_after[i] == new.positions_after[i], (
            f"[{scenario}] Position mismatch at step {i}: "
            f"legacy={legacy.positions_after[i]}, new={new.positions_after[i]}"
        )

    assert legacy.terminated == new.terminated, (
        f"[{scenario}] Termination mismatch: "
        f"legacy={legacy.terminated}, new={new.terminated}"
    )
    assert legacy.termination_reason == new.termination_reason, (
        f"[{scenario}] Termination reason mismatch: "
        f"legacy={legacy.termination_reason}, new={new.termination_reason}"
    )


# ---------------------------------------------------------------------------
# Parametrized equivalence test
# ---------------------------------------------------------------------------

EQUIVALENCE_SCENARIOS = [
    pytest.param({}, id="default_config"),
    pytest.param(
        {"agent": {"initial_energy": 200, "max_energy": 200}},
        id="high_energy",
    ),
    pytest.param(
        {"agent": {"initial_energy": 10}},
        id="low_energy",
    ),
    pytest.param(
        {"obstacle_density": 0.2},
        id="with_obstacles",
    ),
    pytest.param(
        {"world_dynamics": {"resource_regen_rate": 0.05}},
        id="with_regen",
    ),
    pytest.param(
        {"policy": {"selection_mode": "argmax"}},
        id="argmax_mode",
    ),
    pytest.param(
        {"policy": {"selection_mode": "sample"}},
        id="sample_mode",
    ),
]


class TestBehavioralEquivalence:
    """Behavioral equivalence tests: new vs legacy System A."""

    @pytest.mark.parametrize("overrides", EQUIVALENCE_SCENARIOS)
    def test_behavioral_equivalence(self, overrides: dict) -> None:
        legacy_traj = _run_legacy_episode(overrides)
        new_traj = _run_new_episode(overrides)
        scenario = str(overrides) if overrides else "default"
        _assert_trajectories_equal(legacy_traj, new_traj, scenario)
