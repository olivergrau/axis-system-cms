# Notes

## Study Overview

This workspace compares `system_a` and `system_c` under matched execution and world settings.

- Workspace class/type: `investigation` / `system_comparison`
- Reference system: `system_a`
- Candidate system: `system_c`
- Research question: Does prediction provide a meaningful advantage for a simple hunger-driven forager?

## Experimental Setting

All runs reported here used the same shared environment and execution setup unless noted otherwise:

- world: `grid_2d`
- size: `20 x 20`
- topology: `bounded`
- obstacle density: `0.2`
- regeneration mode: `clustered`
- `num_clusters: 3`
- `regen_eligible_ratio: 0.10`
- `resource_regen_rate: 0.01`
- `resource_regen_cooldown_steps: 10`
- seed: `42`
- trace mode: `delta`
- episodes per run: `50`
- max steps per episode: `200`

The clustered world was chosen to give prediction a fairer test than a uniformly sparse layout. If local prediction is useful, this environment should offer repeated spatial regularities that can in principle be learned.

## Initial Diagnostic

Before the focused cluster tests, the predictive signal in `system_c` already appeared weak:

```text
prediction_modulation_strength: 0.002
confidence_trace_mean: 0.020
frustration_trace_mean: 0.008
signed_prediction_error: 0.020
```

This suggested that prediction was learning some structure, but translating only a very small amount of that structure into action modulation.

## Experiment 1: Cluster Confidence Boost

### Hypothesis

Increase the influence of positive predictive structure in clustered environments so that `system_c` can exploit recurring local regularities more effectively.

### Candidate configuration

```yaml
memory_learning_rate: 0.12
modulation_mode: "hybrid"
prediction_bias_scale: 0.08
prediction_bias_clip: 0.25
context_threshold: 0.35
frustration_rate: 0.06
confidence_rate: 0.18
positive_sensitivity: 2.0
negative_sensitivity: 0.8
modulation_min: 0.8
modulation_max: 1.8
positive_weights: [0.45, 0.1375, 0.1375, 0.1375, 0.1375]
negative_weights: [0.5, 0.125, 0.125, 0.125, 0.125]
```

### Results

Reference (`system_a`, experiment `9bc16d949a6b494dadb92411ebdb3d69`):

```text
mean_steps=171.8
death_rate=0.38
mean_final_vitality=0.462
resource_gain_per_step=0.738
net_energy_efficiency=0.840
successful_consume_rate=0.800
failed_movement_rate=0.000
action_entropy=1.571
policy_sharpness=0.283
unique_cells_visited=47.70
coverage_efficiency=0.310
revisit_rate=0.664
```

Candidate (`system_c`, experiment `208e161e939d4bfd845fb3f901966113`):

```text
mean_steps=164.7
death_rate=0.50
mean_final_vitality=0.285
resource_gain_per_step=0.588
net_energy_efficiency=0.635
successful_consume_rate=0.800
failed_movement_rate=0.000
action_entropy=1.518
policy_sharpness=0.325
unique_cells_visited=49.62
coverage_efficiency=0.321
revisit_rate=0.666

mean_prediction_error=0.036
signed_prediction_error=0.025
confidence_trace_mean=0.014
frustration_trace_mean=0.003
prediction_modulation_strength=0.001
prediction_step_count=8236
```

### Interpretation

This configuration did not improve performance. Relative to `system_a`, `system_c` survived for fewer steps, died more often, ended with much lower vitality, and harvested less energy per step. The one consistent behavioral shift was a more structured and sharper policy:

- lower entropy: `1.518` vs `1.571`
- higher sharpness: `0.325` vs `0.283`
- slightly broader coverage: `49.62` visited cells vs `47.70`

The most important point is that increased behavioral structure did not translate into improved foraging.

## Experiment 1b: Cluster Confidence Boost With Stronger Modulation

### Candidate configuration

```yaml
memory_learning_rate: 0.18
modulation_mode: "hybrid"
prediction_bias_scale: 0.15
prediction_bias_clip: 0.40
context_threshold: 0.30
frustration_rate: 0.04
confidence_rate: 0.35
positive_sensitivity: 4.0
negative_sensitivity: 0.4
modulation_min: 0.85
modulation_max: 2.2
positive_weights: [0.25, 0.1875, 0.1875, 0.1875, 0.1875]
negative_weights: [0.35, 0.1625, 0.1625, 0.1625, 0.1625]
```

### Results

Candidate (`system_c`, experiment `1f3a8b4b98c84a23bd047618a0716918`):

```text
mean_steps=161.0
death_rate=0.62
mean_final_vitality=0.235
resource_gain_per_step=0.524
net_energy_efficiency=0.569
successful_consume_rate=0.800
failed_movement_rate=0.000
action_entropy=1.498
policy_sharpness=0.332
unique_cells_visited=49.48
coverage_efficiency=0.324
revisit_rate=0.664

mean_prediction_error=0.030
signed_prediction_error=0.017
confidence_trace_mean=0.016
frustration_trace_mean=0.002
prediction_modulation_strength=0.003
prediction_step_count=8051
```

### Interpretation

Stronger modulation made the policy even sharper and less entropic, and it increased `prediction_modulation_strength` from `0.001` to `0.003`. However, performance worsened further:

- `mean_steps`: `164.7 -> 161.0`
- `death_rate`: `0.50 -> 0.62`
- `resource_gain_per_step`: `0.588 -> 0.524`
- `net_energy_efficiency`: `0.635 -> 0.569`

This is a strong indication that simply amplifying predictive influence does not solve the underlying problem in this task.

## Experiment 1c: Weak Hybrid Smoothing

### Hypothesis

Allow prediction to smooth or gently bias action selection without substantially overriding hunger gradients.

### Candidate configuration

```yaml
memory_learning_rate: 0.08
modulation_mode: "hybrid"
prediction_bias_scale: 0.03
prediction_bias_clip: 0.15
context_threshold: 0.30
frustration_rate: 0.04
confidence_rate: 0.10
positive_sensitivity: 1.0
negative_sensitivity: 0.8
modulation_min: 0.9
modulation_max: 1.3
positive_weights: [0.35, 0.1625, 0.1625, 0.1625, 0.1625]
negative_weights: [0.45, 0.1375, 0.1375, 0.1375, 0.1375]
```

### Results

Candidate (`system_c`, experiment `2fecde933722475bbeb2f10f9f7da40e`):

```text
mean_steps=163.1
death_rate=0.46
mean_final_vitality=0.275
resource_gain_per_step=0.550
net_energy_efficiency=0.594
successful_consume_rate=0.800
failed_movement_rate=0.000
action_entropy=1.507
policy_sharpness=0.330
unique_cells_visited=46.64
coverage_efficiency=0.308
revisit_rate=0.681

mean_prediction_error=0.032
signed_prediction_error=0.022
confidence_trace_mean=0.009
frustration_trace_mean=0.002
prediction_modulation_strength=0.000154
prediction_step_count=8156
```

### Interpretation

Reducing predictive strength pushed `system_c` somewhat closer to `system_a`, but did not produce a gain over the baseline hunger agent. The extremely small `prediction_modulation_strength` (`0.000154`) is especially informative: even very weak predictive influence still changed tie-breaking and reduced behavioral diversity, but did not improve energy return or survival.

This supports a narrower and better-supported conclusion than the original draft: in this task, as predictive influence approaches zero, `system_c` approaches `system_a` in both behavior and performance, but small residual modulation is still enough to alter policy statistics without delivering a functional benefit.

## Experiment 2: Cluster Edge Explorer

### Hypothesis

Use additive prediction to reward movements that lead to locally richer neighboring observations, especially in sparse clustered environments with gaps.

### Candidate configuration

```yaml
memory_learning_rate: 0.10
modulation_mode: "additive"
prediction_bias_scale: 0.10
prediction_bias_clip: 0.30
context_threshold: 0.30
frustration_rate: 0.05
confidence_rate: 0.20
positive_sensitivity: 2.5
negative_sensitivity: 0.6
modulation_min: 1.0
modulation_max: 1.0
positive_weights: [0.30, 0.175, 0.175, 0.175, 0.175]
negative_weights: [0.45, 0.1375, 0.1375, 0.1375, 0.1375]
```

### Results

Reference (`system_a`, experiment `49d4f8e474e54a05b34092f4a194cecb`):

```text
mean_steps=171.8
death_rate=0.38
mean_final_vitality=0.462
resource_gain_per_step=0.738489
net_energy_efficiency=0.840050
successful_consume_rate=0.800000
failed_movement_rate=0.000000
action_entropy=1.571069
policy_sharpness=0.283138
unique_cells_visited=47.700000
coverage_efficiency=0.310025
revisit_rate=0.663771
```

Candidate (`system_c`, experiment `d1926268ede946b4a4f1115e04fec604`):

```text
mean_steps=162.3
death_rate=0.54
mean_final_vitality=0.232
resource_gain_per_step=0.547759
net_energy_efficiency=0.591329
successful_consume_rate=0.800000
failed_movement_rate=0.000000
action_entropy=1.513685
policy_sharpness=0.326100
unique_cells_visited=48.480000
coverage_efficiency=0.318389
revisit_rate=0.670650

mean_prediction_error=0.032201
signed_prediction_error=0.022330
confidence_trace_mean=0.013549
frustration_trace_mean=0.002455
prediction_modulation_strength=0.001101
prediction_step_count=8115
```

### Interpretation

This result is consistent with the previous tests and is arguably the clearest negative result in the set.

Compared with `system_a`, `system_c` showed:

- fewer mean survival steps: `162.3` vs `171.8`
- higher death rate: `0.54` vs `0.38`
- much lower resource gain per step: `0.547759` vs `0.738489`
- much lower net energy efficiency: `0.591329` vs `0.840050`
- lower action entropy: `1.513685` vs `1.571069`
- higher policy sharpness: `0.326100` vs `0.283138`
- slightly higher coverage and visited cells

The pattern is important: prediction again produced more structured and somewhat more exploratory movement, but not better foraging. In other words, the learned structure was behaviorally real but operationally misaligned with the task objective.

## Cross-Experiment Assessment

Across all tested cluster-oriented `system_c` variants, the same qualitative pattern repeated:

1. Prediction changed behavior.
2. The change usually reduced entropy and increased policy sharpness.
3. In some variants it also slightly increased coverage or visited-cell count.
4. None of the tested variants improved resource gain, net energy efficiency, survival, or final vitality over `system_a`.

This makes the central conclusion defensible:

`system_c` prediction is not inert in this setting. It does shape action selection. However, in the present hunger-only architecture and clustered `grid_2d` task, that shaping did not produce a performance advantage.

## Conclusion

The current evidence supports the following professional conclusion:

In the tested hunger-only foraging setting, local prediction alone did not improve performance over the reactive baseline. Across several parameterizations, predictive modulation consistently altered policy structure, but the resulting behavior was not better aligned with energy acquisition or survival.

The stronger claim from the earlier draft should be softened slightly. The data do not prove that prediction is universally insufficient. They do show, quite clearly, that in this architecture and task family, local predictive traces without additional task-relevant structure were not enough to outperform `system_a`.

A reasonable next scientific hypothesis is therefore not "more tuning," but "different architectural support." Two natural follow-up directions are:

- prediction combined with curiosity or novelty pressure
- prediction combined with a richer world model or state representation

That framing is well supported by the measurements above and stays faithful to what the experiments actually demonstrated.
