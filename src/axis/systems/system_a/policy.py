"""System A policy -- softmax action selection with admissibility masking."""

from __future__ import annotations

import math

import numpy as np

from axis.sdk.types import PolicyResult
from axis.systems.system_a.types import HungerDriveOutput, Observation

# Action ordering convention: (up, down, left, right, consume, stay)
_ACTION_NAMES: tuple[str, ...] = ("up", "down", "left", "right", "consume", "stay")

_NEG_INF = float("-inf")


class SystemAPolicy:
    """Softmax policy for System A.

    Satisfies PolicyInterface. Implements admissibility masking,
    softmax normalization, and stochastic/deterministic selection.
    """

    def __init__(self, *, temperature: float, selection_mode: str) -> None:
        self._temperature = temperature
        self._selection_mode = selection_mode

    def select(
        self,
        drive_outputs: HungerDriveOutput,
        observation: Observation,
        rng: np.random.Generator,
    ) -> PolicyResult:
        """Run the full policy pipeline: mask -> softmax -> select."""
        contributions = drive_outputs.action_contributions
        mask = self._compute_admissibility_mask(observation)
        masked = self._apply_mask(contributions, mask)
        probs = self._softmax(contributions, self._temperature, mask)
        action_idx = self._select_from_distribution(probs, rng)
        action = _ACTION_NAMES[action_idx]

        policy_data = {
            "raw_contributions": contributions,
            "admissibility_mask": mask,
            "masked_contributions": masked,
            "probabilities": probs,
            "selected_action": action,
            "temperature": self._temperature,
            "selection_mode": self._selection_mode,
        }

        return PolicyResult(action=action, policy_data=policy_data)

    @staticmethod
    def _compute_admissibility_mask(
        observation: Observation,
    ) -> tuple[bool, bool, bool, bool, bool, bool]:
        """Derive per-action admissibility from observation traversability."""
        return (
            observation.up.traversability > 0,       # UP
            observation.down.traversability > 0,      # DOWN
            observation.left.traversability > 0,      # LEFT
            observation.right.traversability > 0,     # RIGHT
            True,                                      # CONSUME always admissible
            True,                                      # STAY always admissible
        )

    @staticmethod
    def _apply_mask(
        contributions: tuple[float, float, float, float, float, float],
        mask: tuple[bool, bool, bool, bool, bool, bool],
    ) -> tuple[float, float, float, float, float, float]:
        """Replace masked action contributions with -inf."""
        return tuple(  # type: ignore[return-value]
            c if m else _NEG_INF for c, m in zip(contributions, mask)
        )

    @staticmethod
    def _softmax(
        contributions: tuple[float, float, float, float, float, float],
        beta: float,
        mask: tuple[bool, bool, bool, bool, bool, bool],
    ) -> tuple[float, float, float, float, float, float]:
        """Numerically stable softmax with inverse temperature beta.

        P(a_i) = exp(beta * (s_i - s_max)) / SUM_j exp(beta * (s_j - s_max))
        where s_max is taken over admissible actions only.
        Masked actions receive probability 0.
        """
        s_max = max(contributions[i] for i in range(6) if mask[i])

        exp_values = []
        for i in range(6):
            if mask[i]:
                exp_values.append(math.exp(beta * (contributions[i] - s_max)))
            else:
                exp_values.append(0.0)

        z = sum(exp_values)
        return tuple(e / z for e in exp_values)  # type: ignore[return-value]

    def _select_from_distribution(
        self,
        probabilities: tuple[float, float, float, float, float, float],
        rng: np.random.Generator,
    ) -> int:
        """Select an action index from the probability distribution."""
        if self._selection_mode == "argmax":
            max_p = max(probabilities)
            for i in range(6):
                if probabilities[i] == max_p:
                    return i

        # SAMPLE mode
        return int(rng.choice(6, p=probabilities))
