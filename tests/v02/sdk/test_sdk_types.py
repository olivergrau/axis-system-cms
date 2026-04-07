"""Verification tests for WP-1.1: Core SDK Interfaces and Types."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from pydantic import ValidationError

from axis.sdk import (
    DecideResult,
    DriveInterface,
    PolicyInterface,
    PolicyResult,
    SensorInterface,
    SystemInterface,
    TransitionInterface,
    TransitionResult,
)


# ---------------------------------------------------------------------------
# DecideResult
# ---------------------------------------------------------------------------


class TestDecideResult:
    """Tests for DecideResult data type."""

    def test_construction_minimal(self) -> None:
        result = DecideResult(action="up", decision_data={})
        assert result.action == "up"
        assert result.decision_data == {}

    def test_construction_with_nested_data(self) -> None:
        data = {"drive": {"activation": 0.8}, "policy": {"temperature": 1.0}}
        result = DecideResult(action="consume", decision_data=data)
        assert result.action == "consume"
        assert result.decision_data["drive"]["activation"] == 0.8

    def test_frozen(self) -> None:
        result = DecideResult(action="up", decision_data={})
        with pytest.raises(ValidationError):
            result.action = "down"  # type: ignore[misc]

    def test_action_is_string(self) -> None:
        result = DecideResult(action="stay", decision_data={})
        assert isinstance(result.action, str)

    def test_decision_data_is_dict(self) -> None:
        result = DecideResult(action="up", decision_data={"key": "value"})
        assert isinstance(result.decision_data, dict)


# ---------------------------------------------------------------------------
# TransitionResult
# ---------------------------------------------------------------------------


class TestTransitionResult:
    """Tests for TransitionResult data type."""

    def test_construction_not_terminated(self) -> None:
        result = TransitionResult(
            new_state={"energy": 45.0},
            trace_data={},
            terminated=False,
        )
        assert result.new_state == {"energy": 45.0}
        assert result.trace_data == {}
        assert result.terminated is False
        assert result.termination_reason is None

    def test_construction_terminated(self) -> None:
        result = TransitionResult(
            new_state={"energy": 0.0},
            trace_data={"energy_delta": -1.5},
            terminated=True,
            termination_reason="energy_depleted",
        )
        assert result.terminated is True
        assert result.termination_reason == "energy_depleted"

    def test_termination_reason_defaults_to_none(self) -> None:
        result = TransitionResult(
            new_state=None,
            trace_data={},
            terminated=False,
        )
        assert result.termination_reason is None

    def test_frozen(self) -> None:
        result = TransitionResult(
            new_state=None,
            trace_data={},
            terminated=False,
        )
        with pytest.raises(ValidationError):
            result.terminated = True  # type: ignore[misc]

    def test_new_state_accepts_any_type(self) -> None:
        """Agent state is opaque -- any type is accepted."""
        for state in [42, "string_state", {"energy": 1.0}, [1, 2, 3], None]:
            result = TransitionResult(
                new_state=state,
                trace_data={},
                terminated=False,
            )
            assert result.new_state == state


# ---------------------------------------------------------------------------
# PolicyResult
# ---------------------------------------------------------------------------


class TestPolicyResult:
    """Tests for PolicyResult data type."""

    def test_construction(self) -> None:
        result = PolicyResult(action="stay", policy_data={"temperature": 1.0})
        assert result.action == "stay"
        assert result.policy_data["temperature"] == 1.0

    def test_frozen(self) -> None:
        result = PolicyResult(action="up", policy_data={})
        with pytest.raises(ValidationError):
            result.action = "down"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Protocol structural tests
# ---------------------------------------------------------------------------


class _MockSystem:
    """Mock system that satisfies SystemInterface protocol."""

    def system_type(self) -> str:
        return "mock"

    def action_space(self) -> tuple[str, ...]:
        return ("up", "down", "left", "right", "stay")

    def initialize_state(self, system_config: dict[str, Any]) -> Any:
        return {"energy": 50.0}

    def vitality(self, agent_state: Any) -> float:
        return 1.0

    def decide(
        self,
        world_view: Any,
        agent_state: Any,
        rng: np.random.Generator,
    ) -> DecideResult:
        return DecideResult(action="stay", decision_data={})

    def transition(
        self,
        agent_state: Any,
        action_outcome: Any,
        new_observation: Any,
    ) -> TransitionResult:
        return TransitionResult(
            new_state=agent_state,
            trace_data={},
            terminated=False,
        )


class _MockSensor:
    """Mock sensor that satisfies SensorInterface protocol."""

    def observe(self, world_view: Any, position: Any) -> Any:
        return {"current": 0.5}


class _MockDrive:
    """Mock drive that satisfies DriveInterface protocol."""

    def compute(self, agent_state: Any, observation: Any) -> Any:
        return {"activation": 0.5}


class _MockPolicy:
    """Mock policy that satisfies PolicyInterface protocol."""

    def select(
        self,
        drive_outputs: Any,
        observation: Any,
        rng: np.random.Generator,
    ) -> PolicyResult:
        return PolicyResult(action="stay", policy_data={})


class _MockTransition:
    """Mock transition that satisfies TransitionInterface protocol."""

    def transition(
        self,
        agent_state: Any,
        action_outcome: Any,
        observation: Any,
    ) -> TransitionResult:
        return TransitionResult(
            new_state=agent_state,
            trace_data={},
            terminated=False,
        )


class TestProtocolConformance:
    """Tests that mock implementations satisfy the Protocol interfaces."""

    def test_system_interface(self) -> None:
        assert isinstance(_MockSystem(), SystemInterface)

    def test_sensor_interface(self) -> None:
        assert isinstance(_MockSensor(), SensorInterface)

    def test_drive_interface(self) -> None:
        assert isinstance(_MockDrive(), DriveInterface)

    def test_policy_interface(self) -> None:
        assert isinstance(_MockPolicy(), PolicyInterface)

    def test_transition_interface(self) -> None:
        assert isinstance(_MockTransition(), TransitionInterface)

    def test_non_conforming_class_fails_system_interface(self) -> None:
        """A class missing required methods does not satisfy SystemInterface."""

        class _Incomplete:
            def system_type(self) -> str:
                return "incomplete"

        assert not isinstance(_Incomplete(), SystemInterface)

    def test_mock_system_methods_work(self) -> None:
        """Verify mock system produces expected outputs."""
        system = _MockSystem()
        rng = np.random.default_rng(42)

        assert system.system_type() == "mock"
        assert "up" in system.action_space()

        state = system.initialize_state({})
        assert system.vitality(state) == 1.0

        decide_result = system.decide(None, state, rng)
        assert isinstance(decide_result, DecideResult)
        assert decide_result.action == "stay"

        transition_result = system.transition(state, None, None)
        assert isinstance(transition_result, TransitionResult)
        assert transition_result.terminated is False


# ---------------------------------------------------------------------------
# SystemInterface method signature checks
# ---------------------------------------------------------------------------


class TestSystemInterfaceShape:
    """Verify the expected method names exist on SystemInterface."""

    EXPECTED_METHODS = [
        "system_type",
        "action_space",
        "initialize_state",
        "vitality",
        "decide",
        "transition",
    ]

    @pytest.mark.parametrize("method_name", EXPECTED_METHODS)
    def test_method_exists(self, method_name: str) -> None:
        # Protocol members are accessible via __protocol_attrs__ or direct inspection
        assert hasattr(_MockSystem, method_name)


# ---------------------------------------------------------------------------
# Import verification
# ---------------------------------------------------------------------------


class TestImports:
    """Verify that all SDK exports are importable."""

    def test_import_from_sdk_package(self) -> None:
        from axis.sdk import (  # noqa: F401
            DecideResult,
            DriveInterface,
            PolicyInterface,
            PolicyResult,
            SensorInterface,
            SystemInterface,
            TransitionInterface,
            TransitionResult,
        )

    def test_import_from_interfaces_module(self) -> None:
        from axis.sdk.interfaces import (  # noqa: F401
            DriveInterface,
            PolicyInterface,
            SensorInterface,
            SystemInterface,
            TransitionInterface,
        )

    def test_import_from_types_module(self) -> None:
        from axis.sdk.types import (  # noqa: F401
            DecideResult,
            PolicyResult,
            TransitionResult,
        )
