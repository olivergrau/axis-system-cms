# AXIS Comparison Extension Developer Manual (v0.2.3)

> **Related manuals:**
> [Paired Trace Comparison](comparison-manual.md) |
> [System Development](system-dev-manual.md) |
> [CLI User Guide](cli-manual.md)

---

## Overview

The paired trace comparison framework is system-agnostic by default --
it compares actions, positions, and vitality without knowing anything
about the internals of the systems that produced the traces.

**Comparison extensions** allow a system to contribute domain-specific
analysis on top of the generic metrics. For example, System C registers
an extension that analyzes how its predictive modulation mechanism
affected action selection.

This manual explains the extension protocol, the data your extension
receives, and the step-by-step process for building and registering
a new extension.

---

## 1. Architecture

```
compare_episode_traces(reference, candidate)
      │
      ▼
  generic metrics (actions, position, vitality, outcome)
      │
      ▼
  build_system_specific_analysis(ref, cand, alignment)
      │
      ├── extension registered for candidate.system_type?
      │       yes ──► call extension(ref, cand, alignment)
      │       no  ──► return None
      │
      ▼
  PairedTraceComparisonResult.system_specific_analysis = result
```

Extensions are dispatched based on the **candidate** trace's
`system_type`. The framework never imports any system-specific
extension code -- extensions are discovered through the plugin system
at startup.

---

## 2. The SDK Protocol

Every comparison extension must satisfy the `ComparisonExtensionProtocol`
defined in `axis.sdk.comparison`:

```python
from typing import Any, Protocol
from axis.sdk.trace import BaseEpisodeTrace

class ComparisonExtensionProtocol(Protocol):
    def __call__(
        self,
        reference: BaseEpisodeTrace,
        candidate: BaseEpisodeTrace,
        alignment: Any,
    ) -> dict[str, Any] | None: ...
```

In practice, your extension is a **function** (not a class) decorated
with `@register_extension`. The protocol formalizes the callable
signature.

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `reference` | `BaseEpisodeTrace` | The baseline episode trace |
| `candidate` | `BaseEpisodeTrace` | The episode under test |
| `alignment` | `AlignmentSummary` | Shared-prefix alignment info |

**Return:** `dict[str, Any] | None`. Return a dict of metrics, or
`None` if no analysis is applicable. The dict is stored as-is in
`PairedTraceComparisonResult.system_specific_analysis`.

---

## 3. Input Data

### 3.1 BaseEpisodeTrace

The episode-level container (from `axis.sdk.trace`). Key fields:

| Field | Type | Description |
|---|---|---|
| `system_type` | `str` | System identifier (e.g. `"system_c"`) |
| `steps` | `tuple[BaseStepTrace, ...]` | All step traces |
| `total_steps` | `int` | Number of steps in the episode |
| `termination_reason` | `str` | Why the episode ended |
| `final_vitality` | `float` | Vitality at termination (0-1) |
| `world_type` | `str` | World type string |
| `world_config` | `dict[str, Any]` | World configuration |

### 3.2 BaseStepTrace

The step-level container. Key fields for extension authors:

| Field | Type | Description |
|---|---|---|
| `timestep` | `int` | Step number (0-based) |
| `action` | `str` | Action label chosen this step |
| `agent_position_before` | `Position` | Position before action |
| `agent_position_after` | `Position` | Position after action |
| `vitality_before` | `float` | Vitality before action (0-1) |
| `vitality_after` | `float` | Vitality after action (0-1) |
| `system_data` | `dict[str, Any]` | System-specific opaque data |

The `system_data` dict is where your system stores its per-step trace
information during execution. Your extension knows the internal
structure of this dict -- the framework does not.

> **Note:** Persisted traces may nest system-specific data differently
> from in-memory traces. For example, System C stores its data under
> `system_data["decision_data"]` on disk but flat in memory. Always
> handle both formats defensively.

### 3.3 AlignmentSummary

Describes how many steps are aligned between the two traces:

| Field | Type | Description |
|---|---|---|
| `reference_total_steps` | `int` | Total steps in reference |
| `candidate_total_steps` | `int` | Total steps in candidate |
| `aligned_steps` | `int` | `min(reference, candidate)` |
| `reference_extra_steps` | `int` | Unmatched reference tail |
| `candidate_extra_steps` | `int` | Unmatched candidate tail |

### 3.4 Constants

Two tolerance constants are available from `axis.framework.comparison.types`:

```python
from axis.framework.comparison.types import EQUALITY_EPSILON, RANKING_EPSILON

EQUALITY_EPSILON = 1e-9   # for exact float comparison
RANKING_EPSILON  = 1e-6   # for rank-order comparison
```

---

## 4. Iterating Aligned Steps

The `iter_aligned_steps` helper yields step pairs from the shared
prefix of two traces:

```python
from axis.framework.comparison.alignment import iter_aligned_steps

for ref_step, cand_step in iter_aligned_steps(reference, candidate):
    # ref_step and cand_step are BaseStepTrace objects
    # at the same timestep index
    pass
```

This is the standard way to walk through traces inside an extension.
It yields exactly `alignment.aligned_steps` pairs.

---

## 5. Registration

### 5.1 The `register_extension` decorator

```python
from axis.framework.comparison.extensions import register_extension

@register_extension("my_system")
def my_system_analysis(reference, candidate, alignment):
    ...
```

The string argument must exactly match the `system_type` field on
episode traces produced by your system. The framework dispatches on
`candidate.system_type`.

### 5.2 The registry API

```python
from axis.framework.comparison.extensions import (
    register_extension,          # decorator
    registered_extensions,       # introspection
    build_system_specific_analysis,  # dispatch (framework-internal)
)
```

- `registered_extensions()` returns a `tuple[str, ...]` of registered
  system types. Use this for idempotency guards.

### 5.3 Plugin integration

In your system's `__init__.py`, import the extension module inside
`register()` using the standard guarded pattern:

```python
def register() -> None:
    # ... system factory registration ...

    from axis.framework.comparison.extensions import registered_extensions

    if "my_system" not in registered_extensions():
        try:
            import axis.systems.my_system.comparison  # noqa: F401
        except ImportError:
            pass
```

The `try/except ImportError` makes the comparison extension optional.
If the comparison package is not available, the extension is simply
not registered and generic comparison still works.

---

## 6. Return Value Convention

Extensions should return a dict with a **single top-level key** that
namespaces the metrics:

```python
return {
    "my_system_metrics": {
        "custom_count": 42,
        "custom_rate": 0.85,
        "custom_mean_delta": 0.123,
    },
}
```

This convention prevents key collisions if multiple extensions
contribute to the same result. The dict is stored verbatim in
`PairedTraceComparisonResult.system_specific_analysis` and serialized
to JSON as-is.

Return `None` if your extension determines that no meaningful analysis
can be computed (e.g. the candidate trace lacks the expected data).

---

## 7. Complete Example

This example builds an extension for a hypothetical `system_x` that
tracks how often a custom "boost" mechanism was active.

### `src/axis/systems/system_x/comparison.py`

```python
from __future__ import annotations

from typing import Any

from axis.framework.comparison.alignment import iter_aligned_steps
from axis.framework.comparison.extensions import register_extension
from axis.framework.comparison.types import AlignmentSummary
from axis.sdk.trace import BaseEpisodeTrace


@register_extension("system_x")
def system_x_boost_analysis(
    reference: BaseEpisodeTrace,
    candidate: BaseEpisodeTrace,
    alignment: AlignmentSummary,
) -> dict[str, Any] | None:
    boost_active_count = 0
    total_aligned = alignment.aligned_steps

    if total_aligned == 0:
        return None

    for _ref_step, cand_step in iter_aligned_steps(reference, candidate):
        sd = cand_step.system_data or {}
        if sd.get("boost_active", False):
            boost_active_count += 1

    return {
        "system_x_boost": {
            "boost_active_count": boost_active_count,
            "boost_active_rate": boost_active_count / total_aligned,
        },
    }
```

### `src/axis/systems/system_x/__init__.py`

```python
def register() -> None:
    from axis.framework.registry import register_system, registered_system_types

    if "system_x" not in registered_system_types():
        register_system("system_x", lambda cfg: ...)

    from axis.framework.comparison.extensions import registered_extensions

    if "system_x" not in registered_extensions():
        try:
            import axis.systems.system_x.comparison  # noqa: F401
        except ImportError:
            pass
```

---

## 8. Real-World Reference: System C Extension

The System C extension at `src/axis/systems/system_c/comparison.py`
is the canonical example. It demonstrates:

- **Defensive data access**: `_get_decision_data()` handles both
  persisted (nested under `"decision_data"`) and in-memory (flat)
  trace formats.
- **Format normalization**: `_to_list()` handles scores stored as
  either dicts or lists.
- **Rank comparison with tolerance**: `_top_index_changed()` uses
  `RANKING_EPSILON` and returns `None` on ambiguous ties.
- **Multiple derived metrics**: counts, rates, and mean deltas
  computed in a single pass over aligned steps.

Metrics produced by the System C extension:

| Metric | Type | Description |
|---|---|---|
| `prediction_active_step_count` | `int` | Steps where modulation changed any score |
| `prediction_active_step_rate` | `float` | Fraction of aligned steps with active prediction |
| `top_action_changed_by_modulation_count` | `int` | Steps where modulation changed the top-ranked action |
| `top_action_changed_by_modulation_rate` | `float` | Fraction of aligned steps with changed top action |
| `ambiguous_top_action_count` | `int` | Steps where a tie made rank comparison ambiguous |
| `mean_modulation_delta` | `float` | Average absolute score difference from modulation |

---

## 9. Testing Extensions

Extensions can be tested without running experiments by constructing
synthetic traces:

```python
import pytest
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
from axis.framework.comparison.compare import compare_episode_traces


def test_boost_analysis():
    # Build synthetic traces with system_data containing boost info
    ref = make_episode([make_step(0)], system_type="system_a")
    cand = make_episode(
        [make_step(0, system_data={"boost_active": True})],
        system_type="system_x",
    )
    result = compare_episode_traces(ref, cand)
    ext = result.system_specific_analysis
    assert ext is not None
    assert ext["system_x_boost"]["boost_active_count"] == 1
```

See `tests/framework/comparison/test_comparison.py` for the full test
suite, including the `TestExtensionDispatch` and `TestSystemCExtension`
test classes.

> **Note:** Your test file must import the extension module to ensure
> the `@register_extension` decorator fires before any comparison
> function is called.

---

## 10. How It Fits Together

The comparison framework calls your extension automatically when
a comparison involves a candidate trace with your system type:

1. **Plugin startup**: `discover_plugins()` calls your system's
   `register()`, which imports your comparison module.
2. **Module import**: the `@register_extension` decorator fires,
   storing your function in the extension registry.
3. **Comparison**: `compare_episode_traces()` calls
   `build_system_specific_analysis()`, which looks up
   `candidate.system_type` in the registry.
4. **Your function runs**: receives the two traces and alignment,
   returns a metrics dict.
5. **Result**: your dict is stored in
   `PairedTraceComparisonResult.system_specific_analysis` and
   appears in both JSON and text CLI output.
