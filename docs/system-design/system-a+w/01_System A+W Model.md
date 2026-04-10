# System A+W: A Dual-Drive Mechanistic Agent with World Model

## Metadata
- Project: AXIS -- Complex Mechanistic Systems Experiment
- Author: Oliver Grau
- Type: Formal Research Note
- Status: Draft v1.0
- Scope: Dual-drive agent (hunger + curiosity) with spatial world model and dynamic drive arbitration
- Extends: System A Baseline
- Constraints: No self-model, no planning, no meta-cognition, no phenomenology

---

## 1. Objective

This document defines **System A+W** as an extension of the System A baseline agent.

System A+W preserves the full mechanistic architecture of System A while introducing:

- a **curiosity drive** as a second independent regulatory mechanism,
- a **spatial world model** (visit-count map) that tracks explored territory,
- **dynamic drive arbitration** that modulates the relative influence of hunger and curiosity,
- and the activation of **episodic memory for sensory novelty detection**.

The central research question is:

> What behavioral repertoire emerges when a second drive -- curiosity -- competes with hunger for control of action selection, modulated by a simple spatial world model?

---

### 1.1 Relationship to System A

System A+W is a strict superset of System A:

- When curiosity parameters are set to zero, System A+W reduces exactly to System A
- The action space is identical
- The sensor model is identical
- The energy dynamics and transition mechanics are identical
- The hunger drive is unchanged

The only additions are:

- a new drive module (curiosity)
- a new internal state component (visit counts)
- a drive aggregation layer with dynamic weights
- activation of memory for novelty computation

---

### 1.2 Biological Motivation

The dual-drive architecture is inspired by simple biological organisms:

- **Aplysia californica** (sea slug): exhibits habituation to familiar stimuli and orienting responses to novel stimuli, modulated by metabolic state
- **C. elegans**: balances food-seeking chemotaxis against exploratory dispersal depending on satiation level
- **Foraging theory**: the marginal value theorem predicts that well-fed organisms allocate more time to exploration; hungry organisms exploit known patches

The key biological principle:

> Homeostatic drives gate exploratory behavior. When metabolic need is high, exploration is suppressed. When metabolic need is low, curiosity dominates.

---

## 2. Design Principles

### 2.1 Inherited Principles
All design principles from System A (Baseline) Section 2 are inherited:

- Pure mechanism (no mental vocabulary)
- Modular drives
- Locality of perception
- Actions as intent, not outcome

### 2.2 New Principles

#### 2.2.1 Multiple Competing Drives
The system supports $n \geq 2$ independent drive modules. Drives produce independent action contributions and are combined through an explicit aggregation function.

#### 2.2.2 Drive Hierarchy
Homeostatic drives (hunger) take priority over epistemic drives (curiosity). This is enforced through the dynamic weight function, not through hard-coded priority rules.

#### 2.2.3 Minimal World Model
System A+W introduces a **spatial visit-count map** as a minimal world model. This map records only how often each position has been visited. It does not store:

- cell contents
- resource locations
- obstacle positions
- any predictive model

> The world model records presence, not perception.

#### 2.2.4 Memory Activation
Episodic memory, which exists but is behaviorally inactive in System A, is now used for sensory novelty computation. The memory itself is unchanged -- only its role expands.

---

## 3. Formal Definition

System A+W is defined as the 9-tuple

$$
A^{+W} = (\mathcal{X}, \mathcal{U}, \mathcal{M}, \mathcal{W}, \mathcal{A}, \mathcal{D}, F, \Gamma, \pi)
$$

where:

- $\mathcal{X}$ is the internal state space
- $\mathcal{U}$ is the sensory input space (unchanged from System A)
- $\mathcal{M}$ is the episodic perceptual memory space (unchanged from System A)
- $\mathcal{W}$ is the world model space (**new**)
- $\mathcal{A}$ is the action space (unchanged from System A)
- $\mathcal{D} = \{D_H, D_C\}$ is the drive space (extended with curiosity)
- $F$ is the state transition function (extended)
- $\Gamma$ is the action modulation system (extended with aggregation)
- $\pi$ is the policy (unchanged from System A)

---

## 4. Internal State

The internal state of the agent is extended to include the relative position estimate and the world model:

$$
x_t = (e_t, \xi_t, \hat{p}_t, w_t)
$$

where:

- $e_t \in [0, E_{\max}]$: internal energy level (unchanged)
- $\xi_t$: auxiliary internal variables (unchanged)
- $\hat{p}_t \in \mathbb{Z}^2$: relative position estimate (**new**)
- $w_t$: spatial world model state (**new**)

---

### 4.1 Spatial World Model

The world model is a visit-count map defined over a **relative coordinate frame**:

$$
w_t : \mathbb{Z}^2 \rightarrow \mathbb{N}_0
$$

where $w_t(\hat{p})$ records the number of times the agent has occupied relative position $\hat{p}$ up to and including time $t$.

**Important:** The world model uses *agent-relative* coordinates, not absolute world coordinates. The agent does not have access to its true position in the world. All spatial tracking is performed through dead reckoning (path integration).

---

#### 4.1.1 Relative Coordinate Frame

The agent maintains an internal position estimate $\hat{p}_t \in \mathbb{Z}^2$ defined relative to its starting position:

$$
\hat{p}_0 = (0, 0)
$$

This estimate is updated through **dead reckoning** — the agent integrates its own movement history without access to external positional information.

---

#### 4.1.2 Direction Delta Function

The mapping from movement actions to displacement vectors:

$$
\Delta(a) = \begin{cases}
(0, +1) & \text{if } a = \text{UP} \\
(0, -1) & \text{if } a = \text{DOWN} \\
(-1, 0) & \text{if } a = \text{LEFT} \\
(+1, 0) & \text{if } a = \text{RIGHT} \\
(0, 0) & \text{if } a \in \{\text{CONSUME}, \text{STAY}\}
\end{cases}
$$

---

#### 4.1.3 Dead Reckoning Update

After each action $a_t$, the agent receives a binary movement signal $\mu_t \in \{0, 1\}$ indicating whether displacement occurred:

$$
\hat{p}_{t+1} = \hat{p}_t + \mu_t \cdot \Delta(a_t)
$$

where:

- $\mu_t = 1$: the action resulted in movement (the agent displaced to a new cell)
- $\mu_t = 0$: the action did not result in movement (wall, boundary, obstacle, or non-movement action)

The movement signal $\mu_t$ is derived from the action outcome: the framework resolves the action against the world and reports whether displacement occurred. This is the **only** external feedback the world model consumes — no coordinates, no cell contents, no map data.

---

#### 4.1.4 Biological Analogy

This is **path integration** — the same navigation mechanism used by desert ants (*Cataglyphis fortis*), honeybees, and *C. elegans*. The agent integrates its own motor commands and their outcomes to maintain a spatial position estimate. It is an internal odometer, not a GPS.

Path integration is subject to cumulative drift in biological systems. In the discrete grid world, dead reckoning is **exact**: movement is always by one cell in a cardinal direction, and the success/failure signal is unambiguous. There is no noise, no slip, and no uncertainty in the outcome.

---

#### 4.1.5 Visit-Count Update

$$
w_{t+1}(\hat{p}) = \begin{cases} w_t(\hat{p}) + 1 & \text{if } \hat{p} = \hat{p}_{t+1} \\ w_t(\hat{p}) & \text{otherwise} \end{cases}
$$

The visit count at the agent's current (relative) position is incremented after every step, **including steps where the agent did not move**. If the agent bumps into a wall, it stays at $\hat{p}_t$ and the visit count there increases.

---

#### 4.1.6 Initial Condition

$$
w_0(\hat{p}) = \begin{cases} 1 & \text{if } \hat{p} = (0, 0) \\ 0 & \text{otherwise} \end{cases}
$$

The agent starts by recording that its origin has been visited once.

---

#### 4.1.7 Neighbor Lookup for Novelty Computation

During action selection (Section 5.2.4), the spatial novelty for each direction is computed using the relative coordinate frame:

$$
\nu^{spatial}_{dir} = \frac{1}{1 + w_t(\hat{p}_t + \Delta(dir))}
$$

This requires only the agent's current relative position $\hat{p}_t$ and the visit-count map $w_t$ — both are internal state components.

---

#### 4.1.8 World Model vs. Episodic Memory

The world model and episodic memory are distinct internal state components that serve different functions:

| Property | Episodic Memory ($m_t$) | World Model ($w_t$) |
|---|---|---|
| Content | Recent sensory observations | Cumulative visit counts |
| Structure | Bounded FIFO buffer (configurable capacity $k$) | Unbounded map (grows with exploration) |
| Updated from | Sensor output (what the agent *perceives*) | Motor output (where the agent *goes*) |
| Purpose | Sensory novelty detection | Spatial novelty detection |
| Persistence | Sliding window — old entries are overwritten | Permanent — no entry is ever removed |

Both contribute to the curiosity drive but through independent channels: episodic memory feeds the **sensory** novelty signal ($\nu^{sensory}$), while the world model feeds the **spatial** novelty signal ($\nu^{spatial}$). The composite novelty (Section 5.2.6) blends both channels.

---

#### 4.1.9 Design Constraint

The world model stores **only visit counts at relative positions**. It does not store:

- cell types or observations at positions
- resource values
- obstacle locations
- any data derived from the sensor

This prevents the world model from becoming a hidden spatial memory of environment content. It records *where the agent has been*, not *what it saw there*.

---

## 5. Drive System

System A+W defines two drives:

$$
\mathcal{D} = \{D_H, D_C\}
$$

where:

- $D_H$: hunger drive (unchanged from System A)
- $D_C$: curiosity drive (**new**)

---

### 5.1 Hunger Drive (Unchanged)

The hunger drive is identical to System A:

$$
d_H(t) = 1 - \frac{e_t}{E_{\max}}
$$

with:

- dependency only on $x_t$ (specifically $e_t$)
- no dependency on $u_t$, $m_t$, or $w_t$

All properties from System A Section 9 are inherited without modification.

---

### 5.2 Curiosity Drive

The curiosity drive represents an internal pressure toward novel experience. It is derived from a composite of two novelty signals:

- **Spatial novelty**: derived from the world model $w_t$
- **Sensory novelty**: derived from episodic memory $m_t$

---

#### 5.2.1 Curiosity Definition

The curiosity drive activation is defined as:

$$
d_C(t) = \mu_C \cdot (1 - \bar{\nu}_t)
$$

where:

- $\mu_C \in [0, 1]$: base curiosity level (configurable parameter)
- $\bar{\nu}_t$: mean novelty saturation signal

---

#### 5.2.2 Novelty Saturation

The novelty saturation $\bar{\nu}_t$ measures how much novel experience the agent has recently encountered. When the agent has been seeing diverse, novel observations, $\bar{\nu}_t$ is high and curiosity decreases slightly (temporary satiation of the curiosity drive).

$$
\bar{\nu}_t = \frac{1}{|m_t|} \sum_{j=1}^{|m_t|} \sigma_j
$$

where $\sigma_j$ is the sensory surprise of the $j$-th memory entry (defined in Section 5.2.5).

When memory is empty, $\bar{\nu}_t = 0$ and curiosity is at maximum.

---

#### 5.2.3 Interpretation

- $d_C(t) \approx \mu_C$: the agent has been in familiar territory -- curiosity is high
- $d_C(t) \approx 0$: the agent has recently encountered much novelty -- curiosity is temporarily sated

> Curiosity represents the drive to seek novel experience. It is high when the environment has been monotonous.

---

#### 5.2.4 Spatial Novelty Function

For each neighboring direction, the spatial novelty is:

$$
\nu^{spatial}_{dir} = \frac{1}{1 + w_t(\hat{p}_t + \Delta(dir))}
$$

where $\hat{p}_t$ is the agent's current relative position and $\Delta(dir)$ is the direction delta function (Section 4.1.2).

- Unvisited cell ($w_t = 0$): $\nu^{spatial} = 1.0$
- Visited once ($w_t = 1$): $\nu^{spatial} = 0.5$
- Visited $n$ times: $\nu^{spatial} = \frac{1}{1+n}$

The function decays hyperbolically, ensuring novelty is always positive but diminishes with repeated visits.

---

#### 5.2.5 Sensory Novelty Function

For each neighboring direction, the sensory novelty is derived by comparing the current observation with the mean observation stored in memory:

$$
\nu^{sensory}_{dir} = \left| r_{dir}(t) - \bar{r}_{dir} \right|
$$

where:

- $r_{dir}(t)$: currently observed resource intensity in direction $dir$
- $\bar{r}_{dir}$: mean resource intensity in direction $dir$ across all memory entries

$$
\bar{r}_{dir} = \frac{1}{|m_t|} \sum_{j=1}^{|m_t|} r_{dir}^{(j)}
$$

When memory is empty, $\bar{r}_{dir} = 0$, and sensory novelty equals the raw observation.

---

#### Interpretation

- High sensory novelty: the observed resource pattern differs from recent experience -- the environment has changed or the agent has reached a new area
- Low sensory novelty: the observation matches recent memory -- the agent is in a familiar, stable region

---

#### 5.2.6 Composite Novelty Signal

The per-direction novelty signal combines spatial and sensory components:

$$
\nu_{dir} = \alpha \cdot \nu^{spatial}_{dir} + (1 - \alpha) \cdot \nu^{sensory}_{dir}
$$

where:

- $\alpha \in [0, 1]$: spatial-sensory balance parameter (configurable)
- $\alpha = 1$: pure spatial novelty (visit-count only)
- $\alpha = 0$: pure sensory novelty (observation-difference only)
- $\alpha = 0.5$: equal weighting (default)

---

## 6. Action Modulation System

### 6.1 General Multi-Drive Formulation

System A (Baseline) Section 11.2 defines the general multi-drive modulation:

$$
\psi(a) = \psi_0(a) + \sum_{i} d_i(t) \cdot \phi_i(a, u_t, m_t)
$$

System A+W extends this with **dynamic drive weights**:

$$
\psi(a) = \psi_0(a) + w_H(t) \cdot d_H(t) \cdot \phi_H(a, u_t) + w_C(t) \cdot d_C(t) \cdot \phi_C(a, u_t, m_t, w_t)
$$

where:

- $w_H(t)$: dynamic hunger weight
- $w_C(t)$: dynamic curiosity weight
- $\phi_H$: hunger modulation function (unchanged from System A)
- $\phi_C$: curiosity modulation function (**new**)

---

### 6.2 Hunger Modulation Function (Unchanged)

Identical to System A Section 11.4:

$$
\phi_H(\text{UP}, u_t) = r_{up}(t)
$$

$$
\phi_H(\text{DOWN}, u_t) = r_{down}(t)
$$

$$
\phi_H(\text{LEFT}, u_t) = r_{left}(t)
$$

$$
\phi_H(\text{RIGHT}, u_t) = r_{right}(t)
$$

$$
\phi_H(\text{CONSUME}, u_t) = w_{consume} \cdot r_c(t)
$$

$$
\phi_H(\text{STAY}, u_t) = -\lambda_{stay}
$$

---

### 6.3 Curiosity Modulation Function

The curiosity drive modulates action preferences using the composite novelty signal:

---

#### Movement Actions

$$
\phi_C(\text{UP}, u_t, m_t, w_t) = \nu_{up}
$$

$$
\phi_C(\text{DOWN}, u_t, m_t, w_t) = \nu_{down}
$$

$$
\phi_C(\text{LEFT}, u_t, m_t, w_t) = \nu_{left}
$$

$$
\phi_C(\text{RIGHT}, u_t, m_t, w_t) = \nu_{right}
$$

where $\nu_{dir}$ is the composite novelty signal defined in Section 5.2.6.

---

#### Interpretation

- High novelty in a direction increases the preference for movement in that direction
- The agent is drawn toward unexplored areas (spatial) and areas where the environment has changed (sensory)

---

#### Consumption and Stay Actions

$$
\phi_C(\text{CONSUME}, u_t, m_t, w_t) = -\lambda_{explore}
$$

$$
\phi_C(\text{STAY}, u_t, m_t, w_t) = -\lambda_{explore}
$$

where $\lambda_{explore} \geq 0$ is a configurable parameter.

---

#### Interpretation

Curiosity actively suppresses stationary and consumptive behavior:

- A curious agent prefers to **move** rather than consume or stay
- This creates a tension with hunger, which prefers consumption when resources are present

> The suppression of CONSUME by curiosity is the primary source of hunger-curiosity competition.

---

### 6.4 Dynamic Drive Weights

The relative influence of each drive is controlled by weight functions that depend on the hunger activation:

$$
w_H(t) = w_H^{base} + (1 - w_H^{base}) \cdot d_H(t)^{\gamma}
$$

$$
w_C(t) = w_C^{base} \cdot (1 - d_H(t))^{\gamma}
$$

where:

- $w_H^{base} \in (0, 1]$: minimum hunger weight (hunger always has some influence)
- $w_C^{base} > 0$: maximum curiosity weight when fully sated
- $\gamma > 0$: gating sharpness parameter
- $d_H(t)$: hunger drive activation

---

#### Properties

The weight functions satisfy the following properties:

1. **Hunger floor**: $w_H(t) \geq w_H^{base} > 0$ for all $t$. Hunger always contributes.

2. **Curiosity ceiling**: $w_C(t) \leq w_C^{base}$ with equality only when $d_H(t) = 0$ (fully sated).

3. **Curiosity suppression**: $w_C(t) \rightarrow 0$ as $d_H(t) \rightarrow 1$ (starving). When hungry, curiosity is silenced.

4. **Monotonicity**: $w_H(t)$ is monotonically increasing in $d_H(t)$. $w_C(t)$ is monotonically decreasing in $d_H(t)$.

5. **Sharpness control**: $\gamma$ controls the transition. For $\gamma = 1$, the transition is linear. For $\gamma > 1$, the transition is sharper (curiosity persists longer at moderate hunger, then drops rapidly). For $\gamma < 1$, the transition is more gradual.

---

#### Behavioral Regimes

| Energy level | $d_H$ | $w_H$ | $w_C$ | Dominant behavior |
|---|---|---|---|---|
| $e_t = E_{\max}$ | 0.0 | $w_H^{base}$ | $w_C^{base}$ | Exploration-dominant |
| $e_t = 0.7 \cdot E_{\max}$ | 0.3 | $w_H^{base} + (1 - w_H^{base}) \cdot 0.3^{\gamma}$ | $w_C^{base} \cdot 0.7^{\gamma}$ | Balanced |
| $e_t = 0.3 \cdot E_{\max}$ | 0.7 | $w_H^{base} + (1 - w_H^{base}) \cdot 0.7^{\gamma}$ | $w_C^{base} \cdot 0.3^{\gamma}$ | Hunger-dominant |
| $e_t \approx 0$ | $\approx 1.0$ | $\approx 1.0$ | $\approx 0$ | Pure survival |

---

### 6.5 Final Action Score

Given $\psi_0(a) = 0$, the final modulated action score is:

$$
\psi(a) = w_H(t) \cdot d_H(t) \cdot \phi_H(a, u_t) + w_C(t) \cdot d_C(t) \cdot \phi_C(a, u_t, m_t, w_t)
$$

This score is passed to the policy for action selection.

---

### 6.6 Admissibility Masking

Identical to System A: movement actions toward non-traversable cells receive $\psi(a) = -\infty$ and probability 0 in the softmax.

---

## 7. Policy

The policy is **unchanged** from System A Section 12.

$$
P(a \mid x_t, u_t, m_t) = \frac{\exp\left(\beta \cdot \psi(a)\right)}{\sum_{a'} \exp\left(\beta \cdot \psi(a')\right)}
$$

The policy does not know that the action scores originate from multiple drives. It receives a single combined score per action and applies softmax selection.

---

## 8. State Transition

The state transition is extended to update the relative position and world model:

$$
x_{t+1} = F_{agent}(x_t, u_t, a_t, \mu_t)
$$

where $\mu_t \in \{0, 1\}$ is the movement signal (whether displacement occurred).

The transition consists of five phases (extending System A Section 13):

1. **Energy update** (unchanged):
$$
e_{t+1} = \mathrm{clip}(e_t - c(a_t) + \kappa \cdot \Delta R_t^{cons},\ 0,\ E_{\max})
$$

2. **Memory update** (unchanged):
$$
m_{t+1} = M(m_t, u_{t+1})
$$

3. **Dead reckoning update** (**new**):
$$
\hat{p}_{t+1} = \hat{p}_t + \mu_t \cdot \Delta(a_t)
$$

4. **World model update** (**new**):
$$
w_{t+1}(\hat{p}) = \begin{cases} w_t(\hat{p}) + 1 & \text{if } \hat{p} = \hat{p}_{t+1} \\ w_t(\hat{p}) & \text{otherwise} \end{cases}
$$

5. **Termination check** (unchanged):
$$
\text{terminated} = (e_{t+1} \leq 0)
$$

---

## 9. Execution Cycle

The execution cycle extends System A Section 14:

1. **Perception**: $u_t = S(s_t^{world})$
2. **Drive evaluation**: compute $d_H(t)$ and $d_C(t)$
3. **Drive arbitration**: compute $w_H(t)$ and $w_C(t)$
4. **Action modulation**: compute $\psi(a)$ for all $a \in \mathcal{A}$
5. **Admissibility masking**: set $\psi(a) = -\infty$ for blocked directions
6. **Action selection**: sample $a_t \sim \pi(\cdot \mid x_t, u_t, m_t)$
7. **State transition**: update $e_{t+1}$, $m_{t+1}$, $\hat{p}_{t+1}$, $w_{t+1}$
8. **Termination check**: evaluate stopping criteria

---

## 10. Emergent Behavioral Regimes

### 10.1 Exploration Phase (Well-Fed)

When $e_t \approx E_{\max}$:

- $d_H \approx 0$: hunger is inactive
- $w_H \approx w_H^{base}$: minimal hunger influence
- $w_C \approx w_C^{base}$: maximal curiosity influence
- Movement toward unvisited cells is strongly preferred
- CONSUME and STAY are suppressed by curiosity

The agent exhibits **systematic exploration** of the environment.

---

### 10.2 Balanced Foraging (Moderate Energy)

When $e_t \approx 0.5 \cdot E_{\max}$:

- Both drives are active with comparable weights
- The agent moves toward areas that are both novel *and* resource-rich
- CONSUME is available when resources are present, but movement remains competitive

The agent exhibits **opportunistic foraging with exploratory bias**.

---

### 10.3 Urgent Foraging (Low Energy)

When $e_t \ll E_{\max}$:

- $d_H \approx 1$: hunger dominates
- $w_C \approx 0$: curiosity is effectively silenced
- Behavior converges to System A baseline: resource-seeking and consumption

The agent exhibits **pure survival behavior**, identical to System A.

---

### 10.4 Novelty-Seeking Return

An important emergent behavior: after consuming a resource and gaining energy, $d_H$ drops, $w_C$ increases, and the agent resumes exploration. This creates a natural **forage-explore cycle**.

---

## 11. Configuration Parameters

### 11.1 Inherited from System A

| Parameter | Symbol | Domain | Description |
|---|---|---|---|
| Max energy | $E_{\max}$ | $\mathbb{R}^+$ | Energy ceiling |
| Initial energy | $e_0$ | $[0, E_{\max}]$ | Starting energy |
| Memory capacity | $k$ | $\mathbb{N}^+$ | FIFO buffer size |
| Consume weight | $w_{consume}$ | $\mathbb{R}^+$ | Current-cell resource priority |
| Stay suppression | $\lambda_{stay}$ | $\mathbb{R}_{\geq 0}$ | Hunger-driven STAY penalty |
| Move cost | $c_{move}$ | $\mathbb{R}^+$ | Energy cost per movement |
| Consume cost | $c_{consume}$ | $\mathbb{R}^+$ | Energy cost per consume |
| Stay cost | $c_{stay}$ | $\mathbb{R}^+$ | Energy cost per stay |
| Max consume | $\Delta R_{\max}$ | $[0, 1]$ | Max resource per consume |
| Energy gain factor | $\kappa$ | $\mathbb{R}^+$ | Resource-to-energy conversion |
| Temperature | $\beta^{-1}$ | $\mathbb{R}^+$ | Policy stochasticity |
| Selection mode | -- | $\{sample, argmax\}$ | Policy mode |

### 11.2 New Parameters

| Parameter | Symbol | Domain | Default | Description |
|---|---|---|---|---|
| Base curiosity | $\mu_C$ | $[0, 1]$ | 1.0 | Maximum curiosity activation |
| Spatial-sensory balance | $\alpha$ | $[0, 1]$ | 0.5 | Weighting of spatial vs sensory novelty |
| Explore suppression | $\lambda_{explore}$ | $\mathbb{R}_{\geq 0}$ | 0.3 | Curiosity penalty on CONSUME and STAY |
| Hunger weight base | $w_H^{base}$ | $(0, 1]$ | 0.3 | Minimum hunger influence |
| Curiosity weight base | $w_C^{base}$ | $\mathbb{R}^+$ | 1.0 | Maximum curiosity influence |
| Gating sharpness | $\gamma$ | $\mathbb{R}^+$ | 2.0 | Hunger-curiosity transition sharpness |

---

## 12. Reduction to System A

When the following conditions hold:

- $\mu_C = 0$ (no curiosity)
- or $w_C^{base} = 0$ (zero curiosity weight)

then:

- $d_C(t) = 0$ or $w_C(t) = 0$ for all $t$
- $\psi(a) = w_H(t) \cdot d_H(t) \cdot \phi_H(a, u_t)$
- The world model $w_t$ is updated but never read
- Behavior is identical to System A (up to the constant factor $w_H(t)$ which only scales the softmax logits and does not affect relative probabilities when $w_H$ is constant)

---

## 13. Validation Criteria

### 13.1 Structural Consistency

- [ ] All drive outputs are scalar-valued
- [ ] All modulation functions depend only on permitted inputs ($u_t$, $m_t$, $w_t$, $x_t$)
- [ ] No drive has access to true world state $s_t^{world}$
- [ ] Action scores are well-defined for all actions and all states
- [ ] Dynamic weights are non-negative for all $d_H(t) \in [0, 1]$

### 13.2 Behavioral Validation

- [ ] At $e_t = E_{\max}$: exploration behavior dominates (movement probability > consume probability in resource-free areas)
- [ ] At $e_t \approx 0$: behavior converges to System A baseline (hunger-dominated)
- [ ] Forage-explore cycle emerges: agent alternates between resource-seeking and exploration
- [ ] Visit counts increase coverage over time (the agent does not remain in a small area when well-fed)

### 13.3 Reduction Validation

- [ ] With $\mu_C = 0$: all action probabilities match System A baseline exactly
- [ ] With $\alpha = 1$: no dependence on memory for curiosity (pure spatial)
- [ ] With $\alpha = 0$: no dependence on visit counts for curiosity (pure sensory)

---

## 14. Summary

System A+W extends the System A baseline with a minimal but meaningful addition: a curiosity drive modulated by a spatial world model. The architecture preserves all mechanistic constraints of the original system while introducing a second source of behavioral regulation.

The core innovation is the **dynamic drive weight function** that implements a biologically-motivated hierarchy:

> Hunger gates curiosity. The drive to explore exists only in the space left by the drive to survive.

This creates a natural behavioral cycle:

1. Well-fed agent explores and builds its world model
2. Energy decreases → curiosity fades → hunger takes over
3. Agent seeks and consumes resources
4. Energy restored → curiosity re-emerges → return to step 1

The model is fully deterministic given its inputs, fully interpretable, and introduces no hidden knowledge about the environment beyond the minimal visit-count map.
