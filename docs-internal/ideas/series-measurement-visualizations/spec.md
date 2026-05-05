# Series Measurement Visualizations

## Status

Idea / initial spec

## Purpose

AXIS series measurements already produce strong structured artifacts:

- per-run summaries
- paired comparison outputs
- aggregate series summaries

But the current output is still text-heavy and JSON-heavy. Important patterns
remain hard to see quickly, especially when trying to answer questions like:

- Does a system change behavior, or just noise?
- Does a system survive longer overall, or only inside some paired failures?
- Is a mechanism active without improving outcome?
- Which experiments are the real follow-up candidates?

This idea introduces a **standard visualization layer for measurement artifacts**
so that series execution can also emit a set of reusable, interpretable plots.

## High-Level Goal

Extend the measurement/reporting workflow so that AXIS can automatically produce
visual artifacts for series results at three levels:

1. **Series-level overview plots**
2. **Per-experiment comparison plots**
3. **System-specific mechanism plots via extension registration**

These visualizations should be written into the workspace measurement tree and
treated as first-class measurement artifacts, not as ad hoc notebook outputs.

## Design Principles

### 1. Visuals complement, not replace, structured artifacts

Plots should help pattern recognition and prioritization, but:

- `series-summary.json` remains the machine-readable source of truth
- comparison JSON remains the lossless paired-comparison source
- run summary / comparison logs remain the primary textual inspection outputs

### 2. Standard plots must remain system-agnostic where possible

Series-level and per-experiment comparison plots should be generated from
generic AXIS artifacts whenever possible.

### 3. Mechanism plots belong to systems

System-specific measurement visualizations should follow the same architectural
pattern AXIS already uses elsewhere:

- metrics extensions
- comparison extensions
- visualization extensions

That means:

- generic reporting code owns generic plots
- systems own mechanism-specific plots

### 4. Generated images should be lightweight and portable

Default format should be:

- `png`

Rationale:

- better for diagrams than JPEG
- simple to embed in docs and notebooks
- widely supported

## Proposed Output Structure

### Series-level outputs

Under:

- `series/<series-id>/measurements/plots/`

Example files:

- `survival-rates.png`
- `paired-survival-counts.png`
- `trajectory-vs-survival.png`
- `efficiency-vs-survival.png`
- `series-progression.png`
- `prediction-impact-vs-survival.png`
- `modulation-strength-vs-performance.png`
- `prediction-error-profile.png`
- `curiosity-hunger-weight-plane.png`

### Per-experiment outputs

Under:

- `series/<series-id>/measurements/experiment_<n>/plots/`

Example files:

- `paired-steps-delta-hist.png`
- `paired-final-vitality-delta-hist.png`
- `episode-outcomes-strip.png`
- `mismatch-vs-outcome.png`
- `trajectory-distance-distribution.png`

## Visualization Levels

## 1. Series-level overview plots

These plots should help answer:

- Which experiments look promising?
- Which ones diverge behaviorally but fail performance-wise?
- Where are the meaningful tradeoffs?

### Proposed standard plots

#### 1. `survival-rates.png`

Bar or paired bar chart:

- candidate survival rate
- reference survival rate

per experiment.

Primary use:

- fastest overall performance scan

#### 2. `paired-survival-counts.png`

Stacked bar chart:

- `candidate_longer_count`
- `reference_longer_count`
- `equal_count`

per experiment.

Primary use:

- separates paired survival structure from plain survival rate

#### 3. `trajectory-vs-survival.png`

Scatter plot:

- x = mean trajectory distance
- y = candidate survival rate, or survival delta

Primary use:

- detect whether stronger behavioral divergence correlates with benefit or harm

#### 4. `efficiency-vs-survival.png`

Scatter plot:

- x = net energy efficiency
- y = candidate survival rate, or survival delta

Primary use:

- detect whether local energetic improvement translates into robustness

#### 5. `series-progression.png`

Multi-line progression plot across experiment order:

- death rate
- mean final vitality
- net energy efficiency
- candidate survival
- reference survival

Primary use:

- visually inspect local progression across the series

## 2. Per-experiment comparison plots

These plots help inspect one series experiment in more depth.

### Proposed standard plots

#### 1. `paired-steps-delta-hist.png`

Histogram of:

- `candidate_total_steps - reference_total_steps`

across episode pairs.

Primary use:

- distinguish “often tied”, “few huge wins”, and “consistent small losses”

#### 2. `paired-final-vitality-delta-hist.png`

Histogram of:

- `candidate_final_vitality - reference_final_vitality`

across episode pairs.

Primary use:

- inspect whether outcome differences are broad or driven by tails

#### 3. `episode-outcomes-strip.png`

Per-episode categorical strip / dot plot:

- candidate longer
- reference longer
- equal

Primary use:

- fast scan of pair structure without opening the full comparison log table

#### 4. `mismatch-vs-outcome.png`

Scatter plot:

- x = per-episode action mismatch rate
- y = per-episode steps delta or final vitality delta

Primary use:

- show whether stronger policy divergence actually helps or hurts

#### 5. `trajectory-distance-distribution.png`

Box/violin/strip plot over per-episode trajectory distance.

Primary use:

- inspect distribution shape rather than only the mean

## 3. System-specific mechanism plots

These plots are only meaningful for certain systems and must therefore be owned
by system-specific extensions.

### Proposed initial `system_cw` / prediction-oriented plots

#### 1. `prediction-impact-vs-survival.png`

Series-level scatter:

- x = `behavioral_prediction_impact_rate`
- y = `candidate_survival_rate - reference_survival_rate`

Primary use:

- directly test whether active prediction impact correlates with benefit

#### 2. `modulation-strength-vs-performance.png`

Series-level scatter / paired scatter:

- hunger modulation strength vs survival delta
- curiosity modulation strength vs survival delta

Primary use:

- test whether stronger modulation is useful or destabilizing

#### 3. `prediction-error-profile.png`

Grouped bar chart per experiment:

- feature prediction error mean
- hunger prediction error mean
- curiosity prediction error mean

Primary use:

- compare predictive regimes at a glance

#### 4. `curiosity-hunger-weight-plane.png`

2D scatter:

- x = mean hunger weight
- y = mean curiosity weight
- color = survival delta or vitality delta

Primary use:

- inspect whether beneficial runs cluster in a distinct arbitration regime

## Extension Architecture

System-specific measurement visualization generation should follow a new
extension pattern, parallel to existing extension systems.

### Desired pattern

Generic AXIS core:

- renders generic series-level plots
- renders generic per-experiment comparison plots
- discovers optional system-specific measurement visualization extensions

System module:

- contributes additional plots when its metrics/comparison outputs are present

### Desired extension ownership

For example:

- `axis.systems.system_cw.measurement_visualizations`

should register one or more plot builders that understand `system_cw`-specific:

- behavior metrics
- comparison summaries
- system-specific metric payloads

## Data Sources

The plotting pipeline should prefer existing aggregate artifacts instead of
recomputing expensive analysis.

### Generic sources

- `series-summary.json`
- `comparison-XXX.json`
- candidate run summary log is display-only; plots should prefer structured data

### System-specific sources

- `behavior_metrics.system_specific_metrics`
- `comparison_result.system_specific_analysis`

## Workflow Integration

The intended integration point is the workspace measurement/reporting workflow.

### Desired behavior

When `axis workspaces run-series ...` completes, AXIS should:

1. generate the existing aggregate artifacts
2. generate the new plot artifacts
3. write them into the series measurement tree
4. optionally reference them from `series-summary.md`

## Optional Report Linking

Later versions may extend `series-summary.md` to include a small “Generated
Plots” section, for example:

- `plots/survival-rates.png`
- `plots/paired-survival-counts.png`

This is helpful, but not required for the first implementation.

## Non-Goals For The First Version

- no notebook integration
- no automatic image embedding into Markdown summaries yet
- no interactive dashboards
- no web-serving requirement
- no visual generation for `light` runs when the required comparison data does
  not exist

## Open Questions

### 1. Should plot generation be always-on?

Possible answer:

- first version: yes for series workflows, assuming required data exists

Alternative:

- configurable via workspace measurement workflow settings

### 2. Should plot generation failures fail the whole measurement workflow?

Preferred answer:

- no
- plot generation should be best-effort and separately reported

Reason:

- plot rendering should not invalidate already-computed experimental results

### 3. Should plots be regenerated independently later?

Probably yes in the long run.

Potential later command:

- `axis workspaces render-series-plots <workspace> --series <series-id>`

But this is not required for the first milestone.

## Suggested Implementation Split

This idea likely becomes at least two engineering tracks:

1. **Generic series/comparison plotting**
   - generic plot builders
   - file layout
   - workflow integration

2. **System-specific measurement visualization extensions**
   - extension contract
   - registration / discovery
   - initial `system_cw` implementation

## Why This Matters

AXIS is increasingly able to produce rich structured evidence, but evidence is
not automatically readable. Text logs and JSON remain essential, yet many
important scientific patterns only become obvious when viewed spatially.

Adding a visualization layer to measurement artifacts would make it much easier
to:

- triage series results
- catch misleading interpretations
- communicate findings
- identify promising parameter regimes for follow-up work

In short:

this idea turns series measurements from “structured but dense” into “structured
and readable.”
