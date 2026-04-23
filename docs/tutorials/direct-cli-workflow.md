# Tutorial: Using AXIS Without Workspaces

**AXIS Experimentation Framework v0.2.3**

> **Prerequisites:** AXIS framework installed (`pip install -e .`),
> familiarity with the CLI basics, and at least one runnable experiment
> config such as `experiments/configs/system-a-baseline.yaml`.
>
> **What we do:** Use AXIS in its original direct CLI mode, without any
> workspace manifest or workspace-local artifact management. We will run
> experiments from config files, inspect experiments and runs, compare
> persisted traces, and launch replay visualization.
>
> **Related:** [CLI Manual](../manuals/cli-manual.md) |
> [Comparison Manual](../manuals/comparison-manual.md) |
> [Visualization Manual](../manuals/visualization-manual.md) |
> [Experiment Workspaces](../manuals/workspace-manual.md)

---

## What is Direct CLI Mode?

Before workspace support existed, AXIS already had a complete
command-line workflow for working directly with configs and persisted
experiment artifacts.

That workflow is still supported and is often the simplest option when
you want to:

- run a config directly
- inspect raw experiment and run artifacts
- manage your own result roots
- avoid workspace manifests and workspace-specific commands

In direct mode, AXIS writes results to an **experiment repository root**.
By default, that root is:

```text
./experiments/results
```

Every non-workspace command works against that repository root unless
you override it with `--root`.

The direct CLI surface is:

- `axis experiments list`
- `axis experiments run <config>`
- `axis experiments show <experiment-id>`
- `axis experiments resume <experiment-id>`
- `axis runs list --experiment <experiment-id>`
- `axis runs show <run-id> --experiment <experiment-id>`
- `axis compare ...`
- `axis visualize ...`

---

## Step 1: Run a Config Directly

Start with one of the shipped example configs:

```bash
axis experiments run experiments/configs/system-a-baseline.yaml
```

AXIS validates the config, executes the experiment, and writes a new
experiment directory under `experiments/results/`.

The result layout looks like this:

```text
experiments/results/
  <experiment-id>/
    experiment_config.json
    experiment_metadata.json
    experiment_status.json
    experiment_summary.json
    runs/
      run-0000/
        run_config.json
        run_metadata.json
        run_status.json
        run_summary.json
        run_result.json
        episodes/
          episode_0001.json
          episode_0002.json
          ...
```

Use direct mode when you are happy to work with experiment IDs and the
repository layout directly.

---

## Step 2: List and Inspect Experiments

After running one or more configs, list the available experiments:

```bash
axis experiments list
```

You should see one row per persisted experiment, including its ID,
status, number of runs, and system type.

To inspect one experiment in more detail:

```bash
axis experiments show <experiment-id>
```

This is the main command for checking:

- which system was run
- whether the experiment is complete
- how many runs it contains
- what summary metrics were persisted

If an experiment was interrupted or only partially written, you can try:

```bash
axis experiments resume <experiment-id>
```

That command belongs to the direct experiment repository workflow, not
to the workspace layer.

---

## Step 3: Inspect Runs Within an Experiment

Each experiment contains one or more runs.

For a `single_run` config, there is usually one run:

```bash
axis runs list --experiment <experiment-id>
```

To inspect a specific run:

```bash
axis runs show run-0000 --experiment <experiment-id>
```

This is useful for checking:

- run status
- output form (`point` or `sweep`)
- variation metadata for OFAT runs
- number of episodes
- run-level summary metrics

For OFAT experiments, `axis runs list` and `axis runs show` are often
the fastest way to understand which variation corresponds to which run.

---

## Step 4: Run a Second Experiment and Compare

AXIS comparison works on persisted traces. That means you first run the
reference and candidate experiments separately, then compare their
stored artifacts.

Example:

```bash
axis experiments run experiments/configs/system-a-baseline.yaml
axis experiments run experiments/configs/system-c-baseline.yaml
```

Then list experiments and copy the two experiment IDs:

```bash
axis experiments list
```

Now compare the two primary runs:

```bash
axis compare \
  --reference-experiment <system-a-eid> --reference-run run-0000 \
  --candidate-experiment <system-c-eid> --candidate-run run-0000
```

That performs a full run-level comparison across all matched episodes.

To compare just one episode pair:

```bash
axis compare \
  --reference-experiment <system-a-eid> --reference-run run-0000 --reference-episode 1 \
  --candidate-experiment <system-c-eid> --candidate-run run-0000 --candidate-episode 1
```

The comparison layer is asymmetric:

- the **reference** is the baseline
- the **candidate** is the modified or alternative system

Use this direct comparison path when you want explicit control over
which persisted experiments and runs are being paired.

---

## Step 5: Visualize a Persisted Episode

Replay visualization also works directly from persisted experiment
artifacts.

Once you know an experiment ID and run ID, launch the viewer with:

```bash
axis visualize --experiment <experiment-id> --run run-0000 --episode 1
```

You can also open the viewer at a specific step:

```bash
axis visualize --experiment <experiment-id> --run run-0000 --episode 1 --step 50
```

This is the direct-mode equivalent of workspace visualization. No
workspace manifest is involved.

---

## Step 6: Use a Custom Result Root with `--root`

All of the commands above assume the default repository root:

```text
./experiments/results
```

If you want AXIS to read and write somewhere else, pass `--root`:

```bash
axis --root /tmp/axis-results experiments run experiments/configs/system-a-baseline.yaml
```

Then inspect that same repository with the same root:

```bash
axis --root /tmp/axis-results experiments list
axis --root /tmp/axis-results experiments show <experiment-id>
axis --root /tmp/axis-results runs list --experiment <experiment-id>
axis --root /tmp/axis-results runs show run-0000 --experiment <experiment-id>
```

This matters because direct CLI commands are **repository-root aware**,
not directory-context aware. They do not infer your intended root from
the current folder unless you pass `--root` yourself.

---

## When to Use Direct Mode vs Workspaces

Direct mode is usually the better fit when:

- you want the lowest-friction path from config to result
- you are comfortable managing experiment IDs directly
- you want one shared results repository
- you are doing ad hoc runs, debugging, or low-level inspection

Workspaces are usually the better fit when:

- you want configs, results, comparisons, and notes grouped together
- you want manifest-driven organization
- you want workspace-specific comparison and visualization routing
- you want a more structured investigation or development workflow

Neither replaces the other. Workspaces build on top of the underlying
experiment system, but the direct CLI remains a first-class way to use
AXIS.

---

## Quick Reference

```bash
# Run directly from a config
axis experiments run <config.yaml>

# Inspect the repository
axis experiments list
axis experiments show <experiment-id>
axis experiments resume <experiment-id>

# Inspect runs
axis runs list --experiment <experiment-id>
axis runs show <run-id> --experiment <experiment-id>

# Compare persisted traces
axis compare \
  --reference-experiment <eid> --reference-run <rid> \
  --candidate-experiment <eid> --candidate-run <rid>

# Visualize a persisted episode
axis visualize --experiment <eid> --run <rid> --episode 1

# Use a non-default result root
axis --root <results-root> experiments list
```
