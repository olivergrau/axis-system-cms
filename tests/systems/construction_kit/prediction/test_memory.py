"""Tests for predictive memory."""

from __future__ import annotations

import pytest

from axis.systems.construction_kit.prediction.memory import (
    PredictiveMemory,
    create_predictive_memory,
    get_prediction,
    update_predictive_memory,
)


class TestCreatePredictiveMemory:

    def test_default_entry_count(self) -> None:
        mem = create_predictive_memory()
        assert len(mem.entries) == 32 * 6  # 192

    def test_all_entries_zero(self) -> None:
        mem = create_predictive_memory()
        for _key, val in mem.entries:
            assert val == (0.0, 0.0, 0.0, 0.0, 0.0)

    def test_custom_dimensions(self) -> None:
        mem = create_predictive_memory(
            num_contexts=4, actions=("a", "b"), feature_dim=3,
        )
        assert len(mem.entries) == 4 * 2  # 8
        assert mem.feature_dim == 3
        for _key, val in mem.entries:
            assert val == (0.0, 0.0, 0.0)

    def test_feature_dim_stored(self) -> None:
        mem = create_predictive_memory(feature_dim=7)
        assert mem.feature_dim == 7


class TestGetPrediction:

    def test_returns_zero_for_fresh_memory(self) -> None:
        mem = create_predictive_memory()
        pred = get_prediction(mem, context=0, action="up")
        assert pred == (0.0, 0.0, 0.0, 0.0, 0.0)

    def test_returns_zero_for_unseen_pair(self) -> None:
        mem = create_predictive_memory(
            num_contexts=2, actions=("up",), feature_dim=3,
        )
        pred = get_prediction(mem, context=99, action="unknown")
        assert pred == (0.0, 0.0, 0.0)

    def test_returns_correct_length(self) -> None:
        mem = create_predictive_memory(feature_dim=3)
        pred = get_prediction(mem, 0, "up")
        assert len(pred) == 3


class TestUpdatePredictiveMemory:

    def test_full_replacement_at_eta_1(self) -> None:
        mem = create_predictive_memory()
        observed = (0.5, 0.6, 0.7, 0.8, 0.9)
        new_mem = update_predictive_memory(
            mem, context=5, action="up", observed_features=observed,
            learning_rate=1.0,
        )
        pred = get_prediction(new_mem, 5, "up")
        for a, b in zip(pred, observed):
            assert a == pytest.approx(b)

    def test_midpoint_at_eta_0_5(self) -> None:
        mem = create_predictive_memory()
        observed = (1.0, 1.0, 1.0, 1.0, 1.0)
        new_mem = update_predictive_memory(
            mem, context=0, action="stay", observed_features=observed,
            learning_rate=0.5,
        )
        pred = get_prediction(new_mem, 0, "stay")
        for v in pred:
            assert v == pytest.approx(0.5)

    def test_only_updated_pair_changes(self) -> None:
        mem = create_predictive_memory()
        observed = (1.0, 1.0, 1.0, 1.0, 1.0)
        new_mem = update_predictive_memory(
            mem, context=3, action="left", observed_features=observed,
            learning_rate=0.3,
        )
        # Updated pair changed
        pred_updated = get_prediction(new_mem, 3, "left")
        assert pred_updated != (0.0, 0.0, 0.0, 0.0, 0.0)
        # Other pairs unchanged
        pred_other = get_prediction(new_mem, 3, "right")
        assert pred_other == (0.0, 0.0, 0.0, 0.0, 0.0)
        pred_other2 = get_prediction(new_mem, 0, "left")
        assert pred_other2 == (0.0, 0.0, 0.0, 0.0, 0.0)

    def test_sequential_updates_converge(self) -> None:
        mem = create_predictive_memory()
        target = (0.8, 0.8, 0.8, 0.8, 0.8)
        for _ in range(20):
            mem = update_predictive_memory(
                mem, context=0, action="up", observed_features=target,
                learning_rate=0.3,
            )
        pred = get_prediction(mem, 0, "up")
        for v in pred:
            assert v == pytest.approx(0.8, abs=0.01)

    def test_immutability(self) -> None:
        mem = create_predictive_memory()
        new_mem = update_predictive_memory(
            mem, 0, "up", (1.0, 1.0, 1.0, 1.0, 1.0), learning_rate=0.5,
        )
        # Original unchanged
        orig = get_prediction(mem, 0, "up")
        assert orig == (0.0, 0.0, 0.0, 0.0, 0.0)
        # New has the update
        updated = get_prediction(new_mem, 0, "up")
        assert updated != (0.0, 0.0, 0.0, 0.0, 0.0)

    def test_model_is_frozen(self) -> None:
        mem = create_predictive_memory()
        with pytest.raises(Exception):
            mem.feature_dim = 99  # type: ignore[misc]
