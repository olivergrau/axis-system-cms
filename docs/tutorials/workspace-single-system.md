# Tutorial: Investigating a Single System

**AXIS Experimentation Framework v0.2.3**

> **Prerequisites:** AXIS framework installed (`pip install -e .`),
> at least one registered system (e.g. `system_a`), familiarity with
> the CLI basics (`axis experiments run`).
>
> **What we do:** Create an investigation workspace to study how
> changing `consume_weight` affects System A's survival behavior,
> then run a baseline, modify the parameter, run again, compare,
> and analyze the results. This tutorial uses `experiment_type: single_run`
> configs for point-by-point comparison. For parameter sweeps using
> OFAT configs, see [OFAT Parameter Sweep in a Workspace](workspace-ofat-sweep.md).
>
> **Related:** [Workspace Manual](../manuals/workspace-manual.md) |
> [CLI Manual](../manuals/cli-manual.md) |
> [Comparison Manual](../manuals/comparison-manual.md)

---

## What is a Single System Investigation?

Sometimes you want to understand how a single parameter change affects
an agent's behavior. Rather than juggling loose config files and
experiment IDs, an **investigation / single_system** workspace gives
you a structured container: one directory with configs, results,
comparisons, and notes, all tied together by a manifest.

In this tutorial we will:

1. Scaffold a workspace
2. Run the baseline configuration
3. Modify a parameter and run again
4. Compare the two runs
5. Inspect the comparison results

---

## Step 1: Scaffold the Workspace

```bash
axis workspaces scaffold
```

The interactive prompt will ask for:

| Prompt | What to enter |
|---|---|
| Workspace ID | `system-a-consume-weight` |
| Title | `Consume Weight Investigation` |
| Parent directory | `workspaces` (or your preferred location) |
| Class | `investigation` |
| Type | `single_system` |
| Question | `How does consume_weight affect system_a survival?` |
| System under test | `system_a` |

The scaffolder creates the workspace directory with this structure:

```
workspaces/system-a-consume-weight/
  workspace.yaml
  README.md
  notes.md
  configs/
    system_a-baseline.yaml          # baseline config
  results/
  comparisons/
  measurements/
  exports/
```

Verify with:

```bash
axis workspaces show workspaces/system-a-consume-weight
```

You should see the workspace identity, one primary config marked `[OK]`,
no results yet, and `Validation: VALID`.

---

## Step 2: Configure and Run the Baseline

Open `configs/system_a-baseline.yaml`. The scaffolder created a
placeholder config. Review the key parameters:

```yaml
system_type: system_a
execution:
  max_steps: 100
system:
  policy:
    consume_weight: 2.5     # <-- the parameter we'll investigate
    temperature: 1.0
  agent:
    initial_energy: 50.0
    max_energy: 100.0
num_episodes_per_run: 3
```

This is our baseline: `consume_weight = 2.5`. Run it:

```bash
axis workspaces run workspaces/system-a-consume-weight
```

Output:

```
Workspace execution completed: 1 experiment(s)
  <experiment-id>: 1 run(s)
```

Check the workspace state:

```bash
axis workspaces show workspaces/system-a-consume-weight
```

You should see one entry under `Primary results` with the config path,
role, and timestamp annotated.

---

## Step 3: Modify the Parameter and Run Again

Now change `consume_weight` to explore a different value. Edit
`configs/system_a-baseline.yaml`:

```yaml
system:
  policy:
    consume_weight: 5.0     # doubled from baseline
```

Run again:

```bash
axis workspaces run workspaces/system-a-consume-weight
```

A second experiment is created with its own ID. The manifest now lists
two entries under `primary_results` -- one for each run.

```bash
axis workspaces show workspaces/system-a-consume-weight
```

Both results appear with their respective config snapshots and timestamps.

---

## Step 4: Compare

```bash
axis workspaces compare workspaces/system-a-consume-weight
```

The system auto-resolves which experiments to compare: the first recorded
result becomes the **reference** (our baseline with `consume_weight=2.5`),
and the most recent becomes the **candidate** (our modified
`consume_weight=5.0`).

Output:

```
Workspace comparison #1 completed.
  Output: workspaces/system-a-consume-weight/comparisons/comparison-001.json
```

> **Tip:** If you've run more than two experiments and need to compare
> specific ones, use explicit IDs:
>
> ```bash
> axis workspaces compare workspaces/system-a-consume-weight \
>   --reference-experiment <baseline-eid> \
>   --candidate-experiment <modified-eid>
> ```

---

## Step 5: Analyze the Results

```bash
axis workspaces comparison-result workspaces/system-a-consume-weight
```

This displays the full comparison report:

- **Per-episode results** — action mismatch rate, position divergence,
  step counts, and which agent survived longer in each episode.
- **Statistical summary** — aggregated metrics across all episodes with
  mean, standard deviation, min, and max.
- **Configurations** — the exact config values used for both sides,
  so you can confirm what parameter differed.

Look for the key metrics:

- **Action mismatch rate** — how often the two agents chose different
  actions. A high rate means the parameter change significantly altered
  decision-making.
- **Final vitality delta** — positive means the candidate ended
  healthier, negative means the reference did.
- **Survival rates** — whether one configuration leads to more
  early terminations.

---

## Step 6: Iterate

Want to try another value? Edit the config again:

```yaml
system:
  policy:
    consume_weight: 1.0     # much lower than baseline
```

Run and compare:

```bash
axis workspaces run workspaces/system-a-consume-weight
axis workspaces compare workspaces/system-a-consume-weight \
  --reference-experiment <baseline-eid> \
  --candidate-experiment <latest-eid>
```

Each comparison is preserved as a separate numbered file. Review any
comparison by number:

```bash
axis workspaces comparison-result workspaces/system-a-consume-weight --number 1
axis workspaces comparison-result workspaces/system-a-consume-weight --number 2
```

Since each comparison file stores complete config copies, you can always
trace exactly which parameter values produced which results -- even weeks
later.

---

## Step 7: Validate and Document

Validate the workspace is consistent:

```bash
axis workspaces check workspaces/system-a-consume-weight
```

Record your findings in `notes.md`:

```markdown
## Findings

- consume_weight=2.5 (baseline): moderate survival, balanced behavior
- consume_weight=5.0: aggressive consumption, higher final vitality
- consume_weight=1.0: rarely consumes, lower survival rate

## Conclusion

consume_weight has a strong effect on survival strategy. Values above 3.0
shift the agent toward active foraging.
```

---

## Summary

| Step | Command |
|---|---|
| Scaffold | `axis workspaces scaffold` |
| Run baseline | `axis workspaces run <ws>` |
| Modify config, run again | edit config, then `axis workspaces run <ws>` |
| Compare | `axis workspaces compare <ws>` |
| Inspect results | `axis workspaces comparison-result <ws>` |
| Validate | `axis workspaces check <ws>` |

The workspace keeps everything together: configs, results, comparisons,
and notes. Every comparison embeds the full config snapshot, so results
are always reproducible and traceable.

**Next:** [OFAT Parameter Sweep in a Workspace](workspace-ofat-sweep.md) |
[Comparing Two Systems](workspace-system-comparison.md) |
[Developing a System](workspace-system-development.md)
