# Experiment Workspace -- Engineering Specification

## Possible Framework and Tooling Support

**Status:** Draft  
**Based on:** `experiment-workspace-spec.md`  
**Target version:** v0.4.0  
**Date:** 2026-04-17

---

## 1. Purpose

This document specifies a first engineering-oriented direction for supporting the AXIS Experiment Workspace concept in tooling and framework-adjacent infrastructure.

The goal is not to replace the existing AXIS execution model.

The goal is to add practical support around the existing system so that workspaces become easier to create, validate, execute, compare, and use consistently.

The first support layer should focus on:

- workspace scaffolding
- workspace validation and consistency checks
- workspace-aware execution routing
- workspace-aware comparison routing

These are the most useful first capabilities because they improve structure while preserving the current direct config-path execution model.

---

## 2. Scope

### In scope

- CLI-assisted workspace scaffolding
- manifest validation
- directory-structure validation
- linked-artifact existence checks
- consistency checks between workspace manifest and contained files
- workspace-aware execution output routing
- workspace-aware comparison output routing
- minimal summary/introspection support

### Out of scope

- removing or replacing the existing framework-root result mode
- automatic migration of existing result repositories into workspaces
- advanced workspace-aware execution scheduling
- public documentation generation
- comparison semantics

---

## 3. Engineering Principle

The first implementation should support the Experiment Workspace concept without collapsing it into the execution framework.

That means:

- workspaces remain filesystem-level organizational units
- `workspace.yaml` remains the authoritative workspace manifest
- the existing framework-root result mode remains valid
- a new workspace-owned result mode may additionally place artifacts directly into the workspace
- workspace tooling helps users create and validate structure
- workspace-local helper artifacts remain secondary to the manifest

Conceptually:

```text
axis CLI
  -> workspace scaffold
  -> workspace check
  -> workspace-aware run
  -> workspace-aware compare
  -> later workspace summary

framework execution
  -> existing raw results under experiments/results
  -> optional workspace-owned artifact placement

workspace
  -> authoritative manifest + configs + results + comparisons + measurements + notes
```

---

## 4. Proposed Support Areas

The first engineering pass should focus on five support areas.

### 4.1 Scaffolding

Create a new workspace with the correct directory structure and a valid initial `workspace.yaml`.

### 4.2 Validation

Check whether a workspace conforms to the Experiment Workspace specification.

### 4.3 Consistency Checks

Check whether the workspace's internal references and declared roles match its actual artifacts.

### 4.4 Summary / Introspection

Provide a lightweight way to inspect a workspace and understand:

- what it is
- what its primary configs are
- what its primary results and comparisons are
- what linked external artifacts it references, if any
- whether it appears complete

### 4.5 Workspace-Aware Execution and Comparison

Provide a new additive mode in which AXIS can:

- execute configs for a workspace and place raw execution artifacts under `results/`
- create comparison outputs for a workspace and place them under `comparisons/`
- update `workspace.yaml` so the manifest remains aligned with the produced workspace artifacts

This must coexist with the existing direct config-path mode rather than replacing it.

---

## 5. CLI Integration

The support should be exposed through the existing `axis` CLI.

This follows the established AXIS tool model:

- execution via `axis experiments ...`
- replay via `axis visualize ...`
- comparison via `axis compare ...`

Workspace support should follow the same pattern.

### 5.1 Recommended CLI Entity

Recommended new entity:

- `axis workspaces ...`

### 5.2 First Actions

Recommended initial actions:

- `axis workspaces scaffold`
- `axis workspaces check`
- `axis workspaces run`
- `axis workspaces compare`
- `axis workspaces show`

Optional later actions:

- `axis workspaces list`
- `axis workspaces export`
- `axis workspaces link-results`

### 5.3 CLI Role

The CLI remains a delegating entrypoint only.

This means:

- `src/axis/framework/cli.py` owns argument parsing and command dispatch
- workspace business logic does not live in the CLI
- workspace behavior is delegated into `src/axis/framework/workspaces/`

---

## 6. Scaffolding Support

Scaffolding is the highest-value first feature.

### 6.1 Purpose

Scaffolding should create a workspace skeleton that is structurally correct and ready for use.

### 6.2 User Experience

The scaffolding flow should behave like a guided assistant.

It should ask for or accept:

- workspace path or ID
- workspace class
- workspace type
- title
- status
- lifecycle stage
- type-specific required fields

Examples of type-specific prompts:

- for `system_development`:
  - artifact under development
  - development goal
- for `single_system`:
  - system under test
  - question
- for `system_comparison`:
  - reference system
  - candidate system
  - question

The first version should be explicitly **interactive** when launched from the CLI.

That means:

- `axis workspaces scaffold` starts a question-driven terminal flow
- the process prompts the user step by step
- the user does not need to pre-author a manifest manually

### 6.3 Output

Scaffolding should create:

- required directory tree
- initial `workspace.yaml`
- placeholder `README.md`
- placeholder `notes.md`
- required type-specific directories

It should also create initial executable config files.

#### Config creation rule

For `single_system` and development workspaces:

- scaffolding should create at least one baseline config

The default first baseline should be:

- `system-a-baseline.yaml`

unless the chosen workspace type or artifact target clearly requires a different initial baseline.

For `system_comparison`:

- scaffolding should create at least two executable configs

The first version may use:

- `system-a` vs `system-a`

as a valid default paired baseline, with differing parameter values if needed.

This is acceptable because the comparison model is role-based, not system-type-difference-based.

The important requirement is:

- two runnable configs exist immediately after scaffolding
- reference and candidate roles are explicit

This makes the scaffolded workspace directly usable.

### 6.4 First Command Shape

Possible form:

```text
axis workspaces scaffold
```

with either:

- interactive prompts
- or optional non-interactive flags later

The interactive prompt flow should be treated as the primary mode in version 1.

### 6.5 Why This Matters

Without scaffolding, users will drift into inconsistent layouts quickly.

Scaffolding turns the specification into something practically adoptable.

---

## 6.6 Terminal Framework Recommendation

Because scaffolding is interactive, the CLI should use a terminal interaction layer that supports:

- prompt-driven questioning
- validation feedback
- selection menus
- readable terminal formatting

### Recommended stack

The most pragmatic first choice is:

- `questionary` for interactive prompts
- `rich` for formatted terminal output

This combination is suitable because:

- `questionary` provides a clean question/answer flow for terminal applications
- `rich` improves readability for headings, summaries, warnings, and check results
- both fit well with a non-graphical CLI workflow

### Alternative options

Other reasonable options include:

- `InquirerPy`
- plain `prompt_toolkit`

But for AXIS v1 workspace support, the recommended engineering bias should be:

> prefer a lightweight prompt framework plus readable text rendering over a heavier full terminal UI

This means:

- do not build a TUI application first
- keep the scaffold as a guided CLI conversation

That matches the current AXIS tool style better.

### Dependency decision

The workspace scaffolding implementation should assume these additional
packages are available:

- `questionary`
- `rich`

---

## 7. Validation and Consistency Checks

Validation is the second highest-value support feature.

### 7.1 Purpose

Workspace checking should answer:

- is this workspace structurally valid?
- is the manifest valid?
- are the required directories present?
- are required fields present for the declared type?

### 7.2 Distinguish Syntax from Consistency

The tooling should distinguish two classes of checks.

#### Syntax / Structural Checks

Examples:

- `workspace.yaml` exists
- required fields exist
- directory structure is present
- class/type combination is valid

#### Consistency Checks

Examples:

- `workspace_class = development` but `engineering/` is missing
- `workspace_type = system_comparison` but only one config exists
- `linked_runs` refers to a missing run artifact
- `primary_configs` points to files that do not exist
- helper artifacts in `results/` or `comparisons/` contradict the manifest

### 7.3 First Command Shape

Possible form:

```text
axis workspaces check <workspace-path>
```

The output should support:

- text mode for humans
- JSON mode for automation

### 7.4 Validation Result Model

The check result should distinguish:

- valid
- invalid
- warnings

Warnings are useful for things that are not spec violations but may indicate incomplete work.

Examples:

- empty `measurements/` in an investigation workspace
- no linked runs yet
- no primary comparisons in a comparison workspace still in `draft`

---

## 8. Manifest Validation

The first implementation should treat `workspace.yaml` as a typed object.

### 8.1 Recommended Approach

Define a workspace manifest model in the framework or adjacent tooling layer.

This model should validate:

- required fields
- allowed enum values
- valid class/type combinations
- required type-specific fields

This model should be treated as the authoritative workspace representation for tooling purposes.

### 8.2 Benefit

This immediately gives:

- clear validation errors
- structured CLI feedback
- a stable internal representation for future workspace-aware tooling

### YAML library decision for manifest mutation

Workspace creation and mutation need two different YAML concerns:

- reading and validating YAML content
- updating `workspace.yaml` while preserving readability

`PyYAML` is sufficient for loading and basic parsing, but it does not preserve
comments or formatting during writeback.

For manifest synchronization and scaffolded manifest generation, the
recommended decision is:

- keep `PyYAML` for basic read paths
- use `ruamel.yaml` for write paths that must preserve comments, ordering, and readability

This should be treated as an explicit implementation dependency for the
workspace feature set.

---

## 9. Linked Artifact Checks

Because workspaces in v1 may reference existing framework-root artifacts or own artifacts placed directly in the workspace, artifact validation should be part of the first support layer.

### 9.1 What Should Be Checked

If present, the checker should validate:

- `linked_experiments`
- `linked_runs`
- `linked_comparisons`
- files listed under `primary_configs`
- files listed under `primary_results`
- files listed under `primary_comparisons`
- files listed under `primary_measurements`

If helper artifacts exist under `results/` or `comparisons/`, the checker may validate them as auxiliary artifacts, but must not treat them as the primary source of workspace semantics.

### 9.2 Type of Check

Version 1 only needs existence and basic shape checks.

It does not need deep semantic interpretation of linked artifacts.

This means:

- file exists
- path resolves
- JSON/YAML files are readable where appropriate

That is enough for a first support layer.

### 9.3 Helper Artifact Policy

Version 1 should explicitly distinguish between:

- authoritative workspace metadata
- workspace-local helper artifacts

The engineering implementation should therefore assume:

- `workspace.yaml` is authoritative
- helper files in `results/` and `comparisons/` are optional, non-normative, and convenience-oriented

This means the tooling should:

- never require such helper files for workspace validity
- never infer authoritative semantics from them when the manifest already provides the same information
- only check them for contradiction, existence, and basic readability where useful

---

## 10. Additional Practical Support Ideas

Beyond scaffolding and checks, there are a few useful low-risk support features.

### 9.4 Workspace-Aware Output Mode

The engineering layer should support a new additive workspace-aware mode.

This mode must not remove or alter the existing direct execution flow:

- `axis experiments run <config>`

Instead, it should add workspace-oriented entry points such as:

- `axis workspaces run <workspace-path>`
- `axis workspaces compare <workspace-path>`

In this mode:

- raw execution artifacts for the workspace should be placed under `results/`
- comparison artifacts for the workspace should be placed under `comparisons/`
- derived or summarized outputs should be placed under `measurements/`
- `workspace.yaml` should be updated to reflect the current primary artifacts produced by the workspace flow

### 10.1 Workspace Summary

Command idea:

```text
axis workspaces show <workspace-path>
```

This would print:

- workspace class and type
- title
- status
- lifecycle stage
- primary configs
- linked experiments/runs
- whether required directories and files are present

The summary should present the manifest as the canonical workspace description, and helper artifacts only as supplementary local files.

This is useful even before richer automation exists.

### 10.2 Config Count and Role Check

For investigation workspaces, especially `system_comparison`, a checker should validate role completeness.

Examples:

- two configs expected in comparison workspaces
- `reference` and `candidate` roles should both be represented

### 10.3 Manifest/Directory Drift Detection

Useful warning if:

- manifest points to files that are missing
- files exist that are likely primary artifacts but are not declared
- helper artifacts appear to disagree with the manifest

This is not strictly required for v1, but it would be very valuable.

### 10.4 Workspace Readiness Check

A later lightweight readiness classification could be useful:

- structurally valid
- execution-ready
- analysis-ready

This is not required yet, but it is a natural extension of `axis workspaces check`.

---

## 11. Proposed Package Placement

A first implementation could live under:

- `src/axis/framework/workspaces/`

Suggested initial modules:

| File | Purpose |
|---|---|
| `types.py` | Workspace manifest model(s) |
| `validation.py` | Structural and consistency checks |
| `scaffold.py` | Workspace skeleton generation |
| `resolution.py` | Workspace run-resolution helpers |
| `execute.py` | Workspace-aware run orchestration |
| `visualization.py` | Workspace-aware replay target resolution |
| `compare_resolution.py` | Workspace-aware comparison target resolution |
| `compare.py` | Workspace-aware comparison orchestration |
| `sync.py` | Controlled manifest update helpers |
| `drift.py` | Stronger post-execution consistency helpers |
| `summary.py` | Workspace summary helpers |
| `__init__.py` | Exports |

This keeps workspace support separate from:

- replay comparison
- experiment execution
- visualization

while still placing it close enough to the framework tooling layer.

Helper artifact parsing, if added, should remain optional and subordinate to the typed manifest layer.

The central CLI module remains:

- `src/axis/framework/cli.py`

It should delegate into `framework/workspaces/` rather than hosting workspace logic itself.

---

## 12. First Work Package Direction

If this concept moves into implementation, the first work packages should be:

1. Workspace manifest type model
2. Workspace checker
3. Workspace scaffolder
4. Workspace summary / show
5. Workspace run resolution
6. Workspace execution routing
7. Workspace visualization resolution
8. Workspace compare resolution
9. Workspace comparison routing
10. Manifest synchronization
11. Drift detection
12. Integration hardening

This order is important.

The checker and typed manifest should come before the scaffolder, so the scaffolder can be built against a validated target structure.

CLI integration is intentionally not a standalone work package in this model.

Instead, CLI delegation is introduced incrementally in the workspace-facing
feature packages:

- scaffold
- show
- run
- visualize
- compare

---

## 13. Acceptance Criteria for First Support Pass

The first workspace-support implementation should be considered successful if:

- a user can scaffold a valid workspace for any v1 workspace type
- `axis workspaces check` can validate a workspace against the spec
- the checker can distinguish errors from warnings
- linked artifact paths are checked for existence
- manifest authority is preserved in the implementation model
- the existing simple result-root-based mode still works unchanged
- the workspace-aware mode can place execution artifacts directly into `results/`
- the workspace-aware mode can place comparison artifacts directly into `comparisons/`
- `axis workspaces show` can summarize a workspace meaningfully

---

## 14. Summary

The first practical framework/tooling support for Experiment Workspaces should stay narrow and high-value.

The primary features should be:

- guided scaffolding
- syntax and consistency checks
- workspace-aware execution routing
- workspace-aware comparison routing

Additional useful support includes:

- workspace summary
- linked-artifact existence checking
- role completeness checks
- manifest/directory drift warnings

This gives AXIS a practical on-ramp into structured workspaces without forcing early changes into the execution core.
