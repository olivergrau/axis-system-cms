# AXIS Enhanced Metrics Specification

## Version 1 Draft Specification

---

## 1. Purpose

This document defines version 1 of the AXIS **enhanced behavioral metrics**
specification.

The purpose of this specification is to define a first framework-level metric
layer that extends AXIS evaluation beyond survival-only summaries.

This specification defines:

- the scope of first-wave enhanced behavioral metrics
- the trace-mode compatibility rules
- the distinction between baseline summaries and behavioral metrics
- the extension model for system-specific metrics
- the required first-wave metric set
- the boundary between framework-wide and later metrics

This specification does not define:

- all possible future behavior metrics
- a formal context-similarity model
- dynamic world-change semantics for adaptation metrics
- the exact decorator, registry, or catalog API surface
- final CLI/UI wording

---

## 2. Scope

This specification applies to:

- episode-trace-based behavioral analysis
- run-level aggregation of behavioral metrics
- persisted behavioral metric artifacts
- framework-supported behavioral metrics for replay-capable runs

This specification covers:

- `system_a`
- `system_c`
- later extension paths such as `system_aw` and `system_cw`, insofar as they
  expose compatible trace information

This specification does not yet cover:

- context-sensitive metrics that require a formal similarity definition
- environment-change-aware recovery metrics
- light-trace execution outputs

---

## 3. Normative Terms

The terms **must**, **must not**, **should**, and **may** are to be interpreted
normatively.

---

## 4. Core Design Rule

AXIS must treat enhanced behavioral metrics as a distinct analysis layer.

Enhanced behavioral metrics must not be assumed to be identical to:

- the minimal built-in `RunSummary`
- paired trace divergence metrics
- or system-specific visualization-only information

AXIS must also treat behavioral metrics as an extension-capable subsystem.

That means the metrics layer must support:

- framework-provided standard metrics
- optional system-specific metric extensions

The enhanced metrics layer must answer questions such as:

- how efficiently does a system behave?
- how structured is its behavior?
- how much exploratory coverage does it achieve?
- how strongly does prediction influence behavior?

This layer must remain mechanistic and trace-derived.

It must not rely on:

- inferred intention
- hidden cognition
- unformalized notions of understanding

---

## 5. Extension Model

### 5.1 General Rule

AXIS enhanced metrics must support an extension model analogous in role to:

- visualization adapters
- comparison extensions

The framework must provide the generic orchestration, while systems may provide
additional domain-specific metrics.

### 5.2 Framework Responsibilities

The framework must own:

- metric execution lifecycle
- trace loading / trace reconstruction
- standard metric computation
- aggregation and persistence of metric artifacts
- CLI and workspace display of metric results

The framework should remain responsible for all generic metrics that are meant
to be comparable across systems.

### 5.3 System Responsibilities

Systems may provide system-specific metric extensions when they expose
mechanistically meaningful internal trace data that the generic framework does
not understand.

Examples include:

- prediction-specific metrics for `system_c`
- later novelty or world-model metrics for `system_aw`
- future hybrid metrics for `system_cw`

System-specific metrics should be implemented in system-local modules and
registered through an extension mechanism rather than hard-coded into the
framework core.

### 5.4 SDK / Framework Boundary

AXIS must define a stable extension contract for system-specific metric
extensions.

That contract must allow the framework to:

- discover whether an extension exists for a system type
- call the extension with replay-capable episode traces or equivalent
  run-analysis inputs
- receive structured metric output
- merge that output into the persisted behavioral metric artifact

The exact callable signature is out of scope for this specification, but the
extension contract must be explicit and documented.

---

## 6. Trace-Mode Compatibility

### 5.1 Supported Trace Modes

Enhanced behavioral metrics in version 1 must be defined only for replay-capable
trace modes.

The supported trace modes are:

- `full`
- `delta`

### 5.2 Unsupported Trace Modes

Enhanced behavioral metrics in version 1 must not be defined for:

- `light`

`light` is explicitly out of scope for this specification.

### 5.3 Delta Compatibility Rule

`delta` runs must be treated as valid inputs for enhanced metrics whenever AXIS
can reconstruct replay-rich episode traces from persisted delta artifacts.

Version 1 metric computation may therefore operate on:

- native full traces
- reconstructed traces from delta artifacts

without changing the semantic interpretation of the metrics.

---

## 7. Artifact Model

### 6.1 General Rule

AXIS must persist enhanced behavioral metrics as a distinct artifact rather
than overloading the existing minimal `RunSummary` by default.

### 6.2 Run Summary Preservation

The existing minimal run summary contract should remain intact in version 1.

That summary may continue to report:

- mean steps
- step variance
- mean final vitality
- vitality variance
- death rate

Enhanced behavioral metrics must therefore be modeled as:

- a separate persisted run-level artifact
- or a clearly separate typed payload within the analysis layer

That artifact must support both:

- framework-standard metrics
- system-specific extension metrics

### 6.3 Aggregation Unit

Version 1 enhanced metrics must aggregate over a run.

That means the framework must compute metrics:

- from episode traces
- then aggregate them across all episodes in the run

Experiment-level aggregation may be added later, but it is not required by
this version of the specification.

---

## 8. Required First-Wave Metric Categories

Version 1 must support a compact first-wave metric set.

These metrics must be directly derivable from current replay-capable traces
without requiring new ambiguous semantics.

The first-wave metric model must distinguish between:

- standard metrics
- system-specific extension metrics

### 8.1 Standard Metric Set

The framework must provide the following standard metrics directly.

#### Survival Baseline Metrics

The behavioral metric layer may repeat baseline survival metrics for analysis
completeness.

The supported baseline metrics are:

- mean steps survived
- death rate
- mean final vitality

#### Resource Efficiency Metrics

The framework must support:

- resource gain per step
- net energy efficiency
- successful consume rate
- consume-on-empty rate

#### Behavioral Structure Metrics

The framework must support:

- action entropy
- policy sharpness
- action inertia

#### Failure Avoidance Metrics

The framework must support:

- failed movement rate

Version 1 must not require context-sensitive failure metrics such as repeated
failed-action-in-similar-context metrics.

#### Exploration Metrics

The framework must support:

- unique cells visited
- coverage efficiency
- revisit rate

### 8.2 System-Specific Extension Metrics

Version 1 must allow systems to contribute additional metrics through the
metrics extension mechanism.

For systems that emit the required predictive trace fields, AXIS should support
prediction-specific metrics through a system extension rather than requiring
the framework core to hard-code all predictive logic.

For `system_c`, the initial extension-target metrics are:

- mean prediction error
- signed prediction error
- confidence trace mean
- frustration trace mean
- prediction modulation strength

For systems that do not expose the required trace data, such metrics must be:

- absent
- or explicitly marked as not applicable

They must not be fabricated as zero-valued placeholders unless that behavior is
explicitly standardized later.

---

## 9. Metrics Out of Scope for Version 1

The following metrics are explicitly out of scope for version 1.

### 8.1 Context-Sensitive Metrics

These metrics are out of scope until AXIS defines formal context identity or
context similarity semantics:

- local action consistency
- repeated failed action rate in similar context
- post-failure adaptation
- contextual inertia

### 8.2 Environment-Change Metrics

These metrics are out of scope until AXIS defines explicit environment-change
semantics or world-specific analysis layers:

- recovery after change
- regeneration-aware adaptation timing
- stale-bias persistence after outcome reversal

### 8.3 World- or Study-Specific Interpretation Metrics

Metrics whose meaning depends strongly on one world family, one experimental
design, or one research question may be implemented later as:

- study-level analysis code
- comparison extensions
- system-specific analysis layers

They are not part of the version 1 framework-wide metric set.

---

## 10. Metric Semantics

### 9.1 Trace-Derived Requirement

Every version 1 metric, including extension-provided metrics, must be computable
from persisted replay-capable trace
artifacts without requiring hidden runtime state.

### 9.2 Mechanical Interpretation Rule

Every version 1 metric must admit a mechanical interpretation.

Examples:

- efficiency means action cost versus energy gained
- entropy means empirical action-distribution spread
- coverage means distinct visited positions
- prediction modulation strength means observed score difference attributable
  to predictive modulation

Version 1 metrics must not encode anthropomorphic assumptions.

### 9.3 Deterministic Recomputability

Given the same persisted replay-capable trace artifacts, the metric computation
must produce the same result.

This includes traces reconstructed from `delta`.

---

## 11. Extension Output Requirements

### 11.1 Structured Output Rule

System-specific metric extensions must return structured outputs that the
framework can persist and display without special-case ad hoc parsing.

### 11.2 Namespacing Rule

System-specific metrics should be namespaced by system or extension key to
avoid collisions with framework-standard metrics and with other future
extensions.

### 11.3 Failure Rule

If a system-specific metric extension is unavailable, AXIS must still compute
the standard metric set for that run when possible.

Missing system-specific metrics must not invalidate the full behavioral metric
artifact.

---

## 12. Predictive Metric Requirements

### 10.1 Applicability

Prediction-specific metrics must be computed only for systems whose traces
contain the required predictive fields.

### 10.2 Minimum Required Predictive Inputs

To support the version 1 predictive metric set, AXIS traces must provide enough
information to derive:

- prediction error magnitude
- prediction error sign or positive/negative components
- predictive modulation effect on action scores
- confidence/frustration trace levels or their equivalent

### 10.3 Fallback Rule

If a system lacks the required predictive trace fields, AXIS must not pretend
that predictive metrics are available.

Instead, the metric artifact must either:

- omit those fields
- or mark them as unavailable / not applicable

---

## 13. Integration with Comparison

### 11.1 Separation Rule

Enhanced behavioral metrics must remain distinct from paired trace divergence
metrics.

AXIS currently supports paired divergence analyses such as:

- action mismatch
- trajectory distance
- vitality difference

These are not replacements for the run-internal behavioral metrics defined by
this specification.

### 11.2 Future Combination

Later AXIS versions may present both:

- run-internal behavioral metrics
- paired divergence metrics

in one higher-level comparison workflow.

That integration is out of scope for version 1.

---

## 14. Validation Requirements

Version 1 implementation must be validated against:

- hand-checkable small traces
- deterministic recomputation from persisted artifacts
- both `full` and `delta` runs

Validation should cover both:

- framework-standard metrics
- system-specific extension metrics

Validation should include:

- direct unit tests for each metric
- aggregation tests across multiple episodes
- parity tests between `full` and reconstructed `delta` traces
- predictive metric tests on `system_c`
- extension registration / dispatch tests
- graceful behavior when no system-specific extension is registered

---

## 15. Recommended Implementation Posture

Version 1 should prefer a conservative integration strategy.

That means:

- keep the current minimal run summary intact
- add a separate behavioral metrics artifact
- support only replay-capable trace modes
- build the metric layer as an extension-capable subsystem from the start
- keep generic metrics in the framework
- let systems provide their own metric extensions
- keep context-sensitive and change-sensitive metrics out of scope

This posture minimizes architecture risk while still giving AXIS materially
better behavioral evaluation.

---

## 16. Summary

Version 1 of enhanced behavioral metrics must give AXIS a framework-supported,
trace-derived analysis layer beyond survival-only reporting.

The version 1 scope is intentionally narrow:

- only `full` and `delta`
- only directly derivable metrics
- only replay-capable analysis
- standard metrics in the framework core
- optional system-specific metric extensions through an explicit extension model
- no formal context-similarity metrics yet
- no environment-change metrics yet

This makes the idea both scientifically useful and realistically implementable
on the current AXIS system.
