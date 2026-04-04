# AXIS Experimentation Framework -- CLI User Manual

## Overview

The `axis` CLI runs and inspects experiments from the command line.
Every command is stateless: it reads from config files and persisted
repository artifacts, never from hidden caches or in-memory state.

```
python -m axis_system_a.cli <global-flags> <entity> <action> [arguments]
```

| Entity        | Actions                        |
|---------------|-------------------------------|
| `experiments` | `list`, `run`, `resume`, `show` |
| `runs`        | `list`, `show`                |

### Global flags

| Flag       | Default                 | Description                     |
|------------|-------------------------|---------------------------------|
| `--root`   | `./experiments/results` | Path to the repository root where all output data is written |
| `--output` | `text`                  | Output format: `text` or `json` |

---

## 1. Directory layout

The project separates config files from output data:

```
experiments/
    configs/                  # your experiment config files (input)
        baseline.json
        energy-gain-sweep.json
        sparsity-sweep.json
    results/                  # repository root: all output data (auto-created)
        baseline-10x10/
            experiment_config.json
            experiment_summary.json
            ...
            runs/
                run-0000/
                    run_summary.json
                    run_result.json
                    episodes/
                        episode_0001.json
                        ...
        energy-gain-sweep/
            ...
```

- **`experiments/configs/`** -- you put your experiment config files here.
- **`experiments/results/`** -- the CLI writes all output here automatically
  (one subdirectory per experiment). This is the default `--root`.

When you run `experiments run`, the entire result tree is created under
`experiments/results/<experiment-name>/`. You never need to create output
directories yourself.

---

## 2. Setting up an experiment

An experiment config is a single JSON or YAML file with two parts:
experiment-level parameters and the full simulation baseline.

### 2.1 Baseline single-run experiment

A ready-to-use config ships at `experiments/configs/baseline.json`:

```json
{
  "experiment_type": "single_run",
  "name": "baseline-10x10",
  "base_seed": 42,
  "num_episodes_per_run": 10,
  "agent_start_position": { "x": 0, "y": 0 },
  "baseline": {
    "general":    { "seed": 1 },
    "world":      { "grid_width": 10, "grid_height": 10, "resource_regen_rate": 0.05 },
    "agent":      { "initial_energy": 50.0, "max_energy": 100.0, "memory_capacity": 5 },
    "policy":     { "selection_mode": "sample", "temperature": 1.0, "stay_suppression": 0.1, "consume_weight": 1.5 },
    "transition": { "move_cost": 1.0, "consume_cost": 1.0, "stay_cost": 0.5, "max_consume": 1.0, "energy_gain_factor": 10.0 },
    "execution":  { "max_steps": 200 },
    "logging":    { "enabled": false }
  }
}
```

This runs 10 episodes on a 10x10 grid with deterministic seed 42.

### 2.2 Experiment-level fields

| Field                   | Required  | Description |
|-------------------------|-----------|-------------|
| `experiment_type`       | yes       | `"single_run"` or `"ofat"` |
| `name`                  | no        | Experiment identifier. Becomes the output directory name. If omitted, a UUID is generated. |
| `base_seed`             | no        | Root seed for deterministic episode seeds. Omit for random seeds. |
| `num_episodes_per_run`  | yes       | Number of episodes per run (must be > 0). |
| `agent_start_position`  | no        | `{"x": 0, "y": 0}` (default). |
| `baseline`              | yes       | Full simulation config (see below). |
| `parameter_path`        | OFAT only | Dot-path to the parameter to vary, e.g. `"transition.energy_gain_factor"`. |
| `parameter_values`      | OFAT only | List of values to sweep, e.g. `[5.0, 10.0, 20.0]`. |

### 2.3 Simulation baseline fields

The `baseline` object contains the full simulation configuration.
All sections except `logging` are required.

| Section      | Key fields |
|--------------|------------|
| `general`    | `seed` (int) |
| `world`      | `grid_width`, `grid_height`, `resource_regen_rate`, `regeneration_mode`, `regen_eligible_ratio`. See section 2.4 below. |
| `agent`      | `initial_energy`, `max_energy`, `memory_capacity` |
| `policy`     | `selection_mode` (`"sample"` or `"argmax"`), `temperature`, `stay_suppression`, `consume_weight` |
| `transition` | `move_cost`, `consume_cost`, `stay_cost`, `max_consume`, `energy_gain_factor` |
| `execution`  | `max_steps` |
| `logging`    | Optional. Controls console output, verbosity, and JSONL file logging. See section 2.4 below. |

### 2.4 World regeneration modes

The `world` section controls how resource cells recover over time.
Two modes are available:

**`all_traversable` (default)** -- every non-obstacle cell regenerates
each step. This is the original baseline behavior. You do not need to
specify `regeneration_mode` to get this -- it is the default when the
field is omitted.

```json
"world": {
  "grid_width": 10,
  "grid_height": 10,
  "resource_regen_rate": 0.05
}
```

**`sparse_fixed_ratio`** -- only a fixed subset of cells can regenerate.
The subset is chosen deterministically at world initialization (based on
the seed) and remains constant for the entire run. Non-eligible cells
never recover resource, even if depleted. The agent cannot observe
which cells are eligible -- it only sees current resource levels.

```json
"world": {
  "grid_width": 10,
  "grid_height": 10,
  "resource_regen_rate": 0.05,
  "regeneration_mode": "sparse_fixed_ratio",
  "regen_eligible_ratio": 0.17
}
```

| Field                   | Default              | Description |
|-------------------------|----------------------|-------------|
| `grid_width`            | required             | Width of the world grid (> 0) |
| `grid_height`           | required             | Height of the world grid (> 0) |
| `resource_regen_rate`   | `0.0`                | Per-step regeneration amount added to each eligible cell (0.0--1.0) |
| `regeneration_mode`     | `"all_traversable"`  | `"all_traversable"` or `"sparse_fixed_ratio"` |
| `regen_eligible_ratio`  | not set              | Fraction of traversable cells that can regenerate (0.0--1.0). **Required** when `regeneration_mode` is `"sparse_fixed_ratio"`. |

With `regen_eligible_ratio = 0.17`, roughly 17% of traversable cells
are regeneration-capable. This creates a spatially sparse resource
landscape where the agent must navigate to find cells that actually
recover energy.

Both modes use the same per-step regeneration rule:
`resource_next = min(1.0, resource_current + resource_regen_rate)`.

The new world parameters are fully OFAT-compatible. Example sweep config
is shipped at `experiments/configs/sparsity-sweep.json` (see section 2.5).

### 2.5 Logging configuration

The `logging` section inside `baseline` controls runtime observability.
All fields are optional — the defaults produce compact console output
with no file logging.

```json
"logging": {
  "enabled": true,
  "console_enabled": true,
  "verbosity": "verbose",
  "jsonl_enabled": true,
  "jsonl_path": "./experiment_log.jsonl",
  "include_decision_trace": true,
  "include_transition_trace": true
}
```

| Field                      | Default    | Description |
|----------------------------|------------|-------------|
| `enabled`                  | `true`     | Master switch. Set to `false` to suppress all logging. |
| `console_enabled`          | `true`     | Print human-readable step/episode output to the console. |
| `verbosity`                | `"compact"`| `"compact"` — one-line summaries per step. `"verbose"` — includes full decision and transition traces. |
| `jsonl_enabled`            | `false`    | Write machine-readable JSONL output to a file. |
| `jsonl_path`               | `null`     | File path for JSONL output. **Required** when `jsonl_enabled` is `true`. |
| `include_decision_trace`   | `true`     | Include the full decision trace (probabilities, contributions) in JSONL output. |
| `include_transition_trace` | `true`     | Include the full transition trace (position, energy deltas) in JSONL output. |

**Minimal (silent):**

```json
"logging": { "enabled": false }
```

**Compact console output (default):**

```json
"logging": { "enabled": true }
```

**Verbose console output:**

```json
"logging": { "enabled": true, "verbosity": "verbose" }
```

**Verbose console + JSONL file:**

```json
"logging": {
  "enabled": true,
  "verbosity": "verbose",
  "jsonl_enabled": true,
  "jsonl_path": "./my_experiment.jsonl"
}
```

### 2.6 OFAT (One-Factor-At-a-Time) experiment

An OFAT experiment varies one parameter across multiple values while keeping
everything else at baseline. Each value produces one separate run.

The `parameter_path` uses the format `section.field` where `section` is one
of: `general`, `world`, `agent`, `policy`, `transition`, `execution`, `logging`.

Example -- sweep `energy_gain_factor` across three values
(`experiments/configs/energy-gain-sweep.json`):

```json
{
  "experiment_type": "ofat",
  "name": "energy-gain-sweep",
  "base_seed": 42,
  "num_episodes_per_run": 10,
  "parameter_path": "transition.energy_gain_factor",
  "parameter_values": [5.0, 10.0, 20.0],
  "baseline": { "..." : "same baseline block as above" }
}
```

This produces three runs: `run-0000` (factor=5.0), `run-0001` (factor=10.0),
`run-0002` (factor=20.0).

A second shipped OFAT config sweeps the sparse regeneration ratio
(`experiments/configs/sparsity-sweep.json`):

```json
{
  "experiment_type": "ofat",
  "name": "sparsity-sweep",
  "base_seed": 42,
  "num_episodes_per_run": 10,
  "parameter_path": "world.regen_eligible_ratio",
  "parameter_values": [0.05, 0.10, 0.17, 0.30, 0.50],
  "baseline": {
    "...": "same baseline as above, but with:",
    "world": {
      "grid_width": 10, "grid_height": 10,
      "resource_regen_rate": 0.05,
      "regeneration_mode": "sparse_fixed_ratio",
      "regen_eligible_ratio": 0.17
    }
  }
}
```

This produces five runs, each with a different fraction of
regeneration-eligible cells. The experiment summary will show how
agent survival and energy change as the world becomes more or less sparse.

### 2.7 YAML format

YAML configs are also supported. The CLI detects format by file extension
(`.yaml` / `.yml`). The structure is identical to the JSON form.

---

## 3. Running an experiment

```
python -m axis_system_a.cli experiments run <config_file>
```

Run the shipped baseline:

```
$ python -m axis_system_a.cli experiments run experiments/configs/baseline.json
Experiment 'baseline-10x10' completed.
  Runs: 1
```

The output data is now at `experiments/results/baseline-10x10/`.

Run the OFAT sweep:

```
$ python -m axis_system_a.cli experiments run experiments/configs/energy-gain-sweep.json
Experiment 'energy-gain-sweep' completed.
  Runs: 3
```

Running the same experiment twice will fail -- the name must be unique:

```
$ python -m axis_system_a.cli experiments run experiments/configs/baseline.json
Error: Experiment already exists: baseline-10x10. Use --redo to overwrite.
```

### 3.1 Re-running an experiment with `--redo`

Use `--redo` to delete existing results and re-run an experiment from
scratch. This removes the entire experiment directory (including all
runs and episodes) before executing:

```
$ python -m axis_system_a.cli experiments run experiments/configs/baseline.json --redo
Experiment 'baseline-10x10' completed.
  Runs: 1
```

This is useful when you have changed the config file and want fresh
results without manually deleting the output directory.

> **Warning:** `--redo` permanently deletes all previous results for that
> experiment name. If you want to keep the old results, rename the
> experiment in the config file instead.

---

## 4. Analyzing experiment data

All experiment data is written as plain JSON files into the repository.
There are three ways to access it: CLI inspection commands, CLI JSON output
for scripting, and reading the raw files directly.

### 4.1 Where the data lives

After running the baseline experiment, the repository at
`experiments/results/baseline-10x10/` contains:

```
experiments/results/baseline-10x10/
    experiment_config.json      # the input config (copy)
    experiment_metadata.json    # id, type, creation timestamp
    experiment_status.json      # {"status": "completed"}
    experiment_summary.json     # aggregated summary across all runs
    runs/
        run-0000/
            run_config.json     # resolved run configuration
            run_metadata.json   # run id, variation, seed
            run_status.json     # {"status": "completed"}
            run_summary.json    # aggregate statistics over 10 episodes
            run_result.json     # full result (all episode data combined)
            episodes/
                episode_0001.json   # complete trace of episode 1
                episode_0002.json
                ...
                episode_0010.json
```

Every file is self-contained JSON. You can read any of them with `cat`,
`python`, `jq`, or load them into a notebook.

### 4.2 Run-level summary (aggregate statistics)

The most useful starting point for analysis is the **run summary**. Each
run aggregates all its episodes into these statistics:

```
$ cat experiments/results/baseline-10x10/runs/run-0000/run_summary.json
```

```json
{
  "num_episodes": 10,
  "mean_steps": 200.0,
  "std_steps": 0.0,
  "mean_final_energy": 92.4,
  "std_final_energy": 4.91,
  "death_rate": 0.0,
  "mean_consumption_count": 38.7,
  "std_consumption_count": 4.31
}
```

| Metric                    | Description |
|---------------------------|-------------|
| `num_episodes`            | Total episodes in this run |
| `mean_steps`              | Mean episode length (steps before termination) |
| `std_steps`               | Standard deviation of episode length |
| `mean_final_energy`       | Mean agent energy at episode end |
| `std_final_energy`        | Standard deviation of final energy |
| `death_rate`              | Fraction of episodes ending by energy depletion (0.0--1.0) |
| `mean_consumption_count`  | Mean successful consume actions per episode |
| `std_consumption_count`   | Standard deviation of consumption count |

The same data is accessible via the CLI:

```
$ python -m axis_system_a.cli runs show run-0000 --experiment baseline-10x10
Run: run-0000
  Experiment: baseline-10x10
  Status: completed
  Variation: baseline
  Base seed: 42
  Episodes: 10
  Summary: mean_steps=200.0  death_rate=0.00  mean_energy=92.4
```

### 4.3 Experiment-level summary (OFAT comparison)

For OFAT experiments, the experiment summary compares all runs against
the first run (baseline). Open it directly:

```
$ cat experiments/results/energy-gain-sweep/experiment_summary.json
```

```json
{
  "num_runs": 3,
  "run_entries": [
    {
      "run_id": "run-0000",
      "variation_description": "transition.energy_gain_factor=5.0",
      "summary": { "mean_final_energy": 31.9, "death_rate": 0.0, "mean_consumption_count": 44.4, "..." : "..." },
      "delta_mean_steps": 0.0,
      "delta_mean_final_energy": 0.0,
      "delta_death_rate": 0.0
    },
    {
      "run_id": "run-0001",
      "variation_description": "transition.energy_gain_factor=10.0",
      "summary": { "mean_final_energy": 95.9, "..." : "..." },
      "delta_mean_steps": 0.0,
      "delta_mean_final_energy": 64.0,
      "delta_death_rate": 0.0
    },
    {
      "run_id": "run-0002",
      "variation_description": "transition.energy_gain_factor=20.0",
      "summary": { "mean_final_energy": 92.5, "..." : "..." },
      "delta_mean_steps": 0.0,
      "delta_mean_final_energy": 60.6,
      "delta_death_rate": 0.0
    }
  ]
}
```

The delta fields show the difference from the first run:
- `delta_mean_final_energy = 64.0` means the agent ends with 64 more energy
  on average compared to the energy_gain_factor=5.0 baseline.

### 4.4 Episode-level data (step-by-step trace)

Each episode file contains the full execution trace. This is the most
detailed data available:

```
$ python -c "import json; ep = json.load(open('experiments/results/baseline-10x10/runs/run-0000/episodes/episode_0001.json')); print(json.dumps(ep['summary'], indent=2))"
```

```json
{
  "survival_length": 200,
  "action_counts": { "UP": 31, "DOWN": 35, "LEFT": 30, "RIGHT": 38, "CONSUME": 39, "STAY": 27 },
  "total_consume_events": 39,
  "total_failed_consumes": 0,
  "mean_energy": 85.0,
  "min_energy": 45.0,
  "max_energy": 100.0
}
```

Each episode file contains:

| Field                | Content |
|----------------------|---------|
| `total_steps`        | Number of steps in this episode |
| `termination_reason` | `"max_steps_reached"` or `"energy_depleted"` |
| `final_agent_state`  | Agent energy and memory at episode end |
| `final_position`     | Agent grid position at episode end |
| `summary`            | Per-episode statistics (action counts, energy min/max/mean, consumption) |
| `steps`              | Array of every step: observation, selected action, drive output, position, energy |

The `steps` array gives you the full timestep-by-timestep trajectory for
detailed behavioral analysis.

### 4.5 Scripting with --output json and jq

For automated analysis, use `--output json` to get structured data
from CLI commands.

**Extract run summaries into a comparison table:**

```bash
python -m axis_system_a.cli --output json experiments show energy-gain-sweep \
  | jq -r '.summary.run_entries[] | [.variation_description, .summary.mean_final_energy, .summary.death_rate, .delta_mean_final_energy] | @tsv'
```

```
transition.energy_gain_factor=5.0    31.875    0.0    0.0
transition.energy_gain_factor=10.0   95.9      0.0    64.025
transition.energy_gain_factor=20.0   92.5      0.0    60.625
```

**Get full JSON for a single run:**

```bash
python -m axis_system_a.cli --output json runs show run-0000 --experiment baseline-10x10
```

```json
{
  "run_id": "run-0000",
  "experiment_id": "baseline-10x10",
  "status": "completed",
  "base_seed": 42,
  "num_episodes": 10,
  "summary": {
    "num_episodes": 10,
    "mean_steps": 200.0,
    "std_steps": 0.0,
    "mean_final_energy": 92.4,
    "std_final_energy": 4.91,
    "death_rate": 0.0,
    "mean_consumption_count": 38.7,
    "std_consumption_count": 4.31
  }
}
```

### 4.6 Loading data in Python

Since all artifacts are Pydantic models serialized as JSON, you can
load them directly in Python scripts or notebooks:

```python
import json
from axis_system_a import ExperimentRepository, RunResult, EpisodeResult
from pathlib import Path

repo = ExperimentRepository(Path("experiments/results"))

# Load a run summary
summary = repo.load_run_summary("baseline-10x10", "run-0000")
print(f"Mean energy: {summary.mean_final_energy}")
print(f"Death rate:  {summary.death_rate}")

# Load full run result (includes all episode data)
result = repo.load_run_result("baseline-10x10", "run-0000")
for i, ep in enumerate(result.episode_results):
    print(f"  Episode {i+1}: {ep.total_steps} steps, "
          f"energy={ep.final_agent_state.energy}, "
          f"reason={ep.termination_reason.value}")

# Load a single episode for detailed step analysis
ep = repo.load_episode_result("baseline-10x10", "run-0000", 1)
print(f"Action counts: {ep.summary.action_counts}")
print(f"Energy range:  {ep.summary.min_energy} - {ep.summary.max_energy}")
print(f"Total steps recorded: {len(ep.steps)}")

# Load OFAT experiment summary with deltas
exp_summary = repo.load_experiment_summary("energy-gain-sweep")
for entry in exp_summary.run_entries:
    print(f"{entry.variation_description}: "
          f"energy={entry.summary.mean_final_energy:.1f}, "
          f"delta={entry.delta_mean_final_energy:+.1f}")
```

Output:

```
Mean energy: 92.4
Death rate:  0.0
  Episode 1: 200 steps, energy=90.5, reason=max_steps_reached
  Episode 2: 200 steps, energy=88.0, reason=max_steps_reached
  ...
Action counts: {'UP': 31, 'DOWN': 35, 'LEFT': 30, 'RIGHT': 38, 'CONSUME': 39, 'STAY': 27}
Energy range:  45.0 - 100.0
Total steps recorded: 200
transition.energy_gain_factor=5.0: energy=31.9, delta=+0.0
transition.energy_gain_factor=10.0: energy=95.9, delta=+64.0
transition.energy_gain_factor=20.0: energy=92.5, delta=+60.6
```

---

## 5. Inspecting experiments via CLI

### 5.1 List all experiments

```
$ python -m axis_system_a.cli experiments list
baseline-10x10     status=completed  runs=1  completed=1  created=2026-04-04T12:47:22Z
energy-gain-sweep  status=completed  runs=3  completed=3  created=2026-04-04T12:48:44Z
```

### 5.2 Show experiment details

```
$ python -m axis_system_a.cli experiments show energy-gain-sweep
Experiment: energy-gain-sweep
  Status: completed
  Type: ofat
  Name: energy-gain-sweep
  Runs: ['run-0000', 'run-0001', 'run-0002']
  Summary: 3 runs
    run-0000  transition.energy_gain_factor=5.0
    run-0001  transition.energy_gain_factor=10.0
    run-0002  transition.energy_gain_factor=20.0
```

### 5.3 List runs within an experiment

```
$ python -m axis_system_a.cli runs list --experiment energy-gain-sweep
run-0000  status=completed  transition.energy_gain_factor=5.0   summary=yes
run-0001  status=completed  transition.energy_gain_factor=10.0  summary=yes
run-0002  status=completed  transition.energy_gain_factor=20.0  summary=yes
```

### 5.4 Show a single run

```
$ python -m axis_system_a.cli runs show run-0000 --experiment energy-gain-sweep
Run: run-0000
  Experiment: energy-gain-sweep
  Status: completed
  Variation: transition.energy_gain_factor=5.0
  Base seed: 42
  Episodes: 10
  Summary: mean_steps=200.0  death_rate=0.00  mean_energy=31.9
```

---

## 6. Resuming failed or interrupted experiments

If an experiment is interrupted (process killed, a run crashes, etc.),
the completed runs remain safely persisted on disk. The `resume` command
picks up where execution left off.

### 6.1 Resume command

```
python -m axis_system_a.cli experiments resume <experiment_id>
```

Resume logic:
1. Loads the persisted experiment config from the repository.
2. Re-derives the full run plan.
3. Checks each run: if status is `COMPLETED` and all artifacts are valid,
   the run is skipped.
4. Re-executes any run that is `FAILED`, `RUNNING`, `PENDING`, or has
   missing/incomplete artifacts -- from scratch (entire run, not
   individual episodes).
5. Rebuilds the experiment summary from all runs (both previously
   completed and newly executed).
6. Sets the experiment status to `COMPLETED`.

### 6.2 Example: recovering from a partial OFAT experiment

Suppose an OFAT experiment with 3 runs failed during the third run.
The experiment status on disk will be `partial`:

```
$ python -m axis_system_a.cli experiments list
energy-gain-sweep  status=partial  runs=3  completed=2  ...
```

Resume it:

```
$ python -m axis_system_a.cli experiments resume energy-gain-sweep
Experiment 'energy-gain-sweep' resumed and completed.
  Runs: 3
```

Only `run-0002` was re-executed. `run-0000` and `run-0001` were loaded
from disk without re-running.

### 6.3 Idempotent behavior

Resuming an already completed experiment is safe -- it returns the
existing result without re-executing anything:

```
$ python -m axis_system_a.cli experiments resume baseline-10x10
Experiment 'baseline-10x10' resumed and completed.
  Runs: 1
```

You can call `resume` as many times as you want. Completed runs are
never re-executed.

### 6.4 When resume fails again

If the re-executed run fails again during resume, the experiment status
is updated to `partial` (if some runs are completed) or `failed` (if
no runs completed), and the error is reported. Fix the underlying issue
and resume again.

### 6.5 Experiment status reference

| Status      | Meaning |
|-------------|---------|
| `created`   | Experiment directory initialized, no runs started yet |
| `running`   | Execution in progress |
| `completed` | All runs finished successfully |
| `partial`   | Some runs completed, at least one failed |
| `failed`    | No runs completed successfully |

---

## 7. Quick reference

```bash
# Run the shipped baseline experiment
python -m axis_system_a.cli experiments run experiments/configs/baseline.json

# Run the OFAT sweep
python -m axis_system_a.cli experiments run experiments/configs/energy-gain-sweep.json

# Run the sparsity sweep (sparse regeneration mode)
python -m axis_system_a.cli experiments run experiments/configs/sparsity-sweep.json

# Re-run an experiment (deletes previous results)
python -m axis_system_a.cli experiments run experiments/configs/baseline.json --redo

# List all experiments
python -m axis_system_a.cli experiments list

# Inspect an experiment
python -m axis_system_a.cli experiments show baseline-10x10

# List runs
python -m axis_system_a.cli runs list --experiment energy-gain-sweep

# Inspect a run
python -m axis_system_a.cli runs show run-0000 --experiment energy-gain-sweep

# Resume a failed experiment
python -m axis_system_a.cli experiments resume energy-gain-sweep

# Get JSON output (any command)
python -m axis_system_a.cli --output json experiments show baseline-10x10

# Use a custom repository directory
python -m axis_system_a.cli --root /data/results experiments list

# Read raw summary file directly
cat experiments/results/baseline-10x10/runs/run-0000/run_summary.json | python -m json.tool

# Load data in Python
python -c "
from axis_system_a import ExperimentRepository
from pathlib import Path
repo = ExperimentRepository(Path('experiments/results'))
s = repo.load_run_summary('baseline-10x10', 'run-0000')
print(f'mean_energy={s.mean_final_energy}, death_rate={s.death_rate}')
"
```
