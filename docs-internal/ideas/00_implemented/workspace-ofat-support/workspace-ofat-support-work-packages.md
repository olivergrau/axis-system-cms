# Workspace OFAT Support Work Packages

## Purpose

This document provides a first coarse implementation roadmap for introducing
bounded OFAT support in AXIS Experiment Workspaces, based on:

- [Workspace OFAT Support Spec](./workspace-ofat-support-spec.md)
- [Workspace OFAT Support Engineering Spec](./workspace-ofat-support-engineering-spec.md)

The packages below are intentionally still broad. Their purpose is to define a
clear delivery sequence before detailed implementation packages are written.


## Current Code Reality

The current codebase already contains important prerequisites:

- framework-level `ExperimentOutput` support for `point` and `sweep`
- structured `primary_results` entries in `workspace.yaml`
- workspace-owned execution under `results/`
- output-aware visualization that already rejects sweep visualization without
  explicit run selection

However, the actual Workspace OFAT support is still incomplete:

- `validation.py` still rejects non-`single_run` configs globally
- `execute.py` still reuses that global guardrail
- `single_system` comparison still resolves by manifest order rather than by
  filtering point outputs
- `axis workspaces sweep-result` does not yet exist
- current manuals still describe Workspaces as `single_run`-only


## Delivery Strategy

The implementation should proceed in four layers:

1. **Guardrails and execution admission**
   Allow OFAT only where intended: `investigation / single_system`.
2. **Sweep inspection**
   Add a first-class way to inspect sweep outputs without overloading
   `show` or `compare`.
3. **Mixed-history operational semantics**
   Refine `single_system` so point and sweep outputs can coexist without
   ambiguity.
4. **Hardening**
   Add tests, optional scaffolding support, and documentation updates.


## Work Packages

### WP-01: Single-System OFAT Validation and Guardrails

Relax the current global Workspace config guardrail so that valid OFAT configs
are accepted only for `workspace_type = single_system`.

Scope:

- make `check_config_experiment_types(...)` workspace-type-aware
- allow:
  - `single_system`: `single_run`, `ofat`
  - `system_comparison`: `single_run` only
  - `system_development`: `single_run` only
- keep precise early failure messages for unsupported workspace types
- ensure `execute_workspace(...)` uses the refined validation rather than
  blocking valid `single_system + ofat`

Primary files:

- `src/axis/framework/workspaces/validation.py`
- `src/axis/framework/workspaces/execute.py`


### WP-02: Sweep Execution and Result Recording

Ensure a valid OFAT run in a `single_system` workspace behaves correctly as a
workspace-owned sweep result.

Scope:

- confirm `axis workspaces run` executes OFAT configs without extra flags
- ensure one OFAT execution yields exactly one structured `primary_results`
  entry at the experiment root
- ensure the synced result entry carries:
  - `path`
  - `output_form = sweep`
  - `system_type`
  - `role`
  - `baseline_run_id`
- keep point execution behavior unchanged

Primary files:

- `src/axis/framework/cli.py`
- `src/axis/framework/workspaces/execute.py`
- `src/axis/framework/workspaces/sync.py`


### WP-03: Sweep Result Command

Add a first-class Workspace command for inspecting sweep outputs.

Scope:

- add:
  - `axis workspaces sweep-result <workspace>`
- default selection:
  - newest sweep output in `primary_results`
- explicit selection:
  - `--experiment <eid>`
- text and JSON output
- reject point outputs explicitly
- do not overload `show` with sweep analysis

Primary files:

- `src/axis/framework/cli.py`
- `src/axis/framework/workspaces/sweep_result.py` (new)


### WP-04: Single-System Compare Refinement for Mixed Histories

Refine `single_system` comparison behavior so mixed point/sweep histories remain
usable without introducing point-vs-sweep comparison.

Scope:

- filter `primary_results` to point outputs only
- use:
  - first point output as reference
  - latest point output as candidate
- keep explicit experiment override support
- reject any sweep-involving workspace compare path with a clear error that
  points users to `sweep-result`

Primary files:

- `src/axis/framework/workspaces/handlers/single_system.py`
- `src/axis/framework/workspaces/compare_resolution.py`
- `src/axis/framework/workspaces/compare.py`


### WP-05: Optional OFAT Starter Scaffolding

Extend scaffolding so `single_system` workspaces can optionally start with an
OFAT-ready config.

Scope:

- keep current default:
  - scaffold a point (`single_run`) baseline config
- optionally allow an OFAT starter config during interactive scaffolding
- populate starter values for:
  - `experiment_type`
  - `parameter_path`
  - `parameter_values`
- keep this as a convenience feature, not a prerequisite for OFAT support

Primary files:

- `src/axis/framework/cli.py`
- `src/axis/framework/workspaces/scaffold.py`
- `src/axis/framework/workspaces/handlers/single_system.py`


### WP-06: Test Coverage and Regression Hardening

Add and update tests to cover the new bounded OFAT behavior in workspaces.

Scope:

- validation acceptance for `single_system + ofat`
- continued rejection for:
  - `system_comparison + ofat`
  - `system_development + ofat`
- workspace run producing sweep result entries
- `sweep-result` default and explicit selection
- compare filtering to point outputs only
- explicit failure for sweep-involving compare paths
- keep explicit sweep visualization behavior intact

Primary areas:

- `tests/framework/workspaces/test_validation.py`
- `tests/framework/workspaces/test_integration.py`
- `tests/framework/test_cli.py`


### WP-07: Manual and Internal Documentation Update

Update the public and internal documentation to reflect the new bounded OFAT
workspace support.

Scope:

- update `workspace-manual.md`
- update `axis-overview.md`
- keep `show` management-only in documentation
- document:
  - `sweep-result`
  - `single_system` mixed point/sweep histories
  - point-only workspace compare semantics
  - explicit sweep visualization

Primary files:

- `docs/manuals/workspace-manual.md`
- `docs/manuals/axis-overview.md`
- `docs-internal/ideas/workspace-ofat-support/*.md` as needed


## Recommended Sequence

1. `WP-01 Single-System OFAT Validation and Guardrails`
2. `WP-02 Sweep Execution and Result Recording`
3. `WP-03 Sweep Result Command`
4. `WP-04 Single-System Compare Refinement for Mixed Histories`
5. `WP-06 Test Coverage and Regression Hardening`
6. `WP-07 Manual and Internal Documentation Update`
7. `WP-05 Optional OFAT Starter Scaffolding`

Notes:

- `WP-05` can be postponed because it is a convenience feature, not required
  for the first operational OFAT support.
- `WP-03` and `WP-04` are logically independent after `WP-01` and `WP-02`,
  and can be developed in parallel if needed.


## Milestones

### Milestone 1: Admission

Complete when:

- `single_system` accepts valid OFAT configs
- other workspace types still reject OFAT
- OFAT runs persist inside `workspace/results/`

### Milestone 2: Inspection

Complete when:

- `axis workspaces sweep-result` exists
- sweep outputs can be inspected reliably
- mixed point/sweep histories remain understandable

### Milestone 3: Operational Stability

Complete when:

- `single_system` compare behavior is point-only and explicit
- tests cover bounded OFAT support
- public manuals describe the new mode accurately
