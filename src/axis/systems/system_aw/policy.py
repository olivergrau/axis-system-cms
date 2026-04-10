"""System A+W policy -- softmax action selection with admissibility masking.

The policy is unchanged from System A (Model Section 7). It receives
a single combined action score vector and applies:
1. Admissibility masking (blocked directions -> -inf)
2. Softmax with inverse temperature beta
3. Stochastic (sample) or deterministic (argmax) selection
"""

from __future__ import annotations

import numpy as np

from axis.sdk.types import PolicyResult
from axis.systems.system_a.policy import SystemAPolicy
from axis.systems.system_a.types import Observation


class SystemAWPolicy:
    """Softmax policy for System A+W.

    Accepts pre-computed action scores (from the arbitration layer)
    rather than a single drive output. Delegates masking, softmax,
    and selection to System A's policy implementation.

    Model reference: Sections 6.6, 7.
    """

    def __init__(self, *, temperature: float, selection_mode: str) -> None:
        self._inner = SystemAPolicy(
            temperature=temperature,
            selection_mode=selection_mode,
        )
        self._temperature = temperature
        self._selection_mode = selection_mode

    def select(
        self,
        action_scores: tuple[float, float, float, float, float, float],
        observation: Observation,
        rng: np.random.Generator,
    ) -> PolicyResult:
        """Run the policy pipeline on pre-computed action scores.

        Steps:
        1. Compute admissibility mask from observation
        2. Apply mask (blocked -> -inf)
        3. Softmax with temperature beta
        4. Select action (sample or argmax)
        """
        mask = SystemAPolicy._compute_admissibility_mask(observation)
        masked = SystemAPolicy._apply_mask(action_scores, mask)
        probs = SystemAPolicy._softmax(action_scores, self._temperature, mask)
        action_idx = self._inner._select_from_distribution(probs, rng)

        action_names = ("up", "down", "left", "right", "consume", "stay")
        action = action_names[action_idx]

        policy_data = {
            "raw_scores": action_scores,
            "admissibility_mask": mask,
            "masked_scores": masked,
            "probabilities": probs,
            "selected_action": action,
            "temperature": self._temperature,
            "selection_mode": self._selection_mode,
        }

        return PolicyResult(action=action, policy_data=policy_data)
