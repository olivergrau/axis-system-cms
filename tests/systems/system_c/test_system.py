"""Tests for SystemC class construction and interface conformance."""

from __future__ import annotations

import numpy as np
import pytest

from axis.sdk.interfaces import SystemInterface
from axis.sdk.position import Position
from axis.systems.construction_kit.memory.types import ObservationBuffer
from axis.systems.construction_kit.observation.types import CellObservation, Observation
from axis.systems.construction_kit.prediction.memory import PredictiveMemory
from axis.systems.construction_kit.traces.state import TraceState
from axis.systems.construction_kit.types.actions import handle_consume
from axis.systems.system_c.config import SystemCConfig
from axis.systems.system_c.system import SystemC
from axis.systems.system_c.types import AgentStateC
from tests.builders.system_c_config_builder import SystemCConfigBuilder


@pytest.fixture()
def config_dict() -> dict:
    return SystemCConfigBuilder().build()


@pytest.fixture()
def config(config_dict: dict) -> SystemCConfig:
    return SystemCConfig(**config_dict)


@pytest.fixture()
def system(config: SystemCConfig) -> SystemC:
    return SystemC(config)


class TestSystemCConstruction:
    """SystemC construction and identity."""

    def test_constructs_successfully(self, config: SystemCConfig) -> None:
        system = SystemC(config)
        assert system is not None

    def test_system_type(self, system: SystemC) -> None:
        assert system.system_type() == "system_c"

    def test_action_space(self, system: SystemC) -> None:
        assert system.action_space() == (
            "up", "down", "left", "right", "consume", "stay",
        )


class TestSystemInterfaceConformance:
    """Protocol conformance."""

    def test_system_interface(self, system: SystemC) -> None:
        assert isinstance(system, SystemInterface)


class TestInitializeState:
    """State initialization."""

    def test_returns_agent_state_c(self, system: SystemC) -> None:
        state = system.initialize_state()
        assert isinstance(state, AgentStateC)

    def test_initial_energy(self, system: SystemC) -> None:
        state = system.initialize_state()
        assert state.energy == 50.0

    def test_empty_observation_buffer(self, system: SystemC) -> None:
        state = system.initialize_state()
        assert state.observation_buffer.entries == ()

    def test_buffer_capacity(self, system: SystemC) -> None:
        state = system.initialize_state()
        assert state.observation_buffer.capacity == 5

    def test_zero_predictive_memory(self, system: SystemC) -> None:
        state = system.initialize_state()
        assert isinstance(state.predictive_memory, PredictiveMemory)

    def test_zero_trace_state(self, system: SystemC) -> None:
        state = system.initialize_state()
        assert isinstance(state.trace_state, TraceState)
        assert state.trace_state.frustration == ()
        assert state.trace_state.confidence == ()

    def test_last_observation_none(self, system: SystemC) -> None:
        state = system.initialize_state()
        assert state.last_observation is None


class TestVitality:
    """Normalized vitality."""

    def test_full_energy(self, system: SystemC) -> None:
        state = AgentStateC(
            energy=100.0,
            observation_buffer=ObservationBuffer(entries=(), capacity=5),
            predictive_memory=system.initialize_state().predictive_memory,
            trace_state=system.initialize_state().trace_state,
        )
        assert system.vitality(state) == 1.0

    def test_half_energy(self, system: SystemC) -> None:
        state = AgentStateC(
            energy=50.0,
            observation_buffer=ObservationBuffer(entries=(), capacity=5),
            predictive_memory=system.initialize_state().predictive_memory,
            trace_state=system.initialize_state().trace_state,
        )
        assert system.vitality(state) == 0.5

    def test_zero_energy(self, system: SystemC) -> None:
        state = AgentStateC(
            energy=0.0,
            observation_buffer=ObservationBuffer(entries=(), capacity=5),
            predictive_memory=system.initialize_state().predictive_memory,
            trace_state=system.initialize_state().trace_state,
        )
        assert system.vitality(state) == 0.0


class TestActionHandlers:
    """Action handler registration."""

    def test_returns_consume_handler(self, system: SystemC) -> None:
        handlers = system.action_handlers()
        assert "consume" in handlers
        assert handlers["consume"] is handle_consume

    def test_action_context(self, system: SystemC) -> None:
        ctx = system.action_context()
        assert "max_consume" in ctx
        assert ctx["max_consume"] == 1.0


class TestImportVerification:
    """Package import tests."""

    def test_top_level_imports(self) -> None:
        from axis.systems.system_c import (  # noqa: F401
            PredictionConfig,
            SystemC,
            SystemCConfig,
            handle_consume,
        )
