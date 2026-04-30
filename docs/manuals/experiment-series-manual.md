# Experiment Series

Experiment Series add a declarative layer on top of workspace measurements.

Instead of manually repeating:

1. edit config
2. run the workspace
3. compare the result
4. export logs
5. inspect and write notes

you can define a bounded experiment sequence once in `experiment.yaml` and let
AXIS execute it end to end.

## Scope

Current support:

- workspace class: `investigation`
- workspace type: `system_comparison`
- workspace type: `single_system`

If you call the command on any other workspace type, AXIS aborts with an
explicit guardrail error.

## Command

```bash
axis workspaces run-series workspaces/my-workspace
```

Optional notes overwrite:

```bash
axis workspaces run-series workspaces/my-workspace --update-notes
```

Important:

- by default, `notes.md` is left untouched
- `notes.md` is overwritten only when `--update-notes` is specified and
  `defaults.notes.scaffold_notes` is `true`

## Required Files

An experiment series requires:

- a normal `workspace.yaml`
- an additional `experiment.yaml` in the workspace root

The workspace manifest does not need to reference `experiment.yaml`
explicitly.

## Minimal `experiment.yaml`

```yaml
version: 1
workflow_type: experiment_series
workspace_type: system_comparison

experiments:
  - id: exp_01
    title: Weak Symmetric Prediction
    enabled: true
    hypothesis:
      - Prediction should affect behavior slightly
    candidate_config_delta:
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
    candidate_config_delta:
      system:
        prediction:
          curiosity:
            positive_sensitivity: 0.7
            negative_sensitivity: 0.9
```

## `defaults` Block

`experiment.yaml` may include an optional `defaults` block for series-wide
settings:

```yaml
defaults:
  export:
    comparison_summary: true
    candidate_run_summary: true
    reference_run_summary: false
  notes:
    scaffold_notes: true
  labels:
    measurement_label_pattern: "{experiment_id}"
```

### `defaults.labels.measurement_label_pattern`

Controls the fallback measurement label for experiments that do not declare
their own `label`.

Current behavior:

- the pattern must include `{experiment_id}`
- AXIS substitutes `{experiment_id}` with the experiment's `id`
- this fallback is used only when the experiment entry omits `label`
- if `label` is present on the experiment, that explicit label wins

Example:

```yaml
defaults:
  labels:
    measurement_label_pattern: "series-{experiment_id}"
```

With `id: exp_03`, the generated measurement label becomes
`series-exp_03`.

### `defaults.notes.scaffold_notes`

Controls whether `axis workspaces run-series --update-notes` is allowed to
regenerate `notes.md`.

Current behavior:

- `scaffold_notes: true` does not update notes by itself
- `--update-notes` is still required on the CLI
- if `--update-notes` is omitted, AXIS leaves `notes.md` untouched
- if `--update-notes` is provided and `scaffold_notes: true`, AXIS overwrites
  `notes.md` with a fresh scaffold
- if `--update-notes` is provided and `scaffold_notes: false`, AXIS does not
  regenerate `notes.md`

In other words:

- `--update-notes` is the active user request
- `scaffold_notes` is the manifest-side permission switch

The generated scaffold includes:

- one section per executed experiment
- the mapped measurement folder
- copied hypotheses
- placeholders for observations, interpretation, and conclusion

### `defaults.export.*`

The schema currently exposes three export toggles:

- `comparison_summary`
- `candidate_run_summary`
- `reference_run_summary`

Current implementation status:

- these fields are parsed from `experiment.yaml`
- they are not currently used to change `run-series` output behavior

At present, `run-series` still exports the standard per-experiment text
artifacts produced by the measurement workflow:

- a comparison summary log
- one run-summary log

For `system_comparison`, that run-summary log is for the candidate side.

For `single_system`, that run-summary log is for the `system_under_test` run.

## Resolution Model

Each experiment is resolved from the workspace’s baseline configs.

For `system_comparison` this means:

- the reference config stays the manifest-declared reference config
- the candidate config starts from the manifest-declared candidate config
- `candidate_config_delta` is deep-merged onto that candidate baseline

For `single_system`:

- the system-under-test config is the baseline
- each experiment delta is applied to that same fixed baseline config
- AXIS does not inherit config state from the previous experiment

AXIS does not inherit experiment configs from the previous experiment.

AXIS also does not mutate the original workspace config files. It materializes
temporary configs internally for series execution.

## Execution Model

For every enabled experiment, AXIS:

1. resolves a temporary candidate config from the delta
2. runs the workspace
3. runs the workspace comparison
4. exports the comparison summary log
5. exports the candidate run summary log

The implementation reuses the existing `axis workspaces measure` semantics
internally for `system_comparison`.

For `single_system`, AXIS runs one point experiment per series entry and then
compares:

- baseline experiment vs baseline experiment for the first entry
- baseline experiment vs current experiment for all later entries

## Example: `single_system` With System A+W

The following pattern works well for a mechanistic A+W study where you want one
stable anchor run plus a few focused behavioral perturbations:

```yaml
version: 1
workflow_type: experiment_series
workspace_type: single_system
title: System A+W Curiosity and Arbitration Series
base_configs:
  system_under_test: configs/system_aw-baseline.yaml

experiments:
  - id: exp_00
    label: aw-baseline
    title: Baseline Anchor
    enabled: true
    candidate_config_delta:
      system:
        curiosity:
          novelty_sharpness: 2.0

  - id: exp_01
    label: aw-slower-novelty-decay
    title: Slower Novelty Decay
    enabled: true
    candidate_config_delta:
      system:
        curiosity:
          novelty_sharpness: 1.0

  - id: exp_02
    label: aw-softer-arbitration
    title: Softer Hunger-Curiosity Handoff
    enabled: true
    candidate_config_delta:
      system:
        arbitration:
          curiosity_weight_base: 2.0
          gating_sharpness: 2.0

  - id: exp_03
    label: aw-strong-exploration-bias
    title: Stronger Exploration Bias
    enabled: true
    candidate_config_delta:
      system:
        curiosity:
          spatial_sensory_balance: 0.9
          explore_suppression: 0.8
```

This series answers a focused question:

- how does A+W change when novelty persists longer
- how does behavior change when curiosity survives deeper into hunger regimes
- how much overt exploration pressure can the system tolerate before local
  harvesting degrades

Even in `single_system`, the field name remains `candidate_config_delta`.
Conceptually, it means: "the config delta for the current series experiment,"
applied to the workspace's fixed base config.

## Failure Behavior

Series execution is fail-fast.

If one experiment fails, the whole series fails and later experiments are not
executed.

There is no resume support in the current version.

## Outputs

Per experiment, AXIS still creates the normal measurement folder and text logs.

Additionally, the series command writes aggregate artifacts:

- `measurements/series-summary.md`
- `measurements/series-summary.json`
- `measurements/series-metrics.csv`
- `measurements/series-manifest.json`

The exact root directory follows the workspace’s `measurement_workflow.root_dir`
setting.

## Final Overview

The generated series summary includes three comparison lenses:

- previous experiment: local progression
- baseline experiment: campaign anchor
- workspace reference system: scientific comparison view for `system_comparison`
- baseline comparison view for `single_system`

The report stays at pure reporting level:

- metric changes are summarized
- no automatic scientific interpretation is generated

## Notes Scaffolding

If you pass `--update-notes`, AXIS regenerates `notes.md` as a scaffold only
when `defaults.notes.scaffold_notes` is `true`.

The scaffold includes:

- one section per experiment
- the mapped measurement folder
- copied hypotheses
- placeholders for observations, interpretation, and conclusion

Without `--update-notes`, AXIS leaves the existing `notes.md` untouched,
regardless of the `scaffold_notes` setting.

## Relationship To `measure`

Use `measure` when you want one automated run/compare/export cycle.

Use `run-series` when you want many such cycles executed from one declarative
experiment plan.

In short:

- `measure` = one measured checkpoint
- `run-series` = a declared sequence of measured checkpoints

## See Also

- [Experiment Workspaces](workspace-manual.md)
- [CLI User Guide](cli-manual.md)
