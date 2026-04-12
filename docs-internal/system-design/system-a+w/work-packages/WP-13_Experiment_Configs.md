# WP-13: Experiment Configurations

## Metadata
- Work Package: WP-13
- Title: Experiment Configuration YAML Files
- System: System A+W
- Source Files: `experiments/configs/system-aw-baseline.yaml`, `system-aw-curiosity-sweep.yaml`, `system-aw-exploration-demo.yaml`
- Dependencies: WP-10 (system registered and runnable)

---

## 1. Objective

Provide three ready-to-run YAML experiment configurations that exercise System A+W across its key behavioral regimes. These configs serve as both integration tests and reference examples for users.

---

## 2. Configurations

### 2.1 `system-aw-baseline.yaml` — Baseline Dual-Drive Experiment

**Purpose:** Verify the basic forage-explore cycle with default parameters.

```yaml
# System A+W baseline experiment
system_type: "system_aw"
experiment_type: "single_run"

general:
  seed: 42

execution:
  max_steps: 200

world:
  world_type: "grid_2d"
  grid_width: 10
  grid_height: 10
  obstacle_density: 0.15
  resource_regen_rate: 0.2
  regeneration_mode: "sparse_fixed_ratio"
  regen_eligible_ratio: 0.17

system:
  agent:
    initial_energy: 50.0
    max_energy: 100.0
    buffer_capacity: 10
  policy:
    selection_mode: "sample"
    temperature: 0.5
    stay_suppression: 0.1
    consume_weight: 2.5
  transition:
    move_cost: 1.0
    consume_cost: 1.0
    stay_cost: 0.5
    max_consume: 1.0
    energy_gain_factor: 10.0
  curiosity:
    base_curiosity: 1.0
    spatial_sensory_balance: 0.5
    explore_suppression: 0.3
  arbitration:
    hunger_weight_base: 0.3
    curiosity_weight_base: 1.0
    gating_sharpness: 2.0

logging:
  enabled: true
  console_enabled: true
  jsonl_enabled: false
  verbosity: "compact"

num_episodes_per_run: 5
```

**Expected behavior:**
- At high energy: agent explores (movement > consume in logs)
- As energy drops: agent shifts to resource-seeking
- After consuming: agent resumes exploration
- Visit counts grow across the grid over time

---

### 2.2 `system-aw-curiosity-sweep.yaml` — OFAT Sweep Over Base Curiosity

**Purpose:** Show the transition from pure System A behavior ($\mu_C = 0$) to full curiosity ($\mu_C = 1.0$).

```yaml
# OFAT sweep over curiosity strength
system_type: "system_aw"
experiment_type: "ofat"

general:
  seed: 42

execution:
  max_steps: 200

world:
  world_type: "grid_2d"
  grid_width: 10
  grid_height: 10
  obstacle_density: 0.1
  resource_regen_rate: 0.2
  regeneration_mode: "sparse_fixed_ratio"
  regen_eligible_ratio: 0.17

system:
  agent:
    initial_energy: 50.0
    max_energy: 100.0
    buffer_capacity: 10
  policy:
    selection_mode: "sample"
    temperature: 0.5
    stay_suppression: 0.1
    consume_weight: 2.5
  transition:
    move_cost: 1.0
    consume_cost: 1.0
    stay_cost: 0.5
    max_consume: 1.0
    energy_gain_factor: 10.0
  curiosity:
    base_curiosity: 1.0
    spatial_sensory_balance: 0.5
    explore_suppression: 0.3
  arbitration:
    hunger_weight_base: 0.3
    curiosity_weight_base: 1.0
    gating_sharpness: 2.0

logging:
  enabled: true
  console_enabled: true
  jsonl_enabled: true
  jsonl_path: "experiments/output/system-aw-curiosity-sweep.jsonl"
  verbosity: "compact"

num_episodes_per_run: 3

parameter_path: "system.curiosity.base_curiosity"
parameter_values: [0.0, 0.25, 0.5, 0.75, 1.0]
```

**Expected behavior:**
- $\mu_C = 0.0$: behavior identical to System A (pure hunger-driven)
- $\mu_C = 0.25$: slight exploration bias when well-fed
- $\mu_C = 0.5$: moderate exploration-foraging balance
- $\mu_C = 0.75$: strong exploration preference
- $\mu_C = 1.0$: maximum exploration when sated, sharp transition to foraging when hungry

**JSONL output** enables quantitative comparison: mean episode length, consume frequency, unique cells visited.

---

### 2.3 `system-aw-exploration-demo.yaml` — Exploration-Focused Demo

**Purpose:** Demonstrate systematic territory coverage with a well-fed, highly curious agent.

```yaml
# Exploration demo: large grid, high energy, sharp gating
system_type: "system_aw"
experiment_type: "single_run"

general:
  seed: 7

execution:
  max_steps: 500

world:
  world_type: "grid_2d"
  grid_width: 20
  grid_height: 20
  obstacle_density: 0.05
  resource_regen_rate: 0.3
  regeneration_mode: "sparse_fixed_ratio"
  regen_eligible_ratio: 0.10

system:
  agent:
    initial_energy: 100.0
    max_energy: 100.0
    buffer_capacity: 20
  policy:
    selection_mode: "sample"
    temperature: 0.5
    stay_suppression: 0.1
    consume_weight: 2.5
  transition:
    move_cost: 0.5
    consume_cost: 0.5
    stay_cost: 0.3
    max_consume: 1.0
    energy_gain_factor: 15.0
  curiosity:
    base_curiosity: 1.0
    spatial_sensory_balance: 0.7
    explore_suppression: 0.5
  arbitration:
    hunger_weight_base: 0.2
    curiosity_weight_base: 1.5
    gating_sharpness: 3.0

logging:
  enabled: true
  console_enabled: true
  jsonl_enabled: true
  jsonl_path: "experiments/output/system-aw-exploration-demo.jsonl"
  verbosity: "verbose"

num_episodes_per_run: 3
```

**Key parameter choices:**
- $e_0 = E_{\max} = 100$: starts fully sated → maximum curiosity
- 20x20 grid with low obstacles (0.05): large open area to explore
- $\gamma = 3.0$: sharp gating → curiosity persists even at moderate hunger
- $w_C^{base} = 1.5$: stronger curiosity influence
- $\alpha = 0.7$: spatial novelty weighted more (coverage matters more than sensory change)
- $\lambda_{explore} = 0.5$: strong CONSUME/STAY suppression
- Low move cost (0.5): exploration is cheap
- High energy gain ($\kappa = 15$): fast recovery after consuming
- Verbose logging: shows full novelty computation per step

**Expected behavior:**
- Agent explores systematically for many steps before needing to eat
- When energy drops, sharp transition to foraging
- Quick recovery → back to exploration
- High spatial coverage (many unique relative positions visited)

---

## 3. Test Plan

Testing for configs is part of WP-14 (documentation / integration), but the basic validation:

| # | Test | Description |
|---|---|---|
| 1 | `test_baseline_config_parses` | YAML loads and `SystemAWConfig(**system)` succeeds |
| 2 | `test_sweep_config_parses` | YAML loads, parameter path resolves, all sweep values are valid |
| 3 | `test_exploration_config_parses` | YAML loads and config with non-default parameters succeeds |
| 4 | `test_baseline_runs_to_completion` | `axis run system-aw-baseline.yaml` exits cleanly (integration test) |
| 5 | `test_sweep_produces_multiple_runs` | Sweep config produces 5 runs (one per $\mu_C$ value) |

---

## 4. Acceptance Criteria

- [ ] All 3 configs parse without errors
- [ ] Baseline runs to completion and shows forage-explore cycle in logs
- [ ] Sweep produces 5 differentiated runs across $\mu_C$ values
- [ ] Exploration demo shows high spatial coverage and verbose novelty output
- [ ] JSONL files are created for sweep and exploration configs
- [ ] All configs follow the existing YAML structure pattern (consistent with `system-a-*.yaml`)
