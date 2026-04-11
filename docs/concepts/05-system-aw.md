# System A+W: The Exploring Forager

**AXIS Conceptual Series -- Document 5 of 5**

> **Reading order:**
> [1. AXIS Vision](01-axis-cms-vision.md) |
> [2. Math as Modeling](02-math-as-modeling.md) |
> [3. Agent Framework](03-agent-framework.md) |
> [4. System A](04-system-a.md) |
> **5. System A+W**
>
> **Formal specification:** [System A+W Model](../system-design/system-a+w/01_System%20A+W%20Model.md) |
> [Worked Examples](../system-design/system-a+w/02_System%20A+W%20Worked%20Examples.md)

---

## 1. From Foraging to Exploring

System A survives by foraging: sensing nearby food, moving toward
it, and consuming it. But System A has no memory of where it has
been. It cannot distinguish a cell it has visited ten times from
one it has never seen. It has no reason to prefer unexplored
territory over familiar ground.

System A+W adds exactly two things to System A:

1. **A spatial world model** -- a visit-count map maintained through
   dead reckoning, giving the agent a sense of "where I have been."

2. **A curiosity drive** -- a second motivational signal that values
   novelty, pushing the agent toward unfamiliar territory.

With these two additions, a new behavioral capacity emerges:
**exploration**. The agent no longer just reacts to immediate
stimuli. It actively seeks out parts of the environment it has
not visited, driven by a curiosity signal that is suppressed
when survival needs are urgent.

The interaction between hunger and curiosity produces a
**Maslow-like motivational hierarchy**: when energy is plentiful,
curiosity dominates and the agent explores; when energy is scarce,
hunger dominates and the agent forages. The transition between
these regimes is smooth and governed by a single parameter
($\gamma$, the gating sharpness).

---

## 2. Formal Definition

System A+W extends the 8-tuple to a 9-tuple by adding the
world model space $\mathcal{W}$:

$$A^{+W} = (\mathcal{X},\ \mathcal{U},\ \mathcal{M},\ \mathcal{W},\ \mathcal{A},\ \mathcal{D},\ F,\ \Gamma,\ \pi)$$

| Component | System A+W Instantiation |
|---|---|
| $\mathcal{X}$ | $(e_t, m_t, \hat{p}_t, w_t)$ -- energy, buffer, relative position, visit map |
| $\mathcal{U}$ | $\mathbb{R}^{10}$ -- same Von Neumann neighborhood as System A |
| $\mathcal{M}$ | Same FIFO buffer, but now **actively read** by curiosity drive |
| $\mathcal{W}$ | $\mathbb{Z}^2 \to \mathbb{N}_0$ -- visit-count map (spatial memory) |
| $\mathcal{A}$ | Same 6 actions as System A |
| $\mathcal{D}$ | $\{D_H, D_C\}$ -- hunger + curiosity |
| $F$ | Extended transition: energy + memory + dead reckoning + visit map |
| $\Gamma$ | Dual-drive modulation with dynamic weights |
| $\pi$ | Same softmax policy, operating on combined scores |

The sensor, action space, action handlers, and policy mechanism
are **inherited unchanged** from System A. What changes is the
internal state, the drive system, the modulation, and the
transition function.

---

## 3. The World Model

### 3.1 What the Agent Remembers

The world model is a **visit-count map**: a function that records
how many times the agent has visited each location.

$$w_t : \mathbb{Z}^2 \to \mathbb{N}_0$$

The domain is $\mathbb{Z}^2$ (the infinite integer grid), though
in practice only visited cells have non-zero counts. The map is
initialized with count 1 at the origin:

$$w_0(0, 0) = 1, \quad w_0(\hat{p}) = 0 \text{ for all } \hat{p} \neq (0, 0)$$

### 3.2 Dead Reckoning

The agent does not know its absolute position $p_t$ (which belongs
to the world). Instead, it maintains a **relative position
estimate** $\hat{p}_t$ through dead reckoning -- updating its
position belief based on its own motor commands and their outcomes.

Initial estimate:

$$\hat{p}_0 = (0, 0)$$

Update rule:

$$\hat{p}_{t+1} = \hat{p}_t + \mu_t \cdot \Delta(a_t)$$

where:

- $\Delta(a_t)$ is the displacement vector for the chosen action
  (same as the movement deltas: $\Delta(\text{UP}) = (0, -1)$,
  etc.). For non-movement actions (CONSUME, STAY),
  $\Delta(a_t) = (0, 0)$.

- $\mu_t \in \{0, 1\}$ is the **movement signal** from the action
  outcome: $\mu_t = 1$ if the agent actually moved, $\mu_t = 0$
  if the movement was blocked (e.g., by a wall or obstacle).

Dead reckoning is **exact** in AXIS's discrete grid because the
world provides the movement outcome $\mu_t$. In a continuous or
noisy environment, dead reckoning would accumulate errors; here, it
is perfect.

### 3.3 Visit-Count Update

After updating the position estimate, the visit count at the new
location is incremented:

$$w_{t+1}(\hat{p}) = \begin{cases}
w_t(\hat{p}) + 1 & \text{if } \hat{p} = \hat{p}_{t+1} \\
w_t(\hat{p}) & \text{otherwise}
\end{cases}$$

If the agent stays in place (STAY, CONSUME, or blocked movement),
$\hat{p}_{t+1} = \hat{p}_t$ and the current cell's count
increments -- the agent "remembers" spending another timestep here.

### 3.4 What the World Model Is Not

The world model is **not** a map of the environment. It does not
store cell types, resources, or obstacle locations. It records only
visit counts -- a purely egocentric spatial memory of "how familiar
is this place." This is a minimal form of spatial cognition,
analogous to path integration in biology, where organisms maintain
a sense of displacement from a reference point through motor
efference copy.

### 3.5 Comparison with Episodic Memory

| Property | Episodic Memory $m_t$ | World Model $w_t$ |
|---|---|---|
| Content | Observation vectors | Visit counts |
| Structure | Ordered FIFO buffer | Spatial map |
| Update source | Sensor output | Movement outcome |
| Bounded? | Yes (capacity $k$) | No (grows with exploration) |
| Purpose | Temporal context | Spatial novelty |
| System A role | Passive (scaffold) | Does not exist |
| System A+W role | Sensory novelty source | Spatial novelty source |

---

## 4. Novelty: The Fuel of Curiosity

Curiosity in AXIS is defined as the drive to encounter **novelty**
-- to experience things that are different from what the agent has
recently experienced. Novelty has two independent sources: spatial
(where the agent has been) and sensory (what the agent has
perceived).

### 4.1 Spatial Novelty

Spatial novelty measures how unexplored a neighboring cell is,
based on the visit-count map:

$$\nu_{\text{dir}}^{\text{spatial}} = \frac{1}{1 + w_t(\hat{p}_t + \Delta(\text{dir}))}$$

| Visits | $\nu^{\text{spatial}}$ | Interpretation |
|---|---|---|
| 0 | 1.000 | Never visited -- maximally novel |
| 1 | 0.500 | Visited once -- moderately novel |
| 2 | 0.333 | Visited twice -- familiar |
| 5 | 0.167 | Well-trodden |
| 10 | 0.091 | Very familiar |
| $n \to \infty$ | $\to 0$ | Completely habituated |

The hyperbolic decay $1/(1+n)$ models **habituation**: each
additional visit provides diminishing marginal novelty. The first
visit to a cell is maximally novel; subsequent visits rapidly
lose their novelty value. This mirrors biological habituation
curves where organisms show decreasing response to repeated
stimuli.

Spatial novelty is defined per direction (UP, DOWN, LEFT, RIGHT).
It is not defined for CONSUME or STAY -- these actions do not
change the agent's position.

### 4.2 Sensory Novelty

Sensory novelty measures how different the current observation is
from recent experience, using the episodic memory:

$$\nu_{\text{dir}}^{\text{sensory}} = |r_{\text{dir}}(t) - \bar{r}_{\text{dir}}|$$

where $\bar{r}_{\text{dir}}$ is the **mean resource intensity** in
direction $\text{dir}$ across all memory entries:

$$\bar{r}_{\text{dir}} = \frac{1}{|m_t|} \sum_{j=1}^{|m_t|} r_{\text{dir}}^{(j)}$$

Sensory novelty is high when the current observation deviates
significantly from the recent average. If the agent has been
navigating empty terrain and suddenly encounters a resource-rich
cell, the sensory novelty signal spikes.

Unlike spatial novelty, sensory novelty depends on the observation
content, not the location. The same cell can have high sensory
novelty if its resource value has changed since last visit
(e.g., due to regeneration).

When the buffer is empty ($|m_t| = 0$), sensory novelty defaults
to zero for all directions.

### 4.3 Composite Novelty

The two novelty signals are blended with a mixing parameter
$\alpha \in [0, 1]$:

$$\nu_{\text{dir}} = \alpha \cdot \nu_{\text{dir}}^{\text{spatial}} + (1 - \alpha) \cdot \nu_{\text{dir}}^{\text{sensory}}$$

| $\alpha$ | Behavior |
|---|---|
| 0.0 | Pure sensory novelty -- agent chases resource changes |
| 0.5 | Equal blend -- spatial and sensory contribute equally |
| 1.0 | Pure spatial novelty -- agent explores unvisited cells |

The mixing parameter $\alpha$ is a design choice that determines
what "novelty" means for this agent: spatial unfamiliarity,
sensory surprise, or a combination. Different biological organisms
weight these differently -- a bacterium following a chemical gradient
is doing sensory novelty; a rat exploring a maze is doing spatial
novelty; a foraging bird likely does both.

---

## 5. The Curiosity Drive

### 5.1 Activation

The curiosity drive activation depends on a **novelty saturation**
measure -- how much novelty the agent has been experiencing recently:

$$d_C(t) = \mu_C \cdot (1 - \bar{\nu}_t)$$

where $\mu_C \in [0, 1]$ is the **base curiosity level** (a
parameter) and $\bar{\nu}_t$ is the **novelty saturation**:

$$\bar{\nu}_t = \frac{1}{|m_t|} \sum_{j=1}^{|m_t|} \sigma_j$$

Here $\sigma_j$ is the **sensory surprise** of memory entry $j$:
a measure of how unexpected that observation was relative to the
rest of the buffer.

The logic: if the agent has been experiencing high novelty recently
($\bar{\nu}_t \approx 1$), curiosity activation is low
($d_C \approx 0$) -- the drive is "satisfied." If recent experience
has been monotonously familiar ($\bar{\nu}_t \approx 0$), curiosity
is high ($d_C \approx \mu_C$) -- the drive is "hungry for novelty."

The parameter $\mu_C$ caps the maximum curiosity activation.
Setting $\mu_C = 0$ disables curiosity entirely, reducing the
system to System A.

### 5.2 Modulation Function

The curiosity drive's modulation function $\phi_C$ translates
composite novelty into per-action scores:

**Movement actions** (UP, DOWN, LEFT, RIGHT):

$$\phi_C(\text{DIR}, u_t, m_t, w_t) = \nu_{\text{dir}}$$

the composite novelty of the neighboring cell in that direction.
Moving toward unexplored or surprising cells scores higher.

**Non-movement actions** (CONSUME, STAY):

$$\phi_C(\text{CONSUME}) = \phi_C(\text{STAY}) = -\lambda_{\text{explore}}$$

where $\lambda_{\text{explore}} \geq 0$ is the **exploration
penalty**. Under curiosity, consuming and staying are penalized
because they do not move the agent toward novel territory.

This is the curiosity drive's counterpart to hunger's stay
suppression. While hunger penalizes only STAY, curiosity penalizes
both STAY and CONSUME -- a curious agent should be moving, not
eating or idling.

---

## 6. Drive Arbitration

### 6.1 The Problem

With two drives, the agent must balance hunger and curiosity.
This is not a simple weighted average: the drives have a
**priority hierarchy**. Hunger represents a survival need;
curiosity represents a higher-order need. When survival is
threatened, curiosity should yield.

This mirrors Maslow's hierarchy of needs: physiological needs
(hunger) must be satisfied before higher-order needs (curiosity,
exploration) can be pursued.

### 6.2 Dynamic Weight Functions

The arbitration is implemented through dynamic weight functions
that modulate each drive's influence based on the current hunger
level:

**Hunger weight:**

$$w_H(t) = w_H^{\text{base}} + (1 - w_H^{\text{base}}) \cdot d_H(t)^{\gamma}$$

**Curiosity weight:**

$$w_C(t) = w_C^{\text{base}} \cdot (1 - d_H(t))^{\gamma}$$

### 6.3 The Role of $\gamma$ (Gating Sharpness)

The parameter $\gamma > 0$ controls how abruptly the agent
transitions between curiosity-dominated and hunger-dominated
regimes.

**At $d_H = 0.5$ (moderate hunger):**

| $\gamma$ | $w_H$ | $w_C$ | Ratio $w_H / w_C$ |
|---|---|---|---|
| 0.5 | 0.541 | 0.707 | 0.77 (curiosity still stronger) |
| 1.0 | 0.575 | 0.500 | 1.15 (roughly balanced) |
| 2.0 | 0.538 | 0.250 | 2.15 (hunger dominates) |
| 4.0 | 0.519 | 0.063 | 8.27 (hunger strongly dominates) |

(Assumes $w_H^{\text{base}} = 0.3$, $w_C^{\text{base}} = 1.0$)

Low $\gamma$ produces a gradual transition: the agent blends
foraging and exploration over a wide energy range. High $\gamma$
produces a sharp switch: the agent either explores or forages,
with little middle ground.

### 6.4 Weight Function Properties

The weight functions satisfy these properties for all
valid parameter values:

| Property | Statement |
|---|---|
| **Hunger floor** | $w_H(t) \geq w_H^{\text{base}} > 0$ for all $d_H$ |
| **Hunger ceiling** | $w_H(t) \leq 1$ with equality at $d_H = 1$ |
| **Curiosity ceiling** | $w_C(t) \leq w_C^{\text{base}}$ with equality at $d_H = 0$ |
| **Curiosity floor** | $w_C(t) \geq 0$ with equality at $d_H = 1$ |
| **Hunger monotonically increasing** | $\frac{\partial w_H}{\partial d_H} \geq 0$ |
| **Curiosity monotonically decreasing** | $\frac{\partial w_C}{\partial d_H} \leq 0$ |
| **Full curiosity when sated** | $d_H = 0 \Rightarrow w_C = w_C^{\text{base}}$ |
| **No curiosity when starving** | $d_H = 1 \Rightarrow w_C = 0$ |

These are not approximations or heuristics -- they are algebraic
consequences of the weight function definitions and hold exactly.

---

## 7. Combined Action Modulation

### 7.1 The Extended Score

With two drives, the action score combines both contributions:

$$\psi(a) = w_H(t) \cdot d_H(t) \cdot \phi_H(a, u_t) + w_C(t) \cdot d_C(t) \cdot \phi_C(a, u_t, m_t, w_t)$$

The first term is the hunger contribution (identical to System A,
but now scaled by $w_H$ instead of being the sole contributor).
The second term is the curiosity contribution.

### 7.2 Score Decomposition by Action Type

**Movement actions:**

$$\psi(\text{DIR}) = \underbrace{w_H(t) \cdot d_H(t) \cdot r_{\text{dir}}(t)}_{\text{hunger: go toward food}} + \underbrace{w_C(t) \cdot d_C(t) \cdot \nu_{\text{dir}}}_{\text{curiosity: go toward novelty}}$$

Movement scores are the sum of two independent signals: resource
attraction (hunger) and novelty attraction (curiosity).

**Consume:**

$$\psi(\text{CONSUME}) = \underbrace{w_H(t) \cdot d_H(t) \cdot w_{\text{consume}} \cdot r_c(t)}_{\text{hunger: eat}} + \underbrace{w_C(t) \cdot d_C(t) \cdot (-\lambda_{\text{explore}})}_{\text{curiosity: don't eat, explore}}$$

Consumption is favored by hunger and penalized by curiosity. The
balance depends on the relative magnitudes of the two terms.

**Stay:**

$$\psi(\text{STAY}) = \underbrace{-w_H(t) \cdot d_H(t) \cdot \lambda_{\text{stay}}}_{\text{hunger: don't idle}} + \underbrace{w_C(t) \cdot d_C(t) \cdot (-\lambda_{\text{explore}})}_{\text{curiosity: don't idle}}$$

Both drives penalize staying. Hunger penalizes it through
$\lambda_{\text{stay}}$; curiosity penalizes it through
$\lambda_{\text{explore}}$. STAY is doubly suppressed in
System A+W.

### 7.3 Behavioral Examples

**Well-fed agent ($d_H = 0.1$):**

$w_H \approx 0.3$, $w_C \approx 1.0$. Hunger contribution is
small ($\approx 0.03 \cdot r_{\text{dir}}$). Curiosity dominates.
The agent moves toward the cell with highest composite novelty,
largely ignoring resources.

**Moderately hungry ($d_H = 0.5$):**

$w_H \approx 0.55$, $w_C \approx 0.5$. Hunger and curiosity
contribute roughly equally. The agent prefers cells that are
*both* resource-rich *and* novel. CONSUME is attractive when
standing on food, but the curiosity penalty reduces its
advantage.

**Starving ($d_H = 0.95$):**

$w_H \approx 0.95$, $w_C \approx 0.003$. Curiosity is effectively
zero. The agent behaves identically to System A: pure hunger-driven
foraging. The world model still updates (visit counts increment),
but the curiosity signal has no influence on behavior.

---

## 8. Extended Transition

### 8.1 Five Phases

System A+W extends the transition function with two additional
phases for the world model:

| Phase | Operation | Formula |
|---|---|---|
| 1. Energy | Same as System A | $e_{t+1} = \text{clip}(e_t - c(a_t) + \kappa \cdot \Delta R^{\text{cons}})$ |
| 2. Memory | Same as System A | $m_{t+1} = G_{\text{mem}}(m_t, u_{t+1})$ |
| 3. Dead reckoning | Update position estimate | $\hat{p}_{t+1} = \hat{p}_t + \mu_t \cdot \Delta(a_t)$ |
| 4. Visit map | Increment at current position | $w_{t+1}(\hat{p}_{t+1}) = w_t(\hat{p}_{t+1}) + 1$ |
| 5. Termination | Same as System A | $e_{t+1} = 0 \Rightarrow$ stop |

Phases 3-4 are the only additions. The energy model, memory update,
and termination condition are unchanged from System A.

### 8.2 Position Estimation Details

The dead reckoning update uses the **movement signal** $\mu_t$ from
the action outcome, not from the agent's intention. If the agent
intended to move RIGHT but was blocked by a wall, $\mu_t = 0$ and
$\hat{p}_{t+1} = \hat{p}_t$ -- the position estimate correctly
reflects that no movement occurred.

For CONSUME and STAY, $\Delta(a_t) = (0, 0)$ regardless of
$\mu_t$, so the position estimate does not change. However, the
visit count still increments (the agent is "spending time" at this
location).

### 8.3 Coordinate Frame

The position estimate $\hat{p}_t$ is in **agent-relative
coordinates**: it starts at $(0, 0)$ and accumulates displacements.
It does not correspond to any absolute world coordinate. Two agents
starting at different absolute positions would both have
$\hat{p}_0 = (0, 0)$.

This is deliberate. The agent's spatial memory is egocentric --
centered on the agent's starting point. It records relative
displacement, not absolute location. This is analogous to path
integration in biology, where animals maintain a "home vector"
through accumulated motor commands.

---

## 9. Emergent Behavioral Regimes

System A+W exhibits four behavioral regimes, two more than System A:

### 9.1 Active Exploration ($d_H \approx 0$)

The agent is well-fed. $w_C \approx w_C^{\text{base}}$, curiosity
dominates. The agent systematically moves toward cells with high
composite novelty (unvisited or recently changed). It avoids
consuming even when standing on food (the curiosity penalty on
CONSUME outweighs the hunger incentive).

This regime does not exist in System A.

### 9.2 Balanced Foraging-Exploration ($0.3 \leq d_H \leq 0.6$)

Both drives contribute. The agent favors cells that combine resource
availability with spatial novelty. It consumes when standing on
rich resources but otherwise prefers movement toward novel
directions. This creates efficient foraging -- the agent covers new
ground while feeding opportunistically.

### 9.3 Hunger-Dominated Foraging ($0.7 \leq d_H \leq 0.9$)

Hunger suppresses curiosity ($w_C$ low). Behavior resembles
System A: directed toward food, consuming when possible. The
world model still updates, but its influence on action selection
is negligible.

### 9.4 Pure Survival ($d_H \to 1$)

Identical to System A's desperate foraging. $w_C \approx 0$.
The agent is a pure forager fighting for survival.

### 9.5 The Forage-Explore Cycle

The most interesting emergent behavior occurs when the agent
oscillates between regimes. A typical cycle:

1. Agent starts with moderate energy, explores novel territory
   (curiosity-dominated).
2. Energy depletes through movement costs.
3. As $d_H$ crosses $\sim 0.5$, hunger begins to dominate.
4. Agent shifts to foraging, seeks and consumes resources.
5. Energy recovers, $d_H$ drops back below 0.3.
6. Curiosity re-emerges, agent resumes exploration.

This cycle is not programmed. It is an emergent consequence of the
drive weight dynamics: $w_H$ and $w_C$ are continuous functions of
$d_H$, which is a continuous function of energy, which changes
through the energy transition model. The cycle period depends on
the energy costs, resource density, regeneration rate, and the
sharpness parameter $\gamma$.

---

## 10. The Reduction Property

System A+W formally reduces to System A when curiosity is disabled.
This is guaranteed by two mathematical identities:

**Condition 1:** $\mu_C = 0$ (base curiosity level is zero)

$$d_C(t) = \mu_C \cdot (1 - \bar{\nu}_t) = 0 \cdot (\ldots) = 0$$

$$\psi(a) = w_H(t) \cdot d_H(t) \cdot \phi_H(a) + w_C(t) \cdot 0 \cdot \phi_C(a) = w_H(t) \cdot d_H(t) \cdot \phi_H(a)$$

Since $w_H$ and $d_H$ are both scalars that do not depend on
curiosity parameters, the score is proportional to
$d_H(t) \cdot \phi_H(a)$ -- which produces identical softmax
probabilities as System A (the multiplicative constant $w_H$
cancels in the softmax normalization).

**Condition 2:** $w_C^{\text{base}} = 0$

$$w_C(t) = w_C^{\text{base}} \cdot (1 - d_H(t))^{\gamma} = 0$$

Again, the curiosity term vanishes from the action score.

Both conditions are verified by automated tests that run the same
experiment with System A and System A+W (with $\mu_C = 0$) and
confirm identical trajectories, step by step, to floating-point
precision.

The reduction property is the formal guarantee that System A+W is
a **strict extension** of System A: it adds capabilities without
changing the baseline. Every behavior that System A exhibits,
System A+W also exhibits (when curiosity is disabled). Every new
behavior that System A+W exhibits is attributable to the curiosity
drive and its interaction with the hunger drive.

---

## 11. Configuration Parameters

System A+W adds these parameters to System A's set:

| Parameter | Symbol | Domain | Role |
|---|---|---|---|
| Base curiosity | $\mu_C$ | $[0, 1]$ | Maximum curiosity activation |
| Novelty balance | $\alpha$ | $[0, 1]$ | Spatial vs sensory blend |
| Explore penalty | $\lambda_{\text{explore}}$ | $\mathbb{R}_0^+$ | CONSUME/STAY suppression under curiosity |
| Hunger base weight | $w_H^{\text{base}}$ | $(0, 1)$ | Floor for hunger influence |
| Curiosity base weight | $w_C^{\text{base}}$ | $\mathbb{R}^+$ | Ceiling for curiosity influence |
| Gating sharpness | $\gamma$ | $\mathbb{R}^+$ | Hunger-curiosity transition steepness |
| Novelty sharpness | $\gamma_{\nu}$ | $\mathbb{R}^+$ | Controls novelty signal contrast |

All other parameters (energy costs, consume weight, temperature,
buffer capacity, etc.) are inherited from System A unchanged.

---

## 12. Validation Criteria

Beyond System A's 10 criteria, System A+W adds:

1. **World model accuracy.** Visit count at $\hat{p}_t$ equals the
   number of timesteps the agent has occupied that position.
2. **Dead reckoning correctness.** $\hat{p}_t$ equals the sum of
   all successful displacement vectors from $t = 0$.
3. **Spatial novelty monotonicity.** $\nu^{\text{spatial}}$ strictly
   decreases with visit count.
4. **Curiosity suppression.** $d_H \to 1 \Rightarrow w_C \to 0$.
5. **Reduction to System A.** $\mu_C = 0$ or $w_C^{\text{base}} = 0$
   produces identical behavior to System A.
6. **Weight monotonicity.** $w_H$ non-decreasing and $w_C$
   non-increasing in $d_H$.
7. **Exploration penalty.** CONSUME/STAY scores decrease when
   curiosity activation increases.

---

## 13. Design Discussion

### 13.1 Why Visit Counts, Not a Full Map?

A full environmental map (storing cell types and resources at every
visited position) would give the agent much more planning power.
But it would violate two AXIS principles:

- **Minimality.** We add only what is needed for the target behavior
  (exploration). Exploration requires knowing *where the agent has
  been*, not *what was there*. Visit counts are sufficient.

- **Biological plausibility.** Path integration in biology records
  displacement and familiarity, not detailed environmental maps.
  The visit-count map is closer to biological spatial memory than
  a SLAM (Simultaneous Localization and Mapping) system.

### 13.2 Why Two Novelty Sources?

Spatial and sensory novelty capture different aspects of "newness":

- **Spatial novelty** is position-based: a cell is novel because
  the agent has not been there. It does not change even if the
  cell's contents change (e.g., through regeneration).

- **Sensory novelty** is content-based: a cell is novel because
  its current observation differs from what the agent has recently
  seen. It can be high even for a frequently visited cell if the
  environment has changed.

Blending both signals through the $\alpha$ parameter lets us model
different "curiosity styles" -- purely exploratory ($\alpha = 1$),
purely stimulus-seeking ($\alpha = 0$), or a biologically plausible
combination.

### 13.3 Why Not a Neural Curiosity Module?

Intrinsic motivation in reinforcement learning often uses neural
predictors: a curiosity signal is the prediction error of a
learned world model. AXIS avoids this because:

- The curiosity signal would be opaque (depends on learned weights).
- The signal would change over time as the predictor improves.
- The relationship between curiosity and behavior would be mediated
  by learning dynamics that are hard to analyze.

AXIS's curiosity is a direct, analyzable function of visit counts
and observation history. We can predict exactly how novel each
direction is, what the curiosity activation will be, and how it
will influence action selection -- all by hand calculation, before
running any code.

---

## 14. Summary

System A+W demonstrates that adding a spatial memory and a
curiosity drive produces qualitatively new behavior -- active
exploration -- while preserving the mathematical transparency and
mechanistic explanation that characterize System A.

The key additions:

| Component | Mathematical Object | Behavioral Effect |
|---|---|---|
| Visit-count map | $w_t : \mathbb{Z}^2 \to \mathbb{N}_0$ | Spatial memory |
| Dead reckoning | $\hat{p}_{t+1} = \hat{p}_t + \mu_t \cdot \Delta(a_t)$ | Position awareness |
| Spatial novelty | $\nu^{\text{spatial}} = 1/(1 + w_t(\hat{p} + \Delta))$ | Prefer unexplored cells |
| Sensory novelty | $\nu^{\text{sensory}} = |r - \bar{r}|$ | Prefer surprising observations |
| Curiosity drive | $d_C = \mu_C \cdot (1 - \bar{\nu}_t)$ | Motivation to seek novelty |
| Drive weights | $w_H(d_H, \gamma)$, $w_C(d_H, \gamma)$ | Maslow-like priority |

The reduction property guarantees that System A+W is a strict
extension: disable curiosity, and you recover System A exactly.
This incremental composition -- adding precisely one new capability
per system while preserving backward compatibility -- is the
engineering methodology at the heart of AXIS.

---

> **This concludes the AXIS Conceptual Series.**
>
> For implementation details, see the
> [System Developer Manual](../manuals/system-dev-manual.md) and the
> [Building a System Tutorial](../tutorials/building-a-system.md).
>
> For full formal specifications, see the
> [System A Baseline](../system-design/system-a/01_System%20A%20Baseline.md) and
> [System A+W Model](../system-design/system-a+w/01_System%20A+W%20Model.md).
