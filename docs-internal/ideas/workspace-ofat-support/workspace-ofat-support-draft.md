# Workspace OFAT Support Draft

## Purpose

This draft explores whether and how `ofat` experiment support should be added to
AXIS Experiment Workspaces.

The immediate motivation is:

- direct experiment execution already supports `experiment_type = ofat`
- Workspace mode currently supports only `single_run`
- the newly introduced Experiment Output abstraction now distinguishes:
  - `point`
  - `sweep`

This creates a natural foundation for a future Workspace treatment of OFAT, but
it does not yet define the workflow semantics.


## Starting Point

The current Workspace system already supports three concrete workflows:

- `investigation / single_system`
- `investigation / system_comparison`
- `development / system_development`

These workflows are currently shaped around **point outputs**.

That is appropriate because they assume operations such as:

- run a config
- get one concrete experiment result
- compare one result against another
- visualize one selected result

OFAT does not fit this directly.


## Core Observation

There is an important overlap between:

- normal Workspace iteration
- OFAT parameter sweeps

Both involve:

- changing parameters
- executing again
- observing differences

However, they are not the same thing.

### Normal Workspace iteration

This is flexible and exploratory:

- one or many parameters may change
- changes may be irregular between iterations
- the key comparison pattern is usually:
  - old result vs new result

### OFAT

This is stricter and more structured:

- exactly one parameter varies
- a fixed ordered value set is declared
- all other parameters remain constant
- the run family is meaningful as a whole
- the important result is not just “first vs last”, but the behavior of the
  entire sweep

This means:

> normal Workspace iteration may include informal parameter exploration, but it
> is not equivalent to OFAT


## Established Direction

The strongest current design direction is:

- if OFAT is supported in Workspace mode at all,
- it should first be supported only for:
  - `investigation / single_system`

It should **not** initially be supported for:

- `investigation / system_comparison`
- `development / system_development`


## Why Only `investigation / single_system`

### It is the natural fit

`single_system` already studies one system under changing conditions.

That makes it the most natural home for:

- controlled parameter sweeps
- sweep summaries
- sweep-specific measurements

### It keeps the problem bounded

If OFAT were introduced into `system_comparison`, the framework would soon need
to answer questions such as:

- point vs point
- point vs sweep
- sweep vs point
- sweep vs sweep

This is much larger than the actual immediate need.

### It preserves development simplicity

`system_development` is intentionally built around:

- one baseline
- one candidate
- direct validation

Introducing sweep semantics there too early would weaken that clarity.


## Key Principle

OFAT in Workspaces should **not** be implemented as:

- “just run many runs and compare the first and last one”

That would discard the essential meaning of OFAT.

The correct center of gravity is:

- the sweep as a whole
- not only individual run pairs inside the sweep


## Consequence of the Experiment Output Refactor

The recent Experiment Output refactor introduced two explicit output forms:

- `point`
- `sweep`

This is important because Workspace OFAT support no longer needs to invent its
own output semantics.

Instead, it can build on the framework-level output model:

- a `single_run` Workspace execution produces a point output
- an `ofat` Workspace execution would produce a sweep output

This means the real open question is no longer:

> “Can Workspaces somehow store OFAT results?”

but rather:

> “What should a Workspace do with a sweep output?”


## Candidate Behavioral Models

### Option A: No OFAT support in Workspaces

Keep OFAT only in direct experiment mode.

Advantages:

- simplest model
- current Workspace workflows stay clean

Disadvantages:

- parameter sweeps stay outside the structured Workspace workflow
- users must leave the Workspace model for a common investigation pattern

### Option B: OFAT support only in `investigation / single_system`

Treat OFAT as a specialized sweep mode inside the single-system investigation
workflow.

Advantages:

- best conceptual fit
- bounded scope
- reuses the new sweep output form

Disadvantages:

- needs a dedicated workflow design
- compare and visualization semantics need to be clarified

### Option C: General OFAT support across all Workspace types

Allow OFAT broadly across Workspace workflows.

Advantages:

- maximal flexibility

Disadvantages:

- too much complexity too early
- weakens the clarity of `system_development`
- creates unresolved sweep-vs-sweep and sweep-vs-point semantics


## Draft Recommendation

The recommended direction remains:

- **Option B**

That means:

- support OFAT only for `investigation / single_system` in the first wave
- keep `system_comparison` and `system_development` point-output-focused


## What OFAT Support Should Mean in a Workspace

The first important design rule is:

- a sweep output must be treated as a first-class Workspace result
- not flattened into a sequence of ordinary point results

This implies:

- the Workspace should record a sweep result as one result artifact
- the sweep summary should be first-class
- individual variation runs should still be reachable when needed


## Early Workflow Intuition

If OFAT support is added to `investigation / single_system`, the workflow would
likely look more like:

1. configure a baseline plus one sweep axis
2. execute the OFAT config
3. store the resulting sweep output in `results/`
4. inspect the sweep summary
5. optionally visualize one selected variation run
6. optionally compare sweeps later, but not in the first wave

This is notably different from the current default single-system loop:

1. run baseline
2. change config
3. run again
4. compare old vs new


## Open Design Questions

1. Should OFAT in `single_system` be:
   - an allowed config shape inside the existing workspace type,
   - or a formally declared submode of that workspace type?

2. Should `axis workspaces compare` even be used for sweep results in the first
   version of OFAT support?

3. Should OFAT support introduce sweep-specific commands or summaries, such as:
   - sweep show
   - sweep table
   - sweep result

4. Should Workspace visualization accept a sweep variation selector directly,
   rather than requiring raw run selection?

5. How much of the sweep semantics should be written explicitly into
   `workspace.yaml`, versus derived from the Experiment Output layer?


## Current Recommendation

Before any implementation work:

1. keep the current guardrail that rejects OFAT in Workspace mode
2. design OFAT support first as a dedicated extension of
   `investigation / single_system`
3. treat sweep outputs as first-class Workspace results
4. do not force OFAT into the existing point-vs-point comparison workflow


## Next Step

The next useful step is a more detailed draft that answers:

- what the exact operational workflow for `single_system + ofat` should be
- what commands should do
- what should be stored in the Workspace manifest
- and which commands should remain unavailable for sweep results in v1
