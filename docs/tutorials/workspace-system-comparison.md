# Tutorial: Comparing Two Systems

**AXIS Experimentation Framework v0.2.3**

> **Prerequisites:** AXIS framework installed (`pip install -e .`),
> at least two registered systems (e.g. `system_a` and `system_c`),
> familiarity with the CLI basics.
>
> **Important:** Workspace configs must use `experiment_type: single_run`.
> OFAT and other multi-run experiment types are not supported in
> workspace mode — use `axis experiments run` directly for those.
>
> **What we do:** Create an investigation workspace to compare
> System A (energy-driven forager) against System C (prediction-error-driven)
> on a grid world, then run both, compare, analyze the differences,
> and iterate with a parameter tweak.
>
> **Related:** [Workspace Manual](../manuals/workspace-manual.md) |
> [Investigating a Single System](workspace-single-system.md) |
> [Comparison Manual](../manuals/comparison-manual.md)

---

## What is a System Comparison Investigation?

When you have two different systems -- or two configurations of the
same system -- and want to study how they differ under identical
conditions, a **system_comparison** workspace is the right tool.

The workspace ensures both systems run against the same world with
the same seed, then provides structured comparison with per-episode
metrics and statistical analysis.

In this tutorial we will:

1. Scaffold a comparison workspace
2. Configure both sides
3. Run both experiments
4. Compare and analyze
5. Iterate with a parameter change

---

## Step 1: Scaffold the Workspace

```bash
axis workspaces scaffold
```

Fill in the prompts:

| Prompt | What to enter |
|---|---|
| Workspace ID | `system-a-vs-system-c-grid2d` |
| Title | `System A vs System C on Grid 2D` |
| Parent directory | `workspaces` |
| Class | `investigation` |
| Type | `system_comparison` |
| Question | `How does system_c compare to system_a on grid_2d?` |
| Reference system | `system_a` |
| Candidate system | `system_c` |

The scaffolder creates:

```
workspaces/system-a-vs-system-c-grid2d/
  workspace.yaml
  README.md
  notes.md
  configs/
    reference-system_a.yaml
    candidate-system_c.yaml
  results/
  comparisons/
  measurements/
  exports/
```

Two config files are created -- one per system. Both share identical
world and execution settings so the comparison is fair.

Verify:

```bash
axis workspaces show workspaces/system-a-vs-system-c-grid2d
```

You should see two primary configs, both marked `[OK]`, and the
reference/candidate systems displayed.

---

## Step 2: Configure Both Sides

Open `configs/reference-system_a.yaml` and `configs/candidate-system_c.yaml`.
The scaffolder created identical placeholder configs except for
`system_type`. Review and adjust:

**Shared settings** (must be identical for a fair comparison):

```yaml
general:
  seed: 42             # same seed = same world layout
execution:
  max_steps: 100
world:
  world_type: grid_2d
  grid_width: 10
  grid_height: 10
  obstacle_density: 0.15
  resource_regen_rate: 0.2
num_episodes_per_run: 5
```

**System-specific settings** (these differ between the two configs):

Each config has a `system:` block with parameters appropriate to that
system type. Edit these to set the specific configuration you want to
test.

> **Important:** Use the same `seed`, `max_steps`, world settings, and
> `num_episodes_per_run` in both configs. This ensures differences in
> behavior come from the systems, not the environment.

---

## Step 3: Run Both Experiments

```bash
axis workspaces run workspaces/system-a-vs-system-c-grid2d
```

Both configs are executed sequentially. Each produces its own experiment:

```
Workspace execution completed: 2 experiment(s)
  <experiment-id-1>: 1 run(s)
  <experiment-id-2>: 1 run(s)
```

Check the state:

```bash
axis workspaces show workspaces/system-a-vs-system-c-grid2d
```

Two entries appear under `Primary results`, each annotated with its
config file, role, and timestamp.

---

## Step 4: Compare

```bash
axis workspaces compare workspaces/system-a-vs-system-c-grid2d
```

Since the two experiments have different `system_type` values, the
auto-resolver maps them automatically: `system_a` becomes the
reference, `system_c` becomes the candidate.

```
Workspace comparison #1 completed.
  Output: workspaces/system-a-vs-system-c-grid2d/comparisons/comparison-001.json
```

---

## Step 5: Analyze the Results

```bash
axis workspaces comparison-result workspaces/system-a-vs-system-c-grid2d
```

The output includes:

### Per-episode results

```
Episode 1: mismatch=62.0%, pos_div=3.42, steps=100/87, survivor=reference
Episode 2: mismatch=58.0%, pos_div=2.87, steps=100/100, survivor=equal
...
```

Each episode shows:
- **mismatch** — fraction of timesteps where the two agents chose
  different actions
- **pos_div** — average spatial distance between the agents
- **steps** — how many steps each agent survived (reference/candidate)
- **survivor** — which agent lasted longer

### Statistical summary

The summary aggregates across all episodes:

- **Action mismatch rate** — high values (>50%) indicate fundamentally
  different decision strategies
- **Mean trajectory distance** — how far apart the agents typically are
  on the grid
- **Final vitality delta** — positive means the candidate ended
  healthier on average
- **Survival rates** — what fraction of episodes each agent completed
  without early termination

### Configuration diff

The output ends with the full configurations for both sides. Since both
are embedded in the comparison file, you can always trace exactly what
produced the result.

---

## Step 6: Iterate

Suppose the comparison reveals that System C struggles with survival.
You can tweak its parameters and re-run:

```bash
# Edit configs/candidate-system_c.yaml
# e.g. increase initial_energy or adjust prediction parameters

# Re-run both
axis workspaces run workspaces/system-a-vs-system-c-grid2d

# Re-compare
axis workspaces compare workspaces/system-a-vs-system-c-grid2d
```

After multiple runs, the auto-resolver picks the most recent experiment
for each system type. If you need to compare specific runs:

```bash
axis workspaces compare workspaces/system-a-vs-system-c-grid2d \
  --reference-experiment <eid-1> \
  --candidate-experiment <eid-2>
```

Review all comparisons:

```bash
# List comparisons
axis workspaces comparison-result workspaces/system-a-vs-system-c-grid2d

# View specific comparison
axis workspaces comparison-result workspaces/system-a-vs-system-c-grid2d --number 1
axis workspaces comparison-result workspaces/system-a-vs-system-c-grid2d --number 2
```

---

## Step 7: Visualize

To see the agents in action:

```bash
# Watch the reference system
axis visualize --workspace workspaces/system-a-vs-system-c-grid2d \
  --role reference --episode 1

# Watch the candidate system
axis visualize --workspace workspaces/system-a-vs-system-c-grid2d \
  --role candidate --episode 1
```

This helps build intuition about *why* the metrics differ -- you can
see the actual movement patterns, resource gathering behavior, and
energy curves.

---

## Tips

**Same system, different configs.** System comparison also works when
both sides use the same `system_type` but with different parameters.
In this case, auto-resolution uses manifest ordering (first result =
reference, second = candidate) instead of system type matching.

**Seed consistency.** Always use the same seed for both configs. The
framework generates the same world layout for a given seed, ensuring
the comparison is fair.

**Multiple episodes.** Use `num_episodes_per_run: 5` or more to get
meaningful statistics. A single episode can be misleading due to
random variation.

---

## Summary

| Step | Command |
|---|---|
| Scaffold | `axis workspaces scaffold` |
| Run both | `axis workspaces run <ws>` |
| Compare | `axis workspaces compare <ws>` |
| Inspect | `axis workspaces comparison-result <ws>` |
| Visualize | `axis visualize --workspace <ws> --role reference --episode N` |
| Iterate | edit config, re-run, re-compare |

The comparison workspace keeps both sides locked to the same conditions,
making it easy to attribute differences to the system rather than the
environment.

**Next:** [Investigating a Single System](workspace-single-system.md) |
[Developing a System](workspace-system-development.md)
