# Calculation Speedup -- Implementation Roadmap

**Based on:** `spec.md`, `engineering-spec.md`  
**Date:** 2026-04-24

---

## Overview

The implementation should follow a low-risk layered order:

1. establish explicit execution-policy concepts
2. separate replay-rich from lightweight execution outputs
3. refactor the runner around output collection without changing simulation
4. add deterministic episode-level parallel execution
5. add deterministic run-level parallel execution for sweeps
6. make persistence, logging, and workspace integration mode-aware

This order is important.

The current codebase tightly couples:

- simulation
- replay trace construction
- summary computation
- persistence
- logging

So the first implementation wave should not begin with multiprocessing itself.

It should first create the internal shapes that make multiprocessing safe and
trace-mode-aware.


## Delivery Strategy

The roadmap should proceed in six layers:

1. **Execution policy foundation**
   Make speed-related choices explicit and validated.
2. **Light-output semantic layer**
   Introduce non-replay execution results without touching replay contracts.
3. **Runner and run-executor refactor**
   Make the execution path collector-driven and mode-aware.
4. **Episode-parallel execution**
   Add the most valuable multicore path first.
5. **Run-parallel sweep execution**
   Extend parallelism to experiment-level sweep workloads.
6. **Integration and hardening**
   Make persistence, logging, workspace behavior, and docs consistent.


## Dependency Graph

```text
WP-01
  |
WP-02
  |
WP-03
  |
WP-04
  |
WP-05
 /   \
WP-06 WP-07
   \   /
   WP-08
     |
   WP-09
```

Interpretation:

- `WP-01` and `WP-02` establish concepts and lightweight result types
- `WP-03` makes the runner mode-aware
- `WP-04` adapts run execution to the new execution model
- `WP-05` adds episode-parallel execution
- `WP-06` and `WP-07` can proceed after the core parallel path lands
- `WP-08` hardens the wider system
- `WP-09` updates manuals and internal docs


## Work Packages

### WP-01 -- Execution Policy Foundation

Introduce explicit framework-owned execution policy concepts and wire them into
the current config model.

Scope:

- add `trace_mode`, `parallelism_mode`, and `max_workers` to
  `ExecutionConfig`
- add normalized internal execution-policy types and validation
- preserve current defaults:
  - `trace_mode = full`
  - `parallelism_mode = sequential`
  - `max_workers = 1`
- ensure old configs remain valid through defaults

Primary files:

- `src/axis/framework/config.py`
- `src/axis/framework/execution_policy.py` (new)

Delivers:

- config-level policy fields
- normalized internal policy model
- validation tests


### WP-02 -- Lightweight Execution Result Models

Introduce the internal result types required for `light` execution without yet
changing the runner.

Scope:

- add `LightEpisodeResult`
- add `LightRunResult`
- generalize summary computation so it can operate on both:
  - full episode traces
  - lightweight episode results
- define the minimal summary-bearing field set

Primary files:

- `src/axis/framework/execution_results.py` (new)
- `src/axis/framework/run.py`

Delivers:

- lightweight result models
- summary computation that no longer depends exclusively on `BaseEpisodeTrace`


### WP-03 -- Collector-Based Runner Refactor

Refactor the step runner so simulation remains shared while output collection
becomes mode-aware.

Scope:

- introduce collector strategy in or near `runner.py`
- add:
  - `FullTraceCollector`
  - `LightTraceCollector`
- preserve the existing full replay semantics in `full` mode
- implement `light` mode episode result production
- avoid replay-trace redesign

Primary files:

- `src/axis/framework/runner.py`

Delivers:

- one shared simulation loop
- collector-based output construction
- support for both full and light episode outputs


### WP-04 -- Run Executor Refactor for Mode-Aware Execution

Refactor `RunExecutor` so it becomes execution-policy-aware and no longer
assumes serial replay-rich execution only.

Scope:

- route execution by:
  - `trace_mode`
  - `parallelism_mode`
- keep sequential execution working for both modes
- move toward per-execution-unit system construction rather than parent-owned
  long-lived instances when needed
- adapt logging and summary integration for the new result forms

Primary files:

- `src/axis/framework/run.py`
- `src/axis/framework/logging.py`

Delivers:

- sequential `full` execution path
- sequential `light` execution path
- mode-aware logging hooks


### WP-05 -- Deterministic Episode-Parallel Execution

Add multiprocessing-based parallel execution across episodes within a run.

Scope:

- introduce worker entry points
- ensure explicit plugin discovery and registry initialization in workers
- serialize worker input safely across platforms
- reassemble episode results deterministically by episode index
- support both:
  - episode-parallel full mode
  - episode-parallel light mode

Primary files:

- `src/axis/framework/parallel_execution.py` (new)
- `src/axis/framework/run.py`
- `src/axis/plugins.py` if minor worker-safe helpers are needed

Delivers:

- deterministic episode-level multicore execution
- worker-safe setup path
- tests proving result invariance vs sequential execution


### WP-06 -- Deterministic Run-Parallel Sweep Execution

Extend the framework to execute runs in parallel for sweep-like experiments.

Scope:

- use `parallelism_mode = runs` in `ExperimentExecutor`
- dispatch resolved runs independently
- preserve canonical run ordering
- make experiment finalization agnostic to whether run results are full or
  light
- do not reintroduce nested parallelism in the first wave

Primary files:

- `src/axis/framework/experiment.py`
- `src/axis/framework/parallel_execution.py`

Delivers:

- deterministic multicore execution for OFAT/sweep-style experiments


### WP-07 -- Mode-Aware Persistence and Status Simplification

Make persistence explicitly trace-mode-aware and reduce execution complexity
related to resume semantics.

Scope:

- review `RunResult` persistence strategy
- introduce a clean persistence policy for `light` outputs
- avoid persisting replay-looking artifacts in `light` mode
- simplify or remove resume-driven status assumptions from the execution core
- keep repository layout stable in the first wave

Primary files:

- `src/axis/framework/persistence.py`
- `src/axis/framework/experiment.py`

Delivers:

- light-mode artifact persistence
- reduced duplication where feasible
- simplified status model aligned with no-resume-first execution


### WP-08 -- Workspace, CLI, and Test Hardening

Harden the wider system around execution-policy-aware behavior.

Scope:

- ensure workspace execution passes through execution policy unchanged
- make workspace/result inspection aware that some artifacts may be non-replay
- update CLI surfaces and error messages as needed
- add determinism tests, persistence tests, and representative benchmark tests

Primary files:

- `src/axis/framework/workspaces/execute.py`
- related workspace resolution/inspection modules
- CLI command modules as needed
- tests under:
  - `tests/framework/`
  - `tests/framework/workspaces/`

Delivers:

- system-wide operational consistency
- regression coverage for speedup semantics


### WP-09 -- Documentation and Internal Alignment

Update public and internal documentation to describe the new execution modes
and throughput-oriented workflow choices.

Scope:

- document execution policy fields
- document `full` vs `light`
- document sequential vs episode/run parallelism
- document non-replay implications of `light`
- update any manuals or tutorials that imply replay-rich execution is the only
  mode

Primary files:

- `docs/manuals/axis-overview.md`
- `docs/manuals/cli-manual.md`
- `docs/manuals/workspace-manual.md`
- internal idea documents as needed

Delivers:

- documentation alignment
- clearer expectations for users and future contributors


## Suggested Execution Order

### Phase 1 -- Foundations

- `WP-01 Execution Policy Foundation`
- `WP-02 Lightweight Execution Result Models`

Goal:

- make execution policy explicit
- make summaries independent from replay traces

### Phase 2 -- Core Refactor

- `WP-03 Collector-Based Runner Refactor`
- `WP-04 Run Executor Refactor for Mode-Aware Execution`

Goal:

- create one shared simulation core with two output lanes

### Phase 3 -- Main Speedup

- `WP-05 Deterministic Episode-Parallel Execution`

Goal:

- land the most valuable multicore path first

### Phase 4 -- Sweep Speedup

- `WP-06 Deterministic Run-Parallel Sweep Execution`

Goal:

- make sweep-heavy workloads materially faster

### Phase 5 -- Integration Cleanup

- `WP-07 Mode-Aware Persistence and Status Simplification`
- `WP-08 Workspace, CLI, and Test Hardening`

Goal:

- make the system coherent end-to-end

### Phase 6 -- Documentation

- `WP-09 Documentation and Internal Alignment`

Goal:

- document the new operational model clearly


## Milestone Gates

### Milestone 1 -- Policy and Output Separation

Complete when:

- execution policy is explicit in config
- lightweight episode/run results exist
- summary computation no longer requires only full traces

### Milestone 2 -- Dual-Mode Execution

Complete when:

- sequential `full` still works
- sequential `light` works
- the runner is collector-driven rather than replay-hardcoded

### Milestone 3 -- Episode Multicore

Complete when:

- episode-parallel execution is deterministic
- results match sequential execution for identical seeds
- worker setup is safe across spawn-style platforms

### Milestone 4 -- Sweep Multicore

Complete when:

- run-parallel sweep execution works deterministically
- experiment summaries remain stable and correctly ordered

### Milestone 5 -- Operational Stability

Complete when:

- persistence is mode-aware
- workspace behavior is coherent with non-replay outputs
- tests cover the core execution-policy matrix

### Milestone 6 -- Ready for Adoption

Complete when:

- manuals describe the new execution model
- users can intentionally choose between replay richness and speed


## Risk Notes

### Highest-risk package

`WP-03` is the most structurally sensitive package because it touches the
runner contract directly.

However, it is still lower risk than a replay-format redesign because it keeps
the full-mode collector aligned with current trace semantics.

### Highest-value package

`WP-05` is expected to yield the best near-term performance gain because it
unlocks multicore execution for the most common case: many episodes in one run.

### Most likely cleanup package

`WP-07` may expose additional simplifications once `light` mode and
no-resume-first execution are real, especially around status handling and
persisted run-result shape.


## Recommended Delivery Mindset

The implementation should not try to maximize optimization cleverness in the
first wave.

It should instead maximize:

- explicitness
- determinism
- testability
- clean mode separation

If the first wave lands well, AXIS will already gain:

- a usable fast path
- scalable multicore execution
- a clearer execution architecture

without yet committing to deeper replay-trace redesign.
