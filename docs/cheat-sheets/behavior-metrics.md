# Behavioral Metrics Cheat Sheet

Compact reference for the run-level behavioral metrics that AXIS computes from
replay-capable traces.

This page covers:

1. framework-standard metrics shared across systems
2. system-specific metrics currently exposed by `system_aw`, `system_c`, and
   `system_cw`
3. the mathematical definition and interpretation of each metric

See also:

- [CLI Manual](../manuals/cli-manual.md)
- [Metrics Extensions Manual](../manuals/metrics-extension-manual.md)
- [System A+W Cheat Sheet](system-aw.md)
- [System C Cheat Sheet](system-c.md)
- [System C+W Cheat Sheet](system-cw.md)

## 1. Where These Metrics Come From

Behavioral metrics are computed from persisted episode traces with trace mode:

- `full`
- `delta`

They are stored as:

```text
results/<experiment-id>/runs/<run-id>/behavior_metrics.json
```

Useful commands:

```bash
axis runs metrics run-0000 --experiment <experiment-id>
axis workspaces run-metrics <workspace>
axis workspaces run-summary <workspace>
```

Important output detail:

- `run-summary` shows the run summary plus a compact behavioral-metrics table
- for framework-standard metrics, the CLI table shows the `mean`
- the persisted JSON artifact also contains `std`, `min`, `max`, and `n`

## 2. Notation

For one episode:

- $T$: number of executed steps
- $a_t$: action chosen at step $t$
- $g_t$: energy gained at step $t$
- $c_t$: action cost at step $t$
- $v_T$: final vitality at episode end
- $\mathcal{M}$: movement actions `UP, DOWN, LEFT, RIGHT`
- $N_{\mathrm{consume}}$: number of `CONSUME` actions
- $N_{\mathrm{move}}$: number of movement actions

Let:

- $\mathcal{P}$ be the set of visited cells during the episode
- $\mathcal{D}$ be the set of movement destinations actually reached
- $p(a)$ be the empirical action frequency of action $a$
- $\pi_t(a)$ be the policy probability assigned to action $a$ at step $t$

Across episodes in one run, AXIS uses:

$$
\mathrm{mean}(x)=\frac{1}{n}\sum_{i=1}^{n} x_i
$$

$$
\mathrm{std}(x)=\sqrt{\frac{1}{n}\sum_{i=1}^{n}(x_i-\mathrm{mean}(x))^2}
$$

The standard-metric artifact stores:

- `mean`
- `std`
- `min`
- `max`
- `n`

## 3. Framework-Standard Metrics

These metrics exist for every system.

### Run summary scalars

#### `mean_steps`

$$
\mathrm{mean\_steps} = \frac{1}{n}\sum_{i=1}^{n} T_i
$$

Meaning: average episode length.

Interpretation:

- higher values usually mean better survival or longer productive behavior
- but they can also indicate looping or stagnation if coverage stays low

#### `death_rate`

$$
\mathrm{death\_rate} = \frac{1}{n}\sum_{i=1}^{n}\mathbf{1}[v_{T_i}\le 0]
$$

Meaning: fraction of episodes ending in system death / vitality depletion.

Interpretation:

- lower is usually better for survival-oriented systems
- compare with `mean_final_vitality` to distinguish near-failures from healthy runs

#### `mean_final_vitality`

$$
\mathrm{mean\_final\_vitality} = \frac{1}{n}\sum_{i=1}^{n} v_{T_i}
$$

Meaning: average normalized end-of-episode vitality.

Interpretation:

- higher means the agent tends to finish in a healthier state
- useful when episode lengths are capped and death alone is too coarse

### Per-episode metrics later aggregated into `mean/std/min/max/n`

#### `resource_gain_per_step`

$$
\frac{\sum_{t=1}^{T} g_t}{T}
$$

Meaning: average energy/resource intake per step.

Interpretation:

- higher means the agent extracts more value from the environment over time
- insensitive to how expensive actions were

#### `net_energy_efficiency`

$$
\frac{\sum_{t=1}^{T} g_t}{\sum_{t=1}^{T} c_t}
$$

Meaning: gained energy per unit action cost.

Interpretation:

- higher means better energetic return on effort
- useful when two systems gather similar resources but spend different energy

#### `successful_consume_rate`

$$
\frac{\#\{t : a_t=\mathrm{CONSUME}\ \land\ g_t>0\}}{N_{\mathrm{consume}}}
$$

Meaning: fraction of consume attempts that actually gained energy.

Interpretation:

- higher means better timing and location of consumption
- low values often indicate wasteful consume behavior or poor local sensing

#### `consume_on_empty_rate`

$$
\frac{\#\{t : a_t=\mathrm{CONSUME}\ \land\ r_t^{current}\le 0\}}{N_{\mathrm{consume}}}
$$

Meaning: fraction of consume attempts made on an empty current cell.

Interpretation:

- lower is better
- high values often signal poor persistence, poor prediction, or excessive action inertia

#### `failed_movement_rate`

$$
\frac{\#\{t : a_t\in\mathcal{M}\ \land\ p_{t+1}=p_t\}}{N_{\mathrm{move}}}
$$

Meaning: fraction of movement attempts that did not change position.

Interpretation:

- lower is better
- high values usually indicate collision with obstacles or bad local action choice

#### `action_entropy`

$$
H = -\sum_{a} p(a)\log p(a)
$$

Meaning: entropy of the empirical action distribution.

Interpretation:

- higher means more behaviorally diverse action usage
- lower means more concentrated or repetitive policies
- not inherently good or bad; interpret together with outcome metrics

#### `policy_sharpness`

$$
\frac{1}{T}\sum_{t=1}^{T}\max_a \pi_t(a)
$$

Meaning: average peak policy confidence at decision time.

Interpretation:

- higher means the policy tends to strongly favor one action
- lower means more ambiguity or flatter action preferences

#### `action_inertia`

$$
\frac{\#\{t\in\{2,\dots,T\}: a_t=a_{t-1}\}}{T-1}
$$

Meaning: rate of repeating the immediately previous action.

Interpretation:

- higher means more persistence / stickiness
- can be useful for stable exploitation, but can also indicate loops

#### `unique_cells_visited`

$$
|\mathcal{P}|
$$

Meaning: number of distinct cells visited in the episode.

Interpretation:

- higher usually means broader exploration
- compare with `revisit_rate` to distinguish broad exploration from wandering-in-place

#### `coverage_efficiency`

$$
\frac{|\mathcal{P}|}{\sum_{t=1}^{T} c_t}
$$

Meaning: distinct spatial coverage achieved per unit action cost.

Interpretation:

- higher means cheaper exploration for the amount of territory covered
- useful when comparing systems with different movement / stay / consume mixes

#### `revisit_rate`

$$
1-\frac{|\mathcal{D}|}{N_{\mathrm{move}}}
$$

Meaning: fraction of movement steps that ended in already-reached destinations.

Interpretation:

- lower means less revisiting and more spatial novelty
- higher means more looping, local milling, or exploitation of known zones

## 4. Systems Without Additional Metrics

Currently these systems expose only the framework-standard metrics:

- `system_a`
- `system_b`

That means their run-level metrics artifact contains no
`system_specific_metrics` section.

## 5. `system_aw` Metrics

`system_aw` adds curiosity, arbitration, and a visit-count world model.

### `system_aw_arbitration`

#### `mean_hunger_weight`

$$
\frac{1}{K}\sum_{t=1}^{K} w_H(t)
$$

Meaning: average arbitration weight assigned to hunger.

Interpretation:

- higher means the system spent more time in need-driven mode

#### `mean_curiosity_weight`

$$
\frac{1}{K}\sum_{t=1}^{K} w_C(t)
$$

Meaning: average arbitration weight assigned to curiosity.

Interpretation:

- higher means exploratory motivation was allowed to matter more often

#### `curiosity_dominance_rate`

$$
\frac{\#\{t : w_C(t) > w_H(t)\}}{K}
$$

Meaning: fraction of arbitrated steps where curiosity outweighed hunger.

Interpretation:

- high values indicate exploration-first control
- low values indicate hunger-gated curiosity

#### `arbitrated_step_count`

$$
K
$$

Meaning: number of steps with arbitration data available.

Interpretation:

- mainly a coverage / sanity metric for the extension

### `system_aw_curiosity`

#### `mean_curiosity_activation`

$$
\frac{1}{K}\sum_{t=1}^{K} d_C(t)
$$

Meaning: average curiosity-drive activation.

Interpretation:

- higher means the agent often had exploratory pressure available

#### `mean_spatial_novelty`

$$
\frac{1}{K}\sum_{t=1}^{K}\frac{1}{|\mathcal{N}|}\sum_{dir\in\mathcal{N}}\nu^{spatial}_{t,dir}
$$

Meaning: average neighborhood novelty due to low visit counts.

Interpretation:

- higher means the agent often operated near spatially fresh territory

#### `mean_sensory_novelty`

$$
\frac{1}{K}\sum_{t=1}^{K}\frac{1}{|\mathcal{N}|}\sum_{dir\in\mathcal{N}}\nu^{sensory}_{t,dir}
$$

Meaning: average neighborhood novelty in observed resource signal.

Interpretation:

- higher means local observations differed more from buffered experience

#### `mean_composite_novelty`

$$
\frac{1}{K}\sum_{t=1}^{K}\frac{1}{|\mathcal{N}|}\sum_{dir\in\mathcal{N}}\nu_{t,dir}
$$

Meaning: average blended curiosity novelty signal.

Interpretation:

- useful as the main “what curiosity saw” scalar

#### `curiosity_pressure_rate`

$$
\frac{\#\{t : w_C(t)\,d_C(t) > w_H(t)\,d_H(t)\}}{K}
$$

Meaning: fraction of arbitrated steps where curiosity exerted more effective
pressure than hunger.

Interpretation:

- high values mean curiosity was not just active, but stronger than hunger in
  the weighted drive comparison
- low values mean curiosity may still be present, but hunger remained stronger

### `system_aw_behavior`

#### `curiosity_led_move_rate`

$$
\frac{\#\{t : w_C(t)\,d_C(t) > w_H(t)\,d_H(t) \land a_t\in\mathcal{M}\}}{K}
$$

Meaning: fraction of arbitrated steps that became movement under curiosity pressure.

Interpretation:

- higher means curiosity often translated into exploration movement

#### `consume_under_curiosity_pressure_rate`

$$
\frac{\#\{t : w_C(t)\,d_C(t) > w_H(t)\,d_H(t) \land a_t=\mathrm{CONSUME}\}}
{\#\{t : w_C(t)\,d_C(t) > w_H(t)\,d_H(t)\}}
$$

Meaning: fraction of curiosity-pressure steps that still ended in consume.

Interpretation:

- high values mean hunger/exploitation still wins often even when curiosity is active
- `None` means no step satisfied the relative curiosity-pressure condition

#### `movement_step_rate`

$$
\frac{\#\{t : a_t\in\mathcal{M}\}}{K}
$$

Meaning: share of arbitrated steps spent moving.

#### `consume_step_rate`

$$
\frac{\#\{t : a_t=\mathrm{CONSUME}\}}{K}
$$

Meaning: share of arbitrated steps spent consuming.

Interpretation for both:

- together they reveal the exploitation/exploration action mix

### `system_aw_world_model`

#### `world_model_unique_cells`

$$
\frac{1}{n}\sum_{i=1}^{n} |\mathcal{V}_i|
$$

where $\mathcal{V}_i$ is the final visit-count map support in episode $i$.

Meaning: average number of distinct cells represented in the world model.

Interpretation:

- similar to `unique_cells_visited`, but derived from the internal world model

#### `mean_visit_count_at_current`

$$
\mathrm{mean}_t\big(\mathrm{visit\_count\_at\_current}(t)\big)
$$

Meaning: average visit count of the cell the agent currently occupies.

Interpretation:

- higher means the agent often stands on familiar / repeatedly visited cells

#### `world_model_revisit_ratio`

For one episode:

$$
1-\frac{|\mathcal{V}|}{\sum_{x\in\mathcal{V}} \mathrm{visits}(x)}
$$

Then AXIS averages this over episodes.

Meaning: revisit ratio measured from the internal visit-count map.

Interpretation:

- lower means broader, less repetitive coverage
- higher means the world model records repeated returns

## 6. `system_c` Metrics

`system_c` adds prediction, signed error decomposition, traces, and action-score
modulation.

### `system_c_prediction`

#### `mean_prediction_error`

$$
\mathrm{mean}_t\left(\varepsilon_t^+ + \varepsilon_t^-\right)
$$

Meaning: average absolute predictive mismatch magnitude.

Interpretation:

- lower means predictions were more accurate
- higher means the local context-action model was less reliable

#### `signed_prediction_error`

$$
\mathrm{mean}_t\left(\varepsilon_t^+ - \varepsilon_t^-\right)
$$

Meaning: average signed direction of surprise.

Interpretation:

- positive means outcomes tended to be better than predicted
- negative means outcomes tended to disappoint the model

#### `confidence_trace_mean`

$$
\mathrm{mean}_t\big(c_t\big)
$$

Meaning: average confidence trace value.

Interpretation:

- higher means the system often accumulated positive predictive evidence

#### `frustration_trace_mean`

$$
\mathrm{mean}_t\big(f_t\big)
$$

Meaning: average frustration trace value.

Interpretation:

- higher means more repeated disappointment / unreliability

#### `prediction_modulation_strength`

For one step, let $h_t(a)$ be the raw hunger action scores and $\psi_t(a)$ the
prediction-modulated scores. Then:

$$
\Delta_t^{mod} =
\frac{1}{|\mathcal{A}|}\sum_{a\in\mathcal{A}} |\psi_t(a)-h_t(a)|
$$

The metric is:

$$
\mathrm{mean}_t(\Delta_t^{mod})
$$

Meaning: average magnitude of prediction-induced score reshaping.

Interpretation:

- near zero means prediction is effectively behaviorally silent
- larger values mean prediction materially alters action preferences

#### `prediction_step_count`

Meaning: number of steps for which prediction data contributed to the metric.

Interpretation:

- primarily a coverage sanity check

## 7. `system_cw` Metrics

`system_cw` combines the A+W dual-drive architecture with shared prediction and
separate hunger/curiosity trace interpretation.

### `system_cw_prediction`

#### `prediction_step_count`

Meaning: number of steps with populated prediction-trace data.

#### `feature_prediction_error_mean`

$$
\mathrm{mean}_t\left(\varepsilon^{feature,+}_t + \varepsilon^{feature,-}_t\right)
$$

Meaning: average shared-feature prediction error magnitude.

Interpretation:

- measures how well the shared predictive state models next-step features overall

#### `hunger_prediction_error_mean`

$$
\mathrm{mean}_t\left(\varepsilon^{H,+}_t + \varepsilon^{H,-}_t\right)
$$

Meaning: average absolute predictive error as interpreted by the hunger channel.

#### `curiosity_prediction_error_mean`

$$
\mathrm{mean}_t\left(\varepsilon^{C,+}_t + \varepsilon^{C,-}_t\right)
$$

Meaning: average absolute predictive error as interpreted by the curiosity channel.

Interpretation for both:

- differences between them show that the same shared memory is being valued differently by the two drives

#### `hunger_signed_prediction_error`

$$
\mathrm{mean}_t\left(\varepsilon^{H,+}_t - \varepsilon^{H,-}_t\right)
$$

#### `curiosity_signed_prediction_error`

$$
\mathrm{mean}_t\left(\varepsilon^{C,+}_t - \varepsilon^{C,-}_t\right)
$$

Meaning: average signed direction of predictive surprise for each drive.

Interpretation:

- positive means better-than-expected outcomes for that drive
- negative means disappointment for that drive

#### `mean_novelty_weight`

$$
\mathrm{mean}_t(\omega_t^{novelty})
$$

Meaning: average novelty weighting applied inside the curiosity-side prediction trace.

Interpretation:

- higher means curiosity-side interpretation is placing more emphasis on novelty

#### `movement_prediction_step_rate`

$$
\frac{\#\{t : a_t\in\mathcal{M} \land \text{prediction active}\}}{\#\{t : \text{prediction active}\}}
$$

Meaning: fraction of prediction-active steps that were movements.

Interpretation:

- helps separate movement-dominated predictive learning from consume/stay regimes

### `system_cw_traces`

#### `hunger_confidence_trace_mean`, `hunger_frustration_trace_mean`

$$
\mathrm{mean}_t(c_t^H),\qquad \mathrm{mean}_t(f_t^H)
$$

#### `curiosity_confidence_trace_mean`, `curiosity_frustration_trace_mean`

$$
\mathrm{mean}_t(c_t^C),\qquad \mathrm{mean}_t(f_t^C)
$$

Meaning: average confidence / frustration levels in each drive-specific trace system.

#### `hunger_trace_balance`, `curiosity_trace_balance`

$$
\mathrm{mean}_t(c_t^H - f_t^H),\qquad
\mathrm{mean}_t(c_t^C - f_t^C)
$$

Meaning: net trust balance per drive.

Interpretation:

- positive means confidence dominates frustration
- negative means frustration dominates confidence

#### `trace_divergence_mean`

$$
\mathrm{mean}_t\left(\left|(c_t^H-f_t^H)-(c_t^C-f_t^C)\right|\right)
$$

Meaning: average divergence between hunger-side and curiosity-side trust balances.

Interpretation:

- a key “dual interpretation” metric
- near zero means both drives are reading shared prediction similarly

#### `nonzero_hunger_trace_rate`, `nonzero_curiosity_trace_rate`

$$
\frac{\#\{t : c_t^H>0 \lor f_t^H>0\}}{\#\{t : \text{prediction active}\}},
\qquad
\frac{\#\{t : c_t^C>0 \lor f_t^C>0\}}{\#\{t : \text{prediction active}\}}
$$

Meaning: fraction of prediction-active steps where the trace system is nontrivially active.

Interpretation:

- higher means predictive experience is actually leaving a persistent trust signal

### `system_cw_modulation`

#### `hunger_modulation_strength`

For one step:

$$
\Delta_t^H = \frac{1}{|\mathcal{A}|}\sum_a |\psi_t^H(a)-h_t(a)|
$$

Metric:

$$
\mathrm{mean}_t(\Delta_t^H)
$$

Meaning: average magnitude of prediction-driven reshaping of hunger scores.

#### `curiosity_modulation_strength`

For one step:

$$
\Delta_t^C = \frac{1}{|\mathcal{A}|}\sum_a |\psi_t^C(a)-c_t(a)|
$$

Metric:

$$
\mathrm{mean}_t(\Delta_t^C)
$$

Meaning: average magnitude of prediction-driven reshaping of curiosity scores.

#### `mean_modulation_divergence`

$$
\mathrm{mean}_t\left(|\Delta_t^H-\Delta_t^C|\right)
$$

Meaning: average difference in modulation magnitude between the two drives.

Interpretation:

- higher means prediction is influencing hunger and curiosity asymmetrically

#### `hunger_reinforcement_rate`, `curiosity_reinforcement_rate`

$$
\frac{\#\{\mu_t(a) > 1\}}{\#\{\mu_t(a)\}}
$$

computed separately for each drive's reliability factors.

Meaning: fraction of per-action modulation factors that reinforced scores.

#### `hunger_suppression_rate`, `curiosity_suppression_rate`

$$
\frac{\#\{\mu_t(a) < 1\}}{\#\{\mu_t(a)\}}
$$

computed separately for each drive's reliability factors.

Meaning: fraction of per-action modulation factors that suppressed scores.

Interpretation for reinforcement/suppression rates:

- reinforcement-dominant regimes mean prediction tends to validate actions
- suppression-dominant regimes mean prediction tends to veto or distrust actions

### `system_cw_arbitration`

#### `mean_hunger_weight`, `mean_curiosity_weight`

$$
\mathrm{mean}_t(w_H(t)),\qquad \mathrm{mean}_t(w_C(t))
$$

Meaning: average arbitration weights after hunger gating.

#### `curiosity_dominance_rate`

$$
\frac{\#\{t : w_C(t)>w_H(t)\}}{K}
$$

Meaning: fraction of arbitrated steps where curiosity outweighed hunger.

#### `mean_curiosity_activation`

$$
\mathrm{mean}_t(d_C(t))
$$

Meaning: average curiosity activation.

#### `curiosity_pressure_rate`

$$
\frac{\#\{t : w_C(t)\,d_C(t) > w_H(t)\,d_H(t)\}}{K}
$$

Meaning: fraction of arbitrated steps where curiosity exerted more effective
pressure than hunger.

Interpretation:

- higher means curiosity was the stronger weighted drive more often
- lower means hunger still dominated even when curiosity remained nonzero

#### `prediction_weighted_curiosity_pressure`

$$
\mathrm{mean}_t\big(w_C(t)\,d_C(t)\,\omega_t^{novelty}\big)
$$

Meaning: curiosity pressure scaled by novelty-sensitive predictive weighting.

Interpretation:

- higher means curiosity is not only active, but predictively salient

#### `prediction_weighted_hunger_pressure`

$$
\mathrm{mean}_t\big(w_H(t)\,d_H(t)\big)
$$

Meaning: average effective hunger pressure entering the predictive regime.

Interpretation:

- larger values indicate hunger remained strongly behaviorally relevant

### `system_cw_curiosity`

#### `mean_spatial_novelty`, `mean_sensory_novelty`, `mean_composite_novelty`

Same definitions as in `system_aw`, but measured inside the `system_cw` traces.

Interpretation:

- these show what curiosity saw while prediction was also shaping behavior

#### `curiosity_led_move_rate`

$$
\frac{\#\{t : w_C(t)\,d_C(t) > w_H(t)\,d_H(t) \land a_t\in\mathcal{M}\}}{K}
$$

Meaning: how often curiosity pressure turned into movement.

#### `consume_under_curiosity_pressure_rate`

$$
\frac{\#\{t : w_C(t)\,d_C(t) > w_H(t)\,d_H(t) \land a_t=\mathrm{CONSUME}\}}
{\#\{t : w_C(t)\,d_C(t) > w_H(t)\,d_H(t)\}}
$$

Meaning: how often the system still consumed despite curiosity pressure.

Interpretation:

- `None` means no step satisfied the relative curiosity-pressure condition

#### `novel_move_yield_mean`

$$
\mathrm{mean}_t(\mathrm{actual\_curiosity\_yield}_t)
$$

over movement prediction steps.

Meaning: average realized curiosity-side yield of movement.

Interpretation:

- higher means exploratory moves were actually yielding curiosity-relevant gains

#### `novel_move_success_rate`

$$
\frac{\#\{t : a_t\in\mathcal{M} \land \mathrm{actual\_curiosity\_yield}_t > 0\}}
{\#\{t : a_t\in\mathcal{M} \land \text{prediction active}\}}
$$

Meaning: fraction of movement prediction steps with positive curiosity payoff.

Interpretation:

- higher means novelty-seeking motion is paying off empirically

### `system_cw_world_model`

These metrics are defined exactly as in `system_aw_world_model`:

- `world_model_unique_cells`
- `mean_visit_count_at_current`
- `world_model_revisit_ratio`

The interpretation is the same, but now in a predictive dual-drive system.

### `system_cw_prediction_impact`

These metrics ask a counterfactual question:

> How much did prediction actually change the final behavior, not just the
> internal scores?

#### `behavioral_prediction_impact_rate`

Let $\psi_t$ be the final combined scores and $\psi_t^{cf}$ the stored
counterfactual combined scores without predictive modulation. Then:

$$
\frac{\#\{t : \mathrm{rank}(\psi_t)\neq \mathrm{rank}(\psi_t^{cf})\}}
{\#\{t : \psi_t,\psi_t^{cf}\text{ both available}\}}
$$

Meaning: fraction of eligible steps where prediction changed the full action ranking.

Interpretation:

- broader than top-action change
- captures subtler reordering even if the winner stays the same

#### `prediction_changed_top_action_rate`

$$
\frac{\#\{t : \arg\max \psi_t \neq \arg\max \psi_t^{cf}\}}
{\#\{t : \psi_t,\psi_t^{cf}\text{ both available}\}}
$$

Meaning: fraction of eligible steps where prediction changed the winning action.

Interpretation:

- the most direct “did prediction change behavior?” metric

#### `prediction_changed_arbitrated_margin`

If $\mathrm{margin}(x)$ is the difference between the top-1 and top-2 score:

$$
\mathrm{mean}_t\left(\mathrm{margin}(\psi_t)-\mathrm{margin}(\psi_t^{cf})\right)
$$

Meaning: average change in decisiveness of the final arbitrated choice due to prediction.

Interpretation:

- positive means prediction tends to sharpen the winner
- negative means prediction tends to flatten or destabilize the margin

#### `nonmove_curiosity_penalty_rate`

$$
\frac{\#\{t : a_t\notin\mathcal{M} \land \text{nonmove curiosity penalty used}\}}
{\#\{t : a_t\notin\mathcal{M} \land \text{prediction active}\}}
$$

Meaning: rate at which the special curiosity penalty for non-movement was activated.

Interpretation:

- high values mean the system frequently had to downweight curiosity for stay/consume-like actions

#### `counterfactual_hunger_modulation_impact`

$$
\mathrm{mean}_t\left(\mathbf{1}\left[\arg\max \psi_t \neq
\arg\max \psi_t^{(-H\ pred)}\right]\right)
$$

where $\psi_t^{(-H\ pred)}$ is the stored counterfactual final score vector
without hunger-side prediction.

Meaning: fraction of eligible steps where removing hunger-side prediction would
change the chosen action.

#### `counterfactual_curiosity_modulation_impact`

$$
\mathrm{mean}_t\left(\mathbf{1}\left[\arg\max \psi_t \neq
\arg\max \psi_t^{(-C\ pred)}\right]\right)
$$

where $\psi_t^{(-C\ pred)}$ is the stored counterfactual final score vector
without curiosity-side prediction.

Meaning: fraction of eligible steps where removing curiosity-side prediction
would change the chosen action.

Interpretation for both counterfactual impact metrics:

- they isolate which predictive branch actually mattered to behavior
- comparing them reveals whether hunger-side or curiosity-side prediction was more behaviorally decisive

## 8. Practical Reading Guide

When reading a run summary or metrics log:

1. Start with `mean_steps`, `death_rate`, and `mean_final_vitality`.
2. Use framework metrics to classify the behavioral regime:
   resource extraction, efficiency, movement failure, entropy, coverage, revisiting.
3. Then inspect system-specific metrics:
   arbitration for motivational balance, prediction/traces for internal trust,
   and prediction-impact metrics for actual behavioral effect.

Good high-signal combinations:

- `resource_gain_per_step` + `net_energy_efficiency`
- `unique_cells_visited` + `revisit_rate`
- `mean_curiosity_weight` + `curiosity_dominance_rate`
- `prediction_modulation_strength` + `prediction_changed_top_action_rate`
- `trace_divergence_mean` + `counterfactual_*_modulation_impact`
