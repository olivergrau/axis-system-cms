# AXIS Execution and Memory Engineering Specification

## 1. Purpose

This engineering specification derives the implementation shape of the
execution-memory optimization initiative from:

- [Delta-Opt Trace Specification](./spec.md)

This document covers the execution-side initiative only.

Its purpose is to define how AXIS should reduce:

- parent-process memory growth
- worker-process memory pressure
- inter-process payload transfer
- whole-run replay retention

while remaining compatible with multiple trace storage modes:

- `full`
- `light`
- `delta`
- `delta-opt`

This document does not define the compact replay storage contract itself. That
belongs to the trace initiative.


## 2. Initiative Boundary

This initiative is about:

- run execution architecture
- per-episode persistence timing
- worker / parent responsibility split
- run summary aggregation shape
- memory behavior under parallel execution

This initiative is not about:

- the exact fields persisted in `delta-opt`
- the replay reconstruction contract
- world determinism classes
- trace payload minimization details

Those belong to the trace and replay engineering initiative.


## 3. Current System Reality

The execution-memory optimization must start from the actual current code.

### 3.1 Run execution retains whole episode results

Current run execution lives in:

- [src/axis/framework/run.py](/workspaces/axis-system-cms/src/axis/framework/run.py)

Current behavior:

- execute all episodes
- collect them into `episode_results`
- compute summary from the full in-memory collection
- only then return a `RunResult`, `LightRunResult`, or `DeltaRunResult`

This means replay-capable episode payloads remain in memory for the duration of
the run.

### 3.2 Parallel episode execution returns large objects to the parent

Parallel helpers live in:

- [src/axis/framework/parallel_execution.py](/workspaces/axis-system-cms/src/axis/framework/parallel_execution.py)

Current behavior:

- worker executes one episode
- worker returns the full result object to the parent
- parent accumulates all returned episode objects

This amplifies memory pressure in two places:

- workers each materialize large episode results
- parent becomes a collector of all large episode results

### 3.3 Persistence happens after result accumulation

Run persistence is orchestrated in:

- [src/axis/framework/experiment.py](/workspaces/axis-system-cms/src/axis/framework/experiment.py)

Current behavior in `_persist_completed_run(...)`:

- save the run-level result
- save the run summary
- then iterate over all episodes and save them individually

This means persistence currently happens after the full run result already
exists as an in-memory object.

### 3.4 Run summaries depend on whole episode objects

Run summary computation currently lives in:

- [src/axis/framework/run.py](/workspaces/axis-system-cms/src/axis/framework/run.py)

`compute_run_summary(...)` currently consumes:

- `total_steps`
- `final_vitality`
- episode count
- death condition via `final_vitality <= 0.0`

This means the required summary inputs are compact, but the current pipeline
still carries whole episode payloads just to derive them.

### 3.5 Run result duplication worsens memory pressure

Persistence currently stores:

- per-episode artifacts
- plus a `run_result.json` embedding the run payload

This is primarily a persistence problem, but it also reinforces the current
execution shape because the system still thinks in terms of “whole run object
containing all episodes”.


## 4. Engineering Goals

The execution-memory initiative should achieve the following:

1. eliminate whole-run replay retention as the default execution shape
2. allow replay-capable runs to persist episode artifacts incrementally
3. reduce worker-to-parent payload size
4. make run summaries aggregatable from compact episode summaries
5. keep compatibility with all current trace modes where possible
6. support safe multi-worker execution for larger experiments


## 5. Target Architectural Direction

The target direction is:

- episode execution produces:
  - persisted artifact
  - compact episode summary contribution
- parent aggregates compact episode summaries
- run-level persistence stores compact run metadata and summary
- trace-mode-specific heavy payload handling is pushed to the persistence path,
  not retained in the run aggregator

Conceptually:

```text
worker episode execution
-> episode artifact persisted
-> compact episode completion payload returned
-> parent incremental run aggregation
-> compact run artifact persisted
```


## 6. Required Refactoring Direction

### 6.1 Separate execution result from persisted replay payload

Current code conflates:

- “what must be persisted for replay”
- “what must be retained in memory for run orchestration”

This must be separated.

Recommended direction:

- keep replay-capable episode artifact construction
- introduce a compact in-memory episode completion type for run aggregation

This completion type should contain only:

- `episode_index`
- `episode_seed`
- `total_steps`
- `final_vitality`
- `termination_reason`
- `final_position`
- possibly the persisted artifact path or run-local artifact identity

### 6.2 Introduce streaming run aggregation

Current `compute_run_summary(...)` already depends only on compact episode-level
scalars.

Recommended direction:

- introduce an incremental run aggregation helper
- update it after each completed episode
- finalize it into the existing `RunSummary` model at run completion

This should remove the need to keep whole replay payloads only for summary
computation.

### 6.3 Introduce persistence-aware episode completion flow

Recommended run lifecycle:

1. execute episode
2. build trace artifact according to trace mode
3. persist episode artifact immediately
4. derive compact episode completion record
5. release large replay payload
6. update run aggregator

This is the central architectural move for memory reduction.

### 6.4 Move toward worker-side persistence for replay-heavy modes

For parallel replay-capable execution, the preferred direction is:

- worker executes episode
- worker persists episode artifact
- worker returns compact completion payload

This avoids returning large replay structures through `ProcessPoolExecutor`.

This direction will likely require careful repository access design, but it is
the best fit with the scaling problem observed.

### 6.5 Keep parent process aggregation compact

The parent should aggregate:

- compact episode completions
- run summary state
- progress state

The parent should not accumulate:

- full `BaseEpisodeTrace`s
- full `DeltaEpisodeTrace`s
- full replay payloads from all workers


## 7. Concrete Current Hotspots

### 7.1 `RunExecutor.execute(...)`

File:

- [src/axis/framework/run.py](/workspaces/axis-system-cms/src/axis/framework/run.py)

Current issue:

- `episode_results` is a full tuple of all episodes
- replay-capable runs retain all episode results until end of run

Required direction:

- split run aggregation from replay payload retention

### 7.2 `_execute_parallel_episodes(...)`

File:

- [src/axis/framework/run.py](/workspaces/axis-system-cms/src/axis/framework/run.py)

Current issue:

- parallel path still returns full episode objects to the parent

Required direction:

- parent should receive compact episode completion records

### 7.3 `execute_episodes_parallel(...)`

File:

- [src/axis/framework/parallel_execution.py](/workspaces/axis-system-cms/src/axis/framework/parallel_execution.py)

Current issue:

- worker result payload is the full episode result object

Required direction:

- support a worker-side persistence path plus compact completion return

### 7.4 `_persist_completed_run(...)`

File:

- [src/axis/framework/experiment.py](/workspaces/axis-system-cms/src/axis/framework/experiment.py)

Current issue:

- persistence assumes a whole run result containing all episodes is already
  present

Required direction:

- run persistence should finalize compact run artifacts after episode-level
  persistence has already happened


## 8. Compatibility With Existing Trace Modes

This initiative should not require `delta-opt` in order to be useful.

Where possible, the new execution-memory architecture should also improve:

- `full`
- `delta`
- `light`

Expected mode-specific outcomes:

- `light` should benefit most easily because its episode payloads are already
  compact
- `delta` should benefit substantially from streaming and worker-side
  persistence
- `full` may still remain expensive, but should benefit from not retaining all
  episode traces at once
- `delta-opt` should be designed to fit this execution model natively


## 9. Parent / Worker Responsibility Split

### 9.1 Worker responsibilities

The worker should eventually be responsible for:

- episode simulation
- trace materialization for the configured mode
- immediate episode persistence
- compact completion extraction

### 9.2 Parent responsibilities

The parent should eventually be responsible for:

- dispatching episode work
- receiving compact completions
- incremental aggregation
- run summary finalization
- final compact run artifact persistence

### 9.3 Non-goal

The parent should not remain the universal owner of all replay-capable episode
payloads in memory.


## 10. Suggested Implementation Waves

### Wave 1: Compact run result contract

Primary changes:

- stop embedding full episode payloads in run-level result persistence
- introduce smaller run-level persistence contract

Benefit:

- immediate reduction in duplicate storage
- simpler later streaming design

### Wave 2: Incremental aggregation in parent

Primary changes:

- introduce compact episode completion model
- replace whole-run summary derivation from large episode objects

Benefit:

- reduced parent memory growth

### Wave 3: Worker-side persistence for replay-heavy paths

Primary changes:

- move episode persistence into worker lifecycle
- return compact completion payloads only

Benefit:

- reduced IPC volume
- reduced parent memory pressure

### Wave 4: Parallelism guardrails

Primary changes:

- trace-mode-aware worker policies
- memory-safe parallel defaults

Benefit:

- safer large experiments


## 11. Validation Requirements

The execution-memory initiative should be considered successful only if it
demonstrates:

- lower parent peak memory under replay-capable runs
- lower worker-to-parent transfer volume
- no loss of persisted replay correctness
- stable run summary correctness
- compatibility with multi-worker execution

Validation should include:

- `200`-step and `400`-step runs
- replay-capable modes
- at least one dense regeneration world
- at least one sparse world


## 12. Open Questions

- Should worker-side persistence be mandatory for replay-heavy modes or only
  preferred?
- Should compact episode completion records include artifact paths explicitly?
- How should resume semantics interact with incremental persistence later?
- How much of the new execution model can be shared with `full` mode before
  mode-specific exceptions become necessary?


## 13. Summary

This initiative is a separate architectural track from trace format redesign.

Its job is to make AXIS execution scale better by:

- streaming persistence earlier
- retaining less in memory
- aggregating compact summaries
- reducing worker-to-parent payload size

This should benefit all trace modes where possible and provide the execution
foundation on which `delta-opt` can later operate efficiently.
