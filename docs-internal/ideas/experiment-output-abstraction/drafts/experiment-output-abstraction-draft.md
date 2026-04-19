# Experiment Output Abstraction Draft

## Purpose

This draft proposes a first conceptual abstraction for **experiment outputs**
in AXIS-CMS.

The immediate motivation is the mismatch between:

- the current Workspace model, which is effectively built around
  **single-run-oriented results**, and
- the existing framework-level `ofat` experiment type, which produces a
  **parameter sweep** with multiple runs and sweep-specific summary semantics.

The goal of this draft is **not** to redesign the persistence layer.
Instead, it proposes a higher-level abstraction that should sit:

- above the current filesystem repository and persistence code,
- at the framework level,
- below the Workspace layer.

This would make both framework behavior and Workspace behavior more coherent and
extensible.


## Problem

### Current framework reality

At the framework level, AXIS already supports two experiment execution modes:

- `single_run`
- `ofat`

Both are modeled as `ExperimentConfig` values and both are persisted under a
single experiment directory.

This means the low-level storage model is already unified enough:

- one `experiment_id`
- one experiment config
- one experiment summary
- one or more run directories

So the primary problem is **not** that the repository layout is incompatible.

### Current workspace reality

Current Workspace workflows are centered around results that are effectively
treated as:

- "one executed config"
- "one meaningful run target"
- "one comparison side"

This fits `single_run` well, because a `single_run` experiment produces exactly
one concrete run.

However, it does not fit `ofat` well, because an OFAT experiment produces:

- multiple runs
- one varying parameter
- a sweep-level summary with deltas
- an ordered set of variations that are meaningful as a group

In other words:

- `single_run` behaves like a **point result**
- `ofat` behaves like a **sweep result**

The current Workspace model does not express that distinction explicitly.

### Current architectural layering

The current AXIS stack is already naturally layered:

- step
- episode
- run
- experiment
- workspace

The `single_run` vs `ofat` distinction already exists at the
**experiment level**.

This is important:

- `single_run` is not a workspace-specific concept
- `ofat` is not a workspace-specific concept

Both are already first-class framework concepts defined by
`ExperimentConfig`, expanded in `experiment.py`, and persisted by the
experiment repository.


## Core Observation

The main difference between `single_run` and `ofat` is not primarily the
directory layout on disk, but the **semantic shape of the experiment output**.

This suggests that the right abstraction point is:

- **not** the persistence layer,
- and also **not** only the Workspace layer,
- but a framework-level interpretation layer that sits between:
  - persisted experiment artifacts
  - and consumers such as CLI, Workspace, comparison routing, and
    visualization routing.


## Draft Proposal

Introduce a conceptual abstraction called **Experiment Output**.

An Experiment Output is the framework-level interpretation of a completed
experiment artifact tree.

Workspaces would then consume Experiment Outputs rather than invent their own
output semantics.

At minimum, the abstraction should distinguish two output forms:

- **Point Output**
  - represents a `single_run` experiment
  - operationally centered on one concrete run
- **Sweep Output**
  - represents an `ofat` experiment
  - operationally centered on a run set plus sweep-level summary semantics


## Why This Abstraction Helps

### 1. It matches existing framework semantics

The framework already distinguishes:

- one-run experiments
- multi-run sweep experiments

The abstraction simply makes this distinction explicit at the framework output
layer.

### 2. It prevents forced run-level flattening

Without the abstraction, OFAT support tends to collapse into one of two bad
options:

- pretend an OFAT experiment is just "many normal runs"
- or compare only the first and last run and lose sweep semantics

Both approaches destroy important meaning.

### 3. It keeps persistence stable

No storage redesign is required up front.

The current repository layout can remain:

- experiment root
- experiment summary
- run directories

The new abstraction would interpret these artifacts rather than replace them.

### 4. It gives the whole framework a stable semantic contract

Today, several consumers implicitly assume "result = run-like thing" or
"result = experiment whose interesting part is a single run".

With an Experiment Output abstraction, framework consumers can instead say:

- "result = interpreted experiment output"

and then branch by output form:

- point
- sweep

Workspaces would simply be one consumer of that abstraction.


## Proposed Output Forms

### Point Output

Represents an experiment whose meaningful operational result is a single run.

Likely characteristics:

- `experiment_type = single_run`
- exactly one run
- one primary run summary
- one primary set of episode traces
- direct compatibility with existing compare/visualize behavior

### Sweep Output

Represents an experiment whose meaningful operational result is an ordered sweep
over one parameter.

Likely characteristics:

- `experiment_type = ofat`
- multiple runs
- one `parameter_path`
- ordered `parameter_values`
- one baseline run
- one experiment summary containing cross-run delta semantics

The important point is that the sweep should be treated as one meaningful
artifact, not merely as a bag of unrelated runs.


## Minimal Conceptual Model

This draft does not define final types yet, but the conceptual model would
likely need common fields such as:

- `experiment_id`
- `workspace_relative_path`
- `system_type`
- `experiment_type`
- `output_form`
- `created_at`
- `config_path`
- `role`
- `num_runs`

Then output-form-specific fields:

For Point Output:

- `primary_run_id`
- `primary_run_path`

For Sweep Output:

- `parameter_path`
- `parameter_values`
- `baseline_run_id`
- `run_ids`
- `summary_path`


## Where The Abstraction Should Live

The abstraction should initially live in a **framework-level experiment output
layer**, not in low-level repository code.

That means it would likely affect:

- experiment result interpretation
- CLI inspection and summary rendering
- workspace manifest semantics
- workspace summary rendering
- workspace run synchronization
- workspace comparison resolution
- workspace visualization resolution

It should **not** require changing:

- `ExperimentRepository`
- `ExperimentExecutor`
- existing experiment persistence layout

at least not in v1.

Conceptually, the abstraction belongs:

- above `ExperimentRepository`
- above raw `ExperimentResult`
- below `workspaces/`

Possible implementation placement could later be something like:

- `axis.framework.experiment_output`
- or `axis.framework.outputs`

This draft does not fix the final module name yet.


## Relationship to Current Workspace Types

### Investigation / Single System

This is the most natural future home for Sweep Output support at the Workspace
level.

Why:

- the workflow already studies one system under changing parameters
- OFAT is a stricter, more structured form of parameter study

### Investigation / System Comparison

This workspace type currently assumes a reference/candidate comparison between
two concrete experiment sides.

Sweep support here would be substantially more complex:

- point vs point
- sweep vs point
- sweep vs sweep

This should not be part of an initial abstraction rollout.

### Development / System Development

This workflow is intentionally baseline/candidate oriented and should remain
simple.

The current recommendation is:

- keep `system_development` limited to point outputs in v1
- do not introduce Sweep Output support there initially


## Recommended Scope For The Refactoring

### In scope

- define the concept of Experiment Output
- distinguish Point Output vs Sweep Output
- shift framework and Workspace thinking from "result path = run" to
  "result = interpreted experiment output artifact"
- prepare the Workspace layer for future OFAT support by moving output semantics
  below it

### Out of scope

- redesigning the repository layout
- changing direct experiment execution behavior
- adding immediate OFAT support to all workspace types
- introducing sweep-aware comparison behavior in the first step


## Immediate Benefit Even Before OFAT Support

Even before OFAT is supported in Workspace mode, this abstraction would improve
the design by making the current assumptions explicit across the framework:

- existing workspace workflows currently support Point Outputs
- Sweep Outputs are a known but unsupported output form

That is already better than implicitly encoding point-output assumptions across
CLI, Workspace routing, and result handling.


## Open Questions

1. Should `primary_results` eventually point to experiment roots rather than
   run directories?
2. Should the output form be derived from `experiment_type`, or persisted as an
   explicit workspace-level artifact classification?
3. Should visualization resolve from an Experiment Output first, then select a
   run, instead of starting directly from run paths?
4. Should future OFAT support introduce a separate `primary_sweeps` field, or
   should sweep artifacts remain inside a unified `primary_results` model?
5. Should Workspace summaries show both experiment-level and run-level views
   for Sweep Outputs?


## Draft Recommendation

Proceed with a focused refactoring that introduces **Experiment Output** as a
framework-level abstraction above persistence and below Workspace behavior.

The first design target should be:

- unify current framework and Workspace semantics around interpreted experiment
  outputs
- keep the repository unchanged
- explicitly model the distinction between:
  - point outputs
  - sweep outputs

This creates a stable foundation for future OFAT support in
`investigation/single_system` without forcing premature complexity into the
rest of the Workspace system.
