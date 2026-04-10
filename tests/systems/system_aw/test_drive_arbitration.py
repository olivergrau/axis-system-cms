"""WP-7 unit tests -- drive arbitration."""

from __future__ import annotations

import pytest

from axis.systems.system_a.types import HungerDriveOutput
from axis.systems.system_aw.config import ArbitrationConfig
from axis.systems.system_aw.drive_arbitration import (
    compute_action_scores,
    compute_drive_weights,
)
from axis.systems.system_aw.types import CuriosityDriveOutput, DriveWeights


def _default_config(
    hunger_weight_base: float = 0.3,
    curiosity_weight_base: float = 1.0,
    gating_sharpness: float = 2.0,
) -> ArbitrationConfig:
    return ArbitrationConfig(
        hunger_weight_base=hunger_weight_base,
        curiosity_weight_base=curiosity_weight_base,
        gating_sharpness=gating_sharpness,
    )


class TestWeightFunction:
    """Drive weight computation tests."""

    def test_weights_fully_sated(self) -> None:
        w = compute_drive_weights(0.0, _default_config())
        assert w.hunger_weight == pytest.approx(0.3)
        assert w.curiosity_weight == pytest.approx(1.0)

    def test_weights_starving(self) -> None:
        w = compute_drive_weights(1.0, _default_config())
        assert w.hunger_weight == pytest.approx(1.0)
        assert w.curiosity_weight == pytest.approx(0.0)

    def test_weights_half_hunger(self) -> None:
        # d_H=0.5, gamma=2: w_H = 0.3 + 0.7*0.25 = 0.475, w_C = 1.0*0.25 = 0.25
        w = compute_drive_weights(0.5, _default_config())
        assert w.hunger_weight == pytest.approx(0.475)
        assert w.curiosity_weight == pytest.approx(0.250)

    def test_hunger_floor(self) -> None:
        config = _default_config()
        for d_h in [0.0, 0.1, 0.5, 0.9, 1.0]:
            w = compute_drive_weights(d_h, config)
            assert w.hunger_weight >= config.hunger_weight_base

    def test_curiosity_ceiling(self) -> None:
        config = _default_config()
        for d_h in [0.0, 0.1, 0.5, 0.9, 1.0]:
            w = compute_drive_weights(d_h, config)
            assert w.curiosity_weight <= config.curiosity_weight_base + 1e-9

    def test_curiosity_nonneg(self) -> None:
        config = _default_config()
        for d_h in [0.0, 0.1, 0.5, 0.9, 1.0]:
            w = compute_drive_weights(d_h, config)
            assert w.curiosity_weight >= 0.0

    def test_monotonicity_hunger(self) -> None:
        config = _default_config()
        d_h_values = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        w_h_values = [compute_drive_weights(
            d, config).hunger_weight for d in d_h_values]
        for i in range(len(w_h_values) - 1):
            assert w_h_values[i] <= w_h_values[i + 1] + 1e-9

    def test_monotonicity_curiosity(self) -> None:
        config = _default_config()
        d_h_values = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        w_c_values = [compute_drive_weights(
            d, config).curiosity_weight for d in d_h_values]
        for i in range(len(w_c_values) - 1):
            assert w_c_values[i] >= w_c_values[i + 1] - 1e-9


class TestGammaSensitivity:
    """Worked Example E1: gamma sensitivity at d_H=0.5."""

    def test_e1_gamma_0_5(self) -> None:
        w = compute_drive_weights(0.5, _default_config(gating_sharpness=0.5))
        assert w.hunger_weight == pytest.approx(0.795, abs=0.005)
        assert w.curiosity_weight == pytest.approx(0.707, abs=0.005)

    def test_e1_gamma_1_0(self) -> None:
        w = compute_drive_weights(0.5, _default_config(gating_sharpness=1.0))
        assert w.hunger_weight == pytest.approx(0.650, abs=0.005)
        assert w.curiosity_weight == pytest.approx(0.500, abs=0.005)

    def test_e1_gamma_2_0(self) -> None:
        w = compute_drive_weights(0.5, _default_config(gating_sharpness=2.0))
        assert w.hunger_weight == pytest.approx(0.475, abs=0.005)
        assert w.curiosity_weight == pytest.approx(0.250, abs=0.005)

    def test_e1_gamma_4_0(self) -> None:
        w = compute_drive_weights(0.5, _default_config(gating_sharpness=4.0))
        assert w.hunger_weight == pytest.approx(0.344, abs=0.005)
        assert w.curiosity_weight == pytest.approx(0.063, abs=0.005)


def _make_hunger(
    activation: float = 0.5,
    contributions: tuple[float, ...] = (0.1, 0.1, 0.1, 0.1, 0.5, -0.05),
) -> HungerDriveOutput:
    return HungerDriveOutput(
        activation=activation,
        action_contributions=contributions,
    )


def _make_curiosity(
    activation: float = 0.8,
    contributions: tuple[float, ...] = (0.5, 0.5, 0.5, 0.5, -0.3, -0.3),
) -> CuriosityDriveOutput:
    return CuriosityDriveOutput(
        activation=activation,
        spatial_novelty=(1.0, 1.0, 1.0, 1.0),
        sensory_novelty=(0.0, 0.0, 0.0, 0.0),
        composite_novelty=(0.5, 0.5, 0.5, 0.5),
        action_contributions=contributions,
    )


class TestScoreCombination:
    """Action score combination tests."""

    def test_scores_pure_hunger(self) -> None:
        hunger = _make_hunger(activation=0.5, contributions=(
            0.1, 0.2, 0.3, 0.4, 0.5, -0.1))
        curiosity = _make_curiosity(activation=0.0)
        weights = DriveWeights(hunger_weight=1.0, curiosity_weight=1.0)
        scores = compute_action_scores(hunger, curiosity, weights)
        # w_C * d_C = 1.0 * 0.0 = 0, so only hunger contributes
        for i in range(6):
            assert scores[i] == pytest.approx(
                1.0 * 0.5 * hunger.action_contributions[i])

    def test_scores_pure_curiosity(self) -> None:
        hunger = _make_hunger(activation=0.0)
        curiosity = _make_curiosity(
            activation=0.8, contributions=(0.5, 0.4, 0.3, 0.2, -0.3, -0.3))
        weights = DriveWeights(hunger_weight=1.0, curiosity_weight=1.0)
        scores = compute_action_scores(hunger, curiosity, weights)
        for i in range(6):
            assert scores[i] == pytest.approx(
                1.0 * 0.8 * curiosity.action_contributions[i])

    def test_scores_both_drives(self) -> None:
        hunger = _make_hunger(activation=0.5, contributions=(
            0.1, 0.2, 0.3, 0.4, 0.5, -0.1))
        curiosity = _make_curiosity(
            activation=0.8, contributions=(0.6, 0.5, 0.4, 0.3, -0.3, -0.3))
        weights = DriveWeights(hunger_weight=0.5, curiosity_weight=0.7)
        scores = compute_action_scores(hunger, curiosity, weights)
        for i in range(6):
            expected = (
                0.5 * 0.5 * hunger.action_contributions[i]
                + 0.7 * 0.8 * curiosity.action_contributions[i]
            )
            assert scores[i] == pytest.approx(expected)

    def test_scores_tuple_length(self) -> None:
        scores = compute_action_scores(
            _make_hunger(), _make_curiosity(),
            DriveWeights(hunger_weight=0.5, curiosity_weight=0.5),
        )
        assert len(scores) == 6


class TestWorkedExampleWeights:
    """Worked example weight verification."""

    def test_example_a1_weights(self) -> None:
        # d_H=0.10, gamma=2: w_H = 0.3 + 0.7*0.01 = 0.307, w_C = 1.0*0.81 = 0.810
        w = compute_drive_weights(0.10, _default_config())
        assert w.hunger_weight == pytest.approx(0.307, abs=0.005)
        assert w.curiosity_weight == pytest.approx(0.810, abs=0.005)

    def test_example_b1_weights(self) -> None:
        # d_H=0.50, gamma=2: w_H = 0.475, w_C = 0.250
        w = compute_drive_weights(0.50, _default_config())
        assert w.hunger_weight == pytest.approx(0.475, abs=0.005)
        assert w.curiosity_weight == pytest.approx(0.250, abs=0.005)

    def test_example_c1_weights(self) -> None:
        # d_H=0.95, gamma=2: w_H = 0.3 + 0.7*0.9025 = 0.932, w_C = 1.0*0.0025 = 0.003
        w = compute_drive_weights(0.95, _default_config())
        assert w.hunger_weight == pytest.approx(0.932, abs=0.005)
        assert w.curiosity_weight == pytest.approx(0.003, abs=0.005)


class TestWorkedExampleScores:
    """Worked example full score verification."""

    def test_example_a1_scores(self) -> None:
        """A1: d_H=0.10, d_C=1.0, w_H=0.307, w_C=0.810."""
        hunger = HungerDriveOutput(
            activation=0.10,
            action_contributions=(0.0, 0.0, 0.03, 0.0, 0.20, -0.01),
        )
        curiosity = CuriosityDriveOutput(
            activation=1.0,
            spatial_novelty=(1.0, 1.0, 1.0, 1.0),
            sensory_novelty=(0.0, 0.0, 0.3, 0.0),
            composite_novelty=(0.50, 0.50, 0.65, 0.50),
            action_contributions=(0.50, 0.50, 0.65, 0.50, -0.30, -0.30),
        )
        weights = DriveWeights(hunger_weight=0.307, curiosity_weight=0.810)
        scores = compute_action_scores(hunger, curiosity, weights)
        assert scores[0] == pytest.approx(0.405, abs=0.01)   # UP
        assert scores[1] == pytest.approx(0.405, abs=0.01)   # DOWN
        assert scores[2] == pytest.approx(0.527, abs=0.01)   # LEFT
        assert scores[3] == pytest.approx(0.405, abs=0.01)   # RIGHT
        assert scores[4] == pytest.approx(-0.237, abs=0.01)  # CONSUME
        assert scores[5] == pytest.approx(-0.243, abs=0.01)  # STAY

    def test_example_b1_scores(self) -> None:
        """B1: d_H=0.50, d_C=0.85, w_H=0.475, w_C=0.250."""
        hunger = HungerDriveOutput(
            activation=0.50,
            action_contributions=(0.0, 0.20, 0.0, 0.0, 0.75, -0.05),
        )
        curiosity = CuriosityDriveOutput(
            activation=0.85,
            spatial_novelty=(0.50, 0.50, 0.50, 0.50),
            sensory_novelty=(0.1, 0.4, 0.2, 0.0),
            composite_novelty=(0.30, 0.45, 0.35, 0.25),
            action_contributions=(0.30, 0.45, 0.35, 0.25, -0.30, -0.30),
        )
        weights = DriveWeights(hunger_weight=0.475, curiosity_weight=0.250)
        scores = compute_action_scores(hunger, curiosity, weights)
        assert len(scores) == 6
        # DOWN should be the strongest positive movement contribution
        assert scores[1] > scores[0]  # DOWN > UP

    def test_example_c1_scores(self) -> None:
        """C1: d_H=0.95, d_C=1.0, w_H=0.932, w_C=0.003. CONSUME dominates."""
        hunger = HungerDriveOutput(
            activation=0.95,
            action_contributions=(0.0, 0.0, 0.0, 0.19,
                                  0.95 * 2.5 * 0.5, -0.095),
        )
        curiosity = CuriosityDriveOutput(
            activation=1.0,
            spatial_novelty=(1.0, 1.0, 1.0, 1.0),
            sensory_novelty=(0.0, 0.0, 0.0, 0.2),
            composite_novelty=(0.50, 0.50, 0.50, 0.60),
            action_contributions=(0.50, 0.50, 0.50, 0.60, -0.30, -0.30),
        )
        weights = DriveWeights(hunger_weight=0.932, curiosity_weight=0.003)
        scores = compute_action_scores(hunger, curiosity, weights)
        # CONSUME should dominate
        for i in range(4):
            assert scores[4] > scores[i]
        assert scores[4] > 1.0  # Strong consume signal
