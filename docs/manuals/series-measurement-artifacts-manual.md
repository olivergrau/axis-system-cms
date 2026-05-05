# Reading Series Measurement Artifacts

Experiment series produce several layers of measurement artifacts. Those
artifacts answer different questions, at different aggregation levels, and
they are easy to misread when viewed side by side.

This manual explains how to read:

- per-experiment measurement logs
- per-experiment comparison outputs
- aggregate series reports under `series/<series-id>/measurements/`

It also explains the most common source of confusion:

- **survival rate** is not the same as **longer survivor count**

## 1. Mental Model

A workspace series produces three nested levels of evidence:

1. **Run-level artifacts**
   One system in one experiment, aggregated across all episodes.

2. **Pairwise comparison artifacts**
   A reference run and a candidate run compared episode-by-episode.

3. **Series-level aggregate artifacts**
   A compact overview across all declared series experiments.

If you mix those levels mentally, the numbers look inconsistent even when they
are correct.

## 2. Where The Artifacts Live

For a series such as `system-parameter-variations`, the important outputs are:

- `series/<series-id>/measurements/series-summary.md`
- `series/<series-id>/measurements/series-summary.json`
- `series/<series-id>/measurements/series-metrics.csv`
- `series/<series-id>/measurements/series-manifest.json`

Per experiment, AXIS also writes:

- `series/<series-id>/measurements/experiment_N/...-candidate-run-summary.log`
- `series/<series-id>/measurements/experiment_N/...-comparison.log`
- `series/<series-id>/comparisons/comparison-XYZ.json`

These files are related, but they are not duplicates.

## 3. What Each Artifact Means

### 3.1 Candidate run summary log

Example:

- `series/system-parameter-variations/measurements/experiment_6/cw-strong-symmetric-candidate-run-summary.log`

This file answers:

- How did the **candidate system alone** behave in this experiment?

It contains:

- run summary values such as `mean_steps`, `death_rate`, `mean_final_vitality`
- behavioral metrics such as `resource_gain_per_step`, `unique_cells_visited`
- system-specific metrics such as prediction traces or arbitration summaries

This file says nothing directly about whether the candidate was better or worse
than the reference. It is a **single-run aggregate**.

### 3.2 Comparison log

Example:

- `series/system-parameter-variations/measurements/experiment_6/cw-strong-symmetric-comparison.log`

This file answers:

- How did the **candidate and reference** differ when episodes were paired by
  index?

It contains:

- a per-episode comparison table
- a run-level statistical summary across all episode pairs
- optional system-specific comparison analysis

This is the first place where terms like:

- `candidate survival`
- `reference survival`
- `candidate longer`
- `reference longer`
- `final vitality delta`

become meaningful.

### 3.3 Comparison JSON

Example:

- `series/system-parameter-variations/comparisons/comparison-006.json`

This is the structured source of truth behind the comparison log.

It includes:

- `comparison_result.episode_results`
- `comparison_result.summary`
- copies of both experiment configs at comparison time

If you need exact machine-readable values, use this file rather than the text
log.

### 3.4 Series summary markdown

Example:

- `series/system-parameter-variations/measurements/series-summary.md`

This file is a **curated report**, not a lossless raw dump.

It is designed to answer:

- What changed across the series?
- Which experiments look promising?
- How does the candidate compare to the reference at a glance?

It deliberately compresses the underlying artifacts into a few views.

### 3.5 Series summary JSON

Example:

- `series/system-parameter-variations/measurements/series-summary.json`

This file is the structured source for the series summary. Each experiment entry
contains:

- `run_summary`
- `behavior_metrics`
- `comparison_summary`
- file paths and experiment identifiers

This is the best file to inspect when you want to reconcile a series-level
statement with the underlying measurement and comparison artifacts.

### 3.6 Series metrics CSV

Example:

- `series/system-parameter-variations/measurements/series-metrics.csv`

This is a flat spreadsheet-oriented export.

Use it when you want to:

- sort experiments by one metric
- load the series into pandas
- make quick plots outside AXIS

It is convenient, but it drops some structure. For careful interpretation,
prefer the JSON.

## 4. How To Read `series-summary.md`

The markdown report contains several sections. Each section answers a different
question.

### 4.1 `At A Glance`

This table is the fastest scan across the whole series.

For `system_comparison` series, the columns mean:

- `Death rate`
  Candidate run death rate from the candidate run summary.
- `Mean vitality`
  Candidate run mean final vitality.
- `Gain/step`
  Candidate run `resource_gain_per_step`.
- `Energy eff.`
  Candidate run `net_energy_efficiency`.
- `Unique cells`
  Candidate run `unique_cells_visited`.
- `Candidate surv.`
  Candidate survival rate from the comparison summary.
- `Reference surv.`
  Reference survival rate from the comparison summary.

Important:

- the first five columns are **candidate-run metrics**
- the last two columns are **comparison metrics**

That mixed table is useful, but it is one reason people get confused.

### 4.2 `Progression View`

This section compares each experiment to the immediately previous one.

It answers:

- What changed locally in the series sequence?

This is useful when the series was intentionally designed as a parameter walk.

### 4.3 `Baseline View`

This section compares every experiment back to the first one.

It answers:

- How far did we drift from the baseline anchor?

This is usually the better view for scientific interpretation than
`Progression View`, because it avoids chaining local changes.

### 4.4 `Reference-System View`

This section is specific to `system_comparison` series.

A line such as:

```text
exp_06 candidate survival 0.460 vs reference 0.580;
mean trajectory distance 9.243; final vitality delta -0.110
```

means:

- `candidate survival 0.460`
  In `46%` of episode pairs, the candidate reached `max_steps_reached`.
- `reference 0.580`
  In `58%` of episode pairs, the reference reached `max_steps_reached`.
- `mean trajectory distance 9.243`
  Across valid episode pairs, the mean per-episode path distance was `9.243`.
- `final vitality delta -0.110`
  Candidate final vitality minus reference final vitality, averaged across
  valid pairs.

This section is about **horizon success** and broad pairwise divergence, not
about who outlived whom inside failing pairs.

### 4.5 `Paired-Survival View`

This section is also specific to `system_comparison` series.

A line such as:

```text
exp_06 candidate longer 14 vs reference 12; equal 24;
mean total steps delta -9.800
```

means:

- `candidate longer 14`
  In `14` paired episodes, the candidate survived longer than the reference.
- `reference 12`
  In `12` paired episodes, the reference survived longer than the candidate.
- `equal 24`
  In `24` paired episodes, neither outlived the other.
- `mean total steps delta -9.800`
  Candidate episode length minus reference episode length, averaged across
  valid pairs.

This section is the right place to answer:

- Did the candidate often die later, even when it still failed overall?
- Are the two systems mostly tied, or is one systematically outliving the
  other?

This section should be read together with `Reference-System View`, not as a
replacement for it.

## 5. The Most Important Distinction

### Survival rate is not longer-survivor count

This is the most common interpretation error.

These quantities answer different questions:

- `candidate_survival_rate`
  How often did the candidate reach the episode horizon?

- `candidate_longer_count`
  In how many paired episodes did the candidate survive longer than the
  reference, even if it still died before the horizon?

These can point in different directions.

#### Example

Suppose one paired episode shows:

- reference steps: `237`
- candidate steps: `349`

Then:

- the candidate is the **longer survivor** for this pair
- but if the max horizon is `400`, the candidate did **not** count as a
  survival success

So it is entirely possible to observe:

- candidate survival rate lower than reference survival rate
- while candidate longer count is still higher than reference longer count

This is not an inconsistency. It means:

- the candidate often dies too
- but in some failing pairs, it dies later than the reference

### Equality also mixes two situations

`equal_count` includes both:

- both runs reach the horizon, e.g. `400/400`
- both runs die after the same number of steps, e.g. `100/100`

So `equal` does not mean “both succeeded.” It only means “neither outlived the
other.”

## 6. Recommended Reading Order

When inspecting one experiment inside a series, use this order:

1. Read the candidate run summary log.
   Ask: what did the candidate do on its own?

2. Read the comparison log.
   Ask: how did candidate and reference diverge pairwise?

3. Open the corresponding comparison JSON if something feels surprising.
   Ask: is the summary hiding pairwise structure?

4. Return to `series-summary.md`.
   Ask: how should this experiment be positioned relative to the others?
   Use:
   - `Reference-System View` for survival-rate comparison
   - `Paired-Survival View` for longer-survivor comparison

5. If needed, inspect `series-summary.json`.
   Ask: are the series-level summary values consistent with the underlying
   measurement artifacts?

## 7. Which File Should I Use For Which Question?

| Question | Best artifact |
| --- | --- |
| How did the candidate behave overall? | candidate run summary log |
| Did the candidate differ from the reference? | comparison log |
| Which episodes drove the difference? | comparison log or comparison JSON |
| Which experiments look best across the series? | `series-summary.md` |
| Are the series report values exact? | `series-summary.json` |
| Do I want to plot or sort metrics quickly? | `series-metrics.csv` |

## 8. Common Misreadings

### “The series summary says candidate survival is worse, but the comparison log says candidate lived longer.”

Usually this means:

- you are comparing `candidate_survival_rate`
- to `candidate_longer_count`

Those are different statistics.

### “The `At A Glance` table mixes candidate and reference information.”

Correct.

That table combines:

- candidate run metrics
- with paired comparison survival metrics

It is useful for scanning, but not ideal for careful inference.

### “The candidate run summary looks good, so the candidate must have beaten the reference.”

Not necessarily.

The candidate may look good in isolation, but the reference may still be better
on:

- survival rate
- final vitality
- step horizon robustness

That is why the comparison artifacts exist.

## 9. Interpreting Series Results Scientifically

A good series interpretation usually separates three claims:

1. **mechanism claim**
   The candidate activates or modulates something internally.

2. **behavior claim**
   The candidate behaves differently from the reference.

3. **performance claim**
   The candidate is better, worse, or unchanged on the target outcome.

In AXIS, these are often not identical.

For example, a prediction system may show:

- visible internal prediction traces
- high action mismatch against the reference
- large trajectory divergence
- but no survival improvement

That means the mechanism is active and behaviorally consequential, but not yet
beneficial under the tested world conditions.

## 10. Practical Advice

- Use `series-summary.md` for orientation.
- Use per-experiment logs for explanation.
- Use `series-summary.json` when something looks inconsistent.
- Be explicit about whether you mean:
  - single-run aggregate
  - paired comparison statistic
  - or series-level position

If you keep those three levels separate, the measurement artifacts become much
easier to read.

## See Also

- [Experiment Series](experiment-series-manual.md)
- [Experiment Workspaces](workspace-manual.md)
- [Paired Trace Comparison](comparison-manual.md)
