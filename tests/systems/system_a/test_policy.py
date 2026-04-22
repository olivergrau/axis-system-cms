"""WP-2.4 unit tests -- SoftmaxPolicy."""

from __future__ import annotations

import math
import numpy as np
import pytest

from axis.sdk.interfaces import PolicyInterface
from axis.sdk.types import PolicyResult
from axis.systems.construction_kit.observation.types import CellObservation, Observation
from axis.systems.construction_kit.policy.softmax import SoftmaxPolicy
from axis.systems.construction_kit.drives.types import HungerDriveOutput


def _make_policy(
    mode: str = "sample", temperature: float = 1.0,
) -> SoftmaxPolicy:
    return SoftmaxPolicy(temperature=temperature, selection_mode=mode)


def _make_observation(
    *, blocked_dirs: tuple[str, ...] = (),
) -> Observation:
    open_cell = CellObservation(traversability=1.0, resource=0.5)
    blocked_cell = CellObservation(traversability=0.0, resource=0.0)
    return Observation(
        current=open_cell,
        up=blocked_cell if "up" in blocked_dirs else open_cell,
        down=blocked_cell if "down" in blocked_dirs else open_cell,
        left=blocked_cell if "left" in blocked_dirs else open_cell,
        right=blocked_cell if "right" in blocked_dirs else open_cell,
    )


def _make_drive_output(
    contributions: tuple[float, ...] = (0.25, 0.25, 0.25, 0.25, 0.35, -0.05),
) -> HungerDriveOutput:
    return HungerDriveOutput(
        activation=0.5,
        action_contributions=contributions,  # type: ignore[arg-type]
    )


class TestPolicy:
    """SoftmaxPolicy unit tests."""

    def test_argmax_unique_winner_stays_deterministic(self) -> None:
        policy = _make_policy("argmax")
        obs = _make_observation()
        drive = _make_drive_output((0.1, 0.2, 0.3, 0.4, 0.5, -0.1))
        actions = set()
        for seed in range(10):
            rng = np.random.default_rng(seed)
            result = policy.select(drive.action_contributions, obs, rng)
            actions.add(result.action)
        assert len(actions) == 1
        assert actions == {"consume"}

    def test_argmax_selects_highest(self) -> None:
        policy = _make_policy("argmax")
        obs = _make_observation()
        drive = _make_drive_output((0.1, 0.2, 0.3, 0.4, 0.5, -0.1))
        rng = np.random.default_rng(42)
        result = policy.select(drive.action_contributions, obs, rng)
        assert result.action == "consume"

    def test_argmax_tied_top_actions_selected_only_from_tied_set(self) -> None:
        policy = _make_policy("argmax")
        obs = _make_observation()
        drive = _make_drive_output((0.9, 0.9, 0.1, 0.2, 0.1, -0.5))
        actions = set()
        for seed in range(30):
            rng = np.random.default_rng(seed)
            result = policy.select(drive.action_contributions, obs, rng)
            actions.add(result.action)
        assert actions <= {"up", "down"}
        assert actions == {"up", "down"}

    def test_argmax_tied_selection_reproducible_with_fixed_seed(self) -> None:
        policy = _make_policy("argmax")
        obs = _make_observation()
        drive = _make_drive_output((0.9, 0.9, 0.1, 0.2, 0.1, -0.5))

        r1 = policy.select(
            drive.action_contributions, obs, np.random.default_rng(123),
        )
        r2 = policy.select(
            drive.action_contributions, obs, np.random.default_rng(123),
        )

        assert r1.action == r2.action

    def test_argmax_masked_actions_excluded_from_tie_breaking(self) -> None:
        policy = _make_policy("argmax")
        obs = _make_observation(blocked_dirs=("up",))
        drive = _make_drive_output((0.9, 0.9, 0.1, 0.2, 0.1, -0.5))

        actions = set()
        for seed in range(20):
            rng = np.random.default_rng(seed)
            result = policy.select(drive.action_contributions, obs, rng)
            actions.add(result.action)

        assert "up" not in actions
        assert actions == {"down"}

    def test_argmax_uses_tolerance_for_near_equal_top_scores(self) -> None:
        policy = _make_policy("argmax")
        obs = _make_observation()
        drive = _make_drive_output((1.0, 1.0 - 1e-10, 0.0, 0.0, 0.0, -1.0))

        actions = set()
        for seed in range(20):
            rng = np.random.default_rng(seed)
            result = policy.select(drive.action_contributions, obs, rng)
            actions.add(result.action)

        assert actions == {"up", "down"}

    def test_sample_uses_rng(self) -> None:
        policy = _make_policy("sample")
        obs = _make_observation()
        drive = _make_drive_output((0.2, 0.2, 0.2, 0.2, 0.2, 0.2))
        actions = set()
        for seed in range(50):
            rng = np.random.default_rng(seed)
            result = policy.select(drive.action_contributions, obs, rng)
            actions.add(result.action)
        assert len(actions) >= 2

    def test_sample_reproducible(self) -> None:
        policy = _make_policy("sample")
        obs = _make_observation()
        drive = _make_drive_output()
        r1 = policy.select(drive.action_contributions,
                           obs, np.random.default_rng(123))
        r2 = policy.select(drive.action_contributions,
                           obs, np.random.default_rng(123))
        assert r1.action == r2.action

    def test_softmax_mode_probabilities_unchanged(self) -> None:
        policy = _make_policy("sample")
        obs = _make_observation()
        scores = (0.1, 0.2, 0.3, 0.4, 0.5, -0.1)
        drive = _make_drive_output(scores)
        rng = np.random.default_rng(42)

        result = policy.select(drive.action_contributions, obs, rng)
        probs = result.policy_data["probabilities"]
        mask = result.policy_data["admissibility_mask"]

        s_max = max(score for score, admissible in zip(scores, mask) if admissible)
        exp_values = [
            math.exp(score - s_max) if admissible else 0.0
            for score, admissible in zip(scores, mask)
        ]
        z = sum(exp_values)
        expected = tuple(value / z for value in exp_values)

        assert probs == pytest.approx(expected, abs=1e-12)

    def test_obstacle_direction_zero_probability(self) -> None:
        policy = _make_policy("sample")
        obs = _make_observation(blocked_dirs=("left",))
        drive = _make_drive_output()
        rng = np.random.default_rng(42)
        result = policy.select(drive.action_contributions, obs, rng)
        probs = result.policy_data["probabilities"]
        assert probs[2] == 0.0  # left index

    def test_all_actions_blocked_except_stay_and_consume(self) -> None:
        policy = _make_policy("sample")
        obs = _make_observation(blocked_dirs=("up", "down", "left", "right"))
        drive = _make_drive_output()
        rng = np.random.default_rng(42)
        result = policy.select(drive.action_contributions, obs, rng)
        probs = result.policy_data["probabilities"]
        assert probs[0] == 0.0  # up
        assert probs[1] == 0.0  # down
        assert probs[2] == 0.0  # left
        assert probs[3] == 0.0  # right
        assert probs[4] > 0.0  # consume
        assert probs[5] > 0.0  # stay

    def test_returns_policy_result(self) -> None:
        policy = _make_policy()
        obs = _make_observation()
        drive = _make_drive_output()
        rng = np.random.default_rng(42)
        result = policy.select(drive.action_contributions, obs, rng)
        assert isinstance(result, PolicyResult)

    def test_policy_data_contains_probabilities(self) -> None:
        policy = _make_policy()
        obs = _make_observation()
        drive = _make_drive_output()
        rng = np.random.default_rng(42)
        result = policy.select(drive.action_contributions, obs, rng)
        assert "probabilities" in result.policy_data

    def test_policy_data_contains_admissibility(self) -> None:
        policy = _make_policy()
        obs = _make_observation()
        drive = _make_drive_output()
        rng = np.random.default_rng(42)
        result = policy.select(drive.action_contributions, obs, rng)
        assert "admissibility_mask" in result.policy_data

    def test_policy_interface_conformance(self) -> None:
        policy = _make_policy()
        assert isinstance(policy, PolicyInterface)

    def test_action_is_string(self) -> None:
        policy = _make_policy()
        obs = _make_observation()
        drive = _make_drive_output()
        rng = np.random.default_rng(42)
        result = policy.select(drive.action_contributions, obs, rng)
        assert isinstance(result.action, str)
        assert result.action in ("up", "down", "left",
                                 "right", "consume", "stay")
