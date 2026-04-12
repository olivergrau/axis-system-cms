# System B Worked Examples

## Metadata
- Project: AXIS -- Complex Mechanistic Systems Experiment
- Author: Oliver Grau
- Type: Worked Examples
- Status: Draft v1.0
- Companion: System B Model (01_System B Model.md)

---

## 1. Purpose of this Document

This document provides step-by-step numerical worked examples for **System B**, the scout agent with scan action. Each example traces the full decision pipeline: weight computation, softmax policy, action selection, and state transition.

These examples serve as:

- verification targets for the implementation,
- pedagogical illustrations of the formal model,
- and reference points for edge-case behavior.

---

## 2. Common Definitions and Notation

### 2.1 Default Parameters

Unless stated otherwise, all examples use the default configuration:

| Parameter | Symbol | Value |
|-----------|--------|-------|
| Initial energy | $E_{\text{init}}$ | 100.0 |
| Maximum energy | $E_{\max}$ | 100.0 |
| Temperature | $T$ | 1.0 |
| Scan bonus | $b_{\text{scan}}$ | 2.0 |
| Move cost | $c_{\text{move}}$ | 1.0 |
| Scan cost | $c_{\text{scan}}$ | 0.5 |
| Stay cost | $c_{\text{stay}}$ | 0.5 |
| Scan radius | $r$ | 1 |
| Selection mode | -- | sample |

### 2.2 Action Indexing

| Index | Action |
|-------|--------|
| 0 | UP |
| 1 | DOWN |
| 2 | LEFT |
| 3 | RIGHT |
| 4 | SCAN |
| 5 | STAY |

### 2.3 Weight Computation Summary

For each action $a$:

1. Start with base weight: $w_a = 1.0$
2. **SCAN**: if $\sigma_t = 0$, set $w_{\text{SCAN}} = b_{\text{scan}}$
3. **Movement**: $w_{\text{DIR}} = 1.0 + 2 \cdot r_{\text{target}}$ if accessible, else $w_{\text{DIR}} = 0$
4. **Softmax**: $P(a) = \exp(w_a / T) / \sum \exp(w_{a'} / T)$ over admissible actions

### 2.4 Grid Conventions

- Coordinates: $(x, y)$ with $x$ increasing rightward, $y$ increasing downward
- Movement deltas: UP = $(0, -1)$, DOWN = $(0, +1)$, LEFT = $(-1, 0)$, RIGHT = $(+1, 0)$
- Signal values: $r(x, y) \in [0, 1]$

---

## 3. Example Group A: Basic Decision Making

### A1. Uniform Signal Field

#### 1. Objective

Show that on a uniform signal field, all movement directions are equally weighted.

#### 2. Scenario

- Grid: $5 \times 5$, all cells have $r = 0.3$, no obstacles
- Agent position: $(2, 2)$ (center)
- State: $e = 100$, $s = (2.7, 9)$ (previous scan found resources)
- All four neighbors are traversable with $r = 0.3$

#### 3. Weight Computation

| Action | Base | Adjustment | Final Weight |
|--------|------|------------|-------------|
| UP | 1.0 | $+2 \times 0.3 = 0.6$ | 1.6 |
| DOWN | 1.0 | $+2 \times 0.3 = 0.6$ | 1.6 |
| LEFT | 1.0 | $+2 \times 0.3 = 0.6$ | 1.6 |
| RIGHT | 1.0 | $+2 \times 0.3 = 0.6$ | 1.6 |
| SCAN | 1.0 | none ($\sigma > 0$) | 1.0 |
| STAY | 1.0 | none | 1.0 |

#### 4. Policy

$w_{\max} = 1.6$

| Action | $\exp(\beta \cdot (w - w_{\max}))$ |
|--------|-----|
| UP | $\exp(0) = 1.000$ |
| DOWN | $\exp(0) = 1.000$ |
| LEFT | $\exp(0) = 1.000$ |
| RIGHT | $\exp(0) = 1.000$ |
| SCAN | $\exp(-0.6) = 0.549$ |
| STAY | $\exp(-0.6) = 0.549$ |

Sum $= 4 \times 1.000 + 2 \times 0.549 = 5.098$

| Action | Probability |
|--------|-------------|
| UP | $1.000 / 5.098 = 0.196$ |
| DOWN | $1.000 / 5.098 = 0.196$ |
| LEFT | $1.000 / 5.098 = 0.196$ |
| RIGHT | $1.000 / 5.098 = 0.196$ |
| SCAN | $0.549 / 5.098 = 0.108$ |
| STAY | $0.549 / 5.098 = 0.108$ |

#### 5. Interpretation

All four movement directions have equal probability (~19.6% each). The agent moves randomly with no directional preference when the signal field is uniform. SCAN and STAY are less likely because their weights are lower.

---

### A2. Strong Directional Signal

#### 1. Objective

Show that a high-signal neighbor creates strong directional bias.

#### 2. Scenario

- Grid: $5 \times 5$
- Agent position: $(2, 2)$
- Neighbor signals: UP $(2,1)$: $r = 0.9$, DOWN $(2,3)$: $r = 0.1$, LEFT $(1,2)$: $r = 0.0$, RIGHT $(3,2)$: $r = 0.2$
- State: $e = 80$, $s = (1.5, 9)$ ($\sigma > 0$, no scan bonus)

#### 3. Weight Computation

| Action | Base | Adjustment | Final Weight |
|--------|------|------------|-------------|
| UP | 1.0 | $+2 \times 0.9 = 1.8$ | 2.8 |
| DOWN | 1.0 | $+2 \times 0.1 = 0.2$ | 1.2 |
| LEFT | 1.0 | $+2 \times 0.0 = 0.0$ | 1.0 |
| RIGHT | 1.0 | $+2 \times 0.2 = 0.4$ | 1.4 |
| SCAN | 1.0 | none | 1.0 |
| STAY | 1.0 | none | 1.0 |

#### 4. Policy

$w_{\max} = 2.8$

| Action | $\exp(\beta \cdot (w - w_{\max}))$ | Probability |
|--------|-----|-------------|
| UP | $\exp(0) = 1.000$ | 0.393 |
| DOWN | $\exp(-1.6) = 0.202$ | 0.079 |
| LEFT | $\exp(-1.8) = 0.165$ | 0.065 |
| RIGHT | $\exp(-1.4) = 0.247$ | 0.097 |
| SCAN | $\exp(-1.8) = 0.165$ | 0.065 |
| STAY | $\exp(-1.8) = 0.165$ | 0.065 |

Sum $= 1.000 + 0.202 + 0.165 + 0.247 + 0.165 + 0.165 = 1.944$

Probabilities computed as $\exp / \text{sum}$:
- UP: $1.000 / 1.944 = 0.514$
- DOWN: $0.202 / 1.944 = 0.104$
- LEFT: $0.165 / 1.944 = 0.085$
- RIGHT: $0.247 / 1.944 = 0.127$
- SCAN: $0.165 / 1.944 = 0.085$
- STAY: $0.165 / 1.944 = 0.085$

#### 5. Interpretation

The agent moves UP with ~51% probability, strongly biased toward the high-signal cell ($r = 0.9$). RIGHT ($r = 0.2$) gets moderate probability (~13%), while LEFT ($r = 0.0$), SCAN, and STAY share the lowest probabilities (~8.5% each).

---

### A3. No Prior Scan Data (Scan Bonus Active)

#### 1. Objective

Show that the scan bonus activates when the agent has no scan data.

#### 2. Scenario

- Grid: $5 \times 5$, all cells $r = 0.2$
- Agent position: $(2, 2)$
- State: $e = 100$, $s = (0, 0)$ (no scan performed yet, $\sigma = 0$)

#### 3. Weight Computation

| Action | Base | Adjustment | Final Weight |
|--------|------|------------|-------------|
| UP | 1.0 | $+2 \times 0.2 = 0.4$ | 1.4 |
| DOWN | 1.0 | $+2 \times 0.2 = 0.4$ | 1.4 |
| LEFT | 1.0 | $+2 \times 0.2 = 0.4$ | 1.4 |
| RIGHT | 1.0 | $+2 \times 0.2 = 0.4$ | 1.4 |
| SCAN | 1.0 | $b_{\text{scan}} = 2.0$ | **2.0** |
| STAY | 1.0 | none | 1.0 |

Note: when the scan bonus activates, the scan weight is set to $b_{\text{scan}}$ directly (not added to base).

#### 4. Policy

$w_{\max} = 2.0$

| Action | $\exp(\beta \cdot (w - w_{\max}))$ | Probability |
|--------|-----|-------------|
| UP | $\exp(-0.6) = 0.549$ | 0.160 |
| DOWN | $\exp(-0.6) = 0.549$ | 0.160 |
| LEFT | $\exp(-0.6) = 0.549$ | 0.160 |
| RIGHT | $\exp(-0.6) = 0.549$ | 0.160 |
| SCAN | $\exp(0) = 1.000$ | **0.291** |
| STAY | $\exp(-1.0) = 0.368$ | 0.107 |

Sum $= 4 \times 0.549 + 1.000 + 0.368 = 3.564$

#### 5. Interpretation

SCAN is the most probable action (~29%), higher than any individual movement direction (~16%). The scan bonus successfully biases the agent toward gathering information before committing to a direction. After scanning reveals the signal field, the bonus deactivates and movement becomes more attractive.

---

## 4. Example Group B: Scan Mechanics

### B1. Center Scan (Full Coverage)

#### 1. Objective

A scan at the center of a grid reads the full $(2r+1)^2 = 9$ cells.

#### 2. Scenario

- Grid: $5 \times 5$, agent at $(2, 2)$, $r = 1$
- Signal values in $3 \times 3$ neighborhood:

|   | x=1 | x=2 | x=3 |
|---|-----|-----|-----|
| y=1 | 0.1 | 0.3 | 0.2 |
| y=2 | 0.4 | 0.5 | 0.1 |
| y=3 | 0.0 | 0.2 | 0.3 |

#### 3. Scan Result

$$\sigma = 0.1 + 0.3 + 0.2 + 0.4 + 0.5 + 0.1 + 0.0 + 0.2 + 0.3 = 2.1$$

$$n = 9$$

#### 4. Post-scan State

$s_{t+1} = (2.1, 9)$, $e_{t+1} = e_t - c_{\text{scan}} = 100.0 - 0.5 = 99.5$

---

### B2. Corner Scan (Boundary Clipping)

#### 1. Objective

A scan at a corner reads only the cells that fall within the grid bounds.

#### 2. Scenario

- Grid: $5 \times 5$, agent at $(0, 0)$, $r = 1$
- In-bounds cells of $3 \times 3$ neighborhood centered at $(0, 0)$:

|   | x=0 | x=1 |
|---|-----|-----|
| y=0 | 0.5 | 0.3 |
| y=1 | 0.2 | 0.1 |

Cells at $x = -1$ or $y = -1$ are out of bounds and skipped.

#### 3. Scan Result

$$\sigma = 0.5 + 0.3 + 0.2 + 0.1 = 1.1$$

$$n = 4$$

Only 4 of the 9 potential cells are within bounds.

---

### B3. Scan Near Obstacle

#### 1. Objective

Obstacle cells are included in the scan count but contribute $r = 0$.

#### 2. Scenario

- Grid: $5 \times 5$, agent at $(2, 2)$, $r = 1$
- Cell $(3, 2)$ is an OBSTACLE ($r = 0$), all others $r = 0.4$

#### 3. Scan Result

$$\sigma = 8 \times 0.4 + 1 \times 0.0 = 3.2$$

$$n = 9$$

The obstacle cell is within bounds and is counted, but contributes zero resource value.

---

## 5. Example Group C: Energy and Lifetime

### C1. Multi-Step Energy Depletion

#### 1. Objective

Trace energy over a sequence of mixed actions.

#### 2. Scenario

Starting energy $E_0 = 10.0$, $E_{\max} = 10.0$.

| Step | Action | Cost | Energy Before | Energy After |
|------|--------|------|--------------|-------------|
| 0 | SCAN | 0.5 | 10.0 | 9.5 |
| 1 | RIGHT | 1.0 | 9.5 | 8.5 |
| 2 | RIGHT | 1.0 | 8.5 | 7.5 |
| 3 | SCAN | 0.5 | 7.5 | 7.0 |
| 4 | UP | 1.0 | 7.0 | 6.0 |
| 5 | STAY | 0.5 | 6.0 | 5.5 |
| 6 | LEFT | 1.0 | 5.5 | 4.5 |
| 7 | DOWN | 1.0 | 4.5 | 3.5 |
| 8 | SCAN | 0.5 | 3.5 | 3.0 |
| 9 | RIGHT | 1.0 | 3.0 | 2.0 |
| 10 | UP | 1.0 | 2.0 | 1.0 |
| 11 | RIGHT | 1.0 | 1.0 | **0.0** |

#### 3. Result

Agent terminates at step 11. Total actions: 8 movements ($\times 1.0 = 8.0$), 3 scans ($\times 0.5 = 1.5$), 1 stay ($\times 0.5 = 0.5$). Total cost: $8.0 + 1.5 + 0.5 = 10.0 = E_0$.

---

### C2. Terminal Step

#### 1. Objective

Show the exact termination mechanics when energy drops to zero.

#### 2. Scenario

- $e_t = 0.8$, action: MOVE (cost $c_{\text{move}} = 1.0$)
- $e_{t+1} = \max(0, 0.8 - 1.0) = 0.0$
- Since $e_{t+1} \leq 0$: `terminated = true`, `termination_reason = "energy_depleted"`

The agent's final action still executes (movement occurs), but the resulting state has zero energy and the episode ends.

---

## 6. Example Group D: Signal Landscape Dynamics

### D1. Hotspot Drift Changes Optimal Direction

#### 1. Objective

Show how hotspot drift changes the signal field and the agent's preferred direction between timesteps.

#### 2. Scenario

- Grid: $5 \times 5$, single hotspot at initial center $(3.0, 2.0)$, $\rho = 2.0$, $I = 1.0$, $\delta = 0$
- Agent at $(2, 2)$

#### 3. Step 1: Before Drift

Signal at neighbors (using Gaussian RBF, non-toroidal for simplicity with small grid):

- UP $(2,1)$: $d^2 = (2-3)^2 + (1-2)^2 = 2$, $r = \exp(-2/8) = \exp(-0.25) = 0.779$
- DOWN $(2,3)$: $d^2 = (2-3)^2 + (3-2)^2 = 2$, $r = 0.779$
- LEFT $(1,2)$: $d^2 = (1-3)^2 + (2-2)^2 = 4$, $r = \exp(-4/8) = \exp(-0.5) = 0.607$
- RIGHT $(3,2)$: $d^2 = (3-3)^2 + (2-2)^2 = 0$, $r = \exp(0) = 1.000$

Weights: UP = $1.0 + 2 \times 0.779 = 2.558$, DOWN = $2.558$, LEFT = $2.214$, RIGHT = $\mathbf{3.000}$

**Preferred direction: RIGHT** (toward hotspot center).

#### 4. Step 2: After Drift

Hotspot drifts to $(1.0, 2.0)$ (moved left by 2 units).

New signals at neighbors:

- UP $(2,1)$: $d^2 = (2-1)^2 + (1-2)^2 = 2$, $r = 0.779$
- DOWN $(2,3)$: $d^2 = (2-1)^2 + (3-2)^2 = 2$, $r = 0.779$
- LEFT $(1,2)$: $d^2 = (1-1)^2 + (2-2)^2 = 0$, $r = 1.000$
- RIGHT $(3,2)$: $d^2 = (3-1)^2 + (2-2)^2 = 4$, $r = 0.607$

Weights: UP = $2.558$, DOWN = $2.558$, LEFT = $\mathbf{3.000}$, RIGHT = $2.214$

**Preferred direction: LEFT** (hotspot has moved to the other side).

#### 5. Interpretation

A single hotspot drift event completely reverses the agent's preferred direction. This illustrates why System B must repeatedly scan and react: any previously gathered information becomes stale as the landscape shifts. The agent is permanently reactive, with no ability to predict where the signal will move.

---

## 7. Example Group E: Temperature Sensitivity

### E1. Low vs High Temperature

#### 1. Objective

Demonstrate the effect of temperature on action selection with identical weights.

#### 2. Scenario

Weights from Example A2: $\mathbf{w} = (2.8, 1.2, 1.0, 1.4, 1.0, 1.0)$.

#### 3. Low Temperature (T = 0.5)

$w_{\max} = 2.8$

| Action | $w$ | $\exp(2.0 \cdot (w - 2.8))$ | Probability |
|--------|-----|-----|-------------|
| UP | 2.8 | $\exp(0) = 1.000$ | **0.686** |
| DOWN | 1.2 | $\exp(-3.2) = 0.041$ | 0.028 |
| LEFT | 1.0 | $\exp(-3.6) = 0.027$ | 0.019 |
| RIGHT | 1.4 | $\exp(-2.8) = 0.061$ | 0.042 |
| SCAN | 1.0 | $\exp(-3.6) = 0.027$ | 0.019 |
| STAY | 1.0 | $\exp(-3.6) = 0.027$ | 0.019 |

Sum $= 1.183$. UP has **68.6%** probability -- nearly deterministic.

#### 4. High Temperature (T = 3.0)

$w_{\max} = 2.8$

| Action | $w$ | $\exp(0.333 \cdot (w - 2.8))$ | Probability |
|--------|-----|-----|-------------|
| UP | 2.8 | $\exp(0) = 1.000$ | **0.219** |
| DOWN | 1.2 | $\exp(-0.533) = 0.587$ | 0.128 |
| LEFT | 1.0 | $\exp(-0.600) = 0.549$ | 0.120 |
| RIGHT | 1.4 | $\exp(-0.467) = 0.627$ | 0.137 |
| SCAN | 1.0 | $\exp(-0.600) = 0.549$ | 0.120 |
| STAY | 1.0 | $\exp(-0.600) = 0.549$ | 0.120 |

Sum $= 3.861$. UP has only **21.9%** probability -- much more exploratory.

#### 5. Interpretation

| Temperature | UP Probability | Behavior |
|---|---|---|
| $T = 0.5$ | 68.6% | Near-greedy: strongly exploits best direction |
| $T = 1.0$ | 51.4% (from A2) | Balanced: favors best but explores alternatives |
| $T = 3.0$ | 21.9% | Exploratory: all actions have comparable probability |

Low temperature concentrates probability mass on the highest-weight action.
High temperature spreads probability across all admissible actions.
The temperature parameter is System B's primary knob for controlling the exploration-exploitation tradeoff.
