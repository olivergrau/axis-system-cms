# System Development Workflow -- Brainstorm

## Purpose

This document explores the operational workflow for the workspace type:

- `development / system_development`

The goal is not yet to define a final spec.

The goal is to clarify:

- what the actual development chain looks like
- which parts of that chain should live inside the workspace
- which parts can already be supported by the current workspace model
- which parts may later justify additional workspace tooling

---

## 1. Starting Point

For `system_development`, the user is not primarily studying an already
finished artifact.

The user is trying to create a new system architecture and iterate toward a
working implementation.

That means the workspace is not only:

- an execution container
- a comparison container

It is also:

- a design container
- a specification container
- a validation container

This makes `system_development` fundamentally broader than
`investigation / single_system` or `investigation / system_comparison`.

---

## 2. The Development Chain

The practical chain currently looks like this:

1. mathematical concept
2. worked examples
3. formal specs
4. engineering specs / implementation planning
5. implementation
6. first validation runs
7. comparison and analysis
8. refinement of concept/spec/implementation
9. repeated validation

This is not a linear one-pass process.

It is an iterative loop.

The important implication is:

> a `system_development` workspace must support both pre-implementation
> intellectual work and post-implementation validation work

---

## 3. What Should Clearly Live Inside the Workspace

From the current AXIS model, these things should clearly belong inside the
workspace.

### 3.1 Concept artifacts

These belong under:

- `concept/`

Examples:

- mathematical model draft
- system rationale
- worked examples
- reduction cases
- open questions

### 3.2 Engineering artifacts

These belong under:

- `engineering/`

Examples:

- engineering spec
- work packages
- implementation sequencing
- risk notes
- validation plan

### 3.3 Executable configs

These belong under:

- `configs/`

Examples:

- baseline validation configs
- candidate system configs
- regression configs

### 3.4 Validation outputs

These belong under:

- `results/`
- `comparisons/`
- `measurements/`

Examples:

- baseline run artifacts
- candidate run artifacts
- comparison outputs
- summary measurements

### 3.5 Working notes

These belong under:

- `notes.md`

This is important because development is not only about static docs and raw
results, but about capturing interpretation during iteration.

---

## 4. What Probably Does Not Need Dedicated Tool Support Yet

The full development chain contains some parts that should live in the
workspace, but do not yet require dedicated CLI support.

These include:

- writing concept documents
- writing worked examples
- writing specs
- writing engineering planning documents
- updating notes after analysis

The workspace should support these first by:

- providing the correct locations
- making the workflow explicit
- keeping the execution and comparison outputs adjacent to these documents

This is probably enough for v1.

So the first strong idea is:

> `system_development` should initially be supported more by structured
> placement and workflow clarity than by document-authoring automation

---

## 5. What the Workspace Should Support Operationally

Even if concept/spec authoring remains manual, the workspace should still
support the operational side of development strongly.

These support points seem especially valuable.

### 5.1 Scaffold the development structure

This already fits the existing model well.

The workspace should scaffold:

- `concept/`
- `engineering/`
- baseline configs
- workspace manifest
- notes and measurement placeholders

### 5.2 Run validation baselines

Before the new system exists, development often starts by running baseline
systems.

This gives:

- behavioral anchors
- reference metrics
- reference traces

This should be supported through:

- `axis workspaces run <workspace>`

with the workspace deciding which baseline configs are the current validation
set.

### 5.3 Compare candidate vs baseline

Once the new system exists, the workspace should support:

- candidate-vs-baseline comparison
- maybe candidate-vs-candidate comparison later

This should be supported through:

- `axis workspaces compare <workspace>`

### 5.4 Keep workspace-local artifact history

Development is iterative.

So the workspace should preserve:

- earlier runs
- earlier comparisons
- earlier measurements

This matters because development frequently needs:

- regression checks
- comparison against earlier design states
- evidence for why a design changed

### 5.5 Visualization during validation

Once validation artifacts exist, replay should be workspace-local as well.

This supports:

- understanding failures
- checking if the implemented behavior matches the concept
- diagnosing unexpected policy structure

---

## 6. Candidate Operational Workflow for `system_development`

The following looks like a plausible first operational workflow.

### Phase A -- Pre-implementation design

1. scaffold workspace
2. write concept documents under `concept/`
3. write worked examples under `concept/`
4. write formal specs under `concept/` or `engineering/`
5. write implementation planning under `engineering/`

This phase is mostly manual documentation work.

### Phase B -- Baseline orientation

1. prepare baseline configs under `configs/`
2. run workspace baselines
3. inspect results under `results/`
4. inspect replay through workspace visualization
5. write observations into `notes.md`
6. write summary metrics under `measurements/`

This gives a behavioral anchor before the new system is implemented.

### Phase C -- First candidate validation

1. add candidate system config(s) to `configs/`
2. run workspace
3. compare candidate vs baseline
4. inspect comparison result
5. visualize candidate and baseline traces
6. update notes, measurements, concept, or engineering docs

### Phase D -- Iterative refinement

1. change implementation
2. rerun workspace
3. rerun comparison
4. inspect differences
5. update docs and notes
6. repeat

This seems to be the real core loop.

---

## 7. Possible Manifest Semantics for Development

The biggest unresolved question is how a `system_development` workspace should
express its current validation state.

There are several plausible options.

### Option A -- Keep it simple

Use:

- `primary_configs`
- `primary_results`
- `primary_comparisons`
- `primary_measurements`

only.

Interpretation:

- the current validation set is whatever the primary fields point to

Advantage:

- minimal model

Disadvantage:

- baseline vs candidate semantics are less explicit

### Option B -- Add explicit validation roles later

Potential future fields:

- `baseline_configs`
- `candidate_configs`
- `baseline_results`
- `candidate_results`

Advantage:

- clearer development semantics

Disadvantage:

- makes the manifest model more complex

### Current recommendation

For now, Option A is probably sufficient.

Use the existing `primary_*` fields first, and encode role semantics through:

- config naming
- comparison logic
- documented workflow conventions

This keeps v1 simpler.

---

## 8. Where New Tool Support May Eventually Help

The following are possible later extensions, but likely not needed
immediately.

### 8.1 Concept / engineering index helpers

A workspace tool could later summarize:

- which concept docs exist
- which engineering docs exist
- which are still missing

This could be useful, but is not essential for the first implementation.

### 8.2 Workspace readiness states for development

Possible future states:

- concept-ready
- spec-ready
- implementation-ready
- validation-ready

This would fit development better than pure structural validity.

### 8.3 Explicit validation-set management

Later, a workspace might support commands like:

- set current baseline
- set current candidate
- pin validation pair

This may become useful once multiple candidate runs accumulate.

### 8.4 Documentation templates

Later, scaffolding could create:

- concept template
- worked example template
- engineering spec template

This is valuable, but probably not the first priority.

---

## 9. Strongest Current Recommendation

The strongest current recommendation is:

> for `development / system_development`, the workspace should first be a
> structured design-and-validation container, not an automated authoring system

This means:

- concept/spec/engineering documents live inside the workspace
- writing them stays manual for now
- execution, comparison, and visualization should be strongly supported
- iteration is captured by keeping results, comparisons, measurements, and
  notes inside the same workspace

This is likely the most practical v1 shape.

---

## 10. Open Questions

These questions should be refined before turning this into a detailed draft.

1. Should `system_development` compare the latest candidate against the latest
   baseline by default, or should the user have to pin the pair explicitly?
2. Should development workspaces allow more than one candidate config at a
   time in the initial model?
3. Should worked examples be treated as concept artifacts or as their own
   dedicated artifact class?
4. Should `comparison-result` be considered a central development command, or
   only a secondary inspection tool?
5. Should the workspace manifest stay generic, or should development get
   stronger role-specific fields later?

---

## 11. Next Step

The next useful step would be:

> derive a more concrete `system_development` workflow draft from this
> brainstorm, including explicit command sequences and artifact responsibilities

That draft can then become the basis for:

- a refined manual workflow
- an engineering extension plan
- and later implementation changes if needed
