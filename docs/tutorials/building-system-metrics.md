# Building a System-Specific Metric

> **Related manuals:**
> [Metrics Extension Developer Manual](../manuals/metrics-extension-manual.md) |
> [System Development](../manuals/system-dev-manual.md) |
> [System A+W](../manuals/system-aw-manual.md)

This tutorial shows how to add a **system-specific behavioral metric**
to AXIS using `system_aw` as the example system.

We will design and implement a small but meaningful metric:

- `curiosity_dominance_rate`

This metric answers a simple question:

> Across the run, how often did curiosity outweigh hunger in the
> arbitration mechanism?

That makes it a good tutorial example because:

- it is genuinely system-specific
- it is easy to interpret
- the needed data is already present in `system_aw` traces

---

## 1. What We Want to Measure

System A+W combines two drives:

- hunger
- curiosity

At decision time, the system computes arbitration weights and stores
them in the step trace:

```python
"arbitration": {
    "hunger_weight": weights.hunger_weight,
    "curiosity_weight": weights.curiosity_weight,
}
```

So a natural metric is:

```text
curiosity_dominance_rate =
  (# steps where curiosity_weight > hunger_weight) / (# traced steps)
```

This is useful because it tells us whether a run was mostly governed by
exploration pressure or mostly by energy preservation.

We will also compute:

- `mean_curiosity_weight`
- `mean_hunger_weight`

These make the dominance rate easier to interpret.

---

## 2. Confirm the Trace Data Exists

Before writing any extension, check whether the system already persists
the signals you need.

In `src/axis/systems/system_aw/system.py`, the decision trace includes:

```python
"arbitration": {
    "hunger_weight": weights.hunger_weight,
    "curiosity_weight": weights.curiosity_weight,
}
```

That means we do **not** need to change the runner or persistence layer.
The data is already present in replay-capable traces.

---

## 3. Create `metrics.py`

Add a new file:

`src/axis/systems/system_aw/metrics.py`

with this content:

```python
from __future__ import annotations

from typing import Any

from axis.framework.metrics.extensions import register_metric_extension
from axis.framework.metrics.types import StandardBehaviorMetrics
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace


def _decision_data(step: BaseStepTrace) -> dict[str, Any]:
    system_data = step.system_data or {}
    data = system_data.get("decision_data", {})
    return data if isinstance(data, dict) else {}


@register_metric_extension("system_aw")
def system_aw_behavior_metrics(
    episode_traces: tuple[BaseEpisodeTrace, ...],
    standard_metrics: StandardBehaviorMetrics,
) -> dict[str, Any]:
    del standard_metrics

    hunger_weights: list[float] = []
    curiosity_weights: list[float] = []
    dominance_steps = 0
    total_steps = 0

    for trace in episode_traces:
        for step in trace.steps:
            decision = _decision_data(step)
            arbitration = decision.get("arbitration", {}) or {}
            if not isinstance(arbitration, dict):
                continue

            hunger = float(arbitration.get("hunger_weight", 0.0))
            curiosity = float(arbitration.get("curiosity_weight", 0.0))

            hunger_weights.append(hunger)
            curiosity_weights.append(curiosity)
            total_steps += 1

            if curiosity > hunger:
                dominance_steps += 1

    def _mean(values: list[float]) -> float | None:
        if not values:
            return None
        return sum(values) / len(values)

    curiosity_dominance_rate = (
        dominance_steps / total_steps if total_steps > 0 else None
    )

    return {
        "system_aw_arbitration": {
            "curiosity_dominance_rate": curiosity_dominance_rate,
            "mean_curiosity_weight": _mean(curiosity_weights),
            "mean_hunger_weight": _mean(hunger_weights),
            "arbitrated_step_count": total_steps,
        }
    }
```

This follows the standard AXIS pattern:

- read replay-capable traces
- extract system-specific data from `decision_data`
- compute stable scalar summaries
- return them under a namespaced key

---

## 4. Register the Extension

Next, import the new module during system registration.

In `src/axis/systems/system_aw/__init__.py`, add the same guarded
pattern used by other extension systems:

```python
def register() -> None:
    # existing system registration logic...

    from axis.framework.metrics.extensions import registered_metric_extensions

    if "system_aw" not in registered_metric_extensions():
        try:
            import axis.systems.system_aw.metrics  # noqa: F401
        except ImportError:
            pass
```

This keeps the metrics layer optional and idempotent.

---

## 5. Why This Metric Is Useful

`curiosity_dominance_rate` is more informative than a raw curiosity
value alone.

It can help answer questions like:

- Did this parameter setting actually favor exploration?
- Did hunger suppress curiosity almost all the time?
- Across two runs, did one system spend more of its time in
  curiosity-led behavior?

Because the metric is aggregated over the run, it works well alongside
standard metrics such as:

- `coverage_efficiency`
- `revisit_rate`
- `action_entropy`
- `failed_movement_rate`

For example, a high `curiosity_dominance_rate` combined with high
coverage and low revisit rate would support the interpretation that the
agent was genuinely exploring novel space.

---

## 6. Run an Experiment

After implementing the extension, run any replay-capable A+W experiment.

For example:

```bash
axis run path/to/system-aw-config.yaml
```

Then inspect the resulting run:

```bash
axis runs metrics <run-id> --experiment <experiment-id>
```

or, if you are using a workspace:

```bash
axis workspaces run-metrics path/to/workspace
```

You should see a `System Metrics` section containing something like:

```text
system_aw_arbitration
  curiosity_dominance_rate: 0.41
  mean_curiosity_weight: 0.37
  mean_hunger_weight: 0.63
  arbitrated_step_count: 200
```

---

## 7. Add Tests

A minimal test suite should include:

### Unit test

Build a tiny synthetic trace with known arbitration weights and verify:

- the rate is correct
- the means are correct
- the top-level namespace key is correct

### Registration test

Verify that importing and registering `system_aw` exposes
`"system_aw"` in `registered_metric_extensions()`.

### CLI integration test

Run a small experiment and confirm that:

- `behavior_metrics.json` is created
- `axis runs metrics` shows the new metrics

---

## 8. Variations You Could Build Next

Once the basic extension works, A+W offers several natural follow-up
metrics:

- `mean_spatial_novelty`
- `mean_sensory_novelty`
- `hunger_curiosity_balance`
- `consume_under_curiosity_pressure_rate`
- `curiosity_weight_vs_coverage_correlation`

These all reuse the same extension structure. The main design rule is
the same: only compute metrics from signals that are already persisted
into replay-capable traces.

---

## 9. Summary

You now have the full development loop for a system-specific metric:

1. identify a meaningful internal signal
2. verify it is persisted in step traces
3. implement a registered metrics extension
4. register it with the system package
5. inspect it through AXIS CLI and workspace commands

This is the intended AXIS workflow for behavioral metric extensions:
the framework owns the pipeline, and systems contribute meaning.
