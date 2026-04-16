# AXIS Paired Trace Comparison -- User Manual (v0.4.0)

> **Related manuals:**
> [CLI Manual](cli-manual.md) |
> [Configuration Reference](config-manual.md) |
> [Visualization Manual](visualization-manual.md) |
> [System Developer Manual](system-dev-manual.md)

## Overview

The paired trace comparison tool answers a single question: **"What
changed when one system was replaced by another?"**

It takes two episode traces -- a *reference* (baseline) and a
*candidate* (modified system) -- that ran under identical world
conditions (same seed, grid, starting position), and produces a
structured comparison covering validation, alignment, action and
trajectory divergence, outcome differences, and system-specific
prediction analysis.

The comparison is available as:

- A CLI command: `axis compare`
- A Python function: `compare_episode_traces()`
- JSON output for scripting and notebooks

> **Note:** The comparison operates on persisted episode traces after
> execution. It is a pure analysis layer -- it does not re-run
> episodes or modify any artifacts.

---

## 1. Concepts

### 1.1 Reference and candidate

The comparison is **asymmetric**. The two traces have distinct roles:

| Role        | Meaning |
|-------------|---------|
| **Reference** | The baseline trace. Typically the simpler or older system (e.g. System A). |
| **Candidate** | The modified trace. The system under evaluation (e.g. System C). |

This asymmetry matters for signed metrics: a positive vitality delta
means the candidate was healthier; a positive step delta means the
candidate survived longer.

### 1.2 Pairing constraints

Two episodes form a valid pair when they share the same experimental
conditions. The comparison validates these constraints before computing
any metrics. All four must hold:

| Constraint        | What is checked |
|-------------------|-----------------|
| World type        | Both episodes use the same `world_type` (e.g. `"grid_2d"`) |
| World config      | Both episodes use identical world configuration (grid size, obstacles, regen rate, etc.) |
| Start position    | The agent started at the same grid cell in both episodes |
| Episode seed      | Both episodes were generated from the same random seed |

If any constraint is violated, the comparison returns a structured
validation failure with specific error codes -- it never silently
proceeds with mismatched data.

### 1.3 Seed pairing

Episode seeds ensure that the world layout and resource placement are
identical across the two traces. The tool supports **derived seed
pairing**: the episode seed is computed as `base_seed + episode_index`,
where `base_seed` comes from the run configuration.

For example, if both runs use `base_seed: 42` and you compare
`--reference-episode 1` with `--candidate-episode 1`, the derived seed
is `42 + 1 = 43`. The tool verifies this match automatically when run
configs are available.

### 1.4 Shared-prefix alignment

When two episodes have different lengths (e.g. the reference died at
step 163 but the candidate survived to step 200), the comparison aligns
them using a shared prefix: only the first `min(n_ref, n_cand)` steps
are compared side by side. The remaining steps of the longer episode
are captured separately in the outcome comparison.

There is no padding or extrapolation -- the tool never invents data for
steps that did not occur.

### 1.5 Comparison modes

The comparison tool supports two modes:

| Mode | Scope | CLI syntax |
|------|-------|------------|
| **Episode** | Compare a single pair of episodes | `axis compare --reference-episode N --candidate-episode N ...` |
| **Run** | Compare all matched episodes across two runs, with statistical summary | `axis compare ...` (omit `--*-episode` flags) |

In run mode, episodes are paired by index (1, 2, ..., min(n_ref, n_cand)).
Each pair is validated independently -- if one episode fails validation
(e.g. due to a seed mismatch), it is counted as invalid but the other
pairs still proceed. The run-level result includes both the individual
per-episode comparisons and an aggregate statistical summary.

---

## 2. CLI usage

### 2.1 Command syntax

**Single episode:**

```
axis compare \
  --reference-experiment <eid> --reference-run <rid> --reference-episode <n> \
  --candidate-experiment <eid> --candidate-run <rid> --candidate-episode <n> \
  [--output text|json] [--root <path>]
```

**Full run (all episodes):**

```
axis compare \
  --reference-experiment <eid> --reference-run <rid> \
  --candidate-experiment <eid> --candidate-run <rid> \
  [--output text|json] [--root <path>]
```

| Flag                       | Required | Description |
|----------------------------|----------|-------------|
| `--reference-experiment`   | yes      | Experiment ID for the reference trace |
| `--reference-run`          | yes      | Run ID within the reference experiment |
| `--reference-episode`      | no       | Episode index (omit for full-run comparison) |
| `--candidate-experiment`   | yes      | Experiment ID for the candidate trace |
| `--candidate-run`          | yes      | Run ID within the candidate experiment |
| `--candidate-episode`      | no       | Episode index (omit for full-run comparison) |
| `--output`                 | no       | `text` (default) or `json` |
| `--root`                   | no       | Repository root (default: `./experiments/results`) |

> **Note:** `--reference-episode` and `--candidate-episode` must both be
> provided (single-episode mode) or both omitted (run-level mode).
> Providing only one is an error.

### 2.2 Example: comparing System A vs System C

First, identify your experiment IDs:

```
$ axis experiments list
ed3efb3e...  status=completed  runs=1  completed=1  system=system_a  ...
46fb8c97...  status=completed  runs=1  completed=1  system=system_c  ...
```

Compare episode 1 from each:

```
$ axis compare \
    --reference-experiment ed3efb3e... --reference-run run-0000 --reference-episode 1 \
    --candidate-experiment 46fb8c97... --candidate-run run-0000 --candidate-episode 1
```

Output:

```
Comparison: comparison_succeeded
  Reference: system_a run=run-0000
  Candidate: system_c run=run-0000
  Alignment: 163 aligned steps (ref=163, cand=200)
  Action divergence: first=105, mismatch=32 (19.6%)
  Position divergence: mean=2.34, max=13
  Vitality divergence: mean=0.0478, max=0.3900
  Outcome: ref=163 steps (energy_depleted), cand=200 steps (max_steps_reached)
  Vitality delta: +0.4450, longer survivor: candidate
  Extension [system_c_prediction]:
    prediction_active_step_count: 130
    prediction_active_step_rate: 0.7975
    top_action_changed_by_modulation_count: 3
    top_action_changed_by_modulation_rate: 0.0184
    ambiguous_top_action_count: 0
    mean_modulation_delta: 0.0057
```

### 2.3 Example: full-run comparison

Omit the episode flags to compare all episodes at once:

```
$ axis compare \
    --reference-experiment ed3efb3e... --reference-run run-0000 \
    --candidate-experiment 46fb8c97... --candidate-run run-0000
```

Output:

```
Run Comparison: system_a vs system_c
  Reference: experiment=ed3efb3e... run=run-0000
  Candidate: experiment=46fb8c97... run=run-0000
  Episodes: 5 compared, 5 valid, 0 invalid

  --- Per-episode results ---
  Episode 1: mismatch=19.6%, pos_div=2.34, steps=163/200, survivor=candidate
  Episode 2: mismatch=0.0%, pos_div=0.00, steps=108/108, survivor=equal
  Episode 3: mismatch=2.4%, pos_div=0.05, steps=125/124, survivor=reference
  Episode 4: mismatch=13.0%, pos_div=0.73, steps=146/200, survivor=candidate
  Episode 5: mismatch=16.0%, pos_div=1.72, steps=200/200, survivor=equal

  --- Statistical summary ---
  Action mismatch rate: mean=0.1021, std=0.0859, min=0.0000, max=0.1963 (n=5)
  Mean trajectory distance: mean=0.9690, std=1.0363, min=0.0000, max=2.3436 (n=5)
  Mean vitality difference: mean=0.0391, std=0.0369, min=0.0000, max=0.0790 (n=5)
  Final vitality delta: mean=+0.0790, std=0.2093, min=-0.0850, max=+0.4450 (n=5)
  Total steps delta: mean=+18.0000, std=25.8167, min=-1.0000, max=+54.0000 (n=5)
  Survival rates: reference=20%, candidate=60%
  Longer survivor: candidate=2, reference=1, equal=2
```

The per-episode table gives a quick overview. The statistical summary
aggregates across all valid pairs, showing mean, standard deviation,
minimum, and maximum for each metric.

### 2.4 JSON output

Use `--output json` for machine-readable output:

```bash
axis compare \
    --reference-experiment ed3efb3e... --reference-run run-0000 --reference-episode 1 \
    --candidate-experiment 46fb8c97... --candidate-run run-0000 --candidate-episode 1 \
    --output json
```

The JSON output contains the full `PairedTraceComparisonResult` model
(see section 5 for the complete schema). Pipe it to `jq` for analysis:

```bash
# Extract just the outcome
axis compare ... --output json | jq '.outcome'

# Get the action mismatch rate
axis compare ... --output json | jq '.metrics.action_divergence.action_mismatch_rate'
```

### 2.5 Validation failures

When pairing constraints are violated, the comparison reports the
failure and stops:

```
$ axis compare \
    --reference-experiment ed3efb3e... --reference-run run-0000 --reference-episode 1 \
    --candidate-experiment 46fb8c97... --candidate-run run-0000 --candidate-episode 3
Comparison: comparison_failed_validation
  Reference: system_a run=run-0000
  Candidate: system_c run=run-0000
  Validation FAILED: episode_seed_mismatch
```

Possible validation error codes:

| Error code                   | Meaning |
|------------------------------|---------|
| `world_type_mismatch`        | Different world types (e.g. `grid_2d` vs `toroidal`) |
| `world_config_mismatch`      | Different world settings (grid size, obstacle density, etc.) |
| `start_position_mismatch`    | Agent started at different positions |
| `episode_seed_mismatch`      | Episodes were seeded differently |
| `action_space_no_shared_labels` | No actions in common between the two systems |

---

## 3. Python API

### 3.1 Basic usage

```python
from axis.framework.comparison import compare_episode_traces
from axis.framework.persistence import ExperimentRepository
from pathlib import Path

repo = ExperimentRepository(Path("experiments/results"))

ref_trace = repo.load_episode_trace("ed3efb3e...", "run-0000", 1)
cand_trace = repo.load_episode_trace("46fb8c97...", "run-0000", 1)

ref_config = repo.load_run_config("ed3efb3e...", "run-0000")
cand_config = repo.load_run_config("46fb8c97...", "run-0000")

result = compare_episode_traces(
    ref_trace,
    cand_trace,
    reference_run_config=ref_config,
    candidate_run_config=cand_config,
    reference_episode_index=1,
    candidate_episode_index=1,
)
```

### 3.2 Function signature

```python
def compare_episode_traces(
    reference_trace: BaseEpisodeTrace,
    candidate_trace: BaseEpisodeTrace,
    *,
    reference_run_config: RunConfig | None = None,
    candidate_run_config: RunConfig | None = None,
    reference_run_metadata: RunMetadata | None = None,
    candidate_run_metadata: RunMetadata | None = None,
    reference_episode_index: int | None = None,
    candidate_episode_index: int | None = None,
) -> PairedTraceComparisonResult
```

The two traces are required. All keyword arguments are optional but
recommended -- they enable seed validation and populate the identity
block of the result.

### 3.3 Checking the result

```python
from axis.framework.comparison.types import ResultMode

if result.result_mode == ResultMode.COMPARISON_SUCCEEDED:
    print(f"Mismatch rate: {result.metrics.action_divergence.action_mismatch_rate:.1%}")
    print(f"Longer survivor: {result.outcome.longer_survivor}")
else:
    print(f"Validation failed: {result.validation.errors}")
```

### 3.4 Serialization

The result is a frozen Pydantic model. Serialize to JSON:

```python
import json

data = result.model_dump(mode="json")
print(json.dumps(data, indent=2))

# Restore from JSON
from axis.framework.comparison.types import PairedTraceComparisonResult
restored = PairedTraceComparisonResult.model_validate(data)
```

### 3.5 Run-level comparison

For comparing all episodes at once, use `compare_runs()`:

```python
from axis.framework.comparison import compare_runs
from axis.framework.persistence import ExperimentRepository
from pathlib import Path

repo = ExperimentRepository(Path("experiments/results"))

result = compare_runs(
    repo,
    reference_experiment_id="ed3efb3e...",
    reference_run_id="run-0000",
    candidate_experiment_id="46fb8c97...",
    candidate_run_id="run-0000",
)

s = result.summary
print(f"Valid pairs: {s.num_valid_pairs}/{s.num_episodes_compared}")
print(f"Mismatch rate: {s.action_mismatch_rate.mean:.1%} +/- {s.action_mismatch_rate.std:.1%}")
print(f"Survival: ref={s.reference_survival_rate:.0%}, cand={s.candidate_survival_rate:.0%}")
print(f"Vitality delta: {s.final_vitality_delta.mean:+.3f}")

# Access individual episode results
for r in result.episode_results:
    ep = r.identity.reference_episode_index
    if r.metrics:
        print(f"  Episode {ep}: {r.metrics.action_divergence.action_mismatch_rate:.1%}")
```

---

## 4. Reading the comparison output

This section explains each block of the comparison result and how to
interpret the metrics.

### 4.1 Identity

The identity block records what was compared:

| Field                    | Description |
|--------------------------|-------------|
| `reference_system_type`  | System type of the reference trace (e.g. `"system_a"`) |
| `candidate_system_type`  | System type of the candidate trace (e.g. `"system_c"`) |
| `reference_run_id`       | Run ID of the reference (if provided) |
| `candidate_run_id`       | Run ID of the candidate (if provided) |
| `reference_episode_index`| Episode index of the reference |
| `candidate_episode_index`| Episode index of the candidate |
| `episode_seed`           | The shared seed (if verified) |
| `pairing_mode`           | `"derived_seed"` or `null` if seed could not be verified |

### 4.2 Validation

The validation block confirms whether the pair is valid:

| Field                  | Description |
|------------------------|-------------|
| `is_valid_pair`        | `true` if all constraints passed |
| `errors`               | List of error codes (empty on success) |
| `world_type_match`     | Whether world types are identical |
| `world_config_match`   | Whether world configs are identical |
| `start_position_match` | Whether start positions are identical |
| `episode_seed_match`   | Whether seeds match (`null` if not verifiable) |
| `shared_action_labels` | Actions available in both systems |

### 4.3 Alignment

| Field                   | Description |
|-------------------------|-------------|
| `reference_total_steps` | Total steps in the reference episode |
| `candidate_total_steps` | Total steps in the candidate episode |
| `aligned_steps`         | Number of steps compared side by side (`min(ref, cand)`) |
| `reference_extra_steps` | Steps only the reference has beyond the aligned prefix |
| `candidate_extra_steps` | Steps only the candidate has beyond the aligned prefix |

**How to read it:** If `aligned_steps = 163` and
`candidate_extra_steps = 37`, the candidate survived 37 steps longer
than the reference. These extra steps are not included in the
divergence metrics (which only cover the aligned prefix), but they are
reflected in the outcome comparison.

### 4.4 Action divergence

| Field                        | Description |
|------------------------------|-------------|
| `first_action_divergence_step` | Timestep where the agents first chose different actions. `null` if they never diverged. |
| `action_mismatch_count`      | Total number of aligned steps where actions differed |
| `action_mismatch_rate`       | `mismatch_count / aligned_steps` (0.0 to 1.0) |

**How to read it:** A `first_action_divergence_step` of 105 with a
mismatch rate of 19.6% means the agents behaved identically for the
first 105 steps, then began occasionally choosing different actions.
The later divergence suggests the candidate system's prediction
mechanism only kicks in once it has accumulated enough experience.

### 4.5 Position divergence

| Field                      | Description |
|----------------------------|-------------|
| `distance_series`          | Manhattan distance between agents at each aligned step |
| `mean_trajectory_distance` | Average Manhattan distance over all aligned steps |
| `max_trajectory_distance`  | Maximum Manhattan distance reached |

**How to read it:** A mean distance of 2.34 with a maximum of 13
means the agents gradually drifted apart on the grid. The distance
series is a time series -- you can plot it to see when and how fast
they diverged.

> **Note:** Manhattan distance is `|x_ref - x_cand| + |y_ref - y_cand|`.
> It counts the minimum grid steps needed to walk from one agent
> position to the other.

### 4.6 Vitality divergence

| Field                       | Description |
|-----------------------------|-------------|
| `difference_series`         | `vitality_cand - vitality_ref` at each aligned step (signed) |
| `mean_absolute_difference`  | Average of `|difference|` over aligned steps |
| `max_absolute_difference`   | Maximum `|difference|` over aligned steps |

**How to read it:** Positive values in the difference series mean the
candidate was healthier at that step. A max absolute difference of
0.39 means the two agents' vitality levels diverged by up to 39
percentage points during the episode.

### 4.7 Action usage

| Field                        | Description |
|------------------------------|-------------|
| `reference_most_used`        | Most frequently selected action by the reference agent |
| `reference_most_used_ambiguity` | `"ambiguous_due_to_tie"` if two or more actions tied for most used |
| `candidate_most_used`        | Most frequently selected action by the candidate agent |
| `candidate_most_used_ambiguity` | Tie ambiguity for the candidate |
| `shared_action_usage`        | Per-action breakdown (see below) |
| `reference_only_actions`     | Actions used only by the reference (not available to the candidate) |
| `candidate_only_actions`     | Actions used only by the candidate |

Each entry in `shared_action_usage` contains:

| Field              | Description |
|--------------------|-------------|
| `action`           | Action label (e.g. `"consume"`, `"up"`) |
| `reference_count`  | Times the reference agent chose this action |
| `candidate_count`  | Times the candidate agent chose this action |
| `delta`            | `candidate_count - reference_count` |

**How to read it:** A positive delta for `"consume"` means the
candidate consumed more often. Look at the delta values to understand
behavioral shifts -- did the candidate explore more? Consume more
aggressively? Stay in place less?

### 4.8 Outcome

The outcome block compares the full episodes (not just the aligned
prefix):

| Field                          | Description |
|--------------------------------|-------------|
| `reference_termination_reason` | Why the reference episode ended (e.g. `"energy_depleted"`, `"max_steps_reached"`) |
| `candidate_termination_reason` | Why the candidate episode ended |
| `reference_final_vitality`     | Reference agent's vitality at episode end (0.0--1.0) |
| `candidate_final_vitality`     | Candidate agent's vitality at episode end |
| `final_vitality_delta`         | `candidate - reference` (positive = candidate healthier) |
| `reference_total_steps`        | Total steps in the reference episode |
| `candidate_total_steps`        | Total steps in the candidate episode |
| `total_steps_delta`            | `candidate - reference` (positive = candidate survived longer) |
| `longer_survivor`              | `"reference"`, `"candidate"`, or `"equal"` |

**How to read it:** This is the bottom-line comparison. If the
candidate survived to `max_steps_reached` while the reference died of
`energy_depleted`, the candidate's system clearly provided a survival
advantage in this episode.

### 4.9 Run-level statistical summary

When comparing full runs, the summary aggregates scalar metrics
across all valid episode pairs. Each metric is reported with
descriptive statistics:

| Statistic | Meaning |
|-----------|---------|
| `mean`    | Average across all valid episode pairs |
| `std`     | Standard deviation (0 if only 1 pair) |
| `min`     | Minimum value across all pairs |
| `max`     | Maximum value across all pairs |
| `n`       | Number of valid pairs contributing |

The summary includes these aggregated metrics:

| Metric                     | Per-episode source |
|----------------------------|--------------------|
| `action_mismatch_rate`     | `metrics.action_divergence.action_mismatch_rate` |
| `mean_trajectory_distance` | `metrics.position_divergence.mean_trajectory_distance` |
| `mean_vitality_difference` | `metrics.vitality_divergence.mean_absolute_difference` |
| `final_vitality_delta`     | `outcome.final_vitality_delta` (signed) |
| `total_steps_delta`        | `outcome.total_steps_delta` (signed) |

Additional summary fields:

| Field                     | Description |
|---------------------------|-------------|
| `num_episodes_compared`   | Total episode pairs attempted |
| `num_valid_pairs`         | Pairs that passed validation |
| `num_invalid_pairs`       | Pairs that failed validation |
| `reference_survival_rate` | Fraction of valid pairs where the reference reached `max_steps_reached` |
| `candidate_survival_rate` | Fraction of valid pairs where the candidate reached `max_steps_reached` |
| `candidate_longer_count`  | Pairs where the candidate survived longer |
| `reference_longer_count`  | Pairs where the reference survived longer |
| `equal_count`             | Pairs with equal total steps |

**How to read it:** The mean and std give you the central tendency and
spread. Compare `candidate_survival_rate` to `reference_survival_rate`
for the clearest signal of which system performs better. A positive
`final_vitality_delta.mean` means the candidate was healthier on average.

---

## 5. System C prediction extension

When the candidate is a System C trace, the comparison automatically
runs an additional analysis of the prediction mechanism's effect. This
appears under the `system_c_prediction` key in the
`system_specific_analysis` block.

### 5.1 Extension metrics

| Metric                                  | Description |
|-----------------------------------------|-------------|
| `prediction_active_step_count`          | Number of aligned steps where prediction modulation was active (modulated scores differed from raw drive scores) |
| `prediction_active_step_rate`           | `active_count / aligned_steps` |
| `top_action_changed_by_modulation_count`| Steps where modulation changed the highest-scoring action |
| `top_action_changed_by_modulation_rate` | `changed_count / aligned_steps` |
| `ambiguous_top_action_count`            | Steps where the top action could not be determined due to a tie in modulated scores |
| `mean_modulation_delta`                 | Average absolute difference between raw and modulated scores across all actions and aligned steps |

### 5.2 Interpreting the prediction metrics

**prediction_active_step_rate** tells you how often the prediction
mechanism was doing anything at all. A rate of 0.80 means modulation
was active in 80% of steps -- the prediction system had built up
enough experience to adjust scores in most situations.

**top_action_changed_by_modulation_rate** is the sharpest signal. It
tells you how often modulation actually overruled the raw drive ranking.
A rate of 0.018 (1.8%) means modulation changed the top action only 3
times in 163 steps -- the prediction mostly reinforced the drive
rather than overriding it. This is expected in static environments
where the prediction mechanism learns the world quickly and makes
small corrections.

**mean_modulation_delta** measures the average magnitude of
modulation's effect. A value of 0.006 means scores were typically
adjusted by less than 1% -- a subtle influence. In dynamic
environments (fast resource regeneration, higher sensitivities), this
value will be larger.

### 5.3 When the extension produces zero values

If all System C prediction metrics are zero, the most likely causes
are:

1. **Static environment + fast memory learning.** In a world with no
   resource regeneration, the prediction memory learns perfectly and
   prediction errors drop to zero. Zero errors mean zero trace
   accumulation, which means zero modulation. Use the
   `system-c-prediction-demo.yaml` config with fast regeneration to
   see visible prediction effects.

2. **Missing decision data.** The extension reads from
   `system_data.decision_data.prediction.modulated_scores` and
   `system_data.decision_data.drive.action_contributions` in the
   persisted trace. If these keys are missing (e.g. from a different
   system version), the extension gracefully produces zeros rather
   than failing.

---

## 6. Tolerance and ambiguity rules

The comparison uses two tolerance constants to handle floating-point
arithmetic:

| Constant            | Value  | Purpose |
|---------------------|--------|---------|
| `EQUALITY_EPSILON`  | 1e-9   | General floating-point equality |
| `RANKING_EPSILON`   | 1e-6   | Ranking comparisons (which action scored highest) |

When two scores differ by less than `RANKING_EPSILON`, the comparison
treats them as tied. Tied top-action rankings are reported as
`ambiguous_top_action_count` rather than counted as changes. The tool
never silently coerces ambiguous states to false or zero.

---

## 7. Architecture

### 7.1 Package structure

The comparison tool lives in `src/axis/framework/comparison/`:

```
comparison/
    __init__.py             Public API exports
    types.py                Frozen Pydantic result models and enums
    validation.py           Pair validation (world, seed, action space)
    alignment.py            Shared-prefix alignment and step iterator
    actions.py              Action-space intersection and usage stats
    metrics.py              Action, position, and vitality divergence
    outcome.py              Full-episode outcome comparison
    extensions.py           System-specific extension dispatch
    system_c_extension.py   System C prediction analysis
    compare.py              Top-level orchestrator
```

### 7.2 Processing pipeline

The comparison follows a strict pipeline:

```
validate ──> align ──> compute metrics ──> compute outcome ──> run extensions ──> assemble result
```

1. **Validate** -- check all pairing constraints. If validation
   fails, return immediately with error codes.
2. **Align** -- compute shared-prefix length.
3. **Compute metrics** -- action divergence, position divergence,
   vitality divergence, and action usage over the aligned steps.
4. **Compute outcome** -- compare full-episode termination, vitality,
   and survival.
5. **Run extensions** -- dispatch to system-specific analysis (e.g.
   System C prediction). Extensions are registered by system type and
   dispatched based on the candidate's `system_type`.
6. **Assemble result** -- combine all blocks into a single frozen
   `PairedTraceComparisonResult`.

### 7.3 Extension dispatch

System-specific extensions are registered using a decorator:

```python
from axis.framework.comparison.extensions import register_extension

@register_extension("system_c")
def system_c_prediction_analysis(reference, candidate, alignment):
    # ... compute prediction-specific metrics ...
    return {"system_c_prediction": { ... }}
```

The dispatch is based on the **candidate** system type. Extensions
receive the full reference and candidate traces plus the alignment
summary. They return a dictionary that is attached to the result under
`system_specific_analysis`.

Extensions must not import live system classes -- they read only from
the persisted trace data (`system_data`/`decision_data`). This keeps
the comparison layer decoupled from the execution layer.

---

## 8. Workflow recipes

### 8.1 Comparing System A vs System C (standard workflow)

1. Run both experiments with the same seed and world settings:

```bash
axis experiments run experiments/configs/system-a-baseline.yaml
axis experiments run experiments/configs/system-c-baseline.yaml
```

2. Find the experiment IDs:

```bash
axis experiments list
```

3. Compare the full run (all episodes with summary):

```bash
axis compare \
  --reference-experiment <system-a-id> --reference-run run-0000 \
  --candidate-experiment <system-c-id> --candidate-run run-0000
```

4. Or compare a single episode:

```bash
axis compare \
  --reference-experiment <system-a-id> --reference-run run-0000 --reference-episode 1 \
  --candidate-experiment <system-c-id> --candidate-run run-0000 --candidate-episode 1
```

### 8.2 Exporting comparison data for analysis

```bash
# Save JSON for each episode to a file
for ep in 1 2 3 4 5; do
  axis compare \
    --reference-experiment <ref-id> --reference-run run-0000 --reference-episode $ep \
    --candidate-experiment <cand-id> --candidate-run run-0000 --candidate-episode $ep \
    --output json > comparison_ep${ep}.json
done
```

### 8.3 Quick survival summary

```bash
axis compare ... --output json | jq '{
  ref_steps: .outcome.reference_total_steps,
  cand_steps: .outcome.candidate_total_steps,
  ref_reason: .outcome.reference_termination_reason,
  cand_reason: .outcome.candidate_termination_reason,
  vitality_delta: .outcome.final_vitality_delta,
  survivor: .outcome.longer_survivor
}'
```

---

## 9. Result schema reference

### 9.1 Episode-level result

The complete `PairedTraceComparisonResult` model:

```
PairedTraceComparisonResult
 ├── result_mode: "comparison_succeeded" | "comparison_failed_validation"
 ├── identity: PairIdentity
 │    ├── reference_system_type: str
 │    ├── candidate_system_type: str
 │    ├── reference_run_id: str | null
 │    ├── candidate_run_id: str | null
 │    ├── reference_episode_index: int | null
 │    ├── candidate_episode_index: int | null
 │    ├── episode_seed: int | null
 │    └── pairing_mode: "derived_seed" | null
 ├── validation: PairValidationResult
 │    ├── is_valid_pair: bool
 │    ├── errors: [str, ...]
 │    ├── world_type_match: bool
 │    ├── world_config_match: bool
 │    ├── start_position_match: bool
 │    ├── episode_seed_match: bool | null
 │    └── shared_action_labels: [str, ...]
 ├── alignment: AlignmentSummary | null
 │    ├── reference_total_steps: int
 │    ├── candidate_total_steps: int
 │    ├── aligned_steps: int
 │    ├── reference_extra_steps: int
 │    └── candidate_extra_steps: int
 ├── metrics: GenericComparisonMetrics | null
 │    ├── action_divergence: ActionDivergence
 │    │    ├── first_action_divergence_step: int | null
 │    │    ├── action_mismatch_count: int
 │    │    └── action_mismatch_rate: float
 │    ├── position_divergence: PositionDivergence
 │    │    ├── distance_series: [int, ...]
 │    │    ├── mean_trajectory_distance: float
 │    │    └── max_trajectory_distance: int
 │    ├── vitality_divergence: VitalityDivergence
 │    │    ├── difference_series: [float, ...]
 │    │    ├── mean_absolute_difference: float
 │    │    └── max_absolute_difference: float
 │    └── action_usage: ActionUsageComparison
 │         ├── reference_most_used: str | null
 │         ├── reference_most_used_ambiguity: AmbiguityState | null
 │         ├── candidate_most_used: str | null
 │         ├── candidate_most_used_ambiguity: AmbiguityState | null
 │         ├── shared_action_usage: [ActionUsageEntry, ...]
 │         ├── reference_only_actions: [str, ...]
 │         └── candidate_only_actions: [str, ...]
 ├── outcome: OutcomeComparison | null
 │    ├── reference_termination_reason: str
 │    ├── candidate_termination_reason: str
 │    ├── reference_final_vitality: float
 │    ├── candidate_final_vitality: float
 │    ├── final_vitality_delta: float
 │    ├── reference_total_steps: int
 │    ├── candidate_total_steps: int
 │    ├── total_steps_delta: int
 │    └── longer_survivor: "reference" | "candidate" | "equal"
 └── system_specific_analysis: dict | null
      └── system_c_prediction (when candidate is System C):
           ├── prediction_active_step_count: int
           ├── prediction_active_step_rate: float
           ├── top_action_changed_by_modulation_count: int
           ├── top_action_changed_by_modulation_rate: float
           ├── ambiguous_top_action_count: int
           └── mean_modulation_delta: float
```

When `result_mode` is `"comparison_failed_validation"`, the
`alignment`, `metrics`, `outcome`, and `system_specific_analysis`
fields are `null`.

### 9.2 Run-level result schema

The `RunComparisonResult` model (returned by `compare_runs()`):

```
RunComparisonResult
 ├── reference_experiment_id: str | null
 ├── candidate_experiment_id: str | null
 ├── reference_run_id: str
 ├── candidate_run_id: str
 ├── reference_system_type: str
 ├── candidate_system_type: str
 ├── episode_results: [PairedTraceComparisonResult, ...]
 └── summary: RunComparisonSummary
      ├── num_episodes_compared: int
      ├── num_valid_pairs: int
      ├── num_invalid_pairs: int
      ├── action_mismatch_rate: MetricSummaryStats
      ├── mean_trajectory_distance: MetricSummaryStats
      ├── mean_vitality_difference: MetricSummaryStats
      ├── final_vitality_delta: MetricSummaryStats
      ├── total_steps_delta: MetricSummaryStats
      ├── reference_survival_rate: float
      ├── candidate_survival_rate: float
      ├── candidate_longer_count: int
      ├── reference_longer_count: int
      └── equal_count: int

MetricSummaryStats
 ├── mean: float
 ├── std: float
 ├── min: float
 ├── max: float
 └── n: int
```

Each `episode_results` entry is a full `PairedTraceComparisonResult`
(see section 9.1). The `summary` aggregates only over valid pairs.
