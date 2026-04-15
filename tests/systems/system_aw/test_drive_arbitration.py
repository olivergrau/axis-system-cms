"""WP-7 unit tests -- drive arbitration."""

from __future__ import annotations

import pytest

from axis.systems.construction_kit.arbitration.scoring import combine_drive_scores
from axis.systems.construction_kit.arbitration.types import DriveWeights
from axis.systems.construction_kit.arbitration.weights import compute_maslow_weights


def _default_weights(
    hunger_weight_base: float = 0.3,
    curiosity_weight_base: float = 1.0,
    gating_sharpness: float = 2.0,
) -> dict[str, float]:
    return dict(
        primary_weight_base=hunger_weight_base,
        secondary_weight_base=curiosity_weight_base,
        gating_sharpness=gating_sharpness,
    )


class TestWeightFunction:
    """Drive weight computation tests."""

    def test_weights_fully_sated(self) -> None:
        w = compute_maslow_weights(0.0, **_default_weights())
        assert w.hunger_weight == pytest.approx(0.3)
        assert w.curiosity_weight == pytest.approx(1.0)

    def test_weights_starving(self) -> None:
        w = compute_maslow_weights(1.0, **_default_weights())
        assert w.hunger_weight == pytest.approx(1.0)
        assert w.curiosity_weight == pytest.approx(0.0)

    def test_weights_half_hunger(self) -> None:
        # d_H=0.5, gamma=2: w_H = 0.3 + 0.7*0.25 = 0.475, w_C = 1.0*0.25 = 0.25
        w = compute_maslow_weights(0.5, **_default_weights())
        assert w.hunger_weight == pytest.approx(0.475)
        assert w.curiosity_weight == pytest.approx(0.250)

    def test_hunger_floor(self) -> None:
        params = _default_weights()
        for d_h in [0.0, 0.1, 0.5, 0.9, 1.0]:
            w = compute_maslow_weights(d_h, **params)
            assert w.hunger_weight >= params["primary_weight_base"]

    def test_curiosity_ceiling(self) -> None:
        params = _default_weights()
        for d_h in [0.0, 0.1, 0.5, 0.9, 1.0]:
            w = compute_maslow_weights(d_h, **params)
            assert w.curiosity_weight <= params["secondary_weight_base"] + 1e-9

    def test_curiosity_nonneg(self) -> None:
        params = _default_weights()
        for d_h in [0.0, 0.1, 0.5, 0.9, 1.0]:
            w = compute_maslow_weights(d_h, **params)
            assert w.curiosity_weight >= 0.0

    def test_monotonicity_hunger(self) -> None:
        params = _default_weights()
        d_h_values = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        w_h_values = [compute_maslow_weights(
            d, **params).hunger_weight for d in d_h_values]
        for i in range(len(w_h_values) - 1):
            assert w_h_values[i] <= w_h_values[i + 1] + 1e-9

    def test_monotonicity_curiosity(self) -> None:
        params = _default_weights()
        d_h_values = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        w_c_values = [compute_maslow_weights(
            d, **params).curiosity_weight for d in d_h_values]
        for i in range(len(w_c_values) - 1):
            assert w_c_values[i] >= w_c_values[i + 1] - 1e-9


class TestGammaSensitivity:
    """Worked Example E1: gamma sensitivity at d_H=0.5."""

    def test_e1_gamma_0_5(self) -> None:
        w = compute_maslow_weights(
            0.5, **_default_weights(gating_sharpness=0.5))
        assert w.hunger_weight == pytest.approx(0.795, abs=0.005)
        assert w.curiosity_weight == pytest.approx(0.707, abs=0.005)

    def test_e1_gamma_1_0(self) -> None:
        w = compute_maslow_weights(
            0.5, **_default_weights(gating_sharpness=1.0))
        assert w.hunger_weight == pytest.approx(0.650, abs=0.005)
        assert w.curiosity_weight == pytest.approx(0.500, abs=0.005)

    def test_e1_gamma_2_0(self) -> None:
        w = compute_maslow_weights(
            0.5, **_default_weights(gating_sharpness=2.0))
        assert w.hunger_weight == pytest.approx(0.475, abs=0.005)
        assert w.curiosity_weight == pytest.approx(0.250, abs=0.005)

    def test_e1_gamma_4_0(self) -> None:
        w = compute_maslow_weights(
            0.5, **_default_weights(gating_sharpness=4.0))
        assert w.hunger_weight == pytest.approx(0.344, abs=0.005)
        assert w.curiosity_weight == pytest.approx(0.063, abs=0.005)


class TestScoreCombination:
    """Action score combination tests."""

    def test_scores_pure_hunger(self) -> None:
        h_contributions = (0.1, 0.2, 0.3, 0.4, 0.5, -0.1)
        c_contributions = (0.5, 0.5, 0.5, 0.5, -0.3, -0.3)
        h_activation = 0.5
        c_activation = 0.0
        weights = DriveWeights(hunger_weight=1.0, curiosity_weight=1.0)
        scores = combine_drive_scores(
            drive_contributions=[h_contributions, c_contributions],
            drive_activations=[h_activation, c_activation],
            drive_weights=[weights.hunger_weight, weights.curiosity_weight],
        )
        # w_C * d_C = 1.0 * 0.0 = 0, so only hunger contributes
        for i in range(6):
            assert scores[i] == pytest.approx(
                1.0 * 0.5 * h_contributions[i])

    def test_scores_pure_curiosity(self) -> None:
        h_contributions = (0.1, 0.1, 0.1, 0.1, 0.5, -0.05)
        c_contributions = (0.5, 0.4, 0.3, 0.2, -0.3, -0.3)
        h_activation = 0.0
        c_activation = 0.8
        weights = DriveWeights(hunger_weight=1.0, curiosity_weight=1.0)
        scores = combine_drive_scores(
            drive_contributions=[h_contributions, c_contributions],
            drive_activations=[h_activation, c_activation],
            drive_weights=[weights.hunger_weight, weights.curiosity_weight],
        )
        for i in range(6):
            assert scores[i] == pytest.approx(
                1.0 * 0.8 * c_contributions[i])

    def test_scores_both_drives(self) -> None:
        h_contributions = (0.1, 0.2, 0.3, 0.4, 0.5, -0.1)
        c_contributions = (0.6, 0.5, 0.4, 0.3, -0.3, -0.3)
        h_activation = 0.5
        c_activation = 0.8
        weights = DriveWeights(hunger_weight=0.5, curiosity_weight=0.7)
        scores = combine_drive_scores(
            drive_contributions=[h_contributions, c_contributions],
            drive_activations=[h_activation, c_activation],
            drive_weights=[weights.hunger_weight, weights.curiosity_weight],
        )
        for i in range(6):
            expected = (
                0.5 * 0.5 * h_contributions[i]
                + 0.7 * 0.8 * c_contributions[i]
            )
            assert scores[i] == pytest.approx(expected)

    def test_scores_tuple_length(self) -> None:
        scores = combine_drive_scores(
            drive_contributions=[
                (0.1, 0.1, 0.1, 0.1, 0.5, -0.05),
                (0.5, 0.5, 0.5, 0.5, -0.3, -0.3),
            ],
            drive_activations=[0.5, 0.8],
            drive_weights=[0.5, 0.5],
        )
        assert len(scores) == 6


class TestWorkedExampleWeights:
    """Worked example weight verification."""

    def test_example_a1_weights(self) -> None:
        # d_H=0.10, gamma=2: w_H = 0.3 + 0.7*0.01 = 0.307, w_C = 1.0*0.81 = 0.810
        w = compute_maslow_weights(0.10, **_default_weights())
        assert w.hunger_weight == pytest.approx(0.307, abs=0.005)
        assert w.curiosity_weight == pytest.approx(0.810, abs=0.005)

    def test_example_b1_weights(self) -> None:
        # d_H=0.50, gamma=2: w_H = 0.475, w_C = 0.250
        w = compute_maslow_weights(0.50, **_default_weights())
        assert w.hunger_weight == pytest.approx(0.475, abs=0.005)
        assert w.curiosity_weight == pytest.approx(0.250, abs=0.005)

    def test_example_c1_weights(self) -> None:
        # d_H=0.95, gamma=2: w_H = 0.3 + 0.7*0.9025 = 0.932, w_C = 1.0*0.0025 = 0.003
        w = compute_maslow_weights(0.95, **_default_weights())
        assert w.hunger_weight == pytest.approx(0.932, abs=0.005)
        assert w.curiosity_weight == pytest.approx(0.003, abs=0.005)


class TestWorkedExampleScores:
    """Worked example full score verification."""

    def test_example_a1_scores(self) -> None:
        """A1: d_H=0.10, d_C=1.0, w_H=0.307, w_C=0.810."""
        h_contributions = (0.0, 0.0, 0.03, 0.0, 0.20, -0.01)
        c_contributions = (0.50, 0.50, 0.65, 0.50, -0.30, -0.30)
        weights = DriveWeights(hunger_weight=0.307, curiosity_weight=0.810)
        scores = combine_drive_scores(
            drive_contributions=[h_contributions, c_contributions],
            drive_activations=[0.10, 1.0],
            drive_weights=[weights.hunger_weight, weights.curiosity_weight],
        )
        assert scores[0] == pytest.approx(0.405, abs=0.01)   # UP
        assert scores[1] == pytest.approx(0.405, abs=0.01)   # DOWN
        assert scores[2] == pytest.approx(0.527, abs=0.01)   # LEFT
        assert scores[3] == pytest.approx(0.405, abs=0.01)   # RIGHT
        assert scores[4] == pytest.approx(-0.237, abs=0.01)  # CONSUME
        assert scores[5] == pytest.approx(-0.243, abs=0.01)  # STAY

    def test_example_b1_scores(self) -> None:
        """B1: d_H=0.50, d_C=0.85, w_H=0.475, w_C=0.250."""
        h_contributions = (0.0, 0.20, 0.0, 0.0, 0.75, -0.05)
        c_contributions = (0.30, 0.45, 0.35, 0.25, -0.30, -0.30)
        weights = DriveWeights(hunger_weight=0.475, curiosity_weight=0.250)
        scores = combine_drive_scores(
            drive_contributions=[h_contributions, c_contributions],
            drive_activations=[0.50, 0.85],
            drive_weights=[weights.hunger_weight, weights.curiosity_weight],
        )
        assert len(scores) == 6
        # DOWN should be the strongest positive movement contribution
        assert scores[1] > scores[0]  # DOWN > UP

    def test_example_c1_scores(self) -> None:
        """C1: d_H=0.95, d_C=1.0, w_H=0.932, w_C=0.003. CONSUME dominates."""
        h_contributions = (0.0, 0.0, 0.0, 0.19, 0.95 * 2.5 * 0.5, -0.095)
        c_contributions = (0.50, 0.50, 0.50, 0.60, -0.30, -0.30)
        weights = DriveWeights(hunger_weight=0.932, curiosity_weight=0.003)
        scores = combine_drive_scores(
            drive_contributions=[h_contributions, c_contributions],
            drive_activations=[0.95, 1.0],
            drive_weights=[weights.hunger_weight, weights.curiosity_weight],
        )
        # CONSUME should dominate
        for i in range(4):
            assert scores[4] > scores[i]
        assert scores[4] > 1.0  # Strong consume signal
