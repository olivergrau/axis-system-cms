"""Tests for the framework episode runner (WP-3.2)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from axis.framework.registry import create_system
from axis.framework.runner import run_episode, setup_episode
from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
from axis.sdk.world_types import BaseWorldConfig
from axis.systems.system_a.actions import handle_consume
from axis.systems.system_a.config import SystemAConfig
from axis.systems.system_a.system import SystemA
from axis.world.actions import ActionRegistry, create_action_registry
from axis.world.grid_2d.factory import create_world
from axis.world.grid_2d.model import World
from tests.builders.system_config_builder import SystemAConfigBuilder
from tests.constants import (
    DEFAULT_GRID_HEIGHT,
    DEFAULT_GRID_WIDTH,
    DEFAULT_MAX_STEPS,
    DEFAULT_OBSTACLE_DENSITY,
    DEFAULT_SEED,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _default_config_dict() -> dict[str, Any]:
    return SystemAConfigBuilder().build()


def _world_config() -> BaseWorldConfig:
    return BaseWorldConfig(
        grid_width=DEFAULT_GRID_WIDTH,
        grid_height=DEFAULT_GRID_HEIGHT,
        obstacle_density=DEFAULT_OBSTACLE_DENSITY,
    )


def _run_default_episode(
    *,
    config_dict: dict[str, Any] | None = None,
    max_steps: int = DEFAULT_MAX_STEPS,
    seed: int = DEFAULT_SEED,
) -> BaseEpisodeTrace:
    """Run an episode with default settings via the framework runner."""
    cfg = config_dict or _default_config_dict()
    wc = _world_config()
    system = create_system("system_a", cfg)
    world, registry = setup_episode(
        system,
        wc,
        Position(x=0, y=0),
        seed=seed,
    )
    return run_episode(
        system, world, registry,
        max_steps=max_steps,
        seed=seed,
        world_config=wc,
    )


# ---------------------------------------------------------------------------
# Trace structure tests
# ---------------------------------------------------------------------------


class TestEpisodeTraceStructure:
    """Verify the returned trace has the expected shape."""

    def test_run_episode_returns_episode_trace(self) -> None:
        trace = _run_default_episode()
        assert isinstance(trace, BaseEpisodeTrace)

    def test_episode_trace_system_type(self) -> None:
        trace = _run_default_episode()
        assert trace.system_type == "system_a"

    def test_episode_trace_has_steps(self) -> None:
        trace = _run_default_episode()
        assert len(trace.steps) > 0

    def test_step_trace_structure(self) -> None:
        trace = _run_default_episode()
        step = trace.steps[0]
        assert isinstance(step, BaseStepTrace)
        assert step.timestep == 0
        assert isinstance(step.action, str)
        assert isinstance(step.terminated, bool)

    def test_step_trace_action_in_action_space(self) -> None:
        trace = _run_default_episode()
        system = create_system("system_a", _default_config_dict())
        actions = set(system.action_space())
        for step in trace.steps:
            assert step.action in actions

    def test_step_trace_vitality_bounds(self) -> None:
        trace = _run_default_episode()
        for step in trace.steps:
            assert 0.0 <= step.vitality_before <= 1.0
            assert 0.0 <= step.vitality_after <= 1.0

    def test_step_trace_world_snapshots(self) -> None:
        trace = _run_default_episode()
        step = trace.steps[0]
        assert isinstance(step.world_before, WorldSnapshot)
        assert isinstance(step.world_after, WorldSnapshot)

    def test_step_trace_positions(self) -> None:
        trace = _run_default_episode()
        step = trace.steps[0]
        assert isinstance(step.agent_position_before, Position)
        assert isinstance(step.agent_position_after, Position)


# ---------------------------------------------------------------------------
# Termination tests
# ---------------------------------------------------------------------------


class TestTermination:
    """Verify termination behavior."""

    def test_termination_energy_depleted(self) -> None:
        cfg = SystemAConfigBuilder().with_initial_energy(5.0).build()
        trace = _run_default_episode(config_dict=cfg)
        assert trace.termination_reason == "energy_depleted"
        assert trace.total_steps < DEFAULT_MAX_STEPS

    def test_termination_max_steps(self) -> None:
        cfg = SystemAConfigBuilder().with_initial_energy(
            200.0).with_max_energy(200.0).build()
        trace = _run_default_episode(config_dict=cfg, max_steps=5)
        assert trace.termination_reason == "max_steps_reached"
        assert trace.total_steps == 5


# ---------------------------------------------------------------------------
# Determinism tests
# ---------------------------------------------------------------------------


class TestDeterminism:
    """Verify deterministic behavior with same seed."""

    def test_deterministic_same_seed(self) -> None:
        trace1 = _run_default_episode(seed=99)
        trace2 = _run_default_episode(seed=99)
        assert trace1.total_steps == trace2.total_steps
        for s1, s2 in zip(trace1.steps, trace2.steps):
            assert s1.action == s2.action

    def test_different_seeds_differ(self) -> None:
        trace1 = _run_default_episode(seed=1)
        trace2 = _run_default_episode(seed=2)
        actions1 = [s.action for s in trace1.steps]
        actions2 = [s.action for s in trace2.steps]
        assert actions1 != actions2


# ---------------------------------------------------------------------------
# System data tests
# ---------------------------------------------------------------------------


class TestSystemData:
    """Verify system_data in step traces."""

    def test_system_data_has_decision_data(self) -> None:
        trace = _run_default_episode()
        step = trace.steps[0]
        assert "decision_data" in step.system_data

    def test_system_data_has_trace_data(self) -> None:
        trace = _run_default_episode()
        step = trace.steps[0]
        assert "trace_data" in step.system_data


# ---------------------------------------------------------------------------
# Setup helper tests
# ---------------------------------------------------------------------------


class TestSetupEpisode:
    """Verify setup_episode creates correct objects."""

    def test_setup_episode_creates_world_and_registry(self) -> None:
        system = create_system("system_a", _default_config_dict())
        world, registry = setup_episode(
            system, _world_config(), Position(x=0, y=0), seed=DEFAULT_SEED,
        )
        assert isinstance(world, World)
        assert isinstance(registry, ActionRegistry)

    def test_setup_episode_registers_system_actions(self) -> None:
        system = create_system("system_a", _default_config_dict())
        _world, registry = setup_episode(
            system, _world_config(), Position(x=0, y=0), seed=DEFAULT_SEED,
        )
        assert registry.has_handler("consume")


# ---------------------------------------------------------------------------
# Equivalence with manual orchestration (WP-2.4 pattern)
# ---------------------------------------------------------------------------


class TestEquivalenceWithManualOrchestration:
    """Verify runner produces same results as manual orchestration."""

    def test_equivalence_with_manual_orchestration(self) -> None:
        """Runner output matches WP-2.4 manual orchestration."""
        cfg_dict = _default_config_dict()
        system_config = SystemAConfig(**cfg_dict)
        seed = DEFAULT_SEED
        max_steps = DEFAULT_MAX_STEPS
        max_consume = system_config.transition.max_consume

        # --- Manual orchestration (WP-2.4 pattern) ---
        system_m = SystemA(system_config)
        world_m = create_world(
            _world_config(), Position(x=0, y=0), seed=seed,
        )
        registry_m = create_action_registry()
        registry_m.register("consume", handle_consume)

        agent_state = system_m.initialize_state()
        rng = np.random.default_rng(seed)

        manual_actions: list[str] = []
        manual_vitalities: list[float] = []

        for _ in range(max_steps):
            decide_result = system_m.decide(world_m, agent_state, rng)
            manual_actions.append(decide_result.action)

            world_m.tick()
            context = {"max_consume": max_consume}
            outcome = registry_m.apply(
                world_m, decide_result.action, context=context,
            )
            new_obs = system_m.observe(world_m, world_m.agent_position)
            result = system_m.transition(agent_state, outcome, new_obs)
            agent_state = result.new_state
            manual_vitalities.append(system_m.vitality(agent_state))

            if result.terminated:
                break

        # --- Framework runner ---
        system_r = create_system("system_a", cfg_dict)
        world_r, registry_r = setup_episode(
            system_r, _world_config(), Position(x=0, y=0), seed=seed,
        )
        trace = run_episode(
            system_r, world_r, registry_r,
            max_steps=max_steps, seed=seed,
        )

        # --- Compare ---
        runner_actions = [s.action for s in trace.steps]
        runner_vitalities = [s.vitality_after for s in trace.steps]

        assert len(manual_actions) == len(runner_actions)
        for i, (ma, ra) in enumerate(zip(manual_actions, runner_actions)):
            assert ma == ra, f"Action mismatch at step {i}: manual={ma}, runner={ra}"
        for i, (mv, rv) in enumerate(zip(manual_vitalities, runner_vitalities)):
            assert mv == pytest.approx(rv), (
                f"Vitality mismatch at step {i}: manual={mv}, runner={rv}"
            )


# ---------------------------------------------------------------------------
# World metadata wiring (WP-V.0.3)
# ---------------------------------------------------------------------------


class TestWorldMetadataWiring:
    """Verify that world_metadata() is captured in step traces."""

    def test_world_data_present_in_step_trace(self) -> None:
        trace = _run_default_episode(max_steps=3)
        for step in trace.steps:
            assert isinstance(step.world_data, dict)

    def test_grid_2d_world_data_is_empty(self) -> None:
        trace = _run_default_episode(max_steps=3)
        for step in trace.steps:
            assert step.world_data == {}

    def test_episode_world_type_from_config(self) -> None:
        trace = _run_default_episode(max_steps=3)
        assert trace.world_type == "grid_2d"

    def test_episode_world_config_from_config(self) -> None:
        trace = _run_default_episode(max_steps=3)
        assert "world_type" in trace.world_config
        assert trace.world_config["world_type"] == "grid_2d"
