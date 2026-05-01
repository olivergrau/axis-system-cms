# Multiple Experiment Series Per Workspace

## Status

Draft idea.

## Question

How should AXIS support multiple declarative experiment series inside one
workspace without turning the workspace into an ambiguous or hard-to-navigate
artifact container?

## Why This Idea Makes Sense

The current model assumes one workspace-local `experiment.yaml`, which works
well for a single focused campaign. In practice, however, one workspace often
needs several related but distinct series, for example:

- one series where only system parameters vary
- one series where only world parameters vary
- one series for replication or robustness checks
- one series for a narrowed follow-up after an earlier broad sweep

These are conceptually related enough to belong to the same workspace, but they
are not the same experiment campaign.

The user's intuition is therefore sound:

- a workspace is the investigation container
- a series is one declared campaign inside that investigation

Right now AXIS collapses those two levels into one file and one aggregate output
location. That makes later series feel "blocked" or structurally awkward.

## Current Limitation

Today the series workflow is effectively singleton-shaped:

- one `experiment.yaml` in the workspace root
- one implicit active series
- one aggregate output set under `measurements/`
  - `series-summary.md`
  - `series-summary.json`
  - `series-metrics.csv`
  - `series-manifest.json`
- one optional `notes.md` regeneration target

This causes a few problems:

- a second series overwrites the conceptual role of the first one
- aggregate outputs do not distinguish campaign identity
- notes scaffolding is global, not series-specific
- measurement folders from different campaigns end up mixed in one namespace
- the workspace has no first-class index of historical series runs

## Core Design Goal

Introduce a first-class distinction between:

- workspace = investigation container
- series = one named experiment campaign inside that workspace

The workflow should allow multiple series to coexist while preserving:

- reproducibility
- readability
- strong artifact locality
- backward compatibility for existing single-series workspaces

## Representative Use Cases

### 1. System-only vs world-only campaigns

One workspace studies `system_aw`.

Series A:

- varies curiosity and arbitration only
- keeps the world fixed

Series B:

- keeps the system fixed
- varies obstacle density, regeneration, or topology

Both campaigns answer the same overarching research question, but they should
not overwrite each other's summaries or notes.

### 2. Broad exploration followed by focused follow-up

Series A:

- broad initial sweep across many hypotheses

Series B:

- small follow-up series built after interpreting A

The follow-up belongs to the same workspace history but should remain clearly
distinguishable.

### 3. Mechanistic vs reporting-oriented campaigns

One series may be for exploratory internal analysis, another for producing
cleaner final comparison artifacts for documentation.

## Design Principle

The cleanest mental model is:

- one workspace can own many series
- each series has its own declaration, measurements, aggregates, and optional
  notes scaffold
- the workspace should expose which series exist and which one is the default
  or currently active one

## Candidate Structures

### Option A: Multiple root-level series files

Example:

```text
workspaces/my-workspace/
  experiment.system.yaml
  experiment.world.yaml
  experiment.followup.yaml
```

Pros:

- simple to implement initially
- minimal migration cost

Cons:

- naming becomes ad hoc
- aggregate outputs still need extra routing
- poor discoverability unless workspace metadata also changes

Assessment:

This is workable as a stopgap but weak as a long-term model.

### Option B: Dedicated `series/` directory

Example:

```text
workspaces/my-workspace/
  series/
    system-variants/
      experiment.yaml
    world-variants/
      experiment.yaml
    followup/
      experiment.yaml
```

Pros:

- clean namespace
- natural place for series-local outputs later
- easy to browse
- avoids root clutter

Cons:

- requires CLI selection semantics
- requires a decision on where outputs live

Assessment:

This is the strongest structural candidate.

### Option C: One root manifest with embedded many-series list

Example:

```yaml
version: 1
workflow_type: experiment_series_collection

series:
  - id: system-variants
    path: series/system-variants/experiment.yaml
  - id: world-variants
    path: series/world-variants/experiment.yaml
```

Pros:

- explicit index
- better validation opportunities
- good future extensibility

Cons:

- more moving parts
- probably unnecessary for the first increment unless paired with Option B

Assessment:

Potentially valuable, but likely a second-step refinement rather than the
minimal first implementation.

## Recommended Draft Direction

Start with a combination of:

- Option B as the storage model
- a small workspace-level index in `workspace.yaml`

Example:

```yaml
experiment_series:
  default_series: system-variants
  entries:
    - id: system-variants
      path: series/system-variants/experiment.yaml
      title: System-only variants
    - id: world-variants
      path: series/world-variants/experiment.yaml
      title: World-only variants
```

This gives AXIS:

- an explicit series namespace
- stable IDs for CLI addressing
- a default series for backwards-friendly invocation
- room for future metadata such as status, tags, or archived state

## Output Layout Proposal

Each series should get its own output root.

Example:

```text
workspaces/my-workspace/
  series/
    system-variants/
      experiment.yaml
      measurements/
        experiment_1/
        experiment_2/
        series-summary.md
        series-summary.json
        series-metrics.csv
        series-manifest.json
      notes.md
    world-variants/
      experiment.yaml
      measurements/
        experiment_1/
        experiment_2/
        series-summary.md
        series-summary.json
        series-metrics.csv
        series-manifest.json
      notes.md
```

This is preferable to a shared workspace-global `measurements/` root because it:

- keeps campaigns isolated
- avoids filename collisions
- makes deletion, archiving, and review safer
- makes the notes scaffold series-specific by design

## CLI Sketch

Possible command shapes:

```bash
axis workspaces run-series <workspace> --series system-variants
axis workspaces run-series <workspace> --series world-variants
axis workspaces list-series <workspace>
axis workspaces show-series <workspace> --series system-variants
```

If `--series` is omitted:

- use `default_series` when configured
- otherwise fail with a clear error if multiple series exist
- preserve current behavior for legacy single-series workspaces

## Backward Compatibility

Existing workspaces should continue to work unchanged.

Compatibility path:

- if `<workspace>/experiment.yaml` exists and no multi-series index exists,
  treat it as the legacy single-series mode
- new multi-series workspaces use `workspace.yaml` series entries plus
  `series/<series-id>/experiment.yaml`

This allows gradual adoption without forced migration.

## Notes Model

Notes should probably become series-local, not workspace-global, for this
workflow.

Recommended rule:

- legacy mode keeps workspace-root `notes.md`
- multi-series mode writes `series/<series-id>/notes.md`

That matches user expectations better because notes usually belong to one
campaign, not to all campaigns mixed together.

## Open Design Questions

### 1. Where should result experiments themselves live?

Two options:

- keep all experiment result directories under workspace-global `results/`
- or create series-local results roots

Draft recommendation:

- keep `results/` workspace-global for now
- store series ownership in metadata or manifest references

Reason:

- lower migration cost
- less disruption to existing repository and comparison tooling

Answer: I favor series-local results roots

### 2. Should measurements be series-local while results stay global?

Probably yes.

That gives:

- stable low-level result storage
- much cleaner high-level campaign reporting

Answer: Right now a workspace can execute ad-hoc experiments like running a single experiment followed bei a compare and a measurment. This should be kept untouched. The series mode is an add-on. If the user decides to do adhoc experiments, then workspace global folders are used: results and measurements and comparisons, but if the user wants to do a series then local folders should be used (for the series).

### 3. How should comparisons work across series?

Likely still allowed, but explicit.

Examples:

- compare within one series by default
- cross-series comparison requires fully specified experiment IDs or a future
  series-aware selector

Anser: An ad-hoc compare (no series context), should only workd on ad-hoc runs. The existing functionality (with the exception of the single series feature) should be still usable. 

The multiple series is a new feature which builds on that.

### 4. Does a workspace need a "current active series" pointer?

Possibly useful, but not required for the first increment.

`default_series` is enough initially.

## Minimal Viable Implementation

Phase 1:

- support `workspace.yaml` series registry
- support `--series <id>` in `run-series`
- support `series/<id>/experiment.yaml`
- route aggregate outputs and notes into the series directory
- keep legacy root-level `experiment.yaml` mode working

Phase 2:

- add `list-series` / `show-series`
- improve validation and status reporting
- add series-aware notes and measurement summaries to workspace inspection

Phase 3:

- optional migration helper from legacy single-series mode
- series-aware compare/report UX improvements

Answer: No need to be fuzzy here. run-series needs a specific pointer to the series config. If this is ommited than an (expressive) error is shown.

## Recommendation

Yes, the idea is worth pursuing.

It addresses a real structural limitation rather than adding complexity for its
own sake. The key is to treat multiple series as named sub-campaigns inside one
workspace, not as multiple root files competing for the same artifact space.

The best draft direction is:

- many series per workspace
- explicit series IDs
- series-local measurement and notes artifacts
- backward-compatible fallback to legacy `experiment.yaml`
