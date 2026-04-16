# Paired Trace Comparison -- Engineering Specification

## Replay-Based Comparison Analysis on the AXIS Trace Layer

**Status:** Draft  
**Based on:** `paired-trace-comparison-spec.md`  
**Target version:** v0.4.0  
**Date:** 2026-04-16

---

## 1. Purpose

This document specifies the first engineering-oriented implementation plan for the AXIS paired trace comparison concept.

Its purpose is to translate the paired trace comparison specification into a concrete implementation shape that can later be developed incrementally.

The paired trace comparison feature is intended to:

- compare two AXIS episode traces under strict paired conditions
- compute generic comparison metrics
- support system-specific comparison extensions
- provide a stable basis for later tooling, reporting, and visualization

This document is not yet a low-level implementation blueprint.

It defines:

- scope
- proposed package placement
- conceptual component map
- validation and metric responsibilities
- extension responsibilities
- testing scope
- CLI integration role

---

## 2. Scope

### In scope

- a comparison-layer implementation above replay traces
- strict paired validation
- shared-prefix alignment
- generic metric computation
- action-space intersection handling
- support for optional system-specific comparison extensions
- CLI-triggered comparison execution through the `axis` tool
- tests for pairing, alignment, metric computation, and failure modes

### Out of scope

- new trace persistence formats
- framework execution changes
- SDK replay contract changes
- dedicated comparison UI beyond existing CLI-triggered workflows
- statistical aggregation across many episode pairs
- extension registration mechanics beyond a minimal internal attachment point

---

## 3. Architectural Position

Paired trace comparison should not be implemented inside the SDK contract layer.

It should also not be built into the core execution loop of the framework.

The correct placement is:

- above replay traces
- below future reporting and visualization
- beside persistence and replay access

Conceptually:

```text
SDK defines episode traces.
Framework produces episode traces.
Comparison tooling reads episode traces and computes comparison artifacts.
The axis CLI triggers comparison workflows.
Visualization and reporting may later consume comparison artifacts.
```

This keeps the comparison feature aligned with the specification:

- trace production remains generic
- comparison remains analysis-layer logic
- system-specific semantics stay outside the generic replay core
- user-facing execution is routed through the existing `axis` tool boundary

---

## 4. Proposed Package Placement

The initial implementation should live in a new framework-side analysis package.

Recommended location:

- `src/axis/framework/comparison/`

Suggested initial modules:

| File | Purpose |
|---|---|
| `types.py` | Comparison result models, validation result models, metric payload models |
| `validation.py` | Strict pair validation logic |
| `alignment.py` | Shared-prefix alignment helpers |
| `metrics.py` | Generic metric computation |
| `actions.py` | Action-space intersection and usage helpers |
| `extensions.py` | Minimal extension dispatch for system-specific comparison blocks |
| `compare.py` | Main high-level comparison entry point |
| `cli.py` | CLI-facing comparison command helpers |
| `__init__.py` | Public exports |

This is a comparison package, not a general-purpose analytics framework.

It should remain tightly scoped to paired replay comparison.

---

## 5. Component Map

This table maps major specification concepts to engineering artifacts.

| Spec concept | Engineering role | Proposed location |
|---|---|---|
| paired comparison result | frozen result model(s) | `comparison/types.py` |
| strict pair validation | pure validation functions | `comparison/validation.py` |
| pairing identity resolution | helpers for episode seed / derived identity | `comparison/validation.py` |
| shared-prefix alignment | pure alignment helpers | `comparison/alignment.py` |
| action-label intersection | action-space helpers | `comparison/actions.py` |
| generic metrics | pure metric functions | `comparison/metrics.py` |
| system-specific analysis blocks | extension dispatch surface | `comparison/extensions.py` |
| top-level compare operation | orchestration entry point | `comparison/compare.py` |

The overall implementation should stay function-oriented where possible.

Stateful service objects are not necessary for v1.

---

## 5.1 CLI Integration

Paired trace comparison should be invokable through the existing `axis` command-line tool.

This follows the established AXIS interaction model:

- experiments are started through `axis`
- replay and visualization are launched through `axis`
- comparison should also be started through `axis`

The CLI is therefore the intended operational entry point for users, while the comparison package remains the implementation layer behind that command.

Conceptually:

```text
axis CLI command
-> comparison command handler
-> compare_episode_traces(...)
-> structured comparison result
```

The CLI layer should not contain comparison logic itself.

It should:

- resolve user inputs
- load required traces and metadata
- call the comparison package
- render or persist the comparison result

---

## 6. Public Entry Point

The comparison feature should expose one primary entry point.

Suggested shape:

```python
def compare_episode_traces(
    reference_trace: BaseEpisodeTrace,
    candidate_trace: BaseEpisodeTrace,
    *,
    reference_run_metadata: RunMetadata | None = None,
    candidate_run_metadata: RunMetadata | None = None,
    reference_run_config: RunConfig | None = None,
    candidate_run_config: RunConfig | None = None,
) -> PairedTraceComparisonResult:
    ...
```

This top-level function should:

1. validate the pair
2. resolve pairing identity
3. compute shared action labels
4. compute alignment facts
5. compute generic metrics
6. attach optional system-specific extensions
7. return a fully structured result object

If validation fails, it must still return a structured result object, but in failed-validation mode.

---

## 6.1 CLI Entry Shape

The exact command syntax does not need to be fully specified in this draft, but the engineering implementation should assume a dedicated `axis` CLI entry path for paired comparison.

Examples of the intended role:

- compare two explicit episode trace files
- compare two persisted episodes by experiment/run/episode identity
- later compare matched episode sets across runs

The first implementation should focus on the simplest useful mode:

- explicit reference episode
- explicit candidate episode

with optional metadata resolution through run config and run metadata.

---

## 7. Result Models

The engineering implementation should use explicit frozen result models rather than raw dictionaries.

Recommended high-level models:

- `PairedTraceComparisonResult`
- `PairValidationResult`
- `AlignmentSummary`
- `GenericComparisonMetrics`
- `OutcomeComparison`

Optional supporting models:

- `ActionDivergenceMetrics`
- `PositionDivergenceMetrics`
- `VitalityDivergenceMetrics`
- `ActionUsageMetrics`

The result models should preserve the structure from the specification:

- identity
- validation
- alignment
- generic metrics
- outcome
- system-specific analysis

Using typed models here is useful because:

- the result object is likely to become persisted or passed across tools
- validation and ambiguity states need explicit structure
- later visualization/reporting should consume a stable schema

---

## 8. Validation Responsibilities

Validation must be implemented as a separate stage, not mixed ad hoc into metric computation.

### 8.1 Validation Must Check

- replay-contract compatibility of both episode traces
- world type equality
- world config equality
- start position equality
- pairing identity equality
- nonempty shared action-label intersection

### 8.2 Validation Must Support

- explicit episode seed identity
- derived seed identity through episode index and base seed

### 8.3 Validation Output

Validation should return a structured `PairValidationResult` with:

- boolean validity
- explicit error codes
- match booleans for each required condition
- resolved pairing mode

Metric computation must not proceed as if the pair were valid when validation fails.

---

## 9. Alignment Responsibilities

Alignment logic should be isolated in a dedicated helper module.

The alignment layer should compute:

- `reference_total_steps`
- `candidate_total_steps`
- `aligned_steps`
- `reference_extra_steps`
- `candidate_extra_steps`

It should also expose aligned step iterators or aligned index ranges for use by metric functions.

The alignment layer must never pad traces.

---

## 10. Generic Metric Responsibilities

Generic metric computation should be pure and decomposed by metric family.

### 10.1 Required Metric Families

The engineering implementation must support:

- action divergence metrics
- position divergence metrics
- vitality divergence metrics
- action usage statistics
- outcome comparison

### 10.2 Time Series

The implementation must preserve required series as first-class outputs:

- `trajectory_distance_series`
- `vitality_difference_series`

Optional later series can be added without redesigning the generic structure.

### 10.3 Tolerances

Metric functions must use centralized tolerance parameters rather than hardcoded local tolerances.

This suggests a small shared tolerance definition in:

- `comparison/types.py`
- or `comparison/metrics.py`

with values:

- `epsilon = 1e-9`
- `ranking_epsilon = 1e-6`

---

## 11. Action-Space Handling

The implementation must explicitly support non-identical action spaces.

### 11.1 Required Behavior

The comparison layer must:

- compute the shared action-label intersection
- fail validation if the intersection is empty
- compute paired action deltas only on shared labels
- retain per-system action usage counts even for non-shared actions

### 11.2 Engineering Consequence

The implementation should distinguish between:

- full per-system action vocabularies
- shared comparison action vocabulary

This logic belongs in:

- `comparison/actions.py`

---

## 12. Ambiguity Handling

The engineering implementation must preserve explicit ambiguity states.

It must not silently coerce:

- near-ties
- unavailable metrics
- missing required signals

to simple booleans or zeros.

Recommended approach:

- use typed string literals or enums for:
  - `ambiguous_due_to_tie`
  - `not_applicable`
  - `missing_required_signal`

This is especially important for:

- most-used-action metrics
- top-action-changed-by-modulation metrics

---

## 13. System-Specific Extension Layer

The comparison core must support optional system-specific analysis blocks.

### 13.1 Initial Requirement

Version 1 does not require a full plugin registry.

It only requires a minimal internal dispatch mechanism that can attach extension blocks when relevant.

It also does not require a comparison-specific UI.

The expected user entry path is the `axis` CLI.

### 13.2 Proposed Responsibility Split

- generic comparison computes shared metrics
- extension layer checks system type(s)
- extension layer computes additional structured blocks when supported

### 13.3 Initial Extension Target

The first extension target should be:

- `system_c_prediction`

This block should compute the `System C` metrics defined in the paired comparison spec:

- `prediction_active_step_count`
- `prediction_active_step_rate`
- `top_action_changed_by_modulation_count`
- `top_action_changed_by_modulation_rate`
- `mean_modulation_delta`

The initial extension mechanism can remain internal and simple.

The registration architecture can be deferred.

---

## 14. Dependency Constraints

The comparison package should depend on:

- `axis.sdk.trace`
- run metadata and run config types where needed
- pure standard-library helpers
- local comparison modules

It should not depend on:

- execution loop internals
- world mutation logic
- concrete system implementations

System-specific extensions may read system-specific `decision_data` and `trace_data`, but they should do so through comparison-side interpreters, not by importing system runtime classes.

---

## 15. Test Strategy

The implementation should be test-driven with a strong focus on pure comparison behavior.

### 15.1 Core Test Categories

- validation success and failure
- seed identity resolution
- shared-prefix alignment
- action-space intersection behavior
- generic metric correctness
- ambiguity-state correctness
- system-specific extension correctness
- CLI-level comparison invocation

### 15.2 Recommended Test Sources

Tests should use:

- synthetic minimal episode traces for deterministic edge cases
- existing persisted AXIS traces where useful
- system-specific fixture traces for extension logic
- CLI-facing integration tests for loading and dispatch

### 15.3 Priority

Priority should go first to:

- validation correctness
- alignment correctness
- series correctness
- top-level comparison result shape

before building richer extension logic.

---

## 16. Suggested Output Stability Level

The comparison result should be treated as a stable internal analysis schema from the first implementation onward.

This does not require public API guarantees yet, but it does require:

- consistent field naming
- explicit ambiguity handling
- versionable result structure

That will make future reporting and visualization easier to build on top.

---

## 17. Implementation Sequence

The recommended implementation sequence is:

1. typed result models
2. strict validation
3. alignment helpers
4. generic metrics
5. top-level comparison entry point
6. CLI command integration
7. `System C` extension
8. broader fixtures and persisted-trace validation

This keeps the implementation risk low and preserves a usable partial result at each stage.

---

## 18. Acceptance Criteria

The first implementation should be considered successful if it satisfies all of the following:

- it can compare two valid paired episode traces and produce a structured result
- it rejects invalid pairs with explicit validation errors
- it computes all required generic metric families from the spec
- it handles non-identical action spaces through shared-label comparison
- it preserves required time series in simple array form
- it can be triggered through the `axis` CLI
- it exposes explicit ambiguity states where required
- it can attach a first `System C` comparison extension

---

## 19. Summary

The paired trace comparison engineering work should be implemented as a small, focused comparison package above AXIS replay traces.

Its structure should reflect the specification:

- strict validation first
- shared-prefix alignment
- pure metric computation
- typed result models
- explicit extension blocks

This provides a clean bridge from the paired comparison spec to later implementation and tooling.
