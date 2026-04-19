# AXIS - Experiment Workspace

## Draft for Structured Experiment Contexts

---

## 1. Purpose

This document proposes a first draft for a structured **experiment workspace** concept in AXIS.

The purpose of this concept is to move beyond the current flat separation of:

- `experiments/configs/`
- `experiments/results/`

and toward a more coherent experiment-centered structure.

The new structure should bundle everything that belongs to one experimental investigation into one explicit workspace context.

This draft is intentionally pre-specification.

It defines:

- what an experiment should mean in AXIS
- which experiment types should be recognized
- what a minimal experiment workspace should contain
- how the current execution and comparison chain can be embedded into a more structured research workflow

---

## 2. Problem Statement

The current AXIS execution pipeline is already strong:

- step traces
- episode traces
- run-level summaries
- experiment-level execution
- paired comparison

However, the filesystem organization is still relatively flat and operational rather than conceptual.

At the moment:

- configs live in one shared place
- results live in another shared place
- comparisons are operationally possible but not yet clearly embedded into an experiment-centered workspace
- notes, measurements, and interpretation are not structurally first-class

This makes it harder to treat an experiment as a coherent investigation artifact.

In practice, a serious experiment usually includes more than just executable config and raw results.

It also includes:

- a question
- a scope
- involved systems
- derived measurements
- comparisons
- interpretation notes

The current layout does not make that explicit enough.

---

## 3. Core Proposal

Introduce a new conceptual unit:

> the **Experiment Workspace**

An Experiment Workspace is a structured container for one experimental investigation.

It should bundle:

- experiment identity
- experiment intent
- input configs
- generated results
- derived measurements
- comparison outputs
- notes and interpretation

The workspace should become the primary organizational unit for experiment work.

This does not immediately require framework changes.

The first step should be a disciplined directory structure and metadata convention that can be used immediately on top of the current framework.

---

## 4. What Is an Experiment?

Before defining folders, AXIS needs a clearer concept of what an experiment is.

### 4.1 Proposed Definition

An **experiment** in AXIS is:

> a bounded investigation with a defined question, defined inputs, defined execution scope, and persisted outputs

This means an experiment is not merely:

- one config file
- one run
- or one comparison

Instead, an experiment is the larger container that gives those artifacts a shared meaning.

### 4.2 Consequence

An experiment should be able to answer questions such as:

- What system or systems are being studied?
- Under what conditions?
- What exact configurations were used?
- What runs were produced?
- Were comparisons performed?
- What measurements were extracted?
- What interpretation or conclusions were recorded?

This is what the workspace must make explicit.

---

## 5. Top-Level Workspace Classes

The first draft should distinguish between two top-level workspace classes.

### 5.1 Development

A **development workspace** exists to build or modify a system or world.

Its primary purpose is constructive:

- define a new artifact
- refine an existing artifact
- clarify the conceptual model
- prepare engineering implementation
- validate the in-development artifact through runs and comparisons

Development therefore includes more than execution.

It includes the full pre-implementation chain:

- concept
- draft
- specification
- engineering planning

as well as validation through actual runs.

### 5.2 Investigation

An **investigation workspace** exists to study behavior of already existing artifacts under defined conditions.

Its primary purpose is analytical:

- observe
- measure
- compare
- interpret

The critical rule is:

> investigation does not structurally modify the system or world under study

Existing systems and worlds may be instantiated under different configurations, but they are not changed as part of the workspace's purpose.

### 5.3 Why This Split Matters

This distinction is important because AXIS is now used for both:

- creating new agent/world architectures
- studying the behavior of already defined architectures

If both are collapsed into one flat experiment type model, the workspace structure will remain ambiguous.

The development/investigation split makes the working mode explicit.

---

## 6. Workspace Type Hierarchy

Within the two top-level classes, the first draft should define a second layer of workspace types.

### 6.1 Development Types

The model should be symmetric from the beginning.

Initial development types:

- `system_development`
- `world_development`

Future extension could later include:

- `system_world_co_development`

but this should not be required for v1.

### 6.2 Investigation Types

For investigation, the first draft should keep the initial type set small and practical.

Initial investigation types:

- `single_system`
- `system_comparison`

Later investigation types may include:

- `single_world`
- `world_comparison`
- `ablation`
- `parameter_sweep`

### 6.3 Two-Level Model

The intended structure is therefore:

- **Workspace class**
  - `development`
  - `investigation`
- **Workspace type**
  - under `development`:
    - `system_development`
    - `world_development`
  - under `investigation`:
    - `single_system`
    - `system_comparison`

This two-level model separates:

- the mode of work
from
- the concrete investigation or development shape

---

## 7. Relationship to the Existing Execution Chain

The proposed workspace concept does not replace the current AXIS execution chain.

It organizes it.

The chain remains:

- **Step**
  smallest replayable unit
- **Episode**
  ordered sequence of steps
- **Run**
  collection of episodes under one run configuration
- **Experiment Execution**
  one or more runs launched by the framework
- **Comparison**
  analysis layer over persisted traces

The workspace sits above this chain and groups the artifacts produced by it.

Conceptually:

```text
Workspace
  -> configs
  -> runs/results
  -> comparisons
  -> measurements
  -> notes
```

So the workspace is not a new replay concept.

It is a structured research and execution context built around the existing pipeline.

---

## 8. Development vs Investigation in Practice

The distinction between development and investigation should also guide what is considered a valid workspace purpose.

### 8.1 Development Rule

In a development workspace:

- the primary artifact is under active design or change
- system or world structure may evolve
- concept and engineering documents are first-class contents
- execution and comparison are supporting validation activities

Examples:

- developing a new `System D`
- introducing a new world type with changed dynamics
- reworking the architecture of an existing system under a new concept

### 8.2 Investigation Rule

In an investigation workspace:

- the examined systems or worlds already exist
- no structural modifications are part of the workspace purpose
- changes happen only through configuration, run selection, comparison, and measurement

Examples:

- studying `System C` behavior under one world configuration
- comparing `System A` and `System C`
- evaluating an existing world type under several baselines

### 8.3 Development May Contain Investigation

A development workspace may include investigation-like artifacts, but only as secondary material.

Examples:

- baseline runs
- paired comparisons against an existing reference system
- validation measurements

This is desirable, because development needs evidence.

But the workspace remains development if the primary goal is to create or modify the artifact itself.

---

## 9. First Experiment Types

Within the initial `investigation` class, the first draft should recognize at least two experiment types.

### 9.1 Single-System Experiment

A **single-system experiment** investigates one system under defined conditions.

Typical goals:

- understand baseline behavior
- test robustness
- inspect a sweep of one parameter
- observe a newly implemented mechanism in isolation

Examples:

- `System C` baseline in a sparse grid
- `System A` with different energy gain factors
- `System B` in a signal landscape

### 9.2 System-Comparison Experiment

A **system-comparison experiment** investigates differences between two systems under matched conditions.

Typical goals:

- baseline vs. modified system
- ablation comparison
- predictive vs. non-predictive agent
- alternative architectures under identical seeds

Examples:

- `System A` vs. `System C`
- `System A+W` vs. `System C`
- `System B` baseline vs. `System B` with a new scan strategy

### 9.3 Why These Two Come First

These two types cover the immediate practical needs:

- understanding one system
- comparing two systems

They also map directly onto the current framework capabilities.

This keeps the first version realistic.

---

## 10. Experiment Workspace v1

The first version should be deliberately simple.

It should not try to model every future experiment shape.

The goal is:

> clean structure without changing framework behavior

### 10.1 Minimal Workspace Layout

Proposed shape:

```text
experiments/
  <workspace-id>/
    experiment.yaml
    README.md
    notes.md
    configs/
    results/
    comparisons/
    measurements/
    exports/
```

### 10.2 Purpose of Each Element

#### `experiment.yaml`

The workspace metadata file.

It should define:

- experiment identity
- experiment type
- involved systems
- intended scope
- possibly references to primary configs or run artifacts

#### `README.md`

Short human-readable overview.

It should answer:

- what is being investigated
- why this workspace exists
- what the primary artifacts are

#### `notes.md`

Working notes and interpretation.

This can contain:

- observations
- anomalies
- conclusions
- next steps

#### `concept/`

Conceptual and mathematical modeling material for the workspace.

Examples:

- system concept drafts
- world concept drafts
- mathematical notes
- structured specifications before engineering

This folder makes the modeling side of development explicit.

#### `engineering/`

Engineering-oriented implementation planning for the workspace.

Examples:

- engineering specs
- work packages
- component maps
- implementation roadmaps

This folder makes the implementation-concept side of development explicit while still keeping source code outside the workspace.

#### `configs/`

All run configuration files used by the workspace.

These should be copied or curated here as the workspace-local source of truth.

#### `results/`

The raw execution outputs associated with the workspace.

This can initially mirror or reference the framework-generated result tree.

#### `comparisons/`

Derived comparison outputs for system-comparison workspaces.

This is where paired-comparison result artifacts should live.

#### `measurements/`

Derived metrics and processed measurement files.

Examples:

- CSV summaries
- extracted score tables
- stepwise metric exports

#### `exports/`

Optional outward-facing material.

Examples:

- shareable summaries
- selected JSONs
- prepared plots

---

## 11. First Metadata Model

The first draft should already define a minimal conceptual metadata model for `experiment.yaml`.

### 11.1 Required Fields

Suggested first fields:

- `workspace_id`
- `title`
- `workspace_class`
- `workspace_type`
- `status`
- `created_at`

### 11.2 Type-Specific Fields

For `system_development`:

- `artifact_under_development`
- `artifact_kind`

For `world_development`:

- `artifact_under_development`
- `artifact_kind`

For `single_system`:

- `system_under_test`

For `system_comparison`:

- `reference_system`
- `candidate_system`

### 11.3 Optional Structural Fields

Useful optional fields:

- `question`
- `description`
- `tags`
- `baseline_artifacts`
- `validation_scenarios`
- `development_goal`
- `primary_configs`
- `primary_results`
- `primary_comparisons`

### 11.4 Status

A lightweight status field would be helpful from the start.

Example values:

- `idea`
- `draft`
- `running`
- `analyzing`
- `completed`

This would align well with the broader AXIS workflow style:

- idea
- draft
- spec
- implementation
- documentation

---

## 12. `experiment.yaml` as Workspace Manifest

The workspace metadata file should be treated as the **workspace manifest**.

Its role is not to replace run configuration files.

Instead, it should define the identity and structure of the workspace itself.

### 12.1 What `experiment.yaml` Is

`experiment.yaml` should describe:

- what kind of workspace this is
- what artifact or artifacts it is about
- what the primary question or goal is
- which configs belong to it
- which results and comparisons are considered primary outputs

### 12.2 What `experiment.yaml` Is Not

`experiment.yaml` should not directly be the executable framework config.

That is important.

The current AXIS execution layer already has its own config structure for:

- system type
- framework config
- world config
- run execution

The workspace manifest should remain one level above that.

So:

- `experiment.yaml` describes the workspace
- files under `configs/` describe executable runs

### 12.3 Minimal Manifest Skeleton

The first version could conceptually look like this:

```yaml
workspace_id: "system-a-vs-system-c-grid2d-baseline"
title: "System A vs System C in sparse Grid2D baseline"
workspace_class: "investigation"
workspace_type: "system_comparison"
status: "draft"
created_at: "2026-04-17"

question: "How does predictive modulation in System C change behavior relative to System A under matched baseline conditions?"
description: "Baseline paired comparison between System A and System C on sparse Grid2D."
tags:
  - "system-a"
  - "system-c"
  - "comparison"
  - "grid2d"

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
```

This is intentionally not yet a fixed schema, but it is already specific enough to guide practical use.

### 12.4 Manifest Design Principle

The manifest should answer:

- what is this workspace for?
- what is its primary type?
- what artifacts belong here?
- where are the main outputs?

It should not attempt to encode the full execution or comparison internals.

That would collapse the distinction between:

- workspace-level organization
- framework-level execution

which should remain separate for now.

---

## 13. Development Workspace Content

Development workspaces require one additional structural clarification.

### 12.1 Source Code Stays in the Repository

The workspace should not duplicate source code.

Source code remains where it belongs:

- inside `src/`
- inside the actual implementation area of the repo

The workspace should instead contain:

- concept artifacts
- engineering artifacts
- validation artifacts
- references to the implemented code

### 12.2 Concept vs Engineering Must Be Visible

Inside development workspaces, it must remain explicit what belongs to:

- conceptual and mathematical modeling
versus
- engineering and implementation planning

That is why the workspace should already separate:

- `concept/`
- `engineering/`

This matters because AXIS development is not only code-first.

The model/specification chain is part of the development process itself and should therefore be visible in the workspace structure.

---

## 14. Relationship Between Workspace Results and Framework Results

This is one of the most important open points in the entire concept.

The draft should make a first clear recommendation.

### 14.1 Current Situation

The framework currently writes results into a repository-like output tree under:

- `experiments/results/`

This is a good operational execution structure.

But it is not yet a workspace-centered structure.

### 14.2 Recommendation for v1

The first version of the Experiment Workspace should **not** try to replace the framework's result repository.

Instead, it should treat the existing framework output as the execution backend and establish a workspace-level organization on top of it.

So the v1 relationship should be:

- framework results remain framework-owned execution artifacts
- workspace results provide the experiment-centered view of what belongs to this workspace

### 14.3 Two Possible Models

There are two possible ways to do this.

#### Model A -- Copy Results into Workspace

The workspace physically contains copies of run and comparison outputs.

Pros:

- self-contained workspace
- easier export or archival

Cons:

- duplication
- synchronization problems
- unclear ownership between framework repo and workspace repo

#### Model B -- Reference Framework Results

The workspace points to framework-owned results and only stores curated or selected outputs locally.

Pros:

- avoids duplication
- respects the existing execution repository
- cleaner ownership model

Cons:

- workspace is not fully self-contained
- requires explicit references

### 14.4 Recommended Model for the First Draft

The first draft should clearly prefer:

> **Model B -- Reference Framework Results**

This means:

- raw execution outputs remain in the framework results repository
- the workspace stores references, selected exports, derived measurements, and notes

That is the better first step because it avoids premature duplication and keeps the existing framework behavior intact.

### 14.5 Meaning of `results/` Inside the Workspace

Under this recommendation, workspace-local `results/` should not initially be understood as a second raw execution repository.

Instead, it should contain one of the following:

- curated links or references to framework result artifacts
- selected copied outputs that the workspace wants to preserve explicitly
- workspace-local result manifests that point to framework experiment/run IDs

So in v1, `results/` is better thought of as:

> workspace-level result mapping and selected artifacts

not as a mandatory duplication of all framework outputs.

### 14.6 Consequence for Practical Use

This means a workspace can already be useful without any framework change:

- configs live in the workspace
- runs are executed through existing AXIS mechanisms
- raw results remain in the framework result repository
- the workspace records which result artifacts belong to the investigation
- comparisons and measurements can then be collected back into the workspace

That is a pragmatic and low-risk first version.

---

## 15. Referencing Framework-Owned Artifacts

If the workspace does not own all raw results, it needs a clean way to reference them.

The first draft should therefore introduce a small conceptual distinction:

- **primary artifacts**
- **resolved execution artifacts**

### 15.1 Primary Artifacts

Primary artifacts are the workspace-local files that define or summarize the investigation.

Examples:

- `experiment.yaml`
- `README.md`
- selected configs
- selected comparison outputs
- measurements

### 15.2 Resolved Execution Artifacts

Resolved execution artifacts are framework-owned outputs that the workspace points to.

Examples:

- framework experiment IDs
- run IDs
- episode trace locations
- comparison inputs resolved from repository artifacts

### 15.3 Possible Manifest Fields

To support this, `experiment.yaml` may later include fields such as:

- `linked_experiments`
- `linked_runs`
- `linked_comparisons`

Example:

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

This is not yet fixed schema, but it shows the right direction:

the workspace manifest links to execution artifacts instead of trying to absorb them all blindly.

---

## 16. Recommended Workspace Interpretation by Class

The role of `configs/`, `results/`, `comparisons/`, and `measurements/` depends slightly on workspace class.

### 16.1 Development Workspace

In development:

- `concept/` and `engineering/` are primary
- `configs/` contains validation and baseline configs
- `results/` points to validation outputs
- `comparisons/` contains evidence against baselines or previous designs
- `measurements/` contains validation summaries

### 16.2 Investigation Workspace

In investigation:

- `configs/` is primary for reproducible execution
- `results/` records linked or selected execution outputs
- `comparisons/` is primary in comparative workspaces
- `measurements/` contains extracted analytical summaries
- `concept/` and `engineering/` are minimal or absent unless needed

This difference should be explicit in the later spec.

---

## 17. Two Example Workspace Types

The workspace model becomes clearer when shown concretely.

### 17.1 Example A -- System Development Workspace

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
    comparisons/
      system-a-vs-system-d/
    measurements/
      validation-summary.csv
    exports/
```

Meaning:

- the primary purpose is to build a new system
- concept and engineering are first-class
- runs and comparisons are validation material
- source code still lives elsewhere in the repo

### 17.2 Example B -- Single-System Investigation Workspace

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
      run-0000/
      run-0001/
    comparisons/
    measurements/
      run-summary.csv
      vitality-curves.csv
    exports/
```

Meaning:

- one system is studied
- multiple runs or conditions may still exist
- comparisons may remain empty
- measurements focus on behavior and performance of one system

Here `concept/` and `engineering/` may remain empty or minimal because investigation does not primarily develop the artifact.

### 17.3 Example C -- System-Comparison Investigation Workspace

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
      reference/
      candidate/
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

Meaning:

- the workspace is explicitly comparative
- the reference/candidate structure is visible at the filesystem level
- comparison artifacts are first-class rather than implicit

---

## 18. Why This Should Come Before Framework Changes

The first step should not be adding complexity to the framework.

The first step should be:

> establish a clean organizational convention around the current framework

This is better because:

- it clarifies the real experimental workflow before coding abstractions
- it reduces the chance of hard-coding the wrong experiment model into the framework
- it lets the team test the structure in practice first

This is especially important because the right abstraction boundary is not yet fully obvious.

For example:

- should a workspace own results physically or only reference them?
- should comparisons be generated inside the framework or by CLI workflow?
- should `experiment.yaml` become framework-readable later?

These should be informed by practical use first.

---

## 19. Practical First Evaluation

The next concrete step after this draft should be a practical trial with at least two workspace types.

### 19.1 Trial Type A

Create one real **system development workspace**.

Goal:

- verify whether concept, engineering, validation, and notes fit together coherently

### 19.2 Trial Type B

Create one real **system-comparison workspace**.

Goal:

- verify whether configs, results, comparisons, and measurements fit naturally into one shared workspace

### 19.3 What to Observe

The practical trial should answer:

- is the folder structure too heavy or too loose?
- do users know where to put derived artifacts?
- is `experiment.yaml` expressive enough?
- does the workspace cleanly separate raw results from derived material?
- is the distinction between concept and engineering clear enough?
- is development clearly distinguishable from investigation?
- what friction remains for CLI usage?
- does referencing framework-owned results feel natural or awkward?
- do users need more explicit run-link metadata in `experiment.yaml`?

---

## 20. Long-Term Direction

If the workspace concept proves useful in practice, later framework support may become justified.

Possible later framework-facing steps:

- workspace-aware CLI commands
- workspace-aware result routing
- framework-readable experiment metadata
- comparison output placement conventions
- automatic linking between runs and comparisons

But none of this should be assumed yet.

The first version should remain:

- filesystem-based
- human-comprehensible
- framework-independent

---

## 21. Relationship to the AXIS Development Chain

This experiment-workspace concept should follow the same staged process already used elsewhere in AXIS:

- idea
- draft
- spec
- implementation
- documentation

The full chain should be documented explicitly.

That means this area should eventually contain:

- idea-level discussion
- draft documents
- later specification documents
- engineering planning
- public documentation once stabilized

This is important because experiment organization is now becoming a first-class part of AXIS, not just an ad hoc project folder habit.

---

## 22. Summary

The central proposal of this draft is:

> AXIS experiment work should be organized as explicit workspaces, not merely as loose config files plus raw results

The first key distinction is:

- `development`
- `investigation`

Within that, the first concrete workspace types should include:

- `system_development`
- `world_development`
- `single_system`
- `system_comparison`

An Experiment Workspace should:

- define what is being investigated
- or what is being developed
- bundle the input configs
- contain or reference the produced results
- store comparisons
- store derived measurements
- preserve notes and interpretation
- preserve conceptual and engineering artifacts where development is involved

The first version should remain lightweight and file-based.

The first practical evaluation should test at least:

- one development workspace
- one system-comparison workspace

Only after that should later framework or SDK integration be considered.
