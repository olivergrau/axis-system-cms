"""Trace dynamics -- frustration and confidence accumulation.

Provides:
- TraceState: dual-trace state z_t = (f_t, c_t)
- update_traces: EMA update for one (context, action) pair
"""

from axis.systems.construction_kit.traces.state import (
    TraceState,
    create_trace_state,
    get_confidence,
    get_frustration,
)
from axis.systems.construction_kit.traces.update import update_traces

__all__ = [
    "TraceState",
    "create_trace_state",
    "get_confidence",
    "get_frustration",
    "update_traces",
]
