# System A vs System A+W World Variations

Shared-world comparison series for System A versus System A+W. Both sides keep their system parameters fixed while the environment is varied symmetrically across reference and candidate configs.


## Overview

- Experiments executed: 7
- Baseline experiment: `exp_01`

## At A Glance

| Experiment | Death rate | Mean vitality | Gain/step | Energy eff. | Unique cells | Candidate surv. | Reference surv. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `exp_01` | 0.220 | 0.568 | 0.677 | 0.703 | 80.280 | 0.780 | 0.620 |
| `exp_02` | 0.000 | 0.842 | 0.891 | 0.918 | 57.100 | 1.000 | 1.000 |
| `exp_03` | 0.460 | 0.206 | 0.481 | 0.497 | 118.340 | 0.540 | 0.040 |
| `exp_04` | 0.220 | 0.572 | 0.682 | 0.702 | 73.980 | 0.780 | 0.580 |
| `exp_05` | 0.020 | 0.740 | 0.824 | 0.856 | 80.320 | 0.980 | 0.720 |
| `exp_06` | 0.000 | 0.812 | 0.875 | 0.903 | 42.380 | 1.000 | 1.000 |
| `exp_07` | 0.260 | 0.507 | 0.624 | 0.644 | 89.480 | 0.740 | 0.540 |

## Progression View

- `exp_01` establishes the baseline for the series.
- `exp_02` vs `exp_01`: death_rate -0.220, net_energy_efficiency +0.216, unique_cells_visited -23.180
- `exp_03` vs `exp_02`: death_rate +0.460, net_energy_efficiency -0.422, unique_cells_visited +61.240
- `exp_04` vs `exp_03`: death_rate -0.240, net_energy_efficiency +0.206, unique_cells_visited -44.360
- `exp_05` vs `exp_04`: death_rate -0.200, net_energy_efficiency +0.154, unique_cells_visited +6.340
- `exp_06` vs `exp_05`: death_rate -0.020, net_energy_efficiency +0.047, unique_cells_visited -37.940
- `exp_07` vs `exp_06`: death_rate +0.260, net_energy_efficiency -0.259, unique_cells_visited +47.100

## Baseline View

- `exp_02` vs `exp_01`: death_rate -0.220, net_energy_efficiency +0.216, unique_cells_visited -23.180
- `exp_03` vs `exp_01`: death_rate +0.240, net_energy_efficiency -0.206, unique_cells_visited +38.060
- `exp_04` vs `exp_01`: death_rate +0.000, net_energy_efficiency -0.000, unique_cells_visited -6.300
- `exp_05` vs `exp_01`: death_rate -0.200, net_energy_efficiency +0.153, unique_cells_visited +0.040
- `exp_06` vs `exp_01`: death_rate -0.220, net_energy_efficiency +0.201, unique_cells_visited -37.900
- `exp_07` vs `exp_01`: death_rate +0.040, net_energy_efficiency -0.059, unique_cells_visited +9.200

## Reference-System View

- `exp_01` candidate survival 0.780 vs reference 0.620; mean trajectory distance 10.298; final vitality delta 0.105
- `exp_02` candidate survival 1.000 vs reference 1.000; mean trajectory distance 13.737; final vitality delta -0.151
- `exp_03` candidate survival 0.540 vs reference 0.040; mean trajectory distance 10.763; final vitality delta 0.200
- `exp_04` candidate survival 0.780 vs reference 0.580; mean trajectory distance 9.838; final vitality delta 0.082
- `exp_05` candidate survival 0.980 vs reference 0.720; mean trajectory distance 10.215; final vitality delta 0.192
- `exp_06` candidate survival 1.000 vs reference 1.000; mean trajectory distance 8.464; final vitality delta -0.180
- `exp_07` candidate survival 0.740 vs reference 0.540; mean trajectory distance 12.337; final vitality delta 0.092

## Experiment Notes

### Baseline World Anchor (`exp_01`)

- Measurement directory: `series/world-variations/measurements/experiment_1`
- Candidate experiment: `e6c3d617e01f46b6bd4bceb522bf598f`
- Reference experiment: `f0bd896e9a8e4341af7d10b6cee888b8`
- Hypotheses:
  - This should reproduce the current reference-versus-candidate contrast under the clustered bounded world.
  - Later world manipulations can be interpreted relative to this shared anchor rather than to older manual runs.

### Open World with Fast Uniform Regeneration (`exp_02`)

- Measurement directory: `series/world-variations/measurements/experiment_2`
- Candidate experiment: `09b8ca55f1f24ca4ab1f52a06b47e664`
- Reference experiment: `f7a863957a3348aa9e6f24ff1fa433b0`
- Hypotheses:
  - The performance gap between A and A+W may narrow or reverse if exploration is rewarded by rapid local change.
  - Revisit-heavy behavior from System A may become less costly because food recovers quickly.
  - A+W may still retain a coverage advantage, but with less survival penalty than in the baseline world.

### Sparse Scarcity Patches (`exp_03`)

- Measurement directory: `series/world-variations/measurements/experiment_3`
- Candidate experiment: `b8f460c96f2f469d8cd9d6bf59e649ad`
- Reference experiment: `11c24efa89d94af48f6b710e91c0e4ba`
- Hypotheses:
  - System A may benefit from its stronger exploitation bias if productive cells are sparse.
  - A+W may cover more ground but pay for it with lower energy efficiency.
  - The comparison should reveal whether curiosity helps discovery enough to offset scarcity costs.

### Rich Cluster Islands (`exp_04`)

- Measurement directory: `series/world-variations/measurements/experiment_4`
- Candidate experiment: `26fe4e48c64e4f138765206e948edb8f`
- Reference experiment: `63690d0c34144bd1b535bb02ef8bd61e`
- Hypotheses:
  - System A may do well once it settles into a productive island.
  - A+W may outperform if sensory or spatial novelty helps it relocate rich hubs after depletion.
  - Revisit structure should become a more informative discriminator than pure coverage.

### Toroidal Wraparound Grid (`exp_05`)

- Measurement directory: `series/world-variations/measurements/experiment_5`
- Candidate experiment: `ee73ccc98893486a9a883cf05fd22a88`
- Reference experiment: `c3e2e09bf2ef417f9759011118f91722`
- Hypotheses:
  - Trajectories should become less edge-constrained for both systems.
  - A+W may convert its exploratory tendency into more coherent long loops rather than boundary collisions.
  - The fairness of the side-by-side comparison is preserved because both systems face the same topology shift.

### Compact Dense Feedback Arena (`exp_06`)

- Measurement directory: `series/world-variations/measurements/experiment_6`
- Candidate experiment: `383646731bea431dac9ce2750ff91685`
- Reference experiment: `c71cb2d7bdaf490bbacde5697c869be6`
- Hypotheses:
  - System A's exploitation bias may become more competitive in the tighter arena.
  - A+W may lose some of its coverage advantage because the search space is smaller.
  - Revisit metrics should rise for both systems, but possibly for different reasons.

### Large Open Field (`exp_07`)

- Measurement directory: `series/world-variations/measurements/experiment_7`
- Candidate experiment: `284dade3e7b041068f3e6417535519fc`
- Reference experiment: `13a9d67f3b99408f9d200c2a2d9e8468`
- Hypotheses:
  - System A may struggle to rediscover productive areas in the larger arena.
  - A+W may gain relative value if curiosity helps maintain broad search coverage.
  - Absolute coverage should rise for both, but the candidate may preserve a larger proportional lead.
