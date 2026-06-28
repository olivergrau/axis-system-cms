# AXIS Delta-Opt Trace Specification

## Version 1 Draft Specification

---

## 1. Purpose

This document defines a new AXIS trace mode: `delta-opt`.

The purpose of `delta-opt` is to reduce:

- peak memory usage during execution
- persisted trace size on disk
- JSON serialization cost
- replay artifact duplication

while preserving:

- replay correctness
- post-hoc mechanistic analysis
- the visualizer contract that consumers receive fully materialized replay data

The motivating issue is that the current `delta` mode remains too heavy for
longer runs such as `400`-step episodes with many episodes per run. In current
practice, this can produce multi-hundred-megabyte run artifacts and very high
transient memory pressure.

This specification defines:

- the semantics of `delta-opt`
- the persistence contract for compact replay-capable traces
- the replay-data-layer reconstruction model
- the execution and memory model requirements that should support scalable runs
  across trace modes
- the treatment of deterministic and stochastic world dynamics
- required compatibility guarantees for visualization and analysis consumers

This specification does not define:

- the exact binary or JSON encoding optimizations
- the concrete phased migration plan for removing `full`, `light`, or `delta`
- low-level benchmarking methodology
- the final future persistence format after all legacy modes are removed

---

## 2. Scope

This specification applies to:

- trace mode semantics
- episode execution and persistence
- execution-time memory behavior
- replay reconstruction
- replay access and visualization-facing materialization
- comparison and analysis consumers that load replay traces

This specification focuses specifically on:

- `trace_mode = delta-opt`
- current replay-capable grid-style worlds
- future compatibility with stochastic worlds

At the same time, the execution and memory requirements in this specification
are intended to be orthogonal to trace storage mode wherever possible.

This specification does not require:

- immediate removal of `full`
- immediate removal of `light`
- immediate removal of existing `delta`

`delta-opt` is introduced as a new mode first. Existing modes may be removed
later only after `delta-opt` is proven correct and sufficient.

---

## 3. Normative Terms

The terms **must**, **must not**, **should**, and **may** are to be interpreted
normatively.

---

## 4. Problem Statement

The current `delta` mode is replay-compatible, but still too expensive.

### 4.1 Current Failure Pattern

In the current implementation:

- each episode is fully accumulated in memory before persistence
- run execution holds all episode results in memory simultaneously
- parallel episode execution multiplies this pressure
- worker processes return large episode objects back to the parent process
- completed episodes are persisted twice:
  - once as individual episode artifacts
  - once again inside `run_result.json`

For long runs, this creates very large transient and persisted data volumes.

### 4.2 Current Data Inflation Sources

The main inflation sources are:

- full per-step `regen_delta` persistence, especially in dense regeneration worlds
- repeated large system trace payloads such as:
  - `buffer_snapshot`
  - `visit_counts_map`
- duplicate storage of whole episode traces inside `run_result.json`
- pretty-printed JSON for very large artifacts
- large inter-process result transfer under parallel execution
- run summary computation that depends on retaining complete episode objects

### 4.3 Architectural Constraint

AXIS currently assumes that:

- replay consumers do not simulate world logic themselves
- the visualizer receives fully materialized trace data

This is a valuable architectural property and must be preserved.

Therefore, the optimization must not simply move simulation logic into the
visualizer.

AXIS also currently behaves as though higher `max_workers` is mostly a
throughput question. For large replay-capable runs, this is incomplete. Worker
parallelism is also a memory-allocation policy and must be treated as such.

---

## 5. Design Goals

`delta-opt` must:

- remain replay-capable
- materially reduce persisted trace size
- materially reduce peak memory pressure
- materially reduce execution-time object retention
- preserve current visualization semantics for consumers
- allow later support for stochastic worlds

`delta-opt` should:

- reduce or eliminate redundant replay persistence
- centralize reconstruction in a dedicated replay data layer
- keep replay semantics explicit rather than implicit
- support deterministic and stochastic world reconstruction under one model
- support large runs without memory scaling linearly with total replay payload

`delta-opt` must not:

- require the visualizer to run world simulation logic directly
- silently weaken replay correctness
- depend on brittle, hidden assumptions about RNG usage
- rely on full-run in-memory accumulation as a normal execution strategy

---
## 5A. Execution And Memory Goals

In addition to trace optimization, AXIS must optimize the execution model so
that replay-capable runs remain usable for larger experiments.

These execution and memory goals are not specific to `delta-opt` alone.

They should, where architecturally possible, apply across existing trace modes:

- `full`
- `light`
- `delta`
- `delta-opt`

`delta-opt` is the main new storage contract introduced by this specification.
The execution-memory model is a separate concern that should ideally improve all
trace modes, even if some optimizations yield larger benefits for compact modes
than for legacy ones.

The optimized execution path should aim for:

- bounded peak memory per worker
- bounded peak memory in the parent process
- incremental persistence
- incremental aggregation
- reduced inter-process payload transfer

For large runs, memory usage should scale primarily with:

- the largest in-flight episode payload
- the number of concurrent workers
- compact aggregation state

It should not scale primarily with:

- the total number of episodes in the run
- the total persisted replay payload size of the run
- duplicated replay artifacts held simultaneously in memory

---

## 6. Core Model

### 6.1 Two-Level Replay Contract

AXIS must distinguish between:

- **storage trace**
- **replay trace**

The storage trace is the persisted compact artifact.

The replay trace is the fully materialized, consumer-facing trace returned by
the replay access layer.

The visualizer, comparison layer, and replay-oriented analysis tools must
continue to consume replay traces, not raw compact storage traces.

### 6.2 Replay Data Layer Rule

All reconstruction must happen in a replay data layer below consumers.

The visualizer must remain a reader of replay-ready data rather than a world
simulator.

In other words:

```text
persisted delta-opt trace
-> replay data layer reconstruction
-> full replay trace
-> visualizer / replay consumer
```

### 6.3 Compatibility Rule

For visualization and replay consumers, `delta-opt` must appear equivalent to
loading a fully materialized replay trace.

That means:

- world phases must still resolve correctly
- `BEFORE`, `AFTER_REGEN`, and `AFTER_ACTION` views must still work
- system and world visualization adapters must still receive the data they need

---

## 7. New Trace Mode

### 7.1 Required Value

AXIS execution policy must support a new trace mode:

- `delta-opt`

### 7.2 Semantic Definition

`delta-opt` is a replay-capable compact trace mode in which AXIS persists:

- only the minimal state required for deterministic or replay-governed
  reconstruction
- only stochastic outcomes, not full stochastic world deltas
- only compact run-level metadata, not duplicate whole-run episode traces

### 7.3 Relationship To Existing Modes

- `full` persists fully materialized replay data
- `delta` persists compact world deltas plus trace payloads
- `delta-opt` persists a more minimal replay contract and reconstructs full
  replay traces in the replay data layer

`delta-opt` must not change the meaning of `full` or `delta` while those modes
still exist.

---
## 7A. Execution Memory Model

### 7A.1 General Rule

`delta-opt` is a trace storage and replay-contract mode.

It is not, by definition, an execution mode.

Execution-memory optimization must be treated as a separate architectural axis
that should remain compatible with multiple trace modes.

However, `delta-opt` is expected to benefit strongly from that separate
execution-memory optimization axis.

### 7A.2 Bounded Retention Rule

AXIS should not retain all replay-capable episode traces in memory until the end
of a run when executing replay-capable workloads, regardless of whether the
trace mode is `full`, `delta`, or `delta-opt`, unless some explicit exception
is required.

Instead, completed episode data should be reduced and persisted as early as
possible.

### 7A.3 Streaming Aggregation Rule

Run-level summaries should be computed incrementally where possible.

The execution path should keep only the minimal per-episode summary quantities
needed for aggregate statistics, such as:

- total steps
- final vitality
- termination reason
- any other scalar episode-level fields required for run summary

The execution path should not require the full replay payload of every episode
to remain resident merely to produce run-level summaries.

This rule should apply across trace modes wherever possible.

### 7A.4 Parent Process Minimization Rule

Under parallel execution, the parent process should not be used as a sink for
large replay payloads from every worker unless explicitly required.

The parent process should receive compact completion information whenever
possible.

### 7A.5 Worker Memory Rule

Worker processes should dispose of replay-heavy intermediate structures as soon
as the episode artifact has been durably persisted and any required compact
summary payload has been emitted.

### 7A.6 No Run-Scale Replay Accumulation Rule

AXIS should avoid run architectures where the memory footprint naturally
grows with:

- the number of completed episodes
- the length of all completed episodes

This behavior is considered a non-goal for the optimized execution model in
general, including when used with `delta-opt`.

---

## 8. Delta-Opt Persistence Contract

### 8.1 General Rule

The persisted `delta-opt` trace must contain everything required to
deterministically materialize a full replay trace through the official replay
pipeline.

It does not need to contain every fully materialized intermediate state
explicitly.

### 8.2 Minimal Episode-Level Requirements

A `delta-opt` episode must contain at least:

- initial world snapshot
- world identity and relevant world config
- ordered per-step action record
- ordered per-step action outcome record sufficient to reconstruct world
  evolution
- system decision and transition data required for replay interpretation
- episode termination and summary fields

### 8.3 Deterministic World Rule

For deterministic worlds, `delta-opt` must be allowed to omit explicit
`regen_delta` persistence if the replay data layer can reconstruct the same
world transition from:

- the prior world state
- the persisted world config
- the persisted action and action outcome data
- the official world dynamics implementation

### 8.4 Stochastic World Rule

For stochastic worlds, `delta-opt` must not persist the full resulting world
delta by default.

Instead, it must persist only the stochastic outcomes required to replay the
same world evolution.

This is the required model:

> Persist only the stochastic outcomes, not the whole delta-world.

Examples of acceptable persisted replay inputs include:

- sampled event payloads
- stochastic transition decisions
- explicit replay-state payloads
- RNG-state payloads if used carefully

Examples of disallowed weak contracts include:

- “same seed should probably replay the same way”
- hidden dependence on exact RNG call count without explicit contract

---
## 8A. Incremental Persistence Model

### 8A.1 Episode Persistence Rule

Optimized execution should persist episode artifacts incrementally rather than
after the full run has completed.

The intended lifecycle is:

1. episode executes
2. compact episode artifact is produced
3. episode artifact is persisted
4. compact summary contribution is retained
5. large episode objects become eligible for release

### 8A.2 Run Artifact Rule

Run-level artifacts should be finalized from compact summary information and
artifact references.

They should not require re-embedding all episode replay payloads.

### 8A.3 Failure Recovery Consideration

Incremental persistence should improve not only memory behavior, but also crash
survivability of long-running experiments, because already completed episodes
can exist durably on disk even if the overall run later fails.

Failure recovery details are out of scope for this specification, but the
execution model should not move away from this direction.

---

## 9. Replay Reconstruction Model

### 9.1 Required Replay Pipeline

The replay data layer must reconstruct the full replay trace by:

1. loading the compact `delta-opt` episode
2. reconstructing the world step sequence phase by phase
3. materializing full replay snapshots for consumer access

### 9.2 Required Reconstruction Outputs

The replay layer must be able to materialize:

- `world_before`
- `world_after_regen`
- `world_after`
- system step payloads
- world metadata payloads required by visualization

### 9.3 Visualizer Isolation Rule

The visualizer must not be responsible for:

- applying world tick logic
- replaying stochastic outcomes
- inferring omitted world phases

Those responsibilities belong only to the replay data layer.

### 9.4 Replay Equivalence Rule

The reconstructed replay trace must be semantically equivalent to the current
consumer-facing full replay trace for the supported worlds and trace content.

“Equivalent” here means:

- the same per-step world states for replay purposes
- the same step ordering
- the same visible intermediate phases
- the same analysis-relevant system payloads

---

## 10. World Replay Classes

To avoid hidden assumptions, AXIS should explicitly distinguish replay classes
for worlds.

### 10.1 Deterministic Replayable

A world is **deterministic replayable** if its world evolution can be
reconstructed from:

- prior world state
- world config
- persisted step actions and action outcomes

No stochastic replay payload is required.

### 10.2 Outcome-Replayable

A world is **outcome-replayable** if it contains stochastic dynamics but can be
replayed exactly when the relevant stochastic outcomes are persisted.

This is the preferred model for future stochastic worlds.

### 10.3 Seed-Replayable

A world may be **seed-replayable** only if AXIS explicitly guarantees that the
replay contract includes strict RNG schedule stability.

This class is allowed in principle but should be treated as fragile and should
not be the preferred design target.

### 10.4 Required Policy

`delta-opt` should prefer:

- deterministic replayable worlds
- outcome-replayable worlds

It should avoid relying on seed-only replay unless the replay contract is made
explicit and robust.

---

## 11. Required Optimization Changes

### 11.1 Remove Duplicate Run-Level Trace Persistence

For `delta-opt`, AXIS must not persist complete episode traces again inside
`run_result.json`.

Run-level artifacts should contain only:

- run metadata
- run summary
- references or identities for episode artifacts if needed

### 11.2 Stream Episode Persistence

`delta-opt` execution should persist episode artifacts incrementally rather than
holding a full run's episode traces in memory before writing.

At minimum, the architecture should move toward:

- episode completed
- episode persisted
- only compact per-run aggregates retained in memory

### 11.3 Compact JSON Serialization

Large trace artifacts in `delta-opt` should be serialized compactly rather than
pretty-printed.

Pretty-printing should not be required for high-volume trace artifacts.

### 11.4 Redundant System Trace Removal

`delta-opt` should remove redundant persisted fields where the same information
can be deterministically reconstructed from other persisted fields.

Likely candidates include:

- duplicated score variants
- derived counterfactual payloads already represented elsewhere
- repeated full world-model snapshots when only incremental reconstruction is
  needed

---

## 12. Trace Payload Reduction Rules

### 12.1 Deterministically Reconstructable Fields

If a field can be reconstructed exactly from the persisted replay contract and
official reconstruction logic, `delta-opt` may omit it from storage.

### 12.2 Current Candidate Reductions

The following are expected candidates for omission or redesign under
`delta-opt`, provided replay correctness is preserved:

- explicit `regen_delta` for deterministic grid worlds
- `buffer_snapshot`
- `visit_counts_map`
- other repeated deterministic world-model summaries

These may still exist in the replay trace returned to consumers, but need not
exist as stored raw payloads.

### 12.3 Consumer Visibility Rule

If a consumer currently relies on one of these fields, the replay data layer
must reconstruct it before the consumer sees the step trace.

---

## 13. Run Result Contract

### 13.1 Current Problem

Current run persistence duplicates episode traces:

- individual episode files
- full run-level embedded traces

This is not acceptable for `delta-opt`.

### 13.2 Required Contract

For `delta-opt`, `run_result.json` must be reduced to a compact run result.

It should contain:

- run identity
- summary
- seeds if still required
- config reference or embedded compact config

It must not contain:

- full embedded episode trace payloads

### 13.3 Replay Source Of Truth

For `delta-opt`, the episode artifacts must be the replay source of truth.

---
## 13A. Parallel Execution Guardrails

### 13A.1 General Rule

Parallel execution in replay-capable modes must be treated as both a throughput
policy and a memory policy.

### 13A.2 Result Transfer Rule

For optimized replay-capable execution, AXIS should prefer execution patterns
where workers do not return full replay payloads to the parent process after
completion.

Preferred models include:

- worker-side persistence plus compact completion payload
- worker-side persistence plus compact aggregation payload
- worker-side persistence plus small artifact reference payload

### 13A.3 Worker Count Safety

AXIS should make it possible to constrain worker parallelism when replay-heavy
episode payloads would otherwise create unsafe peak memory pressure.

This may later include:

- explicit memory-aware worker caps
- adaptive worker selection
- mode-specific parallelism defaults

The precise mechanism is out of scope here, but the need is normative.

### 13A.4 Parent Aggregation Safety

The parent process should aggregate compact run state, not a growing list of
large replay objects, whenever the optimized execution path is used.

---

## 14. Analysis Compatibility

### 14.1 General Rule

Replay-oriented analysis consumers must continue to work through the replay data
layer, not by assuming that all persisted storage artifacts are already fully
materialized.

### 14.2 Required Compatibility

The following workflows must remain possible:

- replay visualization
- paired trace comparison
- metrics derived from replay traces
- notebook-level inspection via replay-access paths

### 14.3 No Silent Consumer Breakage

The migration to `delta-opt` must not silently break consumers that currently
expect replay-complete traces through official access paths.

If a consumer reads raw episode JSON directly, that consumer may require
migration.

---

## 15. Migration Strategy

### 15.1 Introduction Strategy

`delta-opt` must be introduced as a new trace mode first.

It should coexist with:

- `full`
- `light`
- `delta`

until replay correctness and analysis compatibility are validated.

### 15.2 Validation Requirement

Before deprecating older modes, AXIS should validate that `delta-opt` supports:

- replay visualization parity
- comparison parity
- metrics parity where expected
- significantly lower memory pressure
- materially smaller persisted artifacts

### 15.3 Long-Term Direction

If `delta-opt` proves sufficient, AXIS may later simplify trace-mode support and
remove older modes.

That later simplification is explicitly out of scope for this specification.

---

## 16. Open Questions

The following questions remain open and should be resolved in engineering work:

- What is the precise minimal step payload for deterministic grid replay?
- Which system trace fields should remain persisted versus reconstructed?
- Should outcome-replayable worlds persist sampled events, RNG state, or a
  world-specific replay token?
- Should the replay layer materialize all steps eagerly or lazily?
- What compatibility layer is needed for old persisted `delta` artifacts?
- What is the correct streaming aggregation interface for run summaries?
- Should worker-side persistence be mandatory for `delta-opt`?
- How should `delta-opt` interact with run-resume or partial-run recovery later?
- Which execution-memory optimizations can be applied uniformly across all trace
  modes, and which must remain mode-specific?

---

## 17. Summary

`delta-opt` is a new compact replay-capable trace mode for AXIS.

Its core rules are:

- reconstruction happens in the replay data layer, not in the visualizer
- the visualizer still receives full replay-ready traces
- deterministic world phases may be reconstructed instead of fully persisted
- stochastic worlds should persist stochastic outcomes, not full resulting world
  deltas
- run-level trace duplication must be removed
- memory and I/O pressure must be reduced by contract, not only by incidental
  implementation tweaks
- execution memory behavior must be optimized alongside trace format design
- execution-memory optimization is a separate axis from trace storage mode
- multi-worker execution must be explicitly handled as a memory-management
  problem, not only as a throughput problem

This preserves the conceptual strength of AXIS replay while making the trace
pipeline substantially more scalable.
