# Tutorial: Developing a System with a Workspace

**AXIS Experimentation Framework v0.2.3**

> **Prerequisites:** AXIS framework installed (`pip install -e .`),
> familiarity with the SystemInterface contract
> (see [Building a System](building-a-system.md)), and the CLI basics.
>
> **Important:** Workspace configs must use `experiment_type: single_run`.
> OFAT and other multi-run experiment types are not supported in
> workspace mode — use `axis experiments run` directly for those.
>
> **What we do:** Create a development workspace to build and validate
> a new system. We establish a baseline, implement candidate changes,
> run structured comparisons, and iterate -- all within a single
> workspace that tracks the full development history.
>
> **Related:** [Workspace Manual](../manuals/workspace-manual.md) |
> [Building a System](building-a-system.md) |
> [System Developer Manual](../manuals/system-dev-manual.md)

---

## What is a System Development Workspace?

Building a new system involves many cycles of "change code, run,
compare against baseline, decide what to tweak next." A
**development / system_development** workspace structures this cycle:

- A **baseline config** captures the known-good reference point.
- A **candidate config** captures the parameters you're testing.
- The workspace tracks baseline results, candidate results, and
  comparison history separately.
- `--baseline-only` and `--candidate-only` flags let you run just
  one side.
- The `show` command tells you the current development state and
  which experiments were used in the last comparison.

This tutorial walks through the full development cycle for a system
called `system_d`.

---

## Step 1: Scaffold the Workspace

```bash
axis workspaces scaffold
```

Fill in the prompts:

| Prompt | What to enter |
|---|---|
| Workspace ID | `develop-system-d` |
| Title | `System D Development` |
| Parent directory | `workspaces` |
| Class | `development` |
| Type | `system_development` |
| Development goal | `Implement and validate system_d` |
| Artifact kind | `system` |
| Artifact under development | `system_d` |

The scaffolder creates:

```
workspaces/develop-system-d/
  workspace.yaml
  README.md
  notes.md
  configs/
    baseline-system_d.yaml       # placeholder baseline config
  results/
  comparisons/
  exports/
  concept/                       # for design docs, diagrams
  engineering/                   # for specs, work packages
```

Check the initial state:

```bash
axis workspaces show workspaces/develop-system-d
```

```
Development state: pre-candidate
Baseline config: configs/baseline-system_d.yaml
```

The workspace starts in **pre-candidate** state -- only a baseline
exists, no candidate yet.

---

## Step 2: Configure the Baseline

The scaffolder writes a placeholder config based on `system_a`. Since
you're developing a new system, edit `configs/baseline-system_d.yaml`
to match your system's config structure:

```yaml
system_type: system_d
experiment_type: single_run
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
  # your system's parameters here
  initial_energy: 80.0
  max_energy: 100.0
  learning_rate: 0.1
num_episodes_per_run: 5
```

> **Note:** Make sure `system_d` is registered in `axis-plugins.yaml`
> and has a working `register()` function before running.

---

## Step 3: Run the Baseline

```bash
axis workspaces run workspaces/develop-system-d
```

In pre-candidate state, this runs only the baseline config. Output:

```
Workspace execution completed: 1 experiment(s)
  <experiment-id>: 1 run(s)
```

Check the state:

```bash
axis workspaces show workspaces/develop-system-d
```

```
Development state: pre-candidate
Baseline results: 1/1 present
  [OK] results/<experiment-id>/runs/run-0000
```

The baseline is established. You can also run explicitly with
`--baseline-only` for clarity:

```bash
axis workspaces run workspaces/develop-system-d --baseline-only
```

---

## Step 4: Create the Candidate

Now implement your changes to `system_d` -- new decision logic, tuned
parameters, different components. Create a candidate config that
exercises the new behavior:

```bash
cp workspaces/develop-system-d/configs/baseline-system_d.yaml \
   workspaces/develop-system-d/configs/candidate-system_d.yaml
```

Edit `configs/candidate-system_d.yaml` with the changed parameters:

```yaml
system:
  initial_energy: 80.0
  max_energy: 100.0
  learning_rate: 0.05    # changed from 0.1
```

Register the candidate with the workspace:

```bash
axis workspaces set-candidate workspaces/develop-system-d \
  configs/candidate-system_d.yaml
```

```
Candidate config set: configs/candidate-system_d.yaml
```

Check the state:

```bash
axis workspaces show workspaces/develop-system-d
```

```
Development state: post-candidate
Baseline config: configs/baseline-system_d.yaml
Candidate config: configs/candidate-system_d.yaml
```

The workspace is now in **post-candidate** state.

---

## Step 5: Run the Candidate

```bash
axis workspaces run workspaces/develop-system-d --candidate-only
```

This runs only the candidate config. The result is tracked in
`candidate_results` and `current_candidate_result`:

```bash
axis workspaces show workspaces/develop-system-d
```

```
Candidate results: 1/1 present
  [OK] results/<candidate-eid>/runs/run-0000
Current candidate result: [OK] results/<candidate-eid>/runs/run-0000
```

> **Tip:** You can also run both at once with `axis workspaces run`
> (no flag). This is useful after modifying the baseline config too.

---

## Step 6: Compare Baseline vs Candidate

```bash
axis workspaces compare workspaces/develop-system-d
```

The system automatically uses the latest baseline result as the
reference and `current_candidate_result` as the candidate:

```
Workspace comparison #1 completed.
  Output: workspaces/develop-system-d/comparisons/comparison-001.json
```

---

## Step 7: Analyze

```bash
axis workspaces comparison-summary workspaces/develop-system-d
```

Review the metrics to evaluate your changes:

- **Action mismatch rate** -- how much the candidate's decisions
  differ from baseline. If your change was small, expect a low rate.
- **Final vitality delta** -- positive means the candidate ends
  healthier. This tells you whether your change improved survival.
- **Survival rates** -- check that your changes didn't break the
  agent's ability to survive.

The `show` command now displays which experiments were compared:

```bash
axis workspaces show workspaces/develop-system-d
```

```
Current validation comparison: [OK] comparisons/comparison-001.json
  Reference used: <baseline-eid>
  Candidate used: <candidate-eid>
```

This makes it easy to trace which baseline was used for the comparison,
especially after multiple iterations.

---

## Step 8: Iterate

The development cycle is: **modify candidate -> run -> compare -> analyze -> repeat**.

### Tweak the candidate

Edit `configs/candidate-system_d.yaml`:

```yaml
system:
  learning_rate: 0.02    # further reduced
```

### Re-run and re-compare

```bash
axis workspaces run workspaces/develop-system-d --candidate-only
axis workspaces compare workspaces/develop-system-d
```

Comparison #2 is created. The reference automatically points to the
latest baseline, and the candidate points to the new run.

### Review iteration history

```bash
# Compare results across iterations
axis workspaces comparison-summary workspaces/develop-system-d --number 1
axis workspaces comparison-summary workspaces/develop-system-d --number 2
```

Each comparison file embeds the full configs, so you can trace exactly
which parameter values produced which metrics.

### Re-baseline when needed

If your candidate proves better and you want to adopt it as the new
baseline, update the baseline config and re-run:

```bash
axis workspaces run workspaces/develop-system-d --baseline-only
```

The new baseline result is appended to `baseline_results`. Future
comparisons will use it as the reference.

---

## Step 9: Use the Development Directories

The workspace includes two directories for non-code artifacts:

### `concept/`

Use this for conceptual modeling before and during implementation:

- Design documents describing the system's intended behavior
- Diagrams of the decision pipeline
- Mathematical formulations of drives or policies
- Notes on biological or theoretical inspiration

### `engineering/`

Use this for engineering planning:

- Work package breakdowns
- Component interface sketches
- Test plans
- Integration checklists

These directories are validated by `axis workspaces check` -- a warning
is raised if they're missing from a development workspace.

---

## Step 10: Validate and Wrap Up

```bash
axis workspaces check workspaces/develop-system-d
```

The checker verifies:

- All required directories exist (`concept/`, `engineering/`)
- Declared configs exist on disk
- Baseline and candidate config paths are valid
- Development state is consistent

When development is complete, close the workspace explicitly:

```bash
axis workspaces close workspaces/develop-system-d
```

This finalizes the workflow state by setting:

```yaml
status: closed
lifecycle_stage: final
```

---

## The Development Workflow at a Glance

```
scaffold
  |
  v
configure baseline --> run baseline --> [baseline established]
                                            |
                                            v
                            create candidate config
                                            |
                                            v
                            set-candidate --> run candidate
                                            |
                                            v
                                         compare
                                            |
                                            v
                                         analyze
                                           / \
                                  good?  /   \ not yet
                                        v     v
                                    done    tweak candidate
                                              |
                                              v
                                     run candidate --> compare --> analyze
                                              ^                      |
                                              |______________________|
```

---

## Summary

| Step | Command |
|---|---|
| Scaffold | `axis workspaces scaffold` |
| Run baseline | `axis workspaces run <ws>` or `--baseline-only` |
| Create candidate | copy config, edit, then `axis workspaces set-candidate <ws> <config>` |
| Run candidate | `axis workspaces run <ws> --candidate-only` |
| Compare | `axis workspaces compare <ws>` |
| Inspect | `axis workspaces comparison-summary <ws>` |
| Show state | `axis workspaces show <ws>` |
| Validate | `axis workspaces check <ws>` |
| Iterate | edit candidate, `--candidate-only`, compare, repeat |

The development workspace gives you a structured loop for building and
validating systems. Every run and comparison is preserved, so you have
a complete history of the development process.

**Next:** [Investigating a Single System](workspace-single-system.md) |
[Comparing Two Systems](workspace-system-comparison.md)
