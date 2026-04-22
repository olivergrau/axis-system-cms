# Workspace Workflow Optimizations Draft

## Purpose

This draft explores how to make AXIS workspaces more operationally useful as
long-lived working contexts rather than just structured folders with metadata.

The immediate motivation is:

- the current workspace model already records `status` and `lifecycle_stage`
- but those fields are mostly descriptive today
- and the workflow does not yet provide a first-class notion of freezing or
  closing a workspace once it reaches a final state

So the real opportunity is not only to add more states, but to make workspace
state meaningful to execution, comparison, and maintenance commands.


## Starting Point

AXIS already has a substantial workspace model in place.

The current implementation includes:

- a typed workspace manifest model in
  `src/axis/framework/workspaces/types.py`
- fixed enums for:
  - `workspace_class`
  - `workspace_type`
  - `status`
  - `lifecycle_stage`
- workspace-aware commands:
  - `axis workspaces scaffold`
  - `axis workspaces check`
  - `axis workspaces show`
  - `axis workspaces run`
  - `axis workspaces compare`
  - `axis workspaces sweep-result`
  - development-specific candidate selection
- handler-based workspace-type behavior:
  - `single_system`
  - `system_comparison`
  - `system_development`
- manifest synchronization after run and compare

This means the problem is **not** that AXIS lacks workflow structure.

The problem is that workflow state is only weakly connected to command
semantics.


## What Exists Today

The current manifest defines these workflow enums:

- `WorkspaceStatus`
  - `idea`
  - `draft`
  - `running`
  - `analyzing`
  - `completed`
- `WorkspaceLifecycleStage`
  - `idea`
  - `draft`
  - `spec`
  - `implementation`
  - `documentation`

These fields are:

- required in the manifest
- shown in `axis workspaces show`
- selectable in `axis workspaces scaffold`

But today they are **not** used as operational guardrails for the main
workspace commands.

In practice:

- `axis workspaces run` does not check whether the workspace is still open
- `axis workspaces compare` does not check whether the workspace is finalized
- `axis workspaces check` validates structure and artifact consistency, but not
  workflow policy
- there is no built-in command to transition a workspace into an explicitly
  closed/final state


## Core Idea

The right optimization is probably to introduce a small **workspace workflow
policy layer**.

That layer should answer questions like:

- which states exist for a workspace
- which transitions are allowed
- which commands are permitted in each state
- how a workspace becomes final / closed

This would turn `status` and `lifecycle_stage` from passive metadata into a
lightweight state machine for workspace operations.


## Recommended Direction

The recommended direction is **not** to start with fully arbitrary
user-defined state machines.

That would be much more flexible, but also much more expensive in:

- validation complexity
- CLI complexity
- test surface
- compatibility guarantees

A better first step is:

- keep the current built-in workflow fields
- introduce an explicit `is_closed` or equivalent finalization concept
  through workflow policy
- add a small set of operational rules for run / compare / mutate commands
- optionally allow limited workflow-profile customization later

So the proposed rollout should likely be:

1. clarify and tighten the built-in states
2. define command permissions against those states
3. add a close/finalize command
4. only then consider configurable workflow schemes


## Why “Configurable States” Needs Care

The kickoff suggests making states configurable so a workspace is adaptable.

That is a reasonable long-term idea, but in the current AXIS architecture
there is an important distinction between:

- **configurable labels**
- and **configurable workflow semantics**

Labels alone are cheap but low-value.

Semantics are valuable, but they create real system behavior:

- validation must know what states are legal
- scaffolding must know what defaults to create
- the CLI must know which commands are blocked or allowed
- summaries and checks must know which states count as active or final

Because of that, fully user-defined workflow states are probably too large a
first implementation target.

The cleaner first-wave compromise is:

- keep a framework-owned canonical workflow model
- maybe allow optional workspace-specific aliases or profiles later
- but do not immediately make the state machine freeform


## Proposed First-Wave Semantics

The current states are close, but they need clearer meaning.

Recommended interpretation:

### `status`

`status` should answer:

> what is the current operational state of the workspace?

Recommended built-in values:

- `draft`
  - workspace exists but is not yet actively producing results
- `active`
  - workspace is open for runs, comparisons, and normal updates
- `analyzing`
  - workspace is still open, but the main focus is interpretation rather than
    execution
- `completed`
  - workspace has reached a natural endpoint but is not necessarily frozen yet
- `closed`
  - workspace is finalized; no new executions or comparisons should be allowed

This suggests replacing or refining the current `idea` / `running` split:

- `idea` overlaps too much with `draft`
- `running` describes an activity, not a durable workspace state

### `lifecycle_stage`

`lifecycle_stage` should answer:

> where is the workspace in its intellectual or engineering lifecycle?

This can remain descriptive and relatively stable:

- `idea`
- `draft`
- `spec`
- `implementation`
- `analysis`
- `documentation`
- `final`

That gives lifecycle a clearer narrative role while leaving operational
permissions mostly to `status`.


## Closing A Workspace

The kickoff’s strongest concrete suggestion is to add a way to close a
workspace so no further experiments are possible.

This is a strong fit for the current architecture.

Recommended behavior:

- add a command such as:
  - `axis workspaces close <workspace-path>`
- this updates the manifest to a final operational state
- after closing:
  - `axis workspaces run` should fail
  - `axis workspaces compare` should fail
  - mutating workflow commands should fail unless an explicit reopen command is
    introduced later
- read-only commands should still work:
  - `show`
  - `check`
  - `sweep-result`
  - visualization

The close operation should be explicit and visible in `workspace.yaml`.


## Operational Guardrails

Once workflow state is meaningful, the workspace services should enforce it.

The clean integration points are likely:

- `WorkspaceRunService.execute(...)`
- `WorkspaceCompareService.compare(...)`
- manifest-mutating commands and helpers

The likely rule set is:

- open states:
  - run allowed
  - compare allowed
  - manifest sync allowed
- closed state:
  - read-only inspection allowed
  - new run / compare / candidate updates blocked

This keeps policy enforcement near the orchestration layer rather than burying
it inside individual CLI command functions.


## Scope Of First Implementation

A pragmatic first implementation should probably include:

- refinement of the built-in `WorkspaceStatus` enum
- refinement of the built-in `WorkspaceLifecycleStage` enum
- explicit workflow validation rules
- a close/finalize workspace command
- enforcement in run and compare services
- clearer CLI presentation of whether a workspace is open or closed

This would already produce a meaningful workflow improvement without forcing a
large redesign of workspace manifests.


## Suggested Manifest Direction

The existing manifest model already has the right location for workflow data:

- `status`
- `lifecycle_stage`

So the draft recommendation is to **extend semantics, not add a parallel
workflow block**, at least in the first wave.

Possible later extension:

- optional `workflow_profile`
- optional `closed_at`
- optional `close_reason`

Those would be useful, but they are not required for the minimal feature.


## Suggested Command Additions

Likely useful first-wave commands:

- `axis workspaces close <workspace-path>`

Possibly later:

- `axis workspaces reopen <workspace-path>`
- `axis workspaces set-status <workspace-path> <status>`
- `axis workspaces set-lifecycle <workspace-path> <stage>`

For the first implementation, `close` is the highest-value command because it
introduces a real operational capability instead of generic metadata editing.


## Alignment With Current Architecture

This proposal fits the current workspace design well because:

- the manifest is already authoritative
- manifest mutation already exists through mutator and sync utilities
- the service layer already centralizes run and compare orchestration
- `show` already surfaces workflow fields
- `check` already performs policy-like validation and can be extended

So the implementation does not require a new subsystem.

It is mainly:

- enum/model refinement
- workflow validation
- service-layer command gating
- one or two new manifest mutation utilities
- a CLI entry point


## Recommended First Draft Outcome

The best first implementation target is:

> make workspaces operationally closable and give `status` / `lifecycle_stage`
> clearer semantics, while keeping workflow configuration framework-owned for
> now

That is much more implementable than “fully configurable workspace states,”
and it solves the main practical need expressed in the kickoff.


## Steering Questions

There are still a few design choices worth deciding explicitly before turning
this into a spec.

### 1. Should closed workspaces be strictly immutable?

Options:

- strict:
  - no run
  - no compare
  - no candidate switching
  - no manifest mutation except explicit reopen
- moderate:
  - no run
  - no compare
  - but allow metadata edits

Recommended first-wave answer:

- strict for workflow-affecting commands
- tolerant for manual metadata edits outside the CLI

Final Decision: 

- strict please
- but if the user edits the workspace.yaml outside of the CLI than he can restore or change behavior


### 2. Do we need both `completed` and `closed`?

This is the biggest semantic question.

Possible distinction:

- `completed` means “we believe the work is done”
- `closed` means “the workspace is administratively frozen”

If that distinction does not matter in practice, one of them could be dropped.

Recommended first-wave answer:

- keep both only if we want a visible pre-freeze completion state
- otherwise collapse to a single final state

Final Decision: 

- remove completed please. Closed is sufficient.

### 3. Should workflow be configurable per workspace in v1?

Recommended answer:

- no, not fully
- keep built-in semantics in v1
- revisit customization only after the close/finalize workflow proves useful

Final Decision: 

- recommended answer accepted

### 4. Should lifecycle block commands, or only status?

Recommended answer:

- `status` should carry command permissions
- `lifecycle_stage` should remain descriptive

That keeps the model understandable and reduces contradictory combinations.

Final Decision: 

- recommended answer accepted

## Summary

The kickoff points to a real need, but the most effective implementation is
slightly narrower than the initial wording suggests.

The current AXIS workspace system already has workflow metadata.
What it lacks is:

- clearer semantics
- operational enforcement
- a formal way to finalize a workspace

So the recommended next step is to specify:

- a tightened built-in workflow model
- a close/finalize command
- service-layer enforcement for closed workspaces
- optional future extension points for workflow customization
