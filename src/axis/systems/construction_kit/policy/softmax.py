"""Softmax action selection with admissibility masking.

Generalized policy that receives pre-computed action scores (as a tuple
of floats) rather than a specific drive output type. Applies:
1. Admissibility masking (blocked directions -> -inf)
2. Softmax with temperature multiplier beta
3. Stochastic (sample) or argmax selection with seeded tie-breaks
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
_ARGMAX_TIE_REL_TOL = 1e-9
_ARGMAX_TIE_ABS_TOL = 1e-9


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
        action_idx = self._select_action(masked, probs, rng)
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
            observation.current.resource > 0,          # CONSUME only on resource
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
        """Numerically stable softmax with temperature multiplier beta.

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

    def _select_action(
        self,
        masked_scores: tuple[float, float, float, float, float, float],
        probabilities: tuple[float, float, float, float, float, float],
        rng: np.random.Generator,
    ) -> int:
        """Select an action index from policy mode semantics."""
        if self._selection_mode == "argmax":
            max_score = max(score for score in masked_scores if score != _NEG_INF)
            tied_indices = [
                i
                for i, score in enumerate(masked_scores)
                if score != _NEG_INF
                and math.isclose(
                    score,
                    max_score,
                    rel_tol=_ARGMAX_TIE_REL_TOL,
                    abs_tol=_ARGMAX_TIE_ABS_TOL,
                )
            ]
            if len(tied_indices) == 1:
                return tied_indices[0]
            return int(rng.choice(tied_indices))

        # SAMPLE mode
        return int(rng.choice(6, p=probabilities))
