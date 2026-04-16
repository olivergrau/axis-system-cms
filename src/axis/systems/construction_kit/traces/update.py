"""Trace update -- EMA update for frustration and confidence traces."""

from __future__ import annotations

from axis.systems.construction_kit.traces.state import (
    TraceState,
    get_confidence,
    get_frustration,
)


def _update_entries(
    entries: tuple[tuple[tuple[int, str], float], ...],
    context: int,
    action: str,
    old_value: float,
    new_signal: float,
    learning_rate: float,
) -> tuple[tuple[tuple[int, str], float], ...]:
    """Update a single (context, action) entry in a trace via EMA."""
    updated_value = (1.0 - learning_rate) * old_value + \
        learning_rate * new_signal
    key = (context, action)

    lookup = {k: v for k, v in entries}
    lookup[key] = updated_value
    return tuple(sorted(lookup.items()))


def update_traces(
    state: TraceState,
    context: int,
    action: str,
    scalar_positive: float,
    scalar_negative: float,
    *,
    frustration_rate: float,
    confidence_rate: float,
) -> TraceState:
    """Update frustration and confidence traces for one (context, action) pair.

    f_{t+1}(s_t, a_t) = (1 - eta_f) * f_t(s_t, a_t) + eta_f * epsilon_t^-
    c_{t+1}(s_t, a_t) = (1 - eta_c) * c_t(s_t, a_t) + eta_c * epsilon_t^+

    All other pairs remain unchanged.

    Args:
        state: Current trace state.
        context: Active context index s_t.
        action: Selected action a_t.
        scalar_positive: Aggregated positive error epsilon_t^+.
        scalar_negative: Aggregated negative error epsilon_t^-.
        frustration_rate: eta_f.
        confidence_rate: eta_c.

    Returns:
        New TraceState with updated entries.
    """
    old_f = get_frustration(state, context, action)
    old_c = get_confidence(state, context, action)

    new_frustration = _update_entries(
        state.frustration, context, action,
        old_f, scalar_negative, frustration_rate,
    )
    new_confidence = _update_entries(
        state.confidence, context, action,
        old_c, scalar_positive, confidence_rate,
    )

    return TraceState(
        frustration=new_frustration,
        confidence=new_confidence,
    )
