# Workspace Workflow Optimizations Spec

## Purpose

This specification defines how AXIS workspaces expose and enforce workflow
state.

The goal is to make workspace workflow metadata operationally meaningful.
In particular:

- `status` must no longer be passive descriptive metadata only
- closed workspaces must be explicitly representable
- workspace-aware mutating commands must respect workflow state

This spec does **not** introduce fully user-defined workflow state machines.
Workflow semantics remain framework-owned in this version.


## Scope

This specification applies to:

- workspace manifest semantics
- workspace CLI behavior
- workspace validation and summary behavior
- run / compare / candidate-selection workflow gating

This specification does not change:

- workspace class/type semantics
- workspace artifact structure
- experiment execution semantics outside workspace mode


## Goals

The workflow system must:

- give `status` a clear operational meaning
- keep `lifecycle_stage` as a descriptive progress field
- provide an explicit way to finalize a workspace
- prevent new executions and comparisons in closed workspaces
- preserve read-only inspection of closed workspaces
- remain compatible with the current manifest-centered workspace model


## Non-Goals

This version does not include:

- arbitrary workspace-defined state lists
- arbitrary workspace-defined transition graphs
- a generic workflow editor
- a reopen command
- broad metadata editing commands


## Canonical Workflow Fields

AXIS workspaces continue to use these two manifest fields:

- `status`
- `lifecycle_stage`

No parallel workflow block is introduced in this version.


## `status`

`status` is the operational workflow field.

It answers:

> what is the current operational state of the workspace?

### Allowed values

- `draft`
- `active`
- `analyzing`
- `completed`
- `closed`

### Meaning

- `draft`
  - workspace exists but is not yet in active operational use
- `active`
  - workspace is open for normal execution and comparison activity
- `analyzing`
  - workspace remains open, but the main focus is interpretation of results
- `completed`
  - workspace work is considered complete, but the workspace is still not
    formally frozen
- `closed`
  - workspace is finalized and operationally closed

### Operational rule

Only `closed` is a blocking state in this version.

That means:

- `draft`, `active`, `analyzing`, and `completed` are open states
- `closed` is the only closed state


## `lifecycle_stage`

`lifecycle_stage` is the descriptive progress field.

It answers:

> where is the workspace in its intellectual or engineering lifecycle?

### Allowed values

- `idea`
- `draft`
- `spec`
- `implementation`
- `analysis`
- `documentation`
- `final`

### Semantics

`lifecycle_stage` is descriptive in this version.

It does not independently grant or deny command permissions.


## Workflow Permissions

Workflow permissions are defined by `status`.

### Open workspaces

For workspaces whose `status` is one of:

- `draft`
- `active`
- `analyzing`
- `completed`

the following operations are allowed:

- `axis workspaces show`
- `axis workspaces check`
- `axis workspaces sweep-result`
- workspace visualization
- `axis workspaces run`
- `axis workspaces compare`
- `axis workspaces set-candidate`
- manifest synchronization caused by allowed run/compare operations

### Closed workspaces

For workspaces whose `status` is `closed`:

the following operations remain allowed:

- `axis workspaces show`
- `axis workspaces check`
- `axis workspaces sweep-result`
- workspace visualization

the following operations must be rejected:

- `axis workspaces run`
- `axis workspaces compare`
- `axis workspaces set-candidate`
- any future workspace command whose primary purpose is to mutate execution or
  comparison workflow state


## Closing A Workspace

AXIS must provide an explicit close operation:

- `axis workspaces close <workspace-path>`

### Required effect

Closing a workspace must:

- set `status` to `closed`
- set `lifecycle_stage` to `final`

### Allowed on

The close command is valid only for workspaces that are not already closed.

### Result

After a successful close:

- the workspace becomes read-only from an operational workflow perspective
- future run/compare/candidate-selection attempts must fail


## CLI Behavior

### `axis workspaces show`

Workspace summaries must continue to show:

- `status`
- `lifecycle_stage`

If the workspace is closed, the text output should make that easy to see.

### `axis workspaces check`

Workspace validation must include workflow validation.

At minimum:

- `status` must be one of the allowed values
- `lifecycle_stage` must be one of the allowed values

If a workspace is closed, `check` should not treat that as an error.

### `axis workspaces close`

Text output must clearly indicate that the workspace was closed.

JSON output must return machine-readable confirmation of the new workflow
state.


## Validation Rules

The manifest model must reject unknown `status` and `lifecycle_stage` values.

The workflow validator must treat `closed` as a valid final state.

No additional cross-field restriction is required in this version beyond:

- `status` must be valid
- `lifecycle_stage` must be valid

In particular:

- `completed + implementation` remains valid
- `active + final` is not recommended, but does not need to be rejected in
  this version unless AXIS later chooses stricter workflow consistency rules


## Compatibility

This specification changes the canonical built-in values for both workflow
enums.

Existing workspace manifests that still use removed workflow values are not
silently migrated in this version.

Instead:

- loading such a manifest must fail with a clear validation error
- the user is expected to update `workspace.yaml` explicitly

Removed status values:

- `idea`
- `running`

Added status values:

- `active`
- `closed`

Added lifecycle values:

- `analysis`
- `final`


## Out Of Scope Future Extensions

Possible future extensions include:

- `closed_at`
- `close_reason`
- `axis workspaces reopen`
- `axis workspaces set-status`
- `axis workspaces set-lifecycle`
- optional workflow profiles

These are not part of this specification.


## Summary

This specification turns workspace workflow metadata into a lightweight
operational policy layer.

The central rules are:

- `status` controls workflow permissions
- `lifecycle_stage` remains descriptive
- `closed` is the only blocking state
- `axis workspaces close` finalizes a workspace by setting:
  - `status: closed`
  - `lifecycle_stage: final`
