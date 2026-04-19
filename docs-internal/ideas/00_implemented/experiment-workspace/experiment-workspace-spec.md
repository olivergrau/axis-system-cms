# AXIS - Experiment Workspace Specification

## Version 1 Draft Specification

---

## 1. Purpose

This document defines version 1 of the AXIS **Experiment Workspace** specification.

The purpose of the Experiment Workspace is to provide a structured container for AXIS work contexts that bundle:

- intent
- configuration inputs
- execution outputs
- comparisons
- measurements
- notes
- and, where applicable, concept and engineering artifacts

The Experiment Workspace is intended to organize AXIS work above the level of individual run configurations and raw AXIS execution artifacts.

---

## 2. Scope

This specification defines:

- the Experiment Workspace model
- workspace classification
- the workspace manifest `workspace.yaml`
- required and optional workspace fields
- required directory structure
- minimum required contents by workspace type
- the relationship between workspace-local artifacts and AXIS execution outputs in both supported result-placement modes

This specification does not define:

- framework execution behavior
- source code placement
- workspace-aware CLI behavior
- workspace-aware framework persistence
- statistical analysis semantics
- comparison result schemas

---

## 3. Normative Terms

The terms **must**, **must not**, **should**, and **may** are to be interpreted normatively.

---

## 4. Core Model

An Experiment Workspace is a bounded filesystem-level context for one coherent AXIS work unit.

An Experiment Workspace is not identical to:

- a framework experiment
- a run
- a comparison
- or a run configuration file

Instead, it is the higher-level structure that groups the artifacts relevant to one coherent line of work.

---

## 5. Workspace Classification

Every Experiment Workspace must define two explicit classification fields:

- `workspace_class`
- `workspace_type`

### 5.1 Workspace Class

Version 1 allows exactly these values:

- `development`
- `investigation`

### 5.2 Workspace Type

Version 1 allows exactly these values:

- under `development`:
  - `system_development`
  - `world_development`
- under `investigation`:
  - `single_system`
  - `system_comparison`

### 5.3 Valid Class-Type Combinations

The following combinations are valid:

- `development` + `system_development`
- `development` + `world_development`
- `investigation` + `single_system`
- `investigation` + `system_comparison`

All other combinations are invalid in version 1.

---

## 6. Development vs Investigation

### 6.1 Development

A development workspace is a workspace whose primary purpose is to create or structurally modify an artifact.

In version 1, the supported development artifact kinds are:

- system
- world

Development workspaces may contain:

- conceptual modeling
- engineering planning
- validation runs
- comparison evidence
- measurements

### 6.2 Investigation

An investigation workspace is a workspace whose primary purpose is to study already existing artifacts under defined conditions.

In investigation, the examined systems and worlds must not be structurally modified as part of the workspace purpose.

Variation is allowed only through:

- configuration
- execution
- comparison
- measurement
- interpretation

### 6.3 Secondary Investigation in Development

Development workspaces may contain investigation-like artifacts such as:

- baseline runs
- comparisons against references
- measurements

These are allowed as secondary validation material.

---

## 7. Workspace Manifest

Every Experiment Workspace must contain a manifest file named:

- `workspace.yaml`

This file is the workspace manifest.

### 7.1 Role of the Manifest

The manifest defines:

- workspace identity
- workspace classification
- workspace purpose
- involved artifacts
- primary artifacts
- current process state

### 7.2 What the Manifest Is Not

The manifest is not:

- a run configuration file
- a framework experiment config
- a comparison result payload

Executable run configuration files remain separate artifacts stored under `configs/`.

---

## 8. Required Manifest Fields

Every workspace manifest must contain the following fields:

- `workspace_id`
- `title`
- `workspace_class`
- `workspace_type`
- `status`
- `lifecycle_stage`
- `created_at`

### 8.1 `status`

Version 1 allows these values:

- `idea`
- `draft`
- `running`
- `analyzing`
- `completed`

### 8.2 `lifecycle_stage`

Version 1 allows these values:

- `idea`
- `draft`
- `spec`
- `implementation`
- `documentation`

`status` and `lifecycle_stage` must be treated as distinct fields.

### 8.3 Semantic Boundary Between `status` and `lifecycle_stage`

The two fields serve different purposes.

`status` describes the **operational state of the workspace**.

Typical questions answered by `status`:

- Is this workspace still being drafted?
- Is execution currently happening?
- Are results currently being analyzed?
- Is this workspace considered done for now?

`lifecycle_stage` describes the **maturity of the primary artifact or workstream** represented by the workspace.

Typical questions answered by `lifecycle_stage`:

- Is this still only an idea?
- Has a draft been written?
- Has a specification been produced?
- Has implementation begun?
- Has documentation been produced?

These fields may therefore legitimately differ.

Examples:

- `status: draft`, `lifecycle_stage: spec`
- `status: running`, `lifecycle_stage: implementation`
- `status: analyzing`, `lifecycle_stage: documentation`

---

## 9. Required Purpose Fields

### 9.1 Investigation

For all investigation workspaces, the manifest must contain:

- `question`

### 9.2 Development

For all development workspaces, the manifest must contain:

- `development_goal`

The complementary field may exist, but is not required.

---

## 10. Required Artifact Fields by Workspace Type

### 10.1 `system_development`

The manifest must contain:

- `artifact_kind`
- `artifact_under_development`

where:

- `artifact_kind` must equal `system`

### 10.2 `world_development`

The manifest must contain:

- `artifact_kind`
- `artifact_under_development`

where:

- `artifact_kind` must equal `world`

### 10.3 `single_system`

The manifest must contain:

- `system_under_test`

### 10.4 `system_comparison`

The manifest must contain:

- `reference_system`
- `candidate_system`

`reference_system` and `candidate_system` may be equal system types if the comparison distinguishes configurations rather than system family.

Examples that remain valid:

- `System A` vs `System A`
- `System C` vs `System C`

provided the workspace still represents a meaningful comparison under distinct reference/candidate roles.

---

## 11. Optional Manifest Fields

Version 1 allows at least the following optional fields:

- `description`
- `tags`
- `baseline_artifacts`
- `validation_scenarios`
- `primary_configs`
- `primary_results`
- `primary_comparisons`
- `primary_measurements`
- `linked_experiments`
- `linked_runs`
- `linked_comparisons`

These fields may be omitted if not applicable.

In workspace-owned mode, the `primary_*` fields are the primary way to point to
the workspace's own artifacts.

In framework-root mode, the `linked_*` fields remain useful when the workspace
needs to reference external AXIS execution artifacts explicitly.

### 11.1 `baseline_artifacts`

In version 1, `baseline_artifacts` should be treated as a freeform descriptive label list.

It is intended to record baseline references in a lightweight way.

Typical values may include:

- system type strings
- world type strings
- workspace-local labels

Version 1 does not require a stricter identifier schema.

### 11.2 `validation_scenarios`

In version 1, `validation_scenarios` should also be treated as a freeform descriptive label list.

It is intended to record the names of validation contexts relevant to the workspace.

Typical values may include:

- scenario labels
- baseline labels
- comparison labels

Version 1 does not require a stricter scenario schema.

---

## 12. Required Directory Structure

Every Experiment Workspace must contain at least the following top-level items:

- `workspace.yaml`
- `README.md`
- `notes.md`
- `configs/`
- `results/`
- `comparisons/`
- `measurements/`
- `exports/`

### 12.1 Shared Optional Top-Level Directories

The following directories are part of the version 1 shared workspace model:

- `concept/`
- `engineering/`

Their requirement status depends on workspace type.

---

## 13. Directory Semantics

### 13.1 `configs/`

Must contain executable configuration files relevant to the workspace.

### 13.2 `results/`

Must contain workspace-level execution result artifacts.

Version 1 supports two result-placement modes:

- existing framework-root mode
- workspace-owned mode

In framework-root mode, `results/` may contain workspace-level references, selected copied artifacts, or result manifests.

In workspace-owned mode, `results/` is the structured in-workspace location for raw execution artifacts produced for the workspace.

### 13.3 `comparisons/`

Contains comparison outputs relevant to the workspace.

In version 1, the internal file schemas of artifacts stored in `comparisons/` are not standardized by this specification.

Workspace-local helper files under `comparisons/` are allowed, but remain
non-normative helper artifacts unless a later specification formalizes them.

### 13.4 `measurements/`

Contains processed measurements, metric summaries, or extracted analytical outputs.

### 13.5 `exports/`

Contains optional outward-facing or curated export artifacts.

### 13.6 `concept/`

Contains conceptual and mathematical modeling artifacts.

### 13.7 `engineering/`

Contains engineering-oriented planning artifacts.

---

## 14. Required Directories by Workspace Type

### 14.1 `system_development`

Must contain:

- `concept/`
- `engineering/`

### 14.2 `world_development`

Must contain:

- `concept/`
- `engineering/`

### 14.3 `single_system`

`concept/` and `engineering/` are not required.

They may exist, but investigation must not depend on them.

### 14.4 `system_comparison`

`concept/` and `engineering/` are not required.

They may exist, but investigation must not depend on them.

---

## 15. Minimum Required Contents by Workspace Type

### 15.1 `system_development`

A conforming `system_development` workspace must contain:

- required manifest fields from Sections 8, 9, and 10
- `concept/`
- `engineering/`
- at least one executable config under `configs/`

### 15.2 `world_development`

A conforming `world_development` workspace must contain:

- required manifest fields from Sections 8, 9, and 10
- `concept/`
- `engineering/`
- at least one executable config under `configs/`

### 15.3 `single_system`

A conforming `single_system` workspace must contain:

- required manifest fields from Sections 8, 9, and 10
- at least one executable config under `configs/`

### 15.4 `system_comparison`

A conforming `system_comparison` workspace must contain:

- required manifest fields from Sections 8, 9, and 10
- at least two executable configs under `configs/`
- a `comparisons/` directory intended for comparison outputs

---

## 16. Role Vocabulary

Version 1 standardizes the following role vocabulary for manifest and linking use:

- `reference`
- `candidate`
- `baseline`
- `system_under_test`
- `artifact_under_development`

These role names should be used consistently where applicable.

---

## 17. Relationship to AXIS Execution Outputs

### 17.1 Supported Result-Placement Modes

Version 1 supports two valid result-placement modes:

- existing framework-root mode
- workspace-owned mode

These modes are additive rather than mutually exclusive at the framework level.

The existing AXIS execution style based on direct config-path execution and a separate framework result root must remain valid.

The workspace-owned mode is an additional capability in which AXIS places execution artifacts directly into the workspace in a structured way.

### 17.2 Existing Framework-Root Mode

In existing framework-root mode:

- raw execution outputs remain framework-owned
- AXIS persists them under the normal framework result root
- the workspace may record references to those artifacts in `workspace.yaml`
- the workspace `results/` directory may contain selected copied artifacts, local summaries, or optional helper artifacts

This mode preserves the current AXIS execution behavior.

### 17.3 Workspace-Owned Mode

In workspace-owned mode:

- AXIS persists workspace-associated execution outputs directly inside the workspace
- raw execution artifacts for the workspace are placed under `results/`
- comparison outputs for the workspace are placed under `comparisons/`
- derived analytical outputs remain under `measurements/`
- workspace-aware tooling should update `workspace.yaml` so that the workspace manifest continues to describe the current primary artifact set

In this mode, the workspace is both the semantic and operational container for its execution artifacts.

### 17.4 Workspace `results/` Rule

The workspace-local `results/` directory must be interpreted according to the chosen result-placement mode.

In framework-root mode, it acts as a workspace-level mapping, selection, or local-summary layer.

In workspace-owned mode, it acts as the primary structured location for workspace execution artifacts.

### 17.5 Workspace `comparisons/` Rule

The workspace-local `comparisons/` directory is the canonical location for comparison artifacts belonging to the workspace.

In workspace-owned comparison flows, AXIS comparison outputs should be written directly into this directory.

### 17.6 Manifest Authority Rule

The workspace manifest `workspace.yaml` is the authoritative source of workspace-level artifact semantics.

This means:

- `linked_experiments`, `linked_runs`, `linked_comparisons`, and related manifest fields carry the authoritative workspace meaning
- helper files stored inside `results/` or `comparisons/` are secondary convenience artifacts if they exist

Version 1 does not require any external helper-file convention.

If helper files are present, they must not contradict the authoritative manifest content.

### 17.7 Rationale

This rule preserves backward compatibility while allowing a more coherent workspace-centered operating mode.

---

## 18. Linked Artifact Fields

Because version 1 supports both framework-root and workspace-owned result placement, it may use explicit linking fields in the manifest.

Version 1 allows:

- `linked_experiments`
- `linked_runs`
- `linked_comparisons`

These are optional, but recommended when the workspace needs to identify concrete execution or comparison artifacts explicitly.

### 18.1 Results and Comparison Helper Artifacts

Version 1 intentionally does not standardize a required file schema for helper artifacts stored in:

- `results/`
- `comparisons/`

Examples of such helper artifacts may include local summaries or convenience manifests under:

- `results/`
- `comparisons/`

In version 1, these should be treated as workspace-local freeform helper artifacts.

Their existence is allowed and useful, but their internal schema is not yet normative.

The only normative requirements in version 1 are:

- the directories exist where required
- the workspace manifest remains authoritative
- helper artifacts do not contradict manifest-declared linkage semantics

### 18.2 Placement and Nesting

Version 1 recommends that workspaces should reside under a top-level directory named:

- `workspaces/`

This is a recommendation rather than a strict requirement.

However, one rule is strict:

> a workspace must not be nested inside another workspace

This means a workspace root may contain ordinary subdirectories, but it must not contain another independent workspace root with its own `workspace.yaml`.

---

## 19. Source Code Placement

Source code must not be duplicated into the workspace as part of version 1 workspace structure.

Source code remains in the actual repository implementation areas, such as:

- `src/`

The workspace may contain:

- concept artifacts
- engineering artifacts
- references to implemented code

but not source duplication as a required practice.

### 19.1 `artifact_under_development` for Worlds

Version 1 does not require a dedicated world-specific field such as `world_under_development`.

The field:

- `artifact_under_development`

is sufficient for both development kinds.

For `world_development`, its value should be interpreted as the primary identifier of the world artifact under development, typically aligned with the intended world-type naming convention.

---

## 20. Conformance Rules

An Experiment Workspace conforms to this specification if:

- it contains `workspace.yaml`
- it contains the required shared top-level items
- its `workspace_class` and `workspace_type` are valid and mutually consistent
- it contains all required manifest fields for its class and type
- it satisfies the minimum required directory contents for its type
- it treats `results/` according to one of the supported result-placement modes
- it does not misuse the manifest as an executable run config

---

## 21. Non-Goals for Version 1

Version 1 does not require:

- framework-readable workspace manifests
- fixed CLI command shapes for workspace operations
- automatic synchronization or migration across result-placement modes
- public documentation structure
- statistical semantics for measurements
- full schema validation of all optional manifest fields

---

## 22. Summary

Version 1 of the Experiment Workspace specification defines a structured filesystem-level context for AXIS work.

Its central principles are:

- explicit workspace classification
- explicit workspace manifest
- clear separation between workspace-level organization and framework-level execution
- explicit distinction between development and investigation
- the existing framework-root result model remains valid
- a workspace-owned result-placement mode is additionally allowed
- development requires concept and engineering artifacts
- investigation remains configuration- and analysis-centered

This specification provides the first stable basis for structured AXIS experiment workspaces before any framework integration is introduced.
