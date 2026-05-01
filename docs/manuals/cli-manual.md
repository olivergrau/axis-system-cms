# AXIS Experimentation Framework -- CLI User Manual (v0.2.0)

> **Related manuals:**
> [Configuration Reference](config-manual.md) |
> [Visualization Manual](visualization-manual.md) |
> [Paired Trace Comparison](comparison-manual.md) |
> [Experiment Workspaces](workspace-manual.md) |
> [System Developer Manual](system-dev-manual.md) |
> [World Developer Manual](world-dev-manual.md)
>
> **Tutorials:**
> [Building a System](../tutorials/building-a-system.md) |
> [Building a World](../tutorials/building-a-world.md) |
> [Using AXIS Without Workspaces](../tutorials/direct-cli-workflow.md)

## Overview

The `axis` CLI runs and inspects experiments from the command line.
Every command is stateless: it reads from config files and persisted
repository artifacts, never from hidden caches or in-memory state.

```
axis <global-flags> <entity> <action> [arguments]
```

| Entity        | Actions                         |
|---------------|---------------------------------|
| `experiments` | `list`, `run`, `resume`, `show` |
| `runs`        | `list`, `show`, `metrics`       |
| `workspaces`  | `scaffold`, `check`, `show`, `run`, `measure`, `run-series`, `compare`, `comparison-summary`, `run-summary`, `run-metrics`, `sweep-result`, `set-candidate`, `reset`, `close` |
| `compare`     | *(no sub-action -- runs paired trace comparison)* |
| `visualize`   | *(no sub-action -- launches viewer)* |

Workspace commands are documented in detail in the
[Experiment Workspaces](workspace-manual.md) manual. In short, they add a
workspace-local layer for managing `results/`, `comparisons/`, and
`measurements/` around the normal experiment engine.

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
    configs/                      # v0.2.0 experiment config files (input)
        system-a-baseline.yaml
        system-a-energy-gain-sweep.yaml
        system-a-toroidal-demo.yaml
        system-b-sdk-demo.yaml
    results/                      # repository root: all output data (auto-created)
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
                    behavior_metrics.json
                    run_result.json
                    episodes/
                        episode_0001.json
                        episode_0002.json
                        ...
```

- **`experiments/configs/`** -- you put your experiment config files here.
- **`experiments/results/`** -- the CLI writes all output here automatically
  (one subdirectory per experiment). This is the default `--root`.

When you run `experiments run`, the entire result tree is created under
`experiments/results/<experiment-id>/`. You never need to create output
directories yourself.

> **Note:** In v0.2.0, experiment IDs are auto-generated UUIDs. The
> config file does not contain a `name` field. Use `experiments list`
> to see your experiment IDs after running.

---

## 2. Config file format

An experiment config is a single JSON or YAML file. The v0.2.0 format
separates concerns into three areas:

1. **Framework sections** (`general`, `execution`, `world`, `logging`) --
   owned by the framework, identical across all system types.
2. **System section** (`system`) -- an opaque dictionary passed to the
   registered system. Its internal structure depends on the system type.
3. **Experiment parameters** (`experiment_type`, `system_type`,
   `num_episodes_per_run`, OFAT fields) -- control experiment execution.

### 2.1 Baseline single-run experiment (System A)

A ready-to-use config ships at `experiments/configs/system-a-baseline.yaml`:

```yaml
system_type: "system_a"
experiment_type: "single_run"

general:
  seed: 42

execution:
  max_steps: 200

world:
  world_type: "grid_2d"
  grid_width: 10
  grid_height: 10
  obstacle_density: 0.2
  resource_regen_rate: 0.2
  regeneration_mode: "sparse_fixed_ratio"
  regen_eligible_ratio: 0.17

system:
  agent:
    initial_energy: 50.0
    max_energy: 100.0
    buffer_capacity: 25
  policy:
    selection_mode: "sample"
    temperature: 1.0
    stay_suppression: 0.1
    consume_weight: 2.5
  transition:
    move_cost: 1.0
    consume_cost: 1.0
    stay_cost: 0.5
    max_consume: 1.0
    energy_gain_factor: 10.0

num_episodes_per_run: 5
```

This runs 5 episodes on a 10x10 grid with sparse regeneration and
deterministic seed 42.

### 2.2 Experiment-level fields

| Field                   | Required  | Description |
|-------------------------|-----------|-------------|
| `system_type`           | yes       | Registered system type (e.g. `"system_a"`). Determines which system implementation is loaded. |
| `experiment_type`       | yes       | `"single_run"` or `"ofat"` |
| `general`               | yes       | `{ "seed": <int> }` -- base seed for deterministic execution |
| `execution`             | yes       | `{ "max_steps": <int> }` -- max steps per episode |
| `world`                 | yes       | World grid configuration (see section 2.3) |
| `logging`               | no        | Logging configuration (see section 2.5). Defaults to enabled. |
| `system`                | yes       | System-specific configuration (opaque dict). Structure depends on `system_type`. |
| `num_episodes_per_run`  | yes       | Number of episodes per run (must be > 0). |
| `agent_start_position`  | no        | `{"x": 0, "y": 0}` (default). |
| `parameter_path`        | OFAT only | 3-segment dot-path to the parameter to vary (see section 2.6). |
| `parameter_values`      | OFAT only | List of values to sweep, e.g. `[5.0, 10.0, 20.0]`. |

### 2.3 World configuration

The `world` section configures the grid environment. These fields are
framework-owned and identical regardless of system type.

| Field               | Default   | Description |
|---------------------|-----------|-------------|
| `grid_width`        | required  | Width of the world grid (> 0) |
| `grid_height`       | required  | Height of the world grid (> 0) |
| `obstacle_density`  | `0.0`     | Fraction of cells that are obstacles (0.0--1.0) |
| `resource_regen_rate`  | `0.0`  | Per-step regeneration amount added to each eligible cell (0.0--1.0) |
| `regeneration_mode`    | `"all_traversable"` | `"all_traversable"`, `"sparse_fixed_ratio"`, or `"clustered"` |
| `regen_eligible_ratio` | not set | Fraction of traversable cells that can regenerate (0.0--1.0). Required when mode is `"sparse_fixed_ratio"` or `"clustered"`. |
| `num_clusters`         | not set | Number of regeneration clusters. Required when mode is `"clustered"`. |
| `world_type`           | `"grid_2d"` | World implementation type: `"grid_2d"`, `"toroidal"`, or `"signal_landscape"`. See the World Developer Manual for details on each type. |

Regeneration is a property of the world, not the system. All world
dynamics parameters (regeneration rate, mode, eligibility) are
configured here.

### 2.4 System A configuration reference

When `system_type` is `"system_a"`, the `system` dict has three
sub-sections. All fields are required (see the Configuration Reference
Manual for full constraints).

**`system.agent`** -- Agent parameters

| Field              | Baseline | Description |
|--------------------|----------|-------------|
| `initial_energy`   | `50.0`   | Starting energy |
| `max_energy`       | `100.0`  | Energy cap |
| `buffer_capacity`  | `25`     | Number of recent cells remembered |

**`system.policy`** -- Action selection

| Field              | Baseline   | Description |
|--------------------|------------|-------------|
| `selection_mode`   | `"sample"` | `"sample"` (stochastic) or `"argmax"` (deterministic) |
| `temperature`      | `1.0`      | Softmax temperature (only used in `"sample"` mode) |
| `stay_suppression` | `0.1`      | Penalty applied to the "stay" action |
| `consume_weight`   | `2.5`      | Bonus applied to the "consume" action when resources present |

**`system.transition`** -- Energy dynamics

| Field               | Baseline | Description |
|----------------------|----------|-------------|
| `move_cost`          | `1.0`    | Energy cost per movement action |
| `consume_cost`       | `1.0`    | Energy cost to attempt consumption |
| `stay_cost`          | `0.5`    | Energy cost for staying in place |
| `max_consume`        | `1.0`    | Max resource fraction consumed per action |
| `energy_gain_factor` | `10.0`   | Multiplier converting consumed resource to energy |

### 2.5 Logging configuration

The `logging` section controls runtime observability. All fields are
optional -- the defaults produce compact console output with no file
logging.

```yaml
logging:
  enabled: true
  console_enabled: true
  verbosity: "compact"   # or "verbose"
  jsonl_enabled: false
  jsonl_path: null
  include_decision_trace: true
  include_transition_trace: true
```

| Field                      | Default     | Description |
|----------------------------|-------------|-------------|
| `enabled`                  | `true`      | Master switch. Set to `false` to suppress all logging. |
| `console_enabled`          | `true`      | Print step/episode output to the console. |
| `verbosity`                | `"compact"` | `"compact"` or `"verbose"` |
| `jsonl_enabled`            | `false`     | Write JSONL output to a file. |
| `jsonl_path`               | `null`      | File path for JSONL output. Required when `jsonl_enabled` is `true`. |
| `include_decision_trace`   | `true`      | Include decision trace in JSONL output. |
| `include_transition_trace` | `true`      | Include transition trace in JSONL output. |

Set `logging: { enabled: false }` for silent operation (recommended for
batch experiments).

### 2.6 OFAT (One-Factor-At-a-Time) experiment

An OFAT experiment varies one parameter across multiple values while
keeping everything else at baseline. Each value produces one separate run.

The `parameter_path` uses a 3-segment format: `<domain>.<section>.<field>`.

| Domain        | Meaning | Example paths |
|---------------|---------|---------------|
| `framework`   | Framework-owned sections | `framework.execution.max_steps`, `framework.world.grid_width` |
| `system`      | System-specific config   | `system.transition.energy_gain_factor`, `system.policy.temperature` |

Example -- sweep `energy_gain_factor` across four values
(`experiments/configs/system-a-energy-gain-sweep.yaml`):

```yaml
system_type: "system_a"
experiment_type: "ofat"

general:
  seed: 42
execution:
  max_steps: 200
world:
  grid_width: 10
  grid_height: 10
  obstacle_density: 0.0
system:
  agent:
    initial_energy: 50.0
    max_energy: 100.0
    buffer_capacity: 5
  policy:
    selection_mode: "sample"
    temperature: 1.0
    stay_suppression: 0.1
    consume_weight: 1.5
  transition:
    move_cost: 1.0
    consume_cost: 1.0
    stay_cost: 0.5
    max_consume: 1.0
    energy_gain_factor: 10.0

num_episodes_per_run: 5

parameter_path: "system.transition.energy_gain_factor"
parameter_values: [5.0, 10.0, 15.0, 20.0]
```

This produces four runs: `run-0000` (factor=5.0), `run-0001`
(factor=10.0), `run-0002` (factor=15.0), `run-0003` (factor=20.0).

Each run uses a different base seed (spaced by 1000) for independent
episode randomization.

### 2.7 YAML and JSON formats

Both YAML and JSON configs are supported. The CLI detects format by
file extension (`.yaml`/`.yml` for YAML, anything else treated as JSON).
The structure is identical in both formats.

---

## 3. Modifying the baseline configuration

To create a custom experiment, copy the shipped baseline config and
modify the values you want to change. Here are common examples using
System A.

### 3.1 Changing world size and episode count

```yaml
# my-large-world.yaml -- 20x20 grid, 20 episodes, 500 steps
system_type: "system_a"
experiment_type: "single_run"

general:
  seed: 100
execution:
  max_steps: 500
world:
  grid_width: 20
  grid_height: 20
  obstacle_density: 0.1
  resource_regen_rate: 0.05
system:
  agent:
    initial_energy: 50.0
    max_energy: 100.0
    buffer_capacity: 5
  policy:
    selection_mode: "sample"
    temperature: 1.0
    stay_suppression: 0.1
    consume_weight: 1.5
  transition:
    move_cost: 1.0
    consume_cost: 1.0
    stay_cost: 0.5
    max_consume: 1.0
    energy_gain_factor: 10.0

num_episodes_per_run: 20
```

Key changes from the baseline:
- Larger grid (20x20 instead of 10x10)
- 10% obstacles (vs 20% in the baseline)
- 500 max steps instead of 200
- Lower resource regeneration at 5% per step (vs 20% in the baseline)
- 20 episodes instead of 5

### 3.2 Changing agent behavior

To make the agent more aggressive (higher consume preference) or more
conservative (lower energy costs):

```yaml
# Aggressive consumer -- high consume weight, low costs
system:
  agent:
    initial_energy: 80.0
    max_energy: 150.0
    buffer_capacity: 10
  policy:
    selection_mode: "sample"
    temperature: 0.5        # lower temperature = flatter distribution
    stay_suppression: 0.3   # strongly penalize staying
    consume_weight: 3.0     # strongly prefer consuming
  transition:
    move_cost: 0.5          # cheap movement
    consume_cost: 0.5       # cheap consumption
    stay_cost: 1.0          # expensive staying
    max_consume: 1.0
    energy_gain_factor: 15.0  # more energy per resource
```

### 3.3 Deterministic (argmax) mode

Switch to deterministic action selection for reproducible trajectories
that are easier to analyze:

```yaml
system:
  policy:
    selection_mode: "argmax"  # always picks highest-weighted action
    temperature: 1.0          # ignored in argmax mode
    stay_suppression: 0.1
    consume_weight: 1.5
```

### 3.4 Sparse regeneration

Use the sparse regeneration mode to create a world where only a
fraction of cells can recover resource:

```yaml
world:
  grid_width: 10
  grid_height: 10
  resource_regen_rate: 0.05
  regeneration_mode: "sparse_fixed_ratio"
  regen_eligible_ratio: 0.17   # only ~17% of cells regenerate
```

### 3.5 Sweeping a system parameter (OFAT)

To sweep the policy temperature:

```yaml
experiment_type: "ofat"
parameter_path: "system.policy.temperature"
parameter_values: [0.1, 0.5, 1.0, 2.0, 5.0]
```

To sweep a framework parameter (max steps):

```yaml
experiment_type: "ofat"
parameter_path: "framework.execution.max_steps"
parameter_values: [50, 100, 200, 500]
```

---

## 4. Running an experiment

```
axis experiments run <config_file>
```

Run the shipped baseline:

```
$ axis experiments run experiments/configs/system-a-baseline.yaml
Experiment completed.
  ID: a1b2c3d4e5f6...
  Runs: 1
```

The output data is now at `experiments/results/<experiment-id>/`.

Run the OFAT sweep:

```
$ axis experiments run experiments/configs/system-a-energy-gain-sweep.yaml
Experiment completed.
  ID: f7e8d9c0b1a2...
  Runs: 4
```

### 4.1 Re-running an experiment

Since experiment IDs are auto-generated, each run produces a new
experiment directory. There is no name collision. To remove old results,
delete the experiment directory manually or use `experiments list` to
find old experiment IDs.

---

## 5. Analyzing experiment data

All experiment data is written as plain JSON files into the repository.
There are three ways to access it: CLI inspection commands, CLI JSON
output for scripting, and reading the raw files directly.

### 5.1 Where the data lives

After running the baseline experiment, the repository at
`experiments/results/<experiment-id>/` contains:

```
experiments/results/<experiment-id>/
    experiment_config.json      # the input config (copy)
    experiment_metadata.json    # id, type, system_type, creation timestamp
    experiment_status.json      # {"status": "completed"}
    experiment_summary.json     # aggregated summary across all runs
    runs/
            run-0000/
                run_config.json     # resolved run configuration
                run_metadata.json   # run id, variation, seed
                run_status.json     # {"status": "completed"}
                run_summary.json    # aggregate statistics over N episodes
                behavior_metrics.json # behavioral metrics from replay-capable traces
                run_result.json     # full result (all episode data combined)
                episodes/
                    episode_0001.json   # complete trace of episode 1
                    episode_0002.json
                    ...
```

Every file is self-contained JSON. You can read any of them with `cat`,
`python`, `jq`, or load them into a notebook.

### 5.2 Run-level summary (aggregate statistics)

The most useful starting point for analysis is the **run summary**. Each
run aggregates all its episodes into system-agnostic statistics:

```json
{
  "num_episodes": 5,
  "mean_steps": 142.6,
  "std_steps": 28.3,
  "mean_final_vitality": 0.45,
  "std_final_vitality": 0.12,
  "death_rate": 0.2
}
```

| Metric                    | Description |
|---------------------------|-------------|
| `num_episodes`            | Total episodes in this run |
| `mean_steps`              | Mean episode length (steps before termination) |
| `std_steps`               | Standard deviation of episode length |
| `mean_final_vitality`     | Mean normalized vitality at episode end (0.0--1.0) |
| `std_final_vitality`      | Standard deviation of final vitality |
| `death_rate`              | Fraction of episodes ending by system termination (0.0--1.0) |

> **Note:** v0.2.0 uses `mean_final_vitality` (normalized, 0.0--1.0)
> instead of the v0.1.0 `mean_final_energy` (raw value). For System A,
> vitality = energy / max_energy.

### 5.2a Run-level behavioral metrics

AXIS also supports a dedicated behavioral metrics artifact for replay-capable
runs.

Supported trace modes:

- `full`
- `delta`

Unsupported:

- `light`

The artifact is stored as:

```text
results/<experiment-id>/runs/<run-id>/behavior_metrics.json
```

Inspect it directly via CLI:

```bash
axis runs metrics run-0000 --experiment <experiment-id>
```

Or as JSON:

```bash
axis runs metrics run-0000 --experiment <experiment-id> --output json
```

The behavioral metrics layer includes:

- framework-standard metrics such as:
  - resource efficiency
  - failed movement rate
  - action entropy
  - coverage and revisit behavior
- optional system-specific metrics supplied via the metrics extension system

If the artifact does not exist yet, AXIS computes it lazily from the persisted
replay-capable episode traces and then saves it.

### 5.3 Experiment-level summary (OFAT comparison)

For OFAT experiments, the experiment summary compares all runs against
the first run (baseline):

```json
{
  "num_runs": 4,
  "run_entries": [
    {
      "run_id": "run-0000",
      "variation_description": "system.transition.energy_gain_factor=5.0",
      "summary": { "mean_final_vitality": 0.32, "death_rate": 0.0, "..." : "..." },
      "delta_mean_steps": 0.0,
      "delta_mean_final_vitality": 0.0,
      "delta_death_rate": 0.0
    },
    {
      "run_id": "run-0001",
      "variation_description": "system.transition.energy_gain_factor=10.0",
      "summary": { "mean_final_vitality": 0.96, "..." : "..." },
      "delta_mean_steps": 0.0,
      "delta_mean_final_vitality": 0.64,
      "delta_death_rate": 0.0
    }
  ]
}
```

The delta fields show the difference from the first run.

### 5.4 Episode-level data (step-by-step trace)

Each episode file contains the full execution trace with step-by-step
data:

| Field               | Content |
|---------------------|---------|
| `system_type`       | Which system ran this episode (e.g. `"system_a"`) |
| `total_steps`       | Number of steps in this episode |
| `termination_reason`| `"max_steps_reached"` or system-specific (e.g. `"energy_depleted"`) |
| `final_vitality`    | Normalized vitality at episode end |
| `final_position`    | Agent grid position at episode end |
| `steps`             | Array of step traces (see below) |

Each step trace contains:

| Field                    | Content |
|--------------------------|---------|
| `timestep`               | Step index (0-based) |
| `action`                 | Selected action name (e.g. `"right"`, `"consume"`) |
| `agent_position_before`  | Position before action |
| `agent_position_after`   | Position after action |
| `vitality_before`        | Normalized vitality before step |
| `vitality_after`         | Normalized vitality after step |
| `world_before`           | Full world snapshot before step |
| `world_after`            | Full world snapshot after action |
| `terminated`             | Whether this step ended the episode |
| `system_data`            | System-specific decision and transition data |

### 5.5 Scripting with --output json and jq

For automated analysis, use `--output json` to get structured data
from CLI commands.

**Extract run summaries into a comparison table:**

```bash
axis --output json experiments show <experiment-id> \
  | jq -r '.summary.run_entries[] | [.variation_description, .summary.mean_final_vitality, .summary.death_rate, .delta_mean_final_vitality] | @tsv'
```

```
system.transition.energy_gain_factor=5.0    0.319   0.0    0.0
system.transition.energy_gain_factor=10.0   0.959   0.0    0.640
system.transition.energy_gain_factor=15.0   0.925   0.0    0.606
system.transition.energy_gain_factor=20.0   0.910   0.0    0.591
```

**Get full JSON for a single run:**

```bash
axis --output json runs show run-0000 --experiment <experiment-id>
```

### 5.6 Loading data in Python

Since all artifacts are Pydantic models serialized as JSON, you can
load them directly in Python scripts or notebooks:

```python
from pathlib import Path
from axis.framework.persistence import ExperimentRepository

repo = ExperimentRepository(Path("experiments/results"))

# List all experiments
for eid in repo.list_experiments():
    status = repo.load_experiment_status(eid)
    meta = repo.load_experiment_metadata(eid)
    print(f"{eid}  system={meta.system_type}  status={status.value}")

# Load a run summary
eid = repo.list_experiments()[0]
rid = repo.list_runs(eid)[0]
summary = repo.load_run_summary(eid, rid)
print(f"Mean vitality: {summary.mean_final_vitality:.3f}")
print(f"Death rate:    {summary.death_rate:.2f}")

# Load full run result (includes all episode traces)
result = repo.load_run_result(eid, rid)
for i, trace in enumerate(result.episode_traces):
    print(f"  Episode {i+1}: {trace.total_steps} steps, "
          f"vitality={trace.final_vitality:.3f}, "
          f"reason={trace.termination_reason}")

# Load a single episode trace for step analysis
trace = repo.load_episode_trace(eid, rid, 1)
print(f"Total steps: {trace.total_steps}")
for step in trace.steps[:5]:  # first 5 steps
    print(f"  Step {step.timestep}: action={step.action}, "
          f"vitality={step.vitality_after:.3f}")

# Load OFAT experiment summary with deltas
exp_summary = repo.load_experiment_summary(eid)
for entry in exp_summary.run_entries:
    print(f"{entry.variation_description}: "
          f"vitality={entry.summary.mean_final_vitality:.3f}, "
          f"delta={entry.delta_mean_final_vitality:+.3f}")
```

---

## 6. Inspecting experiments via CLI

### 6.1 List all experiments

```
$ axis experiments list
a1b2c3d4...  status=completed  runs=1  completed=1  system=system_a  created=2026-04-07T...
f7e8d9c0...  status=completed  runs=4  completed=4  system=system_a  created=2026-04-07T...
```

### 6.2 Show experiment details

```
$ axis experiments show <experiment-id>
Experiment: a1b2c3d4...
  Status: completed
  Type: single_run
  System: system_a
  Runs: ['run-0000']
  Summary: 1 runs
    run-0000  baseline
```

### 6.3 List runs within an experiment

```
$ axis runs list --experiment <experiment-id>
run-0000  status=completed  system.transition.energy_gain_factor=5.0   summary=yes
run-0001  status=completed  system.transition.energy_gain_factor=10.0  summary=yes
run-0002  status=completed  system.transition.energy_gain_factor=15.0  summary=yes
run-0003  status=completed  system.transition.energy_gain_factor=20.0  summary=yes
```

### 6.4 Show a single run

```
$ axis runs show run-0000 --experiment <experiment-id>
Run: run-0000
  Experiment: a1b2c3d4...
  Status: completed
  Variation: baseline
  Base seed: 42
  Episodes: 5
  Summary: mean_steps=142.6  death_rate=0.20  mean_final_vitality=0.450
```

---

## 7. Resuming failed or interrupted experiments

If an experiment is interrupted (process killed, a run crashes, etc.),
the completed runs remain safely persisted on disk. The `resume` command
picks up where execution left off.

### 7.1 Resume command

```
axis experiments resume <experiment_id>
```

Resume logic:

1. Loads the persisted experiment config from the repository.
2. Re-derives the full run plan.
3. Checks each run: if status is `COMPLETED` and all artifacts are
   valid, the run is skipped.
4. Re-executes any run that is `FAILED`, `RUNNING`, `PENDING`, or has
   missing/incomplete artifacts -- from scratch (entire run, not
   individual episodes).
5. Rebuilds the experiment summary from all runs (both previously
   completed and newly executed).
6. Sets the experiment status to `COMPLETED`.

### 7.2 Example: recovering from a partial OFAT experiment

Suppose an OFAT experiment with 4 runs failed during the third run.
The experiment status on disk will be `partial`:

```
$ axis experiments list
f7e8d9c0...  status=partial  runs=4  completed=2  system=system_a  ...
```

Resume it:

```
$ axis experiments resume f7e8d9c0...
Experiment 'f7e8d9c0...' resumed and completed.
  Runs: 4
```

Only `run-0002` and `run-0003` were re-executed. `run-0000` and
`run-0001` were loaded from disk without re-running.

### 7.3 Idempotent behavior

Resuming an already completed experiment is safe -- it returns the
existing result without re-executing anything:

```
$ axis experiments resume <experiment-id>
Experiment '<experiment-id>' resumed and completed.
  Runs: 1
```

You can call `resume` as many times as you want. Completed runs are
never re-executed.

### 7.4 When resume fails again

If the re-executed run fails again during resume, the experiment status
is updated to `partial` (if some runs completed) or `failed` (if
no runs completed), and the error is reported. Fix the underlying issue
and resume again.

### 7.5 Experiment status reference

| Status      | Meaning |
|-------------|---------|
| `created`   | Experiment directory initialized, no runs started yet |
| `running`   | Execution in progress |
| `completed` | All runs finished successfully |
| `partial`   | Some runs completed, at least one failed |
| `failed`    | No runs completed successfully |

---

## 8. Visualizing episode replays

The `visualize` command launches an interactive viewer that replays
a recorded episode step by step.

```
axis visualize --experiment <eid> --run <rid> --episode <n>
```

| Flag           | Required | Default | Description |
|----------------|----------|---------|-------------|
| `--experiment` | yes      | --      | Experiment ID |
| `--run`        | yes      | --      | Run ID within the experiment |
| `--episode`    | yes      | --      | Episode index (1-based) |
| `--step`       | no       | `0`     | Initial step to display (0-based) |
| `--phase`      | no       | `null`  | Initial phase index |
| `--width-percent` | no    | `null`  | Initial viewer width as a percentage of the primary screen width |

Example:

```bash
# Replay episode 1 from run-0000
axis visualize --experiment a1b2c3d4... --run run-0000 --episode 1

# Start at step 50
axis visualize --experiment a1b2c3d4... --run run-0000 --episode 1 --step 50
```

The viewer loads the persisted episode trace from the repository and
renders the world grid, agent position, and system-specific overlays.
The visualization adapters are resolved automatically based on the
experiment's `system_type` and `world_type`.

Visualization compatibility depends on the experiment's `trace_mode`:

- `full` -- visualizable
- `delta` -- visualizable
- `light` -- not visualizable

If an experiment was executed in `light` mode, AXIS rejects the command
explicitly rather than opening the viewer with incomplete replay data.

> **Note:** The viewer requires a graphical display (Qt). It is not
> available in headless or remote-only environments.

---

## 9. Quick reference

```bash
# Run the shipped baseline experiment
axis experiments run experiments/configs/system-a-baseline.yaml

# Run the OFAT sweep
axis experiments run experiments/configs/system-a-energy-gain-sweep.yaml

# Run the System B SDK demo
axis experiments run experiments/configs/system-b-sdk-demo.yaml

# Run the toroidal world demo
axis experiments run experiments/configs/system-a-toroidal-demo.yaml

# List all experiments
axis experiments list

# Inspect an experiment
axis experiments show <experiment-id>

# List runs
axis runs list --experiment <experiment-id>

# Inspect a run
axis runs show run-0000 --experiment <experiment-id>

# Resume a failed experiment
axis experiments resume <experiment-id>

# Visualize an episode
axis visualize --experiment <experiment-id> --run run-0000 --episode 1

# Compare two episode traces (paired comparison)
axis compare \
  --reference-experiment <ref-id> --reference-run run-0000 --reference-episode 1 \
  --candidate-experiment <cand-id> --candidate-run run-0000 --candidate-episode 1

# Compare full runs with statistical summary
axis compare \
  --reference-experiment <ref-id> --reference-run run-0000 \
  --candidate-experiment <cand-id> --candidate-run run-0000

# Get JSON output (any command)
axis --output json experiments show <experiment-id>

# Use a custom repository directory
axis --root /data/results experiments list

# Reset one workspace's generated artifacts
axis workspaces reset workspaces/my-workspace

# Reset immediately without confirmation
axis workspaces reset workspaces/my-workspace --force

# Preview reset scope and counts as JSON
axis --output json workspaces reset workspaces/my-workspace

# Read raw summary file directly
cat experiments/results/<experiment-id>/runs/run-0000/run_summary.json | python -m json.tool

# Load data in Python
python -c "
from pathlib import Path
from axis.framework.persistence import ExperimentRepository
repo = ExperimentRepository(Path('experiments/results'))
eid = repo.list_experiments()[0]
s = repo.load_run_summary(eid, repo.list_runs(eid)[0])
print(f'vitality={s.mean_final_vitality:.3f}, death_rate={s.death_rate:.2f}')
"
```
