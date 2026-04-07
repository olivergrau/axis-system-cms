# AXIS System A

## Experimentation Framework – Work Package Delivery Plan (WP11–WP17)

## 1. Purpose

This document defines the **implementation delivery plan** for the **Experimentation Framework** that extends the already completed AXIS System A core runtime.

The core system up to **WP10** is assumed to be available and stable, including:

* episode execution
* policy and transition logic
* structured episode-level results
* passive logging and observability
* tests and fixtures

The Experimentation Framework introduces a higher orchestration layer that enables:

* multi-episode execution under one configuration (**Run**)
* collections of runs for comparative studies (**Experiment**)
* deterministic configuration expansion
* file-system-based persistence
* resumable execution
* CLI-based control

The framework must remain strictly layered above the runtime and must not introduce back-dependencies into the existing simulation engine. 

---

## 2. Delivery Strategy

The implementation is split into **seven work packages**:

* **WP11**: Configuration Models and Resolution
* **WP12**: Run and Experiment Result / Summary Model
* **WP13**: Persistence Layer and Repository Model
* **WP14**: RunExecutor
* **WP15**: ExperimentExecutor
* **WP16**: Fault Tolerance and Resume
* **WP17**: CLI Interface and End-to-End Integration Tests

This order is intentional.

The packages are arranged so that:

1. foundational data contracts come first,
2. orchestration comes only after inputs and outputs are defined,
3. fault tolerance is added after the happy path is stable,
4. the CLI is implemented last as a thin wrapper over the completed framework.

This matches the architectural principles of explicit layering, deterministic execution, immutable artifacts, and minimal interfaces. 

---

## 3. Work Package Overview

---

## WP11 – Configuration Models and Resolution

### Objective

Implement the configuration layer for the Experimentation Framework.

This package defines how experiments and runs are specified, validated, expanded, and resolved before execution begins.

### Scope

WP11 should introduce:

* `ExperimentConfig`
* `RunConfig`
* canonical experiment types:

  * `single_run`
  * `ofat`
* path-based parameter addressing
* configuration validation
* deterministic expansion from experiment-level definitions into fully materialized run-level configurations
* seed strategy definition and seed resolution rules

### Why this comes first

The architecture requires that all parameter variation is resolved **before execution**, and that each run owns a fully resolved configuration snapshot. Without this foundation, later execution packages would be forced to invent their own ad hoc config handling. 

### Deliverable

A stable, validated, and testable configuration subsystem that can transform one experiment definition into one or more concrete run configurations.

---

## WP12 – Run and Experiment Result / Summary Model

### Objective

Implement the result structures and aggregation contracts required above episode level.

This package defines how episode-level outputs are aggregated into run-level and experiment-level artifacts.

### Scope

WP12 should introduce:

* `RunSummary`
* `RunResult`
* `ExperimentSummary`
* `ExperimentResult`
* deterministic aggregation functions from:

  * `EpisodeResult[] -> RunSummary`
  * `RunResult[] -> ExperimentSummary`
* baseline metrics and summary fields already specified in the architecture
* serializable snapshot-friendly structures without live runtime references

### Why this comes before execution

Executors should write into already defined target contracts. This reduces ambiguity and prevents the orchestration layer from inventing result schemas while being implemented.

### Deliverable

A complete and testable result model for runs and experiments, including summary generation and serialization-ready structures.

---

## WP13 – Persistence Layer and Repository Model

### Objective

Implement the file-system-based persistence layer used by the Experimentation Framework.

This package defines how experiment and run artifacts are stored, loaded, and organized.

### Scope

WP13 should introduce:

* repository root handling
* experiment directory resolution
* run directory resolution
* file naming and path helpers
* read/write support for the persisted artifacts defined by the architecture, including:

  * experiment config
  * experiment metadata
  * experiment status
  * experiment summary
  * run config
  * run metadata
  * run status
  * run summary
  * run result
  * episode result files
* serialization and deserialization helpers
* explicit handling of immutable persisted artifacts

### Why this is a separate package

Persistence is a major concern in the framework and directly underpins reproducibility, inspectability, and resume semantics. It should be implemented as its own stable layer before orchestration logic is added. The architecture already defines a concrete file-system strategy and directory structure that this package should realize faithfully. 

### Deliverable

A repository-style persistence subsystem that provides deterministic artifact storage and retrieval for experiments and runs.

---

## WP14 – RunExecutor

### Objective

Implement the first orchestration layer above the existing runtime.

The `RunExecutor` is responsible for executing multiple episodes under one fixed run configuration and aggregating the resulting outputs.

### Scope

WP14 should introduce:

* `RunExecutor`
* episode seed handling within a run
* repeated invocation of the existing `EpisodeRunner`
* collection of `EpisodeResult` objects
* incremental persistence of episode results
* construction of `RunSummary`
* construction of `RunResult`
* run lifecycle/status handling:

  * `PENDING`
  * `RUNNING`
  * `COMPLETED`
  * `FAILED`

### Architectural role

The `RunExecutor` is the minimal statistical execution unit of the framework. It must execute multiple episodes under identical configuration and aggregate them into a run-level artifact. The architecture is explicit that runs are the primary unit for statistical comparison. 

### Deliverable

A deterministic, testable run orchestration component that produces persisted run outputs from repeated episode execution.

---

## WP15 – ExperimentExecutor

### Objective

Implement the top-level orchestration layer for complete experiments.

The `ExperimentExecutor` coordinates multiple runs, based on a validated experiment definition and the resolved run configurations produced from it.

### Scope

WP15 should introduce:

* `ExperimentExecutor`
* expansion of one `ExperimentConfig` into multiple `RunConfig` objects
* stable run identification
* sequential execution of runs
* persistence of experiment-level metadata and status
* collection of run references and/or run results
* construction of `ExperimentSummary`
* construction of `ExperimentResult`
* experiment lifecycle/status handling:

  * `CREATED`
  * `RUNNING`
  * `COMPLETED`
  * `FAILED`
  * `PARTIAL`

### Architectural role

The `ExperimentExecutor` sits above the `RunExecutor` and is responsible for controlled comparative studies, not for episode execution itself. The execution hierarchy must remain:

```text
ExperimentExecutor
    └── RunExecutor
            └── EpisodeRunner
```

This exact layering is a hard architectural constraint. 

### Deliverable

A sequential, deterministic experiment orchestration component that can execute one complete experiment definition into persisted experiment artifacts.

---

## WP16 – Fault Tolerance and Resume

### Objective

Implement the resume and recovery behavior of the Experimentation Framework.

This package adds robust handling for interrupted, partial, and already-completed work without changing the core execution logic.

### Scope

WP16 should introduce:

* status-driven resume logic
* run-level resume semantics
* completed-run detection
* skipping of already completed runs
* handling of incomplete and failed runs
* idempotent resume behavior
* safe interaction with persisted artifacts and statuses
* preservation of already completed work

### Why this is separate

The architecture explicitly requires incremental persistence and resumable execution, but resume logic is a complexity multiplier and should not be mixed into the first implementation of the normal execution path. It is safer and cleaner to implement it after `RunExecutor` and `ExperimentExecutor` already exist in a stable form. The baseline resume boundary is the **run**, not the episode. 

### Deliverable

A robust fault-tolerance layer that allows interrupted experiments to continue safely without recomputing already completed runs.

---

## WP17 – CLI Interface and End-to-End Integration Tests

### Objective

Implement the thin CLI layer and the final end-to-end integration tests for the complete Experimentation Framework.

### Scope

WP17 should introduce:

* CLI commands reflecting the actual framework entities, for example:

  * `experiments run`
  * `experiments resume`
  * `experiments list`
  * `experiments show`
  * `runs list`
  * `runs show`
* argument parsing and config loading
* invocation of existing executors only
* no business logic inside the CLI layer
* end-to-end integration tests that validate:

  * configuration resolution
  * run execution
  * experiment execution
  * persistence
  * resume behavior
  * CLI behavior

### Architectural role

The CLI must remain a **thin wrapper** around the framework, not an alternative execution implementation. It exists to expose the framework in a usable and inspectable way, while reusing the already implemented orchestration and persistence layers. 

### Deliverable

A minimal but functional command-line interface plus integration tests proving that the framework works end to end.

---

## 4. Dependency Chain

The packages should be implemented in the following order:

```text
WP11 → WP12 → WP13 → WP14 → WP15 → WP16 → WP17
```

### Dependency rationale

* **WP11** must come first because execution depends on fully resolved configs.
* **WP12** must come before executors so orchestration writes into stable result contracts.
* **WP13** must come before higher orchestration so persistence semantics are not improvised.
* **WP14** depends on configs, results, and persistence.
* **WP15** depends on run execution being stable.
* **WP16** depends on persisted artifacts and status models already existing.
* **WP17** depends on the full framework being in place and should remain a final presentation layer.

---

## 5. Design Philosophy for Claude Code Agents

These work packages are deliberately cut so that Claude Code agents can implement them cleanly and with minimal ambiguity.

Each package should:

* introduce a small number of new concepts
* have clear boundaries
* have explicit inputs and outputs
* be independently testable
* leave the codebase in a stable intermediate state

The packages are intentionally **not** overly broad. In particular:

* persistence is not mixed with initial executor design
* fault tolerance is not mixed with the first implementation of the happy path
* the CLI is not introduced before the underlying framework is complete

This reduces the risk of architectural drift, speculative abstractions, and hidden coupling.

---

## 6. Final Implementation Intent

Once WP11–WP17 are complete, the Experimentation Framework should provide:

* deterministic experiment definition and config expansion
* run-level statistical execution
* experiment-level orchestration
* persistent reproducible artifacts on disk
* resumable execution after interruption
* a minimal CLI for running and inspecting experiments

At that point, AXIS System A will have evolved from a single-episode simulation runtime into a structured and reproducible experimental platform. 