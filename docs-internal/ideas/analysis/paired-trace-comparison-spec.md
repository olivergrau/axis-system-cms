# AXIS - Paired Trace Comparison Specification

## Version 1 Draft Specification

---

## 1. Purpose

This document defines version 1 of the AXIS **paired trace comparison** specification.

The purpose of paired trace comparison is to provide a strict, replay-based analysis model for comparing two AXIS episode traces under matched environmental conditions.

This specification defines:

- what qualifies as a valid paired comparison
- how episode traces are aligned
- which generic metrics are required
- how action-space overlap is handled
- how system-specific analysis extensions attach to the generic comparison result

This specification does not define:

- implementation architecture
- UI or visualization design
- persistence format for comparison reports
- statistical multi-run aggregation

---

## 2. Scope

This specification applies to:

- comparison of two AXIS episode traces
- comparison at the single-episode level
- strict paired comparison under matched conditions

This specification does not yet cover:

- batch comparison across many paired episodes
- run-level statistical significance
- comparison across non-replay-compatible trace formats
- extension registration mechanics

---

## 3. Normative Terms

The terms **must**, **must not**, **should**, and **may** are to be interpreted normatively.

---

## 4. Core Model

A paired trace comparison is an analysis object constructed from:

- one `reference_trace`
- one `candidate_trace`
- a strict validation process
- a shared-prefix alignment
- a required set of generic metrics
- an optional set of system-specific analysis extensions

The comparison is asymmetric in structure:

- the reference trace is the baseline trace
- the candidate trace is the compared trace

This asymmetry is semantic and interpretive.

It does not imply that every metric is directional in mathematical value.

---

## 5. Inputs

### 5.1 Required Inputs

A paired comparison requires:

- one valid AXIS episode trace as `reference_trace`
- one valid AXIS episode trace as `candidate_trace`

### 5.2 Optional Associated Metadata

The comparison process may additionally use:

- run metadata
- run configuration
- experiment metadata

These may be required when episode seed identity is not directly persisted in the episode trace.

---

## 6. Pairing Identity

### 6.1 Primary Pairing Identity

The primary identity for pairing must be:

- `episode_seed`

If both traces expose explicit episode seed identity, that identity must be used.

### 6.2 Transitional Pairing Identity

If explicit episode seed identity is not available at episode level, pairing may be derived from:

- episode index
- run-level base seed
- the deterministic AXIS episode seed derivation rule

The deterministic derivation rule is:

$$
\text{episode_seed}(i) = \text{base_seed} + i
$$

where `i` is the zero-based episode offset within the run.

### 6.3 Pairing Mode

The comparison result must record one of the following pairing modes:

- `explicit_episode_seed`
- `derived_seed_from_index`

---

## 7. Strict Validation

Paired comparison must be strict.

If the required pairing conditions do not hold, comparison must fail.

### 7.1 Required Equality Conditions

The following properties must match exactly:

- `world_type`
- `world_config`
- agent start position
- episode seed identity

### 7.2 Required Structural Conditions

The following must also hold:

- both traces must conform to the AXIS episode replay contract
- both traces must expose step ordering beginning at timestep `0`
- both traces must be internally consistent episode traces

### 7.3 Allowed Differences

The following may differ:

- `system_type`
- system configuration
- episode length
- termination reason
- step content
- system-specific trace payloads

### 7.4 Invalid Comparison Outcome

If validation fails, the comparison must produce:

- `is_valid_pair = false`
- one or more explicit validation errors

The metric sections must not be treated as valid analytical outputs in that case.

### 7.5 Standard Validation Error Codes

The comparison model must support at least the following validation error codes:

- `world_type_mismatch`
- `world_config_mismatch`
- `start_position_mismatch`
- `episode_seed_mismatch`
- `trace_schema_mismatch`
- `invalid_reference_trace`
- `invalid_candidate_trace`

---

## 8. Alignment

### 8.1 Shared-Prefix Alignment

All stepwise comparison metrics must be computed only on the shared prefix of both traces.

Let:

- `n_ref` = number of steps in the reference trace
- `n_cand` = number of steps in the candidate trace
- `n_align = min(n_ref, n_cand)`

Then aligned timesteps are:

$$
t \in \{0, \dots, n_{\text{align}} - 1\}
$$

### 8.2 No Padding

The shorter episode must not be padded with synthetic or inferred steps.

### 8.3 Post-Prefix Differences

Differences beyond the aligned prefix must be represented only in:

- alignment summary fields
- outcome comparison fields

---

## 9. Comparison Tolerances

The comparison specification defines two global tolerance parameters.

### 9.1 Equality Tolerance

The default equality tolerance must be:

$$
\epsilon = 10^{-9}
$$

This tolerance applies to direct floating-point equality checks.

### 9.2 Ranking Tolerance

The default ranking tolerance must be:

$$
\epsilon_{\text{rank}} = 10^{-6}
$$

This tolerance applies to:

- top-action comparisons
- tie detection
- near-equal score ranking analysis

### 9.3 Tie Rule

Two values `x` and `y` must be treated as tied if:

$$
|x - y| \le \epsilon_{\text{rank}}
$$

---

## 10. Ambiguity and Special States

The comparison model must not silently coerce ambiguous or unavailable results to `false`, `0`, or any other default value.

### 10.1 Allowed Special States

The specification allows at least the following special states:

- `null`
- `not_applicable`
- `ambiguous_due_to_tie`
- `missing_required_signal`

### 10.2 Use of Ambiguous State

If a ranking-based metric cannot be decided because of a tie or near-tie under the ranking tolerance, the result should be:

- `ambiguous_due_to_tie`

---

## 11. Action-Space Comparison Rules

This specification does not require identical action spaces.

### 11.1 Shared Action Basis

The generic paired comparison must be defined over the shared action-label intersection of both systems.

Let:

- `A_ref` = action-label set of reference trace
- `A_cand` = action-label set of candidate trace
- `A_shared = A_ref \cap A_cand`

Then all generic action-comparison metrics must operate only on `A_shared`.

### 11.2 Minimum Requirement

If:

$$
|A_{\text{shared}}| = 0
$$

then paired comparison must fail validation.

Validation must return:

- `action_space_no_shared_labels`

### 11.3 Non-Shared Actions

Actions that exist only in one system:

- must not participate in direct paired action metrics
- may appear in one-sided action usage statistics
- may appear in system-specific analysis extensions

### 11.4 Action Usage Reporting

The comparison result should distinguish between:

- shared-action usage statistics
- full per-system action usage statistics

This preserves generic comparability while retaining descriptive completeness.

---

## 12. Comparison Result Structure

The paired comparison result must contain the following top-level sections.

### 12.1 Identity Section

Required fields:

- `reference_system_type`
- `candidate_system_type`
- `reference_run_id`
- `candidate_run_id`
- `reference_episode_index`
- `candidate_episode_index`
- `episode_seed`
- `pairing_mode`

### 12.2 Validation Section

Required fields:

- `is_valid_pair`
- `validation_errors`
- `world_type_match`
- `world_config_match`
- `start_position_match`
- `episode_seed_match`
- `shared_action_labels`

### 12.3 Alignment Section

Required fields:

- `reference_total_steps`
- `candidate_total_steps`
- `aligned_steps`
- `reference_extra_steps`
- `candidate_extra_steps`

### 12.4 Generic Metrics Section

Required fields are defined in Sections 13 through 17.

### 12.5 Outcome Section

Required fields are defined in Section 18.

### 12.6 System-Specific Extension Section

Optional field:

- `system_specific_analysis`

This field may be empty or omitted if no system-specific extensions are available.

---

## 13. Generic Metric Family: Action Divergence

The comparison result must contain the following action divergence fields.

### 13.1 Required Fields

- `first_action_divergence_step`
- `action_mismatch_count`
- `action_mismatch_rate`

### 13.2 Definitions

`first_action_divergence_step` is:

- the smallest aligned timestep at which the selected action label differs
- `null` if no aligned action divergence occurs

`action_mismatch_count` is:

- the number of aligned timesteps for which the selected action labels differ

`action_mismatch_rate` is:

$$
\frac{\text{action mismatch count}}{n_{\text{align}}}
$$

if `n_align > 0`, otherwise `0`

---

## 14. Generic Metric Family: Position Divergence

The comparison result must contain the following position divergence fields.

### 14.1 Required Fields

- `first_position_divergence_step`
- `trajectory_distance_series`
- `mean_trajectory_distance`
- `max_trajectory_distance`

### 14.2 Distance Definition

Version 1 must use Manhattan distance between aligned agent positions.

For aligned timestep `t`:

$$
d_{\text{traj}}(t) = |x_r(t) - x_c(t)| + |y_r(t) - y_c(t)|
$$

### 14.3 Aggregates

The mean trajectory distance is:

$$
\bar d_{\text{traj}} = \frac{1}{n_{\text{align}}}\sum_{t=0}^{n_{\text{align}}-1} d_{\text{traj}}(t)
$$

if `n_align > 0`, otherwise `0`

The maximum trajectory distance is:

$$
\max_t d_{\text{traj}}(t)
$$

over aligned timesteps, otherwise `0`

### 14.4 First Position Divergence

`first_position_divergence_step` is:

- the first aligned timestep at which the aligned positions differ
- `null` if no aligned position divergence occurs

---

## 15. Generic Metric Family: Vitality Divergence

The comparison result must contain the following vitality divergence fields.

### 15.1 Required Fields

- `vitality_difference_series`
- `mean_absolute_vitality_difference`
- `max_absolute_vitality_difference`

### 15.2 Difference Definition

For aligned timestep `t`:

$$
\Delta v(t) = v_r(t) - v_c(t)
$$

### 15.3 Aggregate Definitions

The mean absolute vitality difference is:

$$
\frac{1}{n_{\text{align}}}\sum_{t=0}^{n_{\text{align}}-1} |\Delta v(t)|
$$

if `n_align > 0`, otherwise `0`

The maximum absolute vitality difference is:

$$
\max_t |\Delta v(t)|
$$

over aligned timesteps, otherwise `0`

---

## 16. Generic Metric Family: Action Usage Statistics

The comparison result must contain action usage statistics.

### 16.1 Required Fields

- `reference_action_counts`
- `candidate_action_counts`
- `reference_most_used_action`
- `candidate_most_used_action`
- `action_count_deltas`

### 16.2 Reporting Rule

`reference_action_counts` and `candidate_action_counts` may include actions that are not shared.

`action_count_deltas` must be defined only on shared action labels.

### 16.3 Most Used Action Rule

If one action has strictly greater usage count than every other action in that system, it must be reported as the most used action.

If the most-used action is not unique within ranking tolerance or count equality, the result should be:

- `ambiguous_due_to_tie`

---

## 17. Generic Metric Family: Time Series Representation

Time series must be treated as first-class comparison outputs.

### 17.1 Required Representation

In version 1, required series must be represented as simple arrays in timestep order.

Examples:

- `trajectory_distance_series`
- `vitality_difference_series`

### 17.2 Timestep Basis

All series must use the persisted episode timestep as their index basis.

No secondary internal indexing scheme may replace the episode timestep for v1 comparison output.

---

## 18. Outcome Comparison Block

The outcome block must summarize whole-episode outcomes.

### 18.1 Required Fields

- `reference_termination_reason`
- `candidate_termination_reason`
- `reference_final_vitality`
- `candidate_final_vitality`
- `final_vitality_delta`
- `reference_total_steps`
- `candidate_total_steps`
- `total_step_delta`
- `longer_survivor`

### 18.2 Delta Definitions

`final_vitality_delta` is:

$$
v^{\text{final}}_r - v^{\text{final}}_c
$$

`total_step_delta` is:

$$
n_{\text{ref}} - n_{\text{cand}}
$$

### 18.3 Longer Survivor Field

`longer_survivor` must take one of:

- `reference`
- `candidate`
- `equal`

where:

- `reference` means `n_ref > n_cand`
- `candidate` means `n_cand > n_ref`
- `equal` means `n_ref = n_cand`

---

## 19. System-Specific Extensions

The paired comparison core must remain generic.

System-specific analysis must be attached only through explicit extension blocks.

### 19.1 Extension Placement

System-specific analysis must be attached under:

- `system_specific_analysis`

### 19.2 Extension Naming

Extensions should use explicit namespaced keys.

Examples:

- `system_c_prediction`
- `system_b_signal_scan`

### 19.3 Generic-Core Rule

The generic comparison model must not hard-code semantics of:

- prediction
- curiosity
- scan dynamics
- visit memory

These belong only in system-specific extensions.

### 19.4 Registration

This version of the specification does not define extension registration mechanics.

Only extension placement and conceptual role are specified.

---

## 20. System C Extension v1

If a `System C`-specific comparison extension is produced, it should appear under:

- `system_specific_analysis.system_c_prediction`

### 20.1 Required Extension Fields

If the extension is present, it should contain at least:

- `prediction_active_step_count`
- `prediction_active_step_rate`
- `top_action_changed_by_modulation_count`
- `top_action_changed_by_modulation_rate`
- `mean_modulation_delta`

### 20.2 Prediction-Active Step

A candidate step counts as prediction-active if at least one action score differs between:

- raw action contributions
- modulated action scores

by more than `epsilon`.

### 20.3 Top-Action Changed by Modulation

A candidate step counts as top-action-changed if:

- the unique top action under raw action scores
  differs from
- the unique top action under modulated action scores

If either ranking is ambiguous under `ranking_epsilon`, the result for that step should be:

- `ambiguous_due_to_tie`

Such ambiguous steps should not be counted as positive changes.

They may be tracked separately in a future extension version.

### 20.4 Mean Modulation Delta

For shared candidate action set `A` and aligned timesteps:

$$
\Delta_{\mu}(t, a) = |\phi_{\text{raw}}(t, a) - \phi_{\text{mod}}(t, a)|
$$

Then:

$$
\bar{\Delta}_{\mu}
= \frac{1}{n_{\text{align}} |A|}
\sum_{t=0}^{n_{\text{align}}-1}\sum_{a \in A}\Delta_{\mu}(t, a)
$$

if `n_align > 0` and `|A| > 0`, otherwise:

- `not_applicable`

---

## 21. Result Modes

The comparison process must distinguish at least two result modes:

- `comparison_succeeded`
- `comparison_failed_validation`

If validation fails:

- `comparison_failed_validation` must be returned
- metric blocks must not be interpreted as valid comparison results

---

## 22. Non-Goals for Version 1

Version 1 does not require:

- textual interpretations in the comparison object
- natural-language summaries
- batch-level aggregation
- significance testing
- explicit per-step comparison objects beyond required time series

Free-form interpretation text should remain outside the core comparison object.

---

## 23. Conformance Summary

An implementation conforms to this specification if it:

- validates pairing strictly
- uses episode seed identity as primary pairing identity
- supports transitional derived seed pairing when explicit seed is absent
- aligns traces on the shared prefix only
- uses the specified tolerance model
- supports explicit ambiguity states
- compares actions through shared label intersection
- produces all required generic metric families
- preserves required time series in array form
- separates system-specific analysis into explicit extensions

---

## 24. Summary

Version 1 of the paired trace comparison specification defines a strict and extensible comparison model for AXIS replay traces.

Its central principles are:

- strict pairing validation
- shared-prefix alignment
- explicit tolerance handling
- honest ambiguity reporting
- shared-label action comparison
- generic metric core
- explicit system-specific extensions

This specification provides the first stable foundation for comparing systems such as `System A` and `System C` in a methodologically clean and replay-grounded way.
