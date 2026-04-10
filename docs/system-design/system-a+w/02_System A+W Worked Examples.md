# System A+W Worked Examples

## Metadata
- Project: AXIS -- Complex Mechanistic Systems Experiment
- Author: Oliver Grau
- Type: Worked Example / Formal Companion Note
- Status: Draft v1.0

## 1. Purpose of this Document

This document provides **worked example scenarios** for System A+W.

The goal is:

- to **validate internal consistency** of the dual-drive model
- to **demonstrate the interplay between hunger and curiosity** across different energy levels
- to **show the drive weight dynamics** in concrete numerical form
- to **prepare for implementation** by defining reproducible calculation paths

No new concepts are introduced.
All examples strictly follow the definitions from:

- `01_System A+W Model.md`
- System A Baseline documents (for inherited definitions)

---

## 2. Scope and Constraints

This document assumes:

- **Dual-drive system**: Hunger + Curiosity
- **World model**: Visit-count map
- **Memory used for sensory novelty**
- **No planning**
- **Deterministic policy evaluation (unless explicitly stated otherwise)**

---

## 3. Structure of Worked Examples

Each example follows the same structure:

1. **Initial State Definition**
2. **Local Observation (Sensor Input)**
3. **Novelty Computation (Spatial + Sensory)**
4. **Drive Evaluation (Hunger + Curiosity)**
5. **Drive Arbitration (Dynamic Weights)**
6. **Action Scoring**
7. **Policy Selection**
8. **State Transition**
9. **Post-State Analysis**

This extends the System A structure with steps 3 and 5.

---

## 4. Common Parameters

Unless stated otherwise, all examples use:

### 4.1 Agent Parameters

| Parameter | Symbol | Value |
|---|---|---|
| Max energy | $E_{\max}$ | 100.0 |
| Memory capacity | $k$ | 5 (configurable) |
| Temperature | $\beta$ | 2.0 |

### 4.2 Hunger Parameters

| Parameter | Symbol | Value |
|---|---|---|
| Consume weight | $w_{consume}$ | 2.5 |
| Stay suppression | $\lambda_{stay}$ | 0.1 |

### 4.3 Curiosity Parameters

| Parameter | Symbol | Value |
|---|---|---|
| Base curiosity | $\mu_C$ | 1.0 |
| Spatial-sensory balance | $\alpha$ | 0.5 |
| Explore suppression | $\lambda_{explore}$ | 0.3 |

### 4.4 Arbitration Parameters

| Parameter | Symbol | Value |
|---|---|---|
| Hunger weight base | $w_H^{base}$ | 0.3 |
| Curiosity weight base | $w_C^{base}$ | 1.0 |
| Gating sharpness | $\gamma$ | 2.0 |

### 4.5 Transition Parameters

| Parameter | Symbol | Value |
|---|---|---|
| Move cost | $c_{move}$ | 1.0 |
| Consume cost | $c_{consume}$ | 1.0 |
| Stay cost | $c_{stay}$ | 0.5 |
| Max consume | $\Delta R_{\max}$ | 1.0 |
| Energy gain factor | $\kappa$ | 10.0 |

---

## 5. Example Categories

---

## 5.1 Example Group A: Drive Weight Dynamics

### A1. Well-Fed Agent in Novel Territory

#### 1. Objective

Demonstrate that a well-fed agent strongly prefers exploration over consumption.

---

#### 2. Initial State

$$
e_0 = 90.0, \quad E_{\max} = 100.0
$$

World model: all neighboring cells unvisited ($w_t(p_{dir}) = 0$ for all $dir$).

Memory: empty ($|m_t| = 0$).

Agent is at position $(3, 3)$ in a 10x10 grid.

---

#### 3. Local Observation

| Cell | $r$ (resource) | $b$ (traversability) |
|---|---|---|
| Current | 0.8 | 1.0 |
| Up | 0.0 | 1.0 |
| Down | 0.0 | 1.0 |
| Left | 0.3 | 1.0 |
| Right | 0.0 | 1.0 |

---

#### 4. Novelty Computation

##### 4.1 Spatial Novelty

All neighbors are unvisited:

$$
\nu^{spatial}_{up} = \frac{1}{1 + 0} = 1.0
$$

$$
\nu^{spatial}_{down} = \frac{1}{1 + 0} = 1.0
$$

$$
\nu^{spatial}_{left} = \frac{1}{1 + 0} = 1.0
$$

$$
\nu^{spatial}_{right} = \frac{1}{1 + 0} = 1.0
$$

##### 4.2 Sensory Novelty

Memory is empty, so $\bar{r}_{dir} = 0$ for all directions:

$$
\nu^{sensory}_{up} = |0.0 - 0| = 0.0
$$

$$
\nu^{sensory}_{down} = |0.0 - 0| = 0.0
$$

$$
\nu^{sensory}_{left} = |0.3 - 0| = 0.3
$$

$$
\nu^{sensory}_{right} = |0.0 - 0| = 0.0
$$

##### 4.3 Composite Novelty ($\alpha = 0.5$)

$$
\nu_{up} = 0.5 \cdot 1.0 + 0.5 \cdot 0.0 = 0.50
$$

$$
\nu_{down} = 0.5 \cdot 1.0 + 0.5 \cdot 0.0 = 0.50
$$

$$
\nu_{left} = 0.5 \cdot 1.0 + 0.5 \cdot 0.3 = 0.65
$$

$$
\nu_{right} = 0.5 \cdot 1.0 + 0.5 \cdot 0.0 = 0.50
$$

---

#### 5. Drive Evaluation

##### Hunger Drive

$$
d_H = 1 - \frac{90}{100} = 0.10
$$

##### Curiosity Drive

Memory is empty, so $\bar{\nu}_t = 0$:

$$
d_C = 1.0 \cdot (1 - 0) = 1.0
$$

---

#### 6. Drive Arbitration

$$
w_H = 0.3 + (1 - 0.3) \cdot 0.10^{2} = 0.3 + 0.7 \cdot 0.01 = 0.307
$$

$$
w_C = 1.0 \cdot (1 - 0.10)^{2} = 1.0 \cdot 0.81 = 0.810
$$

---

#### 7. Action Scoring

##### Hunger Contributions ($w_H \cdot d_H \cdot \phi_H$)

| Action | $\phi_H$ | $w_H \cdot d_H \cdot \phi_H$ |
|---|---|---|
| UP | $r_{up} = 0.0$ | $0.307 \times 0.10 \times 0.0 = 0.000$ |
| DOWN | $r_{down} = 0.0$ | $0.307 \times 0.10 \times 0.0 = 0.000$ |
| LEFT | $r_{left} = 0.3$ | $0.307 \times 0.10 \times 0.3 = 0.009$ |
| RIGHT | $r_{right} = 0.0$ | $0.307 \times 0.10 \times 0.0 = 0.000$ |
| CONSUME | $w_{consume} \cdot r_c = 2.5 \times 0.8 = 2.0$ | $0.307 \times 0.10 \times 2.0 = 0.061$ |
| STAY | $-\lambda_{stay} = -0.1$ | $0.307 \times 0.10 \times (-0.1) = -0.003$ |

##### Curiosity Contributions ($w_C \cdot d_C \cdot \phi_C$)

| Action | $\phi_C$ | $w_C \cdot d_C \cdot \phi_C$ |
|---|---|---|
| UP | $\nu_{up} = 0.50$ | $0.810 \times 1.0 \times 0.50 = 0.405$ |
| DOWN | $\nu_{down} = 0.50$ | $0.810 \times 1.0 \times 0.50 = 0.405$ |
| LEFT | $\nu_{left} = 0.65$ | $0.810 \times 1.0 \times 0.65 = 0.527$ |
| RIGHT | $\nu_{right} = 0.50$ | $0.810 \times 1.0 \times 0.50 = 0.405$ |
| CONSUME | $-\lambda_{explore} = -0.3$ | $0.810 \times 1.0 \times (-0.3) = -0.243$ |
| STAY | $-\lambda_{explore} = -0.3$ | $0.810 \times 1.0 \times (-0.3) = -0.243$ |

##### Combined Scores

| Action | Hunger | Curiosity | $\psi(a)$ |
|---|---|---|---|
| UP | 0.000 | 0.405 | **0.405** |
| DOWN | 0.000 | 0.405 | **0.405** |
| LEFT | 0.009 | 0.527 | **0.536** |
| RIGHT | 0.000 | 0.405 | **0.405** |
| CONSUME | 0.061 | -0.243 | **-0.182** |
| STAY | -0.003 | -0.243 | **-0.246** |

---

#### 8. Policy Selection ($\beta = 2.0$)

Computing $\exp(\beta \cdot \psi(a))$:

| Action | $\beta \cdot \psi$ | $\exp(\beta \cdot \psi)$ |
|---|---|---|
| UP | $2.0 \times 0.405 = 0.810$ | $\exp(0.810) \approx 2.248$ |
| DOWN | $2.0 \times 0.405 = 0.810$ | $\exp(0.810) \approx 2.248$ |
| LEFT | $2.0 \times 0.536 = 1.072$ | $\exp(1.072) \approx 2.921$ |
| RIGHT | $2.0 \times 0.405 = 0.810$ | $\exp(0.810) \approx 2.248$ |
| CONSUME | $2.0 \times (-0.182) = -0.364$ | $\exp(-0.364) \approx 0.695$ |
| STAY | $2.0 \times (-0.246) = -0.492$ | $\exp(-0.492) \approx 0.611$ |

Normalization:

$$
Z = 2.248 + 2.248 + 2.921 + 2.248 + 0.695 + 0.611 = 10.971
$$

| Action | $P(a)$ |
|---|---|
| UP | $2.248 / 10.971 \approx 0.2049$ |
| DOWN | $2.248 / 10.971 \approx 0.2049$ |
| LEFT | $2.921 / 10.971 \approx 0.2663$ |
| RIGHT | $2.248 / 10.971 \approx 0.2049$ |
| CONSUME | $0.695 / 10.971 \approx 0.0633$ |
| STAY | $0.611 / 10.971 \approx 0.0557$ |

---

#### 9. Conclusion

> Despite standing on a cell with $r_c = 0.8$ resource, the well-fed agent has only **6.3% probability of consuming**. Movement actions collectively account for **88.1%** of the probability mass, with LEFT slightly favored due to its higher composite novelty. Curiosity thoroughly dominates behavior.

Compare to System A baseline with the same observation and $d_H = 0.10$: System A would produce near-uniform action probabilities with a slight edge for CONSUME, since the hunger drive is weak and there is no curiosity to push toward movement. System A+W produces structured exploration behavior even at low hunger levels.

---

---

## 5.2 Example Group B: Hunger-Curiosity Competition

### B1. Moderate Hunger with Resource Present

#### 1. Objective

Demonstrate the balanced regime where both drives contribute meaningfully.

---

#### 2. Initial State

$$
e_0 = 50.0, \quad E_{\max} = 100.0
$$

World model: current cell visited 3 times, all neighbors visited once.

Memory contains 3 entries with mean $\bar{r}_{dir}$:

| Direction | $\bar{r}_{dir}$ |
|---|---|
| Current | 0.4 |
| Up | 0.1 |
| Down | 0.0 |
| Left | 0.2 |
| Right | 0.0 |

---

#### 3. Local Observation

| Cell | $r$ (resource) | $b$ (traversability) |
|---|---|---|
| Current | 0.6 | 1.0 |
| Up | 0.0 | 1.0 |
| Down | 0.4 | 1.0 |
| Left | 0.0 | 0.0 |
| Right | 0.0 | 1.0 |

Note: LEFT is an obstacle ($b = 0$).

---

#### 4. Novelty Computation

##### 4.1 Spatial Novelty

$$
\nu^{spatial}_{up} = \frac{1}{1 + 1} = 0.500
$$

$$
\nu^{spatial}_{down} = \frac{1}{1 + 1} = 0.500
$$

$$
\nu^{spatial}_{left} = \frac{1}{1 + 1} = 0.500
$$

$$
\nu^{spatial}_{right} = \frac{1}{1 + 1} = 0.500
$$

##### 4.2 Sensory Novelty

$$
\nu^{sensory}_{up} = |0.0 - 0.1| = 0.1
$$

$$
\nu^{sensory}_{down} = |0.4 - 0.0| = 0.4
$$

$$
\nu^{sensory}_{left} = |0.0 - 0.2| = 0.2
$$

$$
\nu^{sensory}_{right} = |0.0 - 0.0| = 0.0
$$

##### 4.3 Composite Novelty ($\alpha = 0.5$)

$$
\nu_{up} = 0.5 \times 0.500 + 0.5 \times 0.1 = 0.300
$$

$$
\nu_{down} = 0.5 \times 0.500 + 0.5 \times 0.4 = 0.450
$$

$$
\nu_{left} = 0.5 \times 0.500 + 0.5 \times 0.2 = 0.350
$$

$$
\nu_{right} = 0.5 \times 0.500 + 0.5 \times 0.0 = 0.250
$$

---

#### 5. Drive Evaluation

##### Hunger

$$
d_H = 1 - \frac{50}{100} = 0.50
$$

##### Curiosity

Novelty saturation from 3 memory entries. Computing mean sensory surprise of each memory entry against the current observation across all 4 directions would require the full memory contents. For simplicity, assume $\bar{\nu}_t = 0.15$:

$$
d_C = 1.0 \times (1 - 0.15) = 0.85
$$

---

#### 6. Drive Arbitration

$$
w_H = 0.3 + 0.7 \times 0.50^{2} = 0.3 + 0.7 \times 0.25 = 0.475
$$

$$
w_C = 1.0 \times (1 - 0.50)^{2} = 1.0 \times 0.25 = 0.250
$$

---

#### 7. Action Scoring

##### Hunger Contributions

| Action | $\phi_H$ | $w_H \cdot d_H \cdot \phi_H$ |
|---|---|---|
| UP | 0.0 | $0.475 \times 0.50 \times 0.0 = 0.000$ |
| DOWN | 0.4 | $0.475 \times 0.50 \times 0.4 = 0.095$ |
| LEFT | 0.0 | $0.475 \times 0.50 \times 0.0 = 0.000$ |
| RIGHT | 0.0 | $0.475 \times 0.50 \times 0.0 = 0.000$ |
| CONSUME | $2.5 \times 0.6 = 1.5$ | $0.475 \times 0.50 \times 1.5 = 0.356$ |
| STAY | $-0.1$ | $0.475 \times 0.50 \times (-0.1) = -0.024$ |

##### Curiosity Contributions

| Action | $\phi_C$ | $w_C \cdot d_C \cdot \phi_C$ |
|---|---|---|
| UP | 0.300 | $0.250 \times 0.85 \times 0.300 = 0.064$ |
| DOWN | 0.450 | $0.250 \times 0.85 \times 0.450 = 0.096$ |
| LEFT | 0.350 | $0.250 \times 0.85 \times 0.350 = 0.074$ |
| RIGHT | 0.250 | $0.250 \times 0.85 \times 0.250 = 0.053$ |
| CONSUME | $-0.3$ | $0.250 \times 0.85 \times (-0.3) = -0.064$ |
| STAY | $-0.3$ | $0.250 \times 0.85 \times (-0.3) = -0.064$ |

##### Combined Scores (before masking)

| Action | Hunger | Curiosity | $\psi(a)$ |
|---|---|---|---|
| UP | 0.000 | 0.064 | 0.064 |
| DOWN | 0.095 | 0.096 | **0.191** |
| LEFT | 0.000 | 0.074 | 0.074 |
| RIGHT | 0.000 | 0.053 | 0.053 |
| CONSUME | 0.356 | -0.064 | **0.292** |
| STAY | -0.024 | -0.064 | -0.088 |

##### Admissibility Masking

LEFT is blocked (obstacle: $b = 0$). Set $\psi(\text{LEFT}) = -\infty$.

| Action | $\psi(a)$ |
|---|---|
| UP | 0.064 |
| DOWN | **0.191** |
| LEFT | $-\infty$ |
| RIGHT | 0.053 |
| CONSUME | **0.292** |
| STAY | -0.088 |

---

#### 8. Policy Selection ($\beta = 2.0$)

| Action | $\exp(\beta \cdot \psi)$ |
|---|---|
| UP | $\exp(0.128) \approx 1.137$ |
| DOWN | $\exp(0.382) \approx 1.465$ |
| LEFT | $0$ (masked) |
| RIGHT | $\exp(0.106) \approx 1.112$ |
| CONSUME | $\exp(0.584) \approx 1.793$ |
| STAY | $\exp(-0.176) \approx 0.839$ |

$$
Z = 1.137 + 1.465 + 0 + 1.112 + 1.793 + 0.839 = 6.346
$$

| Action | $P(a)$ |
|---|---|
| UP | $1.137 / 6.346 \approx 0.1791$ |
| DOWN | $1.465 / 6.346 \approx 0.2309$ |
| LEFT | $0.0000$ |
| RIGHT | $1.112 / 6.346 \approx 0.1753$ |
| CONSUME | $1.793 / 6.346 \approx 0.2825$ |
| STAY | $0.839 / 6.346 \approx 0.1322$ |

---

#### 9. Conclusion

> At 50% energy, CONSUME leads with **28.3%** but DOWN is close at **23.1%**. DOWN is boosted by both drives: hunger (resource $r_{down} = 0.4$) and curiosity (high sensory novelty for that direction). The agent is torn between consuming the immediately available resource and moving toward a novel, resource-rich direction. This is the balanced foraging regime.

---

---

## 5.3 Example Group C: Hunger Dominance

### C1. Starving Agent Ignores Novelty

#### 1. Objective

Demonstrate that extreme hunger effectively silences curiosity.

---

#### 2. Initial State

$$
e_0 = 5.0, \quad E_{\max} = 100.0
$$

World model: all neighbors unvisited ($w_t(p_{dir}) = 0$).

Memory: empty.

---

#### 3. Local Observation

| Cell | $r$ (resource) | $b$ (traversability) |
|---|---|---|
| Current | 0.5 | 1.0 |
| Up | 0.0 | 1.0 |
| Down | 0.0 | 1.0 |
| Left | 0.0 | 1.0 |
| Right | 0.2 | 1.0 |

---

#### 4. Drive Evaluation

$$
d_H = 1 - \frac{5}{100} = 0.95
$$

$$
d_C = 1.0 \times (1 - 0) = 1.0
$$

---

#### 5. Drive Arbitration

$$
w_H = 0.3 + 0.7 \times 0.95^{2} = 0.3 + 0.7 \times 0.9025 = 0.932
$$

$$
w_C = 1.0 \times (1 - 0.95)^{2} = 1.0 \times 0.0025 = 0.003
$$

> Curiosity weight is effectively zero. The drive weight function has gated curiosity out.

---

#### 6. Novelty Computation

With all neighbors unvisited and empty memory:

$$
\nu_{dir} = 0.5 \times 1.0 + 0.5 \times r_{dir}
$$

$$
\nu_{up} = 0.50, \quad \nu_{down} = 0.50, \quad \nu_{left} = 0.50, \quad \nu_{right} = 0.60
$$

---

#### 7. Action Scoring

##### Hunger Contributions

| Action | $w_H \cdot d_H \cdot \phi_H$ |
|---|---|
| UP | $0.932 \times 0.95 \times 0.0 = 0.000$ |
| DOWN | $0.932 \times 0.95 \times 0.0 = 0.000$ |
| LEFT | $0.932 \times 0.95 \times 0.0 = 0.000$ |
| RIGHT | $0.932 \times 0.95 \times 0.2 = 0.177$ |
| CONSUME | $0.932 \times 0.95 \times 1.25 = 1.107$ |
| STAY | $0.932 \times 0.95 \times (-0.1) = -0.089$ |

##### Curiosity Contributions

| Action | $w_C \cdot d_C \cdot \phi_C$ |
|---|---|
| UP | $0.003 \times 1.0 \times 0.50 = 0.001$ |
| DOWN | $0.003 \times 1.0 \times 0.50 = 0.001$ |
| LEFT | $0.003 \times 1.0 \times 0.50 = 0.001$ |
| RIGHT | $0.003 \times 1.0 \times 0.60 = 0.002$ |
| CONSUME | $0.003 \times 1.0 \times (-0.3) = -0.001$ |
| STAY | $0.003 \times 1.0 \times (-0.3) = -0.001$ |

##### Combined Scores

| Action | Hunger | Curiosity | $\psi(a)$ |
|---|---|---|---|
| UP | 0.000 | 0.001 | 0.001 |
| DOWN | 0.000 | 0.001 | 0.001 |
| LEFT | 0.000 | 0.001 | 0.001 |
| RIGHT | 0.177 | 0.002 | 0.179 |
| CONSUME | 1.107 | -0.001 | **1.106** |
| STAY | -0.089 | -0.001 | -0.090 |

---

#### 8. Policy Selection ($\beta = 2.0$)

| Action | $\exp(\beta \cdot \psi)$ |
|---|---|
| UP | $\exp(0.002) \approx 1.002$ |
| DOWN | $\exp(0.002) \approx 1.002$ |
| LEFT | $\exp(0.002) \approx 1.002$ |
| RIGHT | $\exp(0.358) \approx 1.430$ |
| CONSUME | $\exp(2.212) \approx 9.133$ |
| STAY | $\exp(-0.180) \approx 0.835$ |

$$
Z = 1.002 + 1.002 + 1.002 + 1.430 + 9.133 + 0.835 = 14.404
$$

| Action | $P(a)$ |
|---|---|
| UP | 0.0696 |
| DOWN | 0.0696 |
| LEFT | 0.0696 |
| RIGHT | 0.0993 |
| CONSUME | **0.6341** |
| STAY | 0.0580 |

---

#### 9. Conclusion

> At $e_t = 5$ (5% energy), CONSUME dominates at **63.4%** despite all four neighbors being completely unvisited. Curiosity contributes less than 0.2% to any action score. The gating function has reduced $w_C$ to 0.003, making the drive effectively invisible.

> Behavior is indistinguishable from System A baseline at this energy level. The reduction property holds numerically.

---

---

## 5.4 Example Group D: Exploration Dynamics

### D1. Forage-Explore Cycle (Multi-Step Trajectory)

#### 1. Objective

Trace a minimal 4-step trajectory that demonstrates the forage-explore cycle:
1. Agent consumes a resource (regaining energy)
2. Curiosity increases as hunger drops
3. Agent moves toward a novel cell
4. Curiosity contribution to that direction is reduced on the next step

---

#### 2. Initial State

$$
e_0 = 40.0, \quad E_{\max} = 100.0
$$

World model: current cell $(5, 5)$ visited 2 times, all neighbors visited 0 times.

Memory: empty. Grid: 10x10.

---

#### Step 0: Consume

**Observation:** $r_c = 0.8$, all neighbors $r_{dir} = 0.0$.

**Drives:** $d_H = 0.60$, $d_C = 1.0$.

**Weights:**
$$
w_H = 0.3 + 0.7 \times 0.36 = 0.552
$$
$$
w_C = 1.0 \times 0.16 = 0.160
$$

**Key scores:**
- CONSUME: $w_H \cdot d_H \cdot 2.0 + w_C \cdot d_C \cdot (-0.3) = 0.552 \times 0.60 \times 2.0 + 0.160 \times 1.0 \times (-0.3) = 0.662 - 0.048 = 0.614$
- Movement (each): $w_C \cdot d_C \cdot 0.5 = 0.160 \times 0.5 = 0.080$

CONSUME wins decisively. Agent consumes.

**Transition:**
$$
\Delta R^{cons} = \min(0.8, 1.0) = 0.8
$$
$$
e_1 = 40.0 - 1.0 + 10.0 \times 0.8 = 47.0
$$

---

#### Step 1: Post-Consumption Decision

**Observation:** $r_c = 0.0$ (resource consumed), neighbors unchanged.

**Drives:** $d_H = 1 - 47/100 = 0.53$, $d_C = 1.0$.

**Weights:**
$$
w_H = 0.3 + 0.7 \times 0.53^2 = 0.3 + 0.7 \times 0.281 = 0.497
$$
$$
w_C = 1.0 \times 0.47^2 = 0.221
$$

**Key scores:**
- CONSUME: $w_H \cdot d_H \cdot 2.5 \times 0.0 + w_C \cdot d_C \times (-0.3) = 0 - 0.066 = -0.066$ (no resource left)
- Movement (each): $w_C \cdot d_C \cdot 0.5 = 0.221 \times 0.5 = 0.111$

Movement actions now dominate. Suppose the agent selects RIGHT (to $(6, 5)$).

**Transition:**
$$
e_2 = 47.0 - 1.0 = 46.0
$$
$$
w_2(6, 5) = 0 + 1 = 1
$$

---

#### Step 2: Continuing Exploration

**State:** $e_2 = 46.0$, now at $(6, 5)$.

**World model:** $(6, 5)$ visited 1 time, $(7, 5)$ visited 0 times, $(5, 5)$ visited 2 times.

**Spatial novelty:**
- RIGHT (to $(7, 5)$): $\nu^{spatial} = 1/(1+0) = 1.0$ (unvisited)
- LEFT (to $(5, 5)$): $\nu^{spatial} = 1/(1+2) = 0.333$ (visited twice)

**Drives:** $d_H = 0.54$, $d_C = 1.0$.

**Key insight:** The curiosity contribution for RIGHT ($\nu = 1.0$) is much higher than for LEFT ($\nu = 0.333$). The agent preferentially continues exploring forward rather than returning to familiar territory.

---

#### Step 3: Forward Bias Established

At $(7, 5)$ with $e_3 = 45.0$:
- LEFT (back to $(6, 5)$): $\nu^{spatial} = 1/(1+1) = 0.5$
- RIGHT (to $(8, 5)$): $\nu^{spatial} = 1/(1+0) = 1.0$

The curiosity drive produces a consistent forward bias. The agent continues exploring until hunger increases sufficiently to override curiosity, at which point it switches to resource-seeking.

---

#### 4. Trajectory Summary

| Step | Position | Action | Energy | $d_H$ | $w_C$ | Dominant |
|---|---|---|---|---|---|---|
| 0 | $(5,5)$ | CONSUME | $40 \to 47$ | 0.60 | 0.160 | Hunger |
| 1 | $(5,5)$ | RIGHT | $47 \to 46$ | 0.53 | 0.221 | Curiosity |
| 2 | $(6,5)$ | RIGHT | $46 \to 45$ | 0.54 | 0.212 | Curiosity |
| 3 | $(7,5)$ | RIGHT | $45 \to 44$ | 0.55 | 0.203 | Curiosity |

---

#### 5. Conclusion

> After consuming a resource and gaining energy, the agent immediately shifts toward exploration. The visit-count map creates a directional bias away from familiar territory. The forage-explore cycle emerges naturally from the dynamic weight function: consumption reduces hunger, which increases $w_C$, which activates curiosity-driven movement.

---

---

## 5.5 Example Group E: Parameter Sensitivity

### E1. Effect of Gating Sharpness $\gamma$

#### Objective

Show how $\gamma$ controls the hunger-curiosity transition width.

Fixed state: $e_t = 50.0$, $d_H = 0.50$.

| $\gamma$ | $w_H$ | $w_C$ | Interpretation |
|---|---|---|---|
| 0.5 | $0.3 + 0.7 \times 0.50^{0.5} = 0.795$ | $1.0 \times 0.50^{0.5} = 0.707$ | Gradual. Both drives active at moderate hunger. |
| 1.0 | $0.3 + 0.7 \times 0.50 = 0.650$ | $1.0 \times 0.50 = 0.500$ | Linear. Proportional trade-off. |
| 2.0 | $0.3 + 0.7 \times 0.25 = 0.475$ | $1.0 \times 0.25 = 0.250$ | Sharp. Curiosity drops quickly with hunger. |
| 4.0 | $0.3 + 0.7 \times 0.0625 = 0.344$ | $1.0 \times 0.0625 = 0.063$ | Very sharp. Curiosity nearly gone at 50% hunger. |

---

#### Conclusion

> Higher $\gamma$ creates a more "Maslow-like" hierarchy: curiosity is preserved at low hunger but drops sharply. Lower $\gamma$ creates a more gradual blend where both drives remain influential across a wider energy range.

The default $\gamma = 2.0$ provides a reasonable balance: at 50% hunger, curiosity still has 25% of its weight, allowing some exploration even during moderate energy deficit.

---

### E2. Effect of Spatial-Sensory Balance $\alpha$

#### Objective

Compare the novelty signal for a cell visited 3 times but with unexpected resource ($r = 0.8$, memory average $\bar{r} = 0.1$):

| $\alpha$ | $\nu^{spatial}$ | $\nu^{sensory}$ | $\nu_{composite}$ | Interpretation |
|---|---|---|---|---|
| 0.0 | (ignored) | $|0.8 - 0.1| = 0.7$ | 0.700 | High novelty: resource change detected |
| 0.5 | $1/(1+3) = 0.25$ | 0.7 | 0.475 | Moderate: sensory surprise partly offset by visit count |
| 1.0 | 0.25 | (ignored) | 0.250 | Low novelty: visited 3 times, so familiar |

---

#### Conclusion

> When $\alpha = 0$, the agent responds to environmental **change** (a resource appeared where none was before). When $\alpha = 1$, the agent responds only to spatial **coverage** (how many times visited). The composite $\alpha = 0.5$ balances both: the agent notices changes in visited areas while still preferring completely unvisited territory.

---

---

## 5.6 Example Group F: World Model Mechanics (Dead Reckoning)

### F1. Dead Reckoning and Visit-Count Map (Multi-Step Trajectory)

#### 1. Objective

Demonstrate how the world model builds up through **dead reckoning** — path integration using only the agent's own motor commands and their outcomes. No absolute position information is used. Show how the visit-count map evolves and drives the spatial novelty signal.

---

#### 2. Initial State

$$
\hat{p}_0 = (0, 0), \quad w_0 = \{(0, 0): 1\}
$$

The agent starts at relative origin. All other positions have visit count 0 (not stored in the map).

---

#### 3. Six-Step Trajectory

##### Step 0: Move RIGHT — succeeds

| Input | Value |
|---|---|
| Action $a_0$ | RIGHT |
| Movement signal $\mu_0$ | 1 (moved) |

Dead reckoning:

$$
\hat{p}_1 = (0, 0) + 1 \cdot \Delta(\text{RIGHT}) = (0, 0) + (1, 0) = (1, 0)
$$

Visit-count update:

$$
w_1(1, 0) = 0 + 1 = 1
$$

**Map after step 0:** $\{(0, 0): 1, \; (1, 0): 1\}$

---

##### Step 1: Move RIGHT — succeeds

$$
\hat{p}_2 = (1, 0) + 1 \cdot (1, 0) = (2, 0)
$$

$$
w_2(2, 0) = 0 + 1 = 1
$$

**Map after step 1:** $\{(0, 0): 1, \; (1, 0): 1, \; (2, 0): 1\}$

---

##### Step 2: Move RIGHT — **fails** (obstacle or boundary)

| Input | Value |
|---|---|
| Action $a_2$ | RIGHT |
| Movement signal $\mu_2$ | 0 (did not move) |

Dead reckoning:

$$
\hat{p}_3 = (2, 0) + 0 \cdot (1, 0) = (2, 0)
$$

The agent stays at $(2, 0)$. The visit count at $(2, 0)$ increases:

$$
w_3(2, 0) = 1 + 1 = 2
$$

**Map after step 2:** $\{(0, 0): 1, \; (1, 0): 1, \; (2, 0): 2\}$

> **Key observation:** Failed movement still increments the visit count at the current position. The agent "knows" it failed to move because $\mu_2 = 0$. It does not update its position estimate. Revisiting the same cell makes it less novel.

---

##### Step 3: Move UP — succeeds

$$
\hat{p}_4 = (2, 0) + 1 \cdot (0, 1) = (2, 1)
$$

$$
w_4(2, 1) = 0 + 1 = 1
$$

**Map after step 3:** $\{(0, 0): 1, \; (1, 0): 1, \; (2, 0): 2, \; (2, 1): 1\}$

---

##### Step 4: Move LEFT — succeeds

$$
\hat{p}_5 = (2, 1) + 1 \cdot (-1, 0) = (1, 1)
$$

$$
w_5(1, 1) = 0 + 1 = 1
$$

**Map after step 4:** $\{(0, 0): 1, \; (1, 0): 1, \; (2, 0): 2, \; (2, 1): 1, \; (1, 1): 1\}$

---

##### Step 5: Move LEFT — succeeds

$$
\hat{p}_6 = (1, 1) + 1 \cdot (-1, 0) = (0, 1)
$$

$$
w_6(0, 1) = 0 + 1 = 1
$$

**Map after step 5:** $\{(0, 0): 1, \; (1, 0): 1, \; (2, 0): 2, \; (2, 1): 1, \; (1, 1): 1, \; (0, 1): 1\}$

---

#### 4. Spatial Novelty at Final Position

Agent is now at $\hat{p}_6 = (0, 1)$. Computing spatial novelty for each neighbor:

| Direction | $\Delta(dir)$ | Neighbor $\hat{p}$ | $w_6(\hat{p})$ | $\nu^{spatial}$ |
|---|---|---|---|---|
| UP | $(0, +1)$ | $(0, 2)$ | 0 | $\frac{1}{1+0} = 1.000$ |
| DOWN | $(0, -1)$ | $(0, 0)$ | 1 | $\frac{1}{1+1} = 0.500$ |
| LEFT | $(-1, 0)$ | $(-1, 1)$ | 0 | $\frac{1}{1+0} = 1.000$ |
| RIGHT | $(+1, 0)$ | $(1, 1)$ | 1 | $\frac{1}{1+1} = 0.500$ |

---

#### 5. Spatial Map Visualization

```
        y
        2  [ ]  [ ]  [ ]     [ ] = unvisited (w=0)
        1  [1]  [1]  [1]     [n] = visit count
        0  [1]  [1]  [2]
           0    1    2    x
                          ^-- wall here (step 2 failed)
```

---

#### 6. Conclusion

> The agent has explored a roughly L-shaped path through dead reckoning alone. At position $(0, 1)$, the spatial novelty signal **distinguishes explored from unexplored territory**: UP and LEFT point toward unvisited cells ($\nu = 1.0$), while DOWN and RIGHT lead back to visited cells ($\nu = 0.5$). The curiosity drive will bias exploration toward the unvisited directions.

> The failed movement at step 2 demonstrates graceful handling: the relative position stays correct, and the repeated occupation increases the visit count, reducing future spatial novelty for that cell.

---

---

### F2. Revisitation and Novelty Decay

#### 1. Objective

Show how spatial novelty decays hyperbolically as a position is revisited, creating diminishing returns for staying in the same area.

---

#### 2. Novelty vs. Visit Count

For a cell at relative position $\hat{p}$:

$$
\nu^{spatial} = \frac{1}{1 + w_t(\hat{p})}
$$

| Visits $w_t$ | $\nu^{spatial}$ | Interpretation |
|---|---|---|
| 0 | 1.000 | Completely novel — never been here |
| 1 | 0.500 | Half novelty — visited once |
| 2 | 0.333 | Diminishing — getting familiar |
| 3 | 0.250 | Low novelty |
| 5 | 0.167 | Well-trodden |
| 10 | 0.091 | Very familiar |
| 20 | 0.048 | Negligible novelty |
| 100 | 0.010 | Effectively zero |

---

#### 3. Practical Implication

Consider an agent at $\hat{p}_t$ with two neighboring cells:

- **Cell A** (previously unvisited): $w_t = 0 \implies \nu^{spatial}_A = 1.000$
- **Cell B** (visited 3 times): $w_t = 3 \implies \nu^{spatial}_B = 0.250$

The ratio of spatial novelty contributions:

$$
\frac{\nu^{spatial}_A}{\nu^{spatial}_B} = \frac{1.000}{0.250} = 4.0
$$

The curiosity drive contributes **4x more** modulation toward the unvisited cell than toward the visited one. Combined with the softmax policy, this creates a strong directional bias toward unexplored territory.

---

#### 4. Conclusion

> The hyperbolic decay $\frac{1}{1+n}$ has desirable properties: it drops quickly from 1.0 to 0.5 on first visit (strong "I've been here" signal), continues to decay but never reaches zero (there is always some residual novelty), and the decay rate itself slows (going from 5 to 10 visits matters less than going from 0 to 1). This mirrors biological habituation: the first exposure has the largest impact on familiarity.

---

---

### F3. Dead Reckoning with CONSUME and STAY Actions

#### 1. Objective

Verify that non-movement actions (CONSUME, STAY) are handled correctly by the dead reckoning mechanism: the relative position does not change, but the visit count at the current position increases.

---

#### 2. Scenario

Agent is at $\hat{p}_t = (3, 2)$ with $w_t(3, 2) = 1$.

##### Action: CONSUME

$$
\Delta(\text{CONSUME}) = (0, 0)
$$

Regardless of $\mu_t$:

$$
\hat{p}_{t+1} = (3, 2) + \mu_t \cdot (0, 0) = (3, 2)
$$

$$
w_{t+1}(3, 2) = 1 + 1 = 2
$$

##### Next action: CONSUME again

$$
\hat{p}_{t+2} = (3, 2), \quad w_{t+2}(3, 2) = 3
$$

##### Next action: STAY

$$
\hat{p}_{t+3} = (3, 2), \quad w_{t+3}(3, 2) = 4
$$

---

#### 3. Effect on Novelty

After three stationary actions at $(3, 2)$:

$$
\nu^{spatial}_{current} = \frac{1}{1 + 4} = 0.200
$$

Meanwhile, neighbors that haven't been visited:

$$
\nu^{spatial}_{neighbor} = 1.000
$$

Novelty ratio: $\frac{1.000}{0.200} = 5.0$

---

#### 4. Conclusion

> Staying in place or consuming resources increases the visit count, which **reduces the spatial novelty of the current cell relative to unvisited neighbors**. This creates a natural pressure to move on after consuming. The curiosity drive doesn't just reward going to new places — it penalizes lingering. Combined with example D1 (forage-explore cycle), this shows the full mechanism: consume → visit count rises → curiosity pushes outward → explore.
