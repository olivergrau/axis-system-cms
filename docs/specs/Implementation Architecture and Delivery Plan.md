# System A Baseline – Implementation Architecture and Delivery Plan (Draft Structure)

---

## 1. Purpose and Scope
This document defines the **implementation architecture and delivery foundation** for **AXIS System A (Baseline)**.

Its purpose is to translate the existing conceptual and engineering specification into a **concrete, buildable system structure**, enabling:

- stepwise implementation
- controlled complexity growth
- reproducible and testable development
- decomposition into well-defined work packages

The document provides:

- a **structured architecture breakdown**
- a clearly defined **Minimal Viable Implementation (MVP)**
- a basis for **incremental delivery planning**

This document does **not** aim to:

- define a complete long-term architecture for future AXIS variants
- introduce generalized abstraction layers for all potential extensions
- fully specify advanced subsystems such as experiment orchestration or visualization

Instead, the focus is strictly on:

> building a **minimal, correct, and extensible baseline system** that can be implemented step by step without unnecessary complexity.

---

# 2. Architectural Goals and Guiding Principles
The implementation architecture of System A follows a set of strict engineering principles. These principles are not optional design preferences but **constraints that guide all decisions**.

## 2.1 Minimal but Complete System
The system must be:

- as small as possible
- but still fully functional

A working system is always preferred over a theoretically complete design that cannot be implemented reliably.

---

## 2.2 Separation of Concerns
Core behavioral logic and supporting infrastructure must remain clearly separated:

- runtime behavior must not depend on logging, visualization, or experiment logic
- supporting systems must not influence core decision-making

This ensures clarity, testability, and maintainability.

---

## 2.3 Test-Integrated Development
Testing is a **first-class concern**:

- every module must be testable in isolation
- invariants must be explicitly validated
- deterministic execution must be ensured where required

No component is considered complete without corresponding tests.

---

## 2.4 Determinism and Reproducibility
The system must support:

- deterministic execution under fixed seeds
- reproducible behavior across runs

Stochastic elements are allowed but must be **controlled and observable**.

---

## 2.5 Incremental Buildability
The architecture must support:

- stepwise implementation
- early execution capability
- visible progress after each work package

At every stage, the system should remain in a runnable state.

---

## 2.6 Extension Awareness without Premature Abstraction
The design must:

- avoid obvious architectural dead ends
- allow future extensions (e.g., additional drives, planning, richer memory)

However, it must **not**:

- introduce abstraction layers for features that do not yet exist
- generalize prematurely

---

## 2.7 Fail-Hard and Explicit State Handling
Invalid states or transitions must not be silently tolerated:

- inconsistencies should result in explicit failures
- system behavior must remain transparent and debuggable

---

## 2.8 No Hidden Intelligence
System A is strictly mechanistic:

- no implicit reasoning
- no hidden heuristics outside defined components

All behavior must emerge from explicitly defined mechanisms.

---

# 3. System Boundary and Architectural View
This section defines the **structural decomposition** of the system at a high level.

The architecture is divided into two clearly separated domains:

---

## 3.1 Core Runtime Architecture
The Core Runtime contains all components required to:

> execute a valid System A episode from start to termination.

It includes:

- world representation
- agent state
- sensory processing
- drive computation (hunger)
- decision pipeline (policy)
- transition function
- episode execution loop
- baseline memory handling

Characteristics:

- defines the **actual behavior of the agent**
- must be **fully functional in the MVP**
- must be **independent of supporting systems**

---

## 3.2 Supporting Engineering Architecture
The Supporting Engineering Architecture contains all components that:

> support execution, analysis, configuration, and testing, but do not define behavior.

It includes:

- configuration structures
- result and trace representations
- logging and observability mechanisms
- testing utilities and fixtures
- extension boundaries

Characteristics:

- must not influence core decision logic
- may be partially implemented in MVP form
- can evolve independently from the core runtime

---

## 3.3 Boundary Rules
The separation between both domains is strict:

- Core Runtime must not depend on:
    
    - logging
    - visualization
    - experiment frameworks

- Supporting components may:
    
    - observe runtime behavior
    - record outputs
    - configure parameters


but must **never modify core logic implicitly**.

---

## 3.4 Architectural Intent
This separation serves three purposes:

1. **Clarity**  
    Behavior and infrastructure are not mixed.
    
2. **Testability**  
    Core logic can be validated independently.
    
3. **Controlled Evolution**  
    Supporting systems can grow without destabilizing the core.

---

# 4. Core Runtime Architecture
Describes all components required for the **execution of System A behavior**.

## 4.1 World Representation

### 4.1.1 Design Principle
The world in System A is defined as a **deterministic, passive state container**.

It does not contain any behavioral logic, agent-specific semantics, or implicit dynamics.  
All state changes are applied exclusively through the **state transition function $F$**.

The world encodes only:

- spatial structure
- resource distribution
- static constraints

No notion of “meaning” (e.g., food, reward, desirability) is embedded in the world itself.

---

### 4.1.2 Spatial Structure
The environment is represented as a **finite two-dimensional grid**:

$$  
(x, y), \quad 0 \leq x < W,  0 \leq y < H  
$$

where:

- $W$ is the grid width
- $H$ is the grid height

The grid has **hard boundaries**. Positions outside the defined range are invalid.

No wrap-around or continuous space is considered in the baseline system.

---

### 4.1.3 Cell Representation
Each grid position contains exactly one **cell**, defined as:

```text
Cell:
    type: CellType
    resource_value: float
```

with:

```text
CellType ∈ { EMPTY, RESOURCE, OBSTACLE }
```

Constraints:

- `resource_value > 0` is only valid if `type == RESOURCE`
- `resource_value = 0` implies `type = EMPTY`
- OBSTACLE cells always have `resource_value = 0`

 $$
 0 \le resource\_value \le 1
$$
It represents the **relative amount of locally available resource**, independent of any implementation-specific scaling.

The `resource_value` represents a **continuous, locally available quantity** that can be partially consumed.

---

### 4.1.4 Resource Semantics (Strictly Physical Interpretation)
Resources are defined purely in terms of **available quantity**, without embedded meaning.

The normalization of `resource_value` to the interval $[0,1]$ ensures a consistent and model-aligned representation across all environments and implementations.

The world does not encode:

- whether a resource is “useful”
- whether it should be consumed
- any reward or value interpretation

The effect of interacting with a resource (e.g., energy gain) is defined exclusively in:

- the **agent model**
- the **state transition function $F$**

---

### 4.1.5 World State
The full world state is defined as:

```text
World:
    grid: 2D array of Cell
    width: int
    height: int
```

The world contains no hidden variables or implicit state.

All observable properties must be explicitly encoded in the grid.

---

### 4.1.6 Access Interface
The world provides minimal, side-effect-free access operations:

```text
get_cell(x, y) → Cell
set_cell(x, y, Cell)
is_within_bounds(x, y) → bool
```

These operations do not trigger any additional logic or state transitions.

---

### 4.1.7 World Initialization
World instances are generated deterministically:

```text
WorldGenerator(seed, config) → World
```

The configuration defines:

- grid dimensions
- initial resource distribution
- obstacle placement (optional in baseline)

The use of a fixed seed ensures:

- reproducibility
- testability
- comparability across runs

---

### 4.1.8 State Update Responsibility
The world does not update itself.

All changes to the world state occur exclusively within the **state transition function $F$**, including:

- resource consumption
- resource depletion
- optional resource regeneration (if enabled)

This enforces a strict separation between:

- **state representation (world)**
- **state evolution (transition function)**

---

### 4.1.9 Invariants
The following invariants must always hold:

- Each grid position contains exactly one valid cell
- No cell contains conflicting state (e.g., resource and obstacle simultaneously)
- Resource values are non-negative
- Agent position is always within bounds
- World state is fully explicit and deterministic
- Resource values are bounded: $0 \le resource\_value \le 1$
- Resource Value of 0 implies type = EMPTY
- $resource\_value \ge 0$ implies type = RESOURCE
- No implicit rescaling is allowed within the world state

---

## 4.2 Agent State

### 4.2.1 Design Principle
The agent in System A is defined as a **purely internal dynamical system**.

It does not possess:

- spatial properties (e.g., position)
- direct access to the world state
- implicit knowledge about the environment

All interaction with the world occurs exclusively through:

- sensory input $u_t$
- the state transition function $F$

The agent state encodes only **internal variables required for state evolution and decision-making**.

---

### 4.2.2 Separation from World State
The agent has **no intrinsic spatial representation**.

In particular:

- position is not part of the agent state
- spatial location is stored in the **world state**
- all spatial interactions are mediated through the transition function

This enforces a strict separation between:

- **internal state (agent)**
- **external state (world)**

---

### 4.2.3 Agent State Structure
The agent state at time $t$, denoted $a_t$, is defined as:

```text
AgentState:
    energy: float
    memory_state: MemoryState
```

---

### 4.2.4 Energy State
The variable `energy` represents the agent’s internal energy level.

Constraints:

$$ 
0 \leq \text{energy} \leq E_{\max}  
$$

where $E_{\max}$ is a fixed maximum capacity.

The energy level:

- decreases as a result of actions
- increases through interaction with resources
- directly influences the hunger drive

The exact update rules are defined in the state transition function $F$.

---

### 4.2.5 Memory State
The `memory_state` represents the agent’s internal memory $m_t$.

It is defined as:

> a **state snapshot**, not a reference to a memory component or system.

This distinction is critical:

- the agent state contains the **data representation of memory**
- the logic for updating memory is external

---

### 4.2.6 Memory Update Responsibility
Memory updates are not performed within the agent state itself.

Instead, memory evolves according to a dedicated update mechanism:

$$ 
m_{t+1} = M(m_t, u_t)  
$$

where:

- $M$ is the memory update function
- $u_t$ is the current sensory input

This update is applied as part of the **state transition function $F$**.

---

### 4.2.7 Observability Constraints
The agent state does not contain:

- explicit world information
- hidden references to the environment
- derived spatial knowledge beyond what is encoded in memory

All knowledge about the environment must originate from:

- past observations stored in `memory_state`
- current sensory input $u_t$

---

### 4.2.8 Minimality of the Baseline
The baseline agent state is intentionally minimal.

It includes only:

- energy (internal drive-relevant state)
- memory (experience accumulation)

It excludes:

- planning structures
- world models
- self-representations
- higher-order cognitive constructs

This ensures that any complex behavior arises from:

- interaction dynamics
- state evolution
- environmental structure

rather than pre-defined internal complexity.

---

### 4.2.9 Invariants
The following invariants must hold:

- Energy is bounded:

$$  
0 \leq \text{energy} \leq E_{\max}  
$$

- `memory_state` is always well-defined and consistent with its update rules
- Agent state contains no external references or implicit world dependencies
- All state variables are explicitly represented and serializable

---

## 4.3 Sensor / Observation Model

### 4.3.1 Design Principle
The sensor model in System A defines the **only perceptual interface** between the agent and the external world.

It is intentionally restricted to a **strictly local, memoryless, and non-semantic projection** of the current world state.

The sensor does not:

- expose global structure
- expose absolute position
- expose latent environmental parameters
- infer or derive higher-order signals

Its function is limited to providing the agent with the **instantaneous local state of its immediate surroundings**.

---

### 4.3.2 Role in the Architecture
The sensor model maps the full world state to the agent’s current observation:

$$ 
u_t = S(s_t^{world})  
$$

where:

- $s_t^{world}$ is the complete external world state
- $u_t$ is the local observation available to the agent at time $t$

This mapping is the only allowed information channel from world to agent.  
The agent has no direct access to the world state itself.

---

### 4.3.3 Local Observation Neighborhood
The baseline sensor observes a fixed **von Neumann neighborhood** around the current agent position in the world:

$$
\mathcal{N}(p_t) = \{c, up, down, left, right\}  
$$

This includes:

- the current cell
- the four directly adjacent cells

No cells outside this neighborhood are accessible.

---

### 4.3.4 Per-Cell Observation Structure
Each observed cell $j \in \mathcal{N}(p_t)$ is mapped to a two-component sensory vector:

$$
z_j(t) = \bigl(b_j(t), r_j(t)\bigr)  
$$

where:

- $b_j(t)$ is the **traversability signal**
- $r_j(t)$ is the **resource intensity signal**

This keeps the sensory interface minimal and physically interpretable.

---

### 4.3.5 Traversability Signal
The traversability signal is defined as:

$$  
b_j(t) =  
\begin{cases}  
1 & \text{if the cell is traversable} \\  
0 & \text{if the cell is blocked or invalid}  
\end{cases}  
$$

This signal allows the agent to distinguish between:

- locally reachable directions
- blocked directions
- boundary cells represented as non-traversable

The sensor does not provide any richer obstacle semantics beyond this binary constraint signal.

---

### 4.3.6 Resource Intensity Signal
The resource signal is defined as a normalized continuous quantity:

$$
r_j(t) \in [0,1]  
$$

It represents the **currently available local resource intensity** at the observed cell.

In the formal baseline model, the signal is defined as:

$$ 
r_j(t) = \frac{R_j(t)}{R_{\text{scale}}}  
$$

where $R_{\text{scale}} > 0$ is the normalization constant.

For the baseline implementation, this implies the following engineering rule:

- the sensor must output a value in $[0,1]$
    
- if the world already stores normalized resource values, the sensor may pass them through directly
    
- if the world uses a different internal numeric scale, normalization must be applied explicitly in the sensor layer

The sensor exposes only the **current local intensity**, not:

- maximum capacity
- regeneration rate
- future resource availability

---

### 4.3.7 Full Observation Vector
The complete observation vector is constructed by concatenating the five local cell vectors in fixed order:

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

This ordering must remain stable across the implementation, because downstream components depend on the positional interpretation of each entry.

---

### 4.3.8 Boundary Handling
For observed neighbor positions that lie outside the grid, the sensor must return:

$$ 
b_j = 0,\qquad r_j = 0  
$$

This ensures that out-of-bounds areas are represented exactly like blocked, non-resource cells from the perspective of action admissibility and local perception.

---

### 4.3.9 Accessibility Constraints
The sensor must not expose the following information:

- absolute position $p_t$
- global world structure
- distant cells
- $R_i^{\max}$
- $\alpha_i$
- future resource states
- derived gradients or directional summaries
- semantic labels such as “resource”, “obstacle”, or “good region”

The observation must remain a **local instantaneous projection**, not an interpreted or enriched representation.

---

### 4.3.10 Architectural Responsibility
The sensor model is a **pure projection component**.

It is responsible only for:

- reading the relevant local world state
- constructing the observation vector
- enforcing boundary handling
- applying normalization where required

It is not responsible for:

- decision logic
- action masking
- memory integration
- world updates
- inference of higher-order structure

This preserves the strict separation between:

- world representation
- perception
- decision-making

---

### 4.3.11 Invariants
The following invariants must hold:

- the observation is always defined as a 10-dimensional vector
- all traversability values satisfy:

$$  
b_j \in {0,1}  
$$

- all resource intensity values satisfy:
    

$$
r_j \in [0,1]  
$$

- observation order is fixed and stable
- out-of-bounds cells are represented as $(0,0)$
- no hidden or derived information is added by the sensor

---

### 4.3.12 Baseline Implication
The baseline sensor model provides enough information for:

- local movement constraints
- direct local resource sensitivity
- reactive coupling between hunger and local action preference

At the same time, it deliberately prevents:

- map-building through direct perception
- predictive navigation
- semantic world access
- information leakage from the world state

This keeps System A within its intended baseline regime:  
**local, reactive, mechanistic behavior under partial observability**.

---

## 4.4 Memory System (Baseline)

### 4.4.1 Design Principle
The memory system in System A provides the agent with a **persistent internal record of past observations**.

It is strictly:

- **episodic**
- **non-semantic**
- **non-spatially structured**
- **passive**

The memory does not construct or maintain:

- a world model
- spatial maps
- predictive structures
- abstract representations

It serves only as a **historical trace of sensory input**.

---

### 4.4.2 Role in the Architecture
Memory is part of the agent’s internal state:

$$  
m_t \subset a_t  
$$

It evolves over time according to:

$$  
m_{t+1} = M(m_t, u_t)  
$$

where:

- $m_t$ is the current memory state
- $u_t$ is the current observation
- $M$ is the memory update function

The update is applied within the **state transition function $F$**.

---

### 4.4.3 Memory Representation
In the baseline system, memory is represented as a **finite sequence of past observations**:

```text
MemoryState:
    observations: list[Observation]
```

where each element corresponds to:

$$ 
Observation = u_t \in \mathbb{R}^{10}  
$$

The memory therefore has the structure:

$$
m_t = [u_{t-k}, u_{t-k+1}, ..., u_t]  
$$

with $k$ being the memory horizon.

---

### 4.4.4 Memory Horizon
The memory is bounded by a fixed maximum size:

$$  
|m_t| \leq K  
$$

where $K$ is a configurable parameter.

When the capacity is exceeded:

- the oldest observation is removed
- the newest observation is appended

This results in a **sliding window mechanism**.

---

### 4.4.5 Memory Update Rule
The update function $M$ is defined as:

1. append current observation $u_t$
2. if capacity exceeded → remove oldest entry

Formally:

$$  
m_{t+1} = \text{truncate}_K(m_t \cup {u_t})  
$$

This update is:

- deterministic
- order-preserving
- free of interpretation

---

### 4.4.6 Content Constraints
Memory stores only:

- raw observation vectors $u_t$

Memory does not store:

- derived features
- aggregated statistics
- inferred structure
- action history (in baseline)
- world coordinates
- semantic labels

This ensures that memory remains a **pure record of perception**.

---

### 4.4.7 No Spatial Structure
The memory has **no spatial indexing**.

In particular:

- observations are not tied to coordinates
- no map-like structure is formed
- no alignment across time steps is performed

This prevents implicit construction of a world model.

---

### 4.4.8 No Predictive Capability
The memory system does not:

- extrapolate future states
- estimate resource regeneration
- compute gradients or trends

Any behavioral effect must emerge solely from:

- the interaction of memory content with policy
- the agent’s internal dynamics

---

### 4.4.9 Integration with Agent State
The memory is stored as part of the agent state:

```text
AgentState:
    energy: float
    memory_state: MemoryState
```

The memory state is:

- fully explicit
- serializable
- independent of implementation-specific objects

---

### 4.4.10 Invariants
The following invariants must hold:

- memory size is bounded:

$$  
|m_t| \leq K  
$$

- all entries are valid observation vectors:

$$
u_t \in \mathbb{R}^{10}  
$$

- ordering is strictly chronological
- no implicit transformations are applied
- memory contains no external references

---

### 4.4.11 Baseline Implication
The baseline memory system enables:

- short-term temporal continuity
- basic experience accumulation
- implicit behavioral bias through repeated exposure

At the same time, it deliberately prevents:

- explicit learning
- environment reconstruction
- planning or foresight
- structured knowledge formation

This ensures that System A remains:

> **a reactive, history-aware system without internal world modeling**

---

## 4.5 Drive Computation (Hunger Only)

### 4.5.1 Design Principle
The drive system defines the **motivational layer** of System A.

It is responsible for transforming:

- internal agent state
- current local observation

into **drive-specific action preferences**.

Drives are implemented as **independent, modular components**.  
Each drive can be added, removed, or replaced through configuration without changing the general decision pipeline.

This architectural choice is required because the baseline system is intended to remain extensible toward future multi-drive variants, while keeping the current implementation minimal.

---

### 4.5.2 Role in the Architecture
The drive system operates between:

- **Agent State + Observation**  
    and
    
- **Policy / Decision Pipeline**
    

Each drive $D_i$ receives the agent’s current internal state and observation and produces:

- a **drive activation**
- an **action contribution vector**

Formally:

$$
D_i : (a_t, u_t) \rightarrow \bigl(d_i(t), \mathbf{s}_i(t)\bigr)  
$$

where:

- $d_i(t)$ is the scalar activation of drive $i$
- $\mathbf{s}_i(t)$ is the drive-specific contribution to action preference

The final raw action score vector is then obtained by aggregating the contributions of all active drives. In the baseline system, only the Hunger Drive is active.

---

### 4.5.3 Drive Interface (Conceptual)
Each drive must implement the following conceptual interface:

```text
Drive:
    compute(agent_state, observation) ->
        activation: float
        action_contribution: vector[float]
```

Requirements:

- deterministic given identical inputs
- side-effect free
- no access to global world state
- no access to hidden environment variables

This keeps each drive fully local, explicit, and testable.

---

### 4.5.4 Modularity and Configuration
The set of active drives is defined through runtime configuration:

```text
DriveSystem:
    drives: list[Drive]
```

This is a **code-configurable modular design**, not a heavyweight plugin framework.

The baseline system instantiates exactly one drive:

- **Hunger Drive**

Future drives may later be introduced using the same interface, without redesigning the policy architecture.

---

### 4.5.5 Hunger Drive – Purpose
The Hunger Drive represents the agent’s internal need to maintain its energy level.

Its role is to:

- increase behavioral pressure under energy depletion
- couple this internal pressure to locally observed resource intensity
- bias action preferences toward resource-relevant actions

The Hunger Drive does not:

- plan
- predict future outcomes
- know the world state
- know where resources are beyond current observation

It is strictly reactive and local.

---

### 4.5.6 Hunger Activation Function
The hunger activation is derived from the agent’s current energy state:

$$
d_H(t) = 1 - \frac{E_t}{E_{\max}}  
$$

where:

- $E_t$ is the current internal energy
- $E_{\max}$ is the maximum energy capacity

Properties:

$$
0 \leq d_H(t) \leq 1  
$$

Interpretation:

- $d_H(t)=0$: no hunger pressure
- $d_H(t)=1$: maximal hunger pressure

This directly matches the baseline mathematical model.

---

### 4.5.7 Action Space Reference
The Hunger Drive computes contributions over the full baseline action space:

$$
\mathcal{A} = \{ \text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}, \text{CONSUME}, \text{STAY} \}  
$$

Its output vector must therefore always contain one contribution value per action in this fixed order.

---

### 4.5.8 Hunger Action Contribution Vector
The Hunger Drive produces an action contribution vector:

$$
\mathbf{s}_H(t)

\bigl(  
s_{up},  
s_{down},  
s_{left},  
s_{right},  
s_{consume},  
s_{stay}  
\bigr)  
$$

Each component expresses how strongly the current hunger state, together with the current local observation, biases the corresponding action.

---

### 4.5.9 Contribution Rules for Movement Actions
For movement actions, the contribution is given by the resource intensity in the corresponding neighboring cell:

$$  
s_{up}(t) = d_H(t)\cdot r_{up}(t)  
$$

$$
s_{down}(t) = d_H(t)\cdot r_{down}(t)  
$$

$$
s_{left}(t) = d_H(t)\cdot r_{left}(t)  
$$

$$
s_{right}(t) = d_H(t)\cdot r_{right}(t)  
$$

This preserves the direction-specific structure of the local observation and allows hunger to bias motion toward locally visible resource.

---

### 4.5.10 Contribution Rule for CONSUME
The `CONSUME` action is explicitly part of the action space and must be scored separately from `STAY`.

Its contribution is defined as:

$$
s_{consume}(t) = d_H(t)\cdot w_{consume}\cdot r_c(t)  
$$

where:

- $r_c(t)$ is the resource intensity at the current cell
- $w_{consume} > 0$ is the consumption priority weight

This weighting factor gives directly available local resource a stronger behavioral salience than equally strong neighboring opportunity, if desired by configuration.

---

### 4.5.11 Contribution Rule for STAY
The baseline system treats `STAY` differently from resource-directed actions.

The Hunger Drive does not assign a positive attraction score to `STAY`. Instead, passivity is explicitly suppressed under hunger:

$$ 
s_{stay}(t) = - \lambda_{stay}\cdot d_H(t)  
$$

where:

- $\lambda_{stay} \ge 0$ is the stay-suppression parameter
    

This ensures that inactivity becomes progressively less likely as hunger increases.

---

### 4.5.12 Important Behavioral Rule for CONSUME
The action `CONSUME` always remains part of the action space.

It is **not masked solely because the current cell contains no resource**.

Therefore:

- if $r_c(t)=0$, then:

$$
s_{consume}(t)=0  
$$

- but the action remains formally selectable by the policy

This preserves the baseline system’s mechanistic character: ineffective local consumption attempts remain possible without introducing special-case action removal.

---

### 4.5.13 No World Knowledge and No Action Validity Logic
The Hunger Drive does not:

- check world boundaries
- check obstacles
- perform action masking
- infer future reward
- estimate regeneration
- use global spatial structure

These concerns are handled elsewhere:

- action admissibility in the policy / decision pipeline
- world evolution in the transition function

The Hunger Drive is strictly responsible only for **local motivational scoring**.

---

### 4.5.14 Aggregation Behavior
In the baseline system, only one drive is active, so aggregation reduces to:

$$
\mathbf{s}_{total}(t) = \mathbf{s}_H(t)  
$$

However, the architecture is intentionally prepared for future extension:

$$
\mathbf{s}_{total}(t) = \sum_i \mathbf{s}_i(t)  
$$

for multiple active drives.

This keeps the baseline implementation aligned with the longer-term modular drive concept without over-engineering the current system.

---

### 4.5.15 Invariants
The following invariants must hold:

- hunger activation is bounded:
    

$$
0 \leq d_H(t) \leq 1  
$$

- movement and consume contributions are non-negative whenever resource intensity is non-negative
- stay contribution is non-positive whenever (\lambda_{stay} \ge 0)
- the action contribution vector has fixed dimensionality equal to (|\mathcal{A}|)
- contribution computation is deterministic for identical inputs
- no hidden world variables are consulted

---

### 4.5.16 Baseline Implication
The Hunger Drive creates the first explicit coupling between:

- internal deficit
- current local perception
- action preference

This produces behavior that is:

- reactive
- locally resource-sensitive
- modulated by internal need

without introducing:

- planning
- search strategies
- prediction
- semantic understanding

The result is a minimal but effective motivational system for the baseline agent.

---

## 4.6 Policy and Decision Pipeline

### 4.6.1 Design Principle
The policy defines the **decision mechanism** of the agent.

It transforms:

- aggregated drive-based action scores

into:

- a concrete action selection
    

The policy is:

- stateless
- fully determined by its inputs and configuration
- separated from drive computation

It does not compute motivations itself, but operates purely on the outputs of the drive system.

---

### 4.6.2 Role in the Architecture
The policy receives:

- aggregated action scores $\mathbf{s}_{total}(t)$
- current observation $u_t$ (for masking only)

and produces:

$$ 
a_t \in \mathcal{A}  
$$

The policy implements a **unified decision pipeline**, independent of selection mode.

---

### 4.6.3 Input to the Policy

$$  
\mathbf{s}_{total}(t) \in \mathbb{R}^{|\mathcal{A}|}  
$$

In the baseline system:

$$  
\mathbf{s}_{total}(t) = \mathbf{s}_H(t)  
$$

---

### 4.6.4 Action Masking
Before probability computation, invalid actions are masked.

Masking rules:

- movement into non-traversable cells → masked
- masked actions receive:

$$
s_j(t) = -\infty  
$$

- `CONSUME` is never masked
- `STAY` is never masked

Masking is derived solely from:

$$
b_j(t)  
$$

---

### 4.6.5 Softmax Transformation
The masked score vector is converted into a probability distribution:

$$
P(a_j \mid t) =  
\frac{\exp\left(s_j(t)/\tau\right)}  
{\sum_k \exp\left(s_k(t)/\tau\right)}  
$$

where:

- $\tau > 0$ is the temperature parameter

---

### 4.6.6 Temperature Parameter
The temperature $\tau$ is a **configurable parameter**.

It controls the sharpness of the distribution:

- $\tau \to 0$: near-deterministic
- $\tau = 1$: baseline
- $\tau \to \infty$: near-uniform

---

### 4.6.7 Selection Modes
The system supports two selection modes:

---

#### (1) Stochastic Mode (`sample`)

$$
a_t \sim \text{Categorical}(P(\cdot \mid t))  
$$

Characteristics:

- default execution mode
- introduces variability
- reflects probabilistic behavior

---

#### (2) Deterministic Mode (`argmax`)

$$
a_t = \arg\max_a P(a \mid t)  
$$

Used for:

- debugging
- validation
- comparison with worked examples

---

### 4.6.8 Tie-Breaking Strategy (Deterministic Mode)
If multiple actions share the same maximum probability:

- one action is selected **uniformly at random among all maxima**

This randomness:

- avoids structural bias
- is controlled by the global random seed

Implication:

> Deterministic mode is **reproducible**, but not strictly deterministic in tie cases.

---

### 4.6.9 Unified Policy Pipeline
The policy must always follow the same sequence:

1. receive action scores
2. apply masking
3. compute Softmax probabilities
4. apply selection mode (`sample` or `argmax`)

There are **no alternative decision paths** depending on mode.

---

### 4.6.10 Determinism and Reproducibility
All stochastic elements are controlled by a global random seed.

This includes:

- sampling in stochastic mode
- tie-breaking in deterministic mode

Given identical:

- inputs
- parameters
- seed

the system must produce identical trajectories.

---

### 4.6.11 Output Contract
The policy outputs exactly one action:

```text
Action ∈ {UP, DOWN, LEFT, RIGHT, CONSUME, STAY}
```

The selected action is:

- valid under masking
- consistent with the selection mode

---

### 4.6.12 No Additional Logic
The policy does not:

- modify action scores (except masking)
- introduce heuristics
- access agent internals
- perform reasoning
- incorporate memory

All behavioral structure must originate from:

- drive system

---

### 4.6.13 Invariants
The following must hold:

- probabilities sum to 1:

$$  
\sum_j P(a_j \mid t) = 1  
$$

- masked actions have zero probability
- probabilities are non-negative
- selection respects the chosen mode
- policy is stateless

---

### 4.6.14 Baseline Implication
The policy ensures:

- consistent transformation from drive signals to behavior
- controlled stochasticity
- reproducibility under fixed seeds

The resulting behavior is:

- locally reactive
- probabilistically structured
- free of planning and prediction

---

## 4.7 Transition Engine (State Transition Function F)

### 4.7.1 Role and Responsibility
The **Transition Engine** is the central runtime component responsible for executing the **state transition function**:

$$  
\Sigma_{t+1} = F(\Sigma_t, a_t)  
$$

It defines the complete and deterministic evolution of the system state for a single simulation step.

The Transition Engine operates on the full system state:

- agent state $x_t$
- memory state $m_t$
- world state $s^{world}_t$
- current observation $u_t$
- selected action $a_t$

and produces:

- updated agent state $x_{t+1}$
- updated memory state $m_{t+1}$
- updated world state $s^{world}_{t+1}$
- next observation $u_{t+1}$
- termination signal ( done )

The Transition Engine is the **only component allowed to modify system state**.

It represents the **mechanistic “physics” of System A**, ensuring that all state changes occur in a controlled, explicit, and reproducible manner.

---

### 4.7.2 Architectural Design Decision
The Transition Engine is implemented as a **central orchestrator with a fixed, phase-based execution structure**.

It is explicitly **not** implemented as:

- a generic pipeline framework with dynamically configurable stages
- a distributed mutation model across multiple interacting objects
- a deeply abstracted inheritance-based OOP hierarchy

Instead, the design follows these principles:

- **Deterministic execution order**: all phases are executed in a strictly defined sequence
- **Explicit state transitions**: no hidden or implicit state mutations
- **Result-based design**: all outputs are constructed explicitly from inputs
- **Fail-hard behavior**: invalid transitions are not silently corrected
- **Minimal abstraction**: only introduce modular boundaries where they improve clarity and testability

This design ensures consistency with the formal system definition and avoids premature abstraction while remaining extensible.

---

### 4.7.3 Internal Structure
The Transition Engine delegates specific responsibilities to a small set of dedicated submodules:

- **WorldTransitionModule**
- **ObservationBuilder**
- **AgentTransitionModule**
- **MemoryModule**
- **TerminationCriterion**

The Transition Engine itself is responsible for:

- enforcing execution order
- coordinating data flow between modules
- constructing the resulting state
- ensuring consistency and validity

Submodules are **purely functional in behavior** and must not introduce side effects outside their defined scope.

---

### 4.7.4 Transition Input and Output

#### Input
A single transition step receives:

- `agent_state_t`
- `memory_state_t`
- `world_state_t`
- `observation_t`
- `action_t`
- `step_index`

The observation ( u_t ) is explicitly passed into the Transition Engine and represents the perception used to select the action.

---

#### Output
The Transition Engine produces:

- `agent_state_t1`
- `memory_state_t1`
- `world_state_t1`
- `observation_t1`
- `done`

Additionally, a **transition trace** is produced internally and exposed via the runtime result structures (formalized in Section 5.2).

---

### 4.7.5 Execution Phases
The transition is executed as a **strictly ordered sequence of phases**.

---

#### Phase 1: World Regeneration
The world state is updated through environment dynamics independent of the agent.

Typical operations:

- resource regeneration
- environmental updates (if defined)

$$  
s^{world}_t \rightarrow s^{world,*}_t  
$$

This phase must be executed **before** applying the agent’s action.

---

#### Phase 2: Action Application (World Interaction)
The selected action $a_t$ is applied to the world.

Typical operations:

- movement of the agent within the grid
- interaction with the current cell
- resource consumption (if applicable)

This produces an intermediate world state:

$$
s^{world,*}_t \rightarrow s^{world,**}_t  
$$

Invalid actions (e.g., movement into blocked cells) are handled explicitly and must not be silently corrected.

---

#### Phase 3: Observation Construction
The next observation is constructed from the updated world state:

$$
u_{t+1} = O(s^{world,**}_t)  
$$

The ObservationBuilder derives the local perception of the agent from the world.

---

#### Phase 4: Agent State Update
The agent state is updated based on:

- the previous agent state $x_t$
- the executed action $a_t$
- the resulting world interaction

Typical operations:

- energy update (including action cost and consumption gain)
- internal state adjustments    

$$
x_t \rightarrow x_{t+1}  
$$

The agent state update must be **fully deterministic and explicit**.

---

#### Phase 5: Memory Update
The memory is updated with the newly observed state:

$$
m_{t+1} = m_t \cup {u_{t+1}}  
$$

The memory module appends the observation without modifying past entries.

No hidden information (e.g., rewards or energy deltas) is stored in memory.

---

#### Phase 6: Termination Evaluation
The system evaluates whether the episode terminates:

$$  
done = T(x_{t+1})  
$$

For the baseline system, termination is typically triggered by:

- energy depletion $e_{t+1} \leq 0$

---

### 4.7.6 Determinism and Reproducibility
The Transition Engine must be fully deterministic under fixed inputs and configuration.

Determinism includes:

- identical input states and actions produce identical outputs
- world regeneration follows deterministic rules or seeded randomness
- no hidden global state

This is a strict requirement for:

- debugging
- validation
- reproducibility of experiments

---

### 4.7.7 Error Handling and Constraints
The Transition Engine follows a **fail-hard strategy**:

- invalid state transitions must raise explicit errors
- no silent corrections or implicit fallbacks are allowed
- state invariants must be enforced at each phase

Examples:

- invalid positions outside grid bounds
- inconsistent world state
- negative energy below allowed thresholds (unless defined as terminal)

---

### 4.7.8 Integration into the Execution Loop
The Transition Engine is invoked once per simulation step within the execution loop.

It assumes that:

- action selection has already been completed by the Policy
- the current observation $u_t$ is available

The Execution Engine is responsible for:

- iteratively calling the Transition Engine
- collecting results
- managing episode lifecycle

---

## 4.8 Episode Execution Loop

### 4.8.1 Role and Responsibility
The **Episode Execution Loop** is responsible for executing the temporal progression of System A.

It orchestrates the interaction between:

- the **Policy** (decision-making)
- the **Transition Engine** (state evolution)

over a sequence of discrete time steps.

Each iteration of the loop corresponds to one application of the state transition function:

$$ 
\Sigma_{t+1} = F(\Sigma_t, a_t)  
$$

The Execution Loop defines:

- how actions are selected from observations
- how transitions are applied over time
- how episodes are initialized and terminated
- how results are collected and structured

The loop is the **only component responsible for temporal sequencing**.  
Time in System A is defined purely as the ordered application of transition steps.

---

### 4.8.2 Architectural Design Decision
The Episode Execution Loop is implemented as a **deterministic, step-based orchestrator** with explicit separation between:

- **decision phase** (Policy)
- **transition phase** (Transition Engine)

Key design principles:

- **Strict separation of concerns**:
    
    - Policy computes actions
    - Transition Engine updates state
        
- **Explicit step structure**:
    
    - each iteration is a well-defined unit (Step)
        
- **Deterministic control flow**:
    
    - no hidden control logic or implicit transitions
        
- **Centralized orchestration**:
    
    - all sequencing logic resides in the Execution Loop
        
- **Trace-first design**:
    
    - all steps are captured and aggregated into structured results

The Execution Loop does not contain domain logic of:

- world dynamics
- agent updates
- memory behavior

These are exclusively handled by the Transition Engine and its submodules.

---

### 4.8.3 Execution Flow
For each step $t$, the following sequence is executed:

---

#### **Step t**

1. **Observation Availability**
    
    The current observation $u_t$ is available as part of the system state.

---

2. **Action Selection (Policy Phase)**
    
    The Policy computes the action:
    
    $$  
    a_t = \pi(u_t, x_t)  
    $$
    
    The Policy may use stochastic or greedy sampling, as defined in the configuration.

---

3. **State Transition (Transition Phase)**
    
    The Transition Engine is invoked:
    
    ```text
    transition_engine.step(
        agent_state_t,
        memory_state_t,
        world_state_t,
        observation_t,
        action_t,
        step_index
    )
    ```
    
    This produces:
    
    - updated agent state $x_{t+1}$
    - updated memory $m_{t+1}$
    - updated world $s^{world}_{t+1}$
    - next observation $u_{t+1}$
    - termination signal `done`

---

4. **Result Capture**
    
    The outcome of the step is captured as a structured **Step Result**:
    
    - input state references
    - selected action
    - resulting state
    - termination flag

    
    Step-level trace data is accumulated for later aggregation.

---

5. **Termination Check**
    
    If `done == True`, the episode terminates immediately.

---

6. **State Update**
    
    The system state is advanced:
    
    $$  
    \Sigma_t \rightarrow \Sigma_{t+1}  
    $$
    
    The next iteration uses:
    
    - $x_{t+1}$
    - $m_{t+1}$
    - $s^{world}_{t+1}$
    - $u_{t+1}$


---

### 4.8.4 Step Structure
Each iteration of the Execution Loop is represented as a **Step**.

A Step encapsulates:

- input observation $u_t$
- selected action $a_t$
- resulting next observation $u_{t+1}$
- state transition outputs
- termination status

The Step serves as the **atomic unit of simulation** and forms the basis for:

- debugging
- analysis
- reproducibility

The formal structure of Step results is defined in Section 5.2.

---

### 4.8.5 Episode Initialization
Before the first step ($t = 0$), the system is initialized as follows:

---

#### Initial World State
The world is initialized according to configuration:

- grid size
- resource distribution
- optional randomness (seeded)

---

#### Initial Agent State
The agent state is initialized with:

- position (as defined by configuration)
- initial energy level $e_0$

The initial energy is **parameterized** and must be provided via configuration.

---

#### Initial Memory State
The memory is initialized as empty:

$$ 
m_0 = \emptyset  
$$

---

#### Initial Observation
The initial observation is constructed via:

$$  
u_0 = O(s^{world}_0)  
$$

This ensures consistency with the sensor model and avoids implicit inputs.

---

### 4.8.6 Termination Handling
An episode terminates under either of the following conditions:

---

#### 1. System-Driven Termination
The Transition Engine signals termination:

```text
done == True
```

For the baseline system, this typically corresponds to:

$$  
e_t \leq 0  
$$

---

#### 2. Maximum Step Limit
A configurable upper bound is enforced:

```text
t >= max_steps
```

This acts as a **safety constraint** to prevent infinite execution.

---

Termination is evaluated **after each step**.

---

### 4.8.7 Result Collection and Aggregation
The Execution Loop is responsible for collecting all Step results and aggregating them into an **Episode Result**.

Responsibilities include:

- accumulating ordered Step results
- preserving full transition trace
- ensuring consistency of recorded states
- exposing final episode summary

The exact structure of:

- `StepResult`
- `EpisodeResult`
- `RunResult`

is defined in Section 5.2.

The Transition Engine itself does not perform aggregation.

---

### 4.8.8 Determinism and Reproducibility
The Execution Loop must preserve determinism across runs.

This includes:

- deterministic Policy behavior under fixed seeds
- deterministic Transition Engine behavior
- consistent initialization
- ordered execution without concurrency

Given identical:

- configuration
- initial state
- random seeds

the system must produce identical:

- step sequences
- state trajectories
- termination behavior

---

### 4.8.9 Control and Constraints
The Execution Loop enforces strict control over system execution:

- no parallel execution of steps
- no skipping of phases
- no implicit state mutation outside defined components

The loop must remain:

- simple
- transparent
- fully traceable

It is intentionally designed as a **minimal but explicit control structure**.

---

# 5. Supporting Engineering Architecture
Describes components that support execution but are not part of the core behavior logic.

## 5.1 Configuration Model

### 5.1.1 Role and Responsibility
The **Configuration Model** defines all parameters required to instantiate and execute System A.

It is the **single source of truth** for:

- environment setup
- agent initialization
- policy behavior
- execution constraints

The configuration must enable:

- reproducibility
- controlled experimentation
- deterministic execution (under fixed seeds)

The Configuration Model is strictly **declarative**.  
It does not contain any executable logic.

---

### 5.1.2 Design Principles
The configuration follows these principles:

---

#### 1. Completeness
All runtime-relevant parameters must be externally configurable.

No hidden defaults inside:

- Policy
- Transition Engine
- Execution Loop

If a parameter influences behavior, it must exist in the configuration.

---

#### 2. Determinism Control
All sources of randomness must be controllable:

- global seed
- world generation randomness
- policy sampling randomness

This is essential for:

- debugging
- worked examples
- validation

---

#### 3. Explicitness over Convenience
No implicit coupling or derived magic values.

Example:

- energy decay is explicitly defined
- not derived indirectly from other parameters

---

#### 4. Modular Structure
Configuration is structured according to system components:

- world
- agent
- policy
- execution

This mirrors the architecture and avoids cross-contamination.

---

#### 5. Stability for Extension
Even though System A is minimal, the configuration must allow future extension:

- additional drives
- more complex environments
- alternative policies

Without breaking existing structure.

---

### 5.1.3 High-Level Structure
The configuration is composed of the following sections:

```text
SystemConfig
├── general
├── world
├── agent
├── policy
├── execution
```

Each section is strictly scoped.

---

### 5.1.4 General Configuration
Defines global parameters.

```text
general:
    seed: int
```

---

#### Parameters

- **seed**
    
    - Global random seed
    - Must be used consistently across:
        
        - world generation
        - policy sampling

---

### 5.1.5 World Configuration
Defines the environment.

```text
world:
    grid_width: int
    grid_height: int
    initial_food_density: float
    food_energy_value: float
    respawn_enabled: bool
    respawn_probability: float
```

---

#### Parameters

- **grid_width / grid_height**
    
    - Size of the 2D grid
        
- **initial_food_density**
    
    - Fraction of cells initialized with food
        
- **food_energy_value**
    
    - Energy gained when consuming food
        
- **respawn_enabled**
    
    - Whether food can reappear
        
- **respawn_probability**
    
    - Probability per cell per step

---

### 5.1.6 Agent Configuration
Defines the internal state initialization.

```text
agent:
    initial_position: (int, int)
    initial_energy: float
    max_energy: float
    energy_decay_per_step: float
```

---

#### Parameters

- **initial_position**
    
    - Starting position on the grid
        
- **initial_energy**
    
    - Initial energy level ( e_0 )
        
- **max_energy**
    
    - Upper bound for energy
        
- **energy_decay_per_step**
    
    - Energy loss per time step

---

### 5.1.7 Policy Configuration
Defines action selection behavior.

```text
policy:
    type: "softmax"
    temperature: float
    tie_breaking: bool
    allow_stochastic: bool
```

---

#### Parameters

- **type**
    
    - Currently fixed to `"softmax"` in baseline
        
- **temperature**
    
    - Controls exploration vs. exploitation
        
- **tie_breaking**
    
    - Enables random selection among equal scores
        
- **allow_stochastic**
    
    - If false → greedy selection
    - If true → sampling from distribution

---

### 5.1.8 Execution Configuration
Defines episode constraints.

```text
execution:
    max_steps: int
```

---

#### **Parameters**

- **max_steps**
    - Hard upper bound on episode length

---

### 5.1.9 Configuration Object Definition
The configuration can be represented as a structured object:

```python
@dataclass
class SystemConfig:
    general: GeneralConfig
    world: WorldConfig
    agent: AgentConfig
    policy: PolicyConfig
    execution: ExecutionConfig
```

Each sub-config is independently typed.

---

### 5.1.10 Validation Requirements
The configuration must be validated before execution.

Minimum checks:

---

#### World

- grid size > 0
- 0 ≤ food_density ≤ 1
- food_energy_value > 0

---

#### Agent

- 0 < initial_energy ≤ max_energy
- energy_decay_per_step > 0

---

#### Policy

- temperature > 0

---

#### Execution

- max_steps > 0

---

#### Cross-Component Constraints

- energy_decay_per_step < food_energy_value

---

### 5.1.11 Deterministic Initialization Contract
Given:

- identical configuration
- identical seed

The following must be identical across runs:

- initial world state
- initial agent state
- action sequence (if stochastic but seeded)

This is **non-negotiable** for:

- worked examples
- debugging
- scientific credibility

---

### 5.1.12 Known Limitations
This configuration model deliberately excludes:

- dynamic parameter adaptation
- learning-related parameters
- multiple drives
- environment complexity (terrain, obstacles, etc.)

These will be introduced in future system versions.

---

## 5.2 Result and Trace Structures

### 5.2.1 Purpose and Design Goal
The Result and Trace Structures define the **formal runtime output model** of System A.

Their purpose is to provide:

- explicit and structured outputs for all execution levels
- full traceability of decision-making and state evolution
- compatibility with debugging, testing, replay, and later analysis
- strict separation between:
    
    - **runtime behavior**
    - **observability**
    - **aggregation**

The baseline system must not return only raw actions or loosely structured logs.  
Instead, runtime execution must produce a hierarchy of **well-defined result objects**.

These structures are a core architectural element of the system and not an optional engineering convenience. They are required by the execution model, the transition model, and the policy design already defined in the specification.

---

### 5.2.2 Design Principles
The Result and Trace Structures follow the principles below.

#### Explicitness
All relevant execution outputs must be represented explicitly.  
No critical runtime information may exist only implicitly in logs or in transient local variables.

#### Hierarchical Structure
Results are defined on multiple levels:

- **decision / transition level**
- **step level**
- **episode level**
- **run level**

These levels must remain structurally distinct.

#### Separation of Concerns
The result model must distinguish clearly between:

- **what was decided**
- **what physically happened**
- **what the step produced overall**
- **what was aggregated at episode or run level**

This prevents conceptual mixing between policy, transition, and execution control.

#### Deterministic Reconstructability
Given the structured result objects, the execution history of an episode must be reconstructable in a deterministic and inspectable way.

#### Read-Only Semantics
Result and trace objects represent **recorded outputs**, not mutable runtime control structures.  
They are intended for inspection, aggregation, serialization, and replay.

---

### 5.2.3 Result Hierarchy Overview
The baseline system defines the following runtime output hierarchy:

```text
RunResult
    └── EpisodeResult
            └── StepResult
                    ├── DecisionTrace
                    └── TransitionTrace
```

This hierarchy mirrors the execution model:

- a **Run** contains one or more episodes
- an **Episode** contains an ordered sequence of steps
- a **Step** contains:
    
    - the policy decision trace
    - the transition trace
    - the consolidated step-level outcome


This structure is fully aligned with the baseline execution model defined earlier.

---

### 5.2.4 Decision Trace

#### Role
The **Decision Trace** captures the full internal output of the policy for one decision step.

It exists to make action selection fully inspectable and testable.

This directly reflects the policy requirements from the engineering pre-specification, which requires a structured decision result rather than only a bare selected action.

---

#### Minimum Required Content
A Decision Trace must contain at minimum:

- current observation $u_t$
- relevant policy input state
- drive activations
- raw action scores
- action admissibility / masking information
- effective action scores after masking
- action probabilities
- selection mode
- selected action
- tie-breaking information, if applicable

---

#### Interpretation
The Decision Trace answers the question:

> **Why was this action selected at this step?**

It records the full causal chain from:

- policy input
- through scoring
- through masking
- through probability computation
- to final selection

---

#### Baseline-Specific Constraint
In System A (Baseline), the Decision Trace reflects:

- exactly one active drive: Hunger
- no memory influence on action selection
- no planning
- no world-model-based reasoning

Thus, the Decision Trace must not contain inferred or higher-order structures that do not exist in the baseline system.

---

### 5.2.5 Transition Trace

#### Role
The **Transition Trace** captures the full state evolution produced by the Transition Engine for one step.

It exists to make the physical state transition fully inspectable and debuggable.

This is directly required by the pre-specification of the Transition Engine, which mandates explicit phase visibility and a complete transition trace.

---

#### Minimum Required Content
A Transition Trace must contain at minimum:

- executed action $a_t$
- observation before transition $u_t$
- observation after transition $u_{t+1}$
- world state snapshot before transition
- world state snapshot after regeneration
- world state snapshot after action application
- agent state before transition
- agent state after transition
- memory state before update
- memory state after update
- resource interaction / consumption details
- termination flag

---

#### Interpretation
The Transition Trace answers the question:

> **What actually changed in the system when this action was executed?**

It records the stepwise causal evolution of the full system state through the ordered transition phases.

---

#### Baseline-Specific Constraint
The Transition Trace must reflect the actual baseline transition structure:

1. world regeneration
2. action application
3. observation update
4. agent update
5. memory update
6. termination evaluation

No hidden transition logic may exist outside what is representable in the trace.

---

### 5.2.6 Step Result

#### Role
The **Step Result** is the atomic execution output of one simulation step.

It combines:

- the **Decision Trace**
- the **Transition Trace**
- the consolidated step-level metadata needed by the execution model

The Step Result is the primary unit for:

- debugging
- replay
- stepwise inspection
- episode aggregation

This matches the execution model, where a step is the smallest full execution unit.

---

#### Minimum Required Content
A Step Result must contain at minimum:

- step index $t$
- selected action
- decision trace
- transition trace
- position before transition
- position after transition
- energy before transition
- energy after transition
- termination flag

---

#### Relationship to Traces
The Step Result does not replace the Decision Trace or Transition Trace.  
Instead, it acts as the **step-level container** that references or embeds them.

This preserves a clean separation:

- Decision Trace = decision internals
- Transition Trace = state evolution internals
- Step Result = one complete runtime step

---

#### Baseline Implication
In the baseline system, the Step Result must be sufficient to:

- reconstruct the local agent trajectory
- inspect observation-to-action behavior
- inspect energy dynamics
- inspect memory growth
- inspect termination timing

This is also necessary for later visualization and replay support.

---

### 5.2.7 Episode Result

#### Role
The **Episode Result** represents the structured output of one complete episode.

It aggregates the ordered Step Results produced during episode execution and exposes a compact summary of the episode outcome.

The Episode Result is the natural output of the Episode Execution Loop.

---

#### Minimum Required Content
An Episode Result must contain at minimum:

- episode identifier
- ordered sequence of Step Results
- number of executed steps
- termination reason
- final energy state
- final position
- final memory summary
- lightweight aggregate statistics

---

#### Aggregate Statistics
The Episode Result should expose basic episode-level aggregates, such as:

- survival length
- action frequency summary
- total number of successful consume events
- total number of failed consume attempts, if tracked
- terminal condition type

These aggregates must be derived from step-level data, not from a separate hidden execution path.

---

#### Interpretation
The Episode Result answers the question:

> **How did one complete realization of the system unfold, and how did it end?**

---

#### Constraint
The Episode Result must preserve the full ordered Step Results.  
It must not reduce an episode to summaries only.

This is required for:

- replay
- debugging
- post-hoc analysis
- worked-example validation

---

### 5.2.8 Run Result

#### Role
The **Run Result** represents the structured output of one complete run.

A run contains one or more independent episodes executed under the same effective configuration and seed context, as defined by the execution model.

---

#### Minimum Required Content
A Run Result must contain at minimum:

- run identifier
- effective run configuration reference or snapshot
- random seed
- ordered collection of Episode Results
- run-level summary statistics

---

#### Run-Level Summary
The Run Result should expose lightweight aggregate metrics across episodes, such as:

- number of episodes
- mean episode length
- termination reason distribution
- mean final energy
- aggregate action distribution
- aggregate resource interaction statistics

These summaries are intended to support baseline experimentation and analysis, but they must remain lightweight and reproducible. This is consistent with the experimentation and observability requirements in the engineering pre-specification.

---

#### Interpretation
The Run Result answers the question:

> **What happened across all episodes executed under one coherent run configuration?**

---

### 5.2.9 Required Structural Relationships
The result model must enforce the following relationships:

- every `StepResult` contains exactly one `DecisionTrace`
- every `StepResult` contains exactly one `TransitionTrace`
- every `EpisodeResult` contains an ordered sequence of `StepResult`
- every `RunResult` contains an ordered sequence of `EpisodeResult`

Ordering must be preserved at all levels.

This ordering is not merely a convenience. It defines the reconstructable temporal structure of execution.

---

### 5.2.10 Minimal Serialization Readiness
All result and trace structures must be designed such that they are:

- fully serializable
- stable in structure
- independent of transient runtime references
- suitable for JSON / JSONL conversion where appropriate

This requirement follows from the observability and persistence model already defined in the engineering pre-specification.

This means:

- no hidden pointers to live engine objects
- no implicit dependence on mutable runtime services
- no unserializable closures or callbacks embedded in result objects

---

### 5.2.11 Minimal Summary vs Full Detail
The baseline architecture must support both:

- **full-detail runtime records**
- **lightweight summaries**

The rule is:

- traces preserve detail
- results preserve structure
- summaries provide convenience

But summaries must never replace the full traceable structures internally.

This is especially important because later replay, visualization, and testing depend on preserved step-level detail.

---

### 5.2.12 Architectural Boundary
The Result and Trace Structures belong to the **Supporting Engineering Architecture**, but they are tightly coupled to the core runtime contract.

They must therefore remain:

- structurally aligned with runtime behavior
- independent from visualization logic
- independent from experiment orchestration logic
- independent from logging backend details

In other words:

- the runtime produces structured results
- logging may persist them
- visualization may consume them
- experimentation may aggregate them

but none of those external concerns may redefine the result model implicitly.

---

### 5.2.13 Baseline Scope and Restraint
The baseline system must define only the result structures actually needed for:

- execution
- debugging
- testing
- replay
- lightweight aggregation

It must **not** introduce elaborate enterprise-style event schemas, telemetry taxonomies, or overly abstract trace frameworks.

The goal is:

> **minimal but complete structured runtime output**

This is consistent with the broader architectural principle of extension awareness without premature abstraction.

---

### 5.2.14 Summary
The Result and Trace Structures provide the formal runtime output model of System A.

They define a strict hierarchy:

- **DecisionTrace** for policy internals
- **TransitionTrace** for state evolution internals
- **StepResult** for one atomic execution step
- **EpisodeResult** for one complete episode
- **RunResult** for one coherent run

Together, these structures ensure:

- full traceability
- deterministic reconstructability
- support for debugging and testing
- compatibility with replay and later experimentation
- clean separation between runtime behavior and supporting infrastructure


---

## 5.3 Logging and Observability

### 5.3.1 Role and Responsibility
The **Logging and Observability subsystem** provides structured visibility into the execution of System A.

Its purpose is to:

- enable **debugging of step-by-step behavior**
- support **analysis of agent trajectories**
- ensure **reproducibility and traceability**
- allow **inspection of internal decision processes**

Observability is strictly **read-only**:

- it must not influence execution
- it must not modify system state

---

### 5.3.2 Design Principles

---

#### 1. Trace-first, Logs-second
The primary source of truth is:

- `StepResult`
- `EpisodeResult`

Logging is a **derived representation** of this data.

Important consequence:  
No information should exist _only_ in logs.

---

#### 2. Structured over Textual
Logs must be:

- structured
- machine-readable

Free-form logs are allowed only for:

- debugging
- human readability

---

#### 3. Configurable Granularity
Observability must support multiple levels:

- OFF
- EPISODE
- STEP
- DEBUG

This prevents:

- performance overhead
- excessive data volume

---

#### 4. Deterministic Logging
Given the same run:

- logs must be identical
- ordering must be stable

No asynchronous or unordered logging.

---

#### 5. Minimal Intrusion
Logging must not:

- clutter core logic
- introduce coupling between components

---

### 5.3.3 Observability Levels

```text
OFF       → no logging
EPISODE   → summary per episode
STEP      → per-step structured logging
DEBUG     → extended internal diagnostics
```

---

#### Level: EPISODE
Logs:

- total steps
- termination reason
- final energy
- basic statistics

Use case:

- batch runs
- quick evaluation

---

#### Level: STEP
Logs per step:

- position
- action
- energy before/after
- observation summary

Use case:

- trajectory inspection
- behavior validation

---

#### Level: DEBUG
Includes:

- policy scores per action
- probability distributions
- tie-breaking decisions
- intermediate transition values

Use case:

- debugging policy anomalies
- validating mathematical correctness

---

### 5.3.4 Log Structure
Logs must follow a structured schema.

---

#### Episode Log Entry

```json
{
  "episode_id": 1,
  "total_steps": 87,
  "termination_reason": "energy_depleted",
  "final_energy": 0.0
}
```

---

#### Step Log Entry

```json
{
  "step": 12,
  "position": [4, 7],
  "action": "MOVE_UP",
  "energy_before": 23.0,
  "energy_after": 22.0,
  "consumed": false
}
```

---

#### Debug Log Entry (Extended)

```json
{
  "step": 12,
  "action_scores": {
    "MOVE_UP": 0.2,
    "MOVE_DOWN": 0.1,
    "MOVE_LEFT": 0.3,
    "MOVE_RIGHT": 0.3,
    "CONSUME": 0.1
  },
  "softmax_probabilities": {
    "MOVE_UP": 0.19,
    "MOVE_DOWN": 0.17,
    "MOVE_LEFT": 0.22,
    "MOVE_RIGHT": 0.22,
    "CONSUME": 0.20
  },
  "selected_action": "MOVE_RIGHT"
}
```

---

### 5.3.5 Integration Points
Logging is integrated at two key points:

---

#### 1. Execution Loop (Primary Hook)
After each step:

```text
StepResult → Logging Layer
```

The Execution Loop is responsible for:

- forwarding StepResults
- triggering log emission

---

#### 2. Policy (Optional Debug Hook)
For DEBUG level only:

- action scores
- probability distributions

Must be exposed via:

- structured return data
- not side-effect logging

---

### Important Constraint
The Policy must not log directly.

Otherwise:

- tight coupling
- inconsistent logging behavior

---

### 5.3.6 Output Targets
Logging must support multiple output targets:

---

#### 1. Console

- human-readable
- primarily for debugging

---

#### 2. File (JSONL recommended)

- one entry per line
- append-only
- suitable for analysis

Example:

```text
logs/run_001.jsonl
```

---

#### **3. In-Memory Collector**

- used during execution
- supports later aggregation
- feeds into `RunResult`

---

### Design Opinion
Start with:

👉 JSONL + in-memory

Skip:

- databases
- external logging systems

That’s overkill for this stage.

---

### 5.3.7 Logging Configuration
Extend the configuration model:

```text
logging:
    level: "OFF" | "EPISODE" | "STEP" | "DEBUG"
    output_console: bool
    output_file: bool
    output_path: str
```

---

#### Parameters

- **level**
    
    - defines granularity

- **output_console**
    
    - enable console logs

- **output_file**
    
    - enable file output

- **output_path**
    
    - target file location

---

### 5.3.8 Performance Considerations
Logging introduces overhead:

- serialization cost
- I/O operations
- memory usage

Mitigation:

- disable logging in performance runs
- buffer file writes
- avoid large payloads

---

### Critical Tradeoff
There is a tension between:

- **observability**
- **performance**

You cannot maximize both.

For System A:

- favor observability during development  
- favor performance during scaling

---

### 5.3.9 Determinism and Logging
Logging must not introduce:

- timing differences
- ordering changes

Requirements:

- synchronous execution
- fixed ordering of log entries

---

### 5.3.10 Minimal Implementation Scope
For the first implementation, logging must support:

- STEP level logging (mandatory)
- JSONL file output (mandatory)
- console output (optional)
- DEBUG fields (optional but recommended)

Anything beyond that is deferred.

---

## 5.4 Test Support and Fixtures

### 5.4.1 Purpose and Role
The **Test Support and Fixtures** section defines the engineering structures required to make System A reliably testable.

Its purpose is to ensure:

- deterministic verification of core runtime behavior
- efficient construction of controlled test scenarios
- reproducible debugging of edge cases
- direct validation against the formal baseline specification
- support for both isolated unit tests and integrated end-to-end tests

Testing is not treated as an afterthought. It is a **first-class architectural constraint**, consistent with the guiding principle of test-integrated development already established for the implementation architecture.

---

### 5.4.2 Design Principles
The testing support model follows the principles below.

### Deterministic First
Where deterministic behavior is expected, tests must use:

- fixed seeds
- explicitly constructed world states
- explicitly defined agent states
- explicitly defined observations

This is essential because the baseline system contains controlled stochasticity in policy selection and tie-breaking, but still requires reproducibility under fixed configuration and seed.

#### Explicit Scenario Construction
Tests must not depend primarily on ad hoc random world generation.

Instead, they should rely on:

- small handcrafted worlds
- explicit agent initialization
- explicit expected outcomes

This is especially important for worked-example verification and transition debugging.

#### Layered Testing Support
The test support architecture must enable testing at multiple levels:

- isolated component tests
- interaction tests across modules
- step-level execution tests
- episode-level end-to-end tests

This mirrors the modular system architecture and the execution hierarchy already defined.

#### Minimal but Reusable Fixtures
Fixtures must remain small, explicit, and reusable.

The baseline system does not need a large industrial test harness. It needs a compact and reliable set of scenario builders and reference fixtures that cover the critical behavioral regimes.

---

### 5.4.3 Scope of Test Support
The test support layer must provide practical support for validating the following categories:

#### 1. Structural Correctness
Examples:

- world dimensions are valid
- positions remain within bounds
- memory capacity is respected
- result structures are well formed

#### 2. Mathematical / Behavioral Correctness
Examples:

- hunger activation is computed correctly
- action scores match the formal baseline equations
- masking removes invalid movement actions
- Softmax probabilities are valid and sum to 1
- energy update follows the specified transition rules

#### 3. Temporal Correctness
Examples:

- transition phases occur in the correct order
- memory stores the post-transition observation
- episode termination occurs at the correct step
- max-step limit is enforced

#### 4. Reproducibility
Examples:

- identical configuration and seed yield identical trajectories
- tie-breaking is reproducible under fixed seed
- stochastic sampling remains reproducible across runs

These requirements are all directly implied by the pre-specification and the architecture already defined.

---

### 5.4.4 Test Support Architecture
The system should provide a lightweight but explicit testing support layer, consisting of:

- **reference fixtures**
- **test world builders**
- **state builders**
- **execution helpers**
- **assertion helpers**

This support layer belongs to the **Supporting Engineering Architecture** and must not be coupled into runtime behavior.

---

### 5.4.5 Reference Fixtures
Reference fixtures are predefined, reusable test scenarios used to validate known baseline behaviors.

At minimum, the baseline system should provide fixtures for the following cases:

#### Fixture A: Empty Local Neighborhood
A small world in which:

- the current cell is traversable
- all neighboring cells are traversable
- no local resource is present

Purpose:

- validate no-signal action scoring
- validate STAY suppression under hunger
- validate stochastic distribution in low-information states

This corresponds directly to the kind of regime analyzed in the worked examples.

---

#### Fixture B: Current-Cell Resource
A small world in which:

- the agent stands on a resource-bearing cell
- neighboring cells are empty

Purpose:

- validate CONSUME prioritization
- validate consumption-to-energy transfer
- validate local depletion behavior

This fixture should support direct comparison against the immediate-consumption worked example.

---

#### Fixture C: Directional Neighbor Resource
A small world in which:

- the current cell is empty
- at least one neighboring cell contains visible resource
- resource strengths differ across directions

Purpose:

- validate direction-specific movement scoring
- validate masking interaction with local observation
- validate that local gradients affect action probabilities correctly

---

#### Fixture D: Blocked Movement Case
A small world in which:

- one or more neighboring directions are blocked
- local resource values may still vary

Purpose:

- validate action masking
- validate zero probability for inadmissible movement actions
- validate consistency between traversability signals and policy output

This is especially important because masking is explicitly part of the decision pipeline in the engineering pre-specification.

---

#### Fixture E: Energy Depletion Trajectory
A controlled scenario with:

- no successful resource interaction
- repeated movement or action execution
- fixed initial energy

Purpose:

- validate monotonic depletion
- validate terminal condition timing
- validate episode termination behavior

This directly supports the depletion dynamics worked examples and the execution model.

---

### 5.4.6 Test World Builders
The test support layer should provide a **TestWorldBuilder** or equivalent helper to construct explicit world states for tests.

Its purpose is to create small deterministic worlds without relying on procedural generation.

The builder should support at minimum:

- setting grid size
- placing traversable empty cells
- placing resource cells with explicit resource values
- placing obstacle cells
- placing the agent at an explicit position

The builder must produce a fully valid world state that satisfies all world invariants defined by the architecture.

The builder is not part of runtime execution. It exists solely to reduce test boilerplate and improve clarity of test cases.

---

### 5.4.7 State Builders
In addition to world fixtures, the test support layer should provide explicit helpers for constructing agent-side state.

At minimum:

- **AgentStateBuilder**
- **MemoryStateBuilder**
- optional **ObservationBuilder test helper**

These builders should support:

- explicit initial energy
- explicit memory contents
- explicit empty or pre-populated memory
- explicit observation construction where direct policy testing is required

This is important because many policy tests do not require a full execution loop. They require only:

- a valid agent state
- a valid observation
- a deterministic configuration

The design must therefore support isolated policy testing without forcing end-to-end setup every time. This is fully consistent with the modular decomposition of policy, transition, and execution already established.

---

### 5.4.8 Execution Test Helpers
The testing support layer should provide lightweight helpers for executing controlled runtime scenarios.

Typical helpers may include:

- run exactly one policy decision
- execute exactly one transition
- execute exactly one full step
- execute one full episode under fixed configuration
- execute a run with a fixed seed

The purpose of these helpers is not to introduce a second execution model.  
They must simply expose the existing runtime architecture in a test-friendly way.

Examples of valid usage:

- verify one `DecisionTrace`
- verify one `TransitionTrace`
- verify one `StepResult`
- verify episode termination after a known number of steps

---

### 5.4.9 Assertion Helpers
To keep tests precise and readable, the support layer should provide a small set of reusable assertion helpers.

At minimum, helpers should support assertions such as:

- probabilities sum to 1
- masked actions have zero probability
- selected actions are admissible
- energy stays within bounds
- memory capacity is not exceeded
- positions remain valid
- ordered results are temporally consistent

These helpers reduce repetitive test code and make it easier to express architectural invariants directly.

---

### 5.4.10 Required Testing Levels
The test support layer must enable the following test levels.

#### Unit-Level Tests
For isolated components such as:

- Hunger Drive
- Policy masking
- Softmax transformation
- World transition logic
- Agent energy update
- Memory update
- termination criterion

These are essential because the architecture intentionally separates concerns and expects each module to be testable in isolation.

---

#### Integration-Level Tests
For interaction between multiple components, such as:

- Policy + DecisionTrace
- TransitionEngine + TransitionTrace
- ExecutionLoop + StepResult
- ObservationBuilder + world consistency

These validate that modules work together correctly, not just in isolation.

---

#### End-to-End Episode Tests
For full episodes under fixed configuration and seed.

These tests should validate:

- correct sequencing of steps
- consistent state evolution
- correct termination behavior
- stable episode result generation

---

#### Reproducibility Tests
The system must include tests that verify:

- same seed, same config → identical output
- different seeds can produce different trajectories where stochasticity is active

This is non-negotiable for a system whose behavioral interpretation depends on controlled stochasticity.

---

### 5.4.11 Baseline Fixture Restraint
The baseline system should keep its fixture set intentionally compact.

It should **not** attempt to provide fixtures for every conceivable future extension.

Specifically, baseline fixtures should not assume:

- multi-drive interactions
- learning
- planning
- complex environment semantics
- experiment orchestration
- visualization dependencies

Fixtures must remain aligned with the actual baseline scope:

- one drive
- local perception
- no planning
- no world model
- deterministic transition logic with controlled stochastic action selection

---

### 5.4.12 Serialization and Stability of Fixtures
Fixtures and test helpers should be designed such that:

- they are stable across repeated runs
- they do not depend on external runtime side effects
- they produce valid state structures identical to those used in real execution

Where useful, reference fixtures may also be serializable to simple configuration-like formats for reuse in regression testing.

This is especially helpful for preserving canonical baseline scenarios over time.

---

### 5.4.13 Architectural Boundary
Test Support and Fixtures are part of the **Supporting Engineering Architecture**.

They may:

- construct runtime objects
- invoke runtime components
- verify runtime outputs

But they must not:

- alter runtime logic
- redefine core behavior
- introduce alternative execution semantics

There must be exactly one runtime system.  
Test support exists to exercise and validate that system, not to simulate a parallel one.

---

### 5.4.14 Summary
The Test Support and Fixtures layer provides the practical engineering foundation for validating System A.

It ensures that the baseline implementation can be tested through:

- deterministic reference fixtures
- explicit world and state builders
- reusable execution helpers
- invariant-oriented assertion helpers
- direct comparison with worked examples

Together, these elements support:

- reliable unit testing
- structured integration testing
- reproducible end-to-end validation
- long-term regression safety

without introducing unnecessary testing infrastructure complexity.

---

## 5.5 Extension Boundaries

### 5.5.1 Purpose and Role
The **Extension Boundaries** define how System A can evolve beyond the baseline while preserving:

- architectural integrity
- determinism and reproducibility
- conceptual clarity of the model

They specify:

- which components are **intended to be replaceable or extendable**
- which parts are **structurally fixed in the baseline**
- how extensions must interact with the system

The goal is not maximum flexibility, but **controlled evolvability**.

---

### 5.5.2 Design Philosophy
The extension model follows three core principles:

---

#### 1. Replace Components, Not the System
Extensions should occur by replacing or extending **well-defined components**, not by modifying:

- the execution loop
- the global control flow
- the system contracts

---

#### 2. Preserve the Core Contracts
All extensions must respect:

- state transition contract $\Sigma_{t+1} = F(\Sigma_t, a_t)$
- step-based execution model
- trace and result structure
- configuration-driven initialization

If these break, the system becomes inconsistent.

---

#### 3. Minimal Surface, Strong Boundaries
Only a small number of extension points are allowed.

Each extension point must:

- have a clearly defined interface
- be independently testable
- avoid hidden coupling to other components

---

### 5.5.3 Primary Extension Points
The architecture defines the following extension boundaries.

---

#### 1. Policy (Decision Mechanism)

**Replaceable Component**
The Policy can be replaced with alternative implementations, such as:

- alternative scoring mechanisms
- rule-based policies
- learned policies (future)
- hybrid decision systems

---

#### Contract
A Policy must:

- accept current observation $u_t$ and agent state $x_t$
- produce:
    
    - selected action $a_t$
    - optional decision trace (for DEBUG)

---

#### Constraint
Policy must not:

- modify world state
- update memory
- bypass action masking rules defined by the system

---

#### Observation
This is the **most natural extension point** for future evolution.

---

### 5.5.4 Transition Engine (State Dynamics)

**Extendable Component**
The Transition Engine defines system dynamics and can be extended to support:

- more complex environments
- additional state variables
- richer interaction rules
- multiple entities (future)

---

#### Contract
The Transition Engine must:

- implement:

$$  
\Sigma_{t+1} = F(\Sigma_t, a_t)  
$$

- produce a complete and valid next state
- generate a consistent `TransitionTrace`

---

#### Constraint
It must not:

- introduce hidden side effects
- alter execution ordering
- depend on external mutable state

---

#### Critical Note
This is the **most dangerous extension point**.

If modified carelessly, it can:

- break determinism
- invalidate worked examples
- introduce subtle bugs

---

### 5.5.5 World Model (Environment Representation)

**Replaceable / Extendable Component**
The world representation can evolve from:

- simple grid → structured environments → continuous spaces

Possible extensions:

- obstacles and terrain types
- resource types
- non-uniform distributions
- dynamic environments

---

#### Contract
The world must:

- provide a valid observation via the sensor model
- support all required transition operations
- remain internally consistent

---

#### Constraint
The world must not:

- expose hidden information to the policy
- bypass the observation model

---

#### Important
The **sensor model is part of the boundary**:

- You can change the world  
- But the agent only sees what the sensor exposes

---

### 5.5.6 Agent State and Drives

**Extendable Component**
The agent can be extended with additional internal mechanisms, such as:

- additional drives (multi-drive system)
- internal variables
- adaptive thresholds
- learning signals

---

#### **Contract**
The agent state must:

- remain fully contained in $x_t$
- be updated only through the Transition Engine
- remain serializable and traceable

---

#### Constraint
No hidden state outside:

- agent state
- memory
- world state

---

#### Forward Compatibility
This is where:

- AXIS multi-drive systems
- emotion-like modulators
- internal feedback systems

will later plug in.

---

### 5.5.7 Memory System

**Replaceable / Extendable Component**
The memory system can evolve from:

- simple episodic storage → structured memory → semantic layers

Possible extensions:

- capacity limits
- filtering strategies
- decay mechanisms
- indexing / retrieval logic

---

#### Contract
Memory must:

- store information derived from observations
- not alter past entries
- be updated only during transition

---

#### Constraint
Memory must not:

- directly influence execution outside policy input
- introduce non-deterministic retrieval behavior (unless controlled)

---

### 5.5.8 Sensor Model (Observation Function)

**Replaceable Component**
The observation function:

$$ 
u_t = O(s^{world}_t)  
$$

can be extended to support:

- larger perception radius
- different modalities
- partial observability variations

---

#### Contract
The sensor model must:

- depend only on world state
- produce deterministic observations (given state)

---

#### Constraint
No leakage of:

- hidden world state
- future information

---

### 5.5.9 Configuration Model

**Extendable Component**
The configuration system must support:

- new parameters for extended components
- backward compatibility with baseline configs

---

#### **Contract**

- new parameters must be explicit
- defaults must be well-defined
- validation must be updated accordingly

---

### Constraint
Do not overload existing parameters with new meaning.

---

### 5.5.10 Logging and Observability
**Extendable Component**

Logging can be extended to:

- richer debug traces
- additional metrics
- visualization hooks

---

#### Contract

- logging remains derived from runtime data
- no influence on execution

---

#### Constraint
No logic must depend on logging output.

---

### 5.5.11 Fixed Components (Non-Extensible Core)
The following elements are intentionally **not extension points**:

---

#### 1. Execution Loop
Must remain:

- step-based
- sequential
- deterministic

---

#### 2. State Transition Contract

$$ 
\Sigma_{t+1} = F(\Sigma_t, a_t)  
$$

This is fundamental and must not change.

---

#### 3. Result and Trace Model

- `StepResult`
- `EpisodeResult`
- `RunResult`

These define the system’s observability backbone.

---

#### Why this matters
If you change these:

- you break reproducibility
- you invalidate tests
- you lose comparability between system versions

---

### 5.5.12 Extension Anti-Patterns
The architecture explicitly forbids:

---

#### 1. Hidden Global State
No:

- global caches
- implicit shared memory
- side-channel communication

---

#### 2. Policy Bypassing Transitions
Policy must not:

- directly change state
- simulate transitions internally

---

#### 3. Parallel or Asynchronous Step Execution
No:

- concurrent transitions
- out-of-order execution

---

#### 4. Implicit Coupling Between Components
No:

- direct access from policy to world internals
- memory modifying policy behavior outside defined inputs

---

### 5.5.13 Evolution Path (Guidance)
The architecture supports a natural evolution path:

---

#### **Stage 1 (Baseline)**

- single drive (hunger)
- simple grid world
- local observation
- softmax policy

---

#### **Stage 2**

- multiple drives
- richer world dynamics
- more complex scoring

---

#### **Stage 3**

- learning-based policy
- adaptive internal state
- structured memory

---

#### **Stage 4**

- multi-agent systems
- emergent coordination
- complex environments

---

#### Important
Each stage must:

- preserve execution semantics
- remain testable with fixtures
- remain reproducible under controlled conditions

---

### 5.5.14 Summary
The Extension Boundaries define a system that is:

- **closed at the core**
- **open at the edges**

They ensure that System A can evolve through:

- component replacement
- controlled extension
- explicit configuration

while preserving:

- determinism
- traceability
- architectural clarity

The system is not designed to be infinitely flexible.  
It is designed to be **predictably extensible**.

---

# 6. MVP Implementation Cut

## 1. Purpose of the MVP
The MVP shall deliver the **smallest complete, correct, and testable implementation** of System A (Baseline) that executes full episodes from initialization to termination while preserving the architectural and conceptual constraints of the baseline model.

Its purpose is not to provide the full long-term AXIS engineering ecosystem, but to establish a **working mechanistic runtime core** that is reproducible, inspectable, and suitable for incremental AI-assisted implementation.

---

## 2. What the MVP must prove
The MVP must prove the following:

### 2.1 End-to-End Runtime Correctness
The system can execute a complete episode from:

- initialization
- initial observation
- repeated decision and transition steps
- up to termination or max-step stop

using the real runtime architecture of System A.

### 2.2 Mechanistic Behavioral Integrity
The produced behavior is generated only through the explicitly defined baseline mechanisms:

- local observation
- hunger-based drive computation
- policy-based action selection
- state transition dynamics
- energy update
- memory update

and not through hidden heuristics or implicit reasoning.

### 2.3 Correct World-Agent Separation
The implementation preserves the strict architectural separation between:

- world state
- agent state
- observation
- memory
- policy
- transition logic

so that the agent never has direct access to forbidden world information such as global state or absolute position.

### 2.4 Reproducible Decision and Transition Behavior
The system behaves reproducibly under fixed configuration and seed, including:

- policy sampling
- tie-breaking where applicable
- full episode trajectories

This is mandatory for testing, worked-example validation, and AI-assisted iterative development.

### 2.5 Minimal Inspectability
The MVP must produce enough structured output to inspect what happened at runtime at least on:

- step level
- episode level

including decision and transition information sufficient for debugging and validation. Full engineering richness is not required yet, but opaque execution is unacceptable.

### 2.6 Testability Against the Specification
The MVP must be testable in a way that allows direct validation of:

- architectural invariants
- deterministic scenarios
- selected worked-example behavior
- module interactions

using compact fixtures and explicit assertions.

---

## 3. What the MVP must include
The MVP must include the full **behavioral runtime chain**:

- world representation
- agent state
- sensor / observation builder
- baseline memory handling
- hunger drive
- policy with masking and Softmax-based decision
- transition engine
- episode execution loop
- minimal configuration support
- minimal result / trace structures
- test support required to validate the above

Important point: this means the MVP is **not** just a toy prototype. It is the first complete implementation slice of the actual architecture. Supporting engineering parts may be reduced, but not omitted where they are necessary for reproducibility, testing, and runtime inspection.

---

## 4. What the MVP explicitly does not include
The MVP does **not** include:

- experiment framework beyond single-run / basic execution
- parameter sweep system
- posterior replay visualization
- advanced logging backends
- rich observability modes beyond the minimum needed for inspection
- future multi-drive extensions
- planning, learning, world model, or semantic memory extensions

This exclusion is intentional. These elements are valuable, but they are not required to prove that the baseline mechanistic core has been implemented correctly.

---

## 5. Engineering interpretation of the MVP
From an implementation perspective, the MVP is successful if it gives you:

- one real runtime path through the architecture
- a complete step-to-step episode execution
- deterministic reproducibility under controlled conditions
- enough traceability to verify decisions and transitions
- a stable base for AI-generated code expansion

That makes it the correct implementation target for your current strategy: use specification and decomposition to constrain AI-generated code, instead of asking a coding agent to infer the architecture from the abstract model alone. This is fully aligned with the role of the architecture and engineering pre-specification documents.

---

## 6 MVP Implementation Cut – Component Classification

### 6.1 Purpose
This section defines the **minimal implementation boundary (MVP cut)** for System A (Baseline) by classifying all architectural components into three categories:

- **MVP Core**: strictly required to realize a complete and correct runtime system
- **MVP Light**: required for engineering viability, but implemented in reduced form
- **Post-MVP**: intentionally excluded from the initial implementation phase

The goal is to establish a **small, complete, and testable vertical slice** of the system that:

- executes full episodes end-to-end
- preserves all baseline architectural constraints
- is reproducible and inspectable
- is suitable for AI-assisted incremental implementation

This classification serves as the authoritative boundary for the first implementation phase and directly informs the **Incremental Work Package Roadmap**.

---

### 6.2 MVP Core Components
The following components are **mandatory and must be fully implemented** for the MVP. Together, they form the complete behavioral runtime chain of System A.

#### **World Representation**

- 2D grid-based environment
- cell structure with:
    
    - traversability $b$
    - resource value $r$

- agent position handling
- boundary checks and movement constraints

The world acts as a deterministic, passive state container and is required for all perception and transitions.

---

#### Agent State

- internal energy (`e_t`)
- memory state (`m_t`)

No additional hidden variables are allowed. The agent state must remain minimal and explicit.

---

#### Sensor / Observation Model

- local observation based on von Neumann neighborhood
- fixed-size observation vector (center + adjacent cells)
- per-cell tuple `(b, r)`
- consistent ordering and normalization
- boundary handling via zero-padding

The observation is the **only permitted interface** between world and agent.

---

#### Memory System (Baseline)

- bounded storage (e.g., FIFO)
- stores observations or derived minimal state snapshots
- updated during state transition
- **not used for decision-making in baseline**

Memory must exist as part of the runtime architecture, even if behaviorally inactive.

---

#### Drive Computation (Hunger)

- computation of hunger activation based on energy
- generation of action preference contributions
- includes:
    
    - stay suppression
    - consumption bias (e.g., `w_consume`)

No multi-drive aggregation beyond trivial structure.

---

#### Policy and Decision Pipeline

- transformation of action scores into probabilities
- admissibility masking (e.g., blocked movement)
- Softmax-based action selection
- support for:
    
    - stochastic sampling (seeded)
    - deterministic selection (argmax + tie-breaking)

- minimal decision trace

Only the baseline policy is implemented in the MVP.

---

#### Transition Engine

- single authoritative implementation of state transition function $F$
- includes:
    
    - environment update (e.g., regeneration if applicable)
    - action application (movement, consume)
    - observation construction
    - agent state update (energy)
    - memory update
    - termination evaluation

No implicit state mutations outside this component are allowed.

---

#### Episode Execution Loop

- initialization of world and agent
- iterative step execution:
    
    - observation → decision → transition

- termination based on:
    
    - energy depletion
    - maximum step count  
    
- result accumulation

This loop defines the temporal structure of the system.

---

### 6.3 MVP Light Components
The following components are required for engineering correctness, reproducibility, and debugging, but are implemented in a **minimal and constrained form**.

---

#### Configuration Model

- structured configuration covering:
    
    - general (e.g., seed)
    - world parameters
    - agent parameters
    - policy parameters
    - execution settings

- deterministic initialization via configuration

Not included:

- parameter sweeps
- hierarchical overrides
- experiment-level configuration systems

---

#### Result and Trace Structures

- minimal hierarchical result representation:
    
    - `StepResult`
    - `EpisodeResult`
    - optionally `RunResult`
        
- minimal trace structures:
    
    - `DecisionTrace`
    - `TransitionTrace`


Must provide:

- step-level inspectability
- sufficient information for debugging and validation

Not intended for full analytical workflows at this stage.

---

#### Logging and Observability

- optional step-level logging
- simple output (e.g., in-memory or JSONL)
- no external logging systems

Strict constraint:

- logging must not influence runtime behavior

---

#### Test Support and Fixtures

- deterministic test scenarios
- basic fixture builders:
    
    - world
    - agent state
    - memory

- helper functions for:
    
    - single-step execution
    - short episode execution

- assertion utilities for:
    
    - admissible actions
    - probability validity
    - energy bounds
    - memory bounds
    - temporal consistency

Although categorized as supporting, this component is **critical for MVP viability**.

---

#### Extension Boundaries (Structural Only)

- clear separation of components in code structure
- well-defined replacement points (e.g., policy, sensor, memory)

Not included:

- plugin frameworks
- dynamic loading systems
- reflection-based extensibility

The system must be **extension-ready by design, not by infrastructure**.

---

### 6.4 Post-MVP Components
The following components are explicitly **excluded from the MVP** and will be addressed in later phases.

---

#### Experimentation System

- multi-run orchestration
- parameter sweeps
- experiment-level result aggregation
- parallel execution strategies

---

#### Visualization

- run and episode replay
- state visualization
- debugging overlays

Visualization operates strictly on recorded results and is decoupled from runtime execution.

---

#### Advanced Logging and Observability

- rich logging backends
- advanced metrics and telemetry
- external observability integrations

---

#### Future Extension Implementations

- multi-drive systems
- learning mechanisms
- advanced memory usage
- extended sensor models
- richer world dynamics

These are supported by the architecture but not implemented in the MVP.

---

### 6.5 Summary
The MVP consists of:

- a **fully functional runtime core** implementing System A behavior
- a **minimal but sufficient engineering layer** enabling reproducibility, testing, and inspection
- a deliberate exclusion of all non-essential supporting systems

This ensures that the first implementation:

- is structurally correct
- remains manageable for a single developer
- is suitable for AI-assisted code generation
- provides a stable foundation for incremental extension

---

# 7. Incremental Work Package Roadmap

## 7.1 Purpose and Delivery Strategy
This section defines the **ordered implementation roadmap** for the MVP of System A (Baseline).

Its purpose is to translate the architectural decomposition into a sequence of **implementable work packages** that:

- can be executed incrementally
- preserve a runnable and testable system state after each major step
- respect architectural boundaries and dependencies
- are suitable for controlled AI-assisted code generation

The roadmap is intentionally structured around **dependency order**, not around document order or conceptual elegance alone.

The key delivery principle is:

> **Build the smallest valid runtime chain first, then strengthen it with reproducibility, traceability, and testing support.**

This is necessary because the MVP is not merely a collection of components. It is a **functioning execution path** from initialization to termination.

---

## 7.2 Roadmap Design Principles
The work package plan follows the principles below.

### 7.2.1 Vertical Slice over Horizontal Completion
The implementation shall not proceed by attempting to "finish" one whole architectural layer before touching the next.

Instead, it shall build a **minimal end-to-end executable slice**, then strengthen and extend that slice step by step.

This reduces integration risk and is particularly important when implementation is delegated partially to AI coding systems.

---

### 7.2.2 Architectural Boundaries Must Exist Early
Even where implementations are initially minimal, the basic architectural separation between:

- world
- agent state
- observation
- drive computation
- policy
- transition
- execution
- results / traces

must be visible from the beginning.

The MVP is not intended to be a throwaway prototype. It is the first implementation of the actual baseline architecture.

---

### 7.2.3 Deterministic Testing Is Part of Delivery
A work package is not considered complete when code exists, but when:

- it can be exercised in isolation where appropriate
- its invariants are testable
- its behavior is reproducible under controlled conditions

This follows directly from the engineering pre-specification and is non-negotiable.

---

### 7.2.4 Minimal but Stable Results
Early work packages may use reduced result structures, but they must already align with the final runtime contracts:

- `StepResult`
- `EpisodeResult`
- `DecisionTrace`
- `TransitionTrace`

The system must not rely on ad hoc or temporary output conventions that later need structural replacement.

---

## 7.3 Dependency Logic
The MVP implementation has the following high-level dependency flow:

```text
Configuration Foundations
    ↓
Core Domain State Structures
    ↓
World + Observation Foundations
    ↓
Drive Computation
    ↓
Policy / Decision Pipeline
    ↓
Transition Engine
    ↓
Episode Execution Loop
    ↓
Result / Trace Integration
    ↓
Test Fixtures and Deterministic Validation
```

This dependency chain reflects actual runtime necessity:

- the policy cannot exist meaningfully before observation and drive scoring exist
- the transition engine cannot be validated before world, agent, and observation structures exist
- the execution loop cannot produce meaningful episodes before policy and transition are integrated
- structured results and tests must stabilize the system as soon as the runtime chain becomes executable

---

## 7.4 Work Package Overview
The MVP shall be implemented through the following work packages:

1. **WP1 – Core Configuration and Fundamental Runtime Types**
2. **WP2 – World Model and Observation Construction**
3. **WP3 – Agent State and Baseline Memory**
4. **WP4 – Hunger Drive Module**
5. **WP5 – Policy and Decision Pipeline**
6. **WP6 – Transition Engine**
7. **WP7 – Episode Execution Loop**
8. **WP8 – Result and Trace Structures**
9. **WP9 – Test Support, Fixtures, and Deterministic Validation**
10. **WP10 – Minimal Logging / Observability Integration**

The ordering is deliberate. Some packages may overlap in refinement, but the dependency direction must not be violated.

---

## 7.5 Work Package Definitions

---

### WP1 – Core Configuration and Fundamental Runtime Types

#### Purpose
Establish the minimal structural foundation required by all later packages.

#### Scope

This package defines:

- minimal configuration structures for MVP runtime
- core enums / constants such as action space
- shared value objects and state containers needed across modules
- initial validation logic for basic configuration correctness

#### Must Include

- `SystemConfig` or equivalent MVP configuration root
    
- configuration sections for:
    
    - general
    - world
    - agent
    - policy
    - execution

- action enum for:
    
    - `UP`, `DOWN`, `LEFT`, `RIGHT`, `CONSUME`, `STAY`
        
- basic shared type definitions for:
    
    - position
    - observation
    - agent state
    - memory state
    - world state references or placeholders

#### Must Not Include

- experiment configuration
- sweep definitions
- advanced override layers
- plugin registries

#### Primary Outputs

- minimal validated runtime configuration model
- stable foundational data types reused by later work packages

#### Dependencies

- none

#### Why First
Without stable types and configuration contracts, later AI-generated code is likely to drift into incompatible local definitions.

#### **Testing Focus**

- configuration validation
- enum stability
- structural type correctness
- serialization readiness of core state objects

---

### WP2 – World Model and Observation Construction

#### Purpose
Implement the external environment and the only permitted perception channel from world to agent.

#### Scope
This package defines:

- explicit 2D world representation
- cell structure and invariants
- agent position inside world state
- observation construction from local neighborhood
- boundary handling and traversability interpretation

#### Must Include

- `Cell`
- `World`
- basic world initialization from config
- side-effect-free world access methods
- observation builder implementing the baseline sensor model
- observation vector construction in fixed order
- out-of-bounds handling as `(0,0)`

#### Must Not Include

- complex world generators
- visualization
- policy logic
- transition logic beyond read-only world access

#### Primary Outputs

- valid world state object
- deterministic observation construction for any valid state

#### Dependencies

- WP1

#### Why Here
The drive and policy cannot be implemented correctly before the observation channel exists.

#### Testing Focus

- cell invariants
- world bounds
- traversability behavior
- correct observation ordering
- boundary handling
- observation value ranges

---

### WP3 – Agent State and Baseline Memory

#### Purpose
Implement the internal runtime state of the baseline agent, including behaviorally inactive but architecturally real memory.

#### Scope
This package defines:

- agent energy representation
- bounded memory state
- minimal memory entry structure
- deterministic memory update behavior

#### Must Include

- `AgentState`
- `MemoryState`
- bounded FIFO memory behavior
- minimal memory update function
- clipping and state validation rules for energy bounds

#### Must Not Include

- memory retrieval logic for decision-making
- semantic or structured memory
- hidden state variables

#### Primary Outputs

- valid agent-side state structures
- deterministic memory state evolution primitive

#### Dependencies

- WP1

#### Why Here
The agent state is needed before drive computation and transition logic can be implemented meaningfully.

#### Testing Focus

- energy bounds
- memory capacity handling
- FIFO behavior
- empty initialization
- deterministic update behavior

---

### WP4 – Hunger Drive Module

#### Purpose
Implement the baseline motivational mechanism that transforms internal deficit and local observation into action contribution scores.

#### Scope
This package defines:

- hunger activation from energy
- action contribution vector over the full baseline action space
- stay suppression
- consume weighting

#### Must Include

- hunger activation computation
- contribution computation for:
    
    - four movement actions
    - `CONSUME`
    - `STAY`

- fixed action ordering consistent with policy input

#### Must Not Include

- multi-drive aggregation logic beyond minimal compatibility
- policy masking
- Softmax
- state mutation

#### Primary Outputs

- deterministic hunger drive computation component

#### Dependencies

- WP1
- WP2
- WP3

#### Why Here
The policy should consume a well-defined scoring component, not re-implement drive logic internally. This is already a key architectural rule in the pre-specification.

#### Testing Focus

- hunger activation range
- correct action score mapping from observation
- stay suppression correctness
- consume weighting correctness
- deterministic score output

---

### WP5 – Policy and Decision Pipeline

#### Purpose
Transform baseline drive scores into a reproducible action decision using masking, Softmax, and configured selection mode.

#### Scope
This package defines:

- admissibility masking
- stable Softmax probability computation
- stochastic and deterministic action selection
- minimal decision trace generation

#### Must Include

- policy component
- admissibility masking for blocked movement actions
- Softmax probability computation
- seeded `sample` mode
- seeded `argmax` mode with tie-breaking
- minimal `DecisionTrace`

#### Must Not Include

- alternative policy families
- world mutation
- transition logic
- memory-dependent behavior

#### Primary Outputs

- selected action
- reproducible action probabilities
- inspectable decision result

#### Dependencies

- WP1
- WP2
- WP3
- WP4

#### Why Here
At this point the system gains its first real decision capability, but still without state evolution.

#### Testing Focus

- masking correctness
- probability normalization
- zero probability for inadmissible actions
- deterministic seeded behavior
- tie-breaking behavior
- minimal trace completeness

---

### WP6 – Transition Engine

#### Purpose
Implement the single authoritative mechanism that updates runtime state from one step to the next.

#### Scope
This package defines the ordered transition phases:

- world update
- action application
- next observation construction
- agent update
- memory update
- termination evaluation

#### Must Include

- `TransitionEngine`
- world regeneration or baseline world update logic as configured
- movement application
- consumption handling
- energy update
- memory update integration
- termination criterion
- minimal `TransitionTrace`

#### Must Not Include

- policy logic
- execution loop orchestration
- logging concerns
- visualization hooks with runtime influence

#### Primary Outputs

- next world state
- next agent state
- next memory state
- next observation
- termination signal
- transition trace

#### Dependencies

- WP1
- WP2
- WP3
- WP5 is not strictly required for isolated transition execution, but in roadmap order it should already exist
- practically depends on WP2 and WP3 directly

#### Why Here
This package completes the baseline system physics. It is the most critical runtime package and should be implemented only after the state, observation, and policy-side contracts are stable.

#### Testing Focus

- movement correctness
- blocked movement handling
- resource consumption behavior
- energy update correctness
- memory update timing
- termination behavior
- temporal ordering of transition phases

---

### WP7 – Episode Execution Loop

#### Purpose
Integrate policy and transition into a complete episodic runtime flow.

#### Scope
This package defines:

- initial state construction
- step sequencing
- termination handling
- episode-level accumulation

#### Must Include

- execution loop / runner
    
- initialization path:
    
    - world
    - agent
    - memory
    - initial observation
      
- step iteration:
    
    - decision
    - transition
    - state advancement
      
- episode termination via:
    
    - `done`
    - `max_steps`

#### Must Not Include

- multi-run experiment orchestration
- parameter sweeps
- visualization playback

#### Primary Outputs

- complete episode execution capability
- ordered step progression through runtime components

#### Dependencies

- WP1 through WP6

#### Why Here
This is the first package that produces a true end-to-end MVP runtime slice.

#### Testing Focus

- full episode execution
- correct step ordering
- deterministic replayability under fixed seed
- termination at expected conditions

---

### WP8 – Result and Trace Structures

#### Purpose
Stabilize runtime outputs into explicit, structured, and reusable result objects.

#### Scope
This package defines the minimal structured output hierarchy required by the MVP.

#### Must Include

- `StepResult`
- `EpisodeResult`
- minimal `DecisionTrace`
- minimal `TransitionTrace`
- optional minimal `RunResult` if needed for interface stability

#### Must Preserve

- ordered step structure
- alignment with actual runtime behavior
- serialization readiness

#### Must Not Include

- rich analytical aggregation
- experiment result hierarchies beyond MVP need
- visualization-specific result formats

#### Primary Outputs

- structured runtime output contract for debugging, replay, and testing

#### Dependencies

- WP5
- WP6
- WP7

#### Why Not Earlier
Minimal traces can exist earlier informally, but full formalization makes most sense once the executable runtime path exists.

#### Testing Focus

- structural completeness
- correct ordering relationships
- serialization readiness
- trace-to-step consistency

---

### WP9 – Test Support, Fixtures, and Deterministic Validation

#### Purpose
Provide the practical engineering layer required to validate the MVP reliably and repeatedly.

#### Scope
This package defines:

- deterministic fixtures
- builders
- helper execution utilities
- reusable assertions
- first baseline reference tests

#### Must Include

- world fixture builders
- agent state builder
- memory state builder
- execution helpers for:
    
    - one policy decision
    - one transition
    - one full step
    - one full episode
        
- assertion helpers for:
    
    - probabilities
    - admissibility
    - energy bounds
    - memory bounds
    - temporal consistency

####  Should Include

- initial worked-example-aligned tests for selected baseline scenarios

#### Must Not Include

- giant future-proof testing frameworks
- fixtures for non-baseline future systems

#### Primary Outputs

- stable baseline validation layer

#### Dependencies

- practically depends on all prior MVP runtime packages
- may begin partially earlier, but becomes fully meaningful after WP7 and WP8

#### Why Late but Critical
Testing support can start earlier, but full deterministic validation only becomes coherent once the end-to-end runtime chain and result structures are in place.

#### Testing Focus

This package is itself about testing infrastructure, so its completion criterion is practical usefulness:

- tests become shorter
- deterministic scenarios become easy to construct
- regressions become easy to express

---

### WP10 – Minimal Logging / Observability Integration

#### Purpose
Add a minimal engineering-level visibility layer without changing runtime semantics.

#### Scope
This package defines:

- optional step-level logging
- simple persistence format
- runtime-to-log mapping

#### Must Include

- minimal logging configuration
- optional in-memory or JSONL output
- step-level output integration based on runtime results

#### Must Not Include

- external telemetry systems
- complex backends
- experiment-level observability frameworks

#### Primary Outputs

- basic inspectability beyond test execution
- persistent execution traces suitable for later debugging or replay groundwork

#### Dependencies

- WP7
- WP8

#### Why Last in MVP
Logging should consume stable runtime outputs, not shape them.

#### Testing Focus

- logging does not alter execution
- stable ordering of emitted records
- successful persistence of minimal structured records

---

## 7.6 Recommended Execution Order
The recommended implementation order is:

```text
WP1 → WP2 → WP3 → WP4 → WP5 → WP6 → WP7 → WP8 → WP9 → WP10
```

This is the default roadmap for MVP realization.

A small amount of overlap is acceptable, especially for tests and trace structures, but the architectural dependency direction must remain intact.

---

## 7.7 Runnable Milestones
To keep progress visible and AI-assisted implementation controlled, the roadmap should be evaluated against the following practical milestones.

### Milestone A – Static Runtime Foundations

Completed after:

- WP1
- WP2
- WP3

At this point:

- world, observation, and agent state exist
- no real behavior yet
- foundational invariants can already be tested

---

### Milestone B – Decision Capability
Completed after:

- WP4
- WP5

At this point:

- the system can score actions and choose actions reproducibly
- isolated decision tests become meaningful

---

### Milestone C – Stateful Step Transition
Completed after:

- WP6

At this point:

- one full runtime step can be executed deterministically

---

### Milestone D – Full Episode MVP Runtime
Completed after:

- WP7
- WP8

At this point:

- the MVP core is functionally complete
- full episodes can be executed and inspected through structured results

---

### Milestone E – MVP Validation and Minimal Observability
Completed after:

- WP9
- WP10

At this point:

- the MVP is not only runnable, but engineering-usable
- deterministic validation, regression protection, and basic runtime inspection are available

---

## 7.8 Guidance for AI-Assisted Implementation
This roadmap is intentionally suitable for AI-assisted coding workflows.

Each work package should later be translated into a more specific implementation brief containing:

- objective
- exact scope boundaries
- expected inputs / outputs
- invariants
- required tests
- explicit non-goals

This is important because the success of AI-assisted implementation depends on keeping each package:

- architecturally bounded
- technically concrete
- small enough to avoid uncontrolled inference by the coding system

The roadmap therefore acts as the bridge between:

- architecture documents
- engineering constraints
- executable coding task

---

## 7.9 Summary
The MVP of System A shall be implemented through a sequence of ordered work packages that:

- begin with stable runtime foundations
- introduce decision-making before full execution
- centralize state evolution in the transition engine
- complete the runtime path through the episode loop
- then stabilize the system with structured results, fixtures, tests, and minimal observability

This ordering is designed to maximize:

- correctness
- reproducibility
- inspectability
- suitability for incremental AI-assisted code generation

while avoiding premature expansion into experimentation, visualization, or advanced extension infrastructure.

---

# 8. Testing Strategy Across Work Packages

## 8.1 Purpose
This section defines the **testing strategy for the MVP implementation of System A (Baseline)** across all work packages.

The goal is not only to verify correctness, but to ensure that the system is:

- **deterministic under controlled conditions**
- **structurally consistent with the architecture**
- **inspectable at every stage of execution**
- **robust against regression during incremental development**

Testing is treated as a **first-class engineering concern**, not as a post-hoc validation step.

---

## 8.2 Core Testing Principles

### 8.2.1 Determinism First
All tests must be executable in a **fully deterministic mode**, achieved by:

- fixed random seed
- deterministic policy mode (`argmax + tie-breaking`) where required
- controlled initial conditions (world, agent, memory)

This is critical because stochastic behavior otherwise masks structural defects.

---

### 8.2.2 Smallest Verifiable Unit
Each work package must expose **testable units at the smallest meaningful level**, for example:

- observation builder
- hunger score computation
- Softmax probability output
- single transition step

Tests must not rely solely on full episode execution.

---

### 8.2.3 Explicit Invariants over Implicit Expectations
Tests must validate **explicit invariants**, not vague expectations such as “the agent behaves reasonably”.

Examples:

- probabilities sum to 1
- inadmissible actions have probability 0
- energy remains within defined bounds
- memory size never exceeds capacity

---

### 8.2.4 Structural Alignment with Runtime Contracts
All tests must align with the formal runtime structures:

- `AgentState`
- `Observation`
- `DecisionTrace`
- `TransitionTrace`
- `StepResult`
- `EpisodeResult`

No test should rely on internal shortcuts or bypass these structures.

---

### 8.2.5 Progressive Strengthening
Testing depth increases along the roadmap:

- early work packages → structural correctness
- mid-stage packages → functional correctness
- late-stage packages → temporal and behavioral consistency

---

## 8.3 Test Layers
The MVP testing strategy is structured into four layers.

---

### 8.3.1 Unit-Level Tests
Focus: **pure functions and isolated components**

Applies to:

- observation construction
- drive computation
- policy Softmax
- masking logic

Characteristics:

- no dependency on full runtime
- deterministic input → deterministic output
- no side effects

---

### 8.3.2 Component-Level Tests
Focus: **single architectural components with minimal dependencies**

Applies to:

- world model behavior
- memory update logic
- policy decision pipeline
- transition engine (single-step)

Characteristics:

- controlled test fixtures
- limited integration
- validation of component boundaries

---

### 8.3.3 Step-Level Tests
Focus: **one full perception → decision → transition cycle**

Applies to:

- integration of:
    - observation
    - drive
    - policy
    - transition

Characteristics:

- verifies correct ordering of operations
- ensures state consistency across one step
- validates trace alignment (`DecisionTrace`, `TransitionTrace`)

---

### 8.3.4 Episode-Level Tests
Focus: **full execution loop**

Applies to:

- multi-step episodes
- termination conditions
- cumulative state evolution

Characteristics:

- deterministic replayability
- validation of:
    - termination (energy depletion / max steps)
    - trajectory consistency
- comparison against expected patterns (not vague behavior)

---

## 8.4 Work Package–Aligned Testing Strategy

---

### WP1 – Configuration and Core Types
**Test Focus:**

- configuration validation
- default values
- enum correctness
- serialization compatibility

**Key Invariants:**

- configuration objects are valid and complete
- invalid configurations fail early and explicitly

---

### WP2 – World and Observation
**Test Focus:**

- world initialization
- cell invariants
- boundary handling
- observation vector correctness

**Key Invariants:**

- observation size is constant
- observation ordering is stable
- out-of-bounds values are correctly represented as `(0,0)`

---

### WP3 – Agent State and Memory
**Test Focus:**

- energy initialization and clipping
- memory insertion
- FIFO behavior
- empty and full memory states

**Key Invariants:**

- energy ∈ valid range at all times
- memory size ≤ capacity
- insertion order is preserved

---

### WP4 – Hunger Drive
**Test Focus:**

- hunger activation from energy
- action score mapping
- stay suppression
- consume weighting

**Key Invariants:**

- action score vector has correct dimensionality
- score contributions are deterministic
- no NaN or undefined values

---

### WP5 – Policy and Decision
**Test Focus:**

- admissibility masking
- Softmax correctness
- deterministic action selection
- tie-breaking behavior

**Key Invariants:**

- probabilities sum to 1 (within tolerance)
- inadmissible actions have probability 0
- same input + same seed → same action

---

### WP6 – Transition Engine
**Test Focus:**

- movement application
- blocked movement handling
- consumption logic
- energy update
- memory update timing
- termination detection

**Key Invariants:**

- state transitions are consistent and complete
- no hidden state mutation outside transition engine
- temporal order of operations is preserved

---

### WP7 – Execution Loop
**Test Focus:**

- correct step sequencing
- initialization correctness
- termination behavior
- reproducibility across runs

**Key Invariants:**

- same config + seed → identical episode
- step count matches expected termination condition
- no skipped or duplicated steps

---

### WP8 – Result and Trace Structures
**Test Focus:**

- structural completeness of results
- trace alignment with runtime steps
- serialization

**Key Invariants:**

- each step has corresponding traces
- ordering is preserved
- results are serializable without loss

---

### WP9 – Test Fixtures and Validation Layer
**Test Focus:**

- fixture correctness
- ease of constructing deterministic scenarios
- reusability of helpers

**Key Invariants:**

- fixtures produce valid states
- no hidden randomness in fixtures
- tests become simpler, not more complex

---

### WP10 – Logging
**Test Focus:**

- logging correctness
- ordering of log entries
- non-interference with runtime

**Key Invariants:**

- logging does not alter system state
- logs reflect actual execution order
- logging can be disabled without side effects

---

## 8.5 Deterministic Reference Scenarios
To stabilize behavior across implementations, a small set of **reference scenarios** should be defined.

These scenarios:

- use fixed world layouts
- use fixed initial energy
- use deterministic policy mode
- run for a small number of steps

They serve as:

- regression anchors
- validation for AI-generated implementations
- alignment checks between different implementations

These scenarios should be derived from the **Worked Examples document**, ensuring consistency between theory and implementation.

---

## 8.6 Failure Modes and Anti-Patterns
The following patterns must be explicitly avoided:

---

### Implicit Randomness

- missing seed control
- hidden randomness in fixtures

→ leads to non-reproducible tests

---

### Over-Reliance on Episode Tests

- testing only full runs

→ hides localized defects

---

### Testing via Print/Logging

- manual inspection instead of assertions

→ not scalable, not reliable

---

### Hidden State Mutation

- components modifying shared state outside transition engine

→ breaks architectural guarantees

---

### Coupled Tests

- tests depending on multiple unrelated components

→ fragile and hard to debug

---

## 8.7 Success Criteria
The MVP testing strategy is considered successful when:

- each work package introduces **testable, isolated functionality**
- the system can be **executed deterministically end-to-end**
- failures can be traced to a **specific component or invariant**
- AI-generated code can be validated through **explicit, reproducible tests**

At this point, the system transitions from:

> “code that seems to work”

to:

> “a controlled, inspectable, and reproducible baseline system”

---
