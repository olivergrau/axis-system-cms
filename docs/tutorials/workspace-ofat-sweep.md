# Tutorial: OFAT Parameter Sweep in a Workspace

**AXIS Experimentation Framework v0.2.3**

> **Prerequisites:** AXIS framework installed (`pip install -e .`),
> at least one registered system (e.g. `system_a`), familiarity with
> the CLI basics (`axis experiments run`) and the
> [single system investigation tutorial](workspace-single-system.md).
>
> **What we do:** Use an `investigation / single_system` workspace to
> run an OFAT (one-factor-at-a-time) parameter sweep, inspect the
> sweep results, and combine sweep and point outputs in the same
> workspace.
>
> **Related:** [Workspace Manual](../manuals/workspace-manual.md) |
> [Configuration Reference](../manuals/config-manual.md) |
> [Single System Tutorial](workspace-single-system.md)

---

## When to Use OFAT in a Workspace

The [single system tutorial](workspace-single-system.md) shows a
**manual iteration** workflow: change one parameter, run, compare, repeat.
This works well when you want to explore interactively and compare
specific pairs of runs.

An **OFAT sweep** is better when you want to systematically vary a
single parameter across multiple values in one shot. Instead of manually
editing and re-running, you define all values up front and get one run
per value, each with its own independent seed. The framework then
computes deltas relative to a baseline run automatically.

OFAT is supported only in `investigation / single_system` workspaces.
It is **not** available for `system_comparison` or `system_development`.

---

## Step 1: Scaffold the Workspace

```bash
axis workspaces scaffold
```

| Prompt | What to enter |
|---|---|
| Workspace ID | `system-a-energy-gain-sweep` |
| Title | `Energy Gain Factor Sweep` |
| Parent directory | `workspaces` |
| Class | `investigation` |
| Type | `single_system` |
| Question | `How does energy_gain_factor affect system_a survival?` |
| System under test | `system_a` |

The scaffolder creates a baseline config:

```
workspaces/system-a-energy-gain-sweep/
  workspace.yaml
  README.md
  notes.md
  configs/
    system_a-baseline.yaml          # single_run baseline (declared as primary)
  results/
  comparisons/
  measurements/
  exports/
```

Only `system_a-baseline.yaml` is listed in `primary_configs`. To run an
OFAT sweep, you will create a sweep config manually (see Step 3).

---

## Step 2: Run the Baseline First (Optional but Recommended)

Before sweeping, establish a baseline point output for later comparison:

```bash
axis workspaces run workspaces/system-a-energy-gain-sweep
```

This runs the `single_run` baseline config. The result is a **point**
output recorded in `primary_results`. You can compare this baseline
against future point runs using `axis workspaces compare`.

---

## Step 3: Create the OFAT Sweep Config

Create a new sweep config file in `configs/`. You can copy the baseline
and modify it, or write one from scratch. The key additions are
`experiment_type: ofat`, `parameter_path`, and `parameter_values`:

```bash
cp workspaces/system-a-energy-gain-sweep/configs/system_a-baseline.yaml \
   workspaces/system-a-energy-gain-sweep/configs/system_a-sweep.yaml
```

Edit `configs/system_a-sweep.yaml` to make it an OFAT config:

```yaml
system_type: system_a
experiment_type: ofat
parameter_path: system.transition.energy_gain_factor
parameter_values:
  - 5.0
  - 10.0
  - 15.0
  - 20.0
general:
  seed: 42
execution:
  max_steps: 100
logging:
  console_enabled: false
world:
  world_type: grid_2d
  grid_width: 10
  grid_height: 10
  obstacle_density: 0.15
  resource_regen_rate: 0.2
system:
  agent:
    initial_energy: 50.0
    max_energy: 100.0
    buffer_capacity: 25
  policy:
    selection_mode: sample
    temperature: 1.0
    stay_suppression: 0.1
    consume_weight: 2.5
  transition:
    move_cost: 1.0
    consume_cost: 1.0
    stay_cost: 0.5
    max_consume: 1.0
    energy_gain_factor: 10.0
num_episodes_per_run: 3
```

The two key fields that make this an OFAT config:

- **`parameter_path`** — the dot-separated path to the parameter being
  varied. Must be a valid path into either the `system` or `framework`
  section of the config. Here we sweep `energy_gain_factor` inside
  the system's transition settings.
- **`parameter_values`** — the list of values to try. Each value
  produces one run. The first run uses the baseline config as-is
  (acting as the "baseline" of the sweep).

Customize the parameter sweep to match your investigation. For example,
to sweep `system.policy.temperature` instead:

```yaml
parameter_path: system.policy.temperature
parameter_values:
  - 0.5
  - 1.0
  - 2.0
  - 5.0
```

---

## Step 4: Declare the Sweep Config and Run

Add the sweep config to `primary_configs` in `workspace.yaml`:

```yaml
primary_configs:
  - configs/system_a-baseline.yaml
  - configs/system_a-sweep.yaml
```

Then run the workspace:

```bash
axis workspaces run workspaces/system-a-energy-gain-sweep
```

Output:

```
Workspace execution completed: 2 experiment(s)
  <baseline-eid>: 1 run(s)
  <sweep-eid>: 4 run(s)
```

The sweep creates one run per parameter value (4 values = 4 runs).
Each run uses an independent seed derived from the base seed.

> **Note:** If you already ran the baseline in Step 2, the framework
> creates a new baseline experiment alongside the sweep. Each
> `axis workspaces run` invocation executes all declared primary configs.

Check the workspace state:

```bash
axis workspaces show workspaces/system-a-energy-gain-sweep
```

You should see entries under `Primary results` with both `point` and
`sweep` output forms annotated.

---

## Step 5: Inspect Sweep Results

```bash
axis workspaces sweep-result workspaces/system-a-energy-gain-sweep
```

This displays the sweep output in a structured format:

```
Sweep experiment: <sweep-eid>
  Parameter: system.transition.energy_gain_factor
  Baseline run: run-0000 (energy_gain_factor=5.0)

  Run       | Value  | Mean Steps | Death Rate | Mean Final Vitality
  ----------|--------|------------|------------|--------------------
  run-0000  | 5.0    | 45.3       | 0.67       | 0.12
  run-0001  | 10.0   | 68.7       | 0.33       | 0.35
  run-0002  | 15.0   | 82.1       | 0.00       | 0.52
  run-0003  | 20.0   | 91.4       | 0.00       | 0.68

  Deltas (relative to baseline):
  run-0001  | +23.4 steps | -0.34 death rate | +0.23 vitality
  run-0002  | +36.8 steps | -0.67 death rate | +0.40 vitality
  run-0003  | +46.1 steps | -0.67 death rate | +0.56 vitality
```

The deltas show how each parameter value changes behavior relative to
the baseline run (the first value in the sweep).

For machine-readable output:

```bash
axis workspaces sweep-result workspaces/system-a-energy-gain-sweep --output json
```

If the workspace contains multiple sweep experiments, select one explicitly:

```bash
axis workspaces sweep-result workspaces/system-a-energy-gain-sweep \
  --experiment <sweep-eid>
```

---

## Step 6: Visualize a Specific Sweep Run

Sweep experiments contain multiple runs. To visualize one, you must
specify the run explicitly with `--run`:

```bash
axis visualize --workspace workspaces/system-a-energy-gain-sweep \
  --experiment <sweep-eid> --run run-0002 --episode 1
```

Without `--run`, the visualization command will error and tell you to
provide one. Use the sweep-result output from Step 5 to identify which
run IDs correspond to which parameter values.

---

## Step 7: Combine Point and Sweep Workflows

A `single_system` workspace can contain both point and sweep outputs.
They serve complementary purposes:

- **Point outputs** are used for workspace comparison (`axis workspaces compare`).
  The comparison system auto-resolves point outputs only.
- **Sweep outputs** are used for parameter exploration
  (`axis workspaces sweep-result`). They are excluded from comparison
  auto-resolution.

A typical combined workflow:

```bash
# 1. Run the baseline (point output)
axis workspaces run workspaces/my-workspace

# 2. Edit the config to change a parameter, run again (point output)
axis workspaces run workspaces/my-workspace

# 3. Compare the two point runs
axis workspaces compare workspaces/my-workspace

# 4. Now run an OFAT sweep to explore a wider range
# (add sweep config to primary_configs, then run)
axis workspaces run workspaces/my-workspace

# 5. Inspect sweep results
axis workspaces sweep-result workspaces/my-workspace

# 6. The sweep does not affect comparison — you can still compare
#    point runs without interference
axis workspaces compare workspaces/my-workspace
```

---

## Understanding the Distinction: Point vs Sweep

| Aspect | Point (`single_run`) | Sweep (`ofat`) |
|---|---|---|
| Runs per experiment | 1 | N (one per parameter value) |
| Output form | `point` | `sweep` |
| Used in workspace compare | Yes (auto-resolved) | No |
| Inspected with | `comparison-result` | `sweep-result` |
| Visualization | Automatic run selection | Requires `--run` flag |
| Result entry fields | `primary_run_id` | `baseline_run_id` |

Both types are tracked in `primary_results` with their `output_form`
annotated, so the workspace always knows what it contains.

---

## Summary

| Step | Command |
|---|---|
| Scaffold | `axis workspaces scaffold` (choose single_system) |
| Run baseline | `axis workspaces run <ws>` |
| Configure sweep | Create OFAT config in `configs/`, set `parameter_path` and `parameter_values` |
| Declare sweep config | Add to `primary_configs` in `workspace.yaml` |
| Run sweep | `axis workspaces run <ws>` |
| Inspect sweep | `axis workspaces sweep-result <ws>` |
| Visualize a run | `axis visualize --workspace <ws> --experiment <eid> --run <rid> --episode N` |
| Compare point runs | `axis workspaces compare <ws>` (sweep excluded) |

OFAT in a workspace gives you the structured, repeatable environment of
a workspace combined with the systematic parameter exploration of OFAT.
Sweep outputs sit alongside point outputs without interfering with the
comparison workflow.

**Previous:** [Investigating a Single System](workspace-single-system.md) |
**Next:** [Comparing Two Systems](workspace-system-comparison.md) |
[Developing a System](workspace-system-development.md)
