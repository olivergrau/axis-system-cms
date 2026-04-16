"""Episode smoke tests for System C.

Runs a multi-step loop to verify no crashes, no NaN,
and that prediction is actively influencing behavior.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from axis.sdk.position import Position
from axis.sdk.world_types import ActionOutcome
from axis.systems.construction_kit.observation.types import CellObservation, Observation
from axis.systems.construction_kit.prediction.memory import get_prediction
from axis.systems.construction_kit.traces.state import get_confidence, get_frustration
from axis.systems.system_c.config import SystemCConfig
from axis.systems.system_c.system import SystemC
from axis.world.grid_2d.model import Cell, CellType, World
from tests.builders.system_c_config_builder import SystemCConfigBuilder


def _make_resource_grid(
    width: int, height: int, value: float = 0.5,
) -> list[list[Cell]]:
    return [
        [Cell(cell_type=CellType.RESOURCE, resource_value=value)
         for _ in range(width)]
        for _ in range(height)
    ]


def _make_observation(resource: float = 0.0) -> Observation:
    cell = CellObservation(traversability=1.0, resource=resource)
    return Observation(
        current=cell, up=cell, down=cell, left=cell, right=cell,
    )


def _run_episode(system: SystemC, world: World, steps: int, seed: int = 42):
    """Run an episode loop, returning (final_state, decision_datas)."""
    rng = np.random.default_rng(seed)
    state = system.initialize_state()
    decision_datas = []

    for step in range(steps):
        result = system.decide(world, state, rng)
        decision_datas.append(result.decision_data)

        action = result.action
        moved = action in ("up", "down", "left", "right")
        data = {}
        if action == "consume":
            # Simulate consuming resource at agent position
            data = {"consumed": True, "resource_consumed": 0.3}
        outcome = ActionOutcome(
            action=action, moved=moved,
            new_position=Position(x=2, y=2),
            data=data,
        )
        obs = _make_observation(0.3)

        trans = system.transition(state, outcome, obs)
        if trans.terminated:
            state = trans.new_state
            break
        state = trans.new_state

    return state, decision_datas


class TestEpisodeSmokeTest:
    """Construct SystemC with default config, run a 50-step loop."""

    def test_no_crashes(self) -> None:
        config = SystemCConfig(**SystemCConfigBuilder().build())
        system = SystemC(config)
        world = World(
            _make_resource_grid(5, 5, 0.3), Position(x=2, y=2),
        )
        state, _ = _run_episode(system, world, 50)
        assert state is not None

    def test_no_nan_in_energy(self) -> None:
        config = SystemCConfig(**SystemCConfigBuilder().build())
        system = SystemC(config)
        world = World(
            _make_resource_grid(5, 5, 0.3), Position(x=2, y=2),
        )
        state, _ = _run_episode(system, world, 50)
        assert not math.isnan(state.energy)

    def test_vitality_in_range(self) -> None:
        config = SystemCConfig(**SystemCConfigBuilder().build())
        system = SystemC(config)
        world = World(
            _make_resource_grid(5, 5, 0.3), Position(x=2, y=2),
        )
        state, _ = _run_episode(system, world, 50)
        v = system.vitality(state)
        assert 0.0 <= v <= 1.0


class TestTraceAccumulation:
    """After 50 steps, some trace entries should be non-zero."""

    def test_traces_nonzero_after_episode(self) -> None:
        config = SystemCConfig(**SystemCConfigBuilder().build())
        system = SystemC(config)
        world = World(
            _make_resource_grid(5, 5, 0.3), Position(x=2, y=2),
        )
        state, _ = _run_episode(system, world, 50)

        # Check that at least one trace entry is non-zero
        has_nonzero = (
            len(state.trace_state.frustration) > 0
            or len(state.trace_state.confidence) > 0
        )
        assert has_nonzero, "No trace entries after 50 steps"


class TestMemoryConvergence:
    """After 50 steps, some predictive memory entries differ from zero."""

    def test_memory_nonzero_after_episode(self) -> None:
        config = SystemCConfig(**SystemCConfigBuilder().build())
        system = SystemC(config)
        world = World(
            _make_resource_grid(5, 5, 0.3), Position(x=2, y=2),
        )
        state, _ = _run_episode(system, world, 50)

        # At least one memory entry should have moved from the
        # initial zero vector
        has_learned = False
        for (ctx, act), features in state.predictive_memory.entries:
            if any(f != 0.0 for f in features):
                has_learned = True
                break
        assert has_learned, "No memory learning after 50 steps"


class TestPredictionActive:
    """After 20+ steps, prediction should influence behavior."""

    def test_modulation_differs_from_raw(self) -> None:
        config = SystemCConfig(**SystemCConfigBuilder().build())
        system = SystemC(config)
        world = World(
            _make_resource_grid(5, 5, 0.3), Position(x=2, y=2),
        )
        _, decision_datas = _run_episode(system, world, 50)

        # Check steps 20+: at least one step should have modulated
        # scores that differ from raw drive contributions
        found_modulation = False
        for dd in decision_datas[20:]:
            raw = dd["drive"]["action_contributions"]
            modulated = dd["prediction"]["modulated_scores"]
            if any(
                abs(r - m) > 1e-9
                for r, m in zip(raw, modulated)
            ):
                found_modulation = True
                break

        assert found_modulation, (
            "Prediction never influenced behavior after step 20"
        )
