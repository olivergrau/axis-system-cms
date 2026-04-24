# AXIS Calculation Speedup

## Detailed Draft for Lower-Risk Execution Throughput Improvements

---

## 1. Purpose

This document refines the initial calculation-speedup idea into a more
spec-oriented draft.

Its purpose is to define a practical speedup direction for AXIS that improves
execution throughput substantially while avoiding deep architectural risk in the
first implementation wave.

The intended optimization posture is:

- good acceleration
- minimal architecture risk
- no immediate replay-contract rewrite
- no dependence on backward compatibility for old artifacts

This document is still not a final specification.

It is a detailed draft intended to prepare a later spec by fixing:

- the preferred optimization scope
- the allowed design tradeoffs
- the target execution modes
- the recommended parallelization boundaries
- the artifact policy for fast versus replay-rich execution
- the sequencing of near-term versus later work


## 2. Optimization Goal

The primary goal is:

> make AXIS experiments execute materially faster in everyday use while
> preserving deterministic behavior and keeping the current replay model intact
> for the full-trace path

The target use case is not one narrow workflow.

The goal is to make execution broadly faster across:

- ordinary single-run experiments
- multi-episode runs
- OFAT sweeps
- workspace-driven execution flows

This means the optimization strategy should improve the general execution
architecture, not only one special-case code path.


## 3. Guiding Assumptions

This detailed draft proceeds under the following assumptions.

### 3.1 Low-risk improvements should come first

The first implementation wave should avoid deep redesign of:

- replay trace structure
- visualization contracts
- comparison artifact shape
- step-level trace semantics

The strongest early gains are expected from:

- multicore execution
- better separation of execution modes
- reduced persistence overhead in non-replay modes

### 3.2 Full replay remains a supported first-class mode

The existing replay-rich trace behavior should remain available as an explicit
execution mode.

This is important because replay, visualization, and debugging are central
AXIS capabilities.

### 3.3 Light execution modes may produce lighter artifacts

The framework should support additional lighter execution modes that optimize
for summaries and aggregate results instead of full replay fidelity.

This is a controlled extension of the framework contract, not an accidental
degradation.

### 3.4 Resume is no longer a defining constraint

This detailed draft assumes that robust resume support is not required to shape
the optimization architecture.

This meaningfully simplifies:

- parallel execution design
- artifact commit semantics
- worker lifecycle assumptions
- status management

Resume may later be reintroduced if desired, but it should not constrain the
first speedup architecture.

### 3.5 Cross-platform Python support should be preserved

The speedup design should remain viable across major Python platforms.

In practice that means parallelization choices must be compatible with:

- Linux
- macOS
- Windows

This especially matters for multiprocessing policy and pickling boundaries.


## 4. Current Runtime Model

The current execution stack is effectively:

```text
ExperimentExecutor
-> resolve RunConfig objects
-> execute runs sequentially
   -> execute episodes sequentially
      -> execute steps sequentially
         -> capture snapshots
         -> build Pydantic traces
         -> persist JSON artifacts
```

This model is simple and correct, but it leaves two strong opportunities
underused:

- independence between episodes
- independence between runs

At the same time, it always pays for replay-oriented richness even when the
caller may only need summaries or aggregate comparison inputs.


## 5. Detailed Problem Decomposition

### 5.1 Serial execution is the largest structural limit

The most obvious throughput bottleneck is that AXIS currently uses only one CPU
core for experiment execution logic.

This matters because the framework already has naturally isolated execution
units:

- one episode
- one run

Each such unit is already largely self-contained through:

- seed derivation
- fresh world construction
- fresh system initialization
- run-local artifact output

So the execution architecture has latent parallelism that is not yet exploited.

### 5.2 The framework pays the cost of full traces by default

The current runner captures multiple snapshots per step and constructs a full
`BaseStepTrace` object on every iteration.

This is appropriate for replay.

It is not obviously appropriate for every execution context.

Examples where full replay may be unnecessary:

- exploratory parameter tuning
- bulk sweeps
- CI sanity runs
- summary-oriented benchmark runs

### 5.3 Serialization and persistence likely amplify runtime cost

Persisting full episode traces, run results, and summaries as JSON adds:

- model dumping cost
- string generation cost
- filesystem write cost
- duplicated data at multiple artifact levels

These costs are especially visible when many episodes are produced.

### 5.4 The main hot path is allocation-heavy

The current step loop creates and transforms many immutable objects:

- world snapshots
- cell views
- step traces
- outcome copies
- nested system/world payload dictionaries

This cost is real, but changing it deeply would move the design toward trace
and replay refactoring.

That is valuable, but it is not the preferred first-wave risk profile.


## 6. Core Design Direction

The recommended design direction is:

> keep the existing full-trace execution model as one explicit execution mode,
> and add parallel execution plus lighter trace modes around it rather than
> rewriting the replay core immediately

This leads to three major design pillars:

1. explicit execution modes
2. explicit concurrency policy
3. explicit artifact policy

Conceptually:

```text
ExperimentConfig
-> execution policy
   - trace mode
   - concurrency mode
   - worker count
-> run execution
-> artifact production
```


## 7. Trace Mode Model

The detailed draft recommends introducing explicit trace modes.

### 7.1 Why trace modes should exist

Trace richness is currently implicit.

That makes it hard to optimize because the framework cannot distinguish:

- "I need full replay"
- "I need enough for summaries"
- "I need enough for comparison but not full visualization"

An explicit trace mode system turns this into a first-class framework policy.

### 7.2 Recommended first-wave modes

The first-wave design should define at least two modes.

#### `full`

Purpose:

- preserve current replay behavior
- support visualization
- support current comparison paths
- support detailed debugging

Behavior:

- capture current step traces
- capture current snapshots
- persist replay-compatible episode artifacts
- preserve current downstream compatibility expectations

#### `light`

Purpose:

- optimize for faster execution and summary-oriented workflows

Behavior:

- omit expensive replay-only data where possible
- produce enough information for run summary and experiment summary
- produce artifacts intentionally marked as non-replay

The `light` mode should be designed as a first-class contract, not as
"broken full mode".

### 7.3 Optional future third mode

A later extension may introduce:

#### `comparison_light`

Purpose:

- support comparison-oriented workflows with more structure than `light`
- but less cost than `full`

This mode should not be part of the first implementation wave unless the
specification work shows that it falls out naturally from the first two modes.

### 7.4 Important design rule

The current full trace contract should remain semantically stable.

The light mode should add a new execution lane rather than mutating the meaning
of the existing one.


## 8. What Light Mode Should Optimize

The detailed draft recommends that `light` mode optimize mainly by reducing
step-level artifact richness, not by changing system or world behavior.

That means the execution semantics of the episode should remain the same.

Only the recorded artifact surface changes.

### 8.1 Light mode should still preserve:

- deterministic seeded execution
- the same world evolution
- the same action decisions
- the same final outcome
- enough information to compute run-level summaries

### 8.2 Light mode may omit or reduce:

- full per-step snapshots
- intermediate snapshots
- replay-specific world data
- large step-level payloads not needed for summary computation
- persisted per-episode full traces

### 8.3 Light mode summary requirement

If full episode traces are not produced, the framework must still provide
enough per-episode result data to compute:

- total steps
- final vitality
- termination reason
- any run-level metrics that AXIS currently exposes

So the framework likely needs a distinct lighter episode result model rather
than attempting to fake a full `BaseEpisodeTrace`.

This is an extension of execution output modeling, but still materially smaller
in scope than a replay-trace redesign.


## 9. Concurrency Model

The detailed draft recommends a concurrency model centered on process-based
parallelism rather than threads.

### 9.1 Why process-based parallelism is preferred

Python CPU-bound workloads typically benefit more from multiprocessing than
threading due to the GIL.

AXIS execution appears dominated by:

- Python object creation
- world stepping
- Pydantic model construction
- serialization preparation

So thread-based parallelism is unlikely to yield the best throughput.

### 9.2 Episode-level parallelism

Episode-level parallelism should be the primary first-wave target.

Each episode can be executed independently if the worker receives:

- the resolved `RunConfig`
- the episode seed
- the episode index
- the required system/world catalogs or a reconstructible equivalent

This is attractive because:

- episodes are naturally independent
- aggregation semantics are simple
- determinism is easy to preserve
- the worker result shape is straightforward

### 9.3 Run-level parallelism

Run-level parallelism should also be supported, especially for OFAT sweeps.

However, it should be treated as a second layer above episode parallelism, not
as an entirely separate execution architecture.

Conceptually:

- single-run experiments may parallelize across episodes
- sweep experiments may parallelize across runs, episodes, or both

### 9.4 Hierarchical concurrency policy

The framework should avoid unconstrained nested parallelism.

A sensible policy is:

- choose one parallelization axis at a time by default
- allow configuration of whether parallelism happens at:
  - episode level
  - run level

This avoids oversubscription and reduces complexity.

Recommended default:

- prioritize episode-level parallelism for ordinary runs
- prioritize run-level parallelism only when sweep width is large and episode
  count is small

### 9.5 Cross-platform caution

Because Windows uses `spawn`, worker payloads must remain picklable and worker
startup assumptions must be explicit.

That means the design should avoid:

- unpicklable closures
- reliance on inherited mutable globals
- relying on already-initialized plugin registries in the parent process only

The worker entry path should be explicit and framework-owned.


## 10. Determinism Policy

Parallelization must not alter experimental outcomes.

The detailed draft therefore recommends three rules.

### 10.1 Seeds must be resolved before dispatch

Episode seeds and run seeds should be fully resolved in the parent process
before work is handed to workers.

### 10.2 Results must be reassembled deterministically

Even if episodes finish out of order, the final aggregated results should be
ordered canonically by:

- run index
- episode index

### 10.3 Workers must not share mutable execution state

System instances, worlds, and runtime RNG state should remain local to each
worker execution unit.


## 11. Persistence Policy

The detailed draft recommends that persistence policy become mode-aware.

### 11.1 Full mode persistence

In `full` mode, the current persisted replay-rich artifacts should remain the
normative output.

### 11.2 Light mode persistence

In `light` mode, persisted artifacts should be intentionally leaner.

The framework should persist only what the mode contract requires.

At minimum this likely includes:

- run config
- run summary
- experiment summary
- per-episode lightweight result records or enough aggregated information to
  justify the summaries

### 11.3 Run result duplication should be revisited

Even in full mode, the current duplication between per-episode traces and
`run_result.json` should be examined.

This is a lower-risk persistence cleanup and may provide meaningful savings
without changing replay trace semantics.


## 12. Resume Policy

This detailed draft recommends removing resume from the optimization-critical
path.

### 12.1 Why

Resume adds complexity to:

- partial worker completion handling
- status bookkeeping
- artifact transaction semantics
- deterministic reconstruction of incomplete work

### 12.2 Recommendation

The speedup initiative should proceed as if:

- interrupted runs may be rerun from scratch
- resume is not part of the primary design target

If resume remains in the codebase temporarily, it should not shape the core
architecture of the speedup spec.


## 13. Alternatives Considered

### 13.1 Delta-trace redesign now

Delta-traces are conceptually attractive because they could significantly
reduce snapshot and persistence costs.

However, they require deeper redesign of:

- replay artifact semantics
- snapshot reconstruction
- visualization expectations
- comparison consumers

This is likely too much architectural surface for the preferred first-wave risk
profile.

Recommendation:

- do not make delta-traces part of the first speedup implementation
- keep them as a later follow-on idea or later phase

### 13.2 In-memory trace model rewrite now

Replacing Pydantic-heavy runtime objects with lower-overhead internal structs
could also help, but this again pushes into a broader execution/replay redesign.

Recommendation:

- not first-wave

### 13.3 Alternative binary persistence immediately

Binary formats may reduce serialization cost, but introducing them early also
creates operational and tooling complexity.

Recommendation:

- keep JSON in the first wave unless profiling shows persistence cost is
  overwhelmingly dominant


## 14. Recommended First-Wave Architecture

The recommended first-wave architecture is:

### 14.1 Add explicit execution policy

Introduce execution-policy concepts such as:

- `trace_mode`
- `parallelism_mode`
- `max_workers`

These may live initially in framework execution config rather than being spread
implicitly across command flags.

### 14.2 Add episode-parallel worker execution

Make episode execution optionally parallel with deterministic ordered
reassembly.

### 14.3 Add run-parallel sweep execution

Allow OFAT-style experiments to execute runs in parallel when configured.

### 14.4 Add a light output lane

Introduce a lightweight per-episode/run output path sufficient for summaries,
without full replay artifacts.

### 14.5 Keep full replay lane intact

The current replay-rich behavior should remain available and explicit.


## 15. Suggested Configuration Direction

The detailed draft recommends that speedup controls become explicit framework
configuration rather than only ad hoc CLI flags.

Conceptually:

```text
execution:
  parallelism_mode: sequential | episodes | runs
  max_workers: 1 | N
  trace_mode: full | light
```

This keeps:

- config-driven reproducibility
- workspace integration
- experiment-level explicitness

CLI flags can later override these values, but configuration should be the
normative form.


## 16. Recommendation

The recommended path is:

### Phase 1

- add benchmark and profiling support
- introduce explicit execution policy concepts
- implement episode-parallel execution

### Phase 2

- implement run-parallel execution for sweeps
- implement `light` trace/output mode
- remove or de-emphasize resume semantics from the execution core

### Phase 3

- reduce duplicate persisted outputs
- refine worker startup and platform behavior
- harden workspace and CLI integration around execution policy

### Later, only if needed

- delta-traces
- replay-format redesign
- lower-overhead internal trace representations
- alternative persistence formats


## 17. Draft Conclusion

The strongest current conclusion is:

> AXIS should first pursue speed through explicit mode separation and
> multicore execution, not through immediate replay-trace redesign

This is the best fit for the desired balance of:

- meaningful acceleration
- clean design
- low implementation risk
- preserved replay trust in the full mode

The next document should therefore formalize:

- execution policy concepts
- light versus full output contracts
- episode-parallel and run-parallel semantics
- deterministic aggregation rules
- persistence expectations by mode

That should become the `spec.md` stage.
