# System Development Workflow -- Detailed Draft

## Purpose

This document defines a more concrete workflow draft for the workspace type:

- `development / system_development`

It builds on:

- `system-development-workflow-brainstorm.md`

The goal is to define a practical v1 workflow that can later be turned into:

- a manual workflow section
- a more formal workflow spec
- and, where useful, additional workspace tooling support

This draft focuses on:

- operational structure
- artifact placement
- baseline/candidate semantics
- validation flow

It does not yet define a final implementation spec.

---

## 1. Core Intent

A `system_development` workspace is the structured environment for creating,
implementing, and validating a new system.

It is not only an execution workspace.

It is a combined:

- concept workspace
- engineering workspace
- validation workspace

The workspace should therefore support the full development chain:

1. mathematical concept
2. worked examples
3. formal spec preparation
4. engineering planning
5. implementation
6. baseline validation
7. candidate validation
8. comparison and refinement

This workflow is iterative rather than linear.

---

## 2. Baseline and Candidate Model

### 2.1 Baseline Rule

Version 1 of the `system_development` workflow uses:

- exactly one primary baseline system

The default baseline is:

- `system_a`

This baseline should be created automatically by scaffolding and may later be
changed manually through workspace configuration.

### 2.2 Candidate Rule

Version 1 uses:

- exactly one active candidate configuration

The candidate is the current executable representation of the new system under
development.

This keeps the workflow focused on development rather than branching
investigation.

### 2.3 Candidate Detection Rule

The workspace should detect candidate existence through configuration state,
not through source-code inspection.

Version 1 rule:

- if only the baseline config exists, the workspace is in the pre-candidate state
- if both baseline and candidate config exist, the workspace is in the post-candidate state

This keeps candidate readiness operational and explicit.

### 2.4 Naming Rule for Configs

Version 1 should use a clear naming convention:

- baseline config:
  - `configs/baseline-system_a.yaml`
- candidate config:
  - `configs/candidate-<system_type>.yaml`

Example:

- `configs/candidate-system_d.yaml`

This keeps role semantics visible without adding new manifest fields.

### 2.5 Comparison Rule

The default validation comparison is:

> current candidate vs primary baseline

If that pairing cannot be resolved, the workspace command should fail
explicitly rather than guessing.

---

## 3. Workspace Artifact Structure

The existing workspace directories are sufficient for v1.

### 3.1 `concept/`

This directory is reserved for mathematical and conceptual artifacts.

Typical contents:

- mathematical concept notes
- worked examples
- formalization drafts
- reduction cases
- open conceptual questions

This directory should remain conceptually pure.

Real implementation documents do not belong here.

### 3.2 `engineering/`

This directory is reserved for implementation-oriented artifacts.

Typical contents:

- engineering specs
- work packages
- implementation plans
- test plans
- technical risks

This is the bridge from concept to concrete system work.

Scaffolding should also create initial markdown templates in:

- `concept/`
- `engineering/`

so the workspace is immediately usable for design work.

### 3.3 `configs/`

This directory contains executable configurations.

Version 1 should assume at least:

- one baseline config
- one candidate config once the new system becomes executable

### 3.4 `results/`

This directory contains workspace-owned execution artifacts.

Typical contents:

- baseline run artifacts
- candidate run artifacts

### 3.5 `comparisons/`

This directory contains workspace-owned comparison artifacts.

In `system_development`, these comparison artifacts function as:

- validation evidence
- regression evidence

### 3.6 `measurements/`

This directory contains summary metrics and extracted validation evidence.

### 3.7 `notes.md`

`notes.md` remains a free-form working document.

It should be used for:

- observations from runs
- interpretation of comparisons
- failed hypotheses
- next steps

---

## 4. Workflow Phases

Version 1 should explicitly organize the workflow into these phases.

### Phase 1 -- Workspace Creation

The user creates a `system_development` workspace.

Expected result:

- `concept/` exists
- `engineering/` exists
- baseline config exists
- initial markdown templates exist under `concept/` and `engineering/`
- manifest exists

The workspace is immediately valid as a development container, even before the
new system exists.

### Phase 2 -- Concept and Spec Work

The user writes the early design artifacts.

This includes:

- mathematical concept work
- worked examples
- spec-oriented drafts
- engineering planning

In v1, this remains manual authoring work.

The workspace supports it by providing:

- the correct locations
- a clear separation of artifact types

### Phase 3 -- Baseline Orientation

Before the new system exists, the baseline is executed.

This provides:

- a behavioral anchor
- initial traces
- initial measurements
- reference behavior in the chosen environment

Version 1 behavior:

- `axis workspaces run <workspace>` executes the baseline set
- results are written into `results/`
- notes and measurements can be updated afterward

Version 1 should also support explicit selective execution flags:

- `--baseline-only`
- `--candidate-only`

These flags are part of the intended workflow model from the beginning.

For pre-candidate work, `--baseline-only` is naturally valid.

### Phase 4 -- Candidate Validation

Once the new system is implemented enough to run, the candidate config is added
or activated.

Version 1 behavior:

- `axis workspaces run <workspace>` executes baseline plus candidate
- execution artifacts are written into `results/`

Selective execution remains available:

- `axis workspaces run <workspace> --baseline-only`
- `axis workspaces run <workspace> --candidate-only`

This makes the development workspace the direct operational context for the new
system.

### Phase 5 -- Comparison and Validation

After baseline and candidate results exist:

- `axis workspaces compare <workspace>`

should compare:

- current candidate
- primary baseline

Default compare resolution should use:

- primary baseline
- latest candidate execution

If no candidate execution exists, comparison should fail explicitly.

The resulting comparison artifact is a validation record.

It is not merely an investigation artifact.

It serves as evidence that the current candidate behaves better, worse, or
simply differently than the baseline.

### Phase 6 -- Iterative Refinement

The user then iterates:

1. modify concept
2. modify engineering plan
3. modify implementation
4. rerun workspace
5. rerun comparison
6. inspect results
7. update notes and measurements

This is the central ongoing loop of `system_development`.

---

## 5. Operational Command Mapping

Version 1 can map the workflow onto the existing workspace-oriented commands.

### 5.1 Scaffold

```bash
axis workspaces scaffold
```

Used to create the initial development workspace.

### 5.2 Check

```bash
axis workspaces check workspaces/my-system-dev
```

Used to validate structural integrity and later detect drift.

### 5.3 Show

```bash
axis workspaces show workspaces/my-system-dev
```

Used to inspect the current declared workspace state.

### 5.4 Run

```bash
axis workspaces run workspaces/my-system-dev
```

Operational meaning in `system_development`:

- before implementation: run baseline
- after implementation: run baseline plus candidate

Selective execution flags should exist in v1:

```bash
axis workspaces run workspaces/my-system-dev --baseline-only
axis workspaces run workspaces/my-system-dev --candidate-only
```

### 5.5 Compare

```bash
axis workspaces compare workspaces/my-system-dev
```

Operational meaning in `system_development`:

- validate current candidate against primary baseline

### 5.6 Comparison Result

```bash
axis workspaces comparison-result workspaces/my-system-dev
```

Operational meaning in `system_development`:

- inspect the latest or selected validation evidence

Default behavior:

- show the latest comparison result

Selection behavior:

- `--number N` selects a specific earlier comparison

### 5.7 Visualize

```bash
axis visualize --workspace workspaces/my-system-dev --episode 1
```

Used to inspect baseline or candidate behavior through workspace-local results.

When both baseline and candidate exist, role selection should be used:

```bash
axis visualize --workspace workspaces/my-system-dev --role baseline --episode 1
axis visualize --workspace workspaces/my-system-dev --role candidate --episode 1
```

If only baseline exists, the default may resolve to baseline.

---

## 6. What the Workspace Supports vs Does Not Support

### 6.1 Supported in v1

The workspace should support:

- structured placement of concept artifacts
- structured placement of engineering artifacts
- baseline execution
- candidate execution
- comparison as validation
- local result and measurement storage
- iterative note-taking

### 6.2 Not Yet Supported in v1

The workspace should not yet attempt to automate:

- concept authoring
- worked example authoring
- spec authoring
- engineering document authoring
- automatic extraction of conceptual milestones from documents

These remain manual.

This is intentional.

The first strong value of the workspace is:

- operational coherence
- artifact locality
- repeatable validation structure

not document automation.

---

## 7. Manifest Semantics for `system_development`

For `system_development`, version 1 should use explicit development-specific
manifest fields.

The reason is:

> baseline and candidate semantics are central to development and should not
> be left implicit

The generic workspace fields should still remain part of the model, but
`system_development` should add explicit operational fields so the workspace is
self-describing.

### 7.1 Development-Specific Fields

The following fields should be planned for `system_development`:

- `baseline_config`
- `candidate_config`
- `baseline_results`
- `candidate_results`
- `current_candidate_result`
- `current_validation_comparison`

### 7.2 Field Intent

#### `baseline_config`

Workspace-relative path to the single primary baseline config.

Expected example:

- `configs/baseline-system_a.yaml`

#### `candidate_config`

Workspace-relative path to the single active candidate config.

This field may be absent in the pre-candidate state.

Expected example:

- `configs/candidate-system_d.yaml`

#### `baseline_results`

Ordered list of workspace-relative execution artifacts produced from the
baseline config.

This preserves baseline history.

#### `candidate_results`

Ordered list of workspace-relative execution artifacts produced from the
candidate config.

This preserves candidate history.

#### `current_candidate_result`

Workspace-relative path to the candidate result that should be used by default
in comparison and visualization flows.

#### `current_validation_comparison`

Workspace-relative path to the comparison artifact that currently represents
the active validation state of the workspace.

### 7.3 Relationship to Generic Fields

The generic fields should still exist:

- `primary_configs`
- `primary_results`
- `primary_comparisons`
- `primary_measurements`

But in `system_development` they should be interpreted as generic
workspace-level artifact collections, while the development-specific fields
carry the actual baseline/candidate semantics.

So:

- generic fields preserve cross-workspace consistency
- development-specific fields remove operational ambiguity

### 7.4 Update Semantics

Version 1 should assume:

- `baseline_config` is set at scaffold time
- `candidate_config` is added once the candidate becomes executable
- `baseline_results` accumulates over time
- `candidate_results` accumulates over time
- `current_candidate_result` is updated after candidate runs
- `current_validation_comparison` is updated after successful comparison runs

### 7.5 Pre-Candidate vs Post-Candidate State

The explicit fields also make workspace state clearer.

Pre-candidate state:

- `baseline_config` present
- `candidate_config` absent
- baseline-only validation possible

Post-candidate state:

- `baseline_config` present
- `candidate_config` present
- baseline and candidate validation possible

This is preferable to inferring the whole state only from file naming.

---

## 8. Comparison Semantics in Development

In `system_development`, comparison has a distinct meaning from
`investigation`.

In `investigation`, comparison is mainly:

- analytical
- explanatory
- exploratory

In `system_development`, comparison is mainly:

- validating
- decision-supporting
- iteration-guiding

This means comparison artifacts in development should be interpreted as:

- evidence for whether the current implementation is progressing in the right
  direction

This is an important semantic distinction, even if the underlying command is
the same.

---

## 9. Recommended v1 Rule Set

The strongest v1 rule set is:

1. exactly one primary baseline
2. default baseline is `system_a`
3. exactly one active candidate
4. candidate existence is detected through config presence
5. baseline config naming is explicit
6. candidate config naming is explicit
7. baseline exists before candidate
8. `run` before implementation executes baseline only
9. `run` after implementation executes baseline plus candidate
10. `run` also supports `--baseline-only` and `--candidate-only`
11. `compare` validates latest candidate against primary baseline
12. `comparison-result` defaults to the latest comparison and supports `--number`
13. `visualize` uses `baseline` / `candidate` roles when both exist
14. development-specific manifest fields make baseline/candidate state explicit
15. concept work remains manual under `concept/`
16. engineering work remains manual under `engineering/`
17. notes remain free-form

This is intentionally narrow.

The narrowness is a feature, not a bug.

It should help the first development workflow stay understandable.

---

## 10. Open Questions for the Next Stage

These questions still need refinement before a more formal workflow spec.

1. Should later versions support more than one baseline, or should v1 semantics
   remain fixed on exactly one baseline?
2. Should the development-specific fields be required immediately in the first
   formal workflow spec, or staged in as a development-only extension?

---

## 11. Recommended Next Step

The next useful step would be:

> refine the unresolved operational questions above and turn this document into
> a formal `system_development` workflow spec or manual section

That should happen before:

- adding more development-specific commands
- or introducing stronger development-specific manifest semantics
