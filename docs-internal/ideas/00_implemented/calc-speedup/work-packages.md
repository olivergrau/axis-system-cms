# Calculation Speedup Work Packages

## Purpose

This document provides the first coarse implementation package breakdown for
the AXIS calculation-speedup initiative, based on:

- [Calculation Speedup Spec](./spec.md)
- [Calculation Speedup Engineering Spec](./engineering-spec.md)
- [Calculation Speedup Implementation Roadmap](./implementation-roadmap.md)

The packages below are intentionally implementation-oriented but still broad
enough to allow adjustment while the work is underway.


## Current Code Reality

The current codebase already contains useful prerequisites:

- clear experiment/run/episode layering
- deterministic seed derivation
- workspace-owned execution routing
- plugin discovery and registry-based system/world creation
- output-aware abstractions already present in other areas of the framework

However, the current execution architecture still has several hard constraints:

- no explicit execution-policy model
- no lightweight non-replay output contract
- runner always builds replay-rich traces
- runs execute episodes serially
- experiments execute runs serially
- persistence and logging assume replay-rich episode traces
- resume-oriented status logic still shapes experiment execution


## Delivery Strategy

The implementation should proceed in five layers:

1. **Policy and model foundation**
2. **Runner and run execution separation**
3. **Parallel execution**
4. **Persistence and integration hardening**
5. **Documentation and adoption**


## Work Packages

### WP-01: Execution Policy Model and Config Integration

Add explicit execution-policy fields and normalized internal policy types.

Scope:

- extend `ExecutionConfig` with:
  - `trace_mode`
  - `parallelism_mode`
  - `max_workers`
- add normalized framework-owned enums/models in a new internal module
- validate allowed values
- preserve defaults equivalent to today’s behavior

Primary files:

- `src/axis/framework/config.py`
- `src/axis/framework/execution_policy.py` (new)


### WP-02: Lightweight Result Types and Summary Generalization

Create the new lightweight execution result layer required for `light` mode.

Scope:

- add:
  - `LightEpisodeResult`
  - `LightRunResult`
- generalize summary computation to work from the minimal episode summary fields
- ensure run summary no longer depends exclusively on full replay traces

Primary files:

- `src/axis/framework/execution_results.py` (new)
- `src/axis/framework/run.py`


### WP-03: Collector-Based Runner Refactor

Refactor the runner so one simulation loop can produce either replay-rich or
lightweight outputs.

Scope:

- introduce output collectors
- keep current full-mode semantics intact
- add light-mode collection path
- avoid replay-format redesign

Primary files:

- `src/axis/framework/runner.py`


### WP-04: Mode-Aware Sequential Run Execution

Refactor `RunExecutor` so it can execute both `full` and `light` modes
sequentially before multiprocessing is introduced.

Scope:

- route by trace mode
- keep deterministic seed behavior unchanged
- adapt logging hooks to avoid assuming full step traces in all cases

Primary files:

- `src/axis/framework/run.py`
- `src/axis/framework/logging.py`


### WP-05: Episode-Parallel Worker Foundation

Introduce the worker-execution infrastructure for parallel episodes.

Scope:

- add explicit worker entry points
- make worker inputs serialization-safe
- initialize plugin discovery inside workers
- return deterministic episode-indexed results

Primary files:

- `src/axis/framework/parallel_execution.py` (new)
- `src/axis/plugins.py` if helper exposure is needed


### WP-06: Episode-Parallel Run Execution

Use the new worker foundation to execute episodes in parallel within a run.

Scope:

- add `parallelism_mode = episodes`
- support both:
  - `full`
  - `light`
- verify deterministic equivalence against sequential execution

Primary files:

- `src/axis/framework/run.py`
- `src/axis/framework/parallel_execution.py`


### WP-07: Run-Parallel Experiment Execution

Extend the experiment layer to support parallel execution across resolved runs.

Scope:

- add `parallelism_mode = runs`
- dispatch resolved `RunConfig` items independently
- keep canonical run ordering in aggregated outputs
- avoid nested run+episode parallelism in the first wave

Primary files:

- `src/axis/framework/experiment.py`
- `src/axis/framework/parallel_execution.py`


### WP-08: Mode-Aware Persistence and Status Simplification

Make persistence reflect the new execution modes and reduce resume-driven
complexity.

Scope:

- define persistence behavior for `light`
- avoid persisting replay-looking artifacts for non-replay outputs
- review whether `run_result.json` should still duplicate large payloads
- simplify or remove execution-core resume assumptions

Primary files:

- `src/axis/framework/persistence.py`
- `src/axis/framework/experiment.py`


### WP-09: Workspace and CLI Integration

Ensure the wider framework understands and preserves execution policy.

Scope:

- workspace execution passes through policy unchanged
- workspace/result inspection recognizes non-replay outputs
- CLI surfaces and error messages remain coherent

Primary files:

- `src/axis/framework/workspaces/execute.py`
- workspace inspection/resolution modules
- CLI command modules as needed


### WP-10: Test, Benchmark, and Documentation Hardening

Complete the first wave with regression coverage, representative benchmarking,
and documentation updates.

Scope:

- determinism tests across sequential/parallel and full/light
- persistence-shape tests
- worker-behavior tests compatible with spawn semantics
- representative benchmark scripts/tests
- update manuals and internal docs

Primary areas:

- `tests/framework/`
- `tests/framework/workspaces/`
- `docs/manuals/`
- internal idea documents as needed


## Recommended Sequence

1. `WP-01 Execution Policy Model and Config Integration`
2. `WP-02 Lightweight Result Types and Summary Generalization`
3. `WP-03 Collector-Based Runner Refactor`
4. `WP-04 Mode-Aware Sequential Run Execution`
5. `WP-05 Episode-Parallel Worker Foundation`
6. `WP-06 Episode-Parallel Run Execution`
7. `WP-07 Run-Parallel Experiment Execution`
8. `WP-08 Mode-Aware Persistence and Status Simplification`
9. `WP-09 Workspace and CLI Integration`
10. `WP-10 Test, Benchmark, and Documentation Hardening`

Notes:

- `WP-05` and `WP-06` are split intentionally so worker infrastructure can land
  and stabilize before full run-path integration.
- `WP-08` should follow the first usable parallel paths, because persistence
  design is easier to finalize once real `light` execution exists.
- `WP-09` should not start too early, because workspace and CLI integration
  depends on settled artifact semantics.


## Milestones

### Milestone 1: Policy and Dual Output Foundations

Complete when:

- execution policy is explicit in config
- lightweight episode/run results exist
- summaries work for both full and light outputs

### Milestone 2: Dual-Mode Sequential Execution

Complete when:

- sequential `full` execution remains stable
- sequential `light` execution is functional
- runner output collection is mode-aware

### Milestone 3: Episode Multicore Execution

Complete when:

- episode-parallel execution is operational
- deterministic equivalence with sequential execution is verified

### Milestone 4: Sweep Multicore Execution

Complete when:

- run-parallel experiment execution is operational
- summaries and ordering remain correct

### Milestone 5: Operational Cohesion

Complete when:

- persistence is mode-aware
- workspace and CLI behavior are coherent
- tests and docs cover the new execution model
