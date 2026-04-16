"""Predictive memory -- q_t(s, a) expectation store."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PredictiveMemory(BaseModel):
    """Predictive memory q_t: expected next features per (context, action).

    Stores expectations as a sorted tuple of ((context, action),
    expected_features) pairs. Immutable -- updates return a new instance.
    """

    model_config = ConfigDict(frozen=True)

    entries: tuple[tuple[tuple[int, str], tuple[float, ...]], ...] = ()
    feature_dim: int = 5


def create_predictive_memory(
    *,
    num_contexts: int = 32,
    actions: tuple[str, ...] = (
        "up", "down", "left", "right", "consume", "stay"),
    feature_dim: int = 5,
) -> PredictiveMemory:
    """Create an initial predictive memory with all expectations at zero.

    Returns:
        PredictiveMemory with q_0(s, a) = (0, ..., 0) for all (s, a).
    """
    zero_vec = tuple(0.0 for _ in range(feature_dim))
    entries = tuple(
        sorted(
            ((ctx, act), zero_vec)
            for ctx in range(num_contexts)
            for act in actions
        )
    )
    return PredictiveMemory(entries=entries, feature_dim=feature_dim)


def _entries_to_dict(
    memory: PredictiveMemory,
) -> dict[tuple[int, str], tuple[float, ...]]:
    """Reconstruct lookup dict from sorted tuple entries."""
    return {key: val for key, val in memory.entries}


def get_prediction(
    memory: PredictiveMemory,
    context: int,
    action: str,
) -> tuple[float, ...]:
    """Retrieve the expected features for a (context, action) pair.

    Args:
        memory: Current predictive memory state.
        context: Context index s_t.
        action: Action name.

    Returns:
        Expected feature vector y_hat. Zero vector if pair not found.
    """
    lookup = _entries_to_dict(memory)
    return lookup.get(
        (context, action),
        tuple(0.0 for _ in range(memory.feature_dim)),
    )


def update_predictive_memory(
    memory: PredictiveMemory,
    context: int,
    action: str,
    observed_features: tuple[float, ...],
    *,
    learning_rate: float,
) -> PredictiveMemory:
    """Update predictive memory for one (context, action) pair.

    q_{t+1}(s_t, a_t) = (1 - eta_q) * q_t(s_t, a_t) + eta_q * y_{t+1}

    All other pairs remain unchanged.

    Args:
        memory: Current predictive memory state.
        context: Active context index s_t.
        action: Selected action a_t.
        observed_features: Realized feature vector y_{t+1}.
        learning_rate: eta_q in (0, 1].

    Returns:
        New PredictiveMemory with updated entry.
    """
    lookup = _entries_to_dict(memory)
    key = (context, action)
    old = lookup.get(key, tuple(0.0 for _ in range(memory.feature_dim)))
    updated = tuple(
        (1.0 - learning_rate) * o + learning_rate * y
        for o, y in zip(old, observed_features)
    )
    lookup[key] = updated
    return PredictiveMemory(
        entries=tuple(sorted(lookup.items())),
        feature_dim=memory.feature_dim,
    )
