# The Generic Agent Framework

**AXIS Conceptual Series -- Document 3 of 5**

> **Reading order:**
> [1. AXIS CMS Vision](01-axis-cms-vision.md) |
> [2. Math as Modeling](02-math-as-modeling.md) |
> **3. Agent Framework** |
> [4. System A](04-system-a.md) |
> [5. System A+W](05-system-aw.md)

---

## 1. Purpose

This document presents the **generic mathematical framework** that
all AXIS agent systems instantiate. It defines the abstract
architecture -- the state spaces, the function signatures, the
execution cycle -- without committing to any particular drive,
sensor, or policy. System A and System A+W are specific
instantiations of this generic framework.

The framework answers the question: *What is the minimal
mathematical structure needed to describe a drive-modulated
autonomous agent operating in a discrete grid world?*

---

## 2. The Agent Tuple

An AXIS agent is defined as an 8-tuple:

$$A = (\mathcal{X},\ \mathcal{U},\ \mathcal{M},\ \mathcal{A},\ \mathcal{D},\ F,\ \Gamma,\ \pi)$$

| Symbol | Name | Description |
|---|---|---|
| $\mathcal{X}$ | Internal state space | All possible agent states |
| $\mathcal{U}$ | Observation space | All possible sensory inputs |
| $\mathcal{M}$ | Memory space | All possible memory configurations |
| $\mathcal{A}$ | Action space | Finite set of available actions |
| $\mathcal{D}$ | Drive set | Collection of drive functions $\{D_1, \ldots, D_n\}$ |
| $F$ | Transition function | State update rule |
| $\Gamma$ | Modulation system | Maps drives to action scores |
| $\pi$ | Policy | Maps scores to action probability distribution |

Extended systems (e.g., System A+W) may add additional spaces to
the tuple. System A+W adds $\mathcal{W}$ (world model space),
making it a 9-tuple. The framework accommodates such extensions
by design.

---

## 3. State Spaces

### 3.1 Internal State

The internal state $x_t \in \mathcal{X}$ represents everything the
agent carries between timesteps. At minimum:

$$x_t = (e_t, \xi_t)$$

where:

- $e_t \in [0, E_{\max}]$ is the agent's **energy level**. This is
  the primary survival resource. The framework reads one scalar
  metric from the agent state: **vitality**, defined as
  $v_t = e_t / E_{\max} \in [0, 1]$.

- $\xi_t$ represents **auxiliary internal variables** specific to the
  system (e.g., cooldown timers, mode flags, accumulated statistics).

The framework treats agent state as **opaque**. It passes $x_t$ to
the system's methods without inspecting it. Only the `vitality()`
function, which returns $v_t$, is readable by the framework.

### 3.2 Environment State

The environment has its own state:

$$s_t^{\text{world}} = (\mathcal{E}_t, p_t)$$

where:

- $\mathcal{E}_t$ is the environment configuration at time $t$:
  the grid of cells, each with type and resource value.

- $p_t \in \mathbb{Z}^2$ is the agent's **absolute position**.

**Critical design constraint:** The agent has **no access** to $p_t$.
Position belongs to the world, not to the agent. The agent perceives
its surroundings through the sensor function $S$, which provides
only a local view. If an agent needs spatial awareness, it must
build its own model (as System A+W does with the visit-count map).

### 3.3 Observation Space

An observation $u_t \in \mathcal{U}$ is the agent's sensory input
at time $t$:

$$u_t = S(s_t^{\text{world}})$$

The sensor function $S$ maps the full world state to a local
observation. The observation captures only the agent's immediate
neighborhood -- there is no global perception.

In AXIS, the standard observation is a Von Neumann neighborhood:
the current cell and four cardinal neighbors. Each cell contributes
two signals:

- **Traversability** $b_j \in \{0, 1\}$: whether the cell can be
  entered.
- **Resource intensity** $r_j \in [0, 1]$: how much resource the
  cell contains.

For a 5-cell neighborhood, this produces a 10-dimensional
observation vector:

$$u_t = (b_c, r_c, b_{\uparrow}, r_{\uparrow}, b_{\downarrow}, r_{\downarrow}, b_{\leftarrow}, r_{\leftarrow}, b_{\rightarrow}, r_{\rightarrow})$$

Out-of-bounds cells are observed as $(b = 0, r = 0)$: non-traversable
with no resource.

### 3.4 Memory Space

The episodic perceptual memory $m_t \in \mathcal{M}$ stores a
bounded history of recent observations:

$$m_t = (u_{t-k+1}, u_{t-k+2}, \ldots, u_t)$$

where $k$ is the buffer capacity. The memory is updated as a FIFO
(first-in, first-out) buffer:

$$m_{t+1} = G_{\text{mem}}(m_t, u_{t+1})$$

which appends $u_{t+1}$ and drops the oldest entry if the buffer
exceeds capacity.

In the baseline (System A), memory is **passive**: it stores
observations but no drive reads from it. In extended systems
(System A+W), the curiosity drive uses the memory to compute
sensory novelty.

---

## 4. The Action Space

The action space is a finite set of discrete actions. All AXIS
systems share five **base actions** provided by the framework:

$$\mathcal{A}_{\text{base}} = \{\text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}, \text{STAY}\}$$

Each movement action has a displacement vector:

$$\Delta(\text{UP}) = (0, -1), \quad \Delta(\text{DOWN}) = (0, +1), \quad \Delta(\text{LEFT}) = (-1, 0), \quad \Delta(\text{RIGHT}) = (+1, 0)$$

Systems may extend the action space with **custom actions**:

$$\mathcal{A}_{\text{system}} = \mathcal{A}_{\text{base}} \cup \{a_{\text{custom}, 1}, \ldots, a_{\text{custom}, m}\}$$

For example, System A adds CONSUME: $\mathcal{A} = \{\text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}, \text{CONSUME}, \text{STAY}\}$.

The action space is ordered. All vectors indexed by action
(contributions, probabilities, masks) follow the canonical ordering.

---

## 5. The Drive System

### 5.1 What Is a Drive?

A **drive** is a scalar signal that represents an internal need or
motivation. It modulates the agent's action preferences based on the
agent's current state, observation, and memory.

Formally, a drive function is:

$$D_i : \mathcal{X} \times \mathcal{U} \times \mathcal{M} \to \mathbb{R}$$

producing a scalar **activation** $d_i(t) = D_i(x_t, u_t, m_t)$.

The drive set $\mathcal{D} = \{D_1, D_2, \ldots, D_n\}$ contains
all active drives. In System A, $\mathcal{D} = \{D_H\}$ (hunger
only). In System A+W, $\mathcal{D} = \{D_H, D_C\}$ (hunger +
curiosity).

### 5.2 Drive Activation

The activation $d_i(t)$ is typically bounded in $[0, 1]$ and
represents the "urgency" of the drive's need at time $t$:

- $d_i(t) = 0$: the need is fully satisfied.
- $d_i(t) = 1$: the need is at maximum urgency.

The specific activation function depends on the drive. For example,
hunger activation is:

$$d_H(t) = \text{clip}\!\left(1 - \frac{e_t}{E_{\max}},\ 0,\ 1\right)$$

### 5.3 Drive Modulation Functions

Each drive $D_i$ has an associated **modulation function** $\phi_i$
that maps the drive's activation and the current observation into
per-action scores:

$$\phi_i : \mathcal{A} \times \mathcal{U} \times \mathcal{M} \to \mathbb{R}$$

The modulation function specifies *how* the drive influences action
selection. A hunger drive might boost actions that move toward food;
a curiosity drive might boost actions that move toward unexplored
territory.

### 5.4 Drive Independence

Drives are designed to be **independent modules**. Drive $D_i$ does
not read the output of drive $D_j$. Each drive independently
produces its activation and modulation scores. The combination
happens in the modulation system $\Gamma$, not inside individual
drives.

This independence is what makes the architecture modular: adding a
new drive means adding a new function $D_{n+1}$ with its own
$\phi_{n+1}$, without modifying existing drives.

---

## 6. The Modulation System

The modulation system combines all drive outputs into a single
action score vector. It has two layers.

### 6.1 Baseline Action Term

The **baseline action term** $\psi_0(a)$ represents the prior
preference for an action in the absence of any drive activation:

$$\psi_0 : \mathcal{A} \to \mathbb{R}$$

In all current AXIS systems, $\psi_0(a) = 0\ \forall a$ --
a uniform prior expressing no inherent preference. This could be
changed for systems where certain actions should be intrinsically
preferred or avoided.

### 6.2 Multi-Drive Modulation

The **modulated action score** $\psi(a)$ combines the baseline with
all drive contributions:

$$\psi(a) = \psi_0(a) + \sum_{i=1}^{n} w_i(t) \cdot d_i(t) \cdot \phi_i(a, u_t, m_t)$$

where:

- $w_i(t)$ is the **dynamic weight** of drive $i$ at time $t$.
- $d_i(t)$ is the **activation** of drive $i$.
- $\phi_i(a, u_t, m_t)$ is the **per-action modulation** from
  drive $i$.

The product $w_i(t) \cdot d_i(t) \cdot \phi_i(a)$ is the
*effective contribution* of drive $i$ to action $a$. The sum
across all drives gives the total modulated score.

### 6.3 Dynamic Drive Weights

When multiple drives are active, **drive weights** $w_i(t)$
determine their relative influence. In a single-drive system,
$w_i(t) = 1$ (trivially). In multi-drive systems, the weights
implement a **priority hierarchy**.

The AXIS framework uses a Maslow-like hierarchy where survival
needs gate higher-order needs. For two drives (hunger and
curiosity):

$$w_H(t) = w_H^{\text{base}} + (1 - w_H^{\text{base}}) \cdot d_H(t)^{\gamma}$$

$$w_C(t) = w_C^{\text{base}} \cdot (1 - d_H(t))^{\gamma}$$

Properties of these weight functions:

| Property | Formula | Meaning |
|---|---|---|
| Hunger floor | $w_H(t) \geq w_H^{\text{base}}$ | Hunger always has at least baseline influence |
| Curiosity ceiling | $w_C(t) \leq w_C^{\text{base}}$ | Curiosity never exceeds its configured strength |
| Curiosity suppression | $d_H \to 1 \Rightarrow w_C \to 0$ | Starvation silences curiosity |
| Full curiosity | $d_H = 0 \Rightarrow w_C = w_C^{\text{base}}$ | Well-fed agent has full curiosity |
| Sharpness | $\gamma$ controls transition steepness | Low $\gamma$: gradual; high $\gamma$: sharp switch |

The parameter $\gamma$ controls how the agent transitions between
exploration and survival regimes. With $\gamma = 1$ (linear), the
transition is smooth. With $\gamma = 4$, the transition is
nearly binary: the agent either explores or forages, with little
middle ground.

---

## 7. The Policy

The policy converts the modulated action scores $\psi(a)$ into a
probability distribution over actions.

### 7.1 Admissibility Masking

Before computing probabilities, actions that are physically
impossible are **masked**. An action is inadmissible if it would
move the agent into a non-traversable cell or out of bounds:

$$M(a) = \begin{cases} 1 & \text{if action } a \text{ is admissible} \\ 0 & \text{otherwise} \end{cases}$$

For movement actions, admissibility depends on the traversability
signal from the observation:

$$M(\text{UP}) = \begin{cases} 1 & \text{if } b_{\uparrow} > 0 \\ 0 & \text{otherwise} \end{cases}$$

CONSUME and STAY are always admissible ($M = 1$).

Masked actions receive a score of $-\infty$:

$$\tilde{\psi}(a) = \begin{cases} \psi(a) & \text{if } M(a) = 1 \\ -\infty & \text{otherwise} \end{cases}$$

### 7.2 Softmax (Boltzmann) Selection

The probability of selecting action $a$ is given by the softmax
function with **inverse temperature** $\beta = 1 / T$:

$$P(a \mid x_t, u_t, m_t) = \frac{\exp(\beta \cdot \tilde{\psi}(a))}{\sum_{a' \in \mathcal{A}} \exp(\beta \cdot \tilde{\psi}(a'))}$$

The temperature parameter $T$ (equivalently, inverse temperature
$\beta$) controls the exploration-exploitation balance:

| Regime | $\beta$ | Behavior |
|---|---|---|
| $T \to \infty$ ($\beta \to 0$) | Low | Near-uniform random |
| $T = 1$ ($\beta = 1$) | Moderate | Balanced stochastic |
| $T \to 0$ ($\beta \to \infty$) | High | Near-deterministic (argmax) |

Masked actions ($\tilde{\psi}(a) = -\infty$) receive probability
zero after the softmax, regardless of $\beta$.

### 7.3 Numerical Stability

The softmax is computed in a numerically stable form by subtracting
the maximum admissible score:

$$P(a) = \frac{\exp(\beta \cdot (\tilde{\psi}(a) - \psi_{\max}))}{\sum_{a'} \exp(\beta \cdot (\tilde{\psi}(a') - \psi_{\max}))}$$

where $\psi_{\max} = \max_{a : M(a)=1} \psi(a)$.

### 7.4 Selection Modes

Two selection modes are supported:

- **Sample mode:** Draw action from the probability distribution
  using a seeded random generator.
- **Argmax mode:** Select the action with highest probability
  (deterministically). Ties are broken by action ordering.

---

## 8. The Transition Function

The transition function updates the complete system state after
action execution. It operates in defined phases.

### 8.1 Phase Structure

Each timestep proceeds through four phases. The specific operations
in each phase depend on the system, but the phase ordering is fixed
by the framework:

**Phase 1: World Transition**

The world updates its own state in response to the selected action:

$$s_{t+1}^{\text{world}} = F_{\text{world}}(s_t^{\text{world}}, a_t)$$

This includes three sub-operations:

**1a. Resource regeneration.** Before the action is applied, each
eligible cell regenerates:

$$\widetilde{R}_i(t) = \min\!\bigl(R_i^{\max},\ R_i(t) + \alpha \cdot (R_i^{\max} - R_i(t))\bigr)$$

where $\alpha$ is the regeneration rate and $R_i^{\max}$ is the
cell's maximum resource capacity. In the AXIS implementation,
$R_i^{\max} = 1$ for all cells, so regeneration simplifies to:

$$\widetilde{R}_i(t) = \min(1,\ R_i(t) + \alpha)$$

**1b. Position update.** Movement actions update the agent position:

$$p_{t+1} = \begin{cases} p_t + \Delta(a_t) & \text{if } a_t \in \mathcal{A}_{\text{move}} \text{ and target is traversable} \\ p_t & \text{otherwise} \end{cases}$$

The movement outcome produces a binary signal $\mu_t$:

$$\mu_t = \begin{cases} 1 & \text{if } p_{t+1} \neq p_t \\ 0 & \text{otherwise} \end{cases}$$

**1c. Resource extraction.** For actions that consume resources
(e.g., CONSUME):

$$\Delta R_t^{\text{cons}} = \min(\widetilde{R}_{c_t}(t),\ c_{\max})$$

where $c_{\max}$ is the maximum consumable amount per step and
$c_t$ is the agent's current cell. The cell's resource is reduced
accordingly.

**Phase 2: Observation Update**

A new observation is produced from the post-action world state:

$$u_{t+1} = S(s_{t+1}^{\text{world}})$$

**Phase 3: Agent State Update**

The agent's internal state is updated based on the action outcome:

$$x_{t+1} = F_{\text{agent}}(x_t, a_t, \Delta R_t^{\text{cons}})$$

At minimum, this updates energy:

$$e_{t+1} = \text{clip}(e_t - c(a_t) + \kappa \cdot \Delta R_t^{\text{cons}},\ 0,\ E_{\max})$$

where $c(a_t)$ is the action cost and $\kappa$ is the
resource-to-energy conversion factor.

**Phase 4: Memory Update**

$$m_{t+1} = G_{\text{mem}}(m_t, u_{t+1})$$

The FIFO buffer appends the new observation and drops the oldest
if over capacity.

### 8.2 Action Cost Function

Each action has a defined energy cost:

$$c(a) = \begin{cases} c_{\text{move}} & \text{if } a \in \{\text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}\} \\ c_{\text{consume}} & \text{if } a = \text{CONSUME} \\ c_{\text{stay}} & \text{if } a = \text{STAY} \\ c_{\text{custom}} & \text{for system-defined actions} \end{cases}$$

### 8.3 Terminal Condition

An episode terminates when energy reaches zero:

$$e_{t+1} = 0 \implies \text{episode terminates with reason "energy\_depleted"}$$

The framework also enforces a maximum step count. If the agent
survives to step $T_{\max}$, the episode terminates with reason
"max_steps_reached."

---

## 9. The Execution Cycle

Each timestep follows a fixed sequence of operations:

```
Timestep t:
  1. Agent reads observation:     u_t = S(s_t^world)
  2. Agent selects action:        a_t ~ pi(psi(a) | x_t, u_t, m_t)
  3. World regenerates:           R_i(t) -> R_i(t) + alpha
  4. World applies action:        s_{t+1}^world = F_world(s_t^world, a_t)
  5. Framework produces new obs:  u_{t+1} = S(s_{t+1}^world)
  6. Agent transitions state:     x_{t+1} = F_agent(x_t, a_t, outcome)
  7. Memory updates:              m_{t+1} = G_mem(m_t, u_{t+1})
  8. Check termination:           if e_{t+1} = 0, stop
```

Note the timing: the agent **decides** on the pre-regeneration world
(step 1-2), but the action is **applied** to the post-regeneration
world (step 3-4). This means the agent's observation at decision
time does not include the regeneration that occurs before action
application.

This ordering produces a subtle but important dynamic: cells that
were empty when the agent decided may have gained resource by the
time the action is applied. The agent does not perceive this
regeneration -- it "misses" it.

---

## 10. The Three-Snapshot Mechanism

For visualization and analysis, the framework captures three
immutable snapshots of the world state per step:

| Snapshot | Timing | Contents |
|---|---|---|
| BEFORE | Before everything | World state the agent "saw" when deciding |
| AFTER_REGEN | After regeneration, before action | World state with regenerated resources |
| AFTER_ACTION | After action application | Final world state for this step |

This three-snapshot approach enables the visualization to show
exactly what changed during regeneration versus what changed during
action application -- essential for understanding the dynamics
when resource regeneration interacts with consumption.

---

## 11. Composing Agent Systems

The generic framework is designed for **incremental composition**.
Building a new system means:

1. **Define** the state space $\mathcal{X}$ (what the agent remembers).
2. **Choose** the observation model (which cells, which signals).
3. **Design** the drives $\mathcal{D}$ (what motivates the agent).
4. **Specify** the modulation functions $\phi_i$ (how drives
   influence actions).
5. **Set** the policy parameters (temperature, selection mode).
6. **Define** the transition function (energy costs, state updates).

Each of these choices is independent. You can change the drive
without changing the sensor. You can add a new drive without
modifying existing ones. You can change the policy from softmax to
argmax without touching the drives.

The reduction property guarantees backward compatibility: if
you design System B as an extension of System A, setting the
extension parameters to zero must recover System A's behavior
exactly. This property is verified by automated tests.

---

## 12. Summary Table

| Component | Symbol | Input | Output |
|---|---|---|---|
| Sensor | $S$ | World state $s_t^{\text{world}}$ | Observation $u_t \in \mathcal{U}$ |
| Memory | $G_{\text{mem}}$ | Previous memory $m_t$, new obs $u_{t+1}$ | Updated memory $m_{t+1}$ |
| Drive $i$ | $D_i$ | State $x_t$, obs $u_t$, memory $m_t$ | Activation $d_i(t) \in \mathbb{R}$ |
| Modulation $i$ | $\phi_i$ | Action $a$, obs $u_t$, memory $m_t$ | Score contribution $\in \mathbb{R}$ |
| Weight $i$ | $w_i$ | Drive activations | Weight $w_i(t) \in \mathbb{R}^+$ |
| Modulation system | $\Gamma$ | All drives, weights, obs | Score vector $\psi(a)$ for all $a$ |
| Policy | $\pi$ | Scores $\psi(a)$, mask $M(a)$ | Probability dist $P(a)$ |
| World transition | $F_{\text{world}}$ | World state, action | Updated world state |
| Agent transition | $F_{\text{agent}}$ | Agent state, action outcome | Updated agent state |

---

> **Next:** [System A -- The Hunger-Driven Forager](04-system-a.md) --
> The first concrete instantiation of this framework.
