"""Tests for System C agent state type."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from axis.systems.construction_kit.memory.types import ObservationBuffer
from axis.systems.construction_kit.observation.types import CellObservation, Observation
from axis.systems.construction_kit.prediction.memory import (
    PredictiveMemory,
    create_predictive_memory,
)
from axis.systems.construction_kit.traces.state import TraceState, create_trace_state
from axis.systems.system_c.types import AgentStateC


def _make_observation() -> Observation:
    cell = CellObservation(traversability=1.0, resource=0.5)
    return Observation(
        current=cell, up=cell, down=cell, left=cell, right=cell,
    )


class TestAgentStateC:
    """AgentStateC model tests."""

    def test_construction(self) -> None:
        state = AgentStateC(
            energy=50.0,
            observation_buffer=ObservationBuffer(entries=(), capacity=5),
            predictive_memory=create_predictive_memory(),
            trace_state=create_trace_state(),
        )
        assert state.energy == 50.0

    def test_contains_all_fields(self) -> None:
        state = AgentStateC(
            energy=50.0,
            observation_buffer=ObservationBuffer(entries=(), capacity=5),
            predictive_memory=create_predictive_memory(),
            trace_state=create_trace_state(),
        )
        assert hasattr(state, "energy")
        assert hasattr(state, "observation_buffer")
        assert hasattr(state, "predictive_memory")
        assert hasattr(state, "trace_state")
        assert hasattr(state, "last_observation")

    def test_last_observation_defaults_to_none(self) -> None:
        state = AgentStateC(
            energy=50.0,
            observation_buffer=ObservationBuffer(entries=(), capacity=5),
            predictive_memory=create_predictive_memory(),
            trace_state=create_trace_state(),
        )
        assert state.last_observation is None

    def test_last_observation_accepts_observation(self) -> None:
        obs = _make_observation()
        state = AgentStateC(
            energy=50.0,
            observation_buffer=ObservationBuffer(entries=(), capacity=5),
            predictive_memory=create_predictive_memory(),
            trace_state=create_trace_state(),
            last_observation=obs,
        )
        assert state.last_observation is obs

    def test_frozen(self) -> None:
        state = AgentStateC(
            energy=50.0,
            observation_buffer=ObservationBuffer(entries=(), capacity=5),
            predictive_memory=create_predictive_memory(),
            trace_state=create_trace_state(),
        )
        with pytest.raises(ValidationError):
            state.energy = 99.0  # type: ignore[misc]

    def test_accepts_predictive_memory(self) -> None:
        mem = create_predictive_memory()
        state = AgentStateC(
            energy=50.0,
            observation_buffer=ObservationBuffer(entries=(), capacity=5),
            predictive_memory=mem,
            trace_state=create_trace_state(),
        )
        assert isinstance(state.predictive_memory, PredictiveMemory)

    def test_accepts_trace_state(self) -> None:
        traces = create_trace_state()
        state = AgentStateC(
            energy=50.0,
            observation_buffer=ObservationBuffer(entries=(), capacity=5),
            predictive_memory=create_predictive_memory(),
            trace_state=traces,
        )
        assert isinstance(state.trace_state, TraceState)

    def test_energy_ge_zero(self) -> None:
        with pytest.raises(ValidationError):
            AgentStateC(
                energy=-1.0,
                observation_buffer=ObservationBuffer(entries=(), capacity=5),
                predictive_memory=create_predictive_memory(),
                trace_state=create_trace_state(),
            )
