"""Tests for System C transition with predictive update cycle."""

from __future__ import annotations

import pytest

from axis.sdk.position import Position
from axis.sdk.types import TransitionResult
from axis.sdk.world_types import ActionOutcome
from axis.systems.construction_kit.memory.types import ObservationBuffer
from axis.systems.construction_kit.observation.types import CellObservation, Observation
from axis.systems.construction_kit.prediction.memory import (
    create_predictive_memory,
    get_prediction,
    update_predictive_memory,
)
from axis.systems.construction_kit.traces.state import (
    create_trace_state,
    get_confidence,
    get_frustration,
)
from axis.systems.system_c.config import SystemCConfig
from axis.systems.system_c.transition import SystemCTransition
from axis.systems.system_c.types import AgentStateC
from tests.builders.system_c_config_builder import SystemCConfigBuilder


def _obs(
    c: float = 0.0, u: float = 0.0, d: float = 0.0,
    l: float = 0.0, r: float = 0.0,
) -> Observation:
    def cell(res: float) -> CellObservation:
        return CellObservation(traversability=1.0, resource=res)
    return Observation(
        current=cell(c), up=cell(u), down=cell(d),
        left=cell(l), right=cell(r),
    )


def _config() -> SystemCConfig:
    return SystemCConfig(**SystemCConfigBuilder().build())


def _transition(config: SystemCConfig | None = None) -> SystemCTransition:
    return SystemCTransition(config=config or _config())


def _state(
    energy: float = 50.0,
    last_observation: Observation | None = None,
    memory=None,
    traces=None,
) -> AgentStateC:
    return AgentStateC(
        energy=energy,
        observation_buffer=ObservationBuffer(entries=(), capacity=5),
        predictive_memory=memory or create_predictive_memory(),
        trace_state=traces or create_trace_state(),
        last_observation=last_observation,
    )


def _move_outcome(action: str = "up") -> ActionOutcome:
    return ActionOutcome(
        action=action, moved=True,
        new_position=Position(x=2, y=1),
    )


def _consume_outcome(consumed: float = 0.5) -> ActionOutcome:
    return ActionOutcome(
        action="consume", moved=False,
        new_position=Position(x=2, y=2),
        data={"consumed": True, "resource_consumed": consumed},
    )


def _stay_outcome() -> ActionOutcome:
    return ActionOutcome(
        action="stay", moved=False,
        new_position=Position(x=2, y=2),
    )


# =========================================================================
# Energy update (same as System A)
# =========================================================================


class TestEnergyUpdate:

    def test_movement_costs_energy(self) -> None:
        trans = _transition()
        result = trans.transition(_state(50.0), _move_outcome(), _obs())
        assert result.new_state.energy == 49.0

    def test_consume_gains_energy(self) -> None:
        trans = _transition()
        result = trans.transition(
            _state(50.0), _consume_outcome(0.5), _obs(),
        )
        # 50 - 1.0 (consume_cost) + 10 * 0.5 (gain) = 54.0
        assert result.new_state.energy == 54.0

    def test_energy_clips_at_max(self) -> None:
        trans = _transition()
        result = trans.transition(
            _state(95.0), _consume_outcome(1.0), _obs(),
        )
        # 95 - 1 + 10 = 104 -> clipped to 100
        assert result.new_state.energy == 100.0

    def test_energy_clips_at_zero(self) -> None:
        trans = _transition()
        result = trans.transition(
            _state(0.5), _move_outcome(), _obs(),
        )
        assert result.new_state.energy == 0.0

    def test_stay_cost(self) -> None:
        trans = _transition()
        result = trans.transition(_state(50.0), _stay_outcome(), _obs())
        assert result.new_state.energy == 49.5


# =========================================================================
# Buffer update
# =========================================================================


class TestBufferUpdate:

    def test_observation_appended(self) -> None:
        trans = _transition()
        result = trans.transition(_state(), _stay_outcome(), _obs())
        assert len(result.new_state.observation_buffer.entries) == 1

    def test_buffer_respects_capacity(self) -> None:
        trans = _transition()
        state = _state()
        for i in range(7):
            result = trans.transition(state, _stay_outcome(), _obs())
            state = result.new_state
        # capacity=5
        assert len(state.observation_buffer.entries) == 5


# =========================================================================
# First-step skip (last_observation is None)
# =========================================================================


class TestFirstStepSkip:

    def test_memory_unchanged(self) -> None:
        trans = _transition()
        state = _state(last_observation=None)
        result = trans.transition(state, _move_outcome(), _obs(0.5))
        # Memory should be identical to initial
        assert (
            result.new_state.predictive_memory.entries
            == state.predictive_memory.entries
        )

    def test_traces_unchanged(self) -> None:
        trans = _transition()
        state = _state(last_observation=None)
        result = trans.transition(state, _move_outcome(), _obs(0.5))
        assert result.new_state.trace_state == state.trace_state

    def test_last_observation_set(self) -> None:
        trans = _transition()
        obs = _obs(0.5)
        result = trans.transition(_state(), _move_outcome(), obs)
        assert result.new_state.last_observation == obs

    def test_no_prediction_in_trace_data(self) -> None:
        trans = _transition()
        result = trans.transition(_state(), _move_outcome(), _obs())
        assert "prediction" not in result.trace_data


# =========================================================================
# Predictive update -- memory
# =========================================================================


class TestPredictiveUpdateMemory:

    def test_memory_updated_for_action_pair(self) -> None:
        trans = _transition()
        pre_obs = _obs(0.0)
        post_obs = _obs(0.6, 0.3, 0.0, 0.0, 0.0)
        state = _state(last_observation=pre_obs)

        result = trans.transition(state, _move_outcome("up"), post_obs)

        # Pre-obs is all zeros -> context = 0
        pred = get_prediction(
            result.new_state.predictive_memory, 0, "up",
        )
        # Memory should have moved toward post features
        assert pred[0] > 0.0  # center was 0, observed 0.6

    def test_other_pairs_unchanged(self) -> None:
        trans = _transition()
        pre_obs = _obs(0.0)
        post_obs = _obs(0.6)
        state = _state(last_observation=pre_obs)

        result = trans.transition(state, _move_outcome("up"), post_obs)

        # context=0, action="down" should still be zero
        pred = get_prediction(
            result.new_state.predictive_memory, 0, "down",
        )
        assert all(v == 0.0 for v in pred)


# =========================================================================
# Predictive update -- traces
# =========================================================================


class TestPredictiveUpdateTraces:

    def test_positive_surprise_increases_confidence(self) -> None:
        """Observed > predicted -> positive error -> confidence increases."""
        trans = _transition()
        pre_obs = _obs(0.0)
        post_obs = _obs(0.8, 0.5, 0.0, 0.0, 0.0)
        state = _state(last_observation=pre_obs)

        result = trans.transition(state, _move_outcome("up"), post_obs)
        # context=0, action="up"
        c = get_confidence(result.new_state.trace_state, 0, "up")
        assert c > 0.0

    def test_negative_surprise_increases_frustration(self) -> None:
        """Predicted > observed -> negative error -> frustration increases."""
        trans = _transition()
        # Train memory to expect resources
        memory = create_predictive_memory()
        for _ in range(5):
            memory = update_predictive_memory(
                memory, 0, "up", (0.8, 0.0, 0.0, 0.0, 0.0),
                learning_rate=0.5,
            )
        pre_obs = _obs(0.0)  # context=0
        post_obs = _obs(0.0)  # nothing there -> disappointment
        state = _state(last_observation=pre_obs, memory=memory)

        result = trans.transition(state, _move_outcome("up"), post_obs)
        f = get_frustration(result.new_state.trace_state, 0, "up")
        assert f > 0.0


# =========================================================================
# Prediction trace data
# =========================================================================


class TestPredictionTraceData:

    def test_trace_data_contains_prediction(self) -> None:
        trans = _transition()
        pre_obs = _obs(0.0)
        post_obs = _obs(0.5)
        state = _state(last_observation=pre_obs)

        result = trans.transition(state, _move_outcome("up"), post_obs)
        assert "prediction" in result.trace_data

    def test_prediction_trace_data_keys(self) -> None:
        trans = _transition()
        pre_obs = _obs(0.0)
        post_obs = _obs(0.5)
        state = _state(last_observation=pre_obs)

        result = trans.transition(state, _move_outcome("up"), post_obs)
        pred = result.trace_data["prediction"]
        assert "context" in pred
        assert "predicted_features" in pred
        assert "observed_features" in pred
        assert "error_positive" in pred
        assert "error_negative" in pred


# =========================================================================
# last_observation lifecycle
# =========================================================================


class TestLastObservationLifecycle:

    def test_set_after_transition(self) -> None:
        trans = _transition()
        obs = _obs(0.7, 0.3, 0.0, 0.0, 0.0)
        result = trans.transition(_state(), _move_outcome(), obs)
        assert result.new_state.last_observation == obs

    def test_chains_across_transitions(self) -> None:
        trans = _transition()
        obs1 = _obs(0.3)
        obs2 = _obs(0.6)
        state = _state()

        r1 = trans.transition(state, _move_outcome(), obs1)
        assert r1.new_state.last_observation == obs1

        r2 = trans.transition(r1.new_state, _move_outcome(), obs2)
        assert r2.new_state.last_observation == obs2


# =========================================================================
# Multi-step sequence
# =========================================================================


class TestMultiStep:

    def test_three_step_convergence(self) -> None:
        """Run 3 transitions; memory converges, traces accumulate."""
        trans = _transition()
        state = _state()
        obs_seq = [_obs(0.0), _obs(0.5), _obs(0.5), _obs(0.5)]

        # Step 0: no last_observation
        r = trans.transition(state, _move_outcome("up"), obs_seq[0])
        state = r.new_state
        assert state.last_observation == obs_seq[0]

        # Steps 1-3: predictive update active
        for i in range(1, 4):
            r = trans.transition(
                state, _move_outcome("up"), obs_seq[min(i, 3)])
            state = r.new_state

        # After 3 predictive updates with consistent observations,
        # memory should have moved toward the observed features
        pred = get_prediction(state.predictive_memory, 0, "up")
        assert pred[0] > 0.0  # should have learned something


# =========================================================================
# Termination
# =========================================================================


class TestTermination:

    def test_terminated_at_zero_energy(self) -> None:
        trans = _transition()
        result = trans.transition(_state(1.0), _move_outcome(), _obs())
        assert result.new_state.energy == 0.0
        assert result.terminated is True
        assert result.termination_reason == "energy_depleted"

    def test_not_terminated_with_energy(self) -> None:
        trans = _transition()
        result = trans.transition(_state(50.0), _stay_outcome(), _obs())
        assert result.terminated is False
        assert result.termination_reason is None

    def test_returns_transition_result(self) -> None:
        trans = _transition()
        result = trans.transition(_state(), _stay_outcome(), _obs())
        assert isinstance(result, TransitionResult)
