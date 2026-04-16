"""Tests for trace update function."""

from __future__ import annotations

import pytest

from axis.systems.construction_kit.traces.state import (
    create_trace_state,
    get_confidence,
    get_frustration,
)
from axis.systems.construction_kit.traces.update import update_traces


class TestUpdateTraces:

    def test_first_frustration_update(self) -> None:
        state = create_trace_state()
        new_state = update_traces(
            state, context=0, action="up",
            scalar_positive=0.0, scalar_negative=1.0,
            frustration_rate=0.2, confidence_rate=0.15,
        )
        assert get_frustration(new_state, 0, "up") == pytest.approx(0.2)

    def test_first_confidence_update(self) -> None:
        state = create_trace_state()
        new_state = update_traces(
            state, context=0, action="up",
            scalar_positive=1.0, scalar_negative=0.0,
            frustration_rate=0.2, confidence_rate=0.15,
        )
        assert get_confidence(new_state, 0, "up") == pytest.approx(0.15)

    def test_accumulation_ema(self) -> None:
        """Two updates: EMA accumulation."""
        state = create_trace_state()
        # First update
        state = update_traces(
            state, 0, "up", scalar_positive=0.0, scalar_negative=1.0,
            frustration_rate=0.2, confidence_rate=0.15,
        )
        # f = 0.2
        # Second update
        state = update_traces(
            state, 0, "up", scalar_positive=0.0, scalar_negative=1.0,
            frustration_rate=0.2, confidence_rate=0.15,
        )
        # f = 0.8 * 0.2 + 0.2 * 1.0 = 0.36
        assert get_frustration(state, 0, "up") == pytest.approx(0.36)

    def test_decay_toward_zero(self) -> None:
        """With zero error signals, traces decay."""
        state = create_trace_state()
        # Build up frustration
        state = update_traces(
            state, 0, "up", scalar_positive=0.0, scalar_negative=1.0,
            frustration_rate=0.5, confidence_rate=0.5,
        )
        assert get_frustration(state, 0, "up") == pytest.approx(0.5)
        # Decay with zero signal
        state = update_traces(
            state, 0, "up", scalar_positive=0.0, scalar_negative=0.0,
            frustration_rate=0.5, confidence_rate=0.5,
        )
        assert get_frustration(state, 0, "up") == pytest.approx(0.25)

    def test_only_specified_pair_changes(self) -> None:
        state = create_trace_state()
        # Update (0, "up")
        state = update_traces(
            state, 0, "up", scalar_positive=1.0, scalar_negative=1.0,
            frustration_rate=0.2, confidence_rate=0.15,
        )
        # Other pairs still zero
        assert get_frustration(state, 0, "down") == 0.0
        assert get_confidence(state, 0, "down") == 0.0
        assert get_frustration(state, 1, "up") == 0.0

    def test_both_traces_updated_simultaneously(self) -> None:
        state = create_trace_state()
        new_state = update_traces(
            state, 5, "left",
            scalar_positive=0.8, scalar_negative=0.6,
            frustration_rate=0.2, confidence_rate=0.15,
        )
        assert get_frustration(
            new_state, 5, "left") == pytest.approx(0.2 * 0.6)
        assert get_confidence(
            new_state, 5, "left") == pytest.approx(0.15 * 0.8)

    def test_immutability(self) -> None:
        state = create_trace_state()
        new_state = update_traces(
            state, 0, "up", scalar_positive=1.0, scalar_negative=1.0,
            frustration_rate=0.5, confidence_rate=0.5,
        )
        # Original unchanged
        assert get_frustration(state, 0, "up") == 0.0
        assert get_confidence(state, 0, "up") == 0.0
        # New state has values
        assert get_frustration(new_state, 0, "up") == pytest.approx(0.5)
        assert get_confidence(new_state, 0, "up") == pytest.approx(0.5)

    def test_multiple_pairs_independent(self) -> None:
        state = create_trace_state()
        state = update_traces(
            state, 0, "up", scalar_positive=1.0, scalar_negative=0.0,
            frustration_rate=0.2, confidence_rate=0.15,
        )
        state = update_traces(
            state, 1, "down", scalar_positive=0.0, scalar_negative=1.0,
            frustration_rate=0.2, confidence_rate=0.15,
        )
        # First pair: confidence only
        assert get_confidence(state, 0, "up") == pytest.approx(0.15)
        assert get_frustration(state, 0, "up") == 0.0
        # Second pair: frustration only
        assert get_frustration(state, 1, "down") == pytest.approx(0.2)
        assert get_confidence(state, 1, "down") == 0.0
