"""Trace state -- frustration and confidence dual-trace model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TraceState(BaseModel):
    """Dual-trace state: frustration f_t and confidence c_t.

    Both traces are non-negative functions over (context, action) pairs.
    Stored as sorted tuple of ((context, action), value) pairs.
    """

    model_config = ConfigDict(frozen=True)

    frustration: tuple[tuple[tuple[int, str], float], ...] = ()
    confidence: tuple[tuple[tuple[int, str], float], ...] = ()


def create_trace_state() -> TraceState:
    """Create initial trace state with all values at zero.

    f_0(s, a) = 0, c_0(s, a) = 0 for all (s, a).
    This ensures mu_H = 1 at t=0 (System A behavior).
    """
    return TraceState()


def _lookup(entries: tuple[tuple[tuple[int, str], float], ...],
            context: int, action: str) -> float:
    """Look up a value from sorted trace entries. Returns 0.0 if not found."""
    for key, val in entries:
        if key == (context, action):
            return val
    return 0.0


def get_frustration(state: TraceState, context: int, action: str) -> float:
    """Retrieve f_t(s, a). Returns 0.0 if pair not found."""
    return _lookup(state.frustration, context, action)


def get_confidence(state: TraceState, context: int, action: str) -> float:
    """Retrieve c_t(s, a). Returns 0.0 if pair not found."""
    return _lookup(state.confidence, context, action)
