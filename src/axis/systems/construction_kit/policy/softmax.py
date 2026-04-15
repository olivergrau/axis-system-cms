"""Softmax action selection with admissibility masking.

Generalized policy that receives pre-computed action scores (as a tuple
of floats) rather than a specific drive output type. Applies:
1. Admissibility masking (blocked directions -> -inf)
2. Softmax with inverse temperature beta
3. Stochastic (sample) or deterministic (argmax) selection
"""

from __future__ import annotations

import math

import numpy as np

from axis.sdk.types import PolicyResult
from axis.systems.construction_kit.observation.types import Observation

# Action ordering convention: (up, down, left, right, consume, stay)
_ACTION_NAMES: tuple[str, ...] = (
    "up", "down", "left", "right", "consume", "stay")

_NEG_INF = float("-inf")


class SoftmaxPolicy:
    """Softmax policy for action selection.

    Satisfies PolicyInterface. Implements admissibility masking,
    softmax normalization, and stochastic/deterministic selection.
    """

    def __init__(self, *, temperature: float, selection_mode: str) -> None:
        self._temperature = temperature
        self._selection_mode = selection_mode

    def select(
        self,
        action_scores: tuple[float, ...],
        observation: Observation,
        rng: np.random.Generator,
    ) -> PolicyResult:
        """Run the full policy pipeline: mask -> softmax -> select."""
        mask = self._compute_admissibility_mask(observation)
        masked = self._apply_mask(action_scores, mask)
        probs = self._softmax(action_scores, self._temperature, mask)
        action_idx = self._select_from_distribution(probs, rng)
        action = _ACTION_NAMES[action_idx]

        policy_data = {
            "raw_contributions": action_scores,
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
        scores: tuple[float, float, float, float, float, float],
        mask: tuple[bool, bool, bool, bool, bool, bool],
    ) -> tuple[float, float, float, float, float, float]:
        """Replace masked action scores with -inf."""
        return tuple(  # type: ignore[return-value]
            c if m else _NEG_INF for c, m in zip(scores, mask)
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
