# System A vs System A+W Parameter Variations

Candidate-side series for comparing the System A baseline against targeted System A+W parameter regimes while keeping the world, seed, and execution budget fixed.


## Overview

- Experiments executed: 6
- Baseline experiment: `exp_01`

## At A Glance

| Experiment | Death rate | Mean vitality | Gain/step | Energy eff. | Unique cells | Candidate surv. | Reference surv. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `exp_01` | 0.640 | 0.277 | 0.735 | 0.831 | 61.560 | 0.360 | 0.360 |
| `exp_02` | 0.420 | 0.404 | 0.653 | 0.675 | 153.500 | 0.580 | 0.360 |
| `exp_03` | 0.520 | 0.327 | 0.617 | 0.637 | 160.500 | 0.480 | 0.360 |
| `exp_04` | 0.600 | 0.286 | 0.579 | 0.597 | 158.600 | 0.400 | 0.360 |
| `exp_05` | 0.700 | 0.167 | 0.473 | 0.486 | 156.220 | 0.300 | 0.360 |
| `exp_06` | 0.320 | 0.520 | 0.710 | 0.735 | 109.080 | 0.680 | 0.360 |

## Progression View

- `exp_01` establishes the baseline for the series.
- `exp_02` vs `exp_01`: death_rate -0.220, net_energy_efficiency -0.157, unique_cells_visited +91.940
- `exp_03` vs `exp_02`: death_rate +0.100, net_energy_efficiency -0.037, unique_cells_visited +7.000
- `exp_04` vs `exp_03`: death_rate +0.080, net_energy_efficiency -0.040, unique_cells_visited -1.900
- `exp_05` vs `exp_04`: death_rate +0.100, net_energy_efficiency -0.111, unique_cells_visited -2.380
- `exp_06` vs `exp_05`: death_rate -0.380, net_energy_efficiency +0.249, unique_cells_visited -47.140

## Baseline View

- `exp_02` vs `exp_01`: death_rate -0.220, net_energy_efficiency -0.157, unique_cells_visited +91.940
- `exp_03` vs `exp_01`: death_rate -0.120, net_energy_efficiency -0.194, unique_cells_visited +98.940
- `exp_04` vs `exp_01`: death_rate -0.040, net_energy_efficiency -0.235, unique_cells_visited +97.040
- `exp_05` vs `exp_01`: death_rate +0.060, net_energy_efficiency -0.345, unique_cells_visited +94.660
- `exp_06` vs `exp_01`: death_rate -0.320, net_energy_efficiency -0.096, unique_cells_visited +47.520

## Reference-System View

- `exp_01` candidate survival 0.360 vs reference 0.360; mean trajectory distance 0.000; final vitality delta 0.000
- `exp_02` candidate survival 0.580 vs reference 0.360; mean trajectory distance 11.336; final vitality delta 0.127
- `exp_03` candidate survival 0.480 vs reference 0.360; mean trajectory distance 11.178; final vitality delta 0.050
- `exp_04` candidate survival 0.400 vs reference 0.360; mean trajectory distance 11.735; final vitality delta 0.009
- `exp_05` candidate survival 0.300 vs reference 0.360; mean trajectory distance 11.441; final vitality delta -0.110
- `exp_06` candidate survival 0.680 vs reference 0.360; mean trajectory distance 10.805; final vitality delta 0.243

## Experiment Notes

### A+W Reduction Check (`exp_01`)

- Measurement directory: `series/system-parameter-variations/measurements/experiment_1`
- Candidate experiment: `94d78781857d479d8f499f893ad91221`
- Reference experiment: `d9bfa54216564f78a8e6cfaf9656ab1d`
- Hypotheses:
  - Action mismatch against System A should shrink relative to the more exploratory A+W settings.
  - Coverage should contract and revisit rate should rise toward the System A baseline.
  - Any residual differences should mainly reflect implementation details rather than active curiosity.

### Current Workspace Anchor (`exp_02`)

- Measurement directory: `series/system-parameter-variations/measurements/experiment_2`
- Candidate experiment: `4cf6ccf8080e454bb77a928cb641f1c1`
- Reference experiment: `0979097c35d24afe8fc69f63e95d9d4d`
- Hypotheses:
  - The run should preserve the current moderate-exploration A+W profile.
  - It should outperform the more aggressive explorer on survival while remaining more exploratory than System A.
  - This serves as the local baseline for interpreting the other A+W variants.

### Conservative Foraging Explorer (`exp_03`)

- Measurement directory: `series/system-parameter-variations/measurements/experiment_3`
- Candidate experiment: `d8a5fabe3644422094074f85b55b7e7b`
- Reference experiment: `648308a3c6cf45be9967a803569fe540`
- Hypotheses:
  - Death rate and final vitality should improve relative to the anchor if the current candidate still over-explores.
  - Coverage should remain above System A, but below the more exploratory variants.
  - Consume frequency and resource efficiency should improve if curiosity becomes less disruptive.

### Sharp Hunger Curiosity Handoff (`exp_04`)

- Measurement directory: `series/system-parameter-variations/measurements/experiment_4`
- Candidate experiment: `296a62b63b8348a4964fcafa0302066c`
- Reference experiment: `d626c1cd37bc47eaa32b684d7c55bc56`
- Hypotheses:
  - Behavioral phases should separate more clearly than in the anchor.
  - Early-episode coverage should rise without necessarily increasing late-episode waste.
  - If the switch happens at the right time, survival may improve despite stronger early exploration.

### Spatial Novelty Explorer (`exp_05`)

- Measurement directory: `series/system-parameter-variations/measurements/experiment_5`
- Candidate experiment: `e8f2bfb2177e46208f13e697bbace06f`
- Reference experiment: `1cc4dad22cfe485ca54d6b223c3eee8a`
- Hypotheses:
  - Unique cells visited should increase and revisit rate should fall.
  - Performance may suffer if the agent is pulled away from productive clusters too aggressively.
  - Comparison traces should show larger trajectory divergence from System A than the conservative settings.

### Sensory Opportunist (`exp_06`)

- Measurement directory: `series/system-parameter-variations/measurements/experiment_6`
- Candidate experiment: `5fdf837e9f964b0892116f8adfeefde0`
- Reference experiment: `900eb3d4297d4c8f882a8d33f3caa6a9`
- Hypotheses:
  - Revisit behavior may increase if regenerated cells stay behaviorally interesting.
  - Resource gain can improve relative to the spatial explorer when local change correlates with food availability.
  - Coverage should remain above System A but below the strongest spatial-novelty variant.
