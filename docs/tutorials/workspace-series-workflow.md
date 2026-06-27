# Tutorial: Running a Workspace Series End to End

**AXIS Experimentation Framework v0.2.x**

> **What we do:** Use a `system_comparison` workspace to run one measured
> checkpoint, inspect one run with `run-metrics`, execute a declarative series,
> and finally render series plots.
>
> **Related:** [Experiment Workspaces](../manuals/workspace-manual.md) |
> [Experiment Series](../manuals/experiment-series-manual.md) |
> [Series Measurement Artifacts](../manuals/series-measurement-artifacts-manual.md)

---

## Goal

This tutorial shows how the main workspace-series commands fit together:

1. `measure`
2. `run-metrics`
3. `run-series`
4. `render-series-plots`

The key distinction is:

- `measure` is one automated comparison checkpoint
- `run-series` is many such checkpoints from one declarative plan
- `run-metrics` is a detailed post-hoc inspection command for one selected run
- `render-series-plots` is a post-hoc visualization step for a completed series

---

## Step 1: Start From a System-Comparison Workspace

Assume a workspace like:

```text
workspaces/system_cw_vs_aw/
  workspace.yaml
  configs/
    reference-system_aw.yaml
    candidate-system_cw.yaml
  series/
    system-parameter-variations/
      experiment.yaml
```

Check the workspace first:

```bash
axis workspaces show workspaces/system_cw_vs_aw
axis workspaces check workspaces/system_cw_vs_aw
```

`workspace.yaml` defines the current reference/candidate configs and registers
the available series IDs.

---

## Step 2: Run One Measured Checkpoint

If you want one focused comparison cycle before committing to a full series:

```bash
axis workspaces measure workspaces/system_cw_vs_aw
```

This command:

1. runs the workspace configs
2. compares the resulting reference/candidate runs
3. writes text logs under `measurements/`

Typical outputs:

- `measurements/experiment_N/<label>-comparison.log`
- `measurements/experiment_N/<label>-candidate-run-summary.log`

Use this when:

- you changed one config manually
- you want one checkpoint
- you do not need a full declarative campaign yet

---

## Step 3: Inspect One Run With `run-metrics`

When you want richer behavioral metrics for one persisted run, use:

```bash
axis workspaces run-metrics workspaces/system_cw_vs_aw --role candidate
```

Or pick an exact run:

```bash
axis workspaces run-metrics workspaces/system_cw_vs_aw \
  --experiment <experiment-id> \
  --run run-0000
```

What this command does:

- resolves one run from `results/`
- loads `behavior_metrics.json` if it already exists
- otherwise computes it from the stored trace artifacts
- prints framework-standard and system-specific behavioral metrics

Use `run-metrics` when:

- the run already exists
- the measurement logs are too compact
- you want the detailed metric layer for one specific run

This is why `run-metrics` is separate from `run-series`:

- a series already writes the per-experiment logs and aggregate reports it needs
- `run-metrics` is for targeted inspection, not for driving the campaign

---

## Step 4: Run a Declarative Series

Once your series manifest is ready:

```bash
axis workspaces run-series workspaces/system_cw_vs_aw --series system-parameter-variations
```

This command reads:

- `workspace.yaml`
- `series/system-parameter-variations/experiment.yaml`

and for each enabled experiment:

1. materializes the config delta
2. runs the reference/candidate checkpoint
3. compares the result
4. writes per-experiment logs
5. updates aggregate series artifacts

Main outputs:

- `series/system-parameter-variations/measurements/series-summary.md`
- `series/system-parameter-variations/measurements/series-summary.json`
- `series/system-parameter-variations/measurements/series-metrics.csv`
- per-experiment logs under `series/system-parameter-variations/measurements/experiment_N/`

Use `run-series` when:

- you want a bounded campaign of many related checkpoints
- each experiment is already declared in YAML
- you want one aggregate summary at the end

---

## Step 5: Read the Series Before Plotting

After a completed series, start with:

```bash
less workspaces/system_cw_vs_aw/series/system-parameter-variations/measurements/series-summary.md
```

This is the fastest human-readable entrypoint.

Then use:

- `series-summary.json` when exact values matter
- per-experiment comparison logs when you want episode-level detail
- `run-metrics` when one specific run needs the full metric readout

---

## Step 6: Render Series Plots

When you want visual artifacts after the series already exists:

```bash
axis workspaces render-series-plots workspaces/system_cw_vs_aw --series system-parameter-variations
```

This command:

1. reads the existing series summary and comparison artifacts
2. renders overview plots
3. renders any available system-specific plots
4. writes plot files into the series-local measurements tree

It does **not** rerun experiments.

Typical outputs:

- `series/system-parameter-variations/measurements/plots/plots-report.md`
- `series/system-parameter-variations/measurements/plots/plots-manifest.json`
- series overview plots
- per-experiment comparison plots
- any available system-specific plots

Use this when:

- you finished the series and want visuals
- renderer logic changed
- plot extensions were added later

---

## Recommended Working Pattern

For a comparison workspace with series, a good habit is:

1. `measure` for one exploratory checkpoint while shaping configs
2. `run-metrics` on interesting individual runs
3. `run-series` for the full declared campaign
4. read `series-summary.md`
5. `render-series-plots` for visual analysis
6. use `run-metrics` again on standout runs from the series

This keeps the responsibilities clean:

- execution
- checkpoint measurement
- single-run metric inspection
- campaign execution
- post-hoc plotting

---

## Quick Reference

```bash
# One measured checkpoint
axis workspaces measure workspaces/system_cw_vs_aw

# Detailed metrics for one resolved run
axis workspaces run-metrics workspaces/system_cw_vs_aw --role candidate

# Full declarative campaign
axis workspaces run-series workspaces/system_cw_vs_aw --series system-parameter-variations

# Render plots after the series is complete
axis workspaces render-series-plots workspaces/system_cw_vs_aw --series system-parameter-variations
```

## Summary

The core mental model is:

- `measure` produces one measured checkpoint
- `run-metrics` explains one selected run in detail
- `run-series` executes a declared sequence of checkpoints
- `render-series-plots` visualizes the finished series afterward

If you keep those roles separate, the workspace-series workflow becomes much
easier to navigate.
