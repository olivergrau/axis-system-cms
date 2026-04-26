# Traces

The **traces** package provides dual-trace dynamics for tracking
frustration and confidence. These traces accumulate signed prediction
errors over time using exponential moving averages (EMA) with
asymmetric learning rates.

**Import path:** `from axis.systems.construction_kit.traces import ...`

**Source:** `src/axis/systems/construction_kit/traces/`

---

## Trace State

Stores frustration and confidence values per (context, action) pair.

```python
from axis.systems.construction_kit.traces.state import (
    TraceState,
    create_trace_state,
    get_frustration,
    get_confidence,
)

traces = create_trace_state()                     # all zeros
f = get_frustration(traces, context=5, action="up")  # 0.0
c = get_confidence(traces, context=5, action="up")   # 0.0
```

`TraceState` is a frozen Pydantic model with two fields:

- `frustration` -- accumulated negative prediction error per (context, action)
- `confidence` -- accumulated positive prediction error per (context, action)

Both default to empty (all zeros). Lookups for unknown pairs return 0.0.

The trace package is intentionally **drive-agnostic**. A concrete system
may keep:

- one trace state for the whole predictive layer, as in System C
- or multiple independent trace states, as in System C+W

System C+W uses the same `TraceState` type twice:

- one hunger trace state
- one curiosity trace state

This preserves the generic update rule while allowing drive-specific
confidence/frustration dynamics.

---

## Trace Update

Updates frustration and confidence for a single (context, action) pair.

```python
from axis.systems.construction_kit.traces.update import update_traces

new_traces = update_traces(
    traces,
    context=5, action="up",
    scalar_positive=0.1,    # epsilon_t^+
    scalar_negative=0.0,    # epsilon_t^-
    frustration_rate=0.2,   # eta_f
    confidence_rate=0.15,   # eta_c
)
```

Update rules (EMA):

$$
f_{t+1}(s_t, a_t) = (1 - \eta_f) \cdot f_t(s_t, a_t) + \eta_f \cdot \varepsilon_t^-
$$

$$
c_{t+1}(s_t, a_t) = (1 - \eta_c) \cdot c_t(s_t, a_t) + \eta_c \cdot \varepsilon_t^+
$$

The asymmetric learning rates ($\eta_f > \eta_c$ by default) implement
**loss aversion**: disappointment accumulates faster than positive
reinforcement. This makes the agent quicker to avoid actions that
produce negative surprises than to seek actions that produce positive
ones.

Nothing in the update rule assumes a specific drive semantics. The
scalar positive and negative evidence can come from:

- hunger-side predictive outcome error
- curiosity-side predictive outcome error
- or any future drive-specific predictive channel

| Parameter | Symbol | Default | Role |
|-----------|:------:|:-------:|------|
| `frustration_rate` | $\eta_f$ | 0.2 | EMA rate for frustration |
| `confidence_rate` | $\eta_c$ | 0.15 | EMA rate for confidence |

---

## See Also

- [Prediction](prediction.md) -- prediction error computation that feeds into traces
- [Modulation](modulation.md) -- exponential modulation from trace values
- [System C+W Math Spec](../system-design/system-cw/index.md) -- example of one shared predictive memory with two independent trace states
