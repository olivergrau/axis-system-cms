# Enhanced Metrics -- Implementation Roadmap

**Based on:** `spec.md`, `engineering-spec.md`  
**Date:** 2026-04-24

---

## Overview

The implementation should follow a low-risk layered order:

1. establish the framework-owned behavioral metrics core
2. define a separate behavioral metrics artifact and repository support
3. add an extension mechanism for system-specific metrics
4. implement one real extension in `system_c`
5. surface the results in CLI and then workspaces
6. harden parity, testing, and documentation

This order matters.

The current AXIS codebase already has:

- replay-capable trace loading
- delta reconstruction
- a comparison extension pattern
- plugin/catalog integration

So the first implementation wave should not start by expanding every user-facing
surface at once.

It should first create the stable internal metrics subsystem and artifact model
that all later consumers can rely on.


## Delivery Strategy

The roadmap should proceed in six layers:

1. **Metrics Core Foundation**  
   Introduce framework-owned types, standard metric computation, and run-level
   aggregation.
2. **Persistence and Repository Layer**  
   Add a dedicated behavioral metrics artifact and repository support.
3. **Metric Extension Infrastructure**  
   Mirror the comparison extension pattern for system-specific metrics.
4. **First Concrete Extension**  
   Implement `system_c` as the first proof that extension metrics work.
5. **Consumer Integration**  
   Add CLI inspection first, then workspace integration.
6. **Hardening and Documentation**  
   Validate `full`/`delta` parity, extension dispatch, and public docs.


## Dependency Graph

```text
WP-01
  |
WP-02
  |
WP-03
 /   \
WP-04 WP-05
  \   /
   WP-06
     |
   WP-07
     |
   WP-08
```

Interpretation:

- `WP-01` defines the metric types and standard computation
- `WP-02` makes the results persistable and loadable
- `WP-03` adds the reusable extension subsystem
- `WP-04` and `WP-05` can proceed once the extension foundation exists
- `WP-06` integrates the first concrete system extension
- `WP-07` surfaces the subsystem in CLI / workspace flows
- `WP-08` hardens tests, docs, and rollout behavior


## Work Packages

### WP-01 -- Framework Metrics Core

Introduce the framework-owned behavioral metrics subsystem.

Scope:

- add a dedicated `src/axis/framework/metrics/` package
- define standard metric models
- define episode-level internal metric computation
- define run-level aggregation
- support only replay-capable traces:
  - `full`
  - `delta`
- explicitly reject `light`

Primary files:

- `src/axis/framework/metrics/types.py` (new)
- `src/axis/framework/metrics/standard.py` (new)
- `src/axis/framework/metrics/aggregate.py` (new)
- `src/axis/framework/metrics/compute.py` (new)

Delivers:

- first framework-standard metric families
- one stable run-level behavioral metrics model
- deterministic computation from replay-capable traces


### WP-02 -- Behavioral Metrics Artifact and Repository Support

Introduce a dedicated persisted artifact and repository accessors.

Scope:

- add `behavior_metrics.json` as a run-local artifact
- add path helpers and save/load methods in the repository
- ensure the artifact is clearly separate from `run_summary.json`
- keep current `RunSummary` behavior unchanged

Primary files:

- `src/axis/framework/persistence.py`

Delivers:

- explicit artifact path
- save/load support for behavioral metrics
- repository-level trace-mode guard behavior for metrics computation paths


### WP-03 -- Metrics Extension Infrastructure

Add the extension-capable subsystem that lets systems contribute their own
metrics.

Scope:

- add framework extension registry for metric extensions
- add SDK protocol for metric extensions
- add catalog bridge support:
  - `MetricExtensionCatalog`
  - `metric_extensions`
- implement dispatch that merges:
  - framework-standard metrics
  - extension metrics

Primary files:

- `src/axis/framework/metrics/extensions.py` (new)
- `src/axis/sdk/metrics.py` (new)
- `src/axis/framework/catalogs.py`

Delivers:

- reusable metric extension contract
- plugin-/catalog-friendly dispatch path
- namespaced system-specific metric result support


### WP-04 -- Standalone Run-Level Metrics Computation Path

Create the top-level orchestration for computing behavioral metrics from one
persisted run.

Scope:

- load all replay-capable episode traces for one run
- compute framework-standard metrics
- dispatch optional metric extension
- assemble and persist one `RunBehaviorMetrics` artifact
- keep this as an explicit post-run analysis path in v1

Primary files:

- `src/axis/framework/metrics/loader.py` (new)
- `src/axis/framework/metrics/compute.py`

Delivers:

- single-entry computation path for one run
- explicit post-run analysis workflow
- clean seam for CLI and later workspace consumers


### WP-05 -- First Consumer Surfaces in Framework CLI

Add first read-side integration for the new artifact.

Scope:

- extend `axis runs show` to render behavioral metrics if present
- optionally show behavioral metric availability in `axis runs list`
- avoid overloading `axis experiments show` until experiment-level semantics are
  settled
- keep errors and absence messaging clear

Primary files:

- `src/axis/framework/cli/commands/runs.py`
- possibly `src/axis/framework/cli/commands/experiments.py`

Delivers:

- usable first inspection surface
- clear user-facing distinction between run summary and behavioral metrics


### WP-06 -- System C Metrics Extension

Implement the first real system-specific metric extension using existing
prediction trace data.

Scope:

- add `src/axis/systems/system_c/metrics.py`
- register the extension from `system_c.register()`
- compute:
  - mean prediction error
  - signed prediction error
  - confidence trace mean
  - frustration trace mean
  - prediction modulation strength
- make the extension robust to missing or partially missing predictive fields

Primary files:

- `src/axis/systems/system_c/metrics.py` (new)
- `src/axis/systems/system_c/__init__.py`

Delivers:

- proof that the extension architecture works
- first concrete system-owned metric bundle
- system-specific metric namespacing convention


### WP-07 -- Workspace Integration and Optional Compute Trigger

Wire the subsystem into broader user workflows after the core shape is stable.

Scope:

- add workspace-aware resolution for behavioral metrics where useful
- decide whether there should be:
  - a dedicated CLI command
  - or integration into existing run/workspace inspection
- optionally add explicit compute-trigger commands if metrics are not auto-built
- keep workspace behavior aligned with replay-capable trace requirements

Primary files:

- `src/axis/framework/workspaces/`
- CLI parser / command modules as needed

Delivers:

- coherent workspace behavior
- clear operational path for generating and viewing metrics


### WP-08 -- Test, Parity, and Documentation Hardening

Complete the first wave with broad validation and docs.

Scope:

- unit tests for each framework-standard metric family
- run-level aggregation tests
- parity tests between:
  - `full`
  - `delta`
- extension registration and dispatch tests
- `system_c` extension tests
- update public and internal docs

Primary areas:

- `tests/framework/`
- `tests/systems/system_c/`
- `docs/manuals/`
- internal idea docs as needed

Delivers:

- trustworthy metric behavior
- replay-mode parity confidence
- documented extension model


## Recommended Sequence

1. `WP-01 Framework Metrics Core`
2. `WP-02 Behavioral Metrics Artifact and Repository Support`
3. `WP-03 Metrics Extension Infrastructure`
4. `WP-04 Standalone Run-Level Metrics Computation Path`
5. `WP-05 First Consumer Surfaces in Framework CLI`
6. `WP-06 System C Metrics Extension`
7. `WP-07 Workspace Integration and Optional Compute Trigger`
8. `WP-08 Test, Parity, and Documentation Hardening`

Notes:

- `WP-05` and `WP-06` can partially overlap after `WP-03`, but the CLI should
  not assume extension output semantics before `WP-06` proves the pattern.
- `WP-07` should wait until the run-level artifact shape and user trigger model
  are stable.
- `WP-08` should include regression coverage for both generic metrics and
  extension behavior.


## Milestones

### Milestone 1: Core Metrics Foundation

Complete when:

- framework-standard metrics compute from replay-capable traces
- one run-level behavioral metrics artifact exists
- repository persistence works

Maps to:

- `WP-01`
- `WP-02`
- `WP-04`

### Milestone 2: Extension Architecture Proven

Complete when:

- the framework can dispatch metric extensions by `system_type`
- catalog bridging works
- `system_c` contributes real extension metrics

Maps to:

- `WP-03`
- `WP-06`

### Milestone 3: User-Facing Integration

Complete when:

- users can inspect behavioral metrics from CLI
- workspace flows have a coherent story
- docs describe:
  - standard metrics
  - metric extensions
  - `full` / `delta` applicability

Maps to:

- `WP-05`
- `WP-07`
- `WP-08`


## Recommended First Engineering Slice

The most effective first engineering slice is:

1. add the framework metrics package
2. add `behavior_metrics.json`
3. compute standard metrics from persisted replay-capable traces
4. expose them in `axis runs show`

This slice already delivers user value while keeping the extension system and
`system_c` integration as the next focused layer rather than blocking the whole
subsystem.


## Main Risks and Mitigations

### Risk 1 -- Overloading existing summaries

Mitigation:

- keep `run_summary.json` unchanged
- use a separate artifact from the start

### Risk 2 -- Extension shape becomes ad hoc

Mitigation:

- mirror the comparison-extension architecture
- define an explicit SDK protocol early
- require namespaced extension output

### Risk 3 -- `delta` and `full` behave differently

Mitigation:

- compute from replay-capable `BaseEpisodeTrace`
- rely on repository reconstruction for `delta`
- add parity tests early

### Risk 4 -- User workflow becomes confusing

Mitigation:

- start with one clear CLI entry point
- delay broad workspace integration until the artifact shape settles


## Summary

The roadmap should build enhanced metrics as:

- a framework-owned analysis subsystem
- with a dedicated artifact
- and an extension model from the start

The right order is:

- standard metrics first
- persistence second
- extension infrastructure third
- `system_c` as proof case
- then CLI/workspace integration and hardening

That sequence keeps the architecture clean while delivering useful behavioral
analysis early.
