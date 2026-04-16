"""Tests for System C decide() pipeline."""

from __future__ import annotations

import numpy as np
import pytest

from axis.sdk.position import Position
from axis.sdk.types import DecideResult
from axis.systems.construction_kit.memory.types import ObservationBuffer
from axis.systems.construction_kit.observation.types import CellObservation, Observation
from axis.systems.construction_kit.prediction.memory import create_predictive_memory
from axis.systems.construction_kit.traces.state import create_trace_state
from axis.systems.construction_kit.traces.update import update_traces
from axis.systems.system_c.config import SystemCConfig
from axis.systems.system_c.system import SystemC
from axis.systems.system_c.types import AgentStateC
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


@pytest.fixture()
def config() -> SystemCConfig:
    return SystemCConfig(**SystemCConfigBuilder().build())


@pytest.fixture()
def system(config: SystemCConfig) -> SystemC:
    return SystemC(config)


@pytest.fixture()
def initial_state(system: SystemC) -> AgentStateC:
    return system.initialize_state()


@pytest.fixture()
def resource_world() -> World:
    grid = _make_resource_grid(5, 5, 0.5)
    return World(grid, Position(x=2, y=2))


@pytest.fixture()
def rng() -> np.random.Generator:
    return np.random.default_rng(42)


class TestDecideFreshState:
    """Decide with fresh (zero-trace) state."""

    def test_returns_decide_result(
        self, system: SystemC, resource_world: World,
        initial_state: AgentStateC, rng: np.random.Generator,
    ) -> None:
        result = system.decide(resource_world, initial_state, rng)
        assert isinstance(result, DecideResult)

    def test_action_in_action_space(
        self, system: SystemC, resource_world: World,
        initial_state: AgentStateC, rng: np.random.Generator,
    ) -> None:
        result = system.decide(resource_world, initial_state, rng)
        assert result.action in system.action_space()

    def test_decision_data_keys(
        self, system: SystemC, resource_world: World,
        initial_state: AgentStateC, rng: np.random.Generator,
    ) -> None:
        result = system.decide(resource_world, initial_state, rng)
        assert "observation" in result.decision_data
        assert "drive" in result.decision_data
        assert "prediction" in result.decision_data
        assert "policy" in result.decision_data

    def test_prediction_data_keys(
        self, system: SystemC, resource_world: World,
        initial_state: AgentStateC, rng: np.random.Generator,
    ) -> None:
        result = system.decide(resource_world, initial_state, rng)
        pred = result.decision_data["prediction"]
        assert "context" in pred
        assert "features" in pred
        assert "modulated_scores" in pred

    def test_zero_traces_neutral_modulation(
        self, system: SystemC, resource_world: World,
        initial_state: AgentStateC, rng: np.random.Generator,
    ) -> None:
        """With zero traces, modulated scores equal raw action contributions."""
        result = system.decide(resource_world, initial_state, rng)
        drive_contributions = result.decision_data["drive"]["action_contributions"]
        modulated = result.decision_data["prediction"]["modulated_scores"]
        for raw, mod in zip(drive_contributions, modulated):
            assert raw == pytest.approx(mod)


class TestDecideWithTraces:
    """Decide with non-zero traces injected."""

    def test_nonzero_traces_change_scores(
        self, system: SystemC, resource_world: World, rng: np.random.Generator,
    ) -> None:
        """With frustration traces, modulated scores differ from raw."""
        state = system.initialize_state()

        # Inject frustration on context 31 (all resources above 0.5),
        # action "up"
        traces = state.trace_state
        for _ in range(5):
            traces = update_traces(
                traces, context=31, action="up",
                scalar_positive=0.0, scalar_negative=1.0,
                frustration_rate=0.5, confidence_rate=0.5,
            )

        state_with_traces = AgentStateC(
            energy=state.energy,
            observation_buffer=state.observation_buffer,
            predictive_memory=state.predictive_memory,
            trace_state=traces,
            last_observation=state.last_observation,
        )

        result = system.decide(resource_world, state_with_traces, rng)
        drive_contributions = result.decision_data["drive"]["action_contributions"]
        modulated = result.decision_data["prediction"]["modulated_scores"]

        # The resource world has all cells at 0.5, so context will be 31
        # (all >= 0.5). "up" should be suppressed.
        up_idx = 0
        assert modulated[up_idx] != pytest.approx(drive_contributions[up_idx])
        assert abs(modulated[up_idx]) < abs(drive_contributions[up_idx])

    def test_positive_confidence_makes_negative_stay_penalty_less_negative(
        self, system: SystemC, resource_world: World, rng: np.random.Generator,
    ) -> None:
        state = system.initialize_state()
        traces = state.trace_state
        for _ in range(5):
            traces = update_traces(
                traces, context=31, action="stay",
                scalar_positive=1.0, scalar_negative=0.0,
                frustration_rate=0.5, confidence_rate=0.5,
            )

        state_with_traces = AgentStateC(
            energy=state.energy,
            observation_buffer=state.observation_buffer,
            predictive_memory=state.predictive_memory,
            trace_state=traces,
            last_observation=state.last_observation,
        )

        result = system.decide(resource_world, state_with_traces, rng)
        raw = result.decision_data["drive"]["action_contributions"]
        modulated = result.decision_data["prediction"]["modulated_scores"]

        stay_idx = 5
        assert raw[stay_idx] < 0.0
        assert modulated[stay_idx] > raw[stay_idx]

    def test_frustration_makes_negative_stay_penalty_more_negative(
        self, system: SystemC, resource_world: World, rng: np.random.Generator,
    ) -> None:
        state = system.initialize_state()
        traces = state.trace_state
        for _ in range(5):
            traces = update_traces(
                traces, context=31, action="stay",
                scalar_positive=0.0, scalar_negative=1.0,
                frustration_rate=0.5, confidence_rate=0.5,
            )

        state_with_traces = AgentStateC(
            energy=state.energy,
            observation_buffer=state.observation_buffer,
            predictive_memory=state.predictive_memory,
            trace_state=traces,
            last_observation=state.last_observation,
        )

        result = system.decide(resource_world, state_with_traces, rng)
        raw = result.decision_data["drive"]["action_contributions"]
        modulated = result.decision_data["prediction"]["modulated_scores"]

        stay_idx = 5
        assert raw[stay_idx] < 0.0
        assert modulated[stay_idx] < raw[stay_idx]
