# AXIS Framework Test Playbook

## Purpose

This playbook describes a practical end-to-end test sweep for the AXIS framework.
It is intended for manual framework validation, release checks, and regression
testing after CLI, workspace, comparison, persistence, or visualization changes.

The playbook is organized around real user workflows instead of isolated command
snippets.

Coverage areas:

- Base commands without workspaces
- Workspace commands without series
- Workspace commands with series
- Visualizer workflows

## General Rules

- Run all commands from the repository root unless the step explicitly says otherwise.
- Prefer `--output json` for spot checks where machine-readable structure matters.
- Prefer normal text output for ergonomic workflow checks.
- If a step modifies persistent artifacts, either reset the target workspace afterwards
  or use a disposable copy.
- When validating a workflow, check both:
  - command exit behavior
  - generated artifacts on disk

## Recommended Test Modes

- Smoke pass:
  - run one representative workflow from each section
  - use when iterating quickly
- Full pass:
  - run every section in order
  - use before merging larger framework changes

## Known Test Assets In This Repo

Base configs:

- `experiments/configs/system-a-baseline.yaml`
- `experiments/configs/system-a-energy-gain-sweep.yaml`
- `experiments/configs/system-aw-baseline.yaml`
- `experiments/configs/system-c-baseline.yaml`

Workspace targets without series:

- `workspaces/system_a-baseline`
- `workspaces/system_a_vs_system_c`
- `workspaces/system-d-development`
- `workspaces/system-c-sweep`

Workspace targets with series:

- `workspaces/system_aw-baseline`
- `workspaces/system_cw_vs_aw`

## 1. Base Commands

### 1.1 Single-run experiment lifecycle

Goal:
Verify the standard experiment repository flow without workspaces.

Steps:

```bash
axis experiments run experiments/configs/system-a-baseline.yaml
axis experiments list
```

Expected:

- `experiments run` completes successfully
- a new experiment ID appears in `experiments/results/`
- `experiments list` shows one more completed experiment

Follow-up:

```bash
axis experiments show <experiment-id>
axis runs list --experiment <experiment-id>
axis runs show run-0000 --experiment <experiment-id>
axis runs metrics run-0000 --experiment <experiment-id>
```

Expected:

- `experiments show` includes config, summary, and run inventory
- `runs list` shows `run-0000`
- `runs show` renders behavioral summary
- `runs metrics` renders structured metrics

Artifacts to verify:

- `experiments/results/<experiment-id>/experiment_config.json`
- `experiments/results/<experiment-id>/experiment_summary.json`
- `experiments/results/<experiment-id>/runs/run-0000/run_summary.json`
- `experiments/results/<experiment-id>/runs/run-0000/behavior_metrics.json`

### 1.2 OFAT / sweep flow

Goal:
Verify multi-run experiment execution and sweep inspection.

Steps:

```bash
axis experiments run experiments/configs/system-a-energy-gain-sweep.yaml
axis experiments list
axis experiments show <sweep-experiment-id>
```

Expected:

- one new experiment is created
- the experiment contains multiple runs
- `experiments show` reflects sweep structure rather than a single point run

Optional deeper inspection:

```bash
axis runs list --experiment <sweep-experiment-id>
axis runs show run-0000 --experiment <sweep-experiment-id>
```

### 1.3 Direct comparison flow

Goal:
Verify repository-level paired trace comparison without workspace mediation.

Precondition:

- at least two comparable experiment outputs exist

Steps:

```bash
axis compare \
  --reference-experiment <ref-exp> --reference-run run-0000 \
  --candidate-experiment <cand-exp> --candidate-run run-0000
```

Expected:

- comparison completes without validation failure
- output contains episode counts, valid pair counts, and comparison metrics

Optional single-episode comparison:

```bash
axis compare \
  --reference-experiment <ref-exp> --reference-run run-0000 --reference-episode 1 \
  --candidate-experiment <cand-exp> --candidate-run run-0000 --candidate-episode 1
```

### 1.4 JSON output spot-check

Goal:
Verify CLI JSON mode remains structurally clean.

Steps:

```bash
axis --output json experiments show <experiment-id>
axis --output json runs show run-0000 --experiment <experiment-id>
```

Expected:

- output is valid JSON with no banner noise mixed in

## 2. Workspace Commands Without Series

### 2.1 Workspace validation and inspection

Goal:
Verify baseline workspace inspection behavior.

Steps:

```bash
axis workspaces check workspaces/system_a-baseline
axis workspaces show workspaces/system_a-baseline
axis --output json workspaces show workspaces/system_a-baseline
```

Expected:

- validation succeeds or reports only intentional infos/warnings
- text `show` renders workspace identity and artifact sections
- JSON `show` contains structured summary data

### 2.2 Single-system iterative run workflow

Target:
`workspaces/system_a-baseline`

Goal:
Verify the normal single-system workflow: run, rerun with change, compare, inspect.

Steps:

```bash
axis workspaces reset workspaces/system_a-baseline --force
axis workspaces run workspaces/system_a-baseline
axis workspaces show workspaces/system_a-baseline
axis workspaces run-summary workspaces/system_a-baseline
```

Expected:

- workspace `results/` is populated
- `primary_results` entries are written to `workspace.yaml`
- `run-summary` resolves the latest run automatically

Then create a real config change in the workspace config and rerun:

```bash
axis workspaces run workspaces/system_a-baseline
axis workspaces compare workspaces/system_a-baseline
axis workspaces comparison-summary workspaces/system_a-baseline
```

Expected:

- second run is accepted because config changed
- comparison file appears in `comparisons/`
- comparison summary shows compared experiment IDs and metrics

Artifacts to verify:

- `workspaces/system_a-baseline/results/...`
- `workspaces/system_a-baseline/comparisons/comparison-001.json`

### 2.3 Duplicate-run guard workflow

Target:
`workspaces/system_a-baseline`

Goal:
Verify that unchanged reruns are blocked, but intentional override still works.

Steps:

```bash
axis workspaces run workspaces/system_a-baseline
```

Expected:

- if nothing changed since the previous comparable run, AXIS aborts with a
  duplicate-run style error

Then:

```bash
axis workspaces run workspaces/system_a-baseline --override-guard
```

Expected:

- run executes despite unchanged config

### 2.4 System-comparison workspace workflow

Target:
`workspaces/system_a_vs_system_c`

Goal:
Verify paired workspace comparison workflow across two systems.

Steps:

```bash
axis workspaces reset workspaces/system_a_vs_system_c --force
axis workspaces check workspaces/system_a_vs_system_c
axis workspaces compare-configs workspaces/system_a_vs_system_c
axis workspaces run workspaces/system_a_vs_system_c
axis workspaces compare workspaces/system_a_vs_system_c
axis workspaces comparison-summary workspaces/system_a_vs_system_c
```

Expected:

- both reference and candidate runs are executed
- workspace comparison creates `comparisons/comparison-001.json`
- comparison summary renders the stored comparison

### 2.5 Measurement workflow

Target:
`workspaces/system_a_vs_system_c`

Goal:
Verify automated run + compare + log export.

Steps:

```bash
axis workspaces measure workspaces/system_a_vs_system_c --label manual-check
```

Expected:

- a new `measurements/experiment_<n>/` directory is created
- comparison log is exported
- run summary log is exported

Artifacts to verify:

- `measurements/experiment_<n>/manual-check-comparison.log`
- `measurements/experiment_<n>/manual-check-candidate-run-summary.log`

### 2.6 OFAT workspace workflow

Target:
`workspaces/system-c-sweep`

Goal:
Verify that `single_system` workspaces accept OFAT configs and surface sweep outputs.

Steps:

```bash
axis workspaces reset workspaces/system-c-sweep --force
axis workspaces run workspaces/system-c-sweep
axis workspaces show workspaces/system-c-sweep
axis workspaces sweep-result workspaces/system-c-sweep
```

Expected:

- workspace run succeeds
- sweep artifacts are present
- `sweep-result` resolves the latest sweep without ambiguity

### 2.7 Development workspace workflow

Target:
`workspaces/system-d-development`

Goal:
Verify development-mode commands and state transitions.

Suggested flow:

```bash
axis workspaces check workspaces/system-d-development
axis workspaces show workspaces/system-d-development
axis workspaces set-candidate workspaces/system-d-development <workspace-relative-config>
axis workspaces run workspaces/system-d-development --baseline-only
axis workspaces run workspaces/system-d-development --candidate-only
axis workspaces compare workspaces/system-d-development
axis workspaces comparison-summary workspaces/system-d-development
```

Expected:

- candidate assignment updates the manifest
- baseline and candidate runs are tracked separately
- comparison resolves current validation targets

### 2.8 Reset and close workflow

Goal:
Verify mutation commands that change workspace state.

Steps:

```bash
axis workspaces reset workspaces/system_a-baseline
```

Expected:

- preview lists roots and counts
- command asks for confirmation

Then:

```bash
axis workspaces reset workspaces/system_a-baseline --force
axis workspaces close workspaces/system_a-baseline
axis workspaces show workspaces/system_a-baseline
```

Expected:

- generated artifacts are deleted
- manifest tracking fields are cleared
- closed workspace is still inspectable
- further mutating commands should be rejected

## 3. Workspace Commands With Series

### 3.1 Series registry and inspection

Target:
`workspaces/system_aw-baseline`

Goal:
Verify the workspace recognizes registered series and surfaces them in `show`.

Steps:

```bash
axis workspaces check workspaces/system_aw-baseline
axis workspaces show workspaces/system_aw-baseline
axis --output json workspaces show workspaces/system_aw-baseline
```

Expected:

- `experiment_series` entries are valid
- `show` renders the registered series section
- JSON output includes series entries and generated artifacts when present

### 3.2 Single-system series workflow

Target:
`workspaces/system_aw-baseline`

Series:
- `curiosity-arbitration`
- `world-variations`

Goal:
Verify series-local execution, results, comparisons, measurements, and notes handling.

Steps:

```bash
axis workspaces reset workspaces/system_aw-baseline --force
axis workspaces run-series workspaces/system_aw-baseline --series curiosity-arbitration
axis workspaces show workspaces/system_aw-baseline
```

Expected:

- results are written under `series/curiosity-arbitration/results/`
- comparisons are written under `series/curiosity-arbitration/comparisons/`
- measurement logs and aggregate outputs appear under `series/curiosity-arbitration/measurements/`
- `workspace.yaml` tracks generated artifacts under the owning series entry

Artifacts to verify:

- `series/curiosity-arbitration/measurements/series-summary.md`
- `series/curiosity-arbitration/measurements/series-summary.json`
- `series/curiosity-arbitration/measurements/series-metrics.csv`
- `series/curiosity-arbitration/measurements/series-manifest.json`

Then test notes scaffold refresh:

```bash
axis workspaces run-series workspaces/system_aw-baseline --series curiosity-arbitration --update-notes
```

Expected:

- `series/curiosity-arbitration/notes.md` is regenerated

Repeat the same workflow for the world-study series:

```bash
axis workspaces run-series workspaces/system_aw-baseline --series world-variations
```

Expected:

- world-only series comparisons succeed without any extra flag
- `series/world-variations/measurements/` receives per-experiment logs and aggregate outputs

### 3.3 System-comparison series workflow

Target:
`workspaces/system_cw_vs_aw`

Series:
- `predictive-modulation`

Goal:
Verify multi-experiment comparison campaigns in a comparison workspace.

Steps:

```bash
axis workspaces reset workspaces/system_cw_vs_aw --force
axis workspaces run-series workspaces/system_cw_vs_aw --series predictive-modulation
axis workspaces show workspaces/system_cw_vs_aw
```

Expected:

- each enabled experiment produces series-local results and comparisons
- measurement logs are exported per experiment
- aggregate series outputs are written at the series-local root

### 3.4 Series reset workflow

Goal:
Verify that workspace reset is series-aware.

Steps:

```bash
axis workspaces reset workspaces/system_aw-baseline
```

Expected preview:

- workspace-global roots listed
- series-local roots listed for each registered series
- manifest fields to clear listed
- counts for affected roots shown

Then:

```bash
axis workspaces reset workspaces/system_aw-baseline --force
axis workspaces show workspaces/system_aw-baseline
```

Expected:

- series-local generated directories are emptied
- `generated` tracking blocks disappear from `experiment_series.entries[*]`

## 4. Visualizer

### 4.1 Base repository visualizer

Goal:
Verify the direct replay viewer flow from experiment outputs.

Precondition:

- a completed experiment exists with `trace_mode: full` or `trace_mode: delta`

Steps:

```bash
axis visualize --experiment <experiment-id> --run run-0000 --episode 1
```

Expected:

- viewer launches
- grid renders
- replay controls respond
- step analysis and detail panels populate

Manual checks:

- move between steps
- switch phases
- select cells and agent
- confirm vitality and world status update

### 4.2 Visualizer with initial positioning options

Steps:

```bash
axis visualize --experiment <experiment-id> --run run-0000 --episode 1 --step 20 --phase 1
axis visualize --experiment <experiment-id> --run run-0000 --episode 1 --width-percent 80
```

Expected:

- viewer opens at the requested step/phase
- width override is respected

### 4.3 Workspace-driven visualizer

Goal:
Verify workspace resolution into experiment/run targets.

Target examples:

- `workspaces/system_a-baseline`
- `workspaces/system_a_vs_system_c`

Steps:

```bash
axis visualize --workspace workspaces/system_a-baseline --episode 1
```

Expected:

- viewer resolves the latest suitable workspace run automatically

Comparison workspace variants:

```bash
axis visualize --workspace workspaces/system_a_vs_system_c --role reference --episode 1
axis visualize --workspace workspaces/system_a_vs_system_c --role candidate --episode 1
```

Expected:

- role-based target resolution works

Explicit target resolution:

```bash
axis visualize --workspace workspaces/system_a-baseline --experiment <experiment-id> --run run-0000 --episode 1
```

### 4.4 Negative visualizer checks

Goal:
Verify failure behavior is clear and safe.

Suggested checks:

- try to visualize a `light` trace run
- try to visualize a missing experiment ID
- try to visualize a missing episode index

Expected:

- AXIS rejects the request with a clear error
- no partial viewer launch occurs

## 5. Release Checklist

Use this condensed pass before tagging or merging larger framework work:

1. Run one direct single-run experiment and inspect it.
2. Run one direct sweep experiment and inspect it.
3. Run one direct comparison.
4. Run `check`, `show`, `run`, `compare`, `comparison-summary`, and `reset` on one non-series workspace.
5. Run `measure` on one `system_comparison` workspace.
6. Run `run-series` on one `single_system` series workspace.
7. Run `run-series` on one `system_comparison` series workspace.
8. Open the visualizer once from direct experiment IDs and once from a workspace target.

## 6. Failure Notes

Common failure categories to watch for:

- parser regressions:
  commands parse differently or flags disappear unexpectedly
- manifest regressions:
  `workspace.yaml` tracking does not match disk artifacts
- comparison regressions:
  comparisons run but summaries contain zero valid pairs unexpectedly
- series regressions:
  generated artifacts land in the wrong root or wrong registry branch
- viewer regressions:
  delta traces fail to reconstruct or the viewer opens with missing panels

When a failure appears, capture:

- exact command
- stderr/stdout
- affected workspace or experiment ID
- changed files under `results/`, `comparisons/`, `measurements/`, or `series/`
- relevant `workspace.yaml` excerpt if a workspace is involved
