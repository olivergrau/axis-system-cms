# Declarative Experiment Workflow Draft

## Purpose

This draft explores a next step beyond the current `axis workspaces measure`
workflow.

The motivating user workflow is already stable:

1. define a config
2. run the workspace
3. compare outputs
4. export summary logs
5. inspect and interpret the results
6. repeat for the next experiment

The opportunity is to turn that repeated loop into a first-class,
declarative AXIS workflow:

> define an experiment series once, then let AXIS execute, collect, and
> summarize the full sequence.


## Starting Point

AXIS already has most of the required building blocks:

- typed workspace manifests
- workspace-type-specific execution handlers
- `axis workspaces run`
- `axis workspaces compare`
- `axis workspaces measure`
- persisted run results and persisted comparisons
- workspace-local notes and measurement folders

So the problem is not missing execution primitives.

The problem is that the experimental series itself is still implicit and
manual.

Today the user carries critical structure outside the framework:

- the intended experiment sequence
- the mapping from experiment folder to conceptual hypothesis
- the rationale for each config change
- the stopping condition for the series
- the cross-experiment interpretation


## Core Idea

Introduce a declarative experiment-series file, tentatively:

- `experiment.yaml`, or
- `e-workflow.yaml`

This file would define a bounded sequence of experiments for one workspace.

For a `system_comparison` workspace, that sequence would likely declare:

- experiment identity and ordering
- per-experiment labels
- config changes or full config bindings
- optional notes / hypothesis text
- execution policy
- summary/export policy
- final aggregation policy

The new command would then execute the sequence end to end, for example:

```bash
axis workspaces run-series .
```

or

```bash
axis workspaces execute-workflow .
```

The exact command name is still open.


## Why This Is Different From `measure`

`measure` optimizes one experiment cycle.

This draft targets the next layer up:

- `measure` = one measured checkpoint
- declarative experiment workflow = many measured checkpoints with explicit
  series structure

That distinction matters.

We probably do **not** want to overload `measurement_workflow` in
`workspace.yaml` until we decide whether:

- the experiment series is a reusable workspace policy
- or a concrete, finite investigation plan

My current instinct is:

- keep `measurement_workflow` for per-run output conventions
- add a separate experiment-series file for multi-run scientific intent


## Recommended First Scope

The cleanest first target is:

- workspace type: `system_comparison`
- workspace class: `investigation`

Reason:

- it matches the already proven user workflow
- the loop naturally includes both run and compare
- the final output can include both candidate-side summaries and comparison
  summaries
- the semantics are easier to define than for more open-ended development
  workspaces

However, the design should not accidentally block later support for:

- `single_system`

That means the model should separate:

- workflow concepts that are generic
- workflow steps that are comparison-specific


## Candidate Conceptual Model

### Layer 1: Workspace-Level Policy

This stays in `workspace.yaml`.

Examples:

- where measurements live
- naming conventions
- default export formats
- whether notes generation scaffolding is enabled
- default summary role for `system_comparison`

This is stable workspace policy.

### Layer 2: Experiment-Series Definition

This lives in a dedicated file such as `experiment.yaml`.

Examples:

- the ordered list of experiments
- experiment IDs and labels
- experiment hypotheses
- per-experiment config deltas
- per-experiment notes
- whether an experiment is enabled, skipped, or draft

This is the actual research plan.

### Layer 3: Realized Artifacts

These remain persisted outputs:

- `results/`
- `comparisons/`
- `measurements/experiment_n/...`
- notes / summaries / aggregate tables

This separation keeps intent, policy, and outputs distinct.


## Draft Example

Illustrative only:

```yaml
version: 1
workflow_type: experiment_series
workspace_type: system_comparison

defaults:
  measure_label_pattern: "{experiment_id}"
  export:
    comparison_summary: true
    candidate_run_summary: true
    reference_run_summary: false

experiments:
  - id: exp_01
    title: Weak Symmetric Prediction
    enabled: true
    notes: Small symmetric predictive influence
    hypothesis:
      - Prediction should affect behavior slightly
      - Curiosity should be more sensitive than hunger
    candidate_config_changes:
      system:
        prediction:
          hunger:
            positive_sensitivity: 0.4
            negative_sensitivity: 0.6
          curiosity:
            positive_sensitivity: 0.4
            negative_sensitivity: 0.6

  - id: exp_02
    title: Curiosity-Dominant Prediction
    enabled: true
    depends_on: exp_01
    candidate_config_changes:
      system:
        prediction:
          curiosity:
            positive_sensitivity: 0.7
            negative_sensitivity: 0.9
```

The exact patch format is open.

Possible options:

- full config paths per experiment
- deep merge patches against primary configs
- reusable named parameter sets


## Potential Outputs

The workflow should likely produce more than raw runs.

For `system_comparison`, useful outputs could include:

- one measurement folder per experiment
- exported run summaries and comparison summaries
- one aggregate table over all experiments
- one machine-readable experiment index
- one human-readable cross-experiment report scaffold

Possible aggregate artifacts:

- `measurements/series-summary.md`
- `measurements/series-metrics.csv`
- `measurements/series-comparison-table.md`
- `measurements/series-manifest.json`


## Main Benefits

### 1. Reproducibility

The experimental sequence becomes explicit and replayable.

### 2. Less Manual Drift

Today the user manually maintains consistency between:

- config edits
- folder names
- notes
- interpretation

A declarative series reduces naming drift and mapping errors.

### 3. Better Research Structure

The framework can understand:

- what the experiment series was supposed to test
- which run belonged to which hypothesis
- what the order of escalation was

### 4. Stronger Summarization

Once AXIS knows the full series, it can generate:

- cross-experiment metric tables
- deltas against baseline
- ranked experiment summaries
- anomaly lists


## Important Risks

### 1. Overlap With Existing Concepts

AXIS already has related concepts:

- experiment workspaces
- `measure`
- OFAT / sweep-style support
- persisted outputs and comparisons

We need to avoid introducing a second, slightly different sweep model with
unclear boundaries.

### 2. Config Mutation Semantics

A declarative series only works well if config mutation is predictable.

Open question:

- does each experiment start from the workspace primary config
- or from the previous experiment’s config

Those two semantics produce very different behavior and failure modes.

My current recommendation:

- every experiment should resolve from a declared base config plus explicit
  patch
- never from implicit previous mutable state

### 3. Partial Failure and Resume

Longer series raise operational questions:

- what happens if experiment 4 fails
- can experiment 5 still run
- can the workflow resume from experiment 4
- how are partially completed series represented

### 4. Notes and Interpretation Boundaries

The current workflow ends with human interpretation.

AXIS can help scaffold that step, but should not pretend to replace it.

So the product boundary matters:

- export tables automatically
- maybe pre-fill note sections
- but do not over-automate scientific claims without clear user intent


## Cross-Workspace-Type Fit

### `system_comparison`

This is the strongest first fit.

Each experiment naturally includes:

- reference run
- candidate run
- comparison
- candidate-side and comparison-side summaries

This makes the aggregate table straightforward.

### `single_system`

This should be supported by the conceptual model, but with a reduced step set.

Each experiment would include:

- one run
- one run summary
- maybe optional comparison against a declared baseline result or previous run

Key implication:

The workflow model should define steps abstractly, for example:

- `run`
- `compare`
- `export_summary`
- `aggregate`

Then workspace handlers can activate only the steps that make sense.

### Other Workspace Types

This draft should not assume immediate support for:

- `system_development`
- `world_development`

Those may need a looser, milestone-oriented workflow rather than a strict
experiment series.


## Likely Architectural Direction

The cleanest shape may be:

- a new typed experiment-series model
- a loader/validator for `experiment.yaml`
- a new orchestration service, something like
  `WorkspaceExperimentSeriesService`
- workspace-type-aware execution hooks
- one aggregate rendering layer for series summaries

This should likely reuse existing services rather than duplicate them:

- `run`
- `compare`
- `measure`
- summary rendering

That keeps one source of truth for execution semantics.


## Open Design Tensions

These tensions should be resolved before a spec:

1. Is this primarily a workflow runner or a scientific investigation model?

Answer: Hmm, I would say: both! I want to conduct science here with a workflow ;-)

2. Should experiment hypotheses live in the series file or only in notes?

Answer: They should live in the series file. This makes it more readable and interpretable. Notes.md is not touched by the AXIS Framework and is only edited manually by the user.

3. Should config changes be stored inline, by file reference, or both?

Answer: Inline, via deltas compared to the baseline config (reference). Configs must be reconstructable in full, but this should be given if we store the deltas.

4. Should AXIS mutate the workspace’s active primary config during the series?

Answer: Good Question! I would say it leaves the original confis untouched (they are for manual mode) and creates temp configs regarding the experiment series manifest.

5. Should the final overview be Markdown-first, table-first, or JSON-first?

Answer: JSON should be supported too. And Markdown-first.

6. How much automatic interpretation is desirable before it becomes misleading?

Answer: Pure Reporting. Interpretation is the responsibility of the user. 

## Steering Questions For The First Draft

These are the main questions I would use to steer the first real draft.

### Product Scope

1. Should the first version target only `system_comparison`, with
   `single_system` intentionally deferred but kept compatible at schema level?

   Answer: Yes, target only the system_comparision type. If called with a different type, then error with a explainable message (guardrail).

2. Is the main value execution automation, artifact organization, or
   cross-experiment interpretation?

   Answer: Artifact organization. No cross experiments accross workspaces.

3. Should this feature be framed as:
   - experiment series
   - workflow
   - sweep
   - campaign

   Answer: experiment series. We can later think about to integrate even OFAT, but for now we can assume they are normal single runs (guardrail!).

### File and Schema Design

4. Should the series definition live in `workspace.yaml` or in a separate
   `experiment.yaml` file?

   Answer: separate experiment.yaml

5. If separate, should the workspace manifest explicitly point to it?

  Answer: Not necessarily. The experiment series is an additional feature in the workspace realm.

6. Should experiments reference:
   - full config files
   - config patches
   - or both

   Answer: deltas. All deltas relates to the reference config. Created configs while the series is executed are temporary.

7. Do we want immutable experiment IDs separate from user-facing labels?

Answer: Yes, we need uniquitiy here.

### Execution Semantics

8. Does each experiment resolve from a fixed base config, or can experiments
   inherit from the previous experiment?

   Answer: No inherits please. Always related to a reference. The reference config is defined in the workspace.yaml. You can assume, that a valid experiment.yaml always requires a workspace.yaml. But not vice versa.

9. Should the command execute all enabled experiments by default, or require an
   explicit subset / range?

   Answer: Let us introduce a switch for that in the experiment.yaml. Then the user can deactive experiments in a series.

10. What is the correct resume model after a partial failure?

  Answer: No resume necessary. If it fails, then the user must start over.

11. Should a failed comparison block the rest of the series?

  Answer: Yes, if something fails, the series fails. 

### Workspace-Type Semantics

12. For `single_system`, what is the equivalent of the comparison step?
  
  Answer: the first recorded point experiment becomes the reference, the most recent point experiment becomes the candidate. Sweep outputs are excluded from auto-resolution — workspace comparison is always point-vs-point.

13. Should `single_system` aggregate only run summaries, or support optional
   baseline comparisons as well?

   Answer: Always compare to the baseline, not to the previous run only. This is similar to the system_comparision. But in single_system we have only one system which we work with.

14. Are there workspace types that should explicitly reject this feature in v1?

    Answer: Yes, other than system_comparision and single_system

### Notes and Interpretation

15. Should AXIS generate a notes scaffold per experiment automatically?

Answer: Wonderful idea! Yes please!

16. Should experiment hypotheses be copied into the notes scaffold?

Answer: Again, a wonderful idea! Yes please!

17. Should AXIS generate a final cross-experiment Markdown report, or only raw
   tables plus a scaffold?

   Answer: Final cross-experiment markdown sounds good!

18. How should user-written interpretation be protected from regeneration or
   overwrite?

   Answer: We make this simple. The user should edit notes.md after the experiment series did run. No protection. But you can implement a guard-rail which asks the user after the experiment series if the notes.md should be updated. If the user chose yes, then overwrite it, otherwise leave the notes.md intakt.

### Output and Review

19. What are the minimum aggregate outputs required to call the workflow
   successful?
   Answer:All system specific metrics and the generic ones should be successfully calculated. If an error occurs, then the series fails.

20. Which table views are most valuable:
   - per-experiment metric table
   - best/worst ranking
   - delta-to-baseline table
   - anomaly summary

   Answer: per-experiment metric table (accross all experiments), so that the user can compare all configs "at a glance".

21. Should the final overview compare against:
   - previous experiment
   - baseline experiment
   - workspace reference system
   - all of the above

   Answer: for system_comparison: probably all of the above
      but with different roles:
      previous experiment = progression view
      baseline experiment = campaign anchor view
      workspace reference system = actual scientific comparison view


## Recommended First Draft Position

My current recommendation for the first formal draft would be:

- start with `system_comparison`
- use a separate `experiment.yaml`
- resolve every experiment from a declared base config plus explicit patch
- reuse `measure` internally instead of bypassing it
- generate aggregate tables automatically
- generate only scaffolds for notes, not automatic conclusions

That would keep the first version:

- operationally useful
- conceptually clean
- compatible with `single_system` later
- and aligned with how AXIS already structures workspace execution
