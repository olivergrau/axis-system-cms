# System Development Workflow Specification

## Version 1 Draft Specification

---

## 1. Purpose

This document defines version 1 of the workflow specification for the workspace type:

- `development / system_development`

The purpose of this specification is to define the operational model for
developing a new AXIS system inside a workspace.

This specification covers:

- baseline and candidate semantics
- required artifact placement
- required manifest semantics
- workflow phase structure
- command-level operational expectations

---

## 2. Scope

This specification defines:

- the `system_development` workflow model
- the required baseline/candidate structure
- development-specific manifest fields
- expected behavior of workspace operations for development workspaces
- the role of `concept/`, `engineering/`, `results/`, `comparisons/`, and `measurements/`

This specification does not define:

- implementation details of source code changes
- internal system architecture of the developed system
- concrete comparison metric semantics
- document templates
- world-development workflow behavior

---

## 3. Normative Terms

The terms **must**, **must not**, **should**, and **may** are to be interpreted normatively.

---

## 4. Core Model

A `system_development` workspace is a combined:

- concept workspace
- engineering workspace
- validation workspace

Its purpose is to support the development of a new system through repeated
cycles of:

- conceptualization
- specification
- implementation
- validation
- refinement

The workflow is iterative rather than linear.

---

## 5. Baseline and Candidate Semantics

### 5.1 Baseline Rule

Version 1 of `system_development` must use:

- exactly one primary baseline system

The default baseline system is:

- `system_a`

This baseline must be scaffolded by default and may later be changed manually
through workspace configuration.

### 5.2 Candidate Rule

Version 1 must use:

- exactly one active candidate configuration

The candidate is the current executable representation of the system under
development.

### 5.3 Baseline-First Rule

The baseline must exist before the candidate.

This means a `system_development` workspace must be valid and operational in a
baseline-only state before any candidate execution exists.

### 5.4 Comparison Rule

The default validation comparison must be:

- current candidate vs primary baseline

If that pairing cannot be resolved explicitly, the workspace operation must
fail rather than guessing.

---

## 6. Candidate State Detection

Candidate existence must be determined through explicit workspace state, not
through source-code inspection.

Version 1 must use configuration state and manifest state to determine whether
the workspace is in:

- pre-candidate state
- post-candidate state

### 6.1 Pre-Candidate State

A workspace is in pre-candidate state when:

- `baseline_config` is present
- `candidate_config` is absent

### 6.2 Post-Candidate State

A workspace is in post-candidate state when:

- `baseline_config` is present
- `candidate_config` is present

---

## 7. Config Naming Convention

Version 1 should use the following naming convention.

### 7.1 Baseline Config

The baseline config should be named:

- `configs/baseline-system_a.yaml`

or the equivalent baseline-system filename if the baseline is manually changed.

### 7.2 Candidate Config

The candidate config should be named:

- `configs/candidate-<system_type>.yaml`

Example:

- `configs/candidate-system_d.yaml`

This naming convention should be treated as the standard convention for v1.

---

## 8. Required Artifact Locations

### 8.1 `concept/`

`concept/` must contain mathematical and conceptual development artifacts.

Typical contents include:

- mathematical concept
- worked examples
- formalization drafts
- reduction cases

This directory must remain conceptually focused.

Implementation-planning artifacts do not belong here.

### 8.2 `engineering/`

`engineering/` must contain implementation-oriented artifacts.

Typical contents include:

- engineering specs
- work packages
- implementation planning
- test planning

### 8.3 `configs/`

`configs/` must contain executable configuration files used by the development workflow.

Version 1 requires:

- one baseline config

and later allows:

- one active candidate config

### 8.4 `results/`

`results/` must contain workspace-owned execution artifacts.

These include:

- baseline execution artifacts
- candidate execution artifacts

### 8.5 `comparisons/`

`comparisons/` must contain workspace-owned comparison artifacts.

In `system_development`, these comparison artifacts are validation artifacts.

### 8.6 `measurements/`

`measurements/` must contain summary metrics and extracted validation evidence.

### 8.7 `notes.md`

`notes.md` must remain a free-form workspace note document.

It should be used for:

- observations
- interpretation
- failed hypotheses
- next steps

---

## 9. Development-Specific Manifest Fields

For `system_development`, the following additional manifest fields are required
in version 1.

- `baseline_config`
- `candidate_config`
- `baseline_results`
- `candidate_results`
- `current_candidate_result`
- `current_validation_comparison`

These fields are required workflow fields for the first `system_development`
specification.

### 9.1 `baseline_config`

Must contain the workspace-relative path to the single primary baseline config.

### 9.2 `candidate_config`

Must contain the workspace-relative path to the active candidate config.

In pre-candidate state, this field may be empty or null only if the workspace
is explicitly still pre-candidate.

For post-candidate operation, it must be present.

### 9.3 `baseline_results`

Must contain an ordered list of workspace-relative baseline execution artifacts.

### 9.4 `candidate_results`

Must contain an ordered list of workspace-relative candidate execution artifacts.

### 9.5 `current_candidate_result`

Must contain the workspace-relative path to the candidate result used by
default in validation and visualization operations.

### 9.6 `current_validation_comparison`

Must contain the workspace-relative path to the comparison artifact used by
default in comparison-result inspection.

---

## 10. Relationship to Generic Manifest Fields

The generic workspace fields remain valid:

- `primary_configs`
- `primary_results`
- `primary_comparisons`
- `primary_measurements`

However, in `system_development` they must be interpreted as generic
workspace-level artifact collections, while the development-specific fields
carry the explicit baseline/candidate workflow semantics.

This means:

- generic fields preserve cross-workspace consistency
- development-specific fields define operational development semantics

---

## 11. Workflow Phases

Version 1 of `system_development` must be understood through the following phases.

### 11.1 Phase 1 -- Workspace Creation

The workspace is scaffolded.

Minimum result:

- `concept/` exists
- `engineering/` exists
- baseline config exists
- initial markdown templates exist under `concept/` and `engineering/`
- manifest exists

### 11.2 Phase 2 -- Concept and Spec Work

The user writes:

- mathematical concept artifacts
- worked examples
- spec drafts
- engineering planning artifacts

This authoring work remains manual in version 1.

### 11.3 Phase 3 -- Baseline Orientation

Before the candidate exists, the baseline is executed.

This phase establishes:

- behavioral anchor
- baseline traces
- baseline measurements

### 11.4 Phase 4 -- Candidate Validation

Once the candidate config exists, the candidate becomes part of the operational
workspace flow.

### 11.5 Phase 5 -- Comparison and Validation

Comparison validates the current candidate against the primary baseline.

### 11.6 Phase 6 -- Iterative Refinement

The user iterates through:

- concept updates
- engineering updates
- implementation updates
- execution
- comparison
- interpretation

---

## 12. Command Semantics

### 12.1 `axis workspaces scaffold`

For `system_development`, scaffolding must:

- create `concept/`
- create `engineering/`
- create one baseline config
- create initial markdown templates in `concept/` and `engineering/`

It must not create a candidate config by default.

### 12.2 `axis workspaces run`

Operational meaning:

- pre-candidate state:
  - run baseline only
- post-candidate state:
  - run baseline plus candidate

Version 1 must also support:

- `--baseline-only`
- `--candidate-only`

These selective flags are part of the required workflow model.

### 12.3 `axis workspaces compare`

Operational meaning:

- validate current candidate against primary baseline

Default resolution must use:

- primary baseline
- current candidate result

If candidate validation state cannot be resolved, the command must fail explicitly.

### 12.4 `axis workspaces comparison-result`

Operational meaning:

- inspect validation evidence

Default behavior:

- show the latest or current validation comparison

Selection behavior:

- `--number N` selects a specific earlier comparison artifact

### 12.5 `axis visualize --workspace`

Operational meaning:

- visualize workspace-local execution artifacts

When both baseline and candidate exist, visualization must distinguish them via:

- `--role baseline`
- `--role candidate`

If only baseline exists, default visualization may resolve to baseline.

---

## 13. Comparison Semantics

In `system_development`, comparison is not primarily investigative.

It is primarily:

- validating
- decision-supporting
- iteration-guiding

Comparison artifacts in this workflow must therefore be interpreted as:

- validation evidence for the current state of the system under development

---

## 14. Supported vs Unsupported in Version 1

### 14.1 Supported

Version 1 supports:

- structured placement of concept artifacts
- structured placement of engineering artifacts
- baseline execution
- candidate execution
- validation comparison
- local result placement
- local comparison placement
- iterative note-taking

### 14.2 Unsupported

Version 1 does not support:

- automated concept authoring
- automated worked-example authoring
- automated spec authoring
- automated engineering authoring
- document-derived readiness inference

These remain manual.

---

## 15. Conformance Rules

A `system_development` workspace conforms to this workflow specification if:

- it conforms to the general workspace specification
- it has exactly one primary baseline
- it uses exactly one active candidate configuration
- it provides the required development-specific manifest fields
- it places concept artifacts under `concept/`
- it places engineering artifacts under `engineering/`
- it treats comparison as validation evidence
- it supports baseline-only pre-candidate operation

---

## 16. Non-Goals for Version 1

Version 1 does not require:

- multiple baseline semantics
- multiple active candidates
- automated document generation
- development-specific CLI verbs beyond the shared workspace commands

---

## 17. Summary

Version 1 of the `system_development` workflow defines a narrow, explicit
development model:

- exactly one baseline
- exactly one active candidate
- explicit development-specific manifest fields
- manual concept and engineering authoring
- workspace-local execution, comparison, and measurement artifacts
- comparison as validation evidence

This is intentionally constrained so that the first development workflow stays
operationally clear and implementation-friendly.
