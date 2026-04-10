# WP-11: Validation + Reduction Tests

## Metadata
- Work Package: WP-11
- Title: Validation + Reduction Tests
- System: System A+W
- Source Files: `tests/systems/system_aw/test_worked_examples.py`, `tests/systems/system_aw/test_reduction.py`
- Model Reference: `01_System A+W Model.md`, Section 12 (Reduction to System A) and Section 13 (Validation Criteria)
- Worked Examples: `02_System A+W Worked Examples.md`, all example groups (A through F)
- Dependencies: WP-10 (all components wired and runnable)

---

## 1. Objective

Verify the mathematical correctness of the full System A+W implementation through two classes of tests:

1. **Worked Example Validation:** Reproduce every numerical calculation from the worked examples document and assert that the implementation matches within tolerance.
2. **Reduction Validation:** Verify that System A+W degenerates exactly into System A when curiosity parameters are zeroed (Model Section 12).

This is the "acceptance test suite" for the entire System A+W implementation. Individual WPs have their own unit tests; WP-11 validates the integrated system end-to-end.

---

## 2. Design

### 2.1 Test Strategy

Each worked example is a **fixed-input, known-output** scenario. The tests construct the exact state described in the example, run the computation, and assert numerical outputs match.

Tests use `pytest.approx` with absolute tolerance $\epsilon = 0.01$ for probabilities and $\epsilon = 0.005$ for intermediate values (scores, weights).

### 2.2 Helper Fixtures

To avoid boilerplate, shared fixtures provide:
- `default_params()` → the common parameter set from Worked Examples Section 4
- `make_observation(current, up, down, left, right)` → construct `Observation` from resource/traversability tuples
- `make_memory(entries)` → construct `MemoryState` from a list of observation snapshots
- `make_world_model(position, visits)` → construct `WorldModelState` from a position and visit dict

---

## 3. Worked Example Tests

### File: `tests/systems/system_aw/test_worked_examples.py`

#### Example Group A: Drive Weight Dynamics

| # | Test | Description |
|---|---|---|
| 1 | `test_a1_drive_evaluation` | $e=90$, $E_{\max}=100$ → $d_H=0.10$, $d_C=1.0$ |
| 2 | `test_a1_drive_arbitration` | $d_H=0.10$ → $w_H=0.307$, $w_C=0.810$ |
| 3 | `test_a1_spatial_novelty` | All unvisited → all $\nu^{spatial} = 1.0$ |
| 4 | `test_a1_sensory_novelty` | Empty memory → $\nu^{sensory} = (0.0, 0.0, 0.3, 0.0)$ |
| 5 | `test_a1_composite_novelty` | $\alpha=0.5$ → $\nu = (0.50, 0.50, 0.65, 0.50)$ |
| 6 | `test_a1_hunger_contributions` | Verify all 6 hunger $\phi_H$ values from the table |
| 7 | `test_a1_curiosity_contributions` | Verify all 6 curiosity $\phi_C$ values from the table |
| 8 | `test_a1_combined_scores` | Verify all 6 $\psi(a)$ values: UP=0.405, DOWN=0.405, LEFT=0.536, RIGHT=0.405, CONSUME=-0.182, STAY=-0.246 |
| 9 | `test_a1_probabilities` | Verify all 6 probabilities: UP=0.205, DOWN=0.205, LEFT=0.266, RIGHT=0.205, CONSUME=0.063, STAY=0.056 |
| 10 | `test_a1_conclusion` | Movement collectively > 88%, CONSUME < 7% |

#### Example Group B: Hunger-Curiosity Competition

| # | Test | Description |
|---|---|---|
| 11 | `test_b1_drive_evaluation` | $e=50$ → $d_H=0.50$, $d_C=0.85$ |
| 12 | `test_b1_drive_arbitration` | $d_H=0.50$ → $w_H=0.475$, $w_C=0.250$ |
| 13 | `test_b1_novelty` | Verify spatial, sensory, composite novelty per direction |
| 14 | `test_b1_combined_scores` | Verify all 6 scores (before masking) |
| 15 | `test_b1_masking` | LEFT blocked → $\psi(\text{LEFT}) = -\infty$ |
| 16 | `test_b1_probabilities` | CONSUME=0.283, DOWN=0.231, LEFT=0.000 |

#### Example Group C: Hunger Dominance

| # | Test | Description |
|---|---|---|
| 17 | `test_c1_drive_arbitration` | $d_H=0.95$ → $w_H=0.932$, $w_C=0.003$ |
| 18 | `test_c1_curiosity_contribution_negligible` | All curiosity contributions < 0.002 |
| 19 | `test_c1_combined_scores` | CONSUME=1.106 dominates |
| 20 | `test_c1_probabilities` | CONSUME=0.634, all movements < 0.10 |

#### Example Group D: Forage-Explore Cycle

| # | Test | Description |
|---|---|---|
| 21 | `test_d1_step0_consume_dominates` | $e=40$, $r_c=0.8$ → CONSUME score = 0.614, movement ~0.080 |
| 22 | `test_d1_step0_energy_transition` | After CONSUME: $e = 40 - 1 + 10 \times 0.8 = 47$ |
| 23 | `test_d1_step1_movement_dominates` | $e=47$, $r_c=0$ → CONSUME score negative, movement positive |
| 24 | `test_d1_trajectory_summary` | 4-step sequence: verify energy, $d_H$, $w_C$, dominant drive at each step |

#### Example Group E: Parameter Sensitivity

| # | Test | Description |
|---|---|---|
| 25 | `test_e1_gamma_table` | For $\gamma \in \{0.5, 1.0, 2.0, 4.0\}$: verify $w_H$, $w_C$ at $d_H=0.5$ |
| 26 | `test_e2_alpha_table` | For $\alpha \in \{0.0, 0.5, 1.0\}$: verify composite novelty for cell visited 3 times with $r=0.8$, $\bar{r}=0.1$ |

#### Example Group F: World Model Mechanics

| # | Test | Description |
|---|---|---|
| 27 | `test_f1_trajectory` | 6-step dead reckoning: verify relative position, visit counts, and spatial novelty at final position for all 4 directions |
| 28 | `test_f2_decay_table` | For $w \in \{0, 1, 2, 3, 5, 10, 20, 100\}$: verify $\nu^{spatial}$ |
| 29 | `test_f3_stationary_actions` | 3 stationary actions at $(3,2)$: position unchanged, $w$ increases to 4, $\nu = 0.2$ |

#### Full Pipeline Tests (End-to-End Through SystemAW)

| # | Test | Description |
|---|---|---|
| 30 | `test_a1_full_pipeline` | Construct world matching A1 conditions, run `SystemAW.decide()`, verify selected action probabilities in `decision_data` match A1 |
| 31 | `test_c1_full_pipeline` | Same for C1: verify CONSUME dominance through the full system |

---

## 4. Reduction Tests

### File: `tests/systems/system_aw/test_reduction.py`

#### Model Section 12: Reduction to System A

The formal model states: when $\mu_C = 0$ or $w_C^{base} = 0$, System A+W behavior is identical to System A.

| # | Test | Description |
|---|---|---|
| 32 | `test_reduction_mu_c_zero` | Set `base_curiosity=0.0`. For 5 different (energy, observation) pairs: run both `SystemA.decide()` and `SystemAW.decide()` with same RNG seed. Assert action probabilities match within $\epsilon = 0.001$. |
| 33 | `test_reduction_w_c_base_zero` | Set `curiosity_weight_base=0.0` (in `ArbitrationConfig`). Same test as above — probabilities must match System A. |
| 34 | `test_reduction_multi_step` | With $\mu_C = 0$: run 10 steps through both systems with the same world and seed. Assert identical action sequences (using argmax mode). |
| 35 | `test_reduction_energy_trajectory` | With $\mu_C = 0$: after 10 identical steps, both systems must have identical energy levels. |

#### Boundary Conditions

| # | Test | Description |
|---|---|---|
| 36 | `test_alpha_one_memory_independent` | $\alpha = 1.0$: vary memory contents, verify composite novelty is identical (depends only on visit counts). |
| 37 | `test_alpha_zero_world_model_independent` | $\alpha = 0.0$: vary visit counts in world model, verify composite novelty is identical (depends only on observation + memory). |
| 38 | `test_curiosity_disabled_world_model_updated` | With $\mu_C = 0$: verify the world model is still updated (visit counts increment). The world model is maintained but not read for action selection. |

---

## 5. Validation Criteria Checklist

From Model Section 13, mapped to test coverage:

### 5.1 Structural Consistency

| Criterion | Test Coverage |
|---|---|
| All drive outputs are scalar-valued | WP-5, WP-6 type tests |
| All modulation functions depend only on permitted inputs | WP-6 alpha boundary tests |
| No drive has access to true world state | WP-9 prohibition test (no `new_position` access) |
| Action scores well-defined for all states | WP-11 examples A1-C1 cover full energy range |
| Dynamic weights non-negative | WP-7 tests 4-6 |

### 5.2 Behavioral Validation

| Criterion | Test Coverage |
|---|---|
| At $e = E_{\max}$: exploration dominates | Test #10 (A1 conclusion) |
| At $e \approx 0$: converges to System A | Tests #17-20 (C1) + tests #32-35 (reduction) |
| Forage-explore cycle emerges | Tests #21-24 (D1 trajectory) |
| Visit counts increase coverage | Test #27 (F1 trajectory) |

### 5.3 Reduction Validation

| Criterion | Test Coverage |
|---|---|
| $\mu_C = 0$: matches System A | Tests #32, #34, #35 |
| $\alpha = 1$: no memory dependency | Test #36 |
| $\alpha = 0$: no visit-count dependency | Test #37 |

---

## 6. Acceptance Criteria

- [ ] All 9 worked example groups verified numerically (A1, B1, C1, D1, E1, E2, F1, F2, F3)
- [ ] 2 full pipeline tests pass (world → decide → verify probabilities)
- [ ] Reduction to System A verified for $\mu_C = 0$ (single step + multi-step)
- [ ] Reduction to System A verified for $w_C^{base} = 0$
- [ ] $\alpha$ boundary conditions verified (memory independence at $\alpha=1$, world model independence at $\alpha=0$)
- [ ] World model still updated when curiosity is disabled
- [ ] All 38 tests pass
