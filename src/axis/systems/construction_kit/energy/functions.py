"""Energy management utility functions."""

from __future__ import annotations

from axis.sdk.actions import MOVEMENT_DELTAS, STAY


def clip_energy(energy: float, max_energy: float) -> float:
    """Clip energy to the valid interval [0, max_energy]."""
    return max(0.0, min(energy, max_energy))


def compute_vitality(energy: float, max_energy: float) -> float:
    """Normalized vitality: energy / max_energy."""
    return energy / max_energy


def check_energy_termination(energy: float) -> tuple[bool, str | None]:
    """Check if energy level triggers termination.

    Returns (terminated, reason).
    """
    terminated = energy <= 0.0
    reason = "energy_depleted" if terminated else None
    return terminated, reason


def get_action_cost(
    action: str,
    *,
    move_cost: float,
    stay_cost: float,
    custom_costs: dict[str, float] | None = None,
) -> float:
    """Return the energy cost for a given action.

    Dispatches in order:
    1. Movement actions (in MOVEMENT_DELTAS) -> move_cost
    2. Custom costs dict (e.g. {"consume": 0.5}) -> custom_costs[action]
    3. STAY action -> stay_cost
    4. Unknown actions -> stay_cost (fallback)
    """
    if action in MOVEMENT_DELTAS:
        return move_cost
    if custom_costs and action in custom_costs:
        return custom_costs[action]
    return stay_cost
