"""System A through the framework pipeline -- capstone tests (WP-3.6).

These tests verify that running System A through the full framework
(registry -> RunExecutor -> runner) produces results equivalent to the
WP-2.4 behavioral equivalence tests.

This is the ONLY test file that imports both framework and System A code.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from axis.framework.config import (
    ExperimentConfig,
    ExperimentType,
    ExecutionConfig,
    GeneralConfig,
    LoggingConfig,
)
from axis.framework.experiment import ExperimentExecutor, ExperimentResult
from axis.framework.persistence import ExperimentRepository, ExperimentStatus
from axis.framework.registry import create_system, registered_system_types
from axis.framework.run import RunConfig, RunExecutor, RunResult
from axis.framework.runner import run_episode, setup_episode
from axis.sdk.position import Position
from axis.sdk.trace import BaseEpisodeTrace
from axis.sdk.world_types import BaseWorldConfig
from tests.v02.builders.system_config_builder import SystemAConfigBuilder
from tests.v02.constants import (
    DEFAULT_GRID_HEIGHT,
    DEFAULT_GRID_WIDTH,
    DEFAULT_MAX_STEPS,
    DEFAULT_OBSTACLE_DENSITY,
    DEFAULT_SEED,
)
from tests.v02.systems.system_a.test_equivalence import (
    Trajectory,
    _assert_trajectories_equal,
    _run_legacy_episode,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _system_a_experiment_config(
    *,
    max_steps: int = 10,
    num_episodes: int = 2,
    seed: int = 42,
    system_overrides: dict | None = None,
) -> ExperimentConfig:
    builder = SystemAConfigBuilder()
    system_dict = system_overrides or builder.build()
    return ExperimentConfig(
        system_type="system_a",
        experiment_type=ExperimentType.SINGLE_RUN,
        general=GeneralConfig(seed=seed),
        execution=ExecutionConfig(max_steps=max_steps),
        world=BaseWorldConfig(grid_width=5, grid_height=5),
        logging=LoggingConfig(enabled=False),
        system=system_dict,
        num_episodes_per_run=num_episodes,
    )


def _run_framework_episode(overrides: dict | None = None) -> Trajectory:
    """Run an episode through the full framework pipeline.

    Uses the same override format as test_equivalence.py for comparison.
    """
    from axis.framework.config import FrameworkConfig

    ov = overrides or {}
    seed = ov.get("seed", DEFAULT_SEED)
    max_steps = ov.get("max_steps", DEFAULT_MAX_STEPS)
    grid_width = ov.get("grid_width", DEFAULT_GRID_WIDTH)
    grid_height = ov.get("grid_height", DEFAULT_GRID_HEIGHT)
    obstacle_density = ov.get("obstacle_density", DEFAULT_OBSTACLE_DENSITY)

    # Build system config from overrides
    builder = SystemAConfigBuilder()
    agent_ov = ov.get("agent", {})
    policy_ov = ov.get("policy", {})
    transition_ov = ov.get("transition", {})
    wd_ov = ov.get("world_dynamics", {})

    if "initial_energy" in agent_ov:
        builder = builder.with_initial_energy(agent_ov["initial_energy"])
    if "max_energy" in agent_ov:
        builder = builder.with_max_energy(agent_ov["max_energy"])
    if "memory_capacity" in agent_ov:
        builder = builder.with_memory_capacity(agent_ov["memory_capacity"])
    if "selection_mode" in policy_ov:
        builder = builder.with_selection_mode(policy_ov["selection_mode"])
    if "temperature" in policy_ov:
        builder = builder.with_temperature(policy_ov["temperature"])
    if "stay_suppression" in policy_ov:
        builder = builder.with_stay_suppression(policy_ov["stay_suppression"])
    if "consume_weight" in policy_ov:
        builder = builder.with_consume_weight(policy_ov["consume_weight"])
    if "move_cost" in transition_ov:
        builder = builder.with_move_cost(transition_ov["move_cost"])
    if "consume_cost" in transition_ov:
        builder = builder.with_consume_cost(transition_ov["consume_cost"])
    if "stay_cost" in transition_ov:
        builder = builder.with_stay_cost(transition_ov["stay_cost"])
    if "max_consume" in transition_ov:
        builder = builder.with_max_consume(transition_ov["max_consume"])
    if "energy_gain_factor" in transition_ov:
        builder = builder.with_energy_gain_factor(
            transition_ov["energy_gain_factor"])

    system_config = builder.build()

    # Build world config -- regen params now live in the world config
    regen_rate = wd_ov.get("resource_regen_rate", 0.0)
    world_config = BaseWorldConfig(
        grid_width=grid_width,
        grid_height=grid_height,
        obstacle_density=obstacle_density,
        resource_regen_rate=regen_rate,
    )

    run_config = RunConfig(
        system_type="system_a",
        system_config=system_config,
        framework_config=FrameworkConfig(
            general=GeneralConfig(seed=seed),
            execution=ExecutionConfig(max_steps=max_steps),
            world=world_config,
            logging=LoggingConfig(enabled=False),
        ),
        num_episodes=1,
        base_seed=seed,
        run_id="run-0000",
    )

    result = RunExecutor().execute(run_config)
    trace = result.episode_traces[0]

    # Convert to Trajectory for comparison
    traj = Trajectory()
    for step in trace.steps:
        traj.actions.append(step.action)
        # Energy after step is in system_data.trace_data
        traj.energies_after.append(
            step.system_data["trace_data"]["energy_after"]
        )
        traj.positions_after.append(
            (step.agent_position_after.x, step.agent_position_after.y)
        )
    traj.total_steps = trace.total_steps
    traj.terminated = trace.termination_reason == "energy_depleted"
    traj.termination_reason = trace.termination_reason
    return traj


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestSystemARegistered:
    def test_system_a_registered(self) -> None:
        assert "system_a" in registered_system_types()

    def test_create_system_a(self) -> None:
        system = create_system("system_a", SystemAConfigBuilder().build())
        assert system.system_type() == "system_a"


# ---------------------------------------------------------------------------
# Through runner
# ---------------------------------------------------------------------------


class TestSystemAViaRunner:
    def test_run_episode(self) -> None:
        system = create_system("system_a", SystemAConfigBuilder().build())
        world, registry = setup_episode(
            system,
            BaseWorldConfig(grid_width=5, grid_height=5),
            Position(x=0, y=0),
            seed=42,
        )
        trace = run_episode(
            system, world, registry, max_steps=10, seed=42,
        )
        assert isinstance(trace, BaseEpisodeTrace)
        assert trace.system_type == "system_a"
        assert trace.total_steps > 0


# ---------------------------------------------------------------------------
# Through executor
# ---------------------------------------------------------------------------


class TestSystemAViaExecutor:
    def test_run_executor(self) -> None:
        from axis.framework.config import FrameworkConfig

        config = RunConfig(
            system_type="system_a",
            system_config=SystemAConfigBuilder().build(),
            framework_config=FrameworkConfig(
                general=GeneralConfig(seed=42),
                execution=ExecutionConfig(max_steps=10),
                world=BaseWorldConfig(grid_width=5, grid_height=5),
                logging=LoggingConfig(enabled=False),
            ),
            num_episodes=2,
            base_seed=42,
        )
        result = RunExecutor().execute(config)
        assert isinstance(result, RunResult)
        assert result.num_episodes == 2


# ---------------------------------------------------------------------------
# Behavioral equivalence via framework pipeline
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


class TestSystemAEquivalence:
    """Framework pipeline output matches legacy code."""

    @pytest.mark.parametrize("overrides", EQUIVALENCE_SCENARIOS)
    def test_equivalence(self, overrides: dict) -> None:
        legacy_traj = _run_legacy_episode(overrides)
        framework_traj = _run_framework_episode(overrides)
        scenario = str(overrides) if overrides else "default"
        _assert_trajectories_equal(legacy_traj, framework_traj, scenario)


# ---------------------------------------------------------------------------
# Full experiment
# ---------------------------------------------------------------------------


class TestSystemAExperiment:
    def test_single_run(self) -> None:
        config = _system_a_experiment_config()
        result = ExperimentExecutor().execute(config)
        assert isinstance(result, ExperimentResult)
        assert result.summary.num_runs == 1
        assert len(result.run_results) == 1
        assert result.run_results[0].num_episodes == 2

    def test_ofat_temperature(self) -> None:
        config = ExperimentConfig(
            system_type="system_a",
            experiment_type=ExperimentType.OFAT,
            general=GeneralConfig(seed=42),
            execution=ExecutionConfig(max_steps=10),
            world=BaseWorldConfig(grid_width=5, grid_height=5),
            logging=LoggingConfig(enabled=False),
            system=SystemAConfigBuilder().build(),
            num_episodes_per_run=2,
            parameter_path="system.policy.temperature",
            parameter_values=(0.5, 1.0, 2.0),
        )
        result = ExperimentExecutor().execute(config)
        assert result.summary.num_runs == 3
        # Each run should have different temperature applied
        for i, entry in enumerate(result.summary.run_entries):
            expected = f"system.policy.temperature={[0.5, 1.0, 2.0][i]}"
            assert entry.variation_description == expected
