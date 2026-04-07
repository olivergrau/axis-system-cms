"""Tests validating the MockSystem conforms to SystemInterface (WP-3.6)."""

from __future__ import annotations

import numpy as np

from axis.sdk.interfaces import SystemInterface
from axis.sdk.types import DecideResult, TransitionResult
from tests.v02.framework.mock_system import MockSystem


class TestMockSystemConformance:
    """Verify MockSystem satisfies SystemInterface protocol."""

    def test_conforms_to_system_interface(self) -> None:
        mock = MockSystem()
        assert isinstance(mock, SystemInterface)

    def test_system_type(self) -> None:
        assert MockSystem().system_type() == "mock"

    def test_action_space(self) -> None:
        actions = MockSystem().action_space()
        assert isinstance(actions, tuple)
        for a in ("up", "down", "left", "right", "stay"):
            assert a in actions

    def test_initialize_state(self) -> None:
        state = MockSystem().initialize_state()
        assert isinstance(state, dict)
        assert "energy" in state
        assert state["energy"] == 10.0

    def test_initialize_state_custom_energy(self) -> None:
        state = MockSystem({"initial_energy": 25.0}).initialize_state()
        assert state["energy"] == 25.0

    def test_vitality(self) -> None:
        mock = MockSystem({"initial_energy": 8.0, "max_energy": 10.0})
        state = mock.initialize_state()
        assert mock.vitality(state) == 0.8

    def test_vitality_zero(self) -> None:
        mock = MockSystem()
        assert mock.vitality({"energy": 0.0}) == 0.0

    def test_decide(self) -> None:
        mock = MockSystem()
        state = mock.initialize_state()
        rng = np.random.default_rng(42)
        result = mock.decide(None, state, rng)
        assert isinstance(result, DecideResult)
        assert result.action == "right"
        assert "reason" in result.decision_data

    def test_transition_energy_decreases(self) -> None:
        mock = MockSystem()
        state = {"energy": 5.0}
        result = mock.transition(state, None, None)
        assert isinstance(result, TransitionResult)
        assert result.new_state["energy"] == 4.0
        assert result.terminated is False

    def test_transition_termination(self) -> None:
        mock = MockSystem()
        state = {"energy": 1.0}
        result = mock.transition(state, None, None)
        assert result.new_state["energy"] == 0.0
        assert result.terminated is True
        assert result.termination_reason == "energy_depleted"

    def test_observe(self) -> None:
        from axis.sdk.position import Position

        mock = MockSystem()
        obs = mock.observe(None, Position(x=3, y=7))
        assert obs == {"position": (3, 7)}

    def test_action_handlers_empty(self) -> None:
        assert MockSystem().action_handlers() == {}

    def test_action_context_empty(self) -> None:
        assert MockSystem().action_context() == {}
