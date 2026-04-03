"""Tests for the hunger drive module."""

import inspect

import pytest
from pydantic import ValidationError

from axis_system_a import (
    Action,
    HungerDriveOutput,
    compute_hunger_drive,
)
from tests.fixtures.observation_fixtures import make_observation


# --- Hunger activation tests ---


class TestHungerActivation:
    def test_max_energy_zero_activation(self):
        obs = make_observation()
        result = compute_hunger_drive(
            energy=100.0, max_energy=100.0, observation=obs,
            consume_weight=1.0, stay_suppression=0.0,
        )
        assert result.activation == 0.0

    def test_zero_energy_max_activation(self):
        obs = make_observation()
        result = compute_hunger_drive(
            energy=0.0, max_energy=100.0, observation=obs,
            consume_weight=1.0, stay_suppression=0.0,
        )
        assert result.activation == 1.0

    def test_half_energy(self):
        obs = make_observation()
        result = compute_hunger_drive(
            energy=50.0, max_energy=100.0, observation=obs,
            consume_weight=1.0, stay_suppression=0.0,
        )
        assert result.activation == pytest.approx(0.5)

    def test_quarter_energy(self):
        obs = make_observation()
        result = compute_hunger_drive(
            energy=25.0, max_energy=100.0, observation=obs,
            consume_weight=1.0, stay_suppression=0.0,
        )
        assert result.activation == pytest.approx(0.75)

    def test_activation_bounded_above_max(self):
        obs = make_observation()
        result = compute_hunger_drive(
            energy=100.1, max_energy=100.0, observation=obs,
            consume_weight=1.0, stay_suppression=0.0,
        )
        assert 0.0 <= result.activation <= 1.0


# --- Movement contribution tests ---


class TestMovementContributions:
    def test_movement_from_observation(self):
        obs = make_observation(up=0.8, down=0.6, left=0.4, right=0.2)
        result = compute_hunger_drive(
            energy=50.0, max_energy=100.0, observation=obs,
            consume_weight=1.0, stay_suppression=0.0,
        )
        d_h = 0.5
        assert result.action_contributions[Action.UP] == pytest.approx(
            d_h * 0.8)
        assert result.action_contributions[Action.DOWN] == pytest.approx(
            d_h * 0.6)
        assert result.action_contributions[Action.LEFT] == pytest.approx(
            d_h * 0.4)
        assert result.action_contributions[Action.RIGHT] == pytest.approx(
            d_h * 0.2)

    def test_equal_neighbors_equal_contributions(self):
        obs = make_observation(up=0.5, down=0.5, left=0.5, right=0.5)
        result = compute_hunger_drive(
            energy=50.0, max_energy=100.0, observation=obs,
            consume_weight=1.0, stay_suppression=0.0,
        )
        contributions = result.action_contributions
        assert contributions[Action.UP] == contributions[Action.DOWN]
        assert contributions[Action.DOWN] == contributions[Action.LEFT]
        assert contributions[Action.LEFT] == contributions[Action.RIGHT]

    def test_zero_resource_zero_contribution(self):
        obs = make_observation()
        result = compute_hunger_drive(
            energy=0.0, max_energy=100.0, observation=obs,
            consume_weight=1.0, stay_suppression=0.0,
        )
        assert result.action_contributions[Action.UP] == 0.0
        assert result.action_contributions[Action.DOWN] == 0.0
        assert result.action_contributions[Action.LEFT] == 0.0
        assert result.action_contributions[Action.RIGHT] == 0.0

    def test_action_ordering_matches_enum(self):
        obs = make_observation(up=0.1, down=0.2, left=0.3, right=0.4, current=0.5)
        result = compute_hunger_drive(
            energy=0.0, max_energy=100.0, observation=obs,
            consume_weight=1.0, stay_suppression=0.0,
        )
        assert result.action_contributions[0] == pytest.approx(0.1)  # UP
        assert result.action_contributions[1] == pytest.approx(0.2)  # DOWN
        assert result.action_contributions[2] == pytest.approx(0.3)  # LEFT
        assert result.action_contributions[3] == pytest.approx(0.4)  # RIGHT


# --- Consume contribution tests ---


class TestConsumeContribution:
    def test_consume_with_resource(self):
        obs = make_observation(current=0.6)
        result = compute_hunger_drive(
            energy=50.0, max_energy=100.0, observation=obs,
            consume_weight=1.5, stay_suppression=0.0,
        )
        assert result.action_contributions[Action.CONSUME] == pytest.approx(
            0.45)

    def test_consume_weight_applied(self):
        obs = make_observation(current=0.5)
        r1 = compute_hunger_drive(
            energy=0.0, max_energy=100.0, observation=obs,
            consume_weight=1.0, stay_suppression=0.0,
        )
        r2 = compute_hunger_drive(
            energy=0.0, max_energy=100.0, observation=obs,
            consume_weight=2.0, stay_suppression=0.0,
        )
        assert r2.action_contributions[Action.CONSUME] == pytest.approx(
            2.0 * r1.action_contributions[Action.CONSUME]
        )

    def test_consume_zero_resource(self):
        obs = make_observation(current=0.0)
        result = compute_hunger_drive(
            energy=0.0, max_energy=100.0, observation=obs,
            consume_weight=10.0, stay_suppression=0.0,
        )
        assert result.action_contributions[Action.CONSUME] == 0.0


# --- Stay contribution tests ---


class TestStayContribution:
    def test_stay_negative_or_zero(self):
        obs = make_observation()
        result = compute_hunger_drive(
            energy=50.0, max_energy=100.0, observation=obs,
            consume_weight=1.0, stay_suppression=0.5,
        )
        assert result.action_contributions[Action.STAY] <= 0.0

    def test_stay_stronger_at_higher_hunger(self):
        obs = make_observation()
        r_full = compute_hunger_drive(
            energy=0.0, max_energy=100.0, observation=obs,
            consume_weight=1.0, stay_suppression=1.0,
        )
        r_half = compute_hunger_drive(
            energy=50.0, max_energy=100.0, observation=obs,
            consume_weight=1.0, stay_suppression=1.0,
        )
        assert r_full.action_contributions[Action.STAY] == pytest.approx(-1.0)
        assert r_half.action_contributions[Action.STAY] == pytest.approx(-0.5)

    def test_stay_zero_when_no_hunger(self):
        obs = make_observation()
        result = compute_hunger_drive(
            energy=100.0, max_energy=100.0, observation=obs,
            consume_weight=1.0, stay_suppression=1.0,
        )
        assert result.action_contributions[Action.STAY] == 0.0


# --- Structure and separation tests ---


class TestStructureAndSeparation:
    def test_output_has_six_contributions(self):
        obs = make_observation()
        result = compute_hunger_drive(
            energy=50.0, max_energy=100.0, observation=obs,
            consume_weight=1.0, stay_suppression=0.1,
        )
        assert len(result.action_contributions) == 6

    def test_output_is_frozen(self):
        obs = make_observation()
        result = compute_hunger_drive(
            energy=50.0, max_energy=100.0, observation=obs,
            consume_weight=1.0, stay_suppression=0.1,
        )
        with pytest.raises(ValidationError):
            result.activation = 0.0

    def test_no_world_in_signature(self):
        sig = inspect.signature(compute_hunger_drive)
        params = set(sig.parameters.keys())
        assert "world" not in params

    def test_does_not_mutate_observation(self):
        obs = make_observation(current=0.5, up=0.3)
        obs_dump = obs.model_dump()
        compute_hunger_drive(
            energy=50.0, max_energy=100.0, observation=obs,
            consume_weight=1.5, stay_suppression=0.1,
        )
        assert obs.model_dump() == obs_dump

    def test_all_zero_at_max_energy(self):
        obs = make_observation(current=0.8, up=0.5, down=0.5, left=0.5, right=0.5)
        result = compute_hunger_drive(
            energy=100.0, max_energy=100.0, observation=obs,
            consume_weight=1.5, stay_suppression=0.1,
        )
        assert all(c == 0.0 for c in result.action_contributions)


# --- Worked example tests ---


class TestWorkedExamples:
    def test_half_hunger_asymmetric(self):
        obs = make_observation(current=0.7, up=0.0, down=0.8, left=0.3, right=0.0)
        result = compute_hunger_drive(
            energy=50.0, max_energy=100.0, observation=obs,
            consume_weight=1.5, stay_suppression=0.1,
        )
        assert result.activation == pytest.approx(0.5)
        assert result.action_contributions[Action.UP] == pytest.approx(0.0)
        assert result.action_contributions[Action.DOWN] == pytest.approx(
            0.5 * 0.8)
        assert result.action_contributions[Action.LEFT] == pytest.approx(
            0.5 * 0.3)
        assert result.action_contributions[Action.RIGHT] == pytest.approx(0.0)
        assert result.action_contributions[Action.CONSUME] == pytest.approx(
            0.5 * 1.5 * 0.7
        )
        assert result.action_contributions[Action.STAY] == pytest.approx(
            -0.1 * 0.5
        )

    def test_full_hunger(self):
        obs = make_observation(current=0.5, up=0.5, down=0.5, left=0.5, right=0.5)
        result = compute_hunger_drive(
            energy=0.0, max_energy=100.0, observation=obs,
            consume_weight=2.0, stay_suppression=0.5,
        )
        assert result.activation == 1.0
        assert result.action_contributions[Action.UP] == pytest.approx(0.5)
        assert result.action_contributions[Action.DOWN] == pytest.approx(0.5)
        assert result.action_contributions[Action.LEFT] == pytest.approx(0.5)
        assert result.action_contributions[Action.RIGHT] == pytest.approx(0.5)
        assert result.action_contributions[Action.CONSUME] == pytest.approx(
            1.0)
        assert result.action_contributions[Action.STAY] == pytest.approx(-0.5)
