"""WP-8 unit tests -- SoftmaxPolicy."""

from __future__ import annotations

import numpy as np
import pytest

from axis.sdk.types import PolicyResult
from axis.systems.construction_kit.policy.softmax import SoftmaxPolicy
from axis.systems.construction_kit.drives.types import HungerDriveOutput
from axis.systems.construction_kit.observation.types import CellObservation, Observation


def _open_observation() -> Observation:
    cell = CellObservation(traversability=1.0, resource=0.0)
    return Observation(current=cell, up=cell, down=cell, left=cell, right=cell)


def _blocked_left_observation() -> Observation:
    cell = CellObservation(traversability=1.0, resource=0.0)
    blocked = CellObservation(traversability=0.0, resource=0.0)
    return Observation(current=cell, up=cell, down=cell, left=blocked, right=cell)


def _all_blocked_observation() -> Observation:
    cell = CellObservation(traversability=1.0, resource=0.0)
    blocked = CellObservation(traversability=0.0, resource=0.0)
    return Observation(current=cell, up=blocked, down=blocked, left=blocked, right=blocked)


class TestBasicBehavior:
    """Basic policy behavior tests."""

    def test_uniform_scores_equal_probs(self) -> None:
        policy = SoftmaxPolicy(temperature=1.0, selection_mode="sample")
        rng = np.random.default_rng(42)
        scores = (0.5, 0.5, 0.5, 0.5, 0.5, 0.5)
        result = policy.select(scores, _open_observation(), rng)
        probs = result.policy_data["probabilities"]
        for p in probs:
            assert p == pytest.approx(1.0 / 6, abs=0.001)

    def test_high_score_dominates(self) -> None:
        policy = SoftmaxPolicy(temperature=5.0, selection_mode="sample")
        rng = np.random.default_rng(42)
        scores = (0.0, 0.0, 0.0, 0.0, 10.0, 0.0)
        result = policy.select(scores, _open_observation(), rng)
        probs = result.policy_data["probabilities"]
        assert probs[4] > 0.99

    def test_masked_action_zero_prob(self) -> None:
        policy = SoftmaxPolicy(temperature=1.0, selection_mode="sample")
        rng = np.random.default_rng(42)
        scores = (0.5, 0.5, 0.5, 0.5, 0.5, 0.5)
        result = policy.select(scores, _blocked_left_observation(), rng)
        probs = result.policy_data["probabilities"]
        assert probs[2] == 0.0  # LEFT blocked

    def test_consume_stay_always_admissible(self) -> None:
        policy = SoftmaxPolicy(temperature=1.0, selection_mode="sample")
        rng = np.random.default_rng(42)
        scores = (0.5, 0.5, 0.5, 0.5, 0.5, 0.5)
        result = policy.select(scores, _all_blocked_observation(), rng)
        probs = result.policy_data["probabilities"]
        assert probs[4] > 0.0  # CONSUME
        assert probs[5] > 0.0  # STAY
        # All movement blocked
        for i in range(4):
            assert probs[i] == 0.0

    def test_argmax_mode(self) -> None:
        policy = SoftmaxPolicy(temperature=1.0, selection_mode="argmax")
        rng = np.random.default_rng(42)
        scores = (0.1, 0.2, 0.3, 0.9, 0.0, 0.0)
        actions = set()
        for _ in range(10):
            result = policy.select(scores, _open_observation(), rng)
            actions.add(result.action)
        assert len(actions) == 1
        assert "right" in actions

    def test_sample_mode_respects_probs(self) -> None:
        policy = SoftmaxPolicy(temperature=1.0, selection_mode="sample")
        scores = (5.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        counts = [0] * 6
        action_names = ("up", "down", "left", "right", "consume", "stay")
        for seed in range(1000):
            rng = np.random.default_rng(seed)
            result = policy.select(scores, _open_observation(), rng)
            idx = action_names.index(result.action)
            counts[idx] += 1
        # UP should dominate
        assert counts[0] > 500


class TestSystemAEquivalence:
    """System A equivalence test."""

    def test_same_probs_as_system_a(self) -> None:
        scores = (0.3, 0.1, 0.5, 0.2, 0.4, -0.1)
        obs = _open_observation()
        rng_aw = np.random.default_rng(42)
        rng_a = np.random.default_rng(42)

        aw_policy = SoftmaxPolicy(temperature=1.0, selection_mode="sample")
        aw_result = aw_policy.select(scores, obs, rng_aw)

        a_policy = SoftmaxPolicy(temperature=1.0, selection_mode="sample")
        drive_out = HungerDriveOutput(
            activation=0.5, action_contributions=scores)
        a_result = a_policy.select(drive_out.action_contributions, obs, rng_a)

        aw_probs = aw_result.policy_data["probabilities"]
        a_probs = a_result.policy_data["probabilities"]
        for i in range(6):
            assert aw_probs[i] == pytest.approx(a_probs[i], abs=1e-9)


class TestWorkedExamples:
    """Worked example probability verification."""

    def test_example_a1_probabilities(self) -> None:
        """A1: actual scores from arbitration."""
        policy = SoftmaxPolicy(temperature=1.0, selection_mode="sample")
        rng = np.random.default_rng(42)
        scores = (0.405, 0.405, 0.527, 0.405, -0.237, -0.243)
        result = policy.select(scores, _open_observation(), rng)
        probs = result.policy_data["probabilities"]
        assert probs[0] == pytest.approx(0.193, abs=0.02)  # UP
        assert probs[1] == pytest.approx(0.193, abs=0.02)  # DOWN
        assert probs[2] == pytest.approx(0.218, abs=0.02)  # LEFT
        assert probs[3] == pytest.approx(0.193, abs=0.02)  # RIGHT
        assert probs[4] == pytest.approx(0.102, abs=0.02)  # CONSUME
        assert probs[5] == pytest.approx(0.101, abs=0.02)  # STAY

    def test_example_b1_probabilities(self) -> None:
        """B1: LEFT blocked → P(LEFT) = 0."""
        policy = SoftmaxPolicy(temperature=1.0, selection_mode="sample")
        rng = np.random.default_rng(42)
        # B1 approximate scores (from hunger + curiosity combined)
        scores = (0.064, 0.143, 0.074, 0.053, 0.228, -0.088)
        result = policy.select(scores, _blocked_left_observation(), rng)
        probs = result.policy_data["probabilities"]
        assert probs[2] == 0.0  # LEFT blocked
        assert sum(probs) == pytest.approx(1.0)

    def test_example_c1_probabilities(self) -> None:
        """C1: CONSUME dominates."""
        policy = SoftmaxPolicy(temperature=1.0, selection_mode="sample")
        rng = np.random.default_rng(42)
        scores = (0.002, 0.002, 0.002, 0.170, 1.051, -0.085)
        result = policy.select(scores, _open_observation(), rng)
        probs = result.policy_data["probabilities"]
        assert probs[4] > 0.3  # CONSUME dominates


class TestEdgeCases:
    """Edge case tests."""

    def test_all_negative_scores(self) -> None:
        policy = SoftmaxPolicy(temperature=1.0, selection_mode="sample")
        rng = np.random.default_rng(42)
        scores = (-1.0, -2.0, -3.0, -4.0, -5.0, -6.0)
        result = policy.select(scores, _open_observation(), rng)
        probs = result.policy_data["probabilities"]
        assert sum(probs) == pytest.approx(1.0)
        assert all(p >= 0 for p in probs)

    def test_large_score_difference(self) -> None:
        policy = SoftmaxPolicy(temperature=1.0, selection_mode="sample")
        rng = np.random.default_rng(42)
        scores = (10.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        result = policy.select(scores, _open_observation(), rng)
        probs = result.policy_data["probabilities"]
        assert sum(probs) == pytest.approx(1.0)
        assert all(p >= 0 for p in probs)

    def test_policy_result_type(self) -> None:
        policy = SoftmaxPolicy(temperature=1.0, selection_mode="sample")
        rng = np.random.default_rng(42)
        scores = (0.5, 0.5, 0.5, 0.5, 0.5, 0.5)
        result = policy.select(scores, _open_observation(), rng)
        assert isinstance(result, PolicyResult)
        assert result.action in ("up", "down", "left",
                                 "right", "consume", "stay")
        assert "raw_contributions" in result.policy_data
        assert "probabilities" in result.policy_data
