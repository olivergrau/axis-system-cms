"""End-to-end integration test for the predictive pipeline.

Verifies that prediction, traces, and modulation kit components
compose correctly before building System C on top.
"""

from __future__ import annotations

import pytest

from axis.systems.construction_kit.observation.types import CellObservation, Observation
from axis.systems.construction_kit.prediction.features import extract_predictive_features
from axis.systems.construction_kit.prediction.context import encode_context
from axis.systems.construction_kit.prediction.memory import (
    create_predictive_memory,
    get_prediction,
    update_predictive_memory,
)
from axis.systems.construction_kit.prediction.error import compute_prediction_error
from axis.systems.construction_kit.traces.state import (
    create_trace_state,
    get_confidence,
    get_frustration,
)
from axis.systems.construction_kit.traces.update import update_traces
from axis.systems.construction_kit.modulation.modulation import modulate_action_scores


ACTIONS = ("up", "down", "left", "right", "consume", "stay")
MOD_PARAMS = dict(
    positive_sensitivity=1.0,
    negative_sensitivity=1.5,
    modulation_min=0.3,
    modulation_max=2.0,
    modulation_mode="multiplicative",
    prediction_bias_scale=0.2,
    prediction_bias_clip=1.0,
)


def _obs(c: float, u: float, d: float, l: float, r: float) -> Observation:
    def cell(res: float) -> CellObservation:
        return CellObservation(traversability=1.0, resource=res)
    return Observation(
        current=cell(c), up=cell(u), down=cell(d),
        left=cell(l), right=cell(r),
    )


class TestFullPipelineCycle:
    """Run the complete predictive cycle on synthetic data."""

    def test_single_cycle_no_errors(self) -> None:
        """Full cycle executes without error, all types correct."""
        pre_obs = _obs(0.0, 0.0, 0.0, 0.0, 0.0)
        post_obs = _obs(0.8, 0.0, 0.0, 0.0, 0.3)

        memory = create_predictive_memory()
        traces = create_trace_state()
        base_scores = (0.5, 0.3, 0.1, 0.4, 0.8, -0.2)

        # 1. Extract features + encode context from pre-action obs
        pre_features = extract_predictive_features(pre_obs)
        context = encode_context(pre_features)
        assert isinstance(context, int)
        assert 0 <= context <= 31

        # 2. Get prediction for this (context, action)
        action = "up"
        predicted = get_prediction(memory, context, action)
        assert len(predicted) == 5

        # 3. Extract post-action features
        post_features = extract_predictive_features(post_obs)

        # 4. Compute prediction error
        error = compute_prediction_error(predicted, post_features)
        assert error.scalar_positive >= 0.0
        assert error.scalar_negative >= 0.0

        # 5. Update traces
        new_traces = update_traces(
            traces, context, action,
            error.scalar_positive, error.scalar_negative,
            frustration_rate=0.2, confidence_rate=0.15,
        )
        assert isinstance(new_traces, type(traces))

        # 6. Update memory
        new_memory = update_predictive_memory(
            memory, context, action, post_features,
            learning_rate=0.3,
        )
        assert isinstance(new_memory, type(memory))

        # 7. Modulate scores using updated traces
        modulated = modulate_action_scores(
            base_scores, context, ACTIONS, new_traces, **MOD_PARAMS,
        )
        assert len(modulated) == len(base_scores)


class TestConvergence:
    """Predictive memory converges, error decreases over iterations."""

    def test_memory_converges_and_error_decreases(self) -> None:
        obs = _obs(0.6, 0.0, 0.0, 0.0, 0.4)
        features = extract_predictive_features(obs)
        context = encode_context(features)

        memory = create_predictive_memory()
        traces = create_trace_state()

        prev_error = float("inf")
        for i in range(15):
            predicted = get_prediction(memory, context, "up")
            error = compute_prediction_error(predicted, features)
            total_error = error.scalar_positive + error.scalar_negative

            # Error should decrease monotonically
            if i > 0:
                assert total_error < prev_error + 1e-9
            prev_error = total_error

            traces = update_traces(
                traces, context, "up",
                error.scalar_positive, error.scalar_negative,
                frustration_rate=0.2, confidence_rate=0.15,
            )
            memory = update_predictive_memory(
                memory, context, "up", features, learning_rate=0.3,
            )

        # After 15 iterations, memory should be close to observed
        final_pred = get_prediction(memory, context, "up")
        for a, b in zip(final_pred, features):
            assert a == pytest.approx(b, abs=0.01)

        # Error should be near zero
        final_error = compute_prediction_error(final_pred, features)
        assert final_error.scalar_positive == pytest.approx(0.0, abs=0.01)
        assert final_error.scalar_negative == pytest.approx(0.0, abs=0.01)


class TestNeutralStart:
    """At t=0 with empty traces, modulated scores equal base scores."""

    def test_modulation_neutral_at_start(self) -> None:
        traces = create_trace_state()
        base_scores = (0.5, 0.3, 0.1, 0.4, 0.8, -0.2)

        for context in [0, 15, 31]:
            modulated = modulate_action_scores(
                base_scores, context, ACTIONS, traces, **MOD_PARAMS,
            )
            for a, b in zip(modulated, base_scores):
                assert a == pytest.approx(b)


class TestAsymmetricLearning:
    """Disappointment suppresses, positive surprise reinforces."""

    def test_disappointment_suppresses_action(self) -> None:
        """Repeated negative surprise -> modulated score decreases."""
        memory = create_predictive_memory()
        traces = create_trace_state()

        # Agent expects resources (update memory to expect 0.8)
        context = encode_context((0.8, 0.0, 0.0, 0.0, 0.0))
        for _ in range(5):
            memory = update_predictive_memory(
                memory, context, "consume",
                (0.8, 0.0, 0.0, 0.0, 0.0), learning_rate=0.5,
            )

        # Now deliver disappointment: nothing there
        for _ in range(5):
            predicted = get_prediction(memory, context, "consume")
            error = compute_prediction_error(
                predicted, (0.0, 0.0, 0.0, 0.0, 0.0),
            )
            assert error.scalar_negative > 0.0
            traces = update_traces(
                traces, context, "consume",
                error.scalar_positive, error.scalar_negative,
                frustration_rate=0.2, confidence_rate=0.15,
            )
            memory = update_predictive_memory(
                memory, context, "consume",
                (0.0, 0.0, 0.0, 0.0, 0.0), learning_rate=0.3,
            )

        # Frustration should be positive, confidence zero
        assert get_frustration(traces, context, "consume") > 0.0
        assert get_confidence(traces, context, "consume") == pytest.approx(0.0)

        # Modulated score for "consume" should be suppressed
        base_scores = (1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        modulated = modulate_action_scores(
            base_scores, context, ACTIONS, traces, **MOD_PARAMS,
        )
        consume_idx = ACTIONS.index("consume")
        assert modulated[consume_idx] < 1.0

    def test_positive_surprise_reinforces_action(self) -> None:
        """Repeated positive surprise -> modulated score increases."""
        memory = create_predictive_memory()
        traces = create_trace_state()

        # Memory starts at zero (expects nothing)
        context = encode_context((0.0, 0.0, 0.0, 0.0, 0.0))

        # Deliver positive surprise: resources appear
        for _ in range(5):
            predicted = get_prediction(memory, context, "up")
            error = compute_prediction_error(
                predicted, (0.7, 0.5, 0.0, 0.0, 0.0),
            )
            assert error.scalar_positive > 0.0
            traces = update_traces(
                traces, context, "up",
                error.scalar_positive, error.scalar_negative,
                frustration_rate=0.2, confidence_rate=0.15,
            )
            memory = update_predictive_memory(
                memory, context, "up",
                (0.7, 0.5, 0.0, 0.0, 0.0), learning_rate=0.3,
            )

        # Confidence should be positive
        assert get_confidence(traces, context, "up") > 0.0

        # Modulated score for "up" should be reinforced
        base_scores = (1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        modulated = modulate_action_scores(
            base_scores, context, ACTIONS, traces, **MOD_PARAMS,
        )
        up_idx = ACTIONS.index("up")
        assert modulated[up_idx] > 1.0
