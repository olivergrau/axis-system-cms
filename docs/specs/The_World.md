# System A – Environmental Model (Baseline World Definition)

## 1. Scope and Design Constraints
This document defines the external environment in which the baseline agent operates.
The goal is to construct a minimal, biologically plausible resource environment that:

- supports energy acquisition through local interaction
- enforces resource scarcity and regeneration
- does not require a global world model
- allows survival to emerge from local dynamics + experience

The environment must be:

- fully mechanistically defined
- discrete in space and time
- directly implementable in code

---

## 2. Spatial Structure

### 2.1 Grid Definition
The environment is defined as a 2D discrete grid:

$$  
\mathcal{G} = { (x, y) \mid x \in [0, W-1], y \in [0, H-1] }  
$$

Where:

- $W$ = grid width
- $H$ = grid height
    

Each grid cell represents a local resource patch.

---

### 2.2 Cell State
Each cell $i \in \mathcal{G}$ is defined by:

$$
C_i(t) = \left( R_i(t), R^{\max}_i, \alpha_i, O_i \right)  
$$

Where:

- $R_i(t) \in [0, R^{\max}_i]$  
    Current available resource at time $t$
    
- $R^{\max}_i \geq 0$
    Maximum resource capacity of the cell
    
- $\alpha_i \in [0, 1]$
    Regeneration rate
    
- $O_i \in {0, 1}$
    Obstacle flag
    
    - $O_i = 1$ → cell is non-traversable
    - $O_i = 0$ → cell is traversable

---

## 3. Resource Dynamics

### 3.1 Regeneration Model
Resources regenerate locally according to a bounded growth function:

$$
R_i(t+1) = R_i(t) + \alpha_i \cdot \left( R^{\max}_i - R_i(t) \right)  
$$

Constraints:

- $R_i(t+1) \leq R^{\max}_i$
- $R_i(t+1) \geq 0$

---

### 3.2 Interpretation

- Regeneration slows as the cell approaches capacity
- Fully depleted cells recover gradually
- Overexploitation leads to temporary local scarcity

This models a renewable but limited energy source.

---

## 4. Resource Consumption

### 4.1 Consumption Event
If the agent is located on cell $i$ and performs action `consume`, then:

$$
\Delta E = \min(R_i(t), c_{\max})  
$$

Where:

- $c_{\max}$ = maximum consumption per time step

Update:

$$
R_i(t) \leftarrow R_i(t) - \Delta E  
$$

---

### 4.2 Constraints

- $R_i(t) \geq 0$
- Consumption is partial, not exhaustive

---

### 4.3 Interpretation

- A cell cannot be depleted in a single step unless already low
- Repeated consumption reduces local resource availability
- Staying in place may be beneficial or harmful depending on regeneration

---

## 5. Spatial Resource Distribution

### 5.1 Static Resource Landscape
Each cell has fixed parameters:

- $R^{\max}_i$
- $\alpha_i$

These are initialized at $t = 0$ and remain constant over time.

---

### 5.2 Heterogeneity Requirement
To prevent trivial survival behavior, the environment must exhibit spatial heterogeneity:

$$
\exists i, j \in \mathcal{G} \quad \text{such that} \quad R^{\max}_i \neq R^{\max}_j  
$$

This creates:

- resource-rich regions
- resource-poor regions

---

### 5.3 Optional Generation Methods
The following methods are acceptable:

- clustered distributions (e.g. Gaussian blobs)
- noise-based fields (e.g. Perlin noise)
- manually defined regions

---

### 5.4 No Spontaneous Resource Emergence
No new resource nodes are created dynamically:

$$  
R^{\max}_i = \text{const}, \quad \alpha_i = \text{const}  
$$

This ensures:

- a stable environment topology 
- learnable spatial patterns

---

## 6. Obstacles

### 6.1 Definition
A cell is an obstacle if:

$$  
O_i = 1  
$$

Such cells:

- cannot be occupied
- cannot be traversed
- do not participate in resource dynamics

---

### 6.2 Movement Constraint
If the agent attempts to move into cell $j$ with:

$$
O_j = 1  
$$

then:

- the movement fails
- the agent remains in its current position

---

### 6.3 Design Constraint
Obstacle layouts must satisfy:

- no complete enclosure of the agent
- no requirement for global navigation

---

## 7. Temporal Dynamics

### 7.1 Time Model
The system evolves in discrete time steps:

$$
t = 0, 1, 2, \dots  
$$

Each time step consists of:

1. Environment update (resource regeneration)
2. Agent action execution
3. State transition

---

### 7.2 Update Order
At each time step:

1. Regeneration phase:  
    $$  
    R_i(t) \rightarrow R_i(t+1)  
    $$
    
2. Agent interaction phase:
    
    - movement
    - consumption

---

## 8. Locality Principle
The environment enforces strict locality:

- No global signals are available
- All relevant information is spatially local
- Resource availability is only accessible via direct interaction or local sensing

---

## 9. Minimal Guarantees for Viability
To ensure that survival is possible but not trivial, the environment must satisfy:

### 9.1 Energy Feasibility Condition
There must exist at least one region $S \subset \mathcal{G}$ such that:

$$
\sum_{i \in S} \alpha_i \cdot R^{\max}_i \geq E_{\text{consumption rate}}  
$$

This ensures that:

- sustained survival is theoretically possible
- but requires correct behavior

---
## 10. Position Transition Function

### 10.1 Definition
The environment defines a position transition function:

$$
T : \mathcal{G} \times \mathcal{A} \rightarrow \mathcal{G}
$$

which maps the current position $p_t$ and an action $a_t$ to the next position:

$$
p_{t+1} = T(p_t, a_t)
$$

---

### 10.2 Directional Mapping
Let $p_t = (x, y)$.

Define candidate positions:

$$
\begin{aligned}
p^{up} &= (x, y-1) \\
p^{down} &= (x, y+1) \\
p^{left} &= (x-1, y) \\
p^{right} &= (x+1, y)
\end{aligned}
$$

---

### 10.3 Movement Rule

$$
T(p_t, a_t) =
\begin{cases}
p^{dir} & \text{if } a_t \in \{\text{UP, DOWN, LEFT, RIGHT}\} \text{ and } O_{p^{dir}} = 0 \\
p_t & \text{if movement is blocked or } a_t \in \{\text{STAY, CONSUME}\}
\end{cases}
$$

---

### 10.4 Boundary Conditions
If a candidate position lies outside $\mathcal{G}$:

$$
p^{dir} \notin \mathcal{G}
$$

then the movement is invalid and:

$$
T(p_t, a_t) = p_t
$$

---

### 10.5 Interpretation

- Movement is purely local and deterministic
- Obstacles and boundaries enforce spatial constraints
- No stochasticity is introduced at the environment level
---

## 11. Summary
The environment is defined as:

- a discrete 2D grid
- with locally regenerating resources
- spatially heterogeneous capacity
- partial consumption mechanics
- static topology
- optional obstacles with local interaction only

This setup creates:

- resource gradients
- local scarcity and recovery
- a non-trivial survival problem

without introducing:

- global knowledge
- planning requirements
- explicit world models

---
