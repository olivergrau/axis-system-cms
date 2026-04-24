# AXIS Enhanced Metrics

## Engineering Specification for an Extension-Capable Behavioral Metrics Layer

---

## 1. Purpose

This engineering specification translates the enhanced-metrics spec into a
concrete implementation direction for the current AXIS codebase.

Its purpose is to define:

- where the behavioral metrics layer should live
- how it should reuse existing AXIS extension patterns
- how framework-standard and system-specific metrics should be composed
- how metric artifacts should be persisted and surfaced
- which existing modules should be extended in the first implementation wave

This document is intentionally implementation-oriented.

It is the bridge between:

- the behavioral metrics spec
- and a practical, low-risk implementation on the present AXIS system


## 2. Current System Baseline

The current AXIS system already provides most of the raw material needed for a
first behavioral metrics layer.

### 2.1 Replay-capable episode traces already exist

The fundamental trace contract is in:

- [src/axis/sdk/trace.py](/workspaces/axis-system-cms/src/axis/sdk/trace.py)

`BaseStepTrace` already contains:

- action
- world snapshots
- positions
- vitality before / after
- system-specific data
- world-specific data

This is sufficient for the first wave of trace-derived behavioral metrics.

Delta traces are also already supported and reconstructible into full replay
traces, which means the metrics layer can rely on the existing replay contract
after load-time reconstruction instead of inventing a second analysis path.

### 2.2 Current run summaries are intentionally minimal

Run-level summary aggregation currently lives in:

- [src/axis/framework/run.py](/workspaces/axis-system-cms/src/axis/framework/run.py)

`RunSummary` today contains only:

- `mean_steps`
- `std_steps`
- `mean_final_vitality`
- `std_final_vitality`
- `death_rate`

This is useful because it means we do not need to retrofit the existing summary
contract aggressively. The enhanced metrics layer can remain additive.

### 2.3 The repository already supports replay-oriented loading

Artifact loading currently lives in:

- [src/axis/framework/persistence.py](/workspaces/axis-system-cms/src/axis/framework/persistence.py)

This is especially important because:

- `load_episode_trace(...)` already reconstructs `delta` into
  `BaseEpisodeTrace`
- `list_runs(...)` and `list_episode_files(...)` already provide discovery
- `load_run_summary(...)` and `load_run_result(...)` already support run-level
  inspection

So the behavioral metrics layer should build on repository loading, not bypass
it.

### 2.4 AXIS already has an extension pattern we should reuse

The closest existing architectural analogue is the comparison extension system:

- [src/axis/framework/comparison/extensions.py](/workspaces/axis-system-cms/src/axis/framework/comparison/extensions.py)
- [src/axis/systems/system_c/comparison.py](/workspaces/axis-system-cms/src/axis/systems/system_c/comparison.py)
- [src/axis/framework/catalogs.py](/workspaces/axis-system-cms/src/axis/framework/catalogs.py)

This gives us several useful patterns:

- string-keyed registration by `system_type`
- optional system-specific extension modules
- framework-owned orchestration
- system-owned domain-specific analysis
- catalog bridging for dependency-injected dispatch

This is the right model to copy for enhanced metrics.


## 3. Engineering Goal

The engineering goal for version 1 is:

> add a run-level behavioral metrics subsystem that computes framework-standard
> metrics from replay-capable traces and optionally augments them with
> system-specific metric extensions

This subsystem should:

- work for `full`
- work for `delta`
- not support `light`
- preserve current run summaries
- reuse the current plugin/registry/catal og pattern


## 4. Architectural Shape

The cleanest implementation shape is:

```text
persisted run artifacts
-> repository loads replay-capable traces
-> framework computes standard metrics
-> framework dispatches optional system metric extension
-> framework assembles one run-level behavioral metric artifact
-> CLI / workspace inspection renders the result
```

This keeps the responsibilities clear:

- repository loads data
- framework computes and orchestrates
- systems contribute optional extensions
- CLI and workspaces consume the final artifact


## 5. Recommended Module Layout

The current codebase suggests a dedicated metrics package under the framework.

Recommended first-wave module layout:

```text
src/axis/framework/metrics/
    __init__.py
    types.py
    compute.py
    standard.py
    aggregate.py
    extensions.py
    loader.py
```

Recommended responsibilities:

- `types.py`
  - behavioral metric result models
- `standard.py`
  - standard metric computation from episode traces
- `aggregate.py`
  - run-level aggregation helpers
- `extensions.py`
  - system-specific metric extension registry and dispatch
- `compute.py`
  - top-level orchestration for one run
- `loader.py`
  - helpers that load all traces for one run from the repository

This keeps the subsystem coherent and avoids scattering metric logic across
existing unrelated modules.


## 6. Data Model Recommendation

The engineering design should introduce a new persisted run-level artifact.

### 6.1 New run-level artifact

Recommended artifact:

- `behavior_metrics.json`

Recommended repository path:

- `results/<experiment-id>/runs/<run-id>/behavior_metrics.json`

This mirrors existing run-local artifacts such as:

- `run_config.json`
- `run_summary.json`
- `run_result.json`

### 6.2 Recommended top-level model

The top-level model should distinguish three layers:

- run identity and applicability metadata
- standard framework metrics
- system-specific extension metrics

A plausible structure is:

```text
RunBehaviorMetrics
    experiment_id
    run_id
    system_type
    trace_mode
    num_episodes
    metric_mode
    standard_metrics
    system_specific_metrics
```

Where:

- `metric_mode` can initially simply mean:
  - `replay_capable`
- `standard_metrics` is a typed framework-owned object
- `system_specific_metrics` is a namespaced dict-like payload

### 6.3 Episode-level versus run-level model

The first implementation wave should compute metrics at episode level and then
aggregate to run level.

That suggests two internal model layers:

- `EpisodeBehaviorMetrics`
- `RunBehaviorMetrics`

The persisted artifact should probably only store the run-level aggregate in
v1, to keep artifact size modest.

If later needed, episode-level metric artifacts can be added separately.


## 7. Standard Metric Computation

The standard metric layer should be framework-owned and entirely trace-derived.

### 7.1 Episode-level computation

Standard metrics should be computed from `BaseEpisodeTrace`.

Recommended helpers:

- `_compute_resource_metrics(trace)`
- `_compute_structure_metrics(trace)`
- `_compute_exploration_metrics(trace)`
- `_compute_failure_metrics(trace)`

This keeps each metric family easy to test.

### 7.2 Aggregation strategy

Run-level aggregation should use simple summary statistics over episode metrics.

Recommended baseline summary statistics:

- mean
- std
- min
- max
- count

This mirrors the statistical style already used in comparison summary code:

- [src/axis/framework/comparison/summary.py](/workspaces/axis-system-cms/src/axis/framework/comparison/summary.py)

That existing summary approach is a good pattern to reuse.

### 7.3 Recommended standard metric families in v1

Framework-standard metrics should include:

- survival baseline:
  - mean steps
  - death rate
  - mean final vitality
- resource efficiency:
  - resource gain per step
  - net energy efficiency
  - successful consume rate
  - consume-on-empty rate
- behavioral structure:
  - action entropy
  - policy sharpness
  - action inertia
- failure avoidance:
  - failed movement rate
- exploration:
  - unique cells visited
  - coverage efficiency
  - revisit rate

These metrics are directly derivable from current traces and do not require
formal context semantics.


## 8. Extension System Recommendation

The behavioral metrics subsystem should deliberately mirror the comparison
extension architecture.

### 8.1 Registry module

Recommended module:

- `src/axis/framework/metrics/extensions.py`

Recommended core API shape:

- `register_metric_extension(system_type: str)`
- `registered_metric_extensions()`
- `build_system_behavior_metrics(...)`

This closely parallels:

- [src/axis/framework/comparison/extensions.py](/workspaces/axis-system-cms/src/axis/framework/comparison/extensions.py)

### 8.2 Extension dispatch model

Dispatch should be based on the run's `system_type`.

Unlike paired comparison, behavioral metrics are run-internal rather than
reference/candidate oriented.

So the extension should receive inputs such as:

- the run's episode traces
- or the already computed standard episode metrics plus traces

The better first-wave choice is:

- give the extension the run's replay-capable episode traces
- and optionally the standard run metrics result

This keeps extensions flexible without forcing them to recompute standard
metrics or depend on hidden runtime state.

### 8.3 Extension output model

Extensions should return a namespaced dictionary, similar in spirit to
comparison extensions.

Example:

```text
{
  "system_c_prediction": {
    ...
  }
}
```

This pattern is already familiar in AXIS and avoids key collisions.

### 8.4 Catalog integration

The current catalog bridge in:

- [src/axis/framework/catalogs.py](/workspaces/axis-system-cms/src/axis/framework/catalogs.py)

should be extended with a new catalog type:

- `MetricExtensionCatalog`

and a new built catalog key such as:

- `metric_extensions`

This allows:

- ordinary plugin discovery
- constructor injection in tests
- symmetry with the comparison subsystem


## 9. SDK Boundary Recommendation

The enhanced metrics idea should define an explicit SDK protocol for metric
extensions, analogous to `ComparisonExtensionProtocol`.

Recommended new SDK location:

- `src/axis/sdk/metrics.py`

Recommended contract shape:

- a callable protocol
- replay-capable trace inputs
- structured dict output or `None`

Conceptually:

```text
MetricExtensionProtocol:
    (episode_traces, context) -> dict[str, Any] | None
```

The precise signature can stay lightweight, but the contract should be explicit
and documented.

This is important because the framework should never need to understand system
internals directly.


## 10. System Integration Recommendation

Systems with domain-specific metrics should follow the same registration style
already used for comparison extensions.

### 10.1 Example: `system_c`

`system_c` is the best first extension candidate because it already exposes:

- prediction context
- predicted features
- observed features
- positive/negative prediction error
- modulated scores

These are available in:

- [src/axis/systems/system_c/system.py](/workspaces/axis-system-cms/src/axis/systems/system_c/system.py)
- [src/axis/systems/system_c/transition.py](/workspaces/axis-system-cms/src/axis/systems/system_c/transition.py)

Recommended new module:

- `src/axis/systems/system_c/metrics.py`

Recommended registration pattern:

- import the metric extension module from `system_c.register()`
- guard duplicate registration in the same way as comparison and visualization
  integration

### 10.2 Future systems

This same pattern should later support:

- `system_aw`
- `system_cw`
- or any future system with system-specific internal metrics


## 11. Repository and Persistence Changes

The repository should gain dedicated save/load methods for behavioral metrics.

Recommended additions to:

- [src/axis/framework/persistence.py](/workspaces/axis-system-cms/src/axis/framework/persistence.py)

New path method:

- `behavior_metrics_path(experiment_id, run_id)`

New save/load methods:

- `save_behavior_metrics(...)`
- `load_behavior_metrics(...)`

This keeps the artifact contract explicit and avoids overloading
`run_summary.json`.

### 11.1 Trace-mode guard

The loader or compute path should explicitly reject:

- `trace_mode == "light"`

with a clear error.

That behavior should be centralized rather than reimplemented ad hoc in each
consumer.


## 12. Framework Execution and Backfill Strategy

There are two plausible ways to populate the artifact.

### Option A: Compute during experiment execution

Pros:

- artifact exists immediately after run completion

Cons:

- execution pipeline becomes heavier
- metric rollout becomes coupled to experiment runtime

### Option B: Compute as a post-run analysis step

Pros:

- lower risk
- easier to test
- easier to rerun when metric definitions evolve
- cleaner for old artifacts and workspace backfills

Cons:

- requires explicit compute trigger

Recommended first-wave direction:

- **Option B**

The subsystem should first exist as an explicit post-run analysis layer.

That means:

- compute from persisted run artifacts
- persist `behavior_metrics.json`
- then let CLI / workspace commands read it

Later, AXIS may choose to auto-materialize metrics after successful run
completion.


## 13. CLI and Workspace Integration

The first consumer surfaces should likely be:

- `axis runs show`
- `axis experiments show`
- workspace inspection paths

### 13.1 `runs show`

Recommended behavior:

- if `behavior_metrics.json` exists, show a compact behavioral metrics section
- if not, either omit it or clearly say behavioral metrics are not available

### 13.2 `experiments show`

For v1, experiment-level aggregation is optional.

So `experiments show` should probably only report presence/availability rather
than attempting to summarize all behavioral metrics across runs unless an
experiment-level artifact is later introduced.

### 13.3 Workspace integration

Workspace commands that currently resolve run summaries can later gain an
adjacent behavioral metrics view, but this should not be a blocking dependency
for the first engineering wave.

Recommended posture:

- first implement run-level analysis and inspection
- then wire workspaces once the artifact model is stable


## 14. Relationship to Existing Comparison Metrics

The engineering design should keep a hard boundary between:

- behavioral metrics
- paired divergence metrics

Current divergence metrics in:

- [src/axis/framework/comparison/metrics.py](/workspaces/axis-system-cms/src/axis/framework/comparison/metrics.py)

operate on aligned reference/candidate traces.

Behavioral metrics, by contrast, should operate on:

- one run
- many episodes
- no paired alignment requirement

Some underlying helpers may later be shared, but the subsystem boundary should
remain separate.


## 15. Testing Strategy

The engineering plan should include four testing layers.

### 15.1 Standard metric unit tests

Add hand-checkable episode traces and verify:

- action entropy
- failed movement rate
- consume rates
- coverage and revisit calculations
- resource gain / cost calculations

### 15.2 Aggregation tests

Verify run-level summary statistics over multiple episodes.

### 15.3 Trace parity tests

Verify identical metric results for:

- native `full` traces
- reconstructed `delta` traces

### 15.4 Extension tests

Verify:

- registration
- dispatch
- graceful absence of extension
- `system_c` predictive metric outputs from known traces


## 16. Migration and Rollout Recommendation

The safest rollout is:

1. add framework metric types and standard computation
2. add repository artifact support
3. add extension registry and SDK protocol
4. implement `system_c` metric extension
5. add CLI inspection support
6. only afterwards consider workspace integration and auto-computation

This sequence keeps the architectural risk low and allows each layer to be
validated before the next one depends on it.


## 17. Key Open Choices

Most of the architecture is already clear enough to proceed.

The remaining choices are mainly about preferred shape, not feasibility:

- whether the extension callable should receive:
  - only episode traces
  - or episode traces plus the computed standard metrics object
- whether v1 should persist only run-level aggregates
  - or also episode-level metric details
- whether metric computation should start as:
  - explicit CLI-triggered analysis
  - or immediate post-run materialization

My recommendation on all three is:

- traces plus optional analysis context
- persist run-level aggregates only
- start with explicit post-run analysis


## 18. Recommendation

The enhanced metrics subsystem is very feasible on the current AXIS system if
it is built as:

- a dedicated framework metrics package
- a separate persisted run-level artifact
- a standard-metrics core
- plus a comparison-style system extension mechanism

This direction fits the current AXIS architecture well because it reuses:

- replay-capable trace contracts
- repository loading
- catalog-based extension dispatch
- system-local registration patterns

The best first engineering slice is therefore:

- standard run-level behavioral metrics for `full` and `delta`
- a new metric extension registry
- and one concrete `system_c` extension to prove the pattern
