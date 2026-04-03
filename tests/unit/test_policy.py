"""Tests for the policy and decision pipeline."""

import inspect
import math

import numpy as np
import pytest
from pydantic import ValidationError

from axis_system_a import (
    Action,
    DecisionTrace,
    SelectionMode,
    select_action,
)
from tests.fixtures.observation_fixtures import make_observation

_NEG_INF = float("-inf")


def _all_open_obs():
    return make_observation(current=0.5, up=0.3, down=0.1, left=0.0, right=0.8)


def _all_blocked_obs():
    return make_observation(b_up=0.0, b_down=0.0, b_left=0.0, b_right=0.0, current=0.5)


# --- Admissibility mask tests ---


class TestAdmissibilityMask:
    def test_all_directions_open(self):
        obs = _all_open_obs()
        result = select_action(
            (0.0,) * 6, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.admissibility_mask == (
            True, True, True, True, True, True)

    def test_single_direction_blocked_up(self):
        obs = make_observation(b_up=0.0)
        result = select_action(
            (0.0,) * 6, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.admissibility_mask[Action.UP] is False
        assert all(
            result.admissibility_mask[a] is True
            for a in Action if a != Action.UP
        )

    def test_single_direction_blocked_down(self):
        obs = make_observation(b_down=0.0)
        result = select_action(
            (0.0,) * 6, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.admissibility_mask[Action.DOWN] is False

    def test_single_direction_blocked_left(self):
        obs = make_observation(b_left=0.0)
        result = select_action(
            (0.0,) * 6, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.admissibility_mask[Action.LEFT] is False

    def test_single_direction_blocked_right(self):
        obs = make_observation(b_right=0.0)
        result = select_action(
            (0.0,) * 6, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.admissibility_mask[Action.RIGHT] is False

    def test_all_movement_blocked(self):
        obs = _all_blocked_obs()
        result = select_action(
            (0.0,) * 6, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.admissibility_mask == (
            False, False, False, False, True, True,
        )

    def test_consume_always_admissible(self):
        obs = make_observation(current=0.0, b_up=0.0, b_down=0.0,
                               b_left=0.0, b_right=0.0)
        result = select_action(
            (0.0,) * 6, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.admissibility_mask[Action.CONSUME] is True
        assert result.admissibility_mask[Action.STAY] is True


# --- Masked contributions tests ---


class TestMaskedContributions:
    def test_unmasked_preserves_original(self):
        obs = _all_open_obs()
        contribs = (0.1, 0.2, 0.3, 0.4, 0.5, -0.1)
        result = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.masked_contributions == contribs

    def test_masked_action_gets_negative_infinity(self):
        obs = make_observation(b_up=0.0)
        contribs = (0.1, 0.2, 0.3, 0.4, 0.5, -0.1)
        result = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.masked_contributions[Action.UP] == _NEG_INF

    def test_multiple_masked_actions(self):
        obs = make_observation(b_up=0.0, b_left=0.0)
        contribs = (0.1, 0.2, 0.3, 0.4, 0.5, -0.1)
        result = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.masked_contributions[Action.UP] == _NEG_INF
        assert result.masked_contributions[Action.LEFT] == _NEG_INF
        assert result.masked_contributions[Action.DOWN] == 0.2
        assert result.masked_contributions[Action.RIGHT] == 0.4

    def test_raw_contributions_unchanged(self):
        obs = make_observation(b_up=0.0)
        contribs = (0.1, 0.2, 0.3, 0.4, 0.5, -0.1)
        result = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.raw_contributions == contribs

    def test_negative_contribution_preserved_when_admissible(self):
        obs = _all_open_obs()
        contribs = (0.0, 0.0, 0.0, 0.0, 0.0, -0.5)
        result = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.masked_contributions[Action.STAY] == -0.5


# --- Softmax tests ---


class TestSoftmax:
    def test_probabilities_sum_to_one(self):
        obs = _all_open_obs()
        contribs = (0.1, 0.2, 0.3, 0.4, 0.5, -0.1)
        result = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert sum(result.probabilities) == pytest.approx(1.0)

    def test_equal_scores_uniform(self):
        obs = _all_open_obs()
        result = select_action(
            (0.0,) * 6, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        for p in result.probabilities:
            assert p == pytest.approx(1.0 / 6.0)

    def test_higher_beta_more_peaked(self):
        obs = _all_open_obs()
        contribs = (0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
        r_low = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        r_high = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=10.0,
        )
        assert r_high.probabilities[Action.CONSUME] > r_low.probabilities[Action.CONSUME]

    def test_lower_beta_more_uniform(self):
        obs = _all_open_obs()
        contribs = (0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
        result = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=0.01,
        )
        for p in result.probabilities:
            assert p == pytest.approx(1.0 / 6.0, abs=0.01)

    def test_masked_action_zero_probability(self):
        obs = make_observation(b_up=0.0, b_down=0.0)
        contribs = (0.5, 0.5, 0.5, 0.5, 0.5, 0.5)
        result = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.probabilities[Action.UP] == 0.0
        assert result.probabilities[Action.DOWN] == 0.0
        assert sum(result.probabilities) == pytest.approx(1.0)

    def test_numeric_stability_large_positive(self):
        obs = _all_open_obs()
        contribs = (100.0, 100.0, 100.0, 100.0, 100.0, 100.0)
        result = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=10.0,
        )
        assert all(not math.isnan(p) and not math.isinf(p)
                   for p in result.probabilities)
        assert sum(result.probabilities) == pytest.approx(1.0)

    def test_numeric_stability_large_negative(self):
        obs = _all_open_obs()
        contribs = (-100.0, -100.0, -100.0, -100.0, -100.0, -100.0)
        result = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=10.0,
        )
        assert all(not math.isnan(p) for p in result.probabilities)
        assert sum(result.probabilities) == pytest.approx(1.0)

    def test_all_zero_some_masked_uniform_over_admissible(self):
        obs = make_observation(b_up=0.0, b_down=0.0)
        result = select_action(
            (0.0,) * 6, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.probabilities[Action.UP] == 0.0
        assert result.probabilities[Action.DOWN] == 0.0
        for a in [Action.LEFT, Action.RIGHT, Action.CONSUME, Action.STAY]:
            assert result.probabilities[a] == pytest.approx(0.25)

    def test_probabilities_sum_with_partial_mask(self):
        obs = make_observation(b_up=0.0)
        contribs = (0.3, 0.1, 0.2, 0.4, 0.5, -0.1)
        result = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert sum(result.probabilities) == pytest.approx(1.0)
        assert result.probabilities[Action.UP] == 0.0


# --- Argmax selection tests ---


class TestArgmaxSelection:
    def test_selects_highest_probability(self):
        obs = _all_open_obs()
        contribs = (0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
        result = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.selected_action == Action.CONSUME

    def test_tie_break_lowest_enum_value(self):
        obs = _all_open_obs()
        result = select_action(
            (0.0,) * 6, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.selected_action == Action.UP

    def test_two_way_tie_up_vs_down(self):
        obs = _all_open_obs()
        contribs = (1.0, 1.0, 0.0, 0.0, 0.0, 0.0)
        result = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.selected_action == Action.UP

    def test_consume_vs_stay_tie(self):
        obs = _all_blocked_obs()
        contribs = (0.5, 0.5, 0.5, 0.5, 0.5, 0.5)
        result = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.selected_action == Action.CONSUME

    def test_no_rng_required(self):
        obs = _all_open_obs()
        result = select_action(
            (0.0,) * 6, obs, SelectionMode.ARGMAX, temperature=1.0,
            rng=None,
        )
        assert result.selected_action == Action.UP

    def test_deterministic_across_calls(self):
        obs = _all_open_obs()
        contribs = (0.1, 0.2, 0.3, 0.4, 0.5, -0.1)
        r1 = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=1.0)
        r2 = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=1.0)
        assert r1.selected_action == r2.selected_action
        assert r1.probabilities == r2.probabilities


# --- Sample selection tests ---


class TestSampleSelection:
    def test_same_seed_same_result(self):
        obs = _all_open_obs()
        contribs = (0.1, 0.2, 0.3, 0.4, 0.5, -0.1)
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)
        r1 = select_action(contribs, obs, SelectionMode.SAMPLE, 1.0, rng=rng1)
        r2 = select_action(contribs, obs, SelectionMode.SAMPLE, 1.0, rng=rng2)
        assert r1.selected_action == r2.selected_action

    def test_probability_one_always_selected(self):
        obs = _all_open_obs()
        contribs = (0.0, 0.0, 0.0, 0.0, 10.0, 0.0)
        rng = np.random.default_rng(123)
        for _ in range(100):
            result = select_action(
                contribs, obs, SelectionMode.SAMPLE, temperature=100.0, rng=rng,
            )
            assert result.selected_action == Action.CONSUME

    def test_masked_action_never_selected(self):
        obs = make_observation(b_up=0.0)
        contribs = (0.5, 0.1, 0.1, 0.1, 0.1, 0.1)
        rng = np.random.default_rng(99)
        for _ in range(200):
            result = select_action(
                contribs, obs, SelectionMode.SAMPLE, temperature=1.0, rng=rng,
            )
            assert result.selected_action != Action.UP

    def test_distribution_approximates_probabilities(self):
        obs = _all_open_obs()
        contribs = (0.0,) * 6
        rng = np.random.default_rng(7)
        counts = [0] * 6
        n = 12000
        for _ in range(n):
            result = select_action(
                contribs, obs, SelectionMode.SAMPLE, temperature=1.0, rng=rng,
            )
            counts[result.selected_action] += 1
        for c in counts:
            assert c / n == pytest.approx(1.0 / 6.0, abs=0.03)

    def test_requires_rng(self):
        obs = _all_open_obs()
        with pytest.raises(ValueError, match="rng"):
            select_action(
                (0.0,) * 6, obs, SelectionMode.SAMPLE, temperature=1.0,
                rng=None,
            )

    def test_returns_valid_action(self):
        obs = _all_open_obs()
        rng = np.random.default_rng(0)
        result = select_action(
            (0.1, 0.2, 0.3, 0.4, 0.5, -0.1), obs,
            SelectionMode.SAMPLE, temperature=1.0, rng=rng,
        )
        assert isinstance(result.selected_action, Action)


# --- Decision trace tests ---


class TestDecisionTrace:
    def test_frozen(self):
        obs = _all_open_obs()
        result = select_action(
            (0.0,) * 6, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        with pytest.raises(ValidationError):
            result.selected_action = Action.STAY

    def test_has_exactly_five_fields(self):
        assert set(DecisionTrace.model_fields.keys()) == {
            "raw_contributions",
            "admissibility_mask",
            "masked_contributions",
            "probabilities",
            "selected_action",
            "temperature",
            "selection_mode",
        }

    def test_internal_consistency(self):
        obs = make_observation(b_up=0.0, b_down=0.0)
        contribs = (0.3, 0.2, 0.1, 0.4, 0.5, -0.1)
        result = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        for i in range(6):
            if result.admissibility_mask[i] is False:
                assert result.masked_contributions[i] == _NEG_INF
                assert result.probabilities[i] == 0.0
            else:
                assert result.masked_contributions[i] == contribs[i]
                assert result.probabilities[i] > 0.0
        assert sum(result.probabilities) == pytest.approx(1.0)

    def test_raw_contributions_match_input(self):
        obs = _all_open_obs()
        contribs = (0.1, 0.2, 0.3, 0.4, 0.5, -0.1)
        result = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.raw_contributions == contribs

    def test_selected_action_is_action_type(self):
        obs = _all_open_obs()
        result = select_action(
            (0.0,) * 6, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert isinstance(result.selected_action, Action)


# --- End-to-end tests ---


class TestEndToEnd:
    def test_all_zero_uniform(self):
        obs = _all_open_obs()
        result = select_action(
            (0.0,) * 6, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        for p in result.probabilities:
            assert p == pytest.approx(1.0 / 6.0)
        assert result.selected_action == Action.UP

    def test_blocked_directions_excluded(self):
        obs = make_observation(b_up=0.0, b_left=0.0)
        contribs = (0.5, 0.1, 0.5, 0.1, 0.1, 0.0)
        result = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.probabilities[Action.UP] == 0.0
        assert result.probabilities[Action.LEFT] == 0.0
        assert result.selected_action != Action.UP
        assert result.selected_action != Action.LEFT

    def test_high_beta_near_argmax(self):
        obs = _all_open_obs()
        contribs = (0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
        result = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=100.0,
        )
        assert result.probabilities[Action.CONSUME] > 0.99

    def test_all_movement_blocked_only_consume_stay(self):
        obs = _all_blocked_obs()
        contribs = (0.3, 0.3, 0.3, 0.3, 0.5, -0.1)
        result = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.probabilities[Action.UP] == 0.0
        assert result.probabilities[Action.DOWN] == 0.0
        assert result.probabilities[Action.LEFT] == 0.0
        assert result.probabilities[Action.RIGHT] == 0.0
        assert sum(result.probabilities) == pytest.approx(1.0)
        assert result.selected_action in (Action.CONSUME, Action.STAY)

    def test_stay_suppressed(self):
        obs = _all_open_obs()
        contribs = (0.0, 0.0, 0.0, 0.0, 0.0, -0.5)
        result = select_action(
            contribs, obs, SelectionMode.ARGMAX, temperature=1.0,
        )
        assert result.probabilities[Action.STAY] < result.probabilities[Action.UP]

    def test_drive_output_fed_directly(self):
        from axis_system_a import compute_hunger_drive

        obs = make_observation(current=0.5, up=0.3, down=0.2, left=0.1, right=0.4)
        drive = compute_hunger_drive(
            energy=50.0, max_energy=100.0, observation=obs,
            consume_weight=1.5, stay_suppression=0.1,
        )
        result = select_action(
            drive.action_contributions, obs,
            SelectionMode.ARGMAX, temperature=1.0,
        )
        assert isinstance(result.selected_action, Action)
        assert sum(result.probabilities) == pytest.approx(1.0)


# --- Pipeline structure tests ---


class TestPipelineStructure:
    def test_no_world_in_signature(self):
        sig = inspect.signature(select_action)
        assert "world" not in sig.parameters

    def test_policy_module_does_not_import_world(self):
        import axis_system_a.policy as policy_mod

        source = inspect.getsource(policy_mod)
        assert "from axis_system_a.world" not in source
        assert "import World" not in source

    def test_does_not_mutate_observation(self):
        obs = _all_open_obs()
        dump_before = obs.model_dump()
        select_action(
            (0.1, 0.2, 0.3, 0.4, 0.5, -0.1), obs,
            SelectionMode.ARGMAX, temperature=1.0,
        )
        assert obs.model_dump() == dump_before

    def test_does_not_mutate_contributions(self):
        obs = _all_open_obs()
        contribs = (0.1, 0.2, 0.3, 0.4, 0.5, -0.1)
        select_action(contribs, obs, SelectionMode.ARGMAX, temperature=1.0)
        assert contribs == (0.1, 0.2, 0.3, 0.4, 0.5, -0.1)
