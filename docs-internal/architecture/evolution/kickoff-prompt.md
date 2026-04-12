You are working inside the AXIS / System A repository.

Your task is **not to implement code yet**.

Your task is to create a **reusable kickoff document for future Claude Code agents and human developers** that explains the next architectural milestone in the context of the **current implemented system**.

---

## Primary Objective

Read and understand the documents:

```text
docs/architecture/v0.1.0/*
docs/architecture/evolution/Modular Architecture Evolution.md
docs/specs/*
```

You can and should also read existing source code.

This Modular Architecture Evolution.md document defines the next major milestone of the project:

* transition from a single-system implementation toward a modular framework
* separation of System SDK, World Framework, Experimentation Framework, Persistence, and Visualization
* support for future systems such as `System A`, `System A+W`, and further variants
* explicit interface-based development, not duck typing
* a global replay contract
* execution owned by the experimentation framework, not by individual systems

Your job is to:

1. **read and understand this target vision**
2. **understand the current architecture from the actual codebase**
3. **check whether the target direction is internally coherent**
4. **identify major alignment points, architectural tensions, and likely refactoring fronts**
5. **create a markdown kickoff document** that can be reused by future developers / Claude Code agents as the starting foundation for the next milestone

---

## Important Working Mode

Do **not** rely only on the vision document.

You must analyze both:

* the **target architecture vision** from `Modular Architecture Evolution`
* the **current implemented architecture** from the actual solution/codebase

Use:

* source code
* existing architecture docs
* existing work package docs where useful
* tests where helpful to confirm implementation reality

The result must be grounded in:

* what currently exists
* what the target milestone wants to achieve
* where these two currently align or conflict

---

## Expected Output

Create a markdown document at:

```text
docs/architecture/evolution/modular-architecture-kickoff.md
```

---

## What This Kickoff Document Must Achieve

The document should be reusable as a **starting brief for future implementation work** in VS Code with Claude Code support.

It should allow a future agent or developer to quickly understand:

* where the project stands now
* what architectural evolution is intended next
* what has to change at a high level
* what should remain stable
* what the major refactoring fronts are

This is a **kickoff and guidance document**, not a detailed implementation spec.

---

## Required Tasks Before Writing

### 1. Read the vision

Read and understand the `Modular Architecture Evolution` document carefully.

### 2. Read the current implementation

Inspect the codebase and understand the current implemented architecture, especially:

* runtime architecture
* experiment framework
* persistence layer
* resume logic
* CLI
* replay / visualization assumptions

### 3. Cross-check the current state against the target vision

Assess:

* what already supports the vision
* what is still tightly coupled
* what likely needs extraction or refactoring
* whether the proposed phases in the vision are sensible and internally consistent

### 4. Validate the milestone framing

Critically assess whether the target architecture direction is coherent.
Do not just agree.
If there are tensions, risks, unclear boundaries, or missing assumptions, state them clearly.

---

## Required Structure of the New Document

The new document should contain sections similar to the following.

---

### 1. Purpose of This Kickoff Document

Explain that this document is the starting point for the next major architectural milestone.

---

### 2. Current Implemented Architecture

Summarize the current real architecture of the repository as implemented today.

Focus on:

* System A current shape
* Experimentation Framework
* Persistence / Repository
* Resume behavior
* CLI
* Visualization assumptions / replay dependency

This should be concise but concrete.

---

### 3. Target Architectural Direction

Summarize the intended future direction from `Modular Architecture Evolution`.

This should include:

* System SDK
* World Framework
* Experimentation Framework
* Persistence Layer
* Visualization Layer
* explicit contracts and interface-driven development

---

### 4. Architectural Delta: Current State vs Target State

Describe the difference between:

* what exists now
* what the next milestone wants to achieve

Use a structured comparison.

Examples:

* what is currently System A-specific
* what is already generic enough
* what is currently mixed that should be separated
* what can likely remain stable

Tables are welcome here.

---

### 5. Consistency Check of the Proposed Direction

Assess whether the proposed milestone direction is internally coherent.

Explicitly evaluate:

* Is the definition of “System” consistent?
* Is the ownership of execution vs system logic clear?
* Is world ownership clear enough?
* Is a global replay contract realistic?
* Is partial system-aware visualization compatible with the modularization goal?
* Are the proposed high-level phases sensible?

If you see contradictions, risks, or underspecified boundaries, state them.

---

### 6. Major Refactoring Fronts

Identify the main architectural work areas likely required to move from current state to target state.

Examples might include:

* extraction of System SDK interfaces
* re-homing of runtime execution concerns
* decoupling current System A modules from experiment execution
* formalizing world contracts
* aligning replay/result contracts
* checking CLI / repository assumptions against multi-system support

Do not produce implementation detail yet.
Keep it high-level but concrete.

---

### 7. Proposed Milestone Phases

Review the phases suggested in `Modular Architecture Evolution`.

Assess whether they make sense in the current repository context.

If sensible, restate them in a clean and implementation-oriented way.
If needed, refine them slightly for clarity, but do not redesign the milestone from scratch.

---

### 8. Stability Boundaries

Identify what should remain stable during this milestone.

Examples:

* experiment artifact philosophy
* repository persistence model
* replay-based visualization model
* run/experiment abstraction
* deterministic execution principles

This section is important because future agents should know what **not** to casually break.

---

### 9. Risks and Open Questions

List the most important risks, ambiguities, or architecture decisions that still need careful treatment before implementation begins.

These should be real and specific, not generic.

---

### 10. Recommended Use of This Document

Explain how future Claude Code agents or developers should use this kickoff doc:

* as orientation
* as milestone context
* as a constraint document before detailed specs are written

---

## Style Requirements

Write in **clear technical English**.

The document should be:

* architecturally serious
* implementation-aware
* readable by a new developer
* critical where needed
* not fluffy
* not overly detailed

Use Markdown features freely:

* headings
* bullet lists
* numbered lists
* tables
* code fences
* ASCII diagrams

---

## Important Constraints

* Do **not** implement code
* Do **not** create detailed class/interface specs yet
* Do **not** drift into redesign proposals beyond milestone framing
* Do **not** write generic software architecture filler
* Do **not** just restate the vision doc
* Always compare target vision against the current implementation reality

---

## Quality Bar

A good result will feel like:

> a reusable architectural kickoff brief for the next milestone,
> grounded in the real repository,
> helpful for both Claude Code agents and human developers.

Before finishing, make sure:

* the document is implementation-grounded
* the target milestone is critically assessed
* the major refactoring fronts are clearly visible
* the document can realistically be reused as a kickoff basis for future work

Now analyze the repository and create:

```text
docs/architecture/evolution/modular-architecture-kickoff.md
```
