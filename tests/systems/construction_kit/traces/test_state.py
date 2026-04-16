"""Tests for trace state model."""

from __future__ import annotations

import pytest

from axis.systems.construction_kit.traces.state import (
    TraceState,
    create_trace_state,
    get_confidence,
    get_frustration,
)


class TestCreateTraceState:

    def test_empty_frustration(self) -> None:
        state = create_trace_state()
        assert state.frustration == ()

    def test_empty_confidence(self) -> None:
        state = create_trace_state()
        assert state.confidence == ()

    def test_model_is_frozen(self) -> None:
        state = create_trace_state()
        with pytest.raises(Exception):
            state.frustration = ()  # type: ignore[misc]


class TestGetFrustration:

    def test_returns_zero_for_unseen(self) -> None:
        state = create_trace_state()
        assert get_frustration(state, 0, "up") == 0.0

    def test_returns_zero_for_any_pair(self) -> None:
        state = create_trace_state()
        assert get_frustration(state, 31, "stay") == 0.0
        assert get_frustration(state, 15, "consume") == 0.0

    def test_returns_stored_value(self) -> None:
        state = TraceState(
            frustration=(((5, "left"), 0.42),),
            confidence=(),
        )
        assert get_frustration(state, 5, "left") == pytest.approx(0.42)
        assert get_frustration(state, 5, "right") == 0.0


class TestGetConfidence:

    def test_returns_zero_for_unseen(self) -> None:
        state = create_trace_state()
        assert get_confidence(state, 0, "up") == 0.0

    def test_returns_stored_value(self) -> None:
        state = TraceState(
            frustration=(),
            confidence=(((10, "down"), 0.77),),
        )
        assert get_confidence(state, 10, "down") == pytest.approx(0.77)
        assert get_confidence(state, 10, "up") == 0.0
