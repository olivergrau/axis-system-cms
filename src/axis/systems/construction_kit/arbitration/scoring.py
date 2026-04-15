"""N-drive action score combination."""

from __future__ import annotations

from collections.abc import Sequence


def combine_drive_scores(
    drive_contributions: Sequence[tuple[float, ...]],
    drive_activations: Sequence[float],
    drive_weights: Sequence[float],
) -> tuple[float, ...]:
    """Combine N drives into per-action scores.

    psi(a) = sum_i(w_i * d_i * phi_i(a))

    All contribution tuples must have the same length.
    Raises ValueError if zero drives.
    """
    n = len(drive_contributions)
    if n == 0:
        raise ValueError("At least one drive is required")

    num_actions = len(drive_contributions[0])
    scores = [0.0] * num_actions

    for i in range(n):
        w = drive_weights[i]
        d = drive_activations[i]
        contributions = drive_contributions[i]
        for a in range(num_actions):
            scores[a] += w * d * contributions[a]

    return tuple(scores)
