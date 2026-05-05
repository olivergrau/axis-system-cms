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

### Exactly which generic series-level plots are feasible now

The following plots can be generated immediately from the current generic
series artifacts, without needing any new system-specific data model:

#### Always available for `system_comparison` series

- `survival-rates.png`
  Uses:
  - `comparison_summary.candidate_survival_rate`
  - `comparison_summary.reference_survival_rate`

- `paired-survival-counts.png`
  Uses:
  - `comparison_summary.candidate_longer_count`
  - `comparison_summary.reference_longer_count`
  - `comparison_summary.equal_count`

- `trajectory-vs-survival.png`
  Uses:
  - `comparison_summary.mean_trajectory_distance.mean`
  - survival rate or survival delta

- `efficiency-vs-survival.png`
  Uses:
  - `behavior_metrics.standard_metrics.net_energy_efficiency.mean`
  - survival rate or survival delta

- `series-progression.png`
  Uses:
  - `run_summary.death_rate`
  - `run_summary.mean_final_vitality`
  - `behavior_metrics.standard_metrics.net_energy_efficiency.mean`
  - comparison survival rates

#### Also available for `single_system` series with small semantic changes

The same generic plotting machinery can be reused, but:

- `reference` becomes the baseline experiment in the series
- labels should say `current` vs `baseline` rather than `candidate` vs `reference`

So the generic layer should be written broadly enough to support:

- `system_comparison`
- `single_system`

with naming differences but the same overall plot family.

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

### Exactly which generic per-experiment plots are feasible now

These plots can be generated from the current comparison outputs without any
system-specific extension:

- `paired-steps-delta-hist.png`
  Uses per-episode:
  - `outcome.total_steps_delta`

- `paired-final-vitality-delta-hist.png`
  Uses per-episode:
  - `outcome.final_vitality_delta`

- `episode-outcomes-strip.png`
  Uses per-episode:
  - `outcome.longer_survivor`

- `mismatch-vs-outcome.png`
  Uses per-episode:
  - `metrics.action_divergence.mismatch_rate`
  - `outcome.total_steps_delta`
  - or `outcome.final_vitality_delta`

- `trajectory-distance-distribution.png`
  Uses per-episode:
  - `metrics.position_divergence.mean_trajectory_distance`

These should work for any comparison artifact that already exists, regardless of
system type, as long as the comparison is replay-capable.

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

## System-specific plot inventory by current system

This section makes the proposal concrete for the systems that currently exist in
the codebase.

### `system_a`

Current status:

- no system-specific behavior-metrics extension
- no system-specific comparison extension
- visualization adapter exists, but not measurement-plot logic

Implication:

- `system_a` contributes **no dedicated measurement plots in v1**
- it still participates fully in all generic plots

### `system_aw`

Current system-specific metrics available:

- `system_aw_arbitration`
  - `curiosity_dominance_rate`
  - `mean_curiosity_weight`
  - `mean_hunger_weight`
  - `arbitrated_step_count`

- `system_aw_curiosity`
  - `mean_curiosity_activation`
  - `mean_spatial_novelty`
  - `mean_sensory_novelty`
  - `mean_composite_novelty`
  - `curiosity_pressure_rate`

- `system_aw_behavior`
  - `curiosity_led_move_rate`
  - `consume_under_curiosity_pressure_rate`
  - `movement_step_rate`
  - `consume_step_rate`

- `system_aw_world_model`
  - `world_model_unique_cells`
  - `mean_visit_count_at_current`
  - `world_model_revisit_ratio`

Current comparison-specific metrics:

- none beyond the generic comparison layer

Proposed `system_aw` measurement plots:

- `aw-curiosity-profile.png`
  - spatial vs sensory vs composite novelty across experiments

- `aw-arbitration-balance.png`
  - mean hunger weight vs mean curiosity weight

- `aw-curiosity-pressure-vs-outcome.png`
  - curiosity pressure rate vs survival or vitality

- `aw-world-model-profile.png`
  - world model unique cells vs revisit ratio

Interpretive role:

- explain why `A+W` changes exploration and arbitration across worlds or series

### `system_c`

Current system-specific metrics available:

- `system_c_prediction`
  - `mean_prediction_error`
  - `signed_prediction_error`
  - `confidence_trace_mean`
  - `frustration_trace_mean`
  - `prediction_modulation_strength`
  - `prediction_step_count`

Current comparison-specific analysis available:

- `system_c_prediction`
  - `prediction_active_step_count`
  - `prediction_active_step_rate`
  - `top_action_changed_by_modulation_count`
  - `top_action_changed_by_modulation_rate`
  - `ambiguous_top_action_count`
  - `mean_modulation_delta`

Proposed `system_c` measurement plots:

- `c-prediction-error-profile.png`
  - mean prediction error vs signed prediction error

- `c-trace-balance.png`
  - confidence trace mean vs frustration trace mean

- `c-modulation-strength-vs-outcome.png`
  - prediction modulation strength vs survival/vitality

- `c-comparison-impact.png`
  - top-action-changed rate vs total steps delta or survival delta

Interpretive role:

- separate “prediction signal exists” from “prediction changed behavior” and
  from “prediction helped”

### `system_cw`

Current system-specific metrics available:

- `system_cw_prediction`
  - `prediction_step_count`
  - `feature_prediction_error_mean`
  - `hunger_prediction_error_mean`
  - `curiosity_prediction_error_mean`
  - `hunger_signed_prediction_error`
  - `curiosity_signed_prediction_error`
  - `mean_novelty_weight`
  - `movement_prediction_step_rate`

- `system_cw_traces`
  - hunger/curiosity confidence and frustration trace means
  - hunger/curiosity trace balances
  - `trace_divergence_mean`
  - nonzero trace rates

- `system_cw_modulation`
  - hunger/curiosity modulation strength
  - modulation divergence
  - reinforcement/suppression rates

- `system_cw_arbitration`
  - mean hunger weight
  - mean curiosity weight
  - curiosity dominance rate
  - mean curiosity activation
  - curiosity pressure rate
  - prediction-weighted curiosity/hunger pressure

- `system_cw_curiosity`
  - mean spatial/sensory/composite novelty
  - curiosity-led move rate
  - consume-under-curiosity-pressure rate
  - novel move yield/success

- `system_cw_world_model`
  - unique cells
  - mean visit count at current
  - revisit ratio

- `system_cw_prediction_impact`
  - behavioral prediction impact rate
  - prediction changed top action rate
  - prediction changed arbitrated margin
  - nonmove curiosity penalty rate
  - counterfactual hunger/curiosity modulation impact

Current comparison-specific analysis available:

- `system_cw_comparison`
  - `comparison_scope`
  - `aligned_steps`
  - `mean_hunger_weight_delta`
  - `mean_curiosity_weight_delta`
  - `mean_curiosity_activation_delta`
  - `mean_composite_novelty_delta`
  - `mean_visit_count_delta`

Proposed `system_cw` measurement plots:

- `prediction-impact-vs-survival.png`
  - uses `behavioral_prediction_impact_rate`

- `modulation-strength-vs-performance.png`
  - uses hunger/curiosity modulation strength

- `prediction-error-profile.png`
  - grouped per experiment over feature/hunger/curiosity prediction error means

- `curiosity-hunger-weight-plane.png`
  - uses mean hunger vs mean curiosity weight

- `cw-trace-balance-profile.png`
  - hunger/curiosity confidence-frustration balance across experiments

- `cw-comparison-deltas.png`
  - uses `system_cw_comparison` deltas against the reference system

Interpretive role:

- this is the richest current target for system-specific measurement plots
- it should become the reference implementation for the extension mechanism

## Proposed v1 generic plot set

To keep the first milestone focused, the generic renderer should be required to
support at least:

### Series-level

- `survival-rates.png`
- `paired-survival-counts.png`
- `trajectory-vs-survival.png`
- `efficiency-vs-survival.png`
- `series-progression.png`

### Per-experiment

- `paired-steps-delta-hist.png`
- `paired-final-vitality-delta-hist.png`
- `episode-outcomes-strip.png`
- `mismatch-vs-outcome.png`
- `trajectory-distance-distribution.png`

## Proposed v1 system-specific plot set

To keep the first extension milestone realistic:

- `system_a`
  - none
- `system_aw`
  - 2-3 initial plots
- `system_c`
  - 2-3 initial plots
- `system_cw`
  - full first-class implementation

This reflects current practical value:

- `system_cw` is the strongest current use case
- `system_aw` and `system_c` should participate, but can start smaller

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

The intended design is **two-layered**:

1. a standalone plot-rendering service and CLI command
2. optional integration into `run-series` as a convenience layer

This keeps plot generation reusable and re-runnable, while still allowing
series execution to produce visual artifacts automatically.

### Primary mechanism: standalone rendering

The core capability should be:

- render plots from already existing series artifacts

This should work even when:

- the series was executed earlier
- plot logic has changed since the run
- new system-specific plot extensions were added later
- plots need to be regenerated after a bugfix

Desired future command:

- `axis workspaces render-series-plots <workspace> --series <series-id>`

This command should:

1. read the existing series results, comparisons, and aggregate summaries
2. generate or regenerate all relevant plot artifacts
3. write them into the correct measurement directories

### Secondary mechanism: `run-series` convenience integration

After a successful `run-series`, AXIS may optionally invoke the same rendering
service automatically.

This should be treated as workflow convenience, not as the only path.

### Rendering timing

For the first version, plots should be rendered:

- **after the series completes**

and not after every single experiment during execution.

Reason:

- the most important plots are series-level aggregates
- rendering after each experiment would repeat work
- end-of-series rendering is simpler and more robust

Per-experiment plots may still be generated at that final stage, once all
artifacts are present.

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

### 1. Should automatic rendering be always-on in `run-series`?

Possible answer:

- first version: yes, or enabled by default, assuming required data exists

Alternative:

- configurable via workspace measurement workflow settings

The standalone render command should exist regardless.

### 2. Should plot generation failures fail the whole measurement workflow?

Preferred answer:

- no
- plot generation should be best-effort and separately reported

Reason:

- plot rendering should not invalidate already-computed experimental results

### 3. Should the standalone render command support partial regeneration?

Likely yes later, for example:

- series-level only
- per-experiment only
- system-specific only

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
