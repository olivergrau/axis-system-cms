"""Tests for action score modulation."""

from __future__ import annotations

import math

import pytest

from axis.systems.construction_kit.modulation.modulation import (
    compute_modulation,
    modulate_action_scores,
)
from axis.systems.construction_kit.traces.state import TraceState, create_trace_state
from axis.systems.construction_kit.traces.update import update_traces


class TestComputeModulation:

    def test_zero_traces_gives_one(self) -> None:
        mu = compute_modulation(
            frustration=0.0, confidence=0.0,
            positive_sensitivity=1.0, negative_sensitivity=1.5,
            modulation_min=0.3, modulation_max=2.0,
        )
        assert mu == pytest.approx(1.0)

    def test_pure_frustration_suppresses(self) -> None:
        mu = compute_modulation(
            frustration=0.5, confidence=0.0,
            positive_sensitivity=1.0, negative_sensitivity=1.5,
            modulation_min=0.3, modulation_max=2.0,
        )
        assert mu < 1.0
        expected = math.exp(-1.5 * 0.5)
        assert mu == pytest.approx(expected)

    def test_pure_confidence_reinforces(self) -> None:
        mu = compute_modulation(
            frustration=0.0, confidence=0.5,
            positive_sensitivity=1.0, negative_sensitivity=1.5,
            modulation_min=0.3, modulation_max=2.0,
        )
        assert mu > 1.0
        expected = math.exp(1.0 * 0.5)
        assert mu == pytest.approx(expected)

    def test_clips_at_minimum(self) -> None:
        mu = compute_modulation(
            frustration=10.0, confidence=0.0,
            positive_sensitivity=1.0, negative_sensitivity=1.5,
            modulation_min=0.3, modulation_max=2.0,
        )
        assert mu == pytest.approx(0.3)

    def test_clips_at_maximum(self) -> None:
        mu = compute_modulation(
            frustration=0.0, confidence=10.0,
            positive_sensitivity=1.0, negative_sensitivity=1.5,
            modulation_min=0.3, modulation_max=2.0,
        )
        assert mu == pytest.approx(2.0)

    def test_lambda_zero_gives_one_regardless(self) -> None:
        """Reduction property: lambda_+ = lambda_- = 0 -> mu = 1."""
        mu = compute_modulation(
            frustration=5.0, confidence=3.0,
            positive_sensitivity=0.0, negative_sensitivity=0.0,
            modulation_min=0.3, modulation_max=2.0,
        )
        assert mu == pytest.approx(1.0)

    def test_numerical_check(self) -> None:
        """Exact value: f=0.5, c=0.3, lam+=1.0, lam-=1.5."""
        mu = compute_modulation(
            frustration=0.5, confidence=0.3,
            positive_sensitivity=1.0, negative_sensitivity=1.5,
            modulation_min=0.3, modulation_max=2.0,
        )
        expected = math.exp(1.0 * 0.3 - 1.5 * 0.5)
        assert mu == pytest.approx(expected)

    def test_symmetry_cancellation(self) -> None:
        """Equal and opposing traces with equal sensitivity cancel."""
        mu = compute_modulation(
            frustration=0.5, confidence=0.5,
            positive_sensitivity=1.0, negative_sensitivity=1.0,
            modulation_min=0.3, modulation_max=2.0,
        )
        assert mu == pytest.approx(1.0)


class TestModulateActionScores:

    ACTIONS = ("up", "down", "left", "right", "consume", "stay")
    PARAMS = dict(
        positive_sensitivity=1.0,
        negative_sensitivity=1.5,
        modulation_min=0.3,
        modulation_max=2.0,
    )

    def test_empty_traces_no_change(self) -> None:
        scores = (0.5, 0.3, 0.1, 0.4, 0.8, -0.2)
        state = create_trace_state()
        result = modulate_action_scores(
            scores, context=0, actions=self.ACTIONS,
            trace_state=state, **self.PARAMS,
        )
        for a, b in zip(result, scores):
            assert a == pytest.approx(b)

    def test_output_length_matches_input(self) -> None:
        scores = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0)
        state = create_trace_state()
        result = modulate_action_scores(
            scores, context=0, actions=self.ACTIONS,
            trace_state=state, **self.PARAMS,
        )
        assert len(result) == len(scores)

    def test_nonzero_trace_changes_score(self) -> None:
        """With frustration on 'up', that action's score decreases."""
        state = create_trace_state()
        state = update_traces(
            state, context=5, action="up",
            scalar_positive=0.0, scalar_negative=1.0,
            frustration_rate=0.5, confidence_rate=0.5,
        )
        scores = (1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        result = modulate_action_scores(
            scores, context=5, actions=self.ACTIONS,
            trace_state=state, **self.PARAMS,
        )
        # "up" is index 0, should be suppressed
        assert result[0] < 1.0
        # Others unchanged (no trace for them at context 5)
        assert result[1] == pytest.approx(1.0)
        assert result[2] == pytest.approx(1.0)

    def test_negative_base_scores(self) -> None:
        """Negative base scores are still multiplied correctly."""
        scores = (-0.5, -0.5, -0.5, -0.5, -0.5, -0.5)
        state = create_trace_state()
        result = modulate_action_scores(
            scores, context=0, actions=self.ACTIONS,
            trace_state=state, **self.PARAMS,
        )
        for a, b in zip(result, scores):
            assert a == pytest.approx(b)

    def test_different_context_no_effect(self) -> None:
        """Traces at context 5 don't affect scores at context 10."""
        state = create_trace_state()
        state = update_traces(
            state, context=5, action="up",
            scalar_positive=0.0, scalar_negative=1.0,
            frustration_rate=0.5, confidence_rate=0.5,
        )
        scores = (1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        result = modulate_action_scores(
            scores, context=10, actions=self.ACTIONS,
            trace_state=state, **self.PARAMS,
        )
        for a, b in zip(result, scores):
            assert a == pytest.approx(b)
