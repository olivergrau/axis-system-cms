# System A+W Manual (v0.2.0)

> **Related manuals:**
> [CLI User Manual](cli-manual.md) |
> [Configuration Reference](config-manual.md) |
> [System Developer Manual](system-dev-manual.md) |
> [World Developer Manual](world-dev-manual.md)

## Overview

System A+W extends System A with two new capabilities:

- **Curiosity drive** -- a novelty-seeking drive that encourages
  exploration of unvisited cells.
- **Spatial world model** -- a visit-count map built via dead reckoning,
  giving the agent a spatial memory of where it has been.

The two drives (hunger and curiosity) are combined through **dynamic
drive arbitration** that implements a Maslow-like hierarchy: hunger
gates curiosity. When the agent is well-fed, curiosity dominates and
the agent explores. As energy drops, hunger takes over and the agent
shifts to foraging.

System A+W uses `system_type: "system_aw"` in experiment configs.

---

## 1. Architecture

```
                    WorldView (read-only, from framework)
                              |
                        ┌─────┴─────┐
                        │  Sensor   │
                        └─────┬─────┘
                              │ Observation
                    ┌─────────┴─────────┐
                    │                   │
              ┌─────┴─────┐     ┌──────┴──────┐
              │  Hunger   │     │  Curiosity  │
              │  Drive    │     │  Drive      │◄── World Model
              └─────┬─────┘     └──────┬──────┘
                    │                  │
                    └────────┬─────────┘
                       ┌─────┴─────┐
                       │ Arbitrate │  (dynamic weights)
                       └─────┬─────┘
                             │ Action scores
                       ┌─────┴─────┐
                       │  Policy   │  (softmax / argmax)
                       └─────┬─────┘
                             │ Selected action
                       ┌─────┴─────┐
                       │Transition │──► World Model update
                       └───────────┘
```

**Execution cycle per step:**

1. **Perception** -- Sensor reads the 5-cell neighborhood from the
   world view (current + 4 cardinal neighbors).
2. **Hunger drive** -- Computes drive activation from energy level and
   per-action contributions from resource observations.
3. **Curiosity drive** -- Computes drive activation from novelty
   saturation and per-action contributions from spatial/sensory novelty.
4. **Drive arbitration** -- Computes dynamic weights for each drive
   based on hunger activation and gating sharpness.
5. **Action modulation** -- Combines weighted drive contributions into
   final action scores.
6. **Action selection** -- Softmax (or argmax) over admissible actions.
7. **Transition** -- Updates energy, memory, and world model.

---

## 2. Configuration reference

When `system_type` is `"system_aw"`, the `system` dict is parsed into
a `SystemAWConfig` with five sub-sections. Sections 2.1--2.3 are
shared with System A. Sections 2.4--2.5 are new to System A+W.

### 2.1 `system.agent` -- Agent initialization

| Field             | Type  | Required | Constraints          | Description |
|-------------------|-------|----------|----------------------|-------------|
| `initial_energy`  | float | yes      | > 0, <= `max_energy` | Starting energy at the beginning of each episode. |
| `max_energy`      | float | yes      | > 0                  | Maximum energy the agent can hold. Energy gains are capped here. |
| `buffer_capacity` | int   | yes      | > 0                  | Number of recent observations the agent remembers. Affects sensory novelty and novelty saturation. |

```yaml
system:
  agent:
    initial_energy: 100.0
    max_energy: 100.0
    buffer_capacity: 20
```

### 2.2 `system.policy` -- Action selection

| Field              | Type   | Required | Constraints        | Description |
|--------------------|--------|----------|--------------------|-------------|
| `selection_mode`   | string | yes      | `"sample"` or `"argmax"` | Action selection strategy. |
| `temperature`      | float  | yes      | > 0                | Softmax temperature. Lower = peakier distribution. |
| `stay_suppression` | float  | yes      | >= 0               | Weight penalty applied to the "stay" action in the hunger drive. |
| `consume_weight`   | float  | yes      | > 0                | Weight bonus for "consume" when on a resource cell. |

```yaml
system:
  policy:
    selection_mode: "sample"
    temperature: 1.5
    stay_suppression: 0.1
    consume_weight: 2.5
```

### 2.3 `system.transition` -- Energy dynamics

| Field               | Type  | Required | Constraints | Description |
|---------------------|-------|----------|-------------|-------------|
| `move_cost`         | float | yes      | > 0         | Energy deducted per movement action (up/down/left/right). |
| `consume_cost`      | float | yes      | > 0         | Energy deducted for the "consume" action. |
| `stay_cost`         | float | yes      | >= 0        | Energy deducted for the "stay" action. |
| `max_consume`       | float | yes      | > 0         | Maximum resource fraction consumed per action (0.0--1.0 typical). |
| `energy_gain_factor`| float | yes      | >= 0        | Multiplier: energy gained = `resource_consumed * energy_gain_factor`. |

```yaml
system:
  transition:
    move_cost: 0.5
    consume_cost: 0.5
    stay_cost: 0.3
    max_consume: 1.0
    energy_gain_factor: 15.0
```

### 2.4 `system.curiosity` -- Curiosity drive

| Field                    | Type  | Default | Constraints | Description |
|--------------------------|-------|---------|-------------|-------------|
| `base_curiosity`         | float | `1.0`   | 0.0--1.0    | Base curiosity level (mu_C). Scales the curiosity drive activation. |
| `spatial_sensory_balance` | float | `0.5`  | 0.0--1.0    | Alpha blending weight. 1.0 = pure spatial (visit-count), 0.0 = pure sensory (observation-difference). |
| `explore_suppression`    | float | `0.3`   | >= 0        | Penalty applied to CONSUME and STAY actions in the curiosity drive. Encourages movement. |
| `novelty_sharpness`      | float | `1.0`   | > 0         | Exponent k in spatial novelty formula `1/(1+w)^k`. Higher values create steeper decay, giving stronger preference for unvisited cells. |

```yaml
system:
  curiosity:
    base_curiosity: 1.0
    spatial_sensory_balance: 0.7
    explore_suppression: 0.5
    novelty_sharpness: 2.0
```

### 2.5 `system.arbitration` -- Drive arbitration

| Field                 | Type  | Default | Constraints | Description |
|-----------------------|-------|---------|-------------|-------------|
| `hunger_weight_base`  | float | `0.3`   | > 0, <= 1.0 | Minimum hunger weight. Even at zero hunger, this weight applies. |
| `curiosity_weight_base` | float | `1.0` | > 0         | Maximum curiosity weight (when hunger is zero). |
| `gating_sharpness`    | float | `2.0`   | > 0         | Exponent gamma controlling how sharply hunger gates curiosity. Higher = sharper transition. |

```yaml
system:
  arbitration:
    hunger_weight_base: 0.2
    curiosity_weight_base: 1.5
    gating_sharpness: 3.0
```

---

## 3. Drive pipeline

This section documents the mathematical formulas implemented in the
code. All formulas are computed every step.

### 3.1 Hunger drive

**Activation:**

```
d_H(t) = clamp(1 - E_t / E_max, 0, 1)
```

When energy is full, `d_H = 0` (no hunger). When energy is zero,
`d_H = 1` (maximum hunger).

**Action contributions:**

| Action    | Formula |
|-----------|---------|
| Direction | `phi_H(dir) = d_H * r_dir` (resource at neighbor) |
| Consume   | `phi_H(consume) = d_H * w_consume * r_current` |
| Stay      | `phi_H(stay) = -lambda_stay * d_H` |

Source: `src/axis/systems/system_a/drive.py`

### 3.2 Curiosity drive

**Spatial novelty** (per-direction, from world model):

```
nu^spatial_dir = 1 / (1 + w(neighbor))^k
```

where `w(neighbor)` is the visit count at the neighboring cell and
`k` is `novelty_sharpness`. Unvisited cells have `w=0`, giving
novelty = 1.0. With k=1: `w=1 -> 0.50`, `w=4 -> 0.20`. With k=2:
`w=1 -> 0.25`, `w=4 -> 0.04`.

Source: `src/axis/systems/system_aw/world_model.py:spatial_novelty()`

**Sensory novelty** (per-direction, from observation vs memory):

```
nu^sensory_dir = |r_dir(t) - mean(r_dir over memory)|
```

When memory is empty, mean = 0. Detects resource-level surprises.

Source: `src/axis/systems/system_aw/drive_curiosity.py:compute_sensory_novelty()`

**Composite novelty** (alpha-weighted blend):

```
nu_dir = alpha * nu^spatial_dir + (1 - alpha) * nu^sensory_dir
```

Controlled by `spatial_sensory_balance` (alpha).

Source: `src/axis/systems/system_aw/drive_curiosity.py:compute_composite_novelty()`

**Novelty saturation** (from memory):

```
sigma_j = mean over directions of |r_dir^(j) - mean(r_dir)|
nu_bar_t = mean over entries of sigma_j
```

Returns 0.0 when memory is empty (maximum curiosity).

**Drive activation:**

```
d_C = mu_C * (1 - nu_bar_t)
```

Bounded to [0, mu_C]. High novelty saturation reduces curiosity.

Source: `src/axis/systems/system_aw/drive_curiosity.py:compute_curiosity_activation()`

**Action contributions:**

| Action    | Formula |
|-----------|---------|
| Direction | `phi_C(dir) = nu_dir` (composite novelty for that direction) |
| Consume   | `phi_C(consume) = -lambda_explore` |
| Stay      | `phi_C(stay) = -lambda_explore` |

Source: `src/axis/systems/system_aw/drive_curiosity.py:SystemAWCuriosityDrive.compute()`

### 3.3 Drive arbitration

Dynamic weights implement a Maslow-like hierarchy:

```
w_H(t) = w_H_base + (1 - w_H_base) * d_H(t)^gamma
w_C(t) = w_C_base * (1 - d_H(t))^gamma
```

When `d_H = 0` (full energy): `w_H = w_H_base`, `w_C = w_C_base`.
When `d_H = 1` (starving): `w_H = 1.0`, `w_C = 0.0`.
Higher gamma makes the transition sharper.

Source: `src/axis/systems/system_aw/drive_arbitration.py:compute_drive_weights()`

### 3.4 Action scores

Final per-action score combining both drives:

```
psi(a) = w_H * d_H * phi_H(a) + w_C * d_C * phi_C(a)
```

These scores are passed to the softmax policy for action selection.

Source: `src/axis/systems/system_aw/drive_arbitration.py:compute_action_scores()`

---

## 4. World model

### 4.1 Dead reckoning

The agent maintains a relative position estimate via dead reckoning:

```
p_hat_{t+1} = p_hat_t + mu_t * delta(a_t)
```

where `mu_t = 1` if the agent moved, `mu_t = 0` otherwise, and
`delta(a_t)` is the direction delta for the chosen action.

### 4.2 Visit-count map

A dictionary mapping relative positions to visit counts. The count at
the current position is incremented after every action (including
failed moves, consume, and stay).

### 4.3 Coordinate system

The world model uses an agent-relative coordinate system:

- **Origin** `(0, 0)` = agent's starting position for the episode.
- **UP** = `(0, +1)` (y increases upward).
- **RIGHT** = `(+1, 0)`.

This is independent of the SDK's world grid coordinate system, where
UP = `(0, -1)`. The visualization adapter handles the y-axis flip when
converting world model coordinates to grid coordinates for overlays.

### 4.4 Initial state

At episode start, the world model is initialized with:
- `relative_position = (0, 0)`
- `visit_counts = {(0, 0): 1}`

Source: `src/axis/systems/system_aw/world_model.py`

---

## 5. Tuning guide

### Energy and survival

- **`initial_energy` / `max_energy`**: Set equal for "start full"
  scenarios where curiosity dominates early. A lower ratio
  (e.g., 50/100) forces the agent to forage before exploring.
- **`energy_gain_factor`**: Higher values let the agent recover
  faster from consuming, extending exploration windows.
- **`move_cost`**: Keep low relative to energy gain to allow
  sustained exploration. Too high forces constant foraging.

### Curiosity strength

- **`novelty_sharpness`** (k): The most impactful curiosity parameter.
  - k=1 (default): gentle decay -- visited and unvisited directions
    have moderate contrast.
  - k=2: strong decay -- visited cells become much less attractive.
    Recommended for larger grids where exploration coverage matters.
  - k=3+: very aggressive -- almost binary visited/unvisited distinction.

  The effect on spatial novelty scores:

  | Visit count | k=1    | k=2    | k=3    |
  |-------------|--------|--------|--------|
  | 0 (unvisited) | 1.000 | 1.000  | 1.000  |
  | 1           | 0.500  | 0.250  | 0.125  |
  | 2           | 0.333  | 0.111  | 0.037  |
  | 4           | 0.200  | 0.040  | 0.008  |
  | 9           | 0.100  | 0.010  | 0.001  |

- **`spatial_sensory_balance`** (alpha): Controls whether the agent
  navigates by visit counts or by resource surprises.
  - alpha=1.0: pure spatial -- ignores resource differences, explores
    by visit count only.
  - alpha=0.0: pure sensory -- ignores visit counts, chases resource
    variability.
  - alpha=0.5--0.7: recommended -- balances both signals.

- **`explore_suppression`**: Penalty for CONSUME and STAY in the
  curiosity drive. Higher values discourage idling when curious.

- **`base_curiosity`** (mu_C): Scales the overall curiosity activation.
  Setting to 0.0 disables curiosity entirely (equivalent to System A).

### Drive arbitration

- **`gating_sharpness`** (gamma): Controls the Maslow transition.
  - gamma=1: linear transition between drives.
  - gamma=2--3: moderate gating -- curiosity fades quickly as hunger grows.
  - gamma=5+: sharp gating -- curiosity drops to near-zero with even
    slight hunger.

- **`hunger_weight_base`**: Minimum influence of hunger. Even when
  `d_H = 0`, hunger contributes this weight. A value of 0.2 ensures
  the agent still considers resources even when fully sated.

- **`curiosity_weight_base`**: Maximum influence of curiosity. Values
  above 1.0 make curiosity stronger than hunger at full energy.

### Policy

- **`temperature`**: Interacts with the drive scores. Lower temperature
  makes the softmax distribution peakier (more deterministic), which
  amplifies the effect of curiosity-driven score differences. Higher
  temperature adds exploration noise.
  - Recommended: 1.0--2.0 for `selection_mode: "sample"`.

---

## 6. Assumptions and limitations

1. **1-cell lookahead**: The curiosity drive only computes novelty for
   immediately adjacent cells. The agent has no gradient information
   about cells beyond its neighbors. This means an agent surrounded by
   equally visited cells has no directional preference toward unexplored
   territory, even if unvisited cells exist two steps away.

2. **Dead reckoning drift**: The world model uses dead reckoning and
   does not correct for failed moves beyond tracking `moved = True/False`.
   In grids with dense obstacles, the world model remains accurate because
   failed moves are correctly handled. However, the model has no concept
   of absolute position -- it only knows relative displacement from
   the starting position.

3. **No obstacle awareness**: The world model does not record obstacle
   locations. It only tracks visit counts. The agent discovers obstacles
   reactively through the observation's traversability signal.

4. **No global path planning**: The agent cannot plan multi-step paths.
   It acts greedily based on local novelty and hunger signals.

5. **Memory capacity trade-off**: Larger `buffer_capacity` gives more
   stable sensory novelty and saturation estimates but makes the agent
   slower to adapt to changing environments.

6. **Consume action side effect**: The consume action handler uses a
   `max_consume` parameter to limit resource consumption per step,
   preventing the agent from draining cells instantly.

---

## 7. Example configuration

Complete exploration demo (ships as
`experiments/configs/system-aw-exploration-demo.yaml`):

```yaml
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

agent_start_position:
  x: 10
  y: 10

system:
  agent:
    initial_energy: 100.0
    max_energy: 100.0
    buffer_capacity: 20
  policy:
    selection_mode: "sample"
    temperature: 1.5
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
    novelty_sharpness: 2.0
  arbitration:
    hunger_weight_base: 0.2
    curiosity_weight_base: 1.5
    gating_sharpness: 3.0

logging:
  enabled: true
  console_enabled: true
  jsonl_enabled: false
  verbosity: "compact"

num_episodes_per_run: 3
```

Run with:

```
axis experiments run experiments/configs/system-aw-exploration-demo.yaml
```

Use the visualizer to inspect the agent's behavior step-by-step:

```
axis experiments visualize <experiment_id>
```

The visualization includes debug panels for all drive outputs,
arbitration weights, decision pipeline, and world model state. Overlay
options include visit-count heatmap, action preference arrows, drive
contribution bars, consumption opportunities, and novelty field arrows.
