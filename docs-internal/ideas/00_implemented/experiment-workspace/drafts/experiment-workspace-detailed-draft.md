# AXIS - Experiment Workspace

## Detailed Draft for Structured Experiment Contexts

---

## 1. Purpose

This document refines the initial Experiment Workspace idea into a more specification-oriented detailed draft.

Its purpose is to define a structured experimental context for AXIS that goes beyond loose configuration files and framework-owned raw results.

The Experiment Workspace is intended to support two distinct modes of work:

- development
- investigation

and to do so in a way that remains compatible with the existing AXIS execution chain:

- step
- episode
- run
- experiment execution
- comparison

This document is not yet a final specification.

It fixes:

- the two-level workspace classification model
- the role of `experiment.yaml` as workspace manifest
- the relationship between workspace-local artifacts and framework-owned raw results
- minimum required workspace contents by type
- the initial folder model for the first workspace version

---

## 2. Core Principle

An Experiment Workspace is a bounded container for one coherent AXIS work context.

It is not identical to:

- a framework experiment
- a run
- a comparison
- or a config file

Instead, it is the higher-level structure that groups:

- intent
- input configurations
- linked execution outputs
- comparisons
- measurements
- notes
- and, where relevant, concept and engineering artifacts

Conceptually:

```text
Workspace
  -> manifest
  -> configs
  -> linked or selected results
  -> comparisons
  -> measurements
  -> notes
  -> optional concept / engineering artifacts
```

---

## 3. Two-Level Workspace Classification

The workspace model should use two explicit classification fields:

- `workspace_class`
- `workspace_type`

Both should be mandatory in the later specification.

### 3.1 Workspace Class

Allowed first values:

- `development`
- `investigation`

### 3.2 Workspace Type

Allowed first values:

- under `development`:
  - `system_development`
  - `world_development`
- under `investigation`:
  - `single_system`
  - `system_comparison`

### 3.3 Why Both Fields Must Exist

The distinction between class and type should remain explicit.

This is important because:

- the class tells us what mode of work the workspace represents
- the type tells us the concrete structural form inside that mode

This avoids a flat type list that would blur the difference between:

- building an artifact
- studying an existing artifact

---

## 4. Development vs Investigation

### 4.1 Development

A development workspace exists to create or structurally modify an artifact.

Initial artifact kinds:

- `system`
- `world`

Development therefore includes:

- concept work
- mathematical or architectural drafts
- engineering planning
- validation runs
- validation comparisons

The key rule is:

> in development, the artifact itself is under active change

### 4.2 Investigation

An investigation workspace exists to study existing artifacts under defined conditions.

The key rule is:

> in investigation, existing systems and worlds are not structurally modified as part of the workspace purpose

Variation is allowed only through:

- configuration
- run selection
- comparison
- measurement
- interpretation

### 4.3 Development May Contain Investigation Artifacts

Development workspaces may legitimately contain:

- baseline runs
- comparison outputs
- measurements

but these are subordinate to the primary goal of developing the artifact.

---

## 5. Artifact Kinds

The detailed draft should make artifact kind explicit for development workspaces.

### 5.1 Required Field

For development, `artifact_kind` should be mandatory.

Allowed initial values:

- `system`
- `world`

### 5.2 Required Companion Field

Development workspaces should also include:

- `artifact_under_development`

This identifies the main target artifact, for example:

- `system_d`
- `signal_landscape_v2`

---

## 6. The Workspace Manifest

The file `experiment.yaml` should be treated as the workspace manifest.

It is a workspace-level metadata document.

It is not the same thing as an executable AXIS run config.

### 6.1 What the Manifest Must Describe

The manifest should describe:

- workspace identity
- workspace classification
- workspace purpose
- involved artifacts
- primary linked artifacts
- current process state

### 6.2 What the Manifest Must Not Replace

The manifest must not replace:

- system run config files
- world execution config files
- framework experiment config structures
- comparison result payloads

Those remain separate artifacts.

---

## 7. Manifest Field Model v1

The first manifest should be medium-weight:

- rich enough to organize real work
- not overloaded with speculative future features

### 7.1 Required Core Fields

The detailed draft recommends these as required:

- `workspace_id`
- `title`
- `workspace_class`
- `workspace_type`
- `status`
- `lifecycle_stage`
- `created_at`

### 7.2 Required Purpose Fields

For `investigation`:

- `question`

For `development`:

- `development_goal`

The complementary field may still exist, but should be optional.

### 7.3 Required Artifact Fields

For `system_development`:

- `artifact_kind`
- `artifact_under_development`

For `world_development`:

- `artifact_kind`
- `artifact_under_development`

For `single_system`:

- `system_under_test`

For `system_comparison`:

- `reference_system`
- `candidate_system`

### 7.4 Optional Structural Fields

The detailed draft recommends these as optional:

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

### 7.5 Status vs Lifecycle Stage

The manifest should distinguish:

- `status`
- `lifecycle_stage`

These are not the same.

#### `status`

Describes the current working state of the workspace.

Suggested initial values:

- `idea`
- `draft`
- `running`
- `analyzing`
- `completed`

#### `lifecycle_stage`

Describes where the underlying AXIS artifact work currently sits in the broader workflow.

Suggested initial values:

- `idea`
- `draft`
- `spec`
- `implementation`
- `documentation`

This allows a workspace to be:

- in `status: analyzing`
- while still tracking a `lifecycle_stage: implementation`

which is meaningful in development work.

---

## 8. Manifest Example -- Development

```yaml
workspace_id: "system-d-development"
title: "Development of System D"
workspace_class: "development"
workspace_type: "system_development"
artifact_kind: "system"
artifact_under_development: "system_d"
status: "draft"
lifecycle_stage: "draft"
created_at: "2026-04-17"

development_goal: "Design and validate a new system architecture extending the current AXIS family."
description: "System D development workspace with concept, engineering, and validation artifacts."
tags:
  - "development"
  - "system"
  - "system-d"

baseline_artifacts:
  - "system_a"
  - "system_c"

validation_scenarios:
  - "grid2d-baseline"
  - "paired-against-system-a"

primary_configs:
  - "configs/baseline-validation.yaml"
  - "configs/comparison-against-system-a.yaml"

primary_results:
  - "results/validation/"

primary_comparisons:
  - "comparisons/system-a-vs-system-d/"
```

---

## 9. Manifest Example -- Investigation

```yaml
workspace_id: "system-a-vs-system-c-grid2d-baseline"
title: "System A vs System C in sparse Grid2D baseline"
workspace_class: "investigation"
workspace_type: "system_comparison"
status: "analyzing"
lifecycle_stage: "documentation"
created_at: "2026-04-17"

question: "How does predictive modulation in System C change behavior relative to System A under matched baseline conditions?"
description: "Paired investigation workspace for System A and System C under baseline Grid2D conditions."
tags:
  - "investigation"
  - "comparison"
  - "system-a"
  - "system-c"

reference_system: "system_a"
candidate_system: "system_c"

primary_configs:
  - "configs/reference-system-a.yaml"
  - "configs/candidate-system-c.yaml"

primary_results:
  - "results/reference/"
  - "results/candidate/"

primary_comparisons:
  - "comparisons/run-0000-vs-run-0000.json"

primary_measurements:
  - "measurements/comparison-summary.csv"
```

---

## 10. Folder Model v1

The detailed draft recommends a shared top-level workspace structure, with different expectations by workspace type.

Proposed common layout:

```text
<workspace>/
  experiment.yaml
  README.md
  notes.md
  concept/
  engineering/
  configs/
  results/
  comparisons/
  measurements/
  exports/
```

### 10.1 Rationale for a Shared Structure

Using a shared top-level structure keeps workspaces easy to read and compare.

The semantic difference should come primarily from:

- `workspace_class`
- `workspace_type`
- minimum required contents

rather than from completely different directory trees.

---

## 11. Meaning of Each Top-Level Folder

### 11.1 `concept/`

Contains conceptual and mathematical modeling artifacts.

Examples:

- conceptual notes
- mathematical drafts
- design sketches
- system or world modeling documents

### 11.2 `engineering/`

Contains engineering-oriented planning artifacts.

Examples:

- engineering specs
- work package definitions
- implementation roadmaps

### 11.3 `configs/`

Contains executable configuration files used by the workspace.

These remain the practical bridge into current AXIS execution.

### 11.4 `results/`

Contains workspace-level result references and selected result artifacts.

In v1, this should not be treated as a second full raw result repository.

### 11.5 `comparisons/`

Contains comparison outputs relevant to the workspace.

This is especially important for:

- `system_comparison`
- development validation against baselines

### 11.6 `measurements/`

Contains processed measurement outputs and summaries.

Examples:

- CSV summaries
- metric tables
- extracted series

### 11.7 `exports/`

Contains optional outward-facing or curated artifacts.

Examples:

- shareable summaries
- selected JSON exports
- prepared plots

---

## 12. `concept/` and `engineering/` by Workspace Class

Your question about `engineering/` in investigation is important.

The detailed draft should resolve it clearly.

### 12.1 Development

For `development`, both of these should be first-class:

- `concept/`
- `engineering/`

They are part of the actual purpose of the workspace.

### 12.2 Investigation

For `investigation`, `concept/` and `engineering/` should not be considered primary required workspace areas.

That means:

- `concept/` may exist only if the investigation needs framing notes
- `engineering/` is generally not needed and should not be a required part of the workflow

This follows the rule that investigation does not structurally change the artifact under study.

### 12.3 Practical Recommendation

Therefore:

- keep the shared top-level model for consistency
- but define `engineering/` as **required only for development**
- and **not required for investigation**

This preserves both:

- consistency of the workspace family
- conceptual correctness of the development/investigation distinction

---

## 13. Relationship to Framework-Owned Raw Results

The first version should not replace the current AXIS result repository.

### 13.1 v1 Recommendation

The detailed draft clearly recommends:

> raw execution outputs remain framework-owned

The Experiment Workspace should sit above that structure.

### 13.2 Meaning of Workspace `results/`

In v1, workspace-local `results/` should contain:

- references to framework-owned artifacts
- selected copied outputs where needed
- result manifests or link files

It should not be assumed to contain the full raw execution tree.

### 13.3 Why This Is Better

This avoids:

- duplication of full result repositories
- synchronization problems
- unclear ownership of execution artifacts

It also lets the first workspace version be adopted immediately without framework changes.

---

## 14. Linked Artifacts

Because workspaces do not own all raw execution outputs, they need explicit linking fields.

### 14.1 Recommended Linking Fields

The detailed draft recommends the following optional manifest fields:

- `linked_experiments`
- `linked_runs`
- `linked_comparisons`

### 14.2 Example Shape

```yaml
linked_experiments:
  - experiment_id: "ed3efb3e..."
    role: "reference"
  - experiment_id: "46fb8c97..."
    role: "candidate"

linked_runs:
  - experiment_id: "ed3efb3e..."
    run_id: "run-0000"
    role: "reference"
  - experiment_id: "46fb8c97..."
    run_id: "run-0000"
    role: "candidate"
```

The later spec can make this more formal.

For now, the important thing is the principle:

> a workspace references execution artifacts explicitly instead of absorbing them blindly

---

## 15. Standard Roles

The detailed draft should already normalize a small role vocabulary.

Recommended initial roles:

- `reference`
- `candidate`
- `baseline`
- `system_under_test`
- `artifact_under_development`

This should be used consistently in:

- manifests
- result links
- comparison substructures

---

## 16. Minimum Required Contents by Workspace Type

The detailed draft should define minimum contents for each initial workspace type.

### 16.1 `system_development`

Required:

- `experiment.yaml`
- `README.md`
- `notes.md`
- `concept/`
- `engineering/`
- `configs/`

Minimum manifest requirements:

- `workspace_class = development`
- `workspace_type = system_development`
- `artifact_kind = system`
- `artifact_under_development`
- `development_goal`

### 16.2 `world_development`

Required:

- `experiment.yaml`
- `README.md`
- `notes.md`
- `concept/`
- `engineering/`
- `configs/`

Minimum manifest requirements:

- `workspace_class = development`
- `workspace_type = world_development`
- `artifact_kind = world`
- `artifact_under_development`
- `development_goal`

### 16.3 `single_system`

Required:

- `experiment.yaml`
- `README.md`
- `notes.md`
- `configs/`

Recommended:

- `results/`
- `measurements/`

Minimum manifest requirements:

- `workspace_class = investigation`
- `workspace_type = single_system`
- `system_under_test`
- `question`

### 16.4 `system_comparison`

Required:

- `experiment.yaml`
- `README.md`
- `notes.md`
- `configs/`
- `comparisons/`

Recommended:

- `results/`
- `measurements/`

Minimum manifest requirements:

- `workspace_class = investigation`
- `workspace_type = system_comparison`
- `reference_system`
- `candidate_system`
- `question`

At least two primary configs should be expected here.

---

## 17. Comparison of Identical Systems

The workspace model should allow comparison of the same system family under different configurations.

Examples:

- `System A` vs. `System A` with different parameterization
- `System C` baseline vs. `System C` with altered prediction sensitivity

This is still a valid `system_comparison` workspace.

The comparison is defined by:

- paired execution context
- explicit reference/candidate roles

not by requiring different system type labels.

This is important because configuration-only comparisons are a legitimate investigation mode.

---

## 18. Example Workspace Layouts

### 18.1 System Development

```text
experiments/
  system-d-development/
    experiment.yaml
    README.md
    notes.md
    concept/
      system-d-concept.md
      system-d-draft.md
    engineering/
      system-d-engineering-spec.md
      work-packages.md
    configs/
      baseline-validation.yaml
      comparison-against-system-a.yaml
    results/
      validation/
    comparisons/
      system-a-vs-system-d/
    measurements/
      validation-summary.csv
    exports/
```

### 18.2 World Development

```text
experiments/
  toroidal-v2-development/
    experiment.yaml
    README.md
    notes.md
    concept/
      toroidal-v2-concept.md
    engineering/
      toroidal-v2-engineering-spec.md
    configs/
      baseline-validation.yaml
    results/
      validation/
    comparisons/
    measurements/
      world-validation-summary.csv
    exports/
```

### 18.3 Single-System Investigation

```text
experiments/
  system-c-baseline-grid2d/
    experiment.yaml
    README.md
    notes.md
    concept/
    engineering/
    configs/
      baseline.yaml
    results/
      run-manifest.yaml
    comparisons/
    measurements/
      run-summary.csv
      vitality-curves.csv
    exports/
```

### 18.4 System-Comparison Investigation

```text
experiments/
  system-a-vs-system-c-grid2d-baseline/
    experiment.yaml
    README.md
    notes.md
    concept/
    engineering/
    configs/
      reference-system-a.yaml
      candidate-system-c.yaml
    results/
      linked-runs.yaml
    comparisons/
      run-0000-vs-run-0000.json
      episode-0001.json
      episode-0002.json
    measurements/
      comparison-summary.csv
      action-divergence.csv
      vitality-deltas.csv
    exports/
```

---

## 19. Practical Trial Recommendations

Before any framework change, the detailed draft should be tested in practice with two workspace examples:

- one `system_development` workspace
- one `system_comparison` workspace

The trial should check:

- whether the manifest is expressive enough
- whether linked results are practical
- whether the distinction between development and investigation is clear
- whether concept vs. engineering is clearly visible
- whether `engineering/` being non-required for investigation feels correct

---

## 20. Long-Term Direction

If the workspace concept stabilizes through practical use, later framework support may become justified.

Potential future directions:

- workspace-aware CLI support
- workspace-aware experiment creation
- manifest-aware result linking
- formal validation of workspace manifests
- public documentation for workspace usage

But the first implementation step should remain:

- filesystem-level discipline
- explicit manifests
- no framework behavior changes

---

## 21. Summary

This detailed draft fixes the first stable shape of the Experiment Workspace concept.

Its main decisions are:

- explicit two-level classification:
  - `workspace_class`
  - `workspace_type`
- explicit distinction between:
  - development
  - investigation
- explicit `experiment.yaml` manifest
- explicit split between workspace organization and framework execution config
- framework-owned raw results remain external in v1
- workspace `results/` contains links or selected artifacts
- `engineering/` is required for development, but not for investigation
- minimum contents are defined per workspace type

This makes the concept precise enough to guide a practical trial and prepares the ground for a later formal specification.
