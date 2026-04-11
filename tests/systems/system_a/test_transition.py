"""WP-2.4 unit tests -- SystemATransition."""

from __future__ import annotations

from typing import Any

import pytest

from axis.sdk.interfaces import TransitionInterface
from axis.sdk.position import Position
from axis.sdk.types import TransitionResult
from axis.sdk.world_types import ActionOutcome
from axis.systems.system_a.transition import SystemATransition
from axis.systems.system_a.types import (
    AgentState,
    CellObservation,
    BufferEntry,
    ObservationBuffer,
    Observation,
)


def _make_transition(
    max_energy: float = 100.0,
    move_cost: float = 1.0,
    consume_cost: float = 1.0,
    stay_cost: float = 0.5,
    energy_gain_factor: float = 10.0,
) -> SystemATransition:
    return SystemATransition(
        max_energy=max_energy,
        move_cost=move_cost,
        consume_cost=consume_cost,
        stay_cost=stay_cost,
        energy_gain_factor=energy_gain_factor,
    )


def _make_state(energy: float = 50.0, buffer_capacity: int = 5) -> AgentState:
    return AgentState(
        energy=energy,
        observation_buffer=ObservationBuffer(entries=(), capacity=buffer_capacity),
    )


def _make_observation() -> Observation:
    cell = CellObservation(traversability=1.0, resource=0.0)
    return Observation(current=cell, up=cell, down=cell, left=cell, right=cell)


def _make_outcome(
    action: str = "stay",
    moved: bool = False,
    consumed: bool = False,
    resource_consumed: float = 0.0,
) -> ActionOutcome:
    data: dict[str, Any] = {}
    if consumed or resource_consumed > 0.0:
        data = {"consumed": consumed, "resource_consumed": resource_consumed}
    return ActionOutcome(
        action=action,
        moved=moved,
        new_position=Position(x=2, y=2),
        data=data,
    )


class TestTransition:
    """SystemATransition unit tests."""

    def test_movement_costs_energy(self) -> None:
        trans = _make_transition()
        result = trans.transition(
            _make_state(50.0),
            _make_outcome("up", moved=True),
            _make_observation(),
        )
        assert result.new_state.energy == 49.0

    def test_consume_costs_energy_and_gains(self) -> None:
        trans = _make_transition()
        result = trans.transition(
            _make_state(50.0),
            _make_outcome("consume", consumed=True, resource_consumed=0.5),
            _make_observation(),
        )
        # 50 - 1.0 + 10 * 0.5 = 54.0
        assert result.new_state.energy == 54.0

    def test_stay_costs_energy(self) -> None:
        trans = _make_transition()
        result = trans.transition(
            _make_state(50.0),
            _make_outcome("stay"),
            _make_observation(),
        )
        assert result.new_state.energy == 49.5

    def test_energy_clipped_to_max(self) -> None:
        trans = _make_transition(max_energy=100.0)
        result = trans.transition(
            _make_state(95.0),
            _make_outcome("consume", consumed=True, resource_consumed=1.0),
            _make_observation(),
        )
        # 95 - 1 + 10 = 104 -> clipped to 100
        assert result.new_state.energy == 100.0

    def test_energy_clipped_to_zero(self) -> None:
        trans = _make_transition(move_cost=1.0)
        result = trans.transition(
            _make_state(0.5),
            _make_outcome("up", moved=True),
            _make_observation(),
        )
        assert result.new_state.energy == 0.0

    def test_termination_on_zero_energy(self) -> None:
        trans = _make_transition()
        result = trans.transition(
            _make_state(1.0),
            _make_outcome("up", moved=True),
            _make_observation(),
        )
        assert result.new_state.energy == 0.0
        assert result.terminated is True
        assert result.termination_reason == "energy_depleted"

    def test_no_termination_above_zero(self) -> None:
        trans = _make_transition()
        result = trans.transition(
            _make_state(50.0),
            _make_outcome("stay"),
            _make_observation(),
        )
        assert result.terminated is False
        assert result.termination_reason is None

    def test_observation_buffer_updated(self) -> None:
        trans = _make_transition()
        result = trans.transition(
            _make_state(50.0),
            _make_outcome("stay"),
            _make_observation(),
        )
        assert len(result.new_state.observation_buffer.entries) == 1

    def test_observation_buffer_fifo(self) -> None:
        trans = _make_transition()
        obs = _make_observation()
        # Build state with full observation buffer (capacity=2, 2 entries)
        mem_obs = _make_observation()
        entries = (
            BufferEntry(timestep=0, observation=mem_obs),
            BufferEntry(timestep=1, observation=mem_obs),
        )
        state = AgentState(
            energy=50.0,
            observation_buffer=ObservationBuffer(entries=entries, capacity=2),
        )
        result = trans.transition(state, _make_outcome("stay"), obs)
        buf = result.new_state.observation_buffer
        assert len(buf.entries) == 2
        # Oldest (timestep=0) should be evicted
        assert buf.entries[0].timestep == 1

    def test_returns_transition_result(self) -> None:
        trans = _make_transition()
        result = trans.transition(
            _make_state(), _make_outcome(), _make_observation(),
        )
        assert isinstance(result, TransitionResult)

    def test_trace_data_contains_energy_fields(self) -> None:
        trans = _make_transition()
        result = trans.transition(
            _make_state(), _make_outcome(), _make_observation(),
        )
        assert "energy_before" in result.trace_data
        assert "energy_after" in result.trace_data
        assert "energy_delta" in result.trace_data
        assert "action_cost" in result.trace_data
        assert "energy_gain" in result.trace_data

    def test_trace_data_contains_buffer_snapshot(self) -> None:
        trans = _make_transition()
        result = trans.transition(
            _make_state(), _make_outcome(), _make_observation(),
        )
        assert "buffer_snapshot" in result.trace_data
        assert "buffer_capacity" in result.trace_data
        snapshot = result.trace_data["buffer_snapshot"]
        assert isinstance(snapshot, list)
        assert len(snapshot) == result.trace_data["buffer_entries_after"]
        # Each entry has the expected keys
        if snapshot:
            entry = snapshot[0]
            assert "timestep" in entry
            assert "current_res" in entry
            assert "up_res" in entry
            assert "current_trav" in entry

    def test_new_state_is_agent_state(self) -> None:
        trans = _make_transition()
        result = trans.transition(
            _make_state(), _make_outcome(), _make_observation(),
        )
        assert isinstance(result.new_state, AgentState)

    def test_transition_interface_conformance(self) -> None:
        trans = _make_transition()
        assert isinstance(trans, TransitionInterface)
