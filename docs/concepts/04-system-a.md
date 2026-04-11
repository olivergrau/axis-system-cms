# System A: The Hunger-Driven Forager

**AXIS Conceptual Series -- Document 4 of 5**

> **Reading order:**
> [1. AXIS Vision](01-axis-cms-vision.md) |
> [2. Math as Modeling](02-math-as-modeling.md) |
> [3. Agent Framework](03-agent-framework.md) |
> **4. System A** |
> [5. System A+W](05-system-aw.md)
>
> **Formal specification:** [System A Baseline](../system-design/system-a/01_System%20A%20Baseline.md) |
> [Worked Examples](../system-design/system-a/02_System%20A%20Baseline%20Worked%20Examples.md)

---

## 1. What Is System A?

System A is the simplest non-trivial agent in the AXIS framework.
It is a single-drive, memoryless (in the functional sense) forager
that navigates a grid world, consuming resources to sustain its
energy. When energy reaches zero, the agent dies.

System A answers a foundational question: *What is the minimal
mechanism that produces recognizable foraging behavior?*

The answer turns out to be surprisingly small:

- One sensory function (5-cell neighborhood)
- One drive (hunger)
- One action modulation function
- One policy (softmax)
- One energy model (cost + gain)

From these five components, the agent exhibits recognizable
behaviors: pursuing food, consuming when atop a resource, avoiding
obstacles, and progressively shifting from idle movement to urgent
foraging as energy depletes. None of these behaviors are programmed
as rules. They emerge from the interaction of the mathematical
components.

---

## 2. Formal Definition

System A instantiates the generic 8-tuple with specific choices:

$$A = (\mathcal{X},\ \mathcal{U},\ \mathcal{M},\ \mathcal{A},\ \{D_H\},\ F,\ \Gamma,\ \pi)$$

| Component | System A Instantiation |
|---|---|
| $\mathcal{X}$ | $(e_t, m_t)$ -- energy + observation buffer |
| $\mathcal{U}$ | $\mathbb{R}^{10}$ -- Von Neumann neighborhood |
| $\mathcal{M}$ | Bounded FIFO of observations (passive in baseline) |
| $\mathcal{A}$ | $\{\text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}, \text{CONSUME}, \text{STAY}\}$ |
| $\mathcal{D}$ | $\{D_H\}$ -- hunger drive only |
| $F$ | Energy transition with action costs and consumption gains |
| $\Gamma$ | Single-drive modulation: $\psi(a) = d_H \cdot \phi_H(a, u_t)$ |
| $\pi$ | Softmax with admissibility masking |

Key simplifications relative to the generic framework:

- **Single drive.** Only hunger; no drive weight arbitration needed
  since there is nothing to arbitrate.
- **No world model.** The agent does not track its position or
  spatial history.
- **Passive memory.** The observation buffer is updated each step
  but not read by the hunger drive. It exists as a scaffold for
  System A+W.

---

## 3. The Observation Model

### 3.1 Sensor Function

The sensor reads the agent's immediate Von Neumann neighborhood:
the current cell and the four cardinal neighbors.

For each cell $j$ in the neighborhood, the sensor extracts two
signals:

$$z_j = (b_j, r_j)$$

where:

- $b_j \in \{0, 1\}$ is the **traversability** signal.
  $b_j = 0$ for obstacles and out-of-bounds positions,
  $b_j = 1$ otherwise.

- $r_j \in [0, 1]$ is the **resource intensity** signal.
  For the implementation, $r_j$ equals the cell's raw resource value.
  In the formal model, resource values can be scaled by
  $R_{\text{scale}}$: $r_j = R_j / R_{\text{scale}}$.

### 3.2 Observation Vector

The full observation is the concatenation of five cell observations
in a fixed order:

$$u_t = (b_c, r_c, b_{\uparrow}, r_{\uparrow}, b_{\downarrow}, r_{\downarrow}, b_{\leftarrow}, r_{\leftarrow}, b_{\rightarrow}, r_{\rightarrow}) \in \mathbb{R}^{10}$$

| Component | Index | Source Cell |
|---|---|---|
| $b_c, r_c$ | 0, 1 | Current (agent position) |
| $b_{\uparrow}, r_{\uparrow}$ | 2, 3 | Up neighbor ($y - 1$) |
| $b_{\downarrow}, r_{\downarrow}$ | 4, 5 | Down neighbor ($y + 1$) |
| $b_{\leftarrow}, r_{\leftarrow}$ | 6, 7 | Left neighbor ($x - 1$) |
| $b_{\rightarrow}, r_{\rightarrow}$ | 8, 9 | Right neighbor ($x + 1$) |

### 3.3 Partial Observability

The agent perceives only its immediate neighborhood. It cannot see:

- Cells beyond one step away
- Its own absolute position
- The global resource distribution
- Other potential agents (multi-agent extensions)

This radical locality is a deliberate constraint. It creates
meaningful uncertainty: the agent must decide which direction to
move without knowing what lies beyond its visible horizon.

---

## 4. The Hunger Drive

### 4.1 Activation

The hunger drive measures the deficit between current energy and
maximum capacity:

$$d_H(t) = \text{clip}\!\left(1 - \frac{e_t}{E_{\max}},\ 0,\ 1\right)$$

This is a linear function of energy:

| Energy Level | Hunger Activation | Interpretation |
|---|---|---|
| $e_t = E_{\max}$ | $d_H = 0$ | Fully sated, no hunger |
| $e_t = E_{\max} / 2$ | $d_H = 0.5$ | Moderate hunger |
| $e_t = 0$ | $d_H = 1$ | Maximum hunger (about to die) |

The drive is **purely internal**: it depends only on the agent's
energy level, not on what it observes. A well-fed agent in a
food-rich environment has low hunger ($d_H \approx 0$). A starving
agent in a barren environment has high hunger ($d_H \approx 1$).
The observation determines *where* food is; the drive determines
*how much* the agent cares about it.

### 4.2 Modulation Function

The hunger drive translates its activation into per-action scores
through the modulation function $\phi_H$. Each action receives a
score based on the resource availability it can access:

**Movement actions** (UP, DOWN, LEFT, RIGHT):

$$\phi_H(\text{DIR}, u_t) = r_{\text{dir}}(t)$$

The score for moving in a direction equals the resource intensity
of the cell in that direction. Moving toward food scores higher
than moving toward empty cells. Moving toward obstacles scores
zero (the resource of an obstacle cell is always zero).

**Consume action:**

$$\phi_H(\text{CONSUME}, u_t) = w_{\text{consume}} \cdot r_c(t)$$

The score for consuming is proportional to the resource at the
current cell, amplified by the **consumption priority weight**
$w_{\text{consume}} > 1$. This multiplier ensures that, all else
being equal, consuming from a rich cell scores higher than moving
toward one.

The rationale: an agent standing on food should prefer to consume
it rather than walking toward food elsewhere. The weight
$w_{\text{consume}}$ quantifies this preference.

**Stay action:**

$$\phi_H(\text{STAY}, u_t) = -\lambda_{\text{stay}}$$

The score for staying is always negative: $-\lambda_{\text{stay}} \cdot d_H(t)$
(the $d_H$ factor comes from the full modulation equation below).
Staying is costly because the agent spends energy without gaining
any. The hungrier the agent, the more staying is penalized.

### 4.3 Full Action Score

Combining activation and modulation, the full action score is:

$$\psi(a) = d_H(t) \cdot \phi_H(a, u_t)$$

Expanding for each action type:

$$\psi(\text{DIR}) = d_H(t) \cdot r_{\text{dir}}(t)$$

$$\psi(\text{CONSUME}) = d_H(t) \cdot w_{\text{consume}} \cdot r_c(t)$$

$$\psi(\text{STAY}) = -\lambda_{\text{stay}} \cdot d_H(t)$$

The key insight: **the hunger activation $d_H$ scales all scores**.
When the agent is fully fed ($d_H = 0$), all scores are zero and
the softmax produces a near-uniform distribution -- the agent
wanders randomly. As the agent gets hungrier ($d_H \to 1$), the
scores spread apart, and the policy increasingly concentrates
probability on the best action.

This is not a programmed rule. It is a mathematical consequence of
multiplying every modulation function by $d_H$: the drive's
activation acts as a global gain on action differentiation.

---

## 5. The Policy

### 5.1 Admissibility Masking

Before computing probabilities, inadmissible actions are eliminated:

$$M(a) = \begin{cases}
b_{\text{dir}} > 0 & \text{for movement actions (traversability of target cell)} \\
1 & \text{for CONSUME and STAY (always admissible)}
\end{cases}$$

Masked scores:

$$\tilde{\psi}(a) = \begin{cases}
\psi(a) & \text{if } M(a) = 1 \\
-\infty & \text{otherwise}
\end{cases}$$

### 5.2 Softmax Selection

$$P(a \mid x_t, u_t) = \frac{\exp(\beta \cdot \tilde{\psi}(a))}{\sum_{a' \in \mathcal{A}} \exp(\beta \cdot \tilde{\psi}(a'))}$$

where $\beta = 1 / T$ is the inverse temperature.

### 5.3 Behavioral Examples

**Scenario: High hunger, food under agent**

$d_H = 0.9$, $r_c = 0.8$, $w_{\text{consume}} = 3.0$:

$$\psi(\text{CONSUME}) = 0.9 \times 3.0 \times 0.8 = 2.16$$

If neighboring resources are all $\leq 0.5$:

$$\psi(\text{DIR}) = 0.9 \times 0.5 = 0.45 \quad \text{(at most)}$$

With $\beta = 1$: CONSUME probability will dominate. The agent
strongly prefers to eat.

**Scenario: Low hunger, no nearby food**

$d_H = 0.1$, all $r_j \approx 0$:

$$\psi(a) \approx 0 \quad \forall a \quad (\text{except STAY} \approx -0.01)$$

The softmax produces a near-uniform distribution. The agent
wanders randomly. There is no food to pursue and no urgency to
forage.

**Scenario: Corner position (two walls)**

$b_{\uparrow} = 0$, $b_{\leftarrow} = 0$: UP and LEFT are masked.

The softmax sum excludes these directions. Probability
redistributes across DOWN, RIGHT, CONSUME, STAY.

---

## 6. Episodic Perceptual Memory

### 6.1 Structure

The observation buffer stores the $k$ most recent observations
as a FIFO (first-in, first-out) ring buffer:

$$m_t = (e_1, e_2, \ldots, e_{|m_t|}) \quad \text{where } |m_t| \leq k$$

Each entry $e_i$ is a pair (timestep, observation). The buffer
starts empty and fills over the first $k$ steps.

### 6.2 Update Rule

$$m_{t+1} = G_{\text{mem}}(m_t, u_{t+1}) = \begin{cases}
m_t \oplus (t+1, u_{t+1}) & \text{if } |m_t| < k \\
\text{tail}(m_t) \oplus (t+1, u_{t+1}) & \text{if } |m_t| = k
\end{cases}$$

where $\oplus$ denotes append and $\text{tail}$ drops the oldest
entry.

### 6.3 Role in System A

In the baseline, the buffer is **passive**. It is updated each
step but no drive reads from it. The hunger drive's modulation
function $\phi_H$ depends only on the current observation $u_t$,
not on the memory $m_t$.

The buffer exists as a structural scaffold. In System A+W, the
curiosity drive reads from it to compute sensory novelty.

---

## 7. The Consume Action

System A extends the base action space with a custom action:
**CONSUME**. This is the mechanism by which the agent extracts
resources from the world and converts them to energy.

### 7.1 Handler

The consume handler operates on the mutable world:

1. Read the resource value $R_c$ at the agent's current
   cell $c$.
2. Extract $\Delta R^{\text{cons}} = \min(R_c, c_{\max})$, up to
   the per-step maximum.
3. Reduce the cell's resource by $\Delta R^{\text{cons}}$. If
   fully depleted, the cell becomes empty.
4. Return the extracted amount in the action outcome.

### 7.2 Design Rationale

CONSUME is separate from movement because it creates a **behavioral
trade-off**: consuming costs a timestep that could be spent moving
toward richer resources. The agent must "decide" (through the
mathematics of drive + modulation + policy) whether to eat here or
search elsewhere.

This trade-off does not need to be programmed. It emerges from the
action scores. When $\psi(\text{CONSUME})$ exceeds
$\psi(\text{DIR})$ for all directions, the agent consumes. When a
neighbor has higher resource than the current cell (and hunger
magnifies the difference), the agent moves.

---

## 8. State Transition

### 8.1 Energy Dynamics

The energy update is:

$$e_{t+1} = \text{clip}\!\bigl(e_t - c(a_t) + \kappa \cdot \Delta R_t^{\text{cons}},\ 0,\ E_{\max}\bigr)$$

where:

- $c(a_t)$ is the **action cost** (depends on action type)
- $\kappa$ is the **energy gain factor** (resource-to-energy
  conversion)
- $\Delta R_t^{\text{cons}}$ is the resource consumed at this
  step (zero for all actions except CONSUME)

### 8.2 Action Costs

| Action | Cost Symbol | Description |
|---|---|---|
| UP, DOWN, LEFT, RIGHT | $c_{\text{move}}$ | Movement energy expenditure |
| CONSUME | $c_{\text{consume}}$ | Metabolic cost of consumption |
| STAY | $c_{\text{stay}}$ | Basal metabolic cost |

Costs are configurable parameters, with typical values: $c_{\text{move}} = 1.0$, $c_{\text{consume}} = 0.5$, $c_{\text{stay}} = 0.5$.

### 8.3 Energy Gain

Energy gain occurs only through consumption:

$$\text{gain} = \kappa \cdot \Delta R_t^{\text{cons}}$$

The gain factor $\kappa$ controls how efficiently the agent converts
environmental resources into energy. With $\kappa = 20$ and
$\Delta R = 0.5$, the agent gains 10 energy units.

### 8.4 Worked Example

Initial state: $e_0 = 50$, $E_{\max} = 100$.

| Step | Action | Cost | Gain | $e_{t+1}$ | $d_H$ |
|---|---|---|---|---|---|
| 0 | RIGHT | 1.0 | 0 | 49.0 | 0.51 |
| 1 | RIGHT | 1.0 | 0 | 48.0 | 0.52 |
| 2 | CONSUME | 0.5 | 10.0 | 57.5 | 0.425 |
| 3 | DOWN | 1.0 | 0 | 56.5 | 0.435 |
| 4 | CONSUME | 0.5 | 16.0 | 72.0 | 0.28 |

After consuming at step 2, the agent gains 10 energy, reducing
hunger from 0.52 to 0.425. The reduced hunger means the drive
modulation decreases, making the agent less focused on food --
a natural "satiation" effect, emergent from the math.

### 8.5 Terminal Condition

$$e_{t+1} \leq 0 \implies \text{episode terminates with "energy\_depleted"}$$

Energy is clipped to zero, not allowed to go negative. Once the
agent has zero energy, it is dead.

### 8.6 Starvation Dynamics

Under complete food absence ($r_j = 0$ for all cells), the agent
loses energy at a rate determined by the probability distribution
over actions. In the simplest case (all cells empty, all
traversable, no food), the expected energy loss per step is:

$$\mathbb{E}[\text{cost}] = P(\text{move}) \cdot c_{\text{move}} + P(\text{CONSUME}) \cdot c_{\text{consume}} + P(\text{STAY}) \cdot c_{\text{stay}}$$

With uniform action probabilities (low hunger), this averages the
costs. As hunger increases, the distribution shifts but the
expected cost remains bounded. The deterministic starvation time
from full energy with movement-only behavior is:

$$n_{\text{death}} = \left\lceil \frac{e_0}{c_{\text{move}}} \right\rceil$$

---

## 9. Behavioral Regimes

System A exhibits three recognizable behavioral regimes that emerge
from the mathematics, not from explicit programming:

### 9.1 Exploration (Low Hunger)

When $d_H \approx 0$ (energy is high):

- All action scores $\psi(a) \approx 0$
- Softmax produces near-uniform distribution
- Agent moves essentially randomly
- No preference for food-bearing cells

This is "sated wandering" -- the biological equivalent of an
organism that has recently eaten and moves without urgency.

### 9.2 Directed Foraging (Moderate Hunger)

When $0.3 \leq d_H \leq 0.7$:

- Scores differentiate based on resource values
- Agent probabilistically prefers directions with higher resources
- CONSUME is preferred when standing on food
- STAY is suppressed

The agent begins to exhibit goal-directed behavior, favoring
food-bearing cells. The temperature parameter $\beta$ controls
how sharply: low $\beta$ maintains diversity; high $\beta$
concentrates on the best action.

### 9.3 Desperate Foraging (High Hunger)

When $d_H \to 1$ (energy near zero):

- Scores are strongly scaled by $d_H \approx 1$
- CONSUME dominates whenever current resource > 0
- Movement toward food is strongly preferred
- $\psi(\text{STAY})$ is strongly negative

The agent's behavior becomes nearly deterministic: consume if
possible, otherwise move toward the highest-resource neighbor.
This is "starvation mode" -- the organism is fighting for survival.

### 9.4 The Continuum

These regimes are not discrete states with transition points.
They are points on a continuum parameterized by $d_H(t)$.
The softmax policy produces a smooth, continuous change in
behavior as energy changes. There are no if-then rules, no
mode switches, no thresholds. The agent's entire behavioral
repertoire is encoded in the interaction between the linear
drive activation $d_H$, the observation-dependent modulation
$\phi_H$, and the softmax policy.

---

## 10. Configuration Parameters

The complete parameter set for System A:

| Parameter | Symbol | Domain | Role |
|---|---|---|---|
| Initial energy | $e_0$ | $(0, E_{\max}]$ | Starting energy |
| Maximum energy | $E_{\max}$ | $\mathbb{R}^+$ | Energy capacity |
| Buffer capacity | $k$ | $\mathbb{Z}^+$ | Observation buffer size |
| Temperature | $T$ ($\beta = 1/T$) | $\mathbb{R}^+$ | Policy stochasticity |
| Selection mode | -- | $\{\text{sample}, \text{argmax}\}$ | Deterministic or stochastic |
| Stay suppression | $\lambda_{\text{stay}}$ | $\mathbb{R}_0^+$ | Penalty for idling |
| Consume weight | $w_{\text{consume}}$ | $\mathbb{R}^+$ (typically > 1) | Consumption priority |
| Move cost | $c_{\text{move}}$ | $\mathbb{R}^+$ | Energy per movement |
| Consume cost | $c_{\text{consume}}$ | $\mathbb{R}^+$ | Energy per consumption |
| Stay cost | $c_{\text{stay}}$ | $\mathbb{R}_0^+$ | Basal metabolic cost |
| Max consume | $c_{\max}$ | $\mathbb{R}^+$ | Resource cap per consume |
| Energy gain factor | $\kappa$ | $\mathbb{R}_0^+$ | Resource-to-energy ratio |

These 12 parameters fully determine the agent's behavior. No hidden
state, no learned parameters, no emergent complexity beyond what
the equations produce.

---

## 11. Validation Criteria

System A's correctness is validated through 10 criteria from the
formal specification:

1. **Energy conservation.** $e_{t+1} = \text{clip}(e_t - c(a_t) + \kappa \cdot \Delta R)$ at every step.
2. **Admissibility.** The agent never selects an inadmissible action ($P(a) = 0$ for masked actions).
3. **Hunger monotonicity.** $d_H$ increases as $e$ decreases, linearly.
4. **Score sensitivity.** Higher neighbor resource $\Rightarrow$ higher movement score.
5. **Consumption priority.** For equal resource values, $\psi(\text{CONSUME}) > \psi(\text{DIR})$ when $w_{\text{consume}} > 1$.
6. **Stay suppression.** $\psi(\text{STAY}) < 0$ whenever $d_H > 0$.
7. **Deterministic reproducibility.** Same seed $\Rightarrow$ same trajectory.
8. **Terminal condition.** $e_{t+1} = 0 \Rightarrow$ episode ends.
9. **Buffer fidelity.** Buffer contains exactly the $k$ most recent observations.
10. **Softmax normalization.** $\sum_a P(a) = 1$ at every step.

Each criterion is verified by worked examples in the formal
specification and by automated tests in the implementation.

---

## 12. Summary

System A demonstrates that recognizable foraging behavior can
emerge from a minimal mechanism:

- A 10-dimensional observation (5 cells $\times$ 2 signals)
- A linear hunger activation ($1 - e/E_{\max}$)
- A multiplicative modulation ($d_H \cdot r_{\text{dir}}$)
- A softmax policy
- A linear energy model (cost - gain)

No learning, no planning, no world model. Just five equations
composed into a pipeline. The resulting behavior -- sated wandering,
directed foraging, desperate survival -- is fully explained by
these equations and fully predictable from the parameters.

System A is the foundation that System A+W extends. Understanding
System A completely is the prerequisite for understanding what the
curiosity drive and world model add.

---

> **Next:** [System A+W -- The Exploring Forager](05-system-aw.md) --
> Adding curiosity, spatial cognition, and motivational hierarchy.
