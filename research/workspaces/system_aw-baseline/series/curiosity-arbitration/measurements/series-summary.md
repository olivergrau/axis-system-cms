# System A+W Curiosity and Arbitration Series

A compact single-system series for System A+W that probes how curiosity, arbitration, novelty style, and survival pressure reshape behavior relative to a neutral A+W baseline configuration.


## Overview

- Experiments executed: 8
- Baseline experiment: `exp_01`

## At A Glance

| Experiment | Death rate | Mean vitality | Gain/step | Energy eff. | Unique cells | Candidate surv. | Reference surv. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `exp_01` | 0.620 | 0.276 | 0.703 | 0.794 | 59.260 | 0.380 | 0.380 |
| `exp_02` | 0.620 | 0.238 | 0.602 | 0.620 | 146.560 | 0.380 | 0.380 |
| `exp_03` | 0.560 | 0.220 | 0.544 | 0.559 | 131.800 | 0.440 | 0.380 |
| `exp_04` | 0.440 | 0.403 | 0.653 | 0.675 | 153.940 | 0.560 | 0.380 |
| `exp_05` | 0.580 | 0.245 | 0.589 | 0.607 | 139.600 | 0.420 | 0.380 |
| `exp_06` | 0.700 | 0.148 | 0.530 | 0.544 | 117.860 | 0.300 | 0.380 |
| `exp_07` | 0.920 | 0.038 | 0.395 | 0.404 | 144.600 | 0.080 | 0.380 |
| `exp_08` | 0.440 | 0.289 | 0.630 | 0.648 | 102.320 | 0.560 | 0.380 |

## Progression View

- `exp_01` establishes the baseline for the series.
- `exp_02` vs `exp_01`: death_rate +0.000, net_energy_efficiency -0.174, unique_cells_visited +87.300
- `exp_03` vs `exp_02`: death_rate -0.060, net_energy_efficiency -0.061, unique_cells_visited -14.760
- `exp_04` vs `exp_03`: death_rate -0.120, net_energy_efficiency +0.116, unique_cells_visited +22.140
- `exp_05` vs `exp_04`: death_rate +0.140, net_energy_efficiency -0.068, unique_cells_visited -14.340
- `exp_06` vs `exp_05`: death_rate +0.120, net_energy_efficiency -0.063, unique_cells_visited -21.740
- `exp_07` vs `exp_06`: death_rate +0.220, net_energy_efficiency -0.140, unique_cells_visited +26.740
- `exp_08` vs `exp_07`: death_rate -0.480, net_energy_efficiency +0.244, unique_cells_visited -42.280

## Baseline View

- `exp_02` vs `exp_01`: death_rate +0.000, net_energy_efficiency -0.174, unique_cells_visited +87.300
- `exp_03` vs `exp_01`: death_rate -0.060, net_energy_efficiency -0.235, unique_cells_visited +72.540
- `exp_04` vs `exp_01`: death_rate -0.180, net_energy_efficiency -0.119, unique_cells_visited +94.680
- `exp_05` vs `exp_01`: death_rate -0.040, net_energy_efficiency -0.187, unique_cells_visited +80.340
- `exp_06` vs `exp_01`: death_rate +0.080, net_energy_efficiency -0.250, unique_cells_visited +58.600
- `exp_07` vs `exp_01`: death_rate +0.300, net_energy_efficiency -0.390, unique_cells_visited +85.340
- `exp_08` vs `exp_01`: death_rate -0.180, net_energy_efficiency -0.145, unique_cells_visited +43.060

## Baseline Comparison View

- `exp_01` current survival 0.380 vs baseline 0.380; mean trajectory distance 0.000; final vitality delta 0.000
- `exp_02` current survival 0.380 vs baseline 0.380; mean trajectory distance 11.045; final vitality delta -0.038
- `exp_03` current survival 0.440 vs baseline 0.380; mean trajectory distance 11.632; final vitality delta -0.056
- `exp_04` current survival 0.560 vs baseline 0.380; mean trajectory distance 11.711; final vitality delta 0.127
- `exp_05` current survival 0.420 vs baseline 0.380; mean trajectory distance 10.680; final vitality delta -0.032
- `exp_06` current survival 0.300 vs baseline 0.380; mean trajectory distance 11.535; final vitality delta -0.128
- `exp_07` current survival 0.080 vs baseline 0.380; mean trajectory distance 11.541; final vitality delta -0.238
- `exp_08` current survival 0.560 vs baseline 0.380; mean trajectory distance 10.940; final vitality delta 0.013

## Experiment Notes

### System A Reduction Check (`exp_01`)

- Measurement directory: `series/curiosity-arbitration/measurements/experiment_1`
- Candidate experiment: `d399e549ce624851ad46de2b8aa6ae84`
- Reference experiment: `d399e549ce624851ad46de2b8aa6ae84`
- Hypotheses:
  - Curiosity pressure should collapse to zero or near zero.
  - Behavior should become dominated by resource-seeking and consumption.
  - Coverage and exploration diversity should fall relative to baseline.
  - Survival may improve or worsen depending on resource density, but behavior should be easier to interpret.

### Baseline Anchor (`exp_02`)

- Measurement directory: `series/curiosity-arbitration/measurements/experiment_2`
- Candidate experiment: `f6007c77281445359cd80f28805f8f35`
- Reference experiment: `d399e549ce624851ad46de2b8aa6ae84`
- Hypotheses:
  - The baseline should show an alternating explore-versus-exploit pattern.
  - Curiosity should be behaviorally relevant while energy is high.
  - Hunger should increasingly dominate as energy decreases.
  - The run should provide a stable comparison point for all later variants.

### Exploration-Biased A+W (`exp_03`)

- Measurement directory: `series/curiosity-arbitration/measurements/experiment_3`
- Candidate experiment: `b9dd7afa48f04cf5be38754a7792b713`
- Reference experiment: `d399e549ce624851ad46de2b8aa6ae84`
- Hypotheses:
  - Unique cells visited should increase relative to baseline.
  - Curiosity pressure should increase, especially in early episode phases.
  - Resource gain per step may decline because the agent explores more than it harvests.
  - Death rate may increase if exploration overrides local survival opportunities.

### Survival-Biased A+W (`exp_04`)

- Measurement directory: `series/curiosity-arbitration/measurements/experiment_4`
- Candidate experiment: `15df429bdbbe49bdadaf9ce30a863f7e`
- Reference experiment: `d399e549ce624851ad46de2b8aa6ae84`
- Hypotheses:
  - Death rate should decrease relative to exploration-biased variants.
  - Mean final vitality should improve if resources are locally available.
  - Coverage should decrease because curiosity has less room to dominate.
  - Successful consume rate should increase relative to baseline.

### Sharp Hunger-Curiosity Handoff (`exp_05`)

- Measurement directory: `series/curiosity-arbitration/measurements/experiment_5`
- Candidate experiment: `00eb967e98ed4bdd8c75fe7d6f337324`
- Reference experiment: `d399e549ce624851ad46de2b8aa6ae84`
- Hypotheses:
  - Curiosity should dominate clearly at high energy.
  - Hunger should take over abruptly once energy drops far enough.
  - Traces should show cleaner phase separation than the baseline.
  - Mid-range blended behavior should decrease.

### Soft Blended Drives (`exp_06`)

- Measurement directory: `series/curiosity-arbitration/measurements/experiment_6`
- Candidate experiment: `c8651ddfa1cc43a1a37de55abf66e480`
- Reference experiment: `d399e549ce624851ad46de2b8aa6ae84`
- Hypotheses:
  - The transition from exploration to foraging should become smoother.
  - Curiosity should remain relevant deeper into medium-hunger regimes.
  - Behavior may become more robust but less cleanly phase-separated.
  - Survival may worsen if curiosity interferes with urgent consumption.

### Spatial Novelty Dominant (`exp_07`)

- Measurement directory: `series/curiosity-arbitration/measurements/experiment_7`
- Candidate experiment: `d3545525ae5c45f994d87f6f8dd64bb8`
- Reference experiment: `d399e549ce624851ad46de2b8aa6ae84`
- Hypotheses:
  - Unique cells visited should increase relative to baseline.
  - Revisit rate should decrease if unvisited cells remain available.
  - The agent should behave more like a spatial explorer than a stimulus seeker.
  - Resource efficiency may decline if spatial novelty pulls the agent away from resource-rich regions.

### Sensory Novelty Dominant (`exp_08`)

- Measurement directory: `series/curiosity-arbitration/measurements/experiment_8`
- Candidate experiment: `bee2ea945d4f4f42b19eba41d940e903`
- Reference experiment: `d399e549ce624851ad46de2b8aa6ae84`
- Hypotheses:
  - The agent should react more strongly to changing local resource patterns.
  - Revisit behavior may increase if regenerated or changing areas remain sensory-interesting.
  - Coverage may be lower than in the spatial-novelty-dominant variant.
  - Resource gain may improve in regenerating worlds if sensory novelty correlates with food availability.
