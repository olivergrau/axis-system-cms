# Workspace Workflow Optimizations Engineering Spec

## Purpose

This engineering specification describes how to implement workflow-aware
workspace behavior in the current AXIS codebase.

The implementation target is intentionally narrow:

- tighten built-in workflow enums
- add a close command
- enforce workflow permissions in workspace services
- preserve the existing manifest-centric architecture


## Implementation Goals

The implementation must:

- update the manifest model to the new canonical workflow values
- add a command for closing a workspace
- reject mutating workflow actions for closed workspaces
- keep read-only workspace inspection working unchanged


## Current Architecture

The relevant implementation points today are:

- manifest model:
  - `src/axis/framework/workspaces/types.py`
- CLI parser:
  - `src/axis/framework/cli/parser.py`
- workspace command handlers:
  - `src/axis/framework/cli/commands/workspaces.py`
- service-layer orchestration:
  - `src/axis/framework/workspaces/services/run_service.py`
  - `src/axis/framework/workspaces/services/compare_service.py`
  - `src/axis/framework/workspaces/services/inspection_service.py`
- manifest mutation / sync:
  - `src/axis/framework/workspaces/manifest_mutator.py`
  - `src/axis/framework/workspaces/sync.py`
- summary and validation:
  - `src/axis/framework/workspaces/summary.py`
  - `src/axis/framework/workspaces/validation.py`
- CLI dependency wiring:
  - `src/axis/framework/cli/context.py`


## Proposed Design

### 1. Keep workflow fields where they are

Do not introduce a new `workflow` manifest block.

Continue to use:

- `status`
- `lifecycle_stage`

This keeps the change local and avoids wider schema churn.


### 2. Introduce canonical enum updates in `types.py`

Update `WorkspaceStatus` to:

- `draft`
- `active`
- `analyzing`
- `completed`
- `closed`

Update `WorkspaceLifecycleStage` to:

- `idea`
- `draft`
- `spec`
- `implementation`
- `analysis`
- `documentation`
- `final`


### 3. Reject legacy workflow values explicitly

Existing workspaces already use legacy values like:

- `idea`
- `running`

These values should not be silently mapped.

Recommended approach:

- rely on normal enum validation in `WorkspaceManifest`
- if a manifest contains removed values, loading must fail
- the resulting error should clearly indicate that the user must update
  `workspace.yaml`

This keeps workflow semantics explicit and avoids hidden manifest rewriting.


### 4. Add explicit close mutation support

Add a manifest mutator function in:

- `src/axis/framework/workspaces/manifest_mutator.py`

Recommended API:

- `close_workspace(data: dict) -> None`

Required mutation:

- set `status` to `closed`
- set `lifecycle_stage` to `final`

Guardrail:

- if already closed, raise `ValueError`


### 5. Add a service-layer close operation

Add a dedicated service rather than mutating directly in the command module.

Recommended file:

- `src/axis/framework/workspaces/services/workflow_service.py`

Recommended responsibility:

- load manifest roundtrip
- apply `close_workspace(...)`
- save manifest roundtrip
- return a tiny result object with the new workflow state

This keeps workflow mutation aligned with the existing service-oriented
workspace architecture.


### 6. Wire the close command into the CLI

Parser changes in:

- `src/axis/framework/cli/parser.py`

Add:

- `axis workspaces close <workspace-path>`

Command changes in:

- `src/axis/framework/cli/commands/workspaces.py`

Add:

- `cmd_workspaces_close(...)`

Text output should show:

- workspace id/path
- new `status`
- new `lifecycle_stage`

JSON output should return structured confirmation.


### 7. Enforce closed-state restrictions in the service layer

The workflow guardrails should live in services, not only in CLI functions.

#### `WorkspaceRunService`

In:

- `src/axis/framework/workspaces/services/run_service.py`

Before planning or executing runs:

- load the manifest
- if `manifest.status == "closed"`, raise `ValueError`

#### `WorkspaceCompareService`

In:

- `src/axis/framework/workspaces/services/compare_service.py`

Before running comparison:

- load the manifest
- if `manifest.status == "closed"`, raise `ValueError`

#### Candidate mutation

In:

- `WorkspaceRunService.set_candidate(...)`

Before mutating the manifest:

- load the manifest
- if closed, raise `ValueError`


### 8. Keep inspection services read-only and always available

No workflow gating is needed for:

- summarize
- check
- sweep-result

Closed workspaces must remain inspectable.


### 9. Surface workflow state clearly in summaries

`WorkspaceSummary` already carries:

- `status`
- `lifecycle_stage`

No schema expansion is strictly required for the first version.

Optional improvement:

- add a derived boolean like `is_closed`

This is not required if the CLI can simply interpret `status == closed`.


### 10. Validation changes

The main validation impact is enum acceptance.

Because `WorkspaceManifest` owns enum validation already, no large validation
subsystem change is required.

Possible small enhancement in:

- `src/axis/framework/workspaces/validation.py`

Add informational workflow checks later if desired, but they are not required
for first implementation.

Examples of optional future checks:

- `closed` workspace with empty results
- `final` lifecycle on still-open workspace

Those should not block the first implementation.


## Suggested File-Level Changes

### `src/axis/framework/workspaces/types.py`

Change:

- update `WorkspaceStatus`
- update `WorkspaceLifecycleStage`

### `src/axis/framework/workspaces/manifest_mutator.py`

Add:

- `close_workspace(data: dict) -> None`

### `src/axis/framework/workspaces/services/workflow_service.py`

Add:

- result dataclass for workflow mutations
- `close(...)`

### `src/axis/framework/cli/context.py`

Wire:

- workflow service into CLI context

### `src/axis/framework/cli/parser.py`

Add:

- `workspaces close`

### `src/axis/framework/cli/commands/workspaces.py`

Add:

- `cmd_workspaces_close(...)`

Update if useful:

- text output in `show` to make closed state more obvious

### `src/axis/framework/workspaces/services/run_service.py`

Add:

- closed-workspace guard in `execute(...)`
- closed-workspace guard in `set_candidate(...)`

### `src/axis/framework/workspaces/services/compare_service.py`

Add:

- closed-workspace guard in `compare(...)`


## Error Semantics

Closed-workspace errors should be direct and action-oriented.

Recommended messages:

- run:
  - `Workspace is closed; no further executions are allowed.`
- compare:
  - `Workspace is closed; no further comparisons are allowed.`
- set-candidate:
  - `Workspace is closed; candidate config cannot be changed.`
- close on already closed workspace:
  - `Workspace is already closed.`


## Compatibility Strategy

There are two layers of compatibility to preserve.

### Manifest loading

Old manifests with removed workflow values are expected to fail validation.
This is intentional.

### Scaffold defaults

`axis workspaces scaffold` should stop offering deprecated status values.

Recommended new defaults:

- `status`: `draft`
- `lifecycle_stage`: `idea`


## Test Plan

### Manifest tests

Update/add tests for:

- new enum values accepted
- invalid values rejected
- removed legacy values rejected with clear validation failures

Likely file:

- `tests/framework/test_manifest_mutator.py`
- plus workspace type/model tests if present nearby

### Service tests

Add tests for:

- run blocked when workspace is closed
- compare blocked when workspace is closed
- set-candidate blocked when workspace is closed
- close service updates manifest correctly

Likely file:

- `tests/framework/test_workspace_services.py`

### CLI parser tests

Add:

- parser recognizes `axis workspaces close <workspace>`

Likely file:

- `tests/framework/test_cli_parser.py`

### CLI output tests

Add:

- close command text output
- close command JSON output
- show command still surfaces updated workflow fields correctly

Likely file:

- `tests/framework/test_cli_output.py`

### Validation / summary tests

Add or update:

- closed workspace remains valid
- legacy manifests still summarize correctly after load

Likely files:

- `tests/framework/workspaces/test_validation.py`
- `tests/framework/workspaces/test_summary.py`


## Delivery Sequence

Recommended implementation order:

1. update enums and legacy migration in `types.py`
2. add close mutator
3. add workflow service
4. add parser and command
5. add run/compare/set-candidate gating
6. update scaffold defaults
7. add / update tests

This sequence keeps the system working throughout the change and makes failures
easy to localize.


## Out Of Scope

Do not implement yet:

- reopen workflow
- generic status/lifecycle editing commands
- per-workspace configurable state machines
- `closed_at` and `close_reason`


## Summary

The implementation should be a focused workflow layer on top of the existing
workspace architecture.

Concretely:

- update built-in workflow enums
- support old manifests through migration
- add `axis workspaces close`
- block run / compare / candidate mutation when closed
- keep read-only inspection available
