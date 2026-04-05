# VWP1 – Replay Data Contract Validation and Artifact Access

## Context

We are implementing the **Visualization Layer** for **AXIS System A**.

The AXIS runtime and experimentation framework are already implemented up to **WP17**, including:

* deterministic episode execution
* run and experiment orchestration
* result and trace structures
* passive logging / observability
* repository-based persistence
* fault tolerance and resume
* CLI access to experiments and runs

The Visualization Layer is explicitly defined as a **read-only downstream system** that operates on **persisted structured artifacts** only. It must not simulate, recompute transitions, or bypass the repository. All visualization data access must follow:

```text
Visualization System → Repository → Artifacts
```

Direct file-system access from the visualization layer is strictly forbidden. 

The Visualization Architecture also defines a **Replay Data Contract** as the sole interface between persistence and visualization. This contract is descriptive and artifact-driven: it must be derived from actual persisted results, but validated strictly enough that replay remains deterministic and unambiguous. 

VWP1 must therefore establish the **foundation layer** for the entire visualization system:

* reliable access to persisted experiment/run/episode artifacts
* strict replay-oriented validation
* a clean read-only API for later replay logic

This package must remain below viewer state, replay navigation, and UI rendering.

---

## Objective

Implement **VWP1 – Replay Data Contract Validation and Artifact Access**.

The goal of this package is to provide a correct, explicit, and testable access layer that:

1. loads visualization-relevant artifacts through the existing repository layer
2. validates that episode-level replay data satisfies the minimum replay contract
3. rejects malformed, incomplete, or semantically invalid replay artifacts
4. exposes structured, visualization-ready access to persisted experiment, run, and episode data
5. remains fully read-only and storage-agnostic

This package must provide the minimal but architecturally correct foundation required for later implementation of:

* replay snapshot resolution
* viewer state
* playback/navigation
* rendering and inspection

---

## Core Design Principle

> The Visualization Layer must consume **structured persisted truth**, not raw files and not reconstructed guesses.

Replay correctness must come from:

* repository-backed artifact access
* explicit validation
* deterministic, read-only contracts

Logs are not the source of truth. Structured results are. 

---

## Scope

Implement only the following.

---

### 1. Visualization-Facing Repository Access Layer

Introduce a clearly scoped access layer for visualization that consumes the existing repository abstraction.

This package must not bypass the existing repository model. The visualization architecture is explicit that all artifact access must go through the repository, and that the visualization system must remain agnostic to file layout and serialization details. 

A reasonable design would be one of these:

```python
class ReplayArtifactService:
    def __init__(self, repository: ExperimentRepository) -> None:
        ...
```

or:

```python
class VisualizationArtifactRepository:
    def __init__(self, repository: ExperimentRepository) -> None:
        ...
```

Equivalent naming is acceptable, but the role must be clear:

* consumes existing repository APIs
* exposes visualization-oriented read methods
* performs replay-specific validation
* remains read-only

Important:

* do not introduce raw `Path` handling into visualization code
* do not duplicate repository path logic from WP13
* do not turn this into a general persistence layer
* do not mutate repository artifacts

---

### 2. Artifact Loading Responsibilities

Provide explicit loading support for the artifact hierarchy relevant to visualization:

#### Experiment level

At minimum, support loading:

* experiment configuration
* experiment metadata if present
* experiment summary if present and useful
* experiment-level status if present

#### Run level

At minimum, support loading:

* run configuration
* run metadata if present
* run summary if present
* run result if present

#### Episode level

At minimum, support loading:

* episode result artifacts
* ordered episode references within a run

This aligns with the architecture’s persisted hierarchy:

```text
Experiment
 └── Run
      └── Episode
           └── Steps[]
```

and with the repository layout defined in the experimentation framework.

Important constraints:

* do not load data via raw directory walking outside repository helpers
* do not guess missing artifacts
* fail explicitly if a requested artifact does not exist or fails reconstruction

---

### 3. Replay Contract Validation for Episodes

Implement a strict validation layer for replayable episode artifacts.

The Visualization Architecture defines the episode as the **primary unit of replay** and requires:

* ordered steps
* index-addressable step structure
* phase-aware snapshots
* sufficient state to reconstruct world and agent state for replay

At minimum, validation must check the following.

#### A. Episode-level structural requirements

A replayable episode must contain:

* episode identity
* run identity or equivalent parent linkage
* ordered step sequence

If the persisted runtime structure differs in exact field names, the validator may adapt to the actual model structure, but it must not relax the semantic requirements.

---

#### B. Step-level structural requirements

Each step must be:

* present
* index-addressable
* ordered
* self-contained enough for replay

Minimum conceptual expectation:

```json
{
  "step_index": 0,
  "phases": {
    "before": { ... },
    "after_regen": { ... },
    "after_action": { ... }
  }
}
```

The actual persisted structure may differ, but replay validation must ensure the same semantics are available.

---

#### C. Phase requirements

The replay model assumes phase-aware visualization with at least the semantic phases:

* `BEFORE`
* `AFTER_REGEN`
* `AFTER_ACTION` 

Validation must therefore verify:

* which phases are actually present per step
* whether the required baseline phases exist consistently enough for replay
* whether phase access is unambiguous

Important:

* do not invent missing phases
* do not recompute missing phase states from neighboring steps
* do not silently degrade to a weaker replay model in this package

If the current persisted runtime artifacts do not yet contain all required replay phases explicitly, this package must surface that fact clearly rather than hiding it.

That is important because VWP1 is supposed to expose the **true state of replay readiness**, not mask gaps.

---

#### D. Minimal state requirements per replayable snapshot

For the visualization to function, the episode data must expose, either directly or through clearly structured nested fields:

* world state sufficient for grid reconstruction
* agent position
* agent energy

The architecture also allows additional internal variables and trace data, but those are optional at this stage. The minimum required fields are world state plus agent state with position and energy.

Validation must fail explicitly if these minimum requirements are not met.

---

### 4. Step Ordering and Replay Consistency Validation

Implement semantic validation for replay ordering.

The Visualization Architecture explicitly requires:

* strict monotonic ordering by step index
* no duplicates
* no gaps
* consistent dimensions across replay states 

At minimum, validate:

* step indices are strictly increasing
* no duplicate indices exist
* step sequence is contiguous, unless the actual persisted runtime contract deliberately defines a different stable rule
* grid dimensions remain consistent across replayable snapshots
* phase access is coherent for each valid step

Important:

* reject invalid ordering
* reject structurally inconsistent episodes
* do not silently sort and continue if persisted structure is wrong
* do not “repair” malformed replay sequences

This package must prefer explicit failure over permissive convenience.

---

### 5. Forward-Compatible Validation Philosophy

The replay contract is descriptive and artifact-aligned. It must tolerate **forward-compatible extensions** while remaining strict about required semantics.

Therefore the validator must:

* ignore unknown extra fields
* accept richer trace payloads
* avoid hard-coding assumptions beyond the required replay contract
* fail only when required replay semantics are missing, ambiguous, or invalid

This is important because the execution system may later persist additional diagnostic fields that the visualization should not reject unnecessarily.

---

### 6. Read-Only Visualization Data Models

Introduce minimal, explicit data models for validated visualization inputs.

These models should be visualization-facing, not raw persistence objects. Their goal is to provide a stable access boundary for later VWPs.

A reasonable baseline might include types such as:

* `ReplayExperimentHandle`
* `ReplayRunHandle`
* `ReplayEpisode`
* `ReplayStepDescriptor`
* `ReplayValidationResult`

Equivalent naming is acceptable.

Important:

* keep these models small
* keep them read-only
* do not turn them into UI state objects
* do not embed rendering concerns
* do not duplicate the entire persistence schema if not needed

The point is to expose:

* validated identity
* replayable step structure
* phase availability
* access to underlying structured data

without forcing later components to depend directly on raw repository models.

---

### 7. Failure Model

This package must fail explicitly and clearly.

The visualization architecture requires explicit failure for:

* malformed artifacts
* missing required replay data
* inconsistent step ordering
* ambiguous phase/state structure

Introduce clear exception types or equivalent explicit error signaling for cases such as:

* experiment not found
* run not found
* episode not found
* malformed replay artifact
* replay contract violation
* unsupported replay shape

Important:

* do not swallow repository errors
* do not add direct file-based fallback logic
* do not downgrade invalid replay artifacts into “best effort” replayability

---

### 8. Discovery Support for Visualization Entry Points

Provide explicit discovery helpers needed by later visualization entry points.

At minimum, support:

* list available experiment IDs
* list run IDs for a given experiment
* list replayable episodes for a given run
* inspect whether an episode is replay-valid

These helpers should build on the existing repository discovery capabilities introduced in WP13, not replace them.

Important:

* keep discovery deterministic
* return stable ordering
* separate “artifact exists” from “artifact is replay-valid”

That distinction matters. A persisted episode may exist but still fail replay validation.

---

## Out of Scope

Do **not** implement any of the following in VWP1:

* replay snapshot resolution
* `(step_index, phase) -> snapshot` mapping
* viewer state
* playback controls
* PySide6 UI
* rendering
* selection logic
* dashboard logic
* detail views
* debug overlays
* CLI visualization command
* artifact mutation
* repository path logic reimplementation
* direct file parsing outside repository
* inferred reconstruction of missing phase data
* heuristic recovery of malformed episodes

Do not let VWP1 drift into replay logic or UI logic.

---

## Architectural Constraints

The implementation must follow these rules.

---

### 1. Repository boundary is mandatory

All visualization data access must go through the existing repository abstraction. Direct file access is forbidden. 

---

### 2. Visualization remains storage-agnostic

This package must not assume:

* raw directory layout
* raw JSON structure beyond repository-reconstructed models
* local filesystem as the only future backend

That is the whole point of the repository boundary. 

---

### 3. Validation is strict

If replay requirements are not met, fail explicitly.

Do not:

* fill missing fields with defaults
* infer hidden state
* rebuild missing phases
* repair gaps silently

The architecture explicitly prefers strict validation over silent assumption.

---

### 4. Read-only only

This package must never:

* modify persisted artifacts
* write derived replay files
* update metadata/status
* trigger execution

It is a consumer of persisted truth only.

---

### 5. No duplication of repository logic

Do not duplicate:

* path resolution
* JSON parsing
* listing semantics
* reconstruction logic already provided by WP13

This package may wrap and validate repository outputs, but it must not become a second repository subsystem.

---

## Expected File Structure

A reasonable baseline extension could look like this:

```text
src/axis_system_a/
    visualization/
        __init__.py
        replay_access.py
        replay_models.py
        replay_validation.py
        errors.py
```

If you prefer fewer files, that is acceptable as long as the concerns remain separated:

* repository-backed access
* replay validation
* lightweight replay-facing models
* explicit error types

Do not fragment excessively.

---

## Testing Requirements

Also create pytest tests for VWP1.

At minimum include the following.

---

### A. Artifact access tests

Validate:

* experiment can be loaded through repository-backed visualization access
* run can be loaded through repository-backed visualization access
* episode can be loaded through repository-backed visualization access
* missing experiment/run/episode fails explicitly

Use temporary repositories and small handcrafted persisted artifacts.

---

### B. Discovery tests

Validate:

* experiment listing is stable
* run listing is stable
* episode listing is stable
* replayable vs. non-replayable episodes can be distinguished explicitly

---

### C. Structural replay validation tests

Validate success cases for episodes that contain:

* ordered steps
* valid step indices
* required phase structure
* world state
* agent position
* agent energy

---

### D. Failure validation tests

Validate explicit failure for:

* missing steps
* duplicate step indices
* non-monotonic step ordering
* missing required phase data
* missing world state
* missing agent position
* missing agent energy
* inconsistent grid dimensions across steps/phases
* malformed persisted content reconstructed from repository

---

### E. Forward-compatibility tests

Validate that:

* unknown extra fields do not break replay validation
* richer trace data is tolerated as long as required replay semantics remain intact

---

### F. Repository-boundary tests

Validate that visualization access is built on repository methods and does not rely on direct file parsing inside the visualization layer.

This does not need to become an over-engineered mock-heavy test suite, but the architectural boundary should be visible and test-proven.

---

## Implementation Style

* Python 3.11
* explicit typing
* strict validation
* no hidden magic
* no best-effort fallback behavior
* small, readable models
* explicit exceptions
* deterministic ordering
* repository-first access

Be skeptical of convenience shortcuts here. This package defines the trust boundary for the rest of the visualization system.

---

## Expected Deliverable

1. repository-backed visualization access layer
2. replay-oriented artifact loading for experiment/run/episode hierarchy
3. strict replay contract validation for episodes
4. read-only replay-facing data models
5. explicit failure model for malformed or incomplete replay artifacts
6. deterministic discovery helpers
7. pytest coverage for access, validation, failure cases, and forward-compatible extras

---

## Important Final Constraint

VWP1 must feel like:

> a **read-only replay contract gateway**, not a UI package and not a second repository implementation.

If you want, I’ll do **VWP2** next in the same style.
