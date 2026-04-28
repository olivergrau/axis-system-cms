# System C+W -- Metrics Specification

**Status:** Draft  
**Scope:** system-specific behavioral metrics for `system_cw`  
**Related documents:** `spec.md`, `engineering-spec.md`, `work-packages.md`

---

## 1. Purpose

This document defines the intended system-specific metrics for `system_cw`.

The goal is to make three aspects of the system measurable:

1. dual-drive arbitration under predictive modulation
2. shared predictive memory with drive-specific trust dynamics
3. curiosity as novelty-weighted exploration yield rather than raw novelty alone

The metrics are split into two groups:

- metrics that are immediately implementable from the currently tracked
  `decision_data` and `trace_data`
- metrics that are desirable, but require additional trace or decision payloads
  to be measured robustly

This document is intentionally about metric semantics, not implementation.

---

## 2. Current Observable Surface

With the current `system_cw` runtime, the following categories are already
tracked in usable form:

- hunger and curiosity drive activations
- raw hunger and curiosity action contributions
- shared predictive context and feature vector
- hunger-side modulation details
- curiosity-side modulation details
- arbitration weights
- final combined scores
- world-model summary fields in transition traces
- shared predicted and observed feature vectors
- hunger-side predicted / actual outcome scalars
- curiosity-side predicted / actual outcome scalars
- hunger confidence / frustration updates
- curiosity confidence / frustration updates
- curiosity novelty weight on the realized action

This is already enough to support a meaningful first-wave metric set.

---

## 3. Immediate Metrics

These metrics should be considered first-wave targets because they are already
implementable from the currently tracked data.

### 3.1 `system_cw_arbitration`

These metrics describe how the dual-drive control structure behaves.

- `mean_hunger_weight`
  Mean of `arbitration.hunger_weight` across steps.
- `mean_curiosity_weight`
  Mean of `arbitration.curiosity_weight` across steps.
- `curiosity_dominance_rate`
  Fraction of steps where `curiosity_weight > hunger_weight`.
- `mean_curiosity_activation`
  Mean of `curiosity_drive.activation`.
- `curiosity_pressure_rate`
  Fraction of steps where `curiosity_weight * curiosity_activation > 0`.
- `prediction_weighted_curiosity_pressure`
  Mean of `curiosity_weight * curiosity_activation * novelty_weight`.
- `prediction_weighted_hunger_pressure`
  Mean of `hunger_weight * hunger_activation`.

Interpretation:

- these metrics tell us how often curiosity had room to matter
- and whether that room coincided with strong novelty-weighted predictive context

### 3.2 `system_cw_prediction`

These metrics describe prediction quality and predictive opportunity structure.

- `prediction_step_count`
  Number of steps with a predictive update payload.
- `feature_prediction_error_mean`
  Mean of `feature_error_positive + feature_error_negative`.
- `hunger_prediction_error_mean`
  Mean of hunger-side scalar error magnitude.
- `curiosity_prediction_error_mean`
  Mean of curiosity-side scalar error magnitude.
- `hunger_signed_prediction_error`
  Mean of `hunger.error_positive - hunger.error_negative`.
- `curiosity_signed_prediction_error`
  Mean of `curiosity.error_positive - curiosity.error_negative`.
- `mean_novelty_weight`
  Mean of curiosity-side `novelty_weight`.
- `movement_prediction_step_rate`
  Fraction of predictive-update steps whose action is a movement action.

Interpretation:

- these metrics distinguish feature-level predictive drift from drive-level
  outcome drift
- and reveal whether the predictive loop is mostly updating on exploration or
  on non-exploratory actions

### 3.3 `system_cw_modulation`

These metrics describe the behavioral effect of prediction before arbitration.

- `hunger_modulation_strength`
  Mean absolute difference between hunger raw scores and hunger modulated scores.
- `curiosity_modulation_strength`
  Mean absolute difference between curiosity raw scores and curiosity modulated
  scores.
- `mean_modulation_divergence`
  Mean absolute difference between hunger and curiosity modulation strengths in
  the same step.
- `hunger_reinforcement_rate`
  Fraction of hunger modulation factors greater than `1`.
- `hunger_suppression_rate`
  Fraction of hunger modulation factors less than `1`.
- `curiosity_reinforcement_rate`
  Fraction of curiosity modulation factors greater than `1`.
- `curiosity_suppression_rate`
  Fraction of curiosity modulation factors less than `1`.

Interpretation:

- these metrics expose whether the shared predictive memory yields aligned or
  diverging trust signals across the two drives

### 3.4 `system_cw_traces`

These metrics describe the learned local trust structure.

- `hunger_confidence_trace_mean`
  Mean hunger confidence value at updated context-action pairs.
- `hunger_frustration_trace_mean`
  Mean hunger frustration value at updated context-action pairs.
- `curiosity_confidence_trace_mean`
  Mean curiosity confidence value at updated context-action pairs.
- `curiosity_frustration_trace_mean`
  Mean curiosity frustration value at updated context-action pairs.
- `hunger_trace_balance`
  Mean of `hunger_confidence - hunger_frustration`.
- `curiosity_trace_balance`
  Mean of `curiosity_confidence - curiosity_frustration`.
- `trace_divergence_mean`
  Mean absolute difference between hunger and curiosity trace balance.
- `nonzero_hunger_trace_rate`
  Fraction of predictive steps where hunger confidence or frustration is
  non-zero.
- `nonzero_curiosity_trace_rate`
  Fraction of predictive steps where curiosity confidence or frustration is
  non-zero.

Interpretation:

- these metrics show whether hunger and curiosity build meaningfully different
  trust histories over the same predictive substrate

### 3.5 `system_cw_curiosity`

These metrics describe curiosity as a novelty-sensitive exploratory process.

- `mean_spatial_novelty`
  Mean of the per-step mean spatial novelty.
- `mean_sensory_novelty`
  Mean of the per-step mean sensory novelty.
- `mean_composite_novelty`
  Mean of the per-step mean composite novelty.
- `curiosity_led_move_rate`
  Fraction of steps with positive curiosity pressure that end in a movement
  action.
- `consume_under_curiosity_pressure_rate`
  Fraction of positive-curiosity-pressure steps that end in `consume`.
- `novel_move_yield_mean`
  Mean actual curiosity-side yield on movement actions.
- `novel_move_success_rate`
  Fraction of movement predictive steps with positive curiosity-side actual
  outcome.

Interpretation:

- these metrics distinguish raw novelty availability from successful
  novelty-weighted exploratory payoff

### 3.6 `system_cw_world_model`

These metrics preserve the A+W-style minimal world-model observability.

- `world_model_unique_cells`
  Mean number of unique visited cells per episode.
- `mean_visit_count_at_current`
  Mean current-cell visit count across steps.
- `world_model_revisit_ratio`
  Mean revisit ratio derived from final visit-count maps.

Interpretation:

- these metrics indicate whether predictive curiosity produces broader or more
  repetitive local exploration

---

## 4. Metrics Requiring Additional Trace Fields

These metrics are desirable, but should not be treated as first-wave
requirements because the current payload does not support them robustly.

### 4.1 `behavioral_prediction_impact_rate`

Desired meaning:

- fraction of steps where prediction changed the effective winning action or its
  rank ordering

Why it is not yet robustly measurable:

- current traces contain the final combined scores after modulation
- but they do not contain the counterfactual combined scores without prediction

Required additional payload:

- `combined_scores_without_prediction`
  or
- `selected_action_without_prediction`

Preferred field:

- `prediction.counterfactual_combined_scores`

### 4.2 `prediction_changed_top_action_rate`

Desired meaning:

- fraction of steps where the top-ranked action under prediction differs from
  the top-ranked action without prediction

Why it is not yet robustly measurable:

- same counterfactual gap as above

Required additional payload:

- counterfactual combined-score vector before predictive modulation

### 4.3 `prediction_changed_arbitrated_margin`

Desired meaning:

- average change in the gap between the selected action and the runner-up caused
  by prediction

Why it is not yet robustly measurable:

- final combined scores are present
- counterfactual no-prediction combined scores are not

Required additional payload:

- `combined_scores_without_prediction`

### 4.4 `nonmove_curiosity_penalty_rate`

Desired meaning:

- fraction of non-movement steps where curiosity-side suppressive handling was
  specifically engaged under relevant curiosity motivation

Why it is not yet robustly measurable:

- we can infer non-movement action and curiosity activation
- but we do not explicitly log whether the v1 non-movement curiosity branch was
  taken as a named semantic event

Required additional payload:

- explicit boolean such as `curiosity.used_nonmove_penalty_rule`

### 4.5 `counterfactual_hunger_modulation_impact`

Desired meaning:

- effect of hunger-side predictive modulation on final action competition after
  arbitration

Why it is not yet robustly measurable:

- hunger-side modulated scores are present
- but the contribution of hunger modulation to final combined ranking cannot be
  cleanly isolated without a counterfactual where only the hunger modulation is
  removed

Required additional payload:

- `combined_scores_without_hunger_prediction`

### 4.6 `counterfactual_curiosity_modulation_impact`

Desired meaning:

- effect of curiosity-side predictive modulation on final action competition

Why it is not yet robustly measurable:

- same issue as above, but for the curiosity branch

Required additional payload:

- `combined_scores_without_curiosity_prediction`

---

## 5. Recommended Additional Trace Fields

If the goal is to unlock the second metric tier later, the following additional
fields would provide the best value for the least conceptual disruption.

### 5.1 Decision-level counterfactuals

Recommended additions under `decision_data["prediction"]`:

- `counterfactual_hunger_scores`
- `counterfactual_curiosity_scores`
- `counterfactual_combined_scores`
- `counterfactual_selected_action`

These should represent the no-prediction case while keeping the same raw drives,
same arbitration function, and same policy settings.

### 5.2 Transition-level branch markers

Recommended additions under `trace_data["prediction"]["curiosity"]`:

- `used_nonmove_penalty_rule: bool`
- `is_movement_action: bool`

These fields would make curiosity-side semantics more explicit and reduce the
need for implicit inference in metric code.

---

## 6. Recommended First-Wave Metric Set

If we want a lean but high-value first implementation, the following metrics
should be prioritized.

### 6.1 Core predictive divergence

- `hunger_prediction_error_mean`
- `curiosity_prediction_error_mean`
- `hunger_modulation_strength`
- `curiosity_modulation_strength`
- `mean_modulation_divergence`
- `hunger_trace_balance`
- `curiosity_trace_balance`
- `trace_divergence_mean`

### 6.2 Curiosity-specific exploratory value

- `mean_novelty_weight`
- `mean_composite_novelty`
- `curiosity_led_move_rate`
- `novel_move_yield_mean`
- `novel_move_success_rate`

### 6.3 Arbitration and exploration regime

- `mean_hunger_weight`
- `mean_curiosity_weight`
- `curiosity_dominance_rate`
- `world_model_unique_cells`
- `world_model_revisit_ratio`

This set is already enough to answer the first important empirical questions:

- does C+W actually learn different local trust profiles for hunger and curiosity?
- does prediction meaningfully reshape the two drives differently?
- does curiosity remain behaviorally exploratory rather than collapsing into
  raw novelty or non-movement suppression?

---

## 7. Summary

The immediate metric set is already strong enough to support useful first-wave
analysis of `system_cw`.

The main thing that is *not* yet observable robustly is the counterfactual
behavioral impact of prediction on final action choice. That requires
additional decision payloads rather than a new metric formula alone.

Therefore the metric rollout should proceed in two phases:

1. implement the immediate metrics listed in Section 3
2. only then decide whether the extra counterfactual fields from Section 5 are
   worth adding to support the second-wave metrics in Section 4
