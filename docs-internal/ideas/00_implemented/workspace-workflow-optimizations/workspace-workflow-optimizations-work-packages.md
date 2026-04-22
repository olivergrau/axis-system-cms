# Workspace Workflow Optimizations Work Packages

## Purpose

This document defines a first coarse-grained implementation roadmap for the
workspace workflow optimization effort.

It is derived from:

- `workspace-workflow-optimizations-spec.md`
- `workspace-workflow-optimizations-engineering-spec.md`

The goal is not to fully re-specify implementation details.

The goal is to define a pragmatic delivery structure that can be executed by
human contributors or coding agents in bounded packages.

---

## 1. Implementation Goal

The first implementation goal is:

> make workspace workflow state operationally meaningful by tightening the
> built-in workflow enums, introducing explicit workspace closing, and blocking
> mutating workspace operations once a workspace is closed

This means:

- `status` becomes an enforcement field rather than passive metadata
- `lifecycle_stage` remains descriptive but is updated to the new canonical set
- workspaces can be explicitly closed
- closed workspaces remain inspectable but become operationally read-only
- old removed workflow values fail clearly instead of being silently mapped

---

## 2. Delivery Strategy

The recommended delivery strategy is incremental.

Do not attempt to change the full workspace surface in one pass.

Instead, deliver the workflow layer in stages:

1. manifest enum and schema update
2. close mutation and workflow service
3. CLI close command integration
4. service-layer closed-workspace enforcement
5. summary, validation, and scaffolding alignment
6. tests, fixture updates, and hardening

This keeps the most invasive model changes early, while postponing broad test
churn until the workflow behavior is stable.

---

## 3. Proposed Work Package Structure

### WP-01 Workflow Enum And Manifest Update

Update the canonical workflow enums and manifest validation behavior.

Primary scope:

- `WorkspaceStatus`
- `WorkspaceLifecycleStage`
- explicit rejection of removed legacy values
- manifest model tests

Primary outcome:

- the manifest layer defines the new workflow semantics cleanly and fails fast
  on deprecated state values

---

### WP-02 Close Mutation And Workflow Service

Add the manifest mutation and service layer for closing workspaces.

Primary scope:

- manifest mutator support for closing
- new workflow service
- roundtrip manifest update behavior

Primary outcome:

- AXIS has one canonical implementation path for closing a workspace

---

### WP-03 CLI Close Command Integration

Expose workspace closing as a first-class CLI action.

Primary scope:

- parser wiring
- CLI context wiring
- `cmd_workspaces_close(...)`
- text and JSON output behavior

Primary outcome:

- users can explicitly close workspaces through the CLI

---

### WP-04 Closed-Workspace Enforcement In Services

Block mutating workflow operations when a workspace is closed.

Primary scope:

- `WorkspaceRunService.execute(...)`
- `WorkspaceRunService.set_candidate(...)`
- `WorkspaceCompareService.compare(...)`

Primary outcome:

- closed workspaces are operationally read-only for execution/comparison flows

---

### WP-05 Summary, Validation, And Scaffolding Alignment

Align read-only surfaces and workspace creation with the new workflow model.

Primary scope:

- `workspaces show`
- validation expectations
- scaffold status/lifecycle choices and defaults
- any wording updates needed in workflow-facing summaries

Primary outcome:

- the new workflow model is visible and coherent across creation, checking, and
  inspection

---

### WP-06 Test Hardening, Fixture Migration, And Documentation Touch-Ups

Update tests and shipped workspace examples to the new canonical states.

Primary scope:

- parser / CLI / service / validation test coverage
- existing workspace fixture manifests
- docs/help text touched by the workflow rename

Primary outcome:

- the new workflow model is stable, and removed legacy values are exercised by
  explicit failing tests

---

## 4. Suggested Execution Order

The recommended order is:

1. `WP-01`
2. `WP-02`
3. `WP-03`
4. `WP-04`
5. `WP-05`
6. `WP-06`

`WP-06` should begin partially earlier if tests are written alongside each
package, but it should still exist as a distinct hardening pass.

---

## 5. Suggested Dependency Logic

- `WP-01` must land first because all later workflow behavior depends on the
  canonical enum set.
- `WP-02` depends on `WP-01` because closing must write the new canonical
  values.
- `WP-03` depends on `WP-02` because the CLI close command should call the
  canonical workflow service.
- `WP-04` depends on `WP-01` and should ideally land after `WP-02`, since all
  gating logic needs the new closed semantics.
- `WP-05` depends on `WP-01` and should preferably follow `WP-03`/`WP-04` so
  the visible workflow model matches real behavior.
- `WP-06` depends on all previous packages.

---

## 6. Verification Goal

After completing all work packages:

1. Workspaces accept only the new canonical `status` and `lifecycle_stage`
   values.
2. Removed values such as `idea` and `running` fail with clear validation
   errors.
3. `axis workspaces close <workspace>` updates the manifest correctly.
4. Closed workspaces reject run, compare, and candidate-selection operations.
5. Closed workspaces still support show, check, sweep-result, and
   visualization.
6. Scaffolded workspaces start with the new workflow defaults.
