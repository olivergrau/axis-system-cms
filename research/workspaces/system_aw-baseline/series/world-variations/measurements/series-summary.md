# System A+W World Variations on Sensory-Novelty Fixed Agent

A world-only series for System A+W with the exp_08 sensory-novelty-dominant agent held fixed. The series probes how topology, regeneration structure, scarcity, and map scale reshape behavior when only the environment changes.


## Overview

- Experiments executed: 8
- Baseline experiment: `exp_01`

## At A Glance

| Experiment | Death rate | Mean vitality | Gain/step | Energy eff. | Unique cells | Candidate surv. | Reference surv. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `exp_01` | 0.440 | 0.289 | 0.630 | 0.648 | 102.320 | 0.560 | 0.560 |
| `exp_02` | 0.000 | 0.569 | 0.864 | 0.889 | 68.180 | 1.000 | 0.560 |
| `exp_03` | 0.940 | 0.012 | 0.431 | 0.442 | 128.540 | 0.060 | 0.560 |
| `exp_04` | 0.480 | 0.293 | 0.608 | 0.625 | 91.860 | 0.520 | 0.560 |
| `exp_05` | 0.180 | 0.435 | 0.762 | 0.786 | 114.880 | 0.820 | 0.560 |
| `exp_06` | 0.500 | 0.282 | 0.602 | 0.619 | 117.140 | 0.500 | 0.560 |
| `exp_07` | 0.000 | 0.563 | 0.862 | 0.887 | 50.380 | 1.000 | 0.560 |
| `exp_08` | 0.400 | 0.323 | 0.672 | 0.690 | 101.460 | 0.600 | 0.560 |

## Progression View

- `exp_01` establishes the baseline for the series.
- `exp_02` vs `exp_01`: death_rate -0.440, net_energy_efficiency +0.241, unique_cells_visited -34.140
- `exp_03` vs `exp_02`: death_rate +0.940, net_energy_efficiency -0.447, unique_cells_visited +60.360
- `exp_04` vs `exp_03`: death_rate -0.460, net_energy_efficiency +0.182, unique_cells_visited -36.680
- `exp_05` vs `exp_04`: death_rate -0.300, net_energy_efficiency +0.162, unique_cells_visited +23.020
- `exp_06` vs `exp_05`: death_rate +0.320, net_energy_efficiency -0.168, unique_cells_visited +2.260
- `exp_07` vs `exp_06`: death_rate -0.500, net_energy_efficiency +0.269, unique_cells_visited -66.760
- `exp_08` vs `exp_07`: death_rate +0.400, net_energy_efficiency -0.197, unique_cells_visited +51.080

## Baseline View

- `exp_02` vs `exp_01`: death_rate -0.440, net_energy_efficiency +0.241, unique_cells_visited -34.140
- `exp_03` vs `exp_01`: death_rate +0.500, net_energy_efficiency -0.206, unique_cells_visited +26.220
- `exp_04` vs `exp_01`: death_rate +0.040, net_energy_efficiency -0.024, unique_cells_visited -10.460
- `exp_05` vs `exp_01`: death_rate -0.260, net_energy_efficiency +0.138, unique_cells_visited +12.560
- `exp_06` vs `exp_01`: death_rate +0.060, net_energy_efficiency -0.030, unique_cells_visited +14.820
- `exp_07` vs `exp_01`: death_rate -0.440, net_energy_efficiency +0.239, unique_cells_visited -51.940
- `exp_08` vs `exp_01`: death_rate -0.040, net_energy_efficiency +0.042, unique_cells_visited -0.860

## Baseline Comparison View

- `exp_01` current survival 0.560 vs baseline 0.560; mean trajectory distance 0.000; final vitality delta 0.000
- `exp_02` current survival 1.000 vs baseline 0.560; mean trajectory distance 15.653; final vitality delta 0.280
- `exp_03` current survival 0.060 vs baseline 0.560; mean trajectory distance 12.861; final vitality delta -0.278
- `exp_04` current survival 0.520 vs baseline 0.560; mean trajectory distance 10.111; final vitality delta 0.003
- `exp_05` current survival 0.820 vs baseline 0.560; mean trajectory distance 9.199; final vitality delta 0.145
- `exp_06` current survival 0.500 vs baseline 0.560; mean trajectory distance 13.947; final vitality delta -0.007
- `exp_07` current survival 1.000 vs baseline 0.560; mean trajectory distance 13.153; final vitality delta 0.274
- `exp_08` current survival 0.600 vs baseline 0.560; mean trajectory distance 6.995; final vitality delta 0.033

## Experiment Notes

### Baseline World Anchor (`exp_01`)

- Measurement directory: `series/world-variations/measurements/experiment_1`
- Candidate experiment: `71a2431c5fb346ef8e76caaacac14120`
- Reference experiment: `71a2431c5fb346ef8e76caaacac14120`
- Hypotheses:
  - This run should reproduce the characteristic sensory-novelty behavior of exp_08.
  - It should serve as the comparison point for every later world variation.
  - Coverage and revisit behavior should sit near the already observed exp_08 pattern.

### Open World with Fast Uniform Regeneration (`exp_02`)

- Measurement directory: `series/world-variations/measurements/experiment_2`
- Candidate experiment: `67c7cfc07f574b12ab6b1efcfa0ef50b`
- Reference experiment: `71a2431c5fb346ef8e76caaacac14120`
- Hypotheses:
  - Sensory novelty should stay high because many cells continue changing.
  - Revisit behavior may increase because previously harvested areas recover quickly.
  - Survival should improve if the agent can exploit recurring local change.

### Sparse Scarcity Patches (`exp_03`)

- Measurement directory: `series/world-variations/measurements/experiment_3`
- Candidate experiment: `d1091c6a75c2425a9b1fdb684b2f0c2b`
- Reference experiment: `71a2431c5fb346ef8e76caaacac14120`
- Hypotheses:
  - Coverage pressure should rise because rewards are spatially sparse.
  - Survival may worsen if sensory novelty keeps the agent moving away from productive cells.
  - Successful exploitation should depend more on finding the right sparse patches.

### Rich Cluster Islands (`exp_04`)

- Measurement directory: `series/world-variations/measurements/experiment_4`
- Candidate experiment: `7d2027b618e64bd4a9a352020ea8899c`
- Reference experiment: `71a2431c5fb346ef8e76caaacac14120`
- Hypotheses:
  - Revisit behavior should increase around the richest changing islands.
  - Resource gain may improve if sensory novelty tracks cluster recovery well.
  - Coverage may shrink because fewer regions remain behaviorally attractive.

### Toroidal Wraparound Grid (`exp_05`)

- Measurement directory: `series/world-variations/measurements/experiment_5`
- Candidate experiment: `c2c7f8643bbb491ba0a014d0ef72b38a`
- Reference experiment: `71a2431c5fb346ef8e76caaacac14120`
- Hypotheses:
  - Edge-avoidance artifacts should disappear.
  - Coverage may increase because traversal paths become less interrupted.
  - Sensory novelty may stay more spatially continuous across former borders.

### Larger Open Field (`exp_06`)

- Measurement directory: `series/world-variations/measurements/experiment_6`
- Candidate experiment: `5230a706beaa497aabea8fd966d6b1df`
- Reference experiment: `71a2431c5fb346ef8e76caaacac14120`
- Hypotheses:
  - Unique cells visited should increase in absolute terms but may fall proportionally.
  - The agent may struggle to repeatedly exploit good regions in a larger search space.
  - Survival may drop if exploration costs outrun rediscovery of resources.

### Compact Dense-Feedback Arena (`exp_07`)

- Measurement directory: `series/world-variations/measurements/experiment_7`
- Candidate experiment: `1cb0b70772f647dbb5daea50795d3d4b`
- Reference experiment: `71a2431c5fb346ef8e76caaacac14120`
- Hypotheses:
  - Revisit behavior should increase because the agent cycles through the same cells more frequently.
  - Sensory novelty may remain high despite lower total coverage.
  - Survival should improve if the tighter world keeps resources within easier reach.

### Long Cooldown Regeneration (`exp_08`)

- Measurement directory: `series/world-variations/measurements/experiment_8`
- Candidate experiment: `2d92173320224b1bafa14f7e7438dd48`
- Reference experiment: `71a2431c5fb346ef8e76caaacac14120`
- Hypotheses:
  - Sensory novelty near harvested regions should collapse for longer periods.
  - The agent may be forced into wider exploration before local recovery becomes visible again.
  - Resource efficiency may worsen if the agent repeatedly checks unrecovered areas.
