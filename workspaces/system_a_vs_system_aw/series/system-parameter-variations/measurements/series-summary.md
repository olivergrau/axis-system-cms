# System A vs System A+W Parameter Variations

Candidate-side series for comparing the System A baseline against targeted System A+W parameter regimes while keeping the world, seed, and execution budget fixed.


## Overview

- Experiments executed: 6
- Baseline experiment: `exp_01`

## At A Glance

| Experiment | Death rate | Mean vitality | Gain/step | Energy eff. | Unique cells | Candidate surv. | Reference surv. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `exp_01` | 0.380 | 0.462 | 0.738 | 0.840 | 47.700 | 0.620 | 0.620 |
| `exp_02` | 0.280 | 0.540 | 0.655 | 0.678 | 108.920 | 0.720 | 0.620 |
| `exp_03` | 0.300 | 0.540 | 0.643 | 0.668 | 109.460 | 0.700 | 0.620 |
| `exp_04` | 0.340 | 0.429 | 0.583 | 0.602 | 120.800 | 0.660 | 0.620 |
| `exp_05` | 0.500 | 0.296 | 0.476 | 0.489 | 121.700 | 0.500 | 0.620 |
| `exp_06` | 0.220 | 0.568 | 0.677 | 0.703 | 80.280 | 0.780 | 0.620 |

## Progression View

- `exp_01` establishes the baseline for the series.
- `exp_02` vs `exp_01`: death_rate -0.100, net_energy_efficiency -0.162, unique_cells_visited +61.220
- `exp_03` vs `exp_02`: death_rate +0.020, net_energy_efficiency -0.010, unique_cells_visited +0.540
- `exp_04` vs `exp_03`: death_rate +0.040, net_energy_efficiency -0.066, unique_cells_visited +11.340
- `exp_05` vs `exp_04`: death_rate +0.160, net_energy_efficiency -0.113, unique_cells_visited +0.900
- `exp_06` vs `exp_05`: death_rate -0.280, net_energy_efficiency +0.213, unique_cells_visited -41.420

## Baseline View

- `exp_02` vs `exp_01`: death_rate -0.100, net_energy_efficiency -0.162, unique_cells_visited +61.220
- `exp_03` vs `exp_01`: death_rate -0.080, net_energy_efficiency -0.172, unique_cells_visited +61.760
- `exp_04` vs `exp_01`: death_rate -0.040, net_energy_efficiency -0.238, unique_cells_visited +73.100
- `exp_05` vs `exp_01`: death_rate +0.120, net_energy_efficiency -0.351, unique_cells_visited +74.000
- `exp_06` vs `exp_01`: death_rate -0.160, net_energy_efficiency -0.137, unique_cells_visited +32.580

## Reference-System View

- `exp_01` candidate survival 0.620 vs reference 0.620; mean trajectory distance 0.000; final vitality delta 0.000
- `exp_02` candidate survival 0.720 vs reference 0.620; mean trajectory distance 10.654; final vitality delta 0.077
- `exp_03` candidate survival 0.700 vs reference 0.620; mean trajectory distance 10.781; final vitality delta 0.077
- `exp_04` candidate survival 0.660 vs reference 0.620; mean trajectory distance 11.402; final vitality delta -0.033
- `exp_05` candidate survival 0.500 vs reference 0.620; mean trajectory distance 11.037; final vitality delta -0.166
- `exp_06` candidate survival 0.780 vs reference 0.620; mean trajectory distance 10.298; final vitality delta 0.105

## Experiment Notes

### A+W Reduction Check (`exp_01`)

- Measurement directory: `series/system-parameter-variations/measurements/experiment_1`
- Candidate experiment: `89b64425e60a4efd8dedbf19ac1ad996`
- Reference experiment: `3f44f07741254c748497604f5820e191`
- Hypotheses:
  - Action mismatch against System A should shrink relative to the more exploratory A+W settings.
  - Coverage should contract and revisit rate should rise toward the System A baseline.
  - Any residual differences should mainly reflect implementation details rather than active curiosity.

### Current Workspace Anchor (`exp_02`)

- Measurement directory: `series/system-parameter-variations/measurements/experiment_2`
- Candidate experiment: `eb51351f642547aa9a02194ae33734f5`
- Reference experiment: `9cef8d0ca55e4f2491e2d2e234d5ae5a`
- Hypotheses:
  - The run should preserve the current moderate-exploration A+W profile.
  - It should outperform the more aggressive explorer on survival while remaining more exploratory than System A.
  - This serves as the local baseline for interpreting the other A+W variants.

### Conservative Foraging Explorer (`exp_03`)

- Measurement directory: `series/system-parameter-variations/measurements/experiment_3`
- Candidate experiment: `2fe59fa7675c42cf9e8fe1332a0da56e`
- Reference experiment: `e8418178e7504e0eb4501249abe0d335`
- Hypotheses:
  - Death rate and final vitality should improve relative to the anchor if the current candidate still over-explores.
  - Coverage should remain above System A, but below the more exploratory variants.
  - Consume frequency and resource efficiency should improve if curiosity becomes less disruptive.

### Sharp Hunger Curiosity Handoff (`exp_04`)

- Measurement directory: `series/system-parameter-variations/measurements/experiment_4`
- Candidate experiment: `ff47b455b3b94bbe960d478aecdfd476`
- Reference experiment: `2b0040fd2aed4093b5d1204b4fc1abe5`
- Hypotheses:
  - Behavioral phases should separate more clearly than in the anchor.
  - Early-episode coverage should rise without necessarily increasing late-episode waste.
  - If the switch happens at the right time, survival may improve despite stronger early exploration.

### Spatial Novelty Explorer (`exp_05`)

- Measurement directory: `series/system-parameter-variations/measurements/experiment_5`
- Candidate experiment: `143d80fe332046e39fb6d99806aabaee`
- Reference experiment: `5455f40a108243ecb73733b1b6f999ee`
- Hypotheses:
  - Unique cells visited should increase and revisit rate should fall.
  - Performance may suffer if the agent is pulled away from productive clusters too aggressively.
  - Comparison traces should show larger trajectory divergence from System A than the conservative settings.

### Sensory Opportunist (`exp_06`)

- Measurement directory: `series/system-parameter-variations/measurements/experiment_6`
- Candidate experiment: `1b65e165385349afbcd0198074ba8eff`
- Reference experiment: `7b79e388b18547adba9ec59e09d14454`
- Hypotheses:
  - Revisit behavior may increase if regenerated cells stay behaviorally interesting.
  - Resource gain can improve relative to the spatial explorer when local change correlates with food availability.
  - Coverage should remain above System A but below the strongest spatial-novelty variant.
