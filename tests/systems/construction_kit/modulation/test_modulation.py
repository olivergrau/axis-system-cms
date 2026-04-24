"""Tests for action score modulation."""

from __future__ import annotations

import math

import pytest

from axis.systems.construction_kit.modulation.modulation import (
    compute_prediction_bias,
    describe_action_modulation,
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

    def test_additive_mode_can_move_zero_score(self) -> None:
        state = create_trace_state()
        for _ in range(4):
            state = update_traces(
                state, context=5, action="up",
                scalar_positive=1.0, scalar_negative=0.0,
                frustration_rate=0.5, confidence_rate=0.5,
            )
        scores = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        result = modulate_action_scores(
            scores, context=5, actions=self.ACTIONS, trace_state=state,
            modulation_mode="additive",
            prediction_bias_scale=0.2,
            prediction_bias_clip=1.0,
            **self.PARAMS,
        )
        assert result[0] > 0.0

    def test_hybrid_mode_combines_multiplicative_and_additive(self) -> None:
        state = create_trace_state()
        for _ in range(4):
            state = update_traces(
                state, context=5, action="up",
                scalar_positive=1.0, scalar_negative=0.0,
                frustration_rate=0.5, confidence_rate=0.5,
            )
        details = describe_action_modulation(
            (0.5, 0.0, 0.0, 0.0, 0.0, 0.0),
            context=5,
            actions=self.ACTIONS,
            trace_state=state,
            modulation_mode="hybrid",
            prediction_bias_scale=0.2,
            prediction_bias_clip=1.0,
            **self.PARAMS,
        )
        assert details.modulation_factors[0] > 1.0
        assert details.prediction_biases[0] > 0.0
        assert details.final_scores[0] > 0.5


class TestPredictionBias:

    def test_zero_signal_gives_zero_bias(self) -> None:
        delta = compute_prediction_bias(
            frustration=0.0,
            confidence=0.0,
            positive_sensitivity=1.0,
            negative_sensitivity=1.5,
            prediction_bias_clip=1.0,
        )
        assert delta == pytest.approx(0.0)

    def test_positive_confidence_gives_positive_bias(self) -> None:
        delta = compute_prediction_bias(
            frustration=0.0,
            confidence=0.5,
            positive_sensitivity=1.0,
            negative_sensitivity=1.5,
            prediction_bias_clip=1.0,
        )
        assert delta > 0.0

    def test_negative_signal_clips_symmetrically(self) -> None:
        delta = compute_prediction_bias(
            frustration=10.0,
            confidence=0.0,
            positive_sensitivity=1.0,
            negative_sensitivity=1.5,
            prediction_bias_clip=0.5,
        )
        assert delta == pytest.approx(-0.5)
