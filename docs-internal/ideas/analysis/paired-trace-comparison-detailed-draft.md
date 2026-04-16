# AXIS - Paired Trace Comparison

## Detailed Draft for a Spec-Oriented Comparison Model

---

## 1. Purpose

This document refines the initial paired trace comparison idea into a more specification-oriented draft.

Its purpose is to define a stable conceptual basis for comparing two AXIS episode traces under matched conditions.

The primary motivating use case remains:

- `System A` as reference
- `System C` as candidate

But the model is intended to generalize beyond this specific pair.

This document is still not a final specification.

It is a detailed draft intended to prepare a later spec by fixing:

- comparison identity
- validation rules
- alignment rules
- required metric families
- extension points for system-specific analysis

---

## 2. Core Principle

A paired trace comparison is a comparison between two episode traces that were generated under the same environmental conditions and differ only on the system side.

Conceptually:

```text
reference episode trace
+ candidate episode trace
+ strict pairing validation
-> comparison object
-> generic metrics
-> optional system-specific extensions
```

The comparison object is an analysis artifact.

It is not part of the replay contract itself.

---

## 3. Comparison Direction

Paired comparison should be modeled asymmetrically.

The two traces should be named:

- `reference_trace`
- `candidate_trace`

This does not imply that every metric is mathematically directional.

Many metrics remain symmetric in value.

However, the directional naming is useful because most comparisons in practice are interpretive comparisons of the form:

- baseline versus modified system
- older system versus newer system
- control versus intervention

Examples:

- `System A` as reference, `System C` as candidate
- `System C` with default prediction as reference, stronger prediction as candidate

---

## 4. Pairing Identity

### 4.1 Primary Identity

The primary pairing identity should be:

- `episode_seed`

This should become the canonical identifier for pairing corresponding episodes across runs.

### 4.2 Transitional Identity

Until `episode_seed` is explicitly persisted at episode level, pairing may also be established through:

- `episode_index`
- run-level `base_seed`
- deterministic AXIS seed derivation rule

This is a transitional allowance, not the ideal long-term state.

### 4.3 Design Rule

The comparison model should therefore support both:

- explicit `episode_seed`
- derived pairing through run seed plus episode index

But future specifications should treat explicit `episode_seed` as the normative form.

---

## 5. Strict Pairing Validation

Paired comparison should be strict.

If the traces do not satisfy the pairing contract, the comparison must fail rather than degrade into a weak heuristic comparison.

### 5.1 Required Equality Constraints

The following must match exactly:

- `world_type`
- `world_config`
- agent start position
- episode seed identity

If seed identity is not explicit in the trace, the comparison process must validate it through deterministic derivation from run metadata.

### 5.2 Required Trace Compatibility

The following must also hold:

- both traces must contain valid AXIS episode trace structure
- both traces must be replay-compatible
- both traces must expose step ordering from `timestep = 0`

### 5.3 Allowed Differences

The following may differ:

- `system_type`
- `system_config`
- episode length
- termination reason
- all system-internal decision and transition signals

### 5.4 Validation Outcome

Validation should produce one of two outcomes:

- `valid_paired_comparison`
- `invalid_paired_comparison`

Invalid paired comparisons should report explicit reasons.

Example reasons:

- `world_config_mismatch`
- `episode_seed_mismatch`
- `start_position_mismatch`
- `trace_schema_mismatch`

---

## 6. Alignment Rule

Stepwise comparison must be performed only on the shared prefix of both episodes.

Define:

- `n_ref` = number of steps in reference trace
- `n_cand` = number of steps in candidate trace
- `n_align = min(n_ref, n_cand)`

Then all stepwise metrics operate only on timesteps:

$$
t \in \{0, \dots, n_{\text{align}} - 1\}
$$

### 6.1 No Padding

The shorter trace must not be padded with synthetic steps.

### 6.2 Post-Alignment Difference

Differences beyond the shared prefix should be represented separately in a termination and outcome block.

This preserves methodological clarity:

- shared-prefix metrics describe comparable realized behavior
- post-prefix metrics describe unequal continuation or earlier termination

---

## 7. Comparison Object

The detailed draft proposes a conceptual comparison object with five sections.

### 7.1 Identity Section

This section records what is being compared.

Suggested fields:

- `reference_system_type`
- `candidate_system_type`
- `reference_run_id`
- `candidate_run_id`
- `reference_episode_index`
- `candidate_episode_index`
- `episode_seed`
- `pairing_mode`

Where:

- `pairing_mode` is one of:
  - `explicit_episode_seed`
  - `derived_seed_from_index`

### 7.2 Validation Section

This section records pairing validity.

Suggested fields:

- `is_valid_pair`
- `validation_errors`
- `world_type_match`
- `world_config_match`
- `start_position_match`
- `episode_seed_match`

### 7.3 Generic Metrics Section

This section contains system-agnostic comparison metrics.

### 7.4 Outcome Section

This section compares episode-level outcomes and post-prefix facts.

### 7.5 Extension Section

This section contains optional system-specific analysis blocks.

Suggested field:

- `system_specific_analysis`

This field should behave conceptually like visualization extensions:

- generic comparison core
- optional system-contributed comparison blocks

---

## 8. Required Generic Metrics for v1

The following metric families should be treated as required in the first spec-oriented version.

### 8.1 Action Divergence

Required fields:

- `first_action_divergence_step`
- `action_mismatch_count`
- `action_mismatch_rate`

Definitions:

- `first_action_divergence_step`:
  first aligned timestep at which selected actions differ, or `null` if none
- `action_mismatch_count`:
  number of aligned timesteps with different selected action
- `action_mismatch_rate`:

$$
\frac{\text{action mismatch count}}{n_{\text{align}}}
$$

if `n_align > 0`, otherwise `0`

### 8.2 Position Divergence

Required fields:

- `first_position_divergence_step`
- `trajectory_distance_series`
- `mean_trajectory_distance`
- `max_trajectory_distance`

Initial distance proposal:

- Manhattan distance between agent positions at aligned timestep `t`

For each aligned timestep:

$$
d_{\text{traj}}(t) = |x_r(t) - x_c(t)| + |y_r(t) - y_c(t)|
$$

And:

$$
\bar d_{\text{traj}} = \frac{1}{n_{\text{align}}}\sum_{t=0}^{n_{\text{align}}-1} d_{\text{traj}}(t)
$$

### 8.3 Vitality Divergence

Required fields:

- `vitality_difference_series`
- `mean_absolute_vitality_difference`
- `max_absolute_vitality_difference`

For aligned timesteps:

$$
\Delta v(t) = v_r(t) - v_c(t)
$$

The mean absolute vitality difference is:

$$
\frac{1}{n_{\text{align}}}\sum_{t=0}^{n_{\text{align}}-1} |\Delta v(t)|
$$

### 8.4 Action Usage Statistics

This metric family was added explicitly because action frequency differences are behaviorally meaningful even when divergence timing alone is not.

Required fields:

- `reference_action_counts`
- `candidate_action_counts`
- `reference_most_used_action`
- `candidate_most_used_action`
- `action_count_deltas`

The action vocabulary should be taken from the aligned action space of the compared systems.

For A-vs-C this is expected to be:

- `up`
- `down`
- `left`
- `right`
- `consume`
- `stay`

### 8.5 Alignment Summary

Required fields:

- `reference_total_steps`
- `candidate_total_steps`
- `aligned_steps`
- `reference_extra_steps`
- `candidate_extra_steps`

where:

- `reference_extra_steps = max(0, n_ref - n_align)`
- `candidate_extra_steps = max(0, n_cand - n_align)`

---

## 9. Outcome Comparison Block

The outcome block should summarize the whole episode result, not only the aligned prefix.

Required fields:

- `reference_termination_reason`
- `candidate_termination_reason`
- `reference_final_vitality`
- `candidate_final_vitality`
- `final_vitality_delta`
- `reference_total_steps`
- `candidate_total_steps`
- `total_step_delta`

This block should also provide an interpretable summary of which trace outlasted the other.

Suggested field:

- `longer_survivor`

Possible values:

- `reference`
- `candidate`
- `equal`

---

## 10. Time Series as First-Class Data

Time series should be treated as primary comparison outputs, not merely intermediate calculation artifacts.

This is important for two reasons:

- later visualization
- later diagnostic interpretation

### 10.1 Required Time Series in the Detailed Draft

The draft should already assume these series exist:

- `trajectory_distance_series`
- `vitality_difference_series`
- optional later `action_match_series`

### 10.2 Aggregates Remain Secondary

Aggregated values such as means and maxima remain useful, but they should be derived from preserved time series rather than replacing them.

---

## 11. System-Specific Extension Model

The comparison core should remain generic.

System-specific analysis should be attached through optional extension blocks.

### 11.1 Core Principle

The generic comparison model must not hard-code system-specific semantics such as:

- prediction
- curiosity
- scan confidence
- visit maps

Instead, systems should be allowed to contribute comparison-specific analysis blocks in a dedicated extension area.

### 11.2 Conceptual Shape

Suggested structure:

```text
system_specific_analysis = {
  "reference_system": ...,
  "candidate_system": ...,
  "shared_extensions": ...,
  "candidate_only_extensions": ...
}
```

The exact structure can be finalized later.

The important point is that the extension mechanism is explicit and separable from the generic metrics block.

### 11.3 Relation to Visualization

The intended design philosophy is similar to the visualization system:

- generic host structure
- system-owned interpretation blocks

This keeps the analysis layer extensible without contaminating the generic core.

---

## 12. First System C Extension

For `System C`, the first comparison-specific extension should focus on predictive influence.

### 12.1 Required Candidate Metrics for the Draft

Suggested fields:

- `prediction_active_step_count`
- `prediction_active_step_rate`
- `top_action_changed_by_modulation_count`
- `top_action_changed_by_modulation_rate`
- `mean_modulation_delta`

### 12.2 Working Definitions

#### Prediction-Active Step

A step counts as prediction-active if modulated scores differ from raw action contributions for at least one action beyond a fixed numeric tolerance.

#### Top-Action Changed by Modulation

A step counts as top-action-changed if:

- the highest-scoring action under raw action contributions
  differs from
- the highest-scoring action under modulated scores

This is one of the most important mechanism metrics because it distinguishes:

- weak score perturbation
- actual decision-space restructuring

#### Mean Modulation Delta

An initial working definition may be:

- the mean absolute difference between raw and modulated action scores over all aligned candidate steps and all actions

For action set `A` and aligned steps `t`:

$$
\Delta_{\mu}(t, a) = |\phi_{\text{raw}}(t, a) - \phi_{\text{mod}}(t, a)|
$$

and

$$
\bar{\Delta}_{\mu}
= \frac{1}{n_{\text{align}} |A|}
\sum_{t=0}^{n_{\text{align}}-1}\sum_{a \in A}\Delta_{\mu}(t, a)
$$

This is not yet the only possible definition, but it is a clear and workable one for the detailed draft.

---

## 13. Current Trace Fit

The current AXIS traces are already sufficient for a first implementation of the generic paired comparison core.

### 13.1 Already Supported by Existing Traces

Current traces already support:

- action divergence
- position divergence
- vitality divergence
- action usage statistics
- step alignment
- outcome comparison
- basic `System C` raw-versus-modulated score analysis

### 13.2 Not Yet Ideal

The current trace model is not yet ideal for deeper mechanism analysis because it does not explicitly persist:

- per-action modulation factor `mu`
- per-action frustration values
- per-action confidence values
- explicit episode seed on episode trace

These should therefore be treated as future trace enhancement candidates, not as assumptions of the first comparison spec.

---

## 14. Error Handling Semantics

The detailed draft should treat comparison failure as a first-class outcome.

Suggested result modes:

- `comparison_succeeded`
- `comparison_failed_validation`

This allows downstream tools to distinguish:

- a successful comparison with meaningful metrics
- an invalid pair that must not be interpreted

This is preferable to silently computing partial or weakly valid results.

---

## 15. Open Questions for the Next Spec Step

This detailed draft resolves the main conceptual questions, but a later specification should still decide the following with more precision.

### 15.1 Tolerance Rules

Where exact equality is too strict for floating point series, which tolerances should be normative?

This applies especially to:

- top-action change under ties or near-ties
- prediction-active detection
- derived modulation deltas

### 15.2 Cross-System Action Space Assumption

Should paired comparison v1 require identical action spaces, or only comparable selected-action labels?

For A-vs-C, action spaces match naturally.

For broader future use, this should be made explicit.

### 15.3 Series Storage Shape

Should time series be stored as:

- arrays only
- arrays plus per-step labeled objects
- or arrays in the comparison object and richer per-step forms only in visualization adapters

### 15.4 Interpretation Layer

Should the comparison object eventually contain only raw metrics, or also short derived interpretations such as:

- `candidate diverged early`
- `candidate was more movement-heavy`
- `prediction was frequently decision-relevant`

The current draft does not require textual interpretations.

That should remain a separate decision.

---

## 16. Recommended Next Step

The next artifact after this detailed draft should be a proper versioned specification for paired trace comparison.

That specification should define:

- the exact comparison object schema
- mandatory and optional fields
- exact metric definitions
- validation behavior
- extension registration semantics for systems

The most important principle to preserve is:

> strict paired validation, generic comparison core, explicit system-specific extensions

---

## 17. Summary

This detailed draft fixes the main design choices for a first spec-oriented paired comparison model:

- primary pairing identity is `episode_seed`
- stepwise analysis uses shared-prefix alignment only
- comparison is asymmetrically modeled as reference versus candidate
- paired validation is strict
- time series are first-class outputs
- generic metrics and system-specific extensions are explicitly separated

This provides a stable conceptual foundation for a later specification of A-vs-C comparison and for more general future system comparisons in AXIS.
