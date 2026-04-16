"""Tests for prediction error computation."""

from __future__ import annotations

import pytest

from axis.systems.construction_kit.prediction.error import (
    PredictionError,
    compute_prediction_error,
)


class TestComputePredictionError:

    def test_perfect_prediction_all_zeros(self) -> None:
        err = compute_prediction_error(
            predicted=(0.5, 0.5, 0.5, 0.5, 0.5),
            observed=(0.5, 0.5, 0.5, 0.5, 0.5),
        )
        assert err.positive == (0.0, 0.0, 0.0, 0.0, 0.0)
        assert err.negative == (0.0, 0.0, 0.0, 0.0, 0.0)
        assert err.scalar_positive == pytest.approx(0.0)
        assert err.scalar_negative == pytest.approx(0.0)

    def test_positive_surprise_only(self) -> None:
        err = compute_prediction_error(
            predicted=(0.0, 0.0, 0.0, 0.0, 0.0),
            observed=(1.0, 1.0, 1.0, 1.0, 1.0),
        )
        assert err.positive == (1.0, 1.0, 1.0, 1.0, 1.0)
        assert err.negative == (0.0, 0.0, 0.0, 0.0, 0.0)
        assert err.scalar_positive == pytest.approx(1.0)
        assert err.scalar_negative == pytest.approx(0.0)

    def test_negative_surprise_only(self) -> None:
        err = compute_prediction_error(
            predicted=(1.0, 1.0, 1.0, 1.0, 1.0),
            observed=(0.0, 0.0, 0.0, 0.0, 0.0),
        )
        assert err.positive == (0.0, 0.0, 0.0, 0.0, 0.0)
        assert err.negative == (1.0, 1.0, 1.0, 1.0, 1.0)
        assert err.scalar_positive == pytest.approx(0.0)
        assert err.scalar_negative == pytest.approx(1.0)

    def test_mixed_surprise(self) -> None:
        err = compute_prediction_error(
            predicted=(0.5, 0.5, 0.5, 0.5, 0.5),
            observed=(0.8, 0.2, 0.5, 0.9, 0.1),
        )
        assert err.positive[0] == pytest.approx(0.3)  # center: 0.8 - 0.5
        assert err.negative[0] == pytest.approx(0.0)
        assert err.positive[1] == pytest.approx(0.0)
        assert err.negative[1] == pytest.approx(0.3)  # up: 0.5 - 0.2
        assert err.positive[2] == pytest.approx(0.0)  # down: exact
        assert err.negative[2] == pytest.approx(0.0)

    def test_center_heavy_aggregation(self) -> None:
        """Center weight (0.5) dominates the scalar aggregation."""
        err = compute_prediction_error(
            predicted=(0.0, 0.0, 0.0, 0.0, 0.0),
            observed=(1.0, 0.0, 0.0, 0.0, 0.0),  # only center has surprise
        )
        assert err.scalar_positive == pytest.approx(0.5)  # 0.5 * 1.0

    def test_neighbor_aggregation(self) -> None:
        """Each neighbor contributes 0.125 to the scalar."""
        err = compute_prediction_error(
            predicted=(0.0, 0.0, 0.0, 0.0, 0.0),
            observed=(0.0, 1.0, 0.0, 0.0, 0.0),  # only up has surprise
        )
        assert err.scalar_positive == pytest.approx(0.125)

    def test_custom_weights(self) -> None:
        err = compute_prediction_error(
            predicted=(0.0, 0.0, 0.0, 0.0, 0.0),
            observed=(1.0, 1.0, 1.0, 1.0, 1.0),
            positive_weights=(0.2, 0.2, 0.2, 0.2, 0.2),
            negative_weights=(1.0, 0.0, 0.0, 0.0, 0.0),
        )
        assert err.scalar_positive == pytest.approx(1.0)  # uniform: 5 * 0.2

    def test_model_is_frozen(self) -> None:
        err = compute_prediction_error(
            predicted=(0.0,), observed=(1.0,),
            positive_weights=(1.0,), negative_weights=(1.0,),
        )
        with pytest.raises(Exception):
            err.scalar_positive = 99.0  # type: ignore[misc]
