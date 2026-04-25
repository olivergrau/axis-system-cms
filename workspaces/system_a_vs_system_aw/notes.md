# Notes

## Study Overview

This workspace compares `system_a` and `system_aw` under matched execution and world settings.

- Workspace class/type: `investigation` / `system_comparison`
- Reference system: `system_a`
- Candidate system: `system_aw`
- Research question: Does `system_aw` provide a measurable advantage over `system_a` in the selected foraging task?

## Experimental Setting

Current shared setup for the first comparison batch:

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

Working assumption: the comparison should remain fair unless the experiment explicitly tests a world or execution change.

## Baseline Reference

Use this section to store the current baseline `system_a` numbers for the shared setting. This makes later candidate comparisons easier to interpret.

Reference (`system_a`, experiment `72d9d034727f40e38af5837f12e17ca7`):

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

Reference interpretation:

- `system_a` provides the initial baseline for clustered `grid_2d` under the shared 50-episode setup.

## Experiment Log Template

Repeat the following structure for each `system_aw` experiment.

## Experiment 1: Baseline Run With Baseline Configs

### Hypothesis

Test whether the default `system_aw` architecture provides a measurable advantage over `system_a` under the same clustered foraging conditions.

### Candidate configuration

Candidate delta relative to `system_a`:

```yaml
system_type: system_aw
system.curiosity.base_curiosity: 1.0
system.curiosity.spatial_sensory_balance: 0.7
system.curiosity.explore_suppression: 0.5
system.curiosity.novelty_sharpness: 2.0
system.arbitration.hunger_weight_base: 0.2
system.arbitration.curiosity_weight_base: 1.5
system.arbitration.gating_sharpness: 3.0
```

### Results

Candidate (`system_aw`, experiment `01b09ac68635495b93346fe54607a858`):

```text
mean_steps=161.7
death_rate=0.54
mean_final_vitality=0.231
resource_gain_per_step=0.423110
net_energy_efficiency=0.433731
successful_consume_rate=0.740000
failed_movement_rate=0.000000
action_entropy=1.459805
policy_sharpness=0.437021
unique_cells_visited=117.060000
coverage_efficiency=0.757553
revisit_rate=0.236658
```

System-specific metrics, if present:

```text
system_aw_arbitration
  curiosity_dominance_rate=0.410834
  mean_curiosity_weight=0.330867
  mean_hunger_weight=0.341120
  arbitrated_step_count=8086

system_aw_curiosity
  mean_curiosity_activation=0.893060
  mean_spatial_novelty=0.659439
  mean_sensory_novelty=0.115794
  mean_composite_novelty=0.496346
  curiosity_pressure_rate=1.000000

system_aw_behavior
  curiosity_led_move_rate=0.961662
  consume_under_curiosity_pressure_rate=0.038338
  movement_step_rate=0.961662
  consume_step_rate=0.038338

system_aw_world_model
  world_model_unique_cells=117.060000
  mean_visit_count_at_current=1.643705
  world_model_revisit_ratio=0.259006
```

### Comparison Against `system_a`

Record the most decision-relevant deltas rather than every possible metric.

- `mean_steps`: `161.7` vs `171.8`
- `death_rate`: `0.54` vs `0.38`
- `resource_gain_per_step`: `0.423110` vs `0.738489`
- `net_energy_efficiency`: `0.433731` vs `0.840050`
- `successful_consume_rate`: `0.740000` vs `0.800000`
- `action_entropy`: `1.459805` vs `1.571069`
- `policy_sharpness`: `0.437021` vs `0.283138`
- `unique_cells_visited`: `117.060000` vs `47.700000`
- `coverage_efficiency`: `0.757553` vs `0.310025`
- `revisit_rate`: `0.236658` vs `0.663771`

Comparison output (`comparisons/comparison-001.json`) additionally reports:

- `num_valid_pairs`: `50`
- mean action mismatch rate: `0.789449`
- mean trajectory distance: `10.949979`
- mean vitality difference: `0.247968`
- final vitality delta: `-0.230920`
- total steps delta: `-10.1`
- reference survival rate: `0.62`
- candidate survival rate: `0.46`
- candidate longer count: `13`
- reference longer count: `23`
- equal count: `14`

### Interpretation

Answer the scientific question for this run, not just the configuration question.

- Did `system_aw` improve performance?
- Did it merely change behavior without improving foraging outcomes?
- Was any gain offset by lower survival, lower vitality, or worse energy efficiency?
- Are the effects large enough to matter, or only visible in secondary metrics?

The first baseline comparison shows a clear behavioral change and a clear performance cost. `system_aw` explored far more broadly than `system_a`, visiting many more unique cells and achieving much higher coverage efficiency, while also revisiting far less often. At the same time, that exploratory profile did not improve foraging outcomes. Relative to `system_a`, the candidate survived for fewer steps, died more often, ended with substantially lower vitality, consumed successfully less often, and achieved much lower resource gain and energy efficiency.

The new A+W-specific metrics make that pattern easier to interpret:

- curiosity was active almost continuously: `curiosity_pressure_rate=1.000000`
- curiosity-dominant arbitration occurred often, but not overwhelmingly: `curiosity_dominance_rate=0.410834`
- the agent was overwhelmingly movement-oriented: `curiosity_led_move_rate=0.961662`
- `consume_step_rate=0.038338` shows that only a small fraction of steps were consumption actions
- `world_model_unique_cells=117.060000` confirms that the internal world model expanded substantially during the run
- `mean_visit_count_at_current=1.643705` and `world_model_revisit_ratio=0.259006` indicate relatively low revisitation pressure compared with the reference system's external behavior profile

Taken together, these metrics support a more specific reading: the default `system_aw` configuration did not merely add a small exploratory bias. It placed the agent in a strongly curiosity-shaped operating regime, and that regime appears to have over-prioritized movement and novelty relative to immediate energy collection.

Based on this first run alone, the most defensible interpretation is that the default `system_aw` setting shifts the agent strongly toward exploration, but in this clustered hunger-foraging task that exploration was not yet well aligned with survival or energy collection.

## Experiment 2: Conservative Foraging Explorer

### Hypothesis

Reduce the exploratory aggressiveness of `system_aw` so that curiosity still produces broad search behavior, but does not overwhelm foraging. The intended outcome is a more conservative explorer that preserves some of A+W's survival benefits while reducing the energy cost of excessive wandering.

### Candidate configuration

Candidate delta relative to `system_a`:

```yaml
system_type: system_aw
system.curiosity.base_curiosity: 0.45
system.curiosity.spatial_sensory_balance: 0.55
system.curiosity.explore_suppression: 0.25
system.curiosity.novelty_sharpness: 1.5
system.arbitration.hunger_weight_base: 0.45
system.arbitration.curiosity_weight_base: 0.75
system.arbitration.gating_sharpness: 2.0
```

### Results

Reference (`system_a`, experiment `62f7c66b9a3d44a0bc5477a5d764a9b0`):

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

Candidate (`system_aw`, experiment `df51fa523025482b9c01d27e9ead627a`):

```text
mean_steps=177.4
death_rate=0.32
mean_final_vitality=0.466
resource_gain_per_step=0.605522
net_energy_efficiency=0.625011
successful_consume_rate=0.860000
failed_movement_rate=0.000000
action_entropy=1.495590
policy_sharpness=0.349192
unique_cells_visited=113.600000
coverage_efficiency=0.676649
revisit_rate=0.312017
```

System-specific metrics:

```text
system_aw_arbitration
  curiosity_dominance_rate=0.234724
  mean_curiosity_weight=0.351049
  mean_hunger_weight=0.540140
  arbitrated_step_count=8870

system_aw_curiosity
  mean_curiosity_activation=0.394236
  mean_spatial_novelty=0.668635
  mean_sensory_novelty=0.136494
  mean_composite_novelty=0.429171
  curiosity_pressure_rate=1.000000

system_aw_behavior
  curiosity_led_move_rate=0.945547
  consume_under_curiosity_pressure_rate=0.054453
  movement_step_rate=0.945547
  consume_step_rate=0.054453

system_aw_world_model
  world_model_unique_cells=113.600000
  mean_visit_count_at_current=1.985569
  world_model_revisit_ratio=0.343052
```

### Comparison Against `system_a`

- `mean_steps`: `177.4` vs `171.8`
- `death_rate`: `0.32` vs `0.38`
- `mean_final_vitality`: `0.466` vs `0.462`
- `resource_gain_per_step`: `0.605522` vs `0.738489`
- `net_energy_efficiency`: `0.625011` vs `0.840050`
- `successful_consume_rate`: `0.860000` vs `0.800000`
- `action_entropy`: `1.495590` vs `1.571069`
- `policy_sharpness`: `0.349192` vs `0.283138`
- `unique_cells_visited`: `113.600000` vs `47.700000`
- `coverage_efficiency`: `0.676649` vs `0.310025`
- `revisit_rate`: `0.312017` vs `0.663771`

Comparison output (`comparisons/comparison-002.json`) additionally reports:

- `num_valid_pairs`: `50`
- mean action mismatch rate: `0.786835`
- mean trajectory distance: `10.257101`
- mean vitality difference: `0.215860`
- final vitality delta: `0.004000`
- total steps delta: `5.58`
- reference survival rate: `0.62`
- candidate survival rate: `0.68`
- candidate longer count: `17`
- reference longer count: `11`
- equal count: `22`

### Interpretation

This configuration is the first clearly mixed but positive-leaning result for `system_aw`.

Relative to `system_a`, the candidate now shows better survival outcomes:

- higher mean survival time: `177.4` vs `171.8`
- lower death rate: `0.32` vs `0.38`
- slightly higher mean final vitality: `0.466` vs `0.462`
- higher pairwise survival rate in the comparison summary: `0.68` vs `0.62`

At the same time, the candidate is still not a better energy harvester:

- `resource_gain_per_step` remains lower: `0.605522` vs `0.738489`
- `net_energy_efficiency` remains lower: `0.625011` vs `0.840050`

This makes the main scientific reading fairly strong: the conservative setting improved the survival profile of A+W without yet closing the harvesting gap to `system_a`.

The A+W-specific metrics clarify why this version behaves differently from the first baseline candidate:

- `curiosity_dominance_rate` dropped from `0.410834` to `0.234724`
- `mean_curiosity_activation` dropped from `0.893060` to `0.394236`
- movement is still dominant, but slightly less extreme: `curiosity_led_move_rate=0.945547`
- `consume_step_rate` increased from `0.038338` to `0.054453`
- the world model still expands broadly: `world_model_unique_cells=113.600000`

That pattern is consistent with a more conservative explorer: curiosity remains architecturally important, but hunger has regained more practical control. The result is a candidate that survives better than `system_a` while still paying an exploration cost in immediate harvesting efficiency.

Your working interpretation is well supported by the numbers: this configuration made A+W a better survivor, but not yet a better energy harvester.

## Experiment 3: Conservative Foraging Explorer v2

### Hypothesis

Push the conservative-foraging direction further: keep the survival gains from A+W, reduce curiosity dominance even more, allow slightly easier consumption under curiosity, and move the system toward a weak but persistent exploratory bias rather than an exploration-led regime.

### Candidate configuration

Candidate delta relative to `system_a`:

```yaml
system_type: system_aw
system.curiosity.base_curiosity: 0.38
system.curiosity.spatial_sensory_balance: 0.45
system.curiosity.explore_suppression: 0.18
system.curiosity.novelty_sharpness: 1.4
system.arbitration.hunger_weight_base: 0.52
system.arbitration.curiosity_weight_base: 0.65
system.arbitration.gating_sharpness: 2.2
```

### Results

Reference (`system_a`, experiment `4d8bd19b10514f3bb609851726ff6716`):

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

Candidate (`system_aw`, experiment `3c9e8e8e87ec42f1ac7dabac2952bbd9`):

```text
mean_steps=180.6
death_rate=0.28
mean_final_vitality=0.540
resource_gain_per_step=0.654655
net_energy_efficiency=0.677865
successful_consume_rate=0.880000
failed_movement_rate=0.000000
action_entropy=1.504192
policy_sharpness=0.316267
unique_cells_visited=108.920000
coverage_efficiency=0.640008
revisit_rate=0.346972
```

System-specific metrics:

```text
system_aw_arbitration
  curiosity_dominance_rate=0.080952
  mean_curiosity_weight=0.321504
  mean_hunger_weight=0.577397
  arbitrated_step_count=9030

system_aw_curiosity
  mean_curiosity_activation=0.333507
  mean_spatial_novelty=0.675072
  mean_sensory_novelty=0.134384
  mean_composite_novelty=0.377694
  curiosity_pressure_rate=1.000000

system_aw_behavior
  curiosity_led_move_rate=0.938981
  consume_under_curiosity_pressure_rate=0.061019
  movement_step_rate=0.938981
  consume_step_rate=0.061019

system_aw_world_model
  world_model_unique_cells=108.920000
  mean_visit_count_at_current=2.225249
  world_model_revisit_ratio=0.380371
```

### Comparison Against `system_a`

- `mean_steps`: `180.6` vs `171.8`
- `death_rate`: `0.28` vs `0.38`
- `mean_final_vitality`: `0.540` vs `0.462`
- `resource_gain_per_step`: `0.654655` vs `0.738489`
- `net_energy_efficiency`: `0.677865` vs `0.840050`
- `successful_consume_rate`: `0.880000` vs `0.800000`
- `action_entropy`: `1.504192` vs `1.571069`
- `policy_sharpness`: `0.316267` vs `0.283138`
- `unique_cells_visited`: `108.920000` vs `47.700000`
- `coverage_efficiency`: `0.640008` vs `0.310025`
- `revisit_rate`: `0.346972` vs `0.663771`

Comparison output (`comparisons/comparison-003.json`) additionally reports:

- `num_valid_pairs`: `50`
- mean action mismatch rate: `0.779746`
- mean trajectory distance: `10.654306`
- mean vitality difference: `0.210685`
- final vitality delta: `0.077390`
- total steps delta: `8.78`
- reference survival rate: `0.62`
- candidate survival rate: `0.72`
- candidate longer count: `19`
- reference longer count: `9`
- equal count: `22`

### Interpretation

This is the strongest result in the A vs. A+W sequence so far and a clean end point for the current tuning phase.

Relative to `system_a`, `system_aw` now shows a clear survival advantage:

- higher mean survival time: `180.6` vs `171.8`
- lower death rate: `0.28` vs `0.38`
- higher mean final vitality: `0.540` vs `0.462`
- higher comparison survival rate: `0.72` vs `0.62`

At the same time, it still does not surpass `system_a` on direct harvesting efficiency:

- `resource_gain_per_step` remains lower: `0.654655` vs `0.738489`
- `net_energy_efficiency` remains lower: `0.677865` vs `0.840050`

However, the gap is now clearly narrower than in the previous configurations. Compared with Experiment 2, this version improved:

- `mean_steps`: `177.4 -> 180.6`
- `death_rate`: `0.32 -> 0.28`
- `mean_final_vitality`: `0.466 -> 0.540`
- `resource_gain_per_step`: `0.605522 -> 0.654655`
- `net_energy_efficiency`: `0.625011 -> 0.677865`
- `successful_consume_rate`: `0.860000 -> 0.880000`

The internal A+W metrics explain why this is happening:

- `curiosity_dominance_rate` was pushed down further from `0.234724` to `0.080952`
- `mean_hunger_weight` increased to `0.577397`
- `consume_step_rate` rose again to `0.061019`
- curiosity remained present, but now as a weak spatial bias rather than a dominant controller

This is exactly the regime the tuning process was aiming for. Curiosity still supports broad exploration and strong world-model growth, but it no longer overrides hunger often enough to destabilize foraging.

A careful but strong interpretation is therefore justified: in this clustered world, A+W becomes beneficial when curiosity is regulated into a low-dominance, persistent-support role. In that regime, the world model and exploratory bias appear to reduce local stagnation and improve survival, even though they still carry a step-level efficiency cost.

## Cross-Experiment Assessment

Use this section only after several experiments have been accumulated.

Questions to answer:

1. Does `system_aw` consistently outperform `system_a`, or only under narrow settings?
2. If performance changes, which metrics move together: survival, vitality, energy efficiency, exploration, or policy structure?
3. If behavior changes without better outcomes, what does that imply about the architectural contribution of `system_aw`?

Current synthesis:

- After the first baseline experiment, `system_aw` appears behaviorally very different from `system_a`.
- The dominant visible effect is much broader exploration rather than better energy performance.
- The new A+W-specific metrics suggest that the candidate is operating under sustained curiosity pressure with a very high movement bias.
- The second configuration shows that reducing curiosity pressure can materially improve survival without eliminating the exploratory signature of A+W.
- The third configuration strengthens that pattern: A+W can be tuned into a robust survival-improving regime while keeping curiosity dominance low.
- The current best reading is that A+W can outperform `system_a` on survival in clustered worlds, but has not yet matched `system_a` on energy harvesting efficiency.

## Conclusion

Write the strongest conclusion that is supported by the measurements, but avoid claiming more than the data show.

Recommended style:

- strong about this workspace and this task
- careful about broader generalization
- explicit about what improved, what worsened, and what stayed ambiguous

Draft conclusion:

The experiments now support a clear phase conclusion. In its default configuration, `system_aw` was overly curiosity-driven: it explored broadly, but performed worse than `system_a` on both survival and energy outcomes. Systematic tuning then showed that the right direction was not more curiosity, but stronger regulation of curiosity by hunger and weaker suppression of foraging behavior.

In the best configuration of this phase, `system_aw` achieved a real advantage over `system_a` on survival: lower death rate, longer mean survival, and higher final vitality, while still preserving a much broader exploration footprint and far lower revisit rate. This did not come from luck or arbitrary searching; it emerged from a consistent reduction of curiosity dominance toward a weak-bias regime.

The remaining limitation is also clear. `system_aw` is still less efficient as an immediate energy harvester, with lower `resource_gain_per_step` and lower `net_energy_efficiency` than `system_a`. The strongest supported conclusion is therefore:

`system_aw` is beneficial in this clustered environment when curiosity is strongly regulated and hunger remains the dominant decision basis. In that regime, a minimal world model plus weak curiosity improves survival by reducing local stagnation, even though it still trades away some step-level harvesting efficiency.
