# System Development Workflow -- Engineering Specification

## Version 1 Draft Engineering Specification

**Based on**:

- `system-development-workflow-spec.md`
- `experiment-workspace-spec.md`
- `experiment-workspace-engineering-spec.md`

---

## 1. Purpose

This document defines the engineering direction for supporting the workspace type:

- `development / system_development`

The goal is to translate the workflow specification into implementation-facing
terms that can guide concrete code changes.

This document focuses on:

- manifest model extensions
- scaffolding behavior
- run/compare/visualize behavior
- artifact placement and synchronization
- integration with the current AXIS workspace implementation

It does not yet decompose the work into final implementation work packages.

---

## 2. Engineering Goal

The engineering goal is:

> make `system_development` an explicit, operationally coherent workspace type
> with baseline-first validation semantics

This means:

- one explicit baseline
- one explicit active candidate
- explicit development-specific manifest state
- workspace-aware execution and comparison
- validation-oriented comparison behavior
- no document authoring automation in v1

---

## 3. Current Implementation Baseline

The existing workspace implementation already provides a general foundation:

- typed generic workspace manifests
- scaffolding
- checking
- summary/show
- workspace-aware run
- workspace-aware compare
- manifest synchronization
- visualization resolution

Relevant current modules include:

- `src/axis/framework/workspaces/types.py`
- `src/axis/framework/workspaces/scaffold.py`
- `src/axis/framework/workspaces/resolution.py`
- `src/axis/framework/workspaces/execute.py`
- `src/axis/framework/workspaces/compare_resolution.py`
- `src/axis/framework/workspaces/compare.py`
- `src/axis/framework/workspaces/sync.py`
- `src/axis/framework/workspaces/visualization.py`

The current implementation is still mostly generic.

In particular:

- `system_development` currently does not yet have explicit development-specific
  manifest fields
- scaffolding for development currently creates only a generic baseline config
- run resolution for development currently treats all configs as `baseline`
- compare resolution and visualization logic are not yet specialized around
  baseline/candidate semantics

So the main engineering task is not to invent a new subsystem.

It is to refine the existing workspace subsystem with explicit
`system_development` semantics.

---

## 4. Architectural Rule

The existing architectural rule remains in force:

- `src/axis/framework/cli.py` is a delegating entrypoint
- workspace business logic belongs under `src/axis/framework/workspaces/`
- SDK additions should remain minimal and should only be introduced when a true
  reusable public contract is needed

For this workflow, the expected implementation bias is:

> extend framework-side workspace logic first, avoid new SDK contracts unless
> clearly necessary

---

## 5. Required Engineering Changes

### 5.1 Manifest Model Extension

The generic `WorkspaceManifest` must be extended for `system_development`.

Required new fields:

- `baseline_config`
- `candidate_config`
- `baseline_results`
- `candidate_results`
- `current_candidate_result`
- `current_validation_comparison`

These should become explicit workflow fields for `system_development`.

They should not replace:

- `primary_configs`
- `primary_results`
- `primary_comparisons`
- `primary_measurements`

Instead:

- generic fields preserve common workspace structure
- development fields define the operational semantics for this workflow

### 5.2 Validation Rules

Validation must be extended so that `system_development` enforces:

- exactly one baseline config
- exactly zero or one candidate config
- valid baseline-first state
- valid pre-candidate and post-candidate states

The validator should explicitly distinguish:

- pre-candidate valid state
- post-candidate valid state
- invalid ambiguous state

### 5.3 Scaffolding Rules

Scaffolding for `system_development` must create:

- `concept/`
- `engineering/`
- `configs/baseline-system_a.yaml`
- initial concept markdown template
- initial engineering markdown template
- development-specific manifest fields in their correct initial state

It must not create a candidate config by default.

Initial manifest semantics should be:

- `baseline_config` populated
- `candidate_config` absent or null
- `baseline_results` empty
- `candidate_results` empty
- `current_candidate_result` absent or null
- `current_validation_comparison` absent or null

### 5.4 Run Resolution Rules

Run resolution for `system_development` must stop treating all configs as
generic baselines.

Instead it must use the explicit development fields.

Required behavior:

- if only `baseline_config` exists:
  - resolve baseline only
- if `baseline_config` and `candidate_config` exist:
  - resolve baseline plus candidate

The role mapping must become explicit:

- baseline
- candidate

Version 1 must also support:

- `--baseline-only`
- `--candidate-only`

for `axis workspaces run`.

### 5.5 Compare Resolution Rules

Compare resolution for `system_development` must become explicit as well.

Default comparison must use:

- baseline side from the primary baseline
- candidate side from `current_candidate_result`

If `current_candidate_result` is absent:

- comparison must fail explicitly

Development compare semantics must not rely only on generic
`primary_results` ordering.

### 5.6 Visualization Resolution Rules

Visualization for `system_development` must support:

- `--role baseline`
- `--role candidate`

Required behavior:

- if both baseline and candidate exist, role selection must disambiguate them
- if only baseline exists, default visualization may resolve to baseline
- if both exist and role is omitted, implementation should either:
  - require role explicitly
  - or use a clearly documented default

The preferred v1 behavior is:

- explicit role when both exist

### 5.7 Manifest Synchronization Rules

Manifest synchronization must update both:

- generic workspace fields
- development-specific workflow fields

After baseline runs:

- append to `baseline_results`
- update `primary_results`

After candidate runs:

- append to `candidate_results`
- update `current_candidate_result`
- update `primary_results`

After comparison runs:

- update `current_validation_comparison`
- update `primary_comparisons`

Synchronization must preserve:

- comments
- ordering
- readability

This means:

- read: `PyYAML` is acceptable
- write: `ruamel.yaml` should be used for workspace manifest mutation

### 5.8 Comparison Result Semantics

`system_development` comparison results should be treated as:

- validation records

The existing comparison envelope model can likely remain reusable, but the
operational resolution and default selection rules must be specialized for
development.

### 5.9 Summary / Show Semantics

Workspace summary for `system_development` should be extended to display the
development-specific state explicitly.

At minimum it should show:

- baseline config
- candidate config
- baseline result count
- candidate result count
- current candidate result
- current validation comparison

This is important because generic workspace summaries are not expressive enough
for the development loop.

---

## 6. Module-Level Target Areas

The following current files are expected to be extended.

### `src/axis/framework/workspaces/types.py`

Expected changes:

- add development-specific fields to `WorkspaceManifest`
- add type-specific validation rules for `system_development`

### `src/axis/framework/workspaces/validation.py`

Expected changes:

- validate development-specific field presence and coherence
- distinguish pre-candidate vs post-candidate state
- detect invalid ambiguity

### `src/axis/framework/workspaces/scaffold.py`

Expected changes:

- scaffold `baseline_config`
- scaffold development templates under `concept/` and `engineering/`
- initialize development-specific manifest fields

### `src/axis/framework/workspaces/resolution.py`

Expected changes:

- replace current generic development resolution with explicit baseline/candidate
  resolution
- support `--baseline-only` and `--candidate-only`

### `src/axis/framework/workspaces/execute.py`

Expected changes:

- consume the refined development execution plan
- preserve baseline/candidate role information for sync and later visualization

### `src/axis/framework/workspaces/compare_resolution.py`

Expected changes:

- use `current_candidate_result`
- resolve baseline explicitly from baseline state
- stop relying on generic result ordering for development

### `src/axis/framework/workspaces/compare.py`

Expected changes:

- integrate development compare resolution
- preserve validation-oriented artifact semantics

### `src/axis/framework/workspaces/sync.py`

Expected changes:

- update both generic and development-specific manifest fields

### `src/axis/framework/workspaces/summary.py`

Expected changes:

- expose development-specific summary fields

### `src/axis/framework/workspaces/visualization.py`

Expected changes:

- resolve baseline/candidate visualization targets explicitly

### `src/axis/framework/cli.py`

Expected changes:

- keep delegation thin
- add development-relevant optional flags for `workspaces run`
- support development-oriented role handling in workspace visualization if not
  already sufficient

---

## 7. Command-Level Engineering Expectations

### 7.1 `axis workspaces scaffold`

Must support creating a valid `system_development` workspace with:

- one default baseline
- no candidate yet
- concept template
- engineering template

### 7.2 `axis workspaces run`

Must support:

- baseline-only execution in pre-candidate state
- baseline-plus-candidate execution in post-candidate state
- explicit flags:
  - `--baseline-only`
  - `--candidate-only`

### 7.3 `axis workspaces compare`

Must support:

- candidate-vs-baseline validation compare
- explicit failure if no candidate result exists

### 7.4 `axis workspaces comparison-result`

Must support:

- default to current/latest validation comparison
- selection via `--number`

### 7.5 `axis visualize --workspace`

Must support:

- workspace-local replay
- `--role baseline`
- `--role candidate`

---

## 8. Suggested Delivery Sequence

The recommended delivery order is:

1. extend manifest model and validation
2. extend scaffolding
3. extend summary/show
4. extend run resolution and run flags
5. extend manifest synchronization
6. extend compare resolution and comparison-result semantics
7. extend visualization resolution
8. harden integration tests
9. update public manual

This sequence is recommended because:

- manifest semantics must exist before other logic can use them
- scaffolding should produce valid initial development state
- execution must populate state before comparison can resolve it correctly

---

## 9. Testing Expectations

The implementation should add or extend tests for:

- manifest validation of development-specific fields
- scaffolded initial `system_development` state
- pre-candidate run behavior
- post-candidate run behavior
- `--baseline-only`
- `--candidate-only`
- compare failure when no candidate exists
- compare success when candidate exists
- synchronization of development-specific fields
- visualization role resolution

Tests should live under:

- `tests/framework/workspaces/`

---

## 10. Non-Goals

This engineering spec does not require:

- source-code generation for the new system
- automatic candidate-config creation based on implementation discovery
- multiple baseline support
- multiple active candidate support
- document authoring automation

---

## 11. Summary

The engineering direction for `development / system_development` is:

- keep using the existing workspace subsystem
- make development semantics explicit instead of implicit
- add required baseline/candidate fields to the manifest
- refine scaffold, run, compare, sync, show, and visualize around those fields
- preserve the CLI as a delegator only

This should give AXIS a usable first development workflow without introducing
unnecessary new subsystems or excessive magic.
