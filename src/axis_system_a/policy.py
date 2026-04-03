"""Policy and decision pipeline for baseline action selection."""

from __future__ import annotations

import math

import numpy as np
from pydantic import BaseModel, ConfigDict

from axis_system_a.enums import Action, SelectionMode
from axis_system_a.types import Observation

_NEG_INF = float("-inf")


class DecisionResult(BaseModel):
    """Full decision trace from the policy pipeline.

    All tuple fields are indexed by Action enum:
    (UP, DOWN, LEFT, RIGHT, CONSUME, STAY).
    """

    model_config = ConfigDict(frozen=True)

    raw_contributions: tuple[float, float, float, float, float, float]
    admissibility_mask: tuple[bool, bool, bool, bool, bool, bool]
    masked_contributions: tuple[float, float, float, float, float, float]
    probabilities: tuple[float, float, float, float, float, float]
    selected_action: Action


def _compute_admissibility_mask(
    observation: Observation,
) -> tuple[bool, bool, bool, bool, bool, bool]:
    """Derive per-action admissibility from observation traversability."""
    return (
        observation.up.traversability > 0,       # UP
        observation.down.traversability > 0,     # DOWN
        observation.left.traversability > 0,     # LEFT
        observation.right.traversability > 0,    # RIGHT
        True,                                     # CONSUME always admissible
        True,                                     # STAY always admissible
    )


def _apply_mask(
    contributions: tuple[float, float, float, float, float, float],
    mask: tuple[bool, bool, bool, bool, bool, bool],
) -> tuple[float, float, float, float, float, float]:
    """Replace masked action contributions with -inf."""
    return tuple(  # type: ignore[return-value]
        c if m else _NEG_INF for c, m in zip(contributions, mask)
    )


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
    probabilities: tuple[float, float, float, float, float, float],
    mode: SelectionMode,
    rng: np.random.Generator | None,
) -> Action:
    """Select an action from the probability distribution."""
    if mode is SelectionMode.ARGMAX:
        max_p = max(probabilities)
        for i in range(6):
            if probabilities[i] == max_p:
                return Action(i)

    # SAMPLE mode
    if rng is None:
        raise ValueError("rng is required for SAMPLE selection mode")
    idx = rng.choice(6, p=probabilities)
    return Action(idx)


def select_action(
    contributions: tuple[float, float, float, float, float, float],
    observation: Observation,
    selection_mode: SelectionMode,
    temperature: float,
    rng: np.random.Generator | None = None,
) -> DecisionResult:
    """Run the full policy pipeline: mask -> logits -> softmax -> select.

    Parameters
    ----------
    contributions : 6-element action scores from the drive system.
    observation : Current observation (used for admissibility masking).
    selection_mode : SAMPLE (stochastic) or ARGMAX (deterministic).
    temperature : Inverse temperature beta for softmax. Higher = more peaked.
    rng : Seeded numpy Generator, required for SAMPLE mode.
    """
    mask = _compute_admissibility_mask(observation)
    masked = _apply_mask(contributions, mask)
    probs = _softmax(contributions, temperature, mask)
    action = _select_from_distribution(probs, selection_mode, rng)

    return DecisionResult(
        raw_contributions=contributions,
        admissibility_mask=mask,
        masked_contributions=masked,
        probabilities=probs,
        selected_action=action,
    )
