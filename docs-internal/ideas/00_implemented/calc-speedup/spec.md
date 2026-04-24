# AXIS Calculation Speedup Specification

## Version 1 Draft Specification

---

## 1. Purpose

This document defines version 1 of the AXIS **calculation speedup**
specification.

The purpose of this specification is to define a lower-risk execution
optimization model for AXIS that improves throughput through:

- explicit execution modes
- explicit trace modes
- explicit parallelization policy
- deterministic parallel execution
- lighter non-replay artifact production

This specification defines:

- the normative execution policy concepts
- the required trace modes
- the supported parallelization modes
- determinism requirements
- persistence expectations by mode
- scope exclusions for the first speedup wave

This specification does not define:

- the concrete worker implementation architecture
- the exact process-pool library choice
- the internal UI or CLI wording
- replay-format redesign beyond the first compact replay-capable mode
- low-level delta-trace encoding details
- binary persistence formats

---

## 2. Scope

This specification applies to:

- experiment execution
- run execution
- episode execution
- execution-time artifact policy
- parallel execution semantics

This specification covers:

- ordinary experiments
- OFAT sweep experiments
- workspace-driven execution insofar as they delegate to the framework

This specification does not yet cover:

- a wholesale redesign of replay trace structure
- restoration of interrupted execution
- compatibility with previously persisted artifact formats

---

## 3. Normative Terms

The terms **must**, **must not**, **should**, and **may** are to be interpreted
normatively.

---

## 4. Core Model

AXIS execution must support an explicit **execution policy**.

An execution policy is the combination of:

- `trace_mode`
- `parallelism_mode`
- `max_workers`

Conceptually:

```text
experiment config
+ execution policy
-> run execution
-> artifact production
```

The execution policy must control:

- what level of trace richness is produced
- whether work is executed sequentially or in parallel
- how many workers may be used

The execution policy must not change:

- the underlying simulation semantics
- the seeded outcome of an episode
- the meaning of the `full` trace mode

---

## 5. Supported Execution Policy Fields

### 5.1 Required Fields

The execution policy model must support at least the following fields:

- `trace_mode`
- `parallelism_mode`
- `max_workers`

### 5.2 Required Values

`trace_mode` must support at least:

- `full`
- `delta`
- `light`

`parallelism_mode` must support at least:

- `sequential`
- `episodes`
- `runs`

`max_workers` must be a positive integer.

### 5.3 Default Values

The default execution policy should be:

- `trace_mode = full`
- `parallelism_mode = sequential`
- `max_workers = 1`

This preserves current behavior unless the caller opts into speed-oriented
execution.

---

## 6. Trace Modes

### 6.1 General Rule

Trace mode must be an explicit first-class execution concept.

AXIS must not treat trace richness as an implicit side effect of unrelated
execution code paths.

### 6.2 `full` Trace Mode

`full` trace mode must preserve the current replay-rich execution semantics.

In `full` mode, the execution result must remain suitable for:

- replay visualization
- current comparison workflows that depend on replay-compatible traces
- detailed post-hoc debugging

In `full` mode, AXIS must produce replay-compatible episode artifacts.

### 6.3 `light` Trace Mode

`light` trace mode must be a first-class, explicitly supported execution mode
for faster non-replay workflows.

In `light` mode, AXIS may omit replay-only information, provided that it still
produces enough information to compute required summaries and execution
outcomes.

`light` mode must not be represented as malformed `full` traces.

`light` mode must instead be modeled as a different output contract.

### 6.4 `delta` Trace Mode

`delta` trace mode must be a first-class, replay-compatible execution mode for
more compact persisted replay artifacts.

In `delta` mode, AXIS may persist initial world state plus per-step deltas
instead of full replay snapshots for every phase, provided that replay-rich
episode traces can be reconstructed for consumers that require the current
replay contract.

`delta` mode must remain suitable for:

- replay visualization
- replay-based comparison
- replay validation

### 6.5 Full-Mode Stability Rule

The introduction of `light` mode must not change the semantic meaning of
`full` mode.

The introduction of `delta` mode must not change the semantic meaning of
either `full` or `light` mode.

### 6.6 Optional Future Modes

Additional trace modes may be introduced later.

Such modes are out of scope for version 1 of this specification.

---

## 7. Light Mode Output Contract

### 7.1 General Rule

`light` mode must preserve execution correctness while reducing artifact
richness and persistence overhead.

### 7.2 Required Episode-Level Information

In `light` mode, AXIS must still produce enough per-episode result information
to support:

- run summary computation
- experiment summary computation
- episode ordering
- seed tracking
- termination interpretation

At minimum, the per-episode output contract must support:

- episode index
- episode seed
- total steps
- final vitality
- termination reason

### 7.3 Replay Exclusion Rule

Artifacts produced in `light` mode must not be advertised as replay-compatible
unless they actually satisfy the replay contract.

### 7.4 Comparison Expectations

`light` mode outputs may be insufficient for full replay-based comparison.

Such outputs must therefore be clearly distinguishable from replay-compatible
outputs.

### 7.5 Summary Integrity

Run summaries and experiment summaries produced from `light` mode must reflect
the same underlying execution outcomes that `full` mode would produce for the
same seeds and configuration.

---

## 8. Parallelization Modes

### 8.1 General Rule

Parallelization must be explicit and policy-controlled.

AXIS must not introduce uncontrolled or implicit nested parallelism.

### 8.2 `sequential`

In `sequential` mode, work must execute in the current serial manner.

This mode is the baseline reference behavior.

### 8.3 `episodes`

In `episodes` mode, the framework may execute episodes of a run in parallel.

This mode must preserve deterministic episode identity and deterministic result
ordering.

### 8.4 `runs`

In `runs` mode, the framework may execute runs of one experiment in parallel.

This mode is especially intended for sweep-like experiments such as OFAT.

### 8.5 One-Axis Rule

For version 1, AXIS must treat parallelization as a single active axis per
execution policy.

That means one execution request must not rely on simultaneous nested
parallelism across both runs and episodes unless a later specification defines
that behavior explicitly.

### 8.6 Worker Bound

`max_workers` must define the maximum concurrency available to the active
parallelization mode.

---

## 9. Determinism Requirements

### 9.1 Outcome Invariance

For a fixed configuration and fixed seeds, AXIS must produce the same
simulation outcomes regardless of:

- sequential execution
- episode-parallel execution
- run-parallel execution

This requirement applies to `full`, `delta`, and `light` trace modes.

### 9.2 Seed Resolution

Episode seeds and run seeds must be fully resolved before dispatch to worker
execution units.

### 9.3 No Order-Dependent Semantics

The result of one episode or run must not depend on the completion order of
other episodes or runs.

### 9.4 Canonical Result Ordering

Aggregated results must be reassembled in canonical deterministic order.

For episodes, the canonical order must be by episode index.

For runs, the canonical order must be by resolved run order.

---

## 10. Worker Isolation Requirements

### 10.1 Isolation Rule

Each parallel execution unit must own its runtime state independently.

This includes:

- system instance
- world instance
- RNG state
- step-local trace accumulation

### 10.2 Shared Mutable State Prohibition

Parallel execution units must not depend on shared mutable runtime state for
simulation correctness.

### 10.3 Cross-Platform Compatibility

The execution model must remain viable under multiprocessing environments that
use process spawning semantics.

Therefore worker execution inputs must be serializable and reconstructible in a
platform-agnostic way.

---

## 11. Persistence Requirements

### 11.1 Mode-Aware Persistence

Persistence behavior must be trace-mode-aware.

### 11.2 `full` Mode Persistence

In `full` mode, AXIS must persist replay-compatible artifacts sufficient for
current visualization and replay-oriented analysis workflows.

### 11.3 `delta` Mode Persistence

In `delta` mode, AXIS must persist replay-capable compact artifacts sufficient
to reconstruct replay-compatible episode traces for current replay consumers.

### 11.4 `light` Mode Persistence

In `light` mode, AXIS must persist only artifacts required by the `light`
contract.

It must not persist replay-looking artifacts that are semantically incomplete.

### 11.5 Required Persisted Outputs in `light`

In `light` mode, persisted outputs must be sufficient to support:

- run summary inspection
- experiment summary inspection
- deterministic episode/run identity tracking

### 11.5 Redundant Artifact Review

The framework should reduce avoidable artifact duplication, especially where
run-level artifacts duplicate information already persisted elsewhere.

This review is allowed in `full`, `delta`, and `light` modes, provided the semantic
requirements of each mode are preserved.

---

## 12. Resume and Interruption

### 12.1 Out-of-Scope Rule

Resume semantics are out of scope for version 1 of this specification.

### 12.2 No Architectural Requirement

The execution model must not be shaped around supporting interruption recovery
or partial resumption.

### 12.3 Allowed Behavior

If an execution is interrupted, it is acceptable for the recommended workflow
to rerun the execution from scratch.

---

## 13. Configuration Integration

### 13.1 Config-Driven Policy

The execution policy should be representable in framework configuration.

### 13.2 CLI Overrides

CLI-level overrides may exist, but configuration should remain the normative
source of execution-policy intent.

### 13.3 Workspace Compatibility

Workspaces that delegate to experiment execution must remain able to pass or
resolve execution-policy values explicitly.

---

## 14. Replay-Compatible Mode Requirements

### 14.1 Replay Contract Preservation

The introduction of execution policy must not break the replay compatibility of
`full` or `delta` mode outputs.

### 14.2 Visualization Expectations

Visualization consumers may continue to assume replay-compatible artifacts when
executions are performed in `full` or `delta` mode.

### 14.3 Comparison Expectations

Existing replay-based comparison consumers may continue to assume replay-rich
artifacts when the source execution was performed in `full` or `delta` mode.

---

## 15. Explicitly Deferred Topics

The following topics are explicitly deferred beyond version 1 of this
specification:

- binary persistence formats
- lower-overhead replacement of the existing replay trace model
- nested parallelism across both runs and episodes simultaneously
- resume semantics

---

## 16. Required First-Wave Capabilities

Version 1 of this specification requires AXIS to support at least:

1. explicit `trace_mode`
2. explicit `parallelism_mode`
3. explicit `max_workers`
4. deterministic episode-parallel execution
5. deterministic run-parallel execution
6. `full` trace mode with replay-compatible persistence
7. `delta` trace mode with replay-compatible compact persistence
8. `light` trace mode with non-replay summary-capable outputs

---

## 17. Recommendation Encoded by This Specification

This specification encodes the following design recommendation:

> AXIS should first pursue throughput gains through explicit mode separation
> and multicore execution, while preserving the current replay-rich model as
> the normative `full` mode

This means the first implementation wave must prioritize:

- policy clarity
- deterministic parallel execution
- lighter non-replay output lanes

and must not prioritize:

- deep replay-format redesign
- resume preservation

---

## 18. Next Document

The next document should define the implementation-facing architecture for this
specification, including:

- worker execution boundaries
- result aggregation model
- proposed runtime types for `light` and `delta` outputs
- persistence module changes
- configuration model changes
- testing and benchmarking expectations

That should become the `engineering-spec.md` stage.
