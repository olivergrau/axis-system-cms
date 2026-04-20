# Workspace OFAT Support Engineering Spec

## 1. Purpose

This engineering specification derives the implementation shape of first-wave
OFAT support in AXIS Experiment Workspaces from:

- [Workspace OFAT Support Spec](./workspace-ofat-support-spec.md)

The goal is to add bounded Workspace-level OFAT support without disturbing the
existing semantics of:

- Workspace management
- point-vs-point comparison workflows
- system development workspaces


## 2. Implementation Goal

The framework shall support `experiment_type = ofat` in Workspace mode only for:

- `investigation / single_system`

This support shall include:

- workspace execution of OFAT configs
- structured sweep result tracking in `primary_results`
- dedicated sweep inspection through a new command
- explicit sweep visualization via experiment + run selection

This support shall **not** include:

- sweep comparison
- point-vs-sweep comparison
- sweep support in `system_comparison`
- sweep support in `system_development`


## 3. Architectural Position

The implementation should build directly on the existing Experiment Output
abstraction:

- point output
- sweep output

The Workspace layer should not create a second sweep model.

Instead, it should:

- allow OFAT config execution in the relevant Workspace type
- store sweep outputs as first-class result entries
- resolve sweep behavior through `ExperimentOutput`


## 4. Existing Code Areas Affected

Based on the current codebase, the main affected areas are:

### 4.1 CLI

- `src/axis/framework/cli.py`

### 4.2 Workspace validation and typing

- `src/axis/framework/workspaces/types.py`
- `src/axis/framework/workspaces/validation.py`

### 4.3 Workspace execution and synchronization

- `src/axis/framework/workspaces/execute.py`
- `src/axis/framework/workspaces/sync.py`

### 4.4 Workspace handlers

- `src/axis/framework/workspaces/handlers/single_system.py`
- `src/axis/framework/workspaces/handlers/system_comparison.py`
- `src/axis/framework/workspaces/handlers/system_development.py`

### 4.5 Workspace compare / visualization

- `src/axis/framework/workspaces/compare_resolution.py`
- `src/axis/framework/workspaces/compare.py`
- `src/axis/framework/workspaces/visualization.py`

### 4.6 Workspace summary

- `src/axis/framework/workspaces/summary.py`


## 5. Core Behavioral Requirements

### 5.1 OFAT allowed only for `single_system`

Workspace validation must allow:

- `single_run`
- `ofat`

only for:

- `workspace_type = single_system`

All other workspace types must continue to reject:

- any config whose `experiment_type != single_run`

### 5.2 One sweep = one result artifact

When an OFAT config is executed in a `single_system` workspace:

- the produced sweep output must appear as exactly one result entry
- the result entry must point to the experiment root
- the result entry must carry `output_form = sweep`

### 5.3 Compare remains point-only

`axis workspaces compare` in `single_system` must:

- filter result entries to point outputs only
- ignore sweep outputs for candidate selection
- fail if fewer than two point outputs exist

### 5.4 Sweep inspection uses a dedicated command

A new command must be introduced:

- `axis workspaces sweep-result`

This command must:

- inspect sweep outputs only
- reject non-sweep outputs explicitly
- default to the newest sweep output
- support explicit selection by experiment ID

### 5.5 Sweep visualization stays explicit

Sweep visualization must require:

- explicit experiment selection
- explicit run selection

No implicit baseline or first-run default is allowed.


## 6. CLI Changes

### 6.1 New subcommand

Add to `axis workspaces`:

- `sweep-result`

Suggested flags:

- positional: `<workspace-path>`
- optional: `--experiment <eid>`
- standard `--output` support if appropriate

### 6.2 `run` command

No new flag is required for OFAT support.

The existing:

- `axis workspaces run <workspace>`

should simply allow OFAT configs in `single_system` and produce sweep outputs.

### 6.3 `compare` command

No new flags are required.

The command must continue to behave as a point comparison command and reject
any sweep-involved comparison state explicitly.

### 6.4 `show` command

No command-shape change is required.

`show` should remain management-oriented, but may expose:

- `output_form`

for listed result artifacts.


## 7. Validation Changes

### 7.1 Current behavior

Current Workspace validation already includes the config-type guardrail in:

- `src/axis/framework/workspaces/validation.py`

That logic currently rejects non-`single_run` configs for all workspace types.

### 7.2 Required change

Validation must become workspace-type-aware:

- `single_system`:
  - allow `single_run`
  - allow `ofat`
- all others:
  - allow only `single_run`

### 7.3 Validation responsibilities

For OFAT configs in `single_system`, validation must ensure that the normal
framework OFAT requirements are satisfied.

This can rely on existing config validation, but Workspace validation must not
block valid OFAT configs in `single_system`.


## 8. Workspace Handler Changes

### 8.1 `single_system`

The `single_system` handler should remain the only handler that can
operationally host point and sweep outputs together.

Its role logic does not need a new role system for sweep outputs.

The key required behavior is:

- execution works for both config types
- comparison selection later filters point outputs only

### 8.2 `system_comparison`

No OFAT support should be introduced.

The existing guardrails must continue to reject OFAT configs.

### 8.3 `system_development`

No OFAT support should be introduced.

The existing guardrails must continue to reject OFAT configs.


## 9. Result Tracking Changes

### 9.1 Primary results

The existing structured `primary_results` entries are already suitable for
mixed point/sweep histories because they carry:

- `path`
- `output_form`
- `system_type`
- `role`
- `created_at`

No new top-level manifest fields are required for v1 OFAT support.

### 9.2 Historical accumulation

Multiple sweeps over time must be allowed.

This means:

- execution should append new sweep result entries
- no overwrite behavior should be introduced

### 9.3 Summary presentation

Workspace summaries should display the presence of sweep outputs in artifact
lists, but should not attempt to display sweep analysis.


## 10. Sweep Result Inspection

### 10.1 New workspace module logic

The implementation should introduce a Workspace-level helper for sweep result
resolution and rendering.

This may live in one of two ways:

- extend an existing module under `src/axis/framework/workspaces/`
- or add a focused new module such as:
  - `src/axis/framework/workspaces/sweep_result.py`

The engineering preference is:

- add a focused new module if that keeps responsibilities cleaner

### 10.2 Resolution behavior

The command should:

1. load the Workspace manifest
2. filter `primary_results` to `output_form = sweep`
3. if `--experiment` is given:
   - validate that it exists
   - validate that it is a sweep output
4. otherwise:
   - select the newest sweep output

### 10.3 Rendered information

The result command should show at minimum:

- experiment identity
- system type
- parameter path
- parameter values
- baseline run ID
- variation descriptions
- experiment summary with OFAT deltas


## 11. Comparison Changes

### 11.1 `single_system` selection logic

Current `single_system` comparison behavior uses manifest ordering.

For OFAT-enabled `single_system`, this must be refined:

- filter to point outputs only
- use:
  - first point output as reference
  - latest point output as candidate

If fewer than two point outputs exist:

- fail explicitly

### 11.2 Explicit comparison restriction

Workspace comparison must continue to reject:

- point vs sweep
- sweep vs point
- sweep vs sweep

The error should explain that:

- sweep results must be inspected through `sweep-result`
- and sweep comparison is not yet supported


## 12. Visualization Changes

### 12.1 Current state

Workspace visualization is already output-aware and already rejects sweep
visualization without explicit run selection.

### 12.2 Required alignment

The Workspace OFAT support implementation must ensure that:

- sweep-producing single-system workspaces remain compatible with that explicit
  visualization rule
- no new implicit sweep defaults are introduced

### 12.3 Expected user path

The intended visualization path for a sweep remains:

- `axis visualize --workspace <path> --experiment <eid> --run <rid> --episode N`


## 13. Scaffolding Changes

### 13.1 Default scaffold stays point-based

The existing default scaffold for `single_system` should remain:

- a point config starter

### 13.2 Optional OFAT starter support

Scaffolding may be enhanced to optionally generate:

- an OFAT starter config

This is a convenience feature, not a prerequisite for basic OFAT support.

If added, it should:

- remain optional
- set starter values for:
  - `parameter_path`
  - `parameter_values`


## 14. Testing Strategy

### 14.1 Required new coverage

Add or update tests to cover:

- `single_system` workspace accepts valid OFAT config
- `system_comparison` workspace still rejects OFAT config
- `system_development` workspace still rejects OFAT config
- OFAT execution in `single_system` records one sweep result entry
- `sweep-result` selects newest sweep by default
- `sweep-result --experiment <eid>` works for sweep outputs
- `sweep-result --experiment <eid>` fails for point outputs
- `compare` filters to point outputs only in mixed histories
- `compare` fails when only one or zero point outputs exist

### 14.2 Likely test files

- `tests/framework/workspaces/test_validation.py`
- `tests/framework/workspaces/test_integration.py`
- add a new focused test file for sweep-result if needed


## 15. Implementation Sequence

Recommended order:

1. Relax validation only for `single_system`
2. Ensure run/sync paths already record sweep outputs cleanly
3. Add `sweep-result` resolution and rendering
4. Refine `single_system` compare selection to filter point outputs
5. Update CLI wiring
6. Add tests
7. Update manuals


## 16. Non-Goals

This engineering wave does not include:

- sweep-vs-sweep comparison
- point-vs-sweep comparison
- OFAT in `system_comparison`
- OFAT in `system_development`
- sweep-specific manifest fields
- a generalized output-result command replacing `sweep-result`


## 17. Recommendation

Proceed with OFAT Workspace support as a bounded operational extension of
`investigation / single_system`.

Implementation should:

- reuse the Experiment Output abstraction
- keep `show` management-only
- keep `compare` point-only
- add a dedicated `sweep-result` command
- preserve explicit run selection for sweep visualization

This gives AXIS a practical first Workspace-level OFAT capability without
prematurely committing to sweep comparison semantics.
