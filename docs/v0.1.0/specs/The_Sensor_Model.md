# **System A – Sensor Model (Baseline Perception Definition)**

## 1. Scope and Design Constraints
This document defines the **sensory interface** between the agent and the environment.
The goal is to construct a **minimal, mechanistically grounded perception model** that:

- exposes only **local environmental information**
- avoids any **semantic abstraction** (e.g. “food”, “good region”)
- does not encode a **world model or predictive structure**
- is sufficient to support **experience-based adaptation**

The sensor model must be:

- strictly **local**
- **memoryless** (no temporal aggregation)
- directly derived from the **environmental state variables**

---

## 2. Locality Principle
The agent observes only a **local neighborhood** around its current position.

At time $t$, let the agent be located at position:

$$
p_t \in \mathcal{G}  
$$

The observation neighborhood is defined as:

$$ 
\mathcal{N}(p_t) = \{ c_t, c_{up}, c_{down}, c_{left}, c_{right} \}  
$$

where:

- $c_t$ is the current cell
- the remaining cells are the four direct neighbors

No information outside this neighborhood is accessible.

---

## 3. Per-Cell Sensory Representation
Each observable cell $j \in \mathcal{N}(p_t)$ is mapped to a local sensory vector:

$$
z_j(t) = \bigl( b_j(t), r_j(t) \bigr)  
$$

### 3.1 Traversability Signal

$$  
b_j(t) = \begin{cases}  
0 & \text{if } O_j = 1 \\
1 & \text{if } O_j = 0  
\end{cases}  
$$

Interpretation:

- $b_j = 0$: cell is blocked
- $b_j = 1$: cell is traversable

---

### 3.2 Resource Signal

$$ 
r_j(t) \in [0,1]  
$$

defined as a normalized measure of the currently available resource:

$$
r_j(t) = \frac{R_j(t)}{R_{\text{scale}}}  
$$

where:

- $R_j(t)$ is the current resource level of the cell
- $R_{\text{scale}} > 0$ is a fixed normalization constant

> Choose $R_{\text{scale}}$ such that $R_j(t)/R_{\text{scale}} \in [0,1]$ for all reachable states, or explicitly clip the resulting signal to $[0,1]$.
---

## 4. Full Observation Vector
The complete sensory input at time $t$ is:

$$
u_t =  
\bigl(  
b_c, r_c,  
b_{up}, r_{up},
b_{down}, r_{down},
b_{left}, r_{left},
b_{right}, r_{right}  
\bigr)  
$$

This vector fully defines the agent’s perception at time $t$.

---

## 5. Sensor Function
This section defines the sensor function $S$, which maps the full world state to the agent’s local observation.

---

### 5.1 Definition of the Sensor Function
The sensor function is defined as:

$$
S : s_t^{world} \rightarrow u_t  
$$

with:

$$
S : (\mathcal{E}_t, p_t) \rightarrow \mathbb{R}^d  
$$

where:

- $s_t^{world} = (\mathcal{E}_t, p_t)$: full world state
- $\mathcal{E}_t$: environment configuration (grid with cell states)
- $p_t$: agent position
- $u_t$: local observation vector

---

#### Key Property
The sensor function provides a **strictly local projection** of the world state.

- No global information is passed
- No absolute position is exposed
- No hidden state is inferred

---

### 5.2 Local Neighborhood
The observation is restricted to a fixed local neighborhood around the agent.

We define:

$$
\mathcal{N}(p_t) = \{c, up, down, left, right\}  
$$

where:

- $c$: current cell
- $up, down, left, right$: adjacent cells (von Neumann neighborhood)

---

#### Boundary Handling
For cells outside the grid:

- $b_j = 0$ (non-traversable)
- $r_j = 0$

---

### 5.3 Cell-Level Projection
Each observed cell $j \in \mathcal{N}(p_t)$ is mapped to a feature vector:

$$
z_j(t) = (b_j(t), r_j(t))  
$$

where:

#### **Traversability**

$$  
b_j(t) =  
\begin{cases}  
0 & \text{if cell is non-traversable} \\  
1 & \text{if cell is traversable}  
\end{cases}  
$$

This is derived from the obstacle configuration of the environment.

---

#### Resource Intensity

$$  
r_j(t) = \frac{R_j(t)}{R_{\text{scale}}}  
$$

where:

- $R_j(t)$: current consumable resource at cell (j)
- $R_{\text{scale}}$: normalization constant

---

#### Important Constraint
The sensor provides:

- current resource intensity only
- no information about:
    
    - maximum capacity $R_j^{\max}$
    - regeneration rate $\alpha_j$
    - future availability

---

### 5.4 Observation Vector Construction
The full observation vector is constructed by concatenation:

$$  
u_t =  
(b_c, r_c,
b_{up}, r_{up},
b_{down}, r_{down},
b_{left}, r_{left},
b_{right}, r_{right})  
$$

Thus:

$$ 
u_t \in \mathbb{R}^{10}  
$$

---

### 5.5 Interpretation
The sensor function represents a **minimal physical interface** between agent and environment.

It encodes:

- local interaction constraints $via (b_j)$
- locally available consumable intensity $via (r_j)$

---

#### What is NOT encoded
The sensor function does **not** provide:

- semantic labels (e.g. “food”, “obstacle”)
- explicit energy information
- global spatial structure
- predictive information

---

### 5.6 Design Principle
The sensor function is intentionally restricted to:

> **Local, instantaneous, physically interpretable quantities**

This ensures:

- no implicit world model
- no semantic shortcuts
- no leakage of global information

---

### 5.7 Role in the System
The observation vector is used as input to:

- episodic memory
- policy function
- drive modulation mechanisms

$$
u_t = S(s_t^{world})  
$$

---

### Why this matters
The definition of $S$ determines:

- what the agent can perceive
- what must be inferred
- what can emerge

If $S$ is too expressive:

- the agent receives hidden structure
- behavior becomes trivial

If $S$ is too weak:

- meaningful behavior may not emerge

This formulation provides a **minimal but sufficient interface** for the baseline system.

---

## 5. Accessibility Constraints
The agent does **not** have direct access to the following environmental variables:

- maximum resource capacity $R_i^{\max}$
- regeneration rate $\alpha_i$
- global spatial structure
- future resource states

Thus, the sensor exposes only the **instantaneous local state**, not the underlying environmental parameters.

---

## 6. Action Coupling
The sensory input is coupled to actions as follows:

- `CONSUME` depends only on the current cell:
    
    $$  
    (b_c, r_c)  
    $$
    
- Movement actions depend only on the corresponding neighbor:
    
    $$ 
    (b_{dir}, r_{dir})  
    $$
    

Invalid movements (into $b_j = 0$) fail according to the environment rules.

---

## 7. Absence of Derived Signals
The sensor model does **not** include:

- resource gradients
- direction-to-resource signals
- aggregated statistics
- semantic labels

All higher-order structure must emerge from:

- interaction with the environment
- internal state dynamics
- experience accumulation

---

## 8. Interpretation
The sensor model provides:

- minimal **local spatial awareness**
- direct access to **current resource availability**
- sufficient information to discriminate between:
    
    - depleted vs. resource-rich cells
    - traversable vs. blocked directions

At the same time, it enforces:

- absence of global knowledge
- absence of predictive modeling
- absence of semantic abstraction

---

## 9. Behavioral Implication
The sensor model alone does not enforce exploration or movement.

In regions where:

$$ 
r_c \approx r_{up} \approx r_{down} \approx r_{left} \approx r_{right}  
$$

the observation becomes locally symmetric.

Therefore:

- movement must arise from **policy dynamics**
- sustained exploration requires either:
    
    - stochasticity
    - or internal modulation (e.g. energy-driven behavior)

This ensures that adaptive behavior, if present, is not encoded in perception but must **emerge from the agent’s internal mechanisms**.

---

## 10. Summary
The sensor model defines:

- a strictly local perception field
- minimal physical observables (traversability + resource level)
- no access to latent environmental parameters

It is:

- sufficient for interaction-driven learning
- minimal with respect to information content
- consistent with the environmental model

while deliberately avoiding:

- world modeling
- semantic abstraction
- built-in exploration mechanisms

---
