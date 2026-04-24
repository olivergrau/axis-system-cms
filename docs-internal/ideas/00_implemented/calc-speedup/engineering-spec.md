# AXIS Calculation Speedup Engineering Specification

## 1. Purpose

This engineering specification derives the implementation shape of the
framework-level **calculation speedup** model from:

- [Calculation Speedup Spec](./spec.md)

The goal is to improve execution throughput in AXIS through:

- explicit execution policy
- deterministic multicore execution
- trace-mode-aware output handling
- reduced non-replay persistence overhead

while preserving the current replay-rich path as the normative `full` mode.


## 2. Implementation Goal

The framework shall gain a new internal execution layer that makes three
previously implicit concerns explicit:

- trace richness
- concurrency strategy
- worker count

This layer shall then drive:

- experiment execution
- run execution
- persistence decisions
- logging behavior
- workspace execution routing

The first implementation wave shall optimize for:

- good speedup
- low architecture risk
- predictable integration with the current system

The first wave shall **not** redesign replay consumers or visualization
contracts.


## 3. Current System Baseline

Based on the current codebase, AXIS execution is structured as follows.

### 3.1 Configuration

Execution settings currently live in:

- `src/axis/framework/config.py`

The current `ExecutionConfig` only contains:

- `max_steps`

There is no explicit concept yet for:

- trace mode
- parallelism mode
- worker count

### 3.2 Experiment orchestration

Experiment orchestration currently lives in:

- `src/axis/framework/experiment.py`

Current behavior:

- resolve runs
- execute them serially
- persist run artifacts
- build final experiment summary

The current implementation also still includes resume-oriented logic and status
handling for partial completion.

### 3.3 Run execution

Run execution currently lives in:

- `src/axis/framework/run.py`

Current behavior:

- resolve episode seeds
- create one system instance in the parent process
- execute episodes serially
- collect `BaseEpisodeTrace`
- compute `RunSummary`

There is currently no worker abstraction, no episode-parallel path, and no
lightweight per-episode result type.

### 3.4 Step execution

Step execution currently lives in:

- `src/axis/framework/runner.py`

Current behavior:

- always constructs replay-rich step traces
- always captures multiple snapshots per step
- always returns `BaseEpisodeTrace`

The runner currently conflates:

- simulation
- replay trace construction

This is the main reason new trace modes cannot simply be added by configuration
alone without introducing distinct output lanes.

### 3.5 Persistence

Persistence currently lives in:

- `src/axis/framework/persistence.py`

Current behavior:

- persists experiment config/metadata/status/summary
- persists run config/metadata/status/summary/result
- persists per-episode replay traces

Current persisted run results embed full `RunResult`, which includes:

- `episode_traces`

This creates high persistence cost and potential duplication with per-episode
trace files.

### 3.6 Logging

Episode logging currently lives in:

- `src/axis/framework/logging.py`

Current behavior assumes replay-rich episode traces:

- `EpisodeLogger.log_episode(trace, episode_index)`
- iterates through `trace.steps`

This means the logging subsystem currently depends on the `full` trace contract.

### 3.7 Plugin discovery and runtime catalogs

Plugin discovery currently lives in:

- `src/axis/plugins.py`

Current behavior:

- global discovery with module-level discovered flag
- registry-driven creation of systems/worlds

This matters for multiprocessing because worker processes must not assume that
the parent process's registry state is inherited consistently on all platforms.

### 3.8 Workspace execution

Workspace routing currently lives in:

- `src/axis/framework/workspaces/execute.py`

Current behavior:

- loads config
- creates a repository rooted in `<workspace>/results`
- delegates to `ExperimentExecutor`

This is good for the speedup initiative because workspace execution already
delegates to the core framework.


## 4. Architectural Placement

### 4.1 New framework module for execution policy

Introduce a new internal module:

- `src/axis/framework/execution_policy.py`

Responsibilities:

- execution policy enums
- policy normalization helpers
- validation rules
- defaults

This module should contain:

- `TraceMode`
- `ParallelismMode`
- `ExecutionPolicy`

This module should **not** contain:

- worker pool orchestration
- persistence logic
- CLI parsing

### 4.2 New framework module for lightweight outputs

Introduce a new internal module:

- `src/axis/framework/execution_results.py`

Responsibilities:

- lightweight episode result model
- lightweight run result model
- delta run result model
- helper functions for summary extraction

This module should provide the semantic bridge between:

- `full` replay-rich execution
- `delta` replay-capable compact execution
- `light` summary-oriented execution

### 4.3 New framework module for parallel execution

Introduce a new internal module:

- `src/axis/framework/parallel_execution.py`

Responsibilities:

- worker entry functions
- parent-side dispatch helpers
- deterministic result reassembly
- parallel execution policy interpretation

This module should contain framework-owned worker entry points rather than
scattering multiprocessing logic across `experiment.py` and `run.py`.


## 5. New Internal Model

### 5.1 `TraceMode`

Introduce an enum:

- `TraceMode`
  - `FULL`
  - `DELTA`
  - `LIGHT`

### 5.2 `ParallelismMode`

Introduce an enum:

- `ParallelismMode`
  - `SEQUENTIAL`
  - `EPISODES`
  - `RUNS`

### 5.3 `ExecutionPolicy`

Introduce a normalized internal model:

- `ExecutionPolicy`

Required fields:

- `trace_mode`
- `parallelism_mode`
- `max_workers`

This model should be used internally even if the persisted config still stores
the raw values inside `ExecutionConfig`.

### 5.4 Lightweight episode result

Introduce:

- `LightEpisodeResult`

Required fields:

- `episode_index`
- `episode_seed`
- `total_steps`
- `final_vitality`
- `termination_reason`
- optional `final_position`

This model should be enough to support current run-level summary computation.

### 5.5 Lightweight run result

Introduce:

- `LightRunResult`

Required fields:

- `run_id`
- `num_episodes`
- `episode_results`
- `summary`
- `seeds`
- `config`

Unlike the current `RunResult`, this model should not carry full
`BaseEpisodeTrace` payloads.

### 5.6 Delta replay result

Introduce:

- `DeltaEpisodeTrace`
- `DeltaRunResult`

These models should represent compact replay-capable artifacts that can be
reconstructed into `BaseEpisodeTrace` for replay consumers.


## 6. Configuration Changes

### 6.1 Extend `ExecutionConfig`

The first implementation wave should extend:

- `src/axis/framework/config.py`

Current:

- `max_steps`

Required additions:

- `trace_mode: str = "full"`
- `parallelism_mode: str = "sequential"`
- `max_workers: int = 1`

These may initially be stored as strings in the persisted config and converted
to normalized enums via `execution_policy.py`.

### 6.2 Validation rules

`ExecutionConfig` validation should enforce at least:

- `max_workers >= 1`
- `trace_mode in {"full", "delta", "light"}`
- `parallelism_mode in {"sequential", "episodes", "runs"}`

Recommended additional rule:

- `parallelism_mode == "sequential" -> max_workers` may remain > 1 but should
  effectively behave as `1`

### 6.3 Compatibility note

Older configs that omit the new fields should continue to default to the
current behavior.


## 7. Runner Refactor

### 7.1 Current limitation

`run_episode()` currently always returns `BaseEpisodeTrace`.

That makes the step runner replay-oriented by construction.

### 7.2 Required design change

The runner layer should be split conceptually into:

- simulation
- trace/result collection

The recommended first-wave implementation is not a deep trace rewrite.

Instead, it should introduce a collector strategy.

### 7.3 Collector pattern

Introduce an internal collector concept in or near:

- `src/axis/framework/runner.py`

Recommended collector types:

- `FullTraceCollector`
- `DeltaTraceCollector`
- `LightTraceCollector`

The step loop should remain singular.

What changes is:

- what is recorded per step
- what final episode output object is produced

### 7.4 Output contract

For `full` mode:

- the collector returns `BaseEpisodeTrace`

For `delta` mode:

- the collector returns `DeltaEpisodeTrace`
- the collector persists compact replay-capable state
- replay readers reconstruct `BaseEpisodeTrace` on load

For `light` mode:

- the collector returns `LightEpisodeResult`

This keeps the simulation loop shared while isolating the artifact policy.


## 8. Run Executor Refactor

### 8.1 Current limitation

`RunExecutor.execute()` currently:

- creates the system instance once in the parent process
- executes episodes serially
- always collects replay traces

This is not compatible with process-based episode parallelism.

### 8.2 Required design change

`RunExecutor` should be refactored so that episode execution is delegated
through an execution-policy-aware path.

Recommended methods:

- `_execute_sequential_full(...)`
- `_execute_sequential_delta(...)`
- `_execute_sequential_light(...)`
- `_execute_parallel_episodes_full(...)`
- `_execute_parallel_episodes_delta(...)`
- `_execute_parallel_episodes_light(...)`

These may be factored more elegantly internally, but the semantic distinction
must exist.

### 8.3 System instance ownership

For sequential execution:

- keep local system creation per run or per episode as needed

For parallel execution:

- each worker must create its own system instance

The parent process must not attempt to share a live system object across worker
boundaries.

### 8.4 Summary computation

Current `compute_run_summary()` expects `BaseEpisodeTrace`.

It should be generalized so it can compute from either:

- full episode traces
- delta episode traces
- lightweight episode results

The simplest first-wave approach is to define a shared episode-summary protocol
or extract only the fields needed by summary computation.


## 9. Parallel Execution Module

### 9.1 Worker payload

The worker payload should be explicit and pickle-safe.

Recommended fields:

- serialized `RunConfig`
- episode index or run index
- episode seed or resolved run config
- execution policy subset

### 9.2 Worker initialization

Worker entry points must call plugin discovery explicitly before attempting:

- system creation
- world creation

This is required because registry state is currently populated through:

- `src/axis/plugins.py`

and cannot be assumed to be preinitialized uniformly under process spawning.

### 9.3 Result ordering

Parent-side aggregation must sort worker results by canonical index:

- episode index for episode parallelism
- run index for run parallelism

### 9.4 Recommended transport boundary

The engineering spec recommends using configuration data and result data as the
only process boundary payloads.

The worker layer should not pass live system or world objects across process
boundaries.


## 10. Experiment Executor Refactor

### 10.1 Current limitation

`ExperimentExecutor` currently embeds:

- serial run execution
- run persistence sequencing
- resume semantics

### 10.2 Required design change

`ExperimentExecutor` should become execution-policy-aware and optionally use
parallel run execution when:

- `parallelism_mode == runs`

### 10.3 Resume removal or isolation

The engineering spec recommends one of two approaches:

#### Preferred

Remove resume-oriented logic from the execution-critical path in the first
speedup wave.

This means:

- de-emphasize or remove `_resume_with_persistence`
- simplify run status semantics

#### Acceptable transitional fallback

Keep resume wrappers temporarily, but do not let them shape the parallel
execution architecture.

### 10.4 Persistence finalization

Experiment finalization must be mode-aware.

In particular, it must not assume that all run results contain full episode
traces.


## 11. Persistence Changes

### 11.1 Principle

The persistence layer should become trace-mode-aware without redesigning the
repository tree in the first wave.

### 11.2 Keep current directory layout

The first implementation wave should preserve the current top-level layout:

- experiment directory
- runs directory
- per-run artifact files
- per-episode artifact files where applicable

### 11.3 New persisted execution-policy semantics

The persisted config already captures execution settings indirectly through
`ExperimentConfig`.

No separate execution-policy artifact is strictly required in the first wave if
the config file already contains the fields.

### 11.4 Delta-mode episode artifact

For `delta` mode, introduce a compact replay-capable episode artifact.

Recommended shape:

- initial world snapshot once per episode
- per-step deltas for replay phases
- unchanged replay metadata retained as-is

The persistence layer should reconstruct `BaseEpisodeTrace` when replay readers
load the artifact.

### 11.5 Light-mode episode artifact

For `light` mode, introduce a separate lightweight episode artifact rather than
writing malformed full replay traces.

Recommended file strategy:

- continue using the `episodes/` directory
- store light episode payloads in a distinguishable form

Recommended naming options:

- `episode_0001.light.json`
- or an explicit metadata field inside a uniform file name

The first-wave engineering choice should favor clarity over clever format reuse.

### 11.6 Run result persistence

`save_run_result()` and `load_run_result()` in `persistence.py` are currently
tied to `RunResult`.

This needs a design split.

Recommended new persistence functions:

- `save_full_run_result(...)`
- `save_delta_run_result(...)`
- `save_light_run_result(...)`
- corresponding load helpers where needed

An alternative is to persist only summaries plus per-episode artifacts in
`light` mode and omit a full run-result file entirely.

That second option is attractive and should be considered strongly because it
reduces duplication.

### 11.7 Status files

If resume is removed or de-emphasized, run/experiment status handling can be
simplified significantly.

The first speedup wave should review whether:

- `RUNNING`
- `PARTIAL`

remain necessary in the current form.


## 12. Logging Changes

### 12.1 Current limitation

`EpisodeLogger` currently assumes `BaseEpisodeTrace` with step-level replay
content.

### 12.2 Required design change

Logging must become mode-aware.

Recommended split:

- `FullEpisodeLogger`
- `DeltaEpisodeLogger`
- `LightEpisodeLogger`

or one logger with two explicit code paths.

### 12.3 Light-mode logging

In `light` mode, step-level logging should either:

- be disabled
- or be limited to a lightweight summary-level view

The logging subsystem must not force construction of full replay traces in
`light` mode.

### 12.4 Parallel logging caution

Parallel workers must not write unsynchronized human-facing console logs that
become unreadable by interleaving arbitrarily.

Recommended first-wave rule:

- keep per-worker console logging minimal
- aggregate summary logging in the parent process


## 13. Workspace Integration

### 13.1 Current advantage

Workspace execution already delegates through:

- `src/axis/framework/workspaces/execute.py`

This means workspace support does not require a separate execution engine.

### 13.2 Required change

Workspace execution should pass through execution policy exactly as it appears
in the resolved experiment config.

No workspace-specific reinterpretation of:

- `trace_mode`
- `parallelism_mode`
- `max_workers`

should be introduced in the first wave.

### 13.3 Workspace inspection implication

Workspace result inspection and downstream visualization must recognize that:

- `light` executions are not visualizable
- `delta` executions remain visualizable after reconstruction

This is downstream-facing work, but the engineering spec must call it out early
because it affects artifact semantics.


## 14. CLI and User-Facing Integration

### 14.1 Initial integration strategy

The normative source of execution policy should be configuration.

CLI overrides may exist later, but they should not be required for the first
implementation wave.

### 14.2 Existing code areas affected

Even if first-wave UX is config-first, the following areas will likely require
surface updates:

- `src/axis/framework/cli/commands/experiments.py`
- `src/axis/framework/cli/commands/workspaces.py`
- related manuals and docs


## 15. Testing Strategy

### 15.1 Determinism tests

Add tests that compare:

- sequential full
- sequential delta
- episode-parallel full
- episode-parallel delta
- run-parallel full
- run-parallel delta
- sequential light
- episode-parallel light
- run-parallel light

for identical seeds and configs.

Required assertions:

- same final outcomes
- same summaries
- same episode ordering

### 15.2 Persistence tests

Add tests for:

- full-mode artifact shape
- delta-mode artifact shape
- light-mode artifact shape
- non-replay detection for light artifacts

### 15.3 Cross-platform worker tests

The worker architecture should be exercised in a way that is compatible with
spawn-based execution assumptions.

At minimum, the design should avoid Linux-only assumptions in tests.

### 15.4 Benchmark tests

Introduce benchmark-style tests or scripts for representative workloads:

- single run, many episodes
- OFAT sweep
- workspace execution

The purpose is not strict CI performance gating in the first wave, but baseline
measurement.


## 16. Recommended File-Level Changes

The first-wave implementation is expected to affect at least:

### 16.1 New modules

- `src/axis/framework/execution_policy.py`
- `src/axis/framework/execution_results.py`
- `src/axis/framework/parallel_execution.py`

### 16.2 Refactored existing modules

- `src/axis/framework/config.py`
- `src/axis/framework/runner.py`
- `src/axis/framework/run.py`
- `src/axis/framework/experiment.py`
- `src/axis/framework/persistence.py`
- `src/axis/framework/logging.py`
- `src/axis/framework/workspaces/execute.py`

### 16.3 Likely downstream updates

- workspace inspection/resolution modules
- docs and manuals
- tests across `tests/framework/` and `tests/framework/workspaces/`


## 17. First-Wave Recommendation

The engineering recommendation for the first implementation wave is:

1. add execution-policy fields to config
2. add normalized execution-policy module
3. introduce lightweight episode/run result models
4. refactor runner around collector strategy
5. implement episode-parallel worker execution
6. implement run-parallel execution for sweeps
7. make persistence and logging trace-mode-aware
8. simplify or remove resume-driven complexity from experiment execution

This sequence best fits the current codebase because it layers the new behavior
on top of existing boundaries rather than forcing a replay-format rewrite.


## 18. Deferred Engineering Work

The following engineering directions are intentionally deferred:

- delta-trace encoding
- replay reconstruction from differential state
- binary persistence
- replacing the current full replay models with a lower-overhead runtime-only
  representation
- restoring resume as a guaranteed behavior

These may be pursued later if the first-wave speedups are insufficient.


## 19. Next Document

The next document should decompose this engineering plan into an ordered
delivery plan with implementation phases and dependency-aware milestones.

That should become the `implementation-roadmap.md` stage.
