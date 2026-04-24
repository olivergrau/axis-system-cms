# AXIS Metrics Extension Developer Manual (v0.2.5)

> **Related manuals:**
> [CLI User Guide](cli-manual.md) |
> [System Development](system-dev-manual.md) |
> [Comparison Extensions](comparison-extension-manual.md) |
> [Experiment Workspaces](workspace-manual.md)
>
> **Tutorials:**
> [Building a System-Specific Metric](../tutorials/building-system-metrics.md)

---

## Overview

The AXIS behavioral metrics subsystem computes a set of framework-level
run metrics from replay-capable traces. These standard metrics are
system-agnostic: they know about actions, movement, resource gain,
coverage, revisit behavior, and policy shape, but they do not know the
internal semantics of a particular system.

**Metrics extensions** let a system contribute its own analysis on top
of those standard metrics. This mirrors the extension model used by
visualization and paired-trace comparison:

- the framework owns orchestration, loading, persistence, and display
- a system may register an optional metrics extension
- the extension receives replay-capable episode traces and the already
  computed standard metrics
- the extension returns a namespaced dictionary of system-specific
  metrics

System C already uses this mechanism to expose predictive metrics such
as mean prediction error and modulation strength.

---

## 1. Architecture

```text
load_or_compute_run_behavior_metrics(repo, experiment_id, run_id)
      │
      ▼
load replay-capable traces for the run
      │
      ▼
compute framework standard metrics
      │
      ▼
build_system_behavior_metrics(system_type, traces, standard_metrics)
      │
      ├── extension registered for system_type?
      │       yes ──► call extension(traces, standard_metrics)
      │       no  ──► return None
      │
      ▼
persist behavior_metrics.json
      │
      ▼
show via `axis runs show`, `axis runs metrics`,
or `axis workspaces run-metrics`
```

The framework treats system-specific metrics as an optional add-on. If
no extension is registered, standard metrics still work normally.

---

## 2. Trace Mode Requirements

Metrics extensions are defined only for **replay-capable** trace modes:

- `full`
- `delta`

`light` is intentionally out of scope. A metrics extension should assume
that it receives complete `BaseEpisodeTrace` objects reconstructed from
persisted run artifacts.

If a run has no replay-capable traces, behavioral metrics are not
computed.

---

## 3. The SDK Protocol

Every metrics extension must satisfy
`MetricExtensionProtocol` from `axis.sdk.metrics`:

```python
from typing import Any, Protocol
from axis.sdk.trace import BaseEpisodeTrace


class MetricExtensionProtocol(Protocol):
    def __call__(
        self,
        episode_traces: tuple[BaseEpisodeTrace, ...],
        standard_metrics: Any,
    ) -> dict[str, Any] | None: ...
```

In practice, an extension is usually a function decorated with
`@register_metric_extension(...)`.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `episode_traces` | `tuple[BaseEpisodeTrace, ...]` | All replay-capable episode traces for the run |
| `standard_metrics` | `StandardBehaviorMetrics` | The framework-computed standard metrics for the same run |

### Return value

Return `dict[str, Any] | None`.

- Return a namespaced metrics dictionary when analysis is available.
- Return `None` if the extension cannot compute anything meaningful.

The returned dictionary is stored under
`system_specific_metrics` in `behavior_metrics.json`.

---

## 4. What Data Your Extension Receives

### 4.1 Episode traces

Each extension receives the run as a tuple of `BaseEpisodeTrace`
objects. These include:

- `system_type`
- `steps`
- `total_steps`
- `termination_reason`
- `final_vitality`
- `world_type`
- `world_config`

### 4.2 Step traces

Each `BaseStepTrace` provides:

- `action`
- `agent_position_before`
- `agent_position_after`
- `vitality_before`
- `vitality_after`
- `system_data`

The crucial field for system authors is `system_data`. This is where
your system's `decision_data` and `trace_data` end up after execution.
Extensions are expected to understand that structure for their own
system type.

### 4.3 Standard metrics

The `standard_metrics` parameter lets your extension reuse framework
results instead of recomputing them. That is useful when your custom
metrics are ratios, correlations, or augmentations of existing
behavioral summaries.

For example, a system might compare its own internal arbitration signal
against:

- `action_entropy`
- `failed_movement_rate`
- `coverage_efficiency`

This keeps extension logic focused on genuinely system-specific meaning.

---

## 5. Registration

### 5.1 The decorator

Register your extension with
`axis.framework.metrics.extensions.register_metric_extension`:

```python
from axis.framework.metrics.extensions import register_metric_extension


@register_metric_extension("my_system")
def my_system_metrics(episode_traces, standard_metrics):
    ...
```

The string must match the `system_type` produced by your system.

### 5.2 The registry API

```python
from axis.framework.metrics.extensions import (
    register_metric_extension,
    registered_metric_extensions,
    build_system_behavior_metrics,
)
```

- `registered_metric_extensions()` returns the currently registered
  system types.
- `build_system_behavior_metrics(...)` is the framework dispatch entry
  point.

### 5.3 Plugin integration

In your system package's `__init__.py`, import the metrics module during
registration using the same guarded pattern used by other extension
systems:

```python
def register() -> None:
    # ... system factory registration ...

    from axis.framework.metrics.extensions import registered_metric_extensions

    if "my_system" not in registered_metric_extensions():
        try:
            import axis.systems.my_system.metrics  # noqa: F401
        except ImportError:
            pass
```

This keeps the metrics extension optional. If the module is missing,
system execution still works.

---

## 6. Return Value Convention

Extensions should return a dictionary with a single top-level namespace:

```python
return {
    "my_system_metrics": {
        "custom_mean": 0.42,
        "custom_rate": 0.85,
        "custom_count": 17,
    },
}
```

This avoids key collisions and makes CLI output easier to read.

Use metric names that are:

- descriptive
- stable
- scalar when possible
- JSON-serializable

If you need richer structures, prefer flat dictionaries over deeply
nested payloads unless nesting reflects a real conceptual grouping.

---

## 7. Design Guidelines

Good system-specific metrics usually have three properties:

1. They explain behavior the framework cannot infer generically.
2. They derive directly from persisted trace fields.
3. They remain interpretable when averaged across episodes.

Good examples:

- prediction error metrics for System C
- arbitration balance metrics for System A+W
- memory-confidence or novelty-pressure metrics for future systems

Less useful metrics:

- values already present in standard metrics under another name
- metrics that depend on unpersisted internal state
- metrics with unstable semantics across runs or worlds

When possible, build metrics from persisted `decision_data` and
`trace_data`, not from transient implementation details.

---

## 8. Complete Example: System C

System C already ships with a metrics extension in
`src/axis/systems/system_c/metrics.py`.

Its structure is representative:

```python
@register_metric_extension("system_c")
def system_c_behavior_metrics(
    episode_traces: tuple[BaseEpisodeTrace, ...],
    standard_metrics: StandardBehaviorMetrics,
) -> dict[str, Any]:
    ...
    return {
        "system_c_prediction": {
            "mean_prediction_error": ...,
            "signed_prediction_error": ...,
            "confidence_trace_mean": ...,
            "frustration_trace_mean": ...,
            "prediction_modulation_strength": ...,
            "prediction_step_count": ...,
        },
    }
```

This works because System C persists prediction-related data into
per-step trace payloads. The framework does not know what those fields
mean; it only loads traces and calls the extension.

That is the intended pattern:

- put system semantics into trace payloads
- keep the extension small and analytical
- let the framework handle the rest

---

## 9. Testing Strategy

A good metrics extension should have three layers of tests:

### 9.1 Unit tests for the extension function

Construct small synthetic traces and verify the returned metrics.

### 9.2 Registration tests

Verify that your system registers the extension exactly once and that
the expected system type appears in `registered_metric_extensions()`.

### 9.3 Integration tests

Run a small real experiment and verify that:

- `behavior_metrics.json` is created
- the namespaced system-specific metrics appear
- `axis runs metrics` shows them correctly

---

## 10. User-Facing Commands

Once a metrics extension is registered, users do not need to call it
directly. The framework will surface the results through:

- `axis runs show <run-id> --experiment <eid>`
- `axis runs metrics <run-id> --experiment <eid>`
- `axis workspaces run-metrics <workspace>`

If `behavior_metrics.json` does not exist yet, the framework computes it
on demand from persisted replay-capable traces.

---

## 11. Common Pitfalls

### Missing trace fields

If your extension depends on internal values, make sure the system
actually persists them into `decision_data` or `trace_data`.

### Overly coupled metrics

Do not make a metrics extension reach back into live system objects or
config internals unless that data is already persisted into the run.

### Recomputing framework metrics

Reuse `standard_metrics` instead of recalculating generic behavior.

### Non-namespaced return values

Always wrap your output in a top-level namespace key.

### Assuming `light` support

Metrics extensions should assume `full` or `delta`, never `light`.

---

## 12. Recommended Development Flow

1. Decide what system-specific behavior you want to measure.
2. Verify that the necessary signals are already present in the trace.
3. Add missing trace fields if needed.
4. Implement `metrics.py` with a registered extension.
5. Register it from your system package's `register()` function.
6. Add unit and integration tests.
7. Run a small experiment and inspect the output with:
   - `axis runs metrics`
   - `axis workspaces run-metrics`

For a hands-on walkthrough, see the tutorial:
[Building a System-Specific Metric](../tutorials/building-system-metrics.md).
