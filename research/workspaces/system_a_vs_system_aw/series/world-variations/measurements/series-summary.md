# System A vs System A+W World Variations

Shared-world comparison series for System A versus System A+W. Both sides keep their system parameters fixed while the environment is varied symmetrically across reference and candidate configs.


## Overview

- Experiments executed: 7
- Baseline experiment: `exp_01`

## At A Glance

| Experiment | Death rate | Mean vitality | Gain/step | Energy eff. | Unique cells | Candidate surv. | Reference surv. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `exp_01` | 0.320 | 0.520 | 0.710 | 0.735 | 109.080 | 0.680 | 0.360 |
| `exp_02` | 0.000 | 0.842 | 0.929 | 0.959 | 65.220 | 1.000 | 1.000 |
| `exp_03` | 0.840 | 0.056 | 0.478 | 0.492 | 142.780 | 0.160 | 0.000 |
| `exp_04` | 0.460 | 0.402 | 0.665 | 0.684 | 113.860 | 0.540 | 0.440 |
| `exp_05` | 0.060 | 0.726 | 0.878 | 0.910 | 116.980 | 0.940 | 0.420 |
| `exp_06` | 0.000 | 0.821 | 0.923 | 0.954 | 49.480 | 1.000 | 1.000 |
| `exp_07` | 0.440 | 0.403 | 0.628 | 0.648 | 121.460 | 0.560 | 0.400 |

## Progression View

- `exp_01` establishes the baseline for the series.
- `exp_02` vs `exp_01`: death_rate -0.320, net_energy_efficiency +0.224, unique_cells_visited -43.860
- `exp_03` vs `exp_02`: death_rate +0.840, net_energy_efficiency -0.467, unique_cells_visited +77.560
- `exp_04` vs `exp_03`: death_rate -0.380, net_energy_efficiency +0.192, unique_cells_visited -28.920
- `exp_05` vs `exp_04`: death_rate -0.400, net_energy_efficiency +0.226, unique_cells_visited +3.120
- `exp_06` vs `exp_05`: death_rate -0.060, net_energy_efficiency +0.044, unique_cells_visited -67.500
- `exp_07` vs `exp_06`: death_rate +0.440, net_energy_efficiency -0.306, unique_cells_visited +71.980

## Baseline View

- `exp_02` vs `exp_01`: death_rate -0.320, net_energy_efficiency +0.224, unique_cells_visited -43.860
- `exp_03` vs `exp_01`: death_rate +0.520, net_energy_efficiency -0.243, unique_cells_visited +33.700
- `exp_04` vs `exp_01`: death_rate +0.140, net_energy_efficiency -0.051, unique_cells_visited +4.780
- `exp_05` vs `exp_01`: death_rate -0.260, net_energy_efficiency +0.174, unique_cells_visited +7.900
- `exp_06` vs `exp_01`: death_rate -0.320, net_energy_efficiency +0.218, unique_cells_visited -59.600
- `exp_07` vs `exp_01`: death_rate +0.120, net_energy_efficiency -0.087, unique_cells_visited +12.380

## Reference-System View

- `exp_01` candidate survival 0.680 vs reference 0.360; mean trajectory distance 10.805; final vitality delta 0.243
- `exp_02` candidate survival 1.000 vs reference 1.000; mean trajectory distance 15.651; final vitality delta -0.152
- `exp_03` candidate survival 0.160 vs reference 0.000; mean trajectory distance 10.769; final vitality delta 0.056
- `exp_04` candidate survival 0.540 vs reference 0.440; mean trajectory distance 10.617; final vitality delta 0.041
- `exp_05` candidate survival 0.940 vs reference 0.420; mean trajectory distance 10.438; final vitality delta 0.400
- `exp_06` candidate survival 1.000 vs reference 1.000; mean trajectory distance 8.696; final vitality delta -0.173
- `exp_07` candidate survival 0.560 vs reference 0.400; mean trajectory distance 13.056; final vitality delta 0.067

## Experiment Notes

### Baseline World Anchor (`exp_01`)

- Measurement directory: `series/world-variations/measurements/experiment_1`
- Candidate experiment: `b63099bd666444c4ae03db4d16963398`
- Reference experiment: `f0524efb4f54402db9cdea0db8b629d6`
- Hypotheses:
  - This should reproduce the current reference-versus-candidate contrast under the clustered bounded world.
  - Later world manipulations can be interpreted relative to this shared anchor rather than to older manual runs.

### Open World with Fast Uniform Regeneration (`exp_02`)

- Measurement directory: `series/world-variations/measurements/experiment_2`
- Candidate experiment: `6e19b443e04347c58bb4a25bf1e3824a`
- Reference experiment: `acac6e4389704778aca2254d89f5819b`
- Hypotheses:
  - The performance gap between A and A+W may narrow or reverse if exploration is rewarded by rapid local change.
  - Revisit-heavy behavior from System A may become less costly because food recovers quickly.
  - A+W may still retain a coverage advantage, but with less survival penalty than in the baseline world.

### Sparse Scarcity Patches (`exp_03`)

- Measurement directory: `series/world-variations/measurements/experiment_3`
- Candidate experiment: `629e7b3519814577bbf572a906e08563`
- Reference experiment: `e686bf7c138e41898e1022a1eec106e9`
- Hypotheses:
  - System A may benefit from its stronger exploitation bias if productive cells are sparse.
  - A+W may cover more ground but pay for it with lower energy efficiency.
  - The comparison should reveal whether curiosity helps discovery enough to offset scarcity costs.

### Rich Cluster Islands (`exp_04`)

- Measurement directory: `series/world-variations/measurements/experiment_4`
- Candidate experiment: `d15fe6d5c88c4b06beb8982735cf050f`
- Reference experiment: `1ff5cf68de83487fb721992cf23dfe24`
- Hypotheses:
  - System A may do well once it settles into a productive island.
  - A+W may outperform if sensory or spatial novelty helps it relocate rich hubs after depletion.
  - Revisit structure should become a more informative discriminator than pure coverage.

### Toroidal Wraparound Grid (`exp_05`)

- Measurement directory: `series/world-variations/measurements/experiment_5`
- Candidate experiment: `31eaad8e66e64e66a702f4a646f07f86`
- Reference experiment: `b759160df1ce40bea9ba3e58cafd5c20`
- Hypotheses:
  - Trajectories should become less edge-constrained for both systems.
  - A+W may convert its exploratory tendency into more coherent long loops rather than boundary collisions.
  - The fairness of the side-by-side comparison is preserved because both systems face the same topology shift.

### Compact Dense Feedback Arena (`exp_06`)

- Measurement directory: `series/world-variations/measurements/experiment_6`
- Candidate experiment: `e2768c1543e04ffb9bbba3fa77c328bb`
- Reference experiment: `dedd97a11bc345aebcde4f4e39baf5d8`
- Hypotheses:
  - System A's exploitation bias may become more competitive in the tighter arena.
  - A+W may lose some of its coverage advantage because the search space is smaller.
  - Revisit metrics should rise for both systems, but possibly for different reasons.

### Large Open Field (`exp_07`)

- Measurement directory: `series/world-variations/measurements/experiment_7`
- Candidate experiment: `ad48920b2d3540ffbecff4fdcf03f7a0`
- Reference experiment: `ca4329b79b06457d82df9817c52432f5`
- Hypotheses:
  - System A may struggle to rediscover productive areas in the larger arena.
  - A+W may gain relative value if curiosity helps maintain broad search coverage.
  - Absolute coverage should rise for both, but the candidate may preserve a larger proportional lead.
