# AXIS Calculation Speedup Draft

## Purpose

This draft explores how AXIS experiment execution could be made
significantly faster without giving up the framework's current strengths:

- deterministic seeded execution
- explicit persisted artifacts
- replayable episode traces
- system/world modularity
- workspace compatibility

The central goal is:

> reduce wall-clock execution time for experiments, especially multi-episode
> runs and OFAT-style sweeps

This is not yet a specification.

It is a draft-level design document intended to identify:

- where the current runtime likely spends time
- which speedup directions are plausible
- which improvements are low-risk versus architecture-affecting
- which changes should be prioritized first


## Starting Point

AXIS currently executes experiments through a layered path:

- `ExperimentExecutor` resolves runs and executes them in sequence
- `RunExecutor` executes episodes in sequence within each run
- `run_episode()` executes one step loop at a time
- traces and summaries are persisted as JSON artifacts

The relevant current code paths include:

- `src/axis/framework/experiment.py`
- `src/axis/framework/run.py`
- `src/axis/framework/runner.py`
- `src/axis/framework/persistence.py`
- `src/axis/world/grid_2d/model.py`

The current architecture is optimized primarily for:

- correctness
- clarity
- replayability
- extensibility

It is not yet optimized primarily for throughput.


## Core Observation

The current execution model appears to pay a high per-step and per-episode cost
for artifact richness.

This is not accidental.

AXIS intentionally captures enough state to support:

- replay visualization
- comparison
- trace inspection
- post-hoc debugging

However, this likely means the current runtime is spending substantial time on:

- object creation
- snapshot generation
- serialization preparation
- repeated full-grid traversal
- single-core sequential execution

So the basic problem is not one isolated slow algorithm.

It is more likely a stack of individually reasonable costs that multiply across:

- steps
- episodes
- runs
- sweeps


## Current Performance Weaknesses

### 1. Full world snapshots are captured multiple times per step

In `src/axis/framework/runner.py`, each step currently captures:

- `world_before`
- `world_after_regen`
- `world_after`

For `grid_2d`, `snapshot()` in `src/axis/world/grid_2d/model.py` rebuilds the
entire grid as immutable `CellView` tuples every time.

That means one step performs repeated full-grid traversal and repeated
allocation of snapshot objects even if only a small part of the world changed.

This is likely one of the largest runtime costs in the current architecture.


### 2. The hot path creates many Pydantic trace objects

The step loop constructs a `BaseStepTrace` on every timestep and later a
`BaseEpisodeTrace` per episode.

Likewise, world cells and many intermediate objects are represented as frozen
Pydantic models.

This is good for validation and artifact integrity, but it is expensive in the
innermost execution loop.


### 3. Run execution is fully sequential

`RunExecutor.execute()` currently executes all episodes one after another.

`ExperimentExecutor` also executes runs one after another.

This leaves multicore CPU capacity unused for:

- repeated independent episodes in a run
- repeated independent runs in an OFAT sweep
- workspace-driven multi-run execution

These are naturally parallelizable units because seeded episodes and resolved
run configs are already independent.


### 4. Persistence is artifact-rich and JSON-heavy

AXIS persists:

- experiment configs
- run configs
- summaries
- run results
- per-episode traces

The current persistence layer uses JSON conversion from full Pydantic models.

This is desirable for transparency, but it adds measurable cost through:

- recursive model dumping
- stringification
- filesystem writes
- duplicate storage of some information at multiple artifact levels


### 5. Run results duplicate large in-memory structures

`RunResult` includes full `episode_traces`, and persisted `run_result.json`
therefore risks duplicating information that is already also written into the
individual `episode_XXXX.json` files.

Even if this is convenient for inspection, it increases:

- serialization cost
- memory pressure
- disk write time


### 6. Execution and tracing are not yet separable modes

The current runtime appears to assume a replay-rich execution mode by default.

That means there is not yet a clean distinction between:

- maximum observability mode
- faster execution mode

This limits the framework's ability to trade artifact richness for speed in
cases such as:

- large sweeps
- exploratory tuning
- CI smoke benchmarking
- rapid local iteration


## Main Speedup Directions

The speedup opportunity likely comes from combining several layers of
improvement rather than betting on one mechanism alone.

### 1. Parallelize across episodes

This is the cleanest first parallelization target.

Episodes within one run are naturally independent if:

- the seed is fixed per episode
- each episode constructs its own world
- each episode initializes its own agent state

So a run can conceptually become:

```text
RunConfig
-> resolve episode seeds
-> execute episodes in a worker pool
-> collect traces in episode order
-> compute summary
```

This would likely yield the most obvious multicore speedup on machines with 4
to 16 cores.

Benefits:

- conceptually simple
- preserves current experiment semantics
- keeps determinism manageable
- works for both single runs and sweep runs

Main caution:

- results must still be reassembled in deterministic episode order
- logging and persistence must not interleave unsafely


### 2. Parallelize across runs

OFAT experiments are another strong candidate.

Each resolved `RunConfig` is independent once config resolution is complete.

So an experiment can conceptually execute multiple runs in parallel,
especially when:

- each run contains many episodes
- the experiment contains many parameter values

Benefits:

- large gains for sweeps
- naturally aligned with current run isolation

Main caution:

- experiment-level progress tracking and status updates become more complex
- repository writes must remain isolated per run


### 3. Introduce execution modes with trace richness control

The framework should likely distinguish at least three execution profiles:

- `full_trace`
  current replay-rich behavior
- `analysis_trace`
  enough for comparison and summaries, but less than full replay
- `fast_summary`
  no full per-step replay artifacts unless explicitly requested

This is important because many speed problems likely come from always paying
for maximum trace richness.

Potential reductions in reduced-trace modes:

- omit intermediate snapshots when not needed
- omit per-step `world_data` if empty
- omit repeated full-grid snapshots
- persist only aggregate outputs unless replay is requested


### 4. Replace full snapshots with delta-oriented trace options

The current world snapshot strategy is replay-friendly but expensive.

A more performant alternative is to support a lighter trace format that stores:

- initial full state
- per-step deltas
- periodic checkpoints if needed

Conceptually:

```text
initial snapshot
+ step deltas
+ optional checkpoint snapshots
-> replay reconstruction
```

This could reduce:

- per-step allocation
- trace size
- serialization cost

However, this is also a deeper architectural change and should not be the
first optimization step.


### 5. Reduce duplication in persisted artifacts

If per-episode traces are already persisted separately, then `run_result.json`
may not need to embed full episode payloads.

A leaner run result could persist:

- run metadata
- seeds
- summary
- references to episode files

This would reduce large redundant writes and improve scalability for long runs.


### 6. Add a profiling-first optimization pass

Before changing architecture too aggressively, AXIS should gain lightweight
benchmarking and profiling tooling for representative workloads.

Useful benchmark slices:

- one short baseline run
- one long single-system run
- one OFAT sweep
- one workspace execution path

Useful measurement targets:

- total experiment wall time
- time spent in episode stepping
- time spent in snapshot creation
- time spent in model serialization
- time spent in persistence writes

Without this, optimization work risks guessing correctly in broad direction but
incorrectly in implementation priority.


## Likely Prioritization

The best first-wave order is probably:

### First-wave changes

- add benchmark/profiling support
- add optional episode-level parallel execution
- add optional run-level parallel execution for sweeps
- separate full-trace from faster execution modes
- remove avoidable artifact duplication at run-result level

These changes have the best ratio of:

- expected speed gain
- implementation tractability
- architectural safety

### Second-wave changes

- snapshot reduction
- delta-based replay formats
- lower-overhead in-memory trace representations
- serialization format redesign

These may yield larger long-term gains, but they are also much more invasive.


## Architectural Direction

The strongest direction is not:

- "rewrite everything for speed"

The stronger direction is:

> preserve AXIS's deterministic replay-first architecture, but make
> observability level and execution parallelism explicit configurable concerns

So the architecture should evolve toward:

- explicit execution profiles
- explicit concurrency policy
- explicit artifact policy

Conceptually:

```text
ExperimentConfig
-> execution policy
   - sequential / parallel
   - max workers
   - trace mode
   - persistence mode
-> run execution
-> artifact production
```

This keeps speed improvements aligned with the current framework structure
instead of fighting it.


## Constraints That Must Be Preserved

Any speedup design must preserve the following properties.

### Determinism

Parallel execution must not change seeded outcomes.

That means:

- seeds must be resolved before worker dispatch
- episode outputs must not depend on execution order
- shared mutable global state must be avoided

### Replay integrity

If replay artifacts are requested, the resulting traces must still satisfy the
current visualization and comparison contracts.

### Workspace compatibility

Workspace flows depend on structured persisted outputs.

Speed optimizations must not make workspace state ambiguous or less reliable.

### Plugin/system isolation

Systems and worlds should not need to know whether execution is sequential or
parallel.

Parallelism should remain framework-owned.


## Key Risks

### 1. Determinism regressions

Parallel execution can accidentally introduce ordering-dependent behavior if
logging, plugin registration, or shared caches become stateful.

### 2. Artifact contract fragmentation

If multiple trace modes are introduced carelessly, downstream consumers may
have to support too many partial variants.

### 3. Increased operational complexity

Parallel persistence, progress reporting, and resume behavior are more complex
than the current serial model.

### 4. Premature deep-format redesign

Changing replay data shape too early may create more churn than value if large
speedups are already available from multicore execution and trace-mode control.


## Recommended Draft Conclusion

The strongest current hypothesis is:

> AXIS can likely achieve a substantial execution speedup by combining
> multicore execution with configurable trace richness before attempting any
> deep replay-format redesign

So the recommended next document should develop a more detailed design around:

- episode-parallel execution
- run-parallel execution for sweeps
- configurable trace and persistence modes
- benchmark-driven profiling
- artifact contract preservation

This should become the `detailed-draft` stage.


## Proposed Document Sequence

This idea should follow the standard progression:

- `draft.md`
- `detailed-draft.md`
- `spec.md`
- `engineering-spec.md`
- `implementation-roadmap.md`
- `work-packages.md`

Recommended directory:

- `docs-internal/ideas/calc-speedup/`
