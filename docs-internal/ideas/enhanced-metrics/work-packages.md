# Enhanced Metrics Work Packages

## Purpose

This document provides the first coarse implementation package breakdown for
the AXIS enhanced-metrics initiative, based on:

- [Enhanced Metrics Spec](./spec.md)
- [Enhanced Metrics Engineering Spec](./engineering-spec.md)
- [Enhanced Metrics Implementation Roadmap](./implementation-roadmap.md)

The packages below are intentionally implementation-oriented but still broad
enough to allow refinement while the subsystem is taking shape.


## Current Code Reality

The current codebase already provides several strong prerequisites:

- replay-capable trace contracts
- delta reconstruction into `BaseEpisodeTrace`
- a repository abstraction for persisted run artifacts
- a comparison-extension architecture worth mirroring
- plugin/catalog bridging for extension dispatch

At the same time, the current system still lacks the concrete pieces this idea
needs:

- no dedicated metrics subsystem under the framework
- no behavioral metrics artifact
- no metric extension registry
- no SDK contract for metric extensions
- no run-level CLI surface for behavioral metrics

This makes the project straightforward in direction, but still real framework
work rather than just a few extra summary fields.


## Delivery Strategy

The implementation should proceed in five layers:

1. **Metric core and data model**
2. **Persistence and compute orchestration**
3. **Extension architecture**
4. **First real extension and user surfaces**
5. **Hardening and documentation**


## Work Packages

### WP-01: Behavioral Metric Types and Standard Models

Create the framework-owned type layer for behavioral metrics.

Scope:

- add a dedicated framework metrics package
- define:
  - episode-level internal metric models
  - run-level aggregate metric models
  - top-level persisted artifact model
- separate:
  - standard metrics
  - system-specific extension metrics

Primary files:

- `src/axis/framework/metrics/types.py` (new)
- `src/axis/framework/metrics/__init__.py` (new)


### WP-02: Standard Metric Computation

Implement the first-wave standard metric families from replay-capable traces.

Scope:

- compute:
  - survival baseline metrics
  - resource efficiency metrics
  - behavioral structure metrics
  - failed movement rate
  - exploration metrics
- compute episode-level metrics and aggregate to run level
- reject `light`
- support both:
  - `full`
  - `delta` via reconstructed traces

Primary files:

- `src/axis/framework/metrics/standard.py` (new)
- `src/axis/framework/metrics/aggregate.py` (new)


### WP-03: Repository Artifact Support

Add repository support for behavioral metrics persistence.

Scope:

- add `behavior_metrics.json` path resolution
- add save/load helpers
- keep `run_summary.json` untouched
- ensure artifact naming and location are stable

Primary files:

- `src/axis/framework/persistence.py`


### WP-04: Run-Level Metrics Orchestration

Create the framework entry point that computes behavioral metrics for one run.

Scope:

- load replay-capable traces for a run
- compute standard metrics
- dispatch optional system-specific extension
- assemble and persist final artifact
- make this usable as an explicit post-run analysis step

Primary files:

- `src/axis/framework/metrics/compute.py` (new)
- `src/axis/framework/metrics/loader.py` (new)


### WP-05: Metric Extension SDK and Registry

Introduce the reusable extension mechanism for systems.

Scope:

- add SDK protocol for metric extensions
- add framework registry helpers:
  - register
  - list registered extensions
  - dispatch extension
- enforce namespaced extension outputs
- make extension absence graceful

Primary files:

- `src/axis/sdk/metrics.py` (new)
- `src/axis/framework/metrics/extensions.py` (new)


### WP-06: Catalog and Plugin Bridge Integration

Make metric extensions compatible with the current AXIS catalog / plugin model.

Scope:

- add `MetricExtensionCatalog`
- include it in `build_catalogs_from_registries()`
- make framework orchestration optionally use injected catalogs
- keep parity with existing comparison-extension behavior

Primary files:

- `src/axis/framework/catalogs.py`


### WP-07: `system_c` Metric Extension

Implement the first concrete system-specific metric bundle.

Scope:

- add `src/axis/systems/system_c/metrics.py`
- register from `system_c.register()`
- compute:
  - mean prediction error
  - signed prediction error
  - confidence trace mean
  - frustration trace mean
  - prediction modulation strength
- tolerate incomplete predictive trace payloads gracefully

Primary files:

- `src/axis/systems/system_c/metrics.py` (new)
- `src/axis/systems/system_c/__init__.py`


### WP-08: CLI Inspection Surface

Expose behavioral metrics in the first user-facing command path.

Scope:

- extend `axis runs show`
- optionally annotate `axis runs list`
- keep experiment-level views conservative until experiment-wide semantics are
  intentionally designed
- ensure clear messaging when metrics are unavailable

Primary files:

- `src/axis/framework/cli/commands/runs.py`
- optionally `src/axis/framework/cli/commands/experiments.py`


### WP-09: Workspace Integration

Integrate behavioral metrics into workspace-oriented inspection flows once the
artifact and CLI behavior are stable.

Scope:

- add workspace-aware resolution where helpful
- decide whether metrics should be shown:
  - inline with run-summary views
  - or via a dedicated metrics-oriented command path
- keep replay-capable trace requirements explicit in messaging

Primary files:

- `src/axis/framework/workspaces/`
- parser / CLI command modules as needed


### WP-10: Validation, Docs, and Rollout Hardening

Finish the subsystem with tests and docs.

Scope:

- unit tests for each standard metric family
- run-level aggregation tests
- `full` vs `delta` parity tests
- extension registry / dispatch tests
- `system_c` metric extension tests
- user docs for:
  - standard metrics
  - extension model
  - replay-capable trace requirements

Primary areas:

- `tests/framework/`
- `tests/systems/system_c/`
- `docs/manuals/`
- `docs/tutorials/` if needed


## Recommended Sequence

1. `WP-01 Behavioral Metric Types and Standard Models`
2. `WP-02 Standard Metric Computation`
3. `WP-03 Repository Artifact Support`
4. `WP-04 Run-Level Metrics Orchestration`
5. `WP-05 Metric Extension SDK and Registry`
6. `WP-06 Catalog and Plugin Bridge Integration`
7. `WP-07 system_c Metric Extension`
8. `WP-08 CLI Inspection Surface`
9. `WP-09 Workspace Integration`
10. `WP-10 Validation, Docs, and Rollout Hardening`

Notes:

- `WP-05` and `WP-06` are intentionally separated so the extension contract can
  settle before wider catalog plumbing depends on it.
- `WP-07` should not be attempted before `WP-05`, otherwise the first extension
  will define the architecture by accident.
- `WP-09` should trail CLI integration, because workspaces are easier to wire
  once run-level behavior is already stable.


## Milestones

### Milestone 1: Standard Behavioral Metrics Exist

Complete when:

- framework-standard metrics compute correctly from replay-capable traces
- one persisted run-level artifact exists
- users can inspect that artifact programmatically

Maps to:

- `WP-01`
- `WP-02`
- `WP-03`
- `WP-04`

### Milestone 2: Extension System Proven

Complete when:

- metric extensions can register and dispatch by `system_type`
- catalog integration works
- `system_c` contributes real extension metrics

Maps to:

- `WP-05`
- `WP-06`
- `WP-07`

### Milestone 3: End-to-End User Flow

Complete when:

- CLI shows behavioral metrics
- workspace flows have a coherent story
- tests cover both standard and extension metrics
- docs explain how systems can add their own metrics

Maps to:

- `WP-08`
- `WP-09`
- `WP-10`


## Recommended First Slice

The best first implementation slice is:

1. metric types
2. standard computation
3. repository artifact
4. run-level orchestration

This slice gives AXIS a useful standard behavioral metrics subsystem before any
extension logic is required.

Then the second slice should be:

1. extension SDK + registry
2. catalog bridge
3. `system_c` extension

This proves the extension architecture without blocking the value of the
framework-standard metrics.


## Main Risks

### Risk 1: Framework core and extensions blur together

Mitigation:

- explicitly separate standard metrics from extension metrics in the data model
- require namespaced extension output
- keep system-specific logic out of the framework metric core

### Risk 2: The first extension silently defines bad framework contracts

Mitigation:

- define the SDK protocol and registry before implementing `system_c`
- validate the extension path with explicit tests

### Risk 3: Replay mode differences leak into metrics

Mitigation:

- compute from `BaseEpisodeTrace`
- let the repository reconstruct `delta`
- add parity tests early

### Risk 4: User experience becomes confusing

Mitigation:

- start with one simple run-level CLI surface
- document clearly that metrics require replay-capable traces
- defer broader workspace exposure until the artifact shape stabilizes


## Summary

The work packages should build enhanced metrics as:

- a framework-owned standard metrics subsystem
- a separate persisted artifact
- and an extension architecture that systems can plug into

The clean sequence is:

- standard core first
- extension model second
- `system_c` as first concrete extension
- then CLI/workspace integration and hardening

That gives AXIS a strong behavioral-analysis foundation without collapsing
generic and system-specific concerns into one undifferentiated summary model.
