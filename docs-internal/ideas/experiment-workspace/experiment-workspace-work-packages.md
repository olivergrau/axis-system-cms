# Experiment Workspace -- Implementation Roadmap

## Purpose

This document defines a first coarse-grained implementation roadmap for
introducing AXIS workspace support.

It is derived from:

- `experiment-workspace-spec.md`
- `experiment-workspace-engineering-spec.md`

The goal of this document is not to fully specify implementation details.

The goal is to define a pragmatic delivery structure that can later be
expanded into detailed implementation work packages for Codex, Claude Code,
or human engineering work.

---

## 1. Implementation Goal

The first implementation goal is:

> introduce workspace-aware tooling into AXIS without removing the existing
> direct config-path execution model

This means:

- the existing AXIS mode remains valid
- a new workspace-aware mode is added
- workspaces become a first-class operational context
- `workspace.yaml` becomes the canonical workspace manifest

The first supported workspace-oriented user flow should eventually allow:

1. scaffold a valid workspace
2. validate and inspect it
3. execute it through `axis workspaces run`
4. compute comparisons through `axis workspaces compare`
5. keep produced artifacts and manifest state coherent inside the workspace

---

## 2. Delivery Strategy

The recommended delivery strategy is incremental.

Do not attempt to build the entire workspace system in one pass.

Instead, introduce support in layers:

1. typed manifest and validation foundation
2. scaffolding and inspection support
3. workspace-aware execution routing
4. workspace-aware comparison routing
5. manifest update and consistency support
6. integration hardening and documentation

This keeps early implementation risk low while ensuring that each stage
produces a usable capability.

---

## 3. Proposed Work Package Structure

### WP-01 Manifest Model

Implement the typed representation of `workspace.yaml`.

Primary scope:

- workspace manifest type model
- enum validation
- class/type validation
- required field validation
- type-specific field validation

Primary outcome:

- AXIS can load and validate a workspace manifest as a structured object

---

### WP-02 Workspace Checker

Implement structural and semantic checking for workspaces.

Primary scope:

- validate required directories
- validate required files
- validate primary artifact references
- validate optional linked artifact references
- distinguish errors and warnings

Primary outcome:

- `axis workspaces check <workspace-path>` becomes possible

---

### WP-03 Workspace Scaffolder

Implement interactive creation of valid workspaces.

Primary scope:

- interactive CLI prompt flow
- workspace directory creation
- `workspace.yaml` generation
- baseline config generation
- type-specific skeleton generation

Primary outcome:

- `axis workspaces scaffold` creates a valid initial workspace

---

### WP-04 Workspace Summary / Show

Implement a read-oriented workspace introspection command.

Primary scope:

- workspace summary rendering
- manifest summary
- primary artifact summary
- validation state summary
- human-readable CLI output

Primary outcome:

- `axis workspaces show <workspace-path>` becomes possible

---

### WP-05 Workspace Run Resolution

Implement workspace-to-config resolution for execution.

Primary scope:

- resolve the executable config set from `workspace.yaml`
- support `single_system`
- support `system_comparison`
- support development workspaces with validation configs
- define execution target selection rules

Primary outcome:

- AXIS can interpret a workspace as an execution target

---

### WP-06 Workspace Execution Routing

Implement workspace-aware execution result placement.

Primary scope:

- add `axis workspaces run <workspace-path>`
- route produced execution artifacts into `results/`
- preserve separation from `measurements/` and `comparisons/`
- keep compatibility with the existing AXIS execution stack

Primary outcome:

- workspace execution artifacts can be created inside the workspace

---

### WP-07 Workspace Visualization Resolution

Implement workspace-to-replay resolution for visualization.

Primary scope:

- resolve a replay target from workspace state
- support `single_system`
- support reference/candidate role selection for `system_comparison`
- define default episode and artifact selection rules

Primary outcome:

- AXIS can interpret a workspace as a visualization target

---

### WP-08 Workspace Compare Resolution

Implement workspace-to-comparison resolution.

Primary scope:

- resolve reference/candidate artifacts from workspace state
- define comparison target selection rules
- support `system_comparison`
- support development workspaces where comparisons are secondary validation artifacts

Primary outcome:

- AXIS can interpret a workspace as a comparison target

---

### WP-09 Workspace Comparison Routing

Implement workspace-aware comparison output placement.

Primary scope:

- add `axis workspaces compare <workspace-path>`
- place comparison artifacts under `comparisons/`
- preserve separation from raw execution artifacts and measurements
- support future system-specific comparison extensions

Primary outcome:

- comparison outputs can be generated directly into the workspace

---

### WP-10 Manifest Synchronization

Implement controlled updates to `workspace.yaml` after workspace-aware
execution and comparison actions.

Primary scope:

- update primary artifact fields where appropriate
- preserve manifest authority
- prevent stale primary artifact references
- define overwrite/update rules

Primary outcome:

- workspace tools keep `workspace.yaml` aligned with produced artifacts

---

### WP-11 Consistency and Drift Detection

Implement stronger consistency checks once execution and comparison routing
exist.

Primary scope:

- detect missing declared artifacts
- detect undeclared likely-primary artifacts
- detect mismatch between manifest and workspace content
- detect invalid role completeness in comparison workspaces

Primary outcome:

- AXIS can diagnose workspace drift after real usage

---

### WP-12 Integration Hardening

Harden the new workspace toolchain against real repository usage.

Primary scope:

- end-to-end CLI validation
- persisted artifact checks
- error handling and recovery
- compatibility checks against the old AXIS mode

Primary outcome:

- workspace support is stable enough for regular usage

---

### WP-13 Public Documentation and Examples

Document the implemented workspace flow after the tooling stabilizes.

Primary scope:

- update public docs
- add CLI examples
- document workspace usage patterns
- align public examples with implemented command behavior

Primary outcome:

- workspace support becomes teachable and discoverable

---

## 4. Recommended Execution Order

The recommended implementation order is:

1. `WP-01 Manifest Model`
2. `WP-02 Workspace Checker`
3. `WP-03 Workspace Scaffolder`
4. `WP-04 Workspace Summary / Show`
5. `WP-05 Workspace Run Resolution`
6. `WP-06 Workspace Execution Routing`
7. `WP-07 Workspace Visualization Resolution`
8. `WP-08 Workspace Compare Resolution`
9. `WP-09 Workspace Comparison Routing`
10. `WP-10 Manifest Synchronization`
11. `WP-11 Consistency and Drift Detection`
12. `WP-12 Integration Hardening`
13. `WP-13 Public Documentation and Examples`

This order is recommended because:

- typed manifest support is foundational
- checking and scaffolding should exist before execution writes data
- comparison support depends on run support
- manifest synchronization should be built after artifact creation behavior is clear
- public docs should follow stable behavior, not precede it

---

## 5. Parallelization Opportunities

Some work packages can later be executed in parallel.

### Early parallelization

After `WP-01`:

- `WP-02 Workspace Checker`
- `WP-03 Workspace Scaffolder`
- `WP-04 Workspace Summary / Show`

### Mid-stage parallelization

After `WP-05`:

- `WP-06 Workspace Execution Routing`
- `WP-07 Workspace Visualization Resolution`
- `WP-08 Workspace Compare Resolution`

### Late parallelization

After `WP-09` and `WP-10`:

- `WP-11 Consistency and Drift Detection`
- `WP-12 Integration Hardening`

`WP-13` should remain late because it depends on stabilized user-facing behavior.

---

## 6. Suggested First Milestone

The first useful milestone should be:

> a user can scaffold, validate, inspect, and execute a workspace

This milestone includes:

- `WP-01`
- `WP-02`
- `WP-03`
- `WP-04`
- `WP-05`
- `WP-06`

This is the smallest milestone that makes the workspace operational rather
than merely descriptive.

---

## 7. Suggested Second Milestone

The second useful milestone should be:

> a user can compare through the workspace and keep the workspace coherent

This milestone includes:

- `WP-07`
- `WP-08`
- `WP-09`
- `WP-10`
- `WP-11`

This turns the workspace from an execution container into a full experiment
and comparison workspace.

---

## 8. Suggested Third Milestone

The third useful milestone should be:

> workspace support is stable, checked, and publicly documented

This milestone includes:

- `WP-12`
- `WP-13`

---

## 9. Non-Goals of This Roadmap

This roadmap does not yet define:

- exact module boundaries
- exact CLI argument syntax
- exact artifact naming conventions inside `results/`
- exact comparison payload schemas
- exact manifest mutation rules
- test case inventories

These belong in the later detailed work-package documents.

---

## 10. Summary

The recommended workspace implementation roadmap is:

- build the manifest foundation first
- add scaffold/check/show early
- introduce workspace-aware run next
- introduce workspace-aware compare after that
- then add manifest synchronization and drift handling
- harden and document only after the flow is stable

This gives AXIS a controlled path from specification to practical
workspace-centered tooling without destabilizing the existing framework model.
