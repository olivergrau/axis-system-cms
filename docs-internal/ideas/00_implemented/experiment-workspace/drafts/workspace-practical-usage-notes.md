# Experiment Workspace -- Practical Usage Notes

## Where Framework Support Becomes Essential

This document summarizes the practical friction points observed while
walking through the current probe workspaces using the existing AXIS
command model from the public manuals.

The main conclusion is:

> the current workspace model is already usable as a semantic container,
> but it is not yet a cohesive execution environment

The largest unresolved issue is result ownership and placement.

---

## 1. The Central Tension

The existing AXIS execution model places raw execution outputs outside the
workspace under the normal framework result root.

That remains a valid mode.

However, in practical usage it creates repeated friction when the workspace
is treated as the primary work context:

- execute from workspace config
- outputs are created outside the workspace
- user must discover new experiment IDs
- user must manually link or summarize those outputs back into the workspace

This weakens the workspace as the primary operational context.

The strongest practical refinement is therefore:

> AXIS should support creating execution artifacts directly inside the workspace in a structured way

This would make the workspace not only the semantic home of the work,
but also the operational home of its results.

The current simple path-based execution model should still remain available.

---

## 2. Essential Framework / CLI Support Points

These are the points that feel truly essential rather than just convenient.

### 2.1 Workspace-Aware Scaffolding

Why essential:

- without it, users will create structurally inconsistent workspaces
- the spec is too rich to expect manual creation every time

Needed support:

- `axis workspaces scaffold`
- interactive prompting
- type-aware manifest generation
- baseline config generation

### 2.2 Workspace Validation and Consistency Checks

Why essential:

- the model has many structural rules
- manual checking will drift quickly

Needed support:

- `axis workspaces check`
- manifest validation
- required-directory validation
- linked-artifact checks
- contradiction detection between manifest and helper files

### 2.3 Workspace-Aware Result Placement

Why essential:

- this is the biggest practical pain point in every workflow
- without it, the workspace never becomes the real operational center

Needed support:

- ability to execute a workspace config and route outputs into the workspace in a structured way
- or at minimum, automatic registration/linking of newly created framework results back into the workspace

This point should be treated as a major engineering support area.

### 2.4 Workspace-Aware Summary / Introspection

Why essential:

- users need a quick way to understand a workspace as a working object

Needed support:

- `axis workspaces show`
- one place to view manifest, primary configs, linked results, and state

### 2.5 Workspace-Aware Comparison Routing

Why essential for comparison workspaces:

- today `axis compare` produces output, but the workspace must be updated manually

Needed support:

- comparison output should be placeable or registrable directly in the workspace

---

## 3. Strongly Useful but Slightly Less Essential

These are highly useful, but slightly less foundational than the five points above.

### 3.1 Workspace Readiness Checks

Examples:

- structurally valid
- execution-ready
- analysis-ready

### 3.2 Drift Detection

Examples:

- manifest references missing artifacts
- helper files disagree with manifest
- likely primary artifacts are present but undeclared

### 3.3 Role Completeness Checks

Especially useful for:

- `system_comparison`

Examples:

- missing reference/candidate config pairing
- missing linked run on one side

---

## 4. Most Important Spec Refinement

The largest conceptual issue is this:

### Current model

- configs live in the workspace
- raw outputs live outside the workspace
- workspace stores links or helper manifests

### Practical problem

This keeps forcing the user to move mentally between:

- workspace context
- framework output repository

That undermines the workspace as the main unit of work.

### Strong refinement direction

The refined workspace model should explicitly support:

> workspace-owned structured output placement

This does not require deleting the existing simple framework result model.

Instead, AXIS should support both:

- simple execution by config path
- workspace-aware execution with structured output placement

That would preserve backward compatibility while making workspaces much more coherent in practice.

---

## 5. Recommended Discussion Points

These are the points worth refining together before implementation:

1. Should raw execution artifacts ultimately be created inside the workspace?
2. If yes, should the workspace hold:
   - full raw result trees
   - or a workspace-scoped result subtree with references to lower-level artifacts
3. Should `axis experiments run <config>` remain untouched while a new workspace-aware command is added?
4. Should `axis compare` gain a workspace-aware output-routing mode?
5. Should helper artifacts remain optional once workspace-aware result placement exists?

---

## 6. Summary

The practical walkthroughs show that the current workspace model is already useful for:

- orientation
- organization
- documentation
- manual linking

But they also show a clear next pressure point:

> workspaces need structured execution and comparison output handling if they are to become the true operational context

That is the main area where future framework and CLI support becomes both essential and high-value.
