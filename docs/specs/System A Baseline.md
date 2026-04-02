# System A (Baseline): A Minimal Mechanistic Single-Drive Agent Without World Model

## Metadata
- Project: AXIS – Complex Mechanistic Systems Experiment
- Author: Oliver Grau
- Type: Formal Research Note
- Status: Draft v2.0
- Scope: Baseline agent with modular drive-based action modulation
- Constraints: No world model, no self-model, no planning, no meta-cognition, no phenomenology

---

## 1. Objective
This document defines **System A** as a minimal, fully mechanistic baseline agent for the *Complex Mechanistic Systems Experiment*.

The purpose of System A is to establish a formally precise agent architecture that is capable of:

- sensing its local environment,
- maintaining internal regulatory state,
- storing local perceptual episodes,
- expressing multiple primitive drives,
- selecting actions through drive-based modulation,
- and updating its state over time,

while **not** containing:

- a world model,
- a self-model,
- planning,
- meta-cognitive structures,
- semantic concepts such as "food" or "danger",
- or any phenomenological assumptions.

The baseline question remains:

> How much adaptive and goal-directed behavior can already emerge from a minimal mechanistic system before introducing richer representational structures?

---

## 2. Design Principles

### 2.1 Pure Mechanism
All behavior must be explainable in terms of:

- state variables,
- explicit update functions,
- local sensor mappings,
- drive computations,
- and action selection rules.

### 2.2 No Implicit Mental Vocabulary
The following notions are intentionally excluded from the formal model:

- feeling
- awareness
- consciousness
- reflection
- understanding
- intention

### 2.3 Modular Drives
Primitive regulation is implemented through **independent drive modules**.

In the baseline system, two drives are defined:

#### 2.3.1 Hunger Drive 
This is a homeostatic pressure related to energy depletion.

These drives do **not** constitute emotions. They are scalar regulatory subsystems that modulate action selection.

### 2.4 No World Model
System A has no map, no spatial memory of the environment, no explicit representation of "visited places", and no predictive model of future world states.

### 2.5 Locality
System A only receives **local perceptual input**. All action modulation must be computed from:

- current internal state,
- current local observation,
- and stored local perceptual episodes.

---

## 3. Formal Definition
System A is defined as the 8-tuple

$$
A = (\mathcal{X}, \mathcal{U}, \mathcal{M}, \mathcal{A}, \mathcal{D}, F, \Gamma, \pi)
$$

where:

- $\mathcal{X}$ is the internal state space
- $\mathcal{U}$ is the sensory input space
- $\mathcal{M}$ is the episodic perceptual memory space
- $\mathcal{A}$ is the action space
- $\mathcal{D}$ is the drive space
- $F$ is the state transition function
- $\Gamma$ is the action modulation system
- $\pi$ is the policy

---

## 4. Internal State
The internal state of the agent captures all quantities that are **intrinsic to the agent itself** and evolve over time independently of the external world representation.

It is defined as:

$$
x_t = (e_t, \xi_t)
$$

where:

* $e_t \in [0, E_{\max}]$
  Internal energy level of the agent at time (t)

* $\xi_t$
  Set of auxiliary internal variables (e.g. derived quantities such as hunger or internal drive-related states)

---

### Important Clarification
The **physical position of the agent is not part of the internal state**.

* The agent does **not have direct access to its absolute position** in the grid

The position is maintained exclusively by the environment as part of the world state:

$$
s_t^{world} = (\mathcal{E}_t, p_t)
$$

where:

* $\mathcal{E}_t$: environment configuration (grid, resources, obstacles)
* $p_t$: agent position in the grid

---

### Interpretation
This separation enforces a strict modeling constraint:

* The agent operates **purely on perception and internal variables**
* There is **no privileged access to global spatial information**
* All behavior must emerge from:

  * local sensing
  * memory
  * internal drive dynamics

---

## 5. Environment and Local Observation
The agent operates within a discrete, spatially structured environment (grid world) that is **fully external to the agent’s internal state**.

This section provides a high-level overview of:

- the **environment representation**
- the **observation mechanism**

Detailed specifications are defined in the following companion documents:

- [[The_World]]
- [[The_Sensor_Model]]

---

### 5.1 Environment Overview
The environment is modeled as a discrete 2D grid consisting of cells with different semantic roles, such as:

- empty space
- food resources
- obstacles

At any time $t$, the complete environment state is defined as:

$$
s_t^{world} = (\mathcal{E}_t, p_t)  
$$

where:

- $\mathcal{E}_t$: full grid configuration, including all cell contents
- $p_t$: physical position of the agent within the grid

---

#### Key Property
The environment state is **not directly accessible to the agent**.

- The agent has **no global view**
- The agent has **no access to absolute coordinates**
- The agent does **not know its position $p_t$**

All interaction with the environment is mediated through a sensor function.

---

### 5.2 Sensor Model and Local Observation
The agent perceives the environment through a sensor function:

$$
u_t = S(s_t^{world})  
$$

This function maps the full world state to a **local observation** $u_t$.

---

#### Locality Constraint
The observation is strictly local:

- The agent observes:
    
    - the current cell
    - neighboring cells (e.g. von Neumann or Moore neighborhood)
        
- The observation does **not include**:
    
    - global grid structure
    - distant cells
    - absolute position

---

#### Interpretation
This induces a **partial observability setting**:

- The agent must act under **incomplete information**
    
- Spatial structure may in principle be inferred indirectly via:
    
    - temporal sequences of observations
    - episodic memory

> In the baseline system, however, episodic memory is not used for inference or behavior.

---

### 5.3 Separation of Concerns
The system enforces a strict separation:

- **World (external)**
    
    - grid structure
    - resources
    - agent position
    - physical dynamics
        
- **Agent (internal)**
    
    - energy
    - internal variables
    - decision-making

The only interface between both is:

$$
u_t = S(s_t^{world})  
$$

---

### 5.4 Reference Documents
The following documents provide the full formal specification:

- [[The_World]]  
    Defines:
    
    - grid structure
    - cell types
    - resource dynamics
    - position handling

- [[The_Sensor_Model]]  
    Defines:
    
    - observation function $S$
    - neighborhood structure
    - encoding of observations
    - constraints on perceptual information

---

### Why this matters (important for later sections)
All subsequent mechanisms depend critically on this design:

- energy acquisition
- search behavior
- exploration dynamics
- memory formation

If additional information is introduced here implicitly, it will:

- break the minimality of the baseline
- introduce hidden world models
- invalidate later conclusions about emergent behavior

---

## 6. Episodic Perceptual Memory
The agent maintains an episodic memory that stores a history of past observations.

This memory is **purely perceptual** and reflects only what the agent has experienced through its sensor model over time.

---

### 6.1 Definition
The episodic memory at time $t$ is defined as:

$$
m_t = (u_{t-k}, u_{t-k+1}, \dots, u_t)  
$$

where:

- $u_t$: local observation at time $t$
- $k$: memory horizon (finite)

---

#### Key Property
The memory contains **only observations**, not world states.

- No global grid representation
- No absolute positions
- No explicit spatial map

---

### Formal Definition

$$
m_{t+1} = M(m_t, u_{t+1})
$$
> In System A (Baseline), memory is a passive recording mechanism.
> It is not used for action selection, prediction, or state evaluation.

### 6.2 Nature of Stored Information
Each memory element corresponds to a past local observation:

$$
u_t = S(s_t^{world})  
$$

Thus, memory consists of:

- local cell configurations
- perceived resource presence (e.g. energy)
- perceived obstacles

---

#### Important Constraint
The agent does **not store**:

- the true world state $\mathcal{E}_t$
- its position $p_t$
- transitions of the environment

Any structure beyond raw observations must **emerge from processing**, not from explicit representation.

---

### 6.3 Interpretation
The episodic memory serves as a temporal trace of experience:

- It enables comparison between:
    
    - current observation $u_t$
    - past observations $u_{t-i}$
        
The episodic memory stores a temporal trace of past observations.

In the baseline system, this memory is not used for:

- novelty detection
- repetition recognition
- behavioral conditioning

It serves purely as a recorded history for future system extensions.

---

#### Partial Observability Context
Because the agent only observes locally:

- the environment is **partially observable**
- memory becomes the only mechanism to integrate information over time

However:

- memory does **not reconstruct the world**
- it only accumulates **perceptual fragments**

---

### 6.4 Minimal Design Principle
The memory system is intentionally restricted:

- no compression (yet)
- no abstraction (yet)
- no learned embeddings (yet)
- no spatial reconstruction

This ensures:

- maximal transparency
- no hidden inductive biases
- clear attribution of emergent behavior

---

### 6.5 Role in Decision Making
The policy depends on memory as:

$$
a_t = \pi(x_t, u_t, m_t)  
$$

Memory may influence behavior by enabling:

- repetition avoidance
- simple exploration heuristics
- temporal pattern recognition

But in the baseline system, action selection is defined as:

$$
a_t = π(x_t, u_t)
$$
The episodic memory $m_t$ is not used for decision making at this stage.

---

### 6.6 Future Extensions (Deferred)
The current memory model is deliberately minimal.

Potential future extensions include:

- compressed or summarized memory
- learned representations
- similarity-based retrieval
- implicit spatial structuring

These are **explicitly excluded** from the baseline system and will only be introduced in later variants.

---

> The system includes an episodic memory structure $m_t$​, which is updated at each time step but does not influence behavior in the baseline configuration.

---

### Why this matters
This definition prevents a common modeling error:

> Smuggling a world model into memory.

By restricting memory to raw observations:

- the agent cannot “know” where it is
- the agent cannot build an explicit map
- any structure must emerge indirectly

This keeps the baseline system:

- mechanistic
- interpretable
- minimal

---

## 7. Action System
The agent interacts with the environment through a discrete set of actions.

The action system defines:

- the available actions
- their interpretation at the interface level
- their role in the overall system dynamics

---

### 7.1 Action Space
At each time step $t$, the agent selects an action:

$$
a_t \in \mathcal{A}  
$$

where the action space is defined as:

$$
\mathcal{A} = \{ \text{UP},\text{DOWN},\text{LEFT},\text{RIGHT},\text{CONSUME},\text{STAY} \}  
$$

---

### 7.2 Action Semantics (Interface Level)
Actions are defined **purely operationally**, without embedding outcome semantics.

---

### Movement Actions

- $\text{UP}$
- $\text{DOWN}$
- $\text{LEFT}$
- $\text{RIGHT}$

These actions express an **intended displacement** of the agent within the grid.

---

#### Consumption Action

- $\text{CONSUME}$

This action expresses an **attempt to interact with the current cell** in a way that may lead to resource extraction.

Important:

- The action itself does **not guarantee any effect**
- The outcome depends entirely on the environment state

---

#### No-Op Action

- $\text{STAY}$

The agent remains at its current position and performs no explicit interaction with the environment.

---

### 7.3 Separation of Action and Outcome
A key design principle is:

> **Actions specify intent, not outcome**

The consequences of an action are determined by the system dynamics:

- **World Transition**  
    $$
    s_{t+1}^{world} = F_{world}(s_t^{world}, a_t)  
    $$
    
- **Agent Transition**  
    $$ 
    x_{t+1} = F_{agent}(x_t, u_t, a_t)  
    $$
    

---

#### Implication

- Movement actions may:
    
    - succeed
    - fail (e.g. obstacle, boundary)
        
- The $\text{CONSUME}$ action may:
    
    - result in resource extraction
    - have no effect


The agent does **not know the outcome in advance**.

---

### 7.4 No Embedded Reward or Energy Semantics
The action system does **not encode**:

- energy gain
- energy cost
- reward signals
- success probabilities

All such effects are handled exclusively by:

- $F_{world}$ (external effects)
- $F_{agent}$ (internal effects)

---

### 7.5 Role in Decision Making
The action is selected by the policy:

$$
a_t = \pi(x_t, u_t, m_t)  
$$

where:

- $x_t$: internal state
- $u_t$: current observation
- $m_t$: episodic memory

---

### 7.6 Design Principle
The action system is intentionally minimal and neutral.

It provides:

- a finite set of discrete interaction primitives
- no embedded knowledge about the environment
- no direct coupling to internal drives

---

### Why this matters
This separation prevents a common modeling error:

> Embedding outcome knowledge directly into the action definition.

By keeping actions purely declarative:

- the environment remains the source of physical truth
- the agent must learn or infer effective behaviour
- system dynamics remain transparent and modular

---

## 8. Drive System
The agent’s behavior is modulated by a set of internal drives.

Drives represent **internal regulatory mechanisms** that influence action selection based on the agent’s internal state, perception, and experience.

> This section defines the generic drive framework of System A.
>
> Concrete baseline instantiations may use only a restricted subset of the available inputs and may leave some formally available arguments behaviorally inactive.
---

### 8.1 Definition
A drive $D_i$ is defined as a function:

$$
D_i : (x_t, u_t, m_t) \rightarrow \mathbb{R}  
$$

which produces a scalar activation:

$$
d_i(t) = D_i(x_t, u_t, m_t)  
$$

where:

- $x_t$: internal state 
- $u_t$: current observation
- $m_t$: episodic memory

---

#### Interpretation
The value $d_i(t)$ represents the **current activation level** of drive $i$.

- Higher values indicate stronger influence on behavior
- Lower values indicate weaker influence

---

### 8.2 Role of Drives
Drives do not directly select actions.
Instead, they **modulate the action selection process**.

Formally, the policy depends on drive activations:

$$  
a_t = \pi(x_t, u_t, m_t, d_1(t), \dots, d_n(t))  
$$

---

#### Key Property
Drives influence behavior **indirectly** through the policy.

- They do not act on the environment
- They do not modify the world state
- They do not bypass the policy

---

### 8.3 Separation from World Dynamics
Drives are strictly internal mechanisms.

They have:

- no direct access to the world state $s_t^{world}$
- no access to global information
- no direct influence on environment transitions

All inputs to drives are limited to:

- internal state $x_t$
- local observation $u_t$
- episodic memory $m_t$

---

### 8.4 Modulation Mechanism
Drives influence the relative preference of actions.

Conceptually, this can be expressed as:

$$
\tilde{p}(a \mid x_t, u_t, m_t) = \Gamma\bigl(a; x_t, u_t, m_t, d_1(t), \dots, d_n(t)\bigr)  
$$

where:

- $\Gamma$: modulation function
- $\tilde{p}(a)$: adjusted action preference

The final action is then selected according to:

$$
a_t = \arg\max_a \tilde{p}(a \mid x_t, u_t, m_t)  
$$

---

#### Important Constraint
The modulation mechanism must:

- not introduce hidden world knowledge
- not encode direct outcome predictions
- remain consistent with the available information

---

### 8.5 Minimal Design Principle
The drive system is intentionally defined in an abstract and minimal way.

- No assumption about specific drives
- No assumption about functional form
- No assumption about learning or adaptation

This allows:

- flexible extension
- controlled introduction of complexity
- clear attribution of behavioral effects

---

### 8.6 Interaction Between Drives
Multiple drives may be active simultaneously.

- Drives may reinforce or oppose each other
- The modulation function $\Gamma$ resolves these interactions

No predefined hierarchy between drives is assumed in the baseline system.

---

### 8.7 Scope of the Baseline System
In the baseline system, drives are:

- deterministic functions
- fully observable internally
- directly derived from current inputs

More advanced properties such as:

- learning
- adaptation
- long-term regulation

are explicitly excluded at this stage.

---

### Why this matters
The drive system is the primary source of **goal-directed behavior**.

By keeping it:

- modular
- minimal
- information-consistent

we ensure that:

- behavior emerges from structure, not hardcoding
- extensions remain controlled
- the system stays interpretable

---

## 9. Hunger Drive Module
The hunger drive represents the agent’s internal need to maintain its energy level.
It is derived solely from the agent’s internal state and does not depend on external semantics.

---

### 9.1 Energy as Internal State Variable
The agent maintains an internal energy level:

$$  
e_t \in [0, E_{\max}]  
$$

This variable is part of the internal state $x_t$.

---

#### Interpretation

- $e_t = E_{\max}$: fully saturated
- $e_t \approx 0$: critical depletion

The agent has **direct access** to its internal energy level.

---

### 9.2 Hunger Definition
The hunger drive is defined as a normalized function of energy:

$$
h_t = 1 - \frac{e_t}{E_{\max}}  
$$

Thus:

$$
h_t \in [0,1]  
$$

---

#### Interpretation

- $h_t = 0$: no hunger
- $h_t = 1$: maximal hunger

The hunger signal increases monotonically as energy decreases.

---

### 9.3 Hunger Drive Function
The hunger drive is defined as:

$$
D_{\text{hunger}}(x_t) = h_t  
$$

with:

- dependency only on $x_t$
- no dependency on $u_t$ or $m_t$

> In the baseline system, the hunger drive output is defined directly as the normalized hunger variable. Thus, the drive module is currently identity-mapped. But in advanced models we can include more dependencies for the $D_{hunger}$ function.
---

#### Key Property
The hunger drive is:

- purely internal
- state-based
- independent of perception

---
#### Drive Activation
Following the general definition in Section 8, the activation of the hunger drive is:

$$
d_H(t) = D_{\text{hunger}}(x_t)
$$

In the baseline system, this reduces to:

$$
d_H(t) = h_t
$$

---

##### Interpretation

* $h_t$: normalized internal hunger variable
* $d_H(t)$: resulting drive activation used by the policy

In the baseline system, both are identical. This represents a minimal formulation of the drive.

---

### 9.4 No Embedded World Knowledge
The hunger drive does **not** include:

- knowledge of where resources are
- knowledge of which observations lead to energy gain
- prediction of future energy changes

It only reflects the current internal deficit.

---

### 9.5 Interaction with the Action System
The hunger drive influences behavior through modulation:

- increasing preference for actions that **may restore energy**
- decreasing preference for irrelevant actions

However:

- the hunger drive does **not know** which actions are effective
- it only provides a scalar pressure signal

---

#### Important Constraint
There is no direct mapping such as:

$$
h_t \rightarrow \text{CONSUME}  
$$

Any such mapping must emerge through:

- policy structure
- interaction with observation $u_t$
- memory $m_t$

---

### 9.6 Coupling to Energy Dynamics
The hunger drive itself does not modify energy.

Energy changes are handled exclusively by the agent transition:

$$  
x_{t+1} = F_{agent}(x_t, u_t, a_t)  
$$

This includes:

- energy decrease due to actions
- energy increase due to successful interaction with the environment

---

#### Separation Principle

- Hunger reflects energy
- It does not control energy

---

### 9.7 Minimal Design Principle
The hunger drive is intentionally simple:

- linear function of energy
- no thresholds
- no nonlinearities
- no memory dependence

This ensures:

- interpretability
- no hidden dynamics
- clean baseline behavior

---

### 9.8 Role in the System
The hunger drive provides:

- a continuous internal pressure signal
- a motivation for sustained behavior
- a mechanism for survival constraints

Without this drive:

- behavior would be unconstrained
- no self-regulation would emerge

---

### Why this matters
This formulation avoids a critical modeling mistake:

> Encoding goal-directed behavior directly into the drive.

Instead:

- the drive only represents **need**
- the mapping from need to action must emerge

This keeps the system:

- mechanistic
- minimal
- extensible

---

## 10. Baseline Action Term
The baseline action term defines the agent’s **intrinsic action preferences** before modulation by internal drives.

It represents a neutral prior over actions that is independent of:

- internal needs (e.g. hunger)
- specific environmental semantics
- expected outcomes

---

### 10.1 Definition
The baseline action term assigns a score to each action:

$$
\psi_0(a) : \mathcal{A} \rightarrow \mathbb{R}  
$$

where:

- $\psi_0(a)$: baseline preference for action $a$

---

#### **Interpretation**
$\psi_0(a)$ represents a **default tendency** of the agent to select certain actions in the absence of drive influence.

---

### 10.2 Minimal Baseline
In the baseline system, the action term is defined as uniform:

$$
\psi_0(a) = 0 \quad \forall a \in \mathcal{A}  
$$

---

#### Implication

- All actions are equally preferred at the baseline level
- No action is intrinsically favored or penalized
- Behavior emerges only through:
    
    - drives
    - observations
    - memory

---

### 10.3 Separation from Environment
The baseline action term does **not depend on**:

- observation $u_t$
- memory $m_t$
- internal state $x_t$

Formally:

$$
\psi_0(a) \neq f(u_t, m_t, x_t)  
$$

---

#### Key Property
The baseline term encodes **no knowledge about the environment**.

- No preference for resource-related actions
- No avoidance of obstacles
- No spatial bias

---

### 10.4 Separation from Outcome Semantics
The baseline action term does **not encode**:

- energy gain
- energy cost
- success likelihood
- reward

---

#### Important Constraint
There is no assumption such as:

- “CONSUME is beneficial”
- “MOVE leads to exploration”

All such effects must arise from:

- system dynamics
- interaction with the environment
- drive modulation

---

### 10.5 Role in Action Selection
The baseline action term contributes to the policy through modulation:

$$
\tilde{p}(a) = \Gamma\bigl(a; \psi_0(a), d_H(t), x_t, u_t, m_t \bigr)  
$$

where:

- $\Gamma$: modulation function
- $d_H(t)$: hunger drive activation 

---

#### Interpretation

- $\psi_0(a)$ provides a neutral reference
- drives introduce directional bias
- observations and memory shape context

---

### 10.6 Design Principle
The baseline action term is intentionally minimal.

It serves only to:

- define a neutral starting point
- avoid implicit behavioral assumptions
- ensure that all structure emerges explicitly

---

### Why this matters
This definition prevents a subtle but critical modeling error:

> Embedding goal-directed behavior directly into the action prior.

By keeping the baseline uniform:

- the agent does not “know” what is useful
- all behavior must arise from interaction
- the system remains fully interpretable

---

### Critical Note
Any non-uniform definition of $\psi_0(a)$ would introduce implicit assumptions about:

- action usefulness
- environmental structure
- expected outcomes

Such assumptions are **explicitly excluded** from the baseline system.

---

## 11. Action Modulation System
The action modulation system defines how internal drives influence the agent’s action preferences.

It combines:

- the baseline action term
- the activation of internal drives

into a unified action preference score.

>The modulation framework defined in this section is generic.
>
>Concrete drive modules may define additional action-specific effects, including suppression or amplification terms, as long as they only depend on permitted inputs.

> This section defines the generic action modulation framework.
>
> The concrete baseline instantiation used in the present document employs only the Hunger Drive and uses a reduced modulation function $\phi_H(a, u_t)$, while other formally available inputs remain inactive.

---

### 11.1 Objective
The goal of the modulation system is to transform:

- neutral action preferences $\psi_0(a)$
- drive activations $e.g. (d_H(t))$

into **modulated action scores**:

$$
\psi(a \mid x_t, u_t, m_t)  
$$

which are then used by the policy.

---

### 11.2 General Formulation
The modulated action score is defined as:

$$
\psi(a) = \psi_0(a) + \sum_{i} d_i(t) \cdot \phi_i(a, u_t, m_t)  
$$

In the baseline system (single drive) the modulated action score is simply:

$$
\psi(a) = \psi_0(a) + d_H(t) \cdot \phi_H(a, u_t)  
$$

---

#### Components

- $\psi_0(a)$: baseline action term
- $d_H(t)$: hunger drive activation
- $\phi_H(a, u_t)$: action-specific modulation function

---

### 11.3 Role of the Modulation Function
The function:

$$
\phi_H(a, u_t)  
$$

defines how the hunger drive translates into **action-dependent preferences**.

It is the only component that connects:

- drive activation
- observation
- action structure

---

#### Important Constraint
$\phi_H$ must:

- only depend on $a, u_t, m_t$
- not depend on:
    
    - world state $s_t^{world}$
    - hidden environment variables
    - future outcomes

---

### 11.4 Minimal Baseline Definition
In the baseline system, $\phi_H$ is defined using only **local observable quantities**.

---

#### Consumption Modulation
For action $\text{CONSUME}$:

$$
\phi_H(\text{CONSUME}, u_t) = w_{\text{consume}} \cdot r_c(t)
$$

where:

- $r_c(t)$: locally observed resource intensity at the current cell
- $w_{\text{consume}} > 1$: consumption priority weight

This additional weighting factor reflects the behavioral priority of directly accessible resource over equally strong neighboring resource signals.

---

#### Movement Modulation
For movement actions, the hunger modulation function is defined direction-specifically:

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

where:

* $r_{up}(t)$: locally observed resource intensity in the upper neighboring cell
* $r_{down}(t)$: locally observed resource intensity in the lower neighboring cell
* $r_{left}(t)$: locally observed resource intensity in the left neighboring cell
* $r_{right}(t)$: locally observed resource intensity in the right neighboring cell

This preserves the directional structure of the local observation and allows movement preferences to depend on which neighboring direction currently contains resource. At the same time, the current-cell resource signal used by $\text{CONSUME}$ may be assigned a stronger action-specific weight than neighboring movement signals, reflecting the fact that directly available energy is behaviorally more salient than equally strong adjacent opportunity.

 > Higher neighboring resource intensity increases the relative preference for movement

---

#### Stay Action
In general we can define no modulation for the STAY Action:
$$  
\phi_H(\text{STAY}, u_t) = 0  
$$

But in the baseline system, the STAY action is explicitly suppressed under increasing hunger:

$$
ψ(STAY) = -\lambda_{stay} \cdot d_H(t)
$$
where:

- $\lambda_{stay}$ ≥ 0 is a configurable parameter
- $d_H(t)$ is the hunger activation

This ensures that inactivity becomes increasingly unlikely as hunger increases.

---

### 11.5 Interpretation
The modulation function implements a simple local directional coupling:

- higher resource intensity at the current cell increases the relative preference for **CONSUME**
- higher resource intensity in a specific neighboring cell increases the relative preference for movement **in that same direction**
- the current-cell resource signal may be weighted more strongly than equally strong neighboring signals through $w_{\text{consume}}$

This enables the agent to:

- consume directly available resource with prioritized probability
- move toward locally visible resource when it is not yet directly reachable

without requiring:

- a world model
- planning
- memory-based inference

The coupling remains:

- local
- instantaneous
- non-predictive

---

### 11.6 Minimal Behavioral Coupling Assumption
The definition of $\phi_H$ introduces a minimal structural assumption:

> Locally observed resource intensity is used as an action-specific heuristic signal for action prioritization.

This means:

- resource at the current cell increases the preference for **CONSUME**
- resource in a neighboring cell increases the preference for movement toward that specific neighboring cell
- directly available resource may be behaviorally prioritized over equally strong neighboring signals through the parameter $w_{\text{consume}}$

This does **not** imply that the agent:

- understands the concept of “food”
- predicts future reward
- possesses a map or world model

Instead, the system is constructed such that directly observable local resource structure modulates action preference in an explicitly action-specific way.

---

### 11.7 Final Action Score
Given $\psi_0(a) = 0$, the final score simplifies to:

$$
\psi(a) = d_H(t) \cdot \phi_H(a, u_t)
$$

In the baseline system, $\phi_H(a, u_t)$ is action-specific and may include explicit weighting terms for selected actions, such as the prioritized current-cell consumption signal.

---

### 11.8 Design Principles
The modulation system is constrained to:

* scalar-valued signals
* local observability
* absence of explicit prediction
* explicit and transparent assumptions

---

### Why this matters
This formulation ensures:

* behavior is driven by internal need (hunger)
* behavior is shaped by local perception
* no hidden world knowledge is introduced

while explicitly acknowledging the presence of a minimal heuristic coupling.

---

### Critical Note
The modulation function is the **first source of structured behavior** in the system.

Its definition must remain:

* minimal
* explicit
* controlled

to preserve the interpretability and integrity of the baseline model.

---

## 12. Policy
The policy defines how the agent selects an action based on the modulated action scores.

It maps:

$$  
\psi(a \mid x_t, u_t, m_t)  
$$

to a probability distribution over actions.

> This section defines the generic policy interface.
>
> In the present baseline instantiation, episodic memory is maintained but not behaviorally consulted, even if the generic policy signature formally permits memory-dependent extensions.

---

### 12.1 Objective
The policy must:

- select actions based on current internal state and perception
- allow behavior under uncertainty (absence of informative signals)
- remain consistent with system constraints:
    
    - no planning
    - no world model
    - no goal representation
    - no explicit exploration strategy

---

### 12.2 Stochastic Policy Definition
The policy is defined as a Softmax distribution over action scores:

$$  
P(a \mid x_t, u_t, m_t)
=
\frac{\exp\left(\beta \cdot \psi(a)\right)}  
{\sum_{a'} \exp\left(\beta \cdot \psi(a')\right)}  
$$

---

#### Components

- $\psi(a)$: modulated action score
- $\beta > 0$: inverse temperature parameter
    

---

#### Interpretation

- high $\psi(a)$ → higher selection probability
- low $\psi(a)$ → lower selection probability
- similar scores → near-uniform distribution

---

### 12.3 Rationale for Stochasticity
A deterministic policy:

$$  
a_t = \arg\max_a \psi(a)  
$$

would lead to:

- deadlocks in low-information states
- repetitive behavior
- lack of exploration

The stochastic policy ensures:

> the agent can act even when no informative signal is available.

---

### 12.4 Behavior in Different Regimes

#### Case 1: Strong Current-Cell Resource Signal

- $\psi(\text{CONSUME})$ becomes strongly competitive, and may dominate the action distribution due to the weighted current-cell resource signal
    → high probability for CONSUME

---

#### Case 2: Weak Directional Signal (Neighbor Resources)

- movement actions slightly preferred  
    → probabilistic movement
    

---

#### Case 3: No Local Signal

- $\psi(a) \approx 0$ for all $a$  
    → distribution approaches uniform

---

#### Consequence
The agent exhibits:

- directed behavior when information is available
- random exploration when information is absent

---

### 12.5 Hunger-Dependent Modulation of Passivity
To couple internal state to behavioral activity, the policy incorporates a **hunger-dependent suppression of the STAY action**.

---

#### Modified STAY Score

$$
\psi(\text{STAY}) = - \lambda_{stay} \cdot d_H(t)  
$$

with:

- $\lambda_{stay} > 0$: scaling parameter
- $d_H(t)$: hunger drive activation

---

#### Effect

- low hunger → STAY remains competitive
- high hunger → STAY becomes unlikely

---

#### Interpretation
This mechanism implements:

> increased behavioral activation under energy deficit

without introducing:

- a separate exploration drive
- explicit search strategies

---

### 12.6 Emergent Exploration Behavior
In the absence of local resource signals:

- all movement actions have similar scores
- STAY is suppressed when hunger is high

→ the policy produces:

> random movement across the environment

---

#### Important Clarification
This behavior is:

- not goal-directed search
- not memory-based navigation
- not predictive

It is:

> stochastic motion induced by lack of information and internal pressure

---

### 12.7 Role of Temperature Parameter $\beta$
The parameter $\beta$ controls the trade-off between:

- randomness
- score sensitivity

---

#### Regimes

- high $\beta$: near-deterministic selection
- low $\beta$: near-uniform randomness

---

#### Baseline Choice
In System A:

- $\beta$ is treated as a constant

---

#### Design Note
A hunger-dependent $\beta$ could be introduced, but is excluded in the baseline to:

- avoid additional coupling mechanisms
- maintain interpretability

---

### 12.8 Constraints and Limitations
The policy does not:

- use memory for navigation
- plan future actions
- represent goals
- optimize trajectories

---

#### Implication
All behavior is:

- reactive
- local
- instantaneous

---

### 12.9 Summary
The policy:

- transforms action scores into probabilities
- enables action under uncertainty
- couples internal state (hunger) to behavioral activation
- produces exploration as a consequence of stochasticity

---

### Critical Perspective
The policy introduces:

- randomness as a mechanism for exploration
- a minimal bias against passivity under hunger

It does not introduce:

- intelligence
- strategy
- knowledge

---

## 13. State Transition Function

### 13.1 Objective
The state transition function defines how the complete system evolves from time $t$ to time $t+1$ after an action has been selected.

Because the baseline system cleanly separates:

- the **external world state**
- the **internal agent state**
- and the **episodic perceptual memory**

the transition must update all three in a coordinated manner.

The purpose of this section is therefore to define a **joint transition function** that is:

- mechanistically explicit
- temporally consistent
- directly implementable
- and fully aligned with the previously defined environment and sensor model

---

### 13.2 Why a Joint Transition Function Is Required
The baseline system contains two distinct dynamical subsystems:

1. **World dynamics**
    
    - physical position of the agent
    - resource regeneration
    - resource depletion through consumption

2. **Agent dynamics**
    
    - internal energy
    - derived internal quantities
    - behavioral viability

These two subsystems cannot be updated independently, because they are coupled by action:

- an action changes the world
- the changed world produces an interaction outcome
- that interaction outcome changes the agent

Thus, the transition must be defined at the level of the **combined system**.

---

### 13.3 Combined System State
We define the full system state at time (t) as:

$$
\Sigma_t = (x_t, m_t, s_t^{world})  
$$

where:

- $x_t$: internal agent state
- $m_t$: episodic perceptual memory
- $s_t^{world}$: world state

The system evolves according to:

$$
\Sigma_{t+1} = F(\Sigma_t, a_t)  
$$

or explicitly:

$$
(x_{t+1}, m_{t+1}, s_{t+1}^{world}) = F(x_t, m_t, s_t^{world}, a_t)  
$$

---

### 13.4 Decomposition of the Transition
The transition function is decomposed into four ordered components:

1. **World transition**
2. **Observation update**
3. **Agent transition**
4. **Memory update**

Formally:

$$
s_{t+1}^{world} = F_{world}(s_t^{world}, a_t)  
$$

$$
u_{t+1} = S(s_{t+1}^{world})  
$$

$$
x_{t+1} = F_{agent}(x_t, a_t, s_t^{world}, s_{t+1}^{world})  
$$

$$
m_{t+1} = G_{mem}(m_t, u_{t+1})  
$$

This ordering ensures that memory records the **new perceptual state that actually results from the action**.

---

### 13.5 World Transition

#### 13.5.1 World State Structure
The world state is defined as:

$$  
s_t^{world} = (\mathcal{E}_t, p_t)  
$$

where:

- $\mathcal{E}_t$: environment configuration
- $p_t$: physical position of the agent in the grid

The environment configuration contains:

- current resource field $R_i(t)$
- fixed maximum capacities $R_i^{\max}$
- fixed regeneration rates $\alpha_i$
- fixed obstacle structure $O_i$

---

#### 13.5.2 Regeneration Phase
In accordance with the environmental model, resources regenerate first.

For every traversable cell (i):

$$  
\widetilde{R}_i(t) = R_i(t) + \alpha_i \bigl(R_i^{\max} - R_i(t)\bigr)  
$$

with the constraint:

$$  
0 \le \widetilde{R}_i(t) \le R_i^{\max}  
$$

For obstacle cells, resource dynamics are not applied.

---

#### 13.5.3 Position Update
The new physical position is determined by the world transition rule:

$$
p_{t+1} = T(p_t, a_t)  
$$

where $T$ is the position transition function defined by the world.

Its baseline interpretation is:

- if $a_t$ is a movement action and the target cell is traversable and within bounds, then the agent moves
- otherwise, the position remains unchanged
- for `STAY` and `CONSUME`, the position remains unchanged
    

Thus:

$$ 
p_{t+1} =  
\begin{cases}  
T(p_t, a_t) & \text{if } a_t \in {\text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}} \\
p_t & \text{if } a_t \in {\text{STAY}, \text{CONSUME}}  
\end{cases}  
$$

---

#### 13.5.4 Consumption Update
Consumption operates on the **current cell** and only if the selected action is `CONSUME`.

Let the current cell before interaction be denoted by:

$$
c_t = p_t  
$$

The amount of resource extracted from the cell is defined as:

$$
\Delta R_t^{cons} =  
\begin{cases}  
\min\bigl(\widetilde{R}_{c_t}(t), c_{\max}\bigr) & \text{if } a_t = \text{CONSUME} \\ 
0 & \text{otherwise}  
\end{cases}  
$$

where:

- $c_{\max} > 0$: maximum consumable amount per time step

The updated resource field becomes:

$$
R_i(t+1) =  
\begin{cases}  
\widetilde{R}_i(t) - \Delta R_t^{cons} & \text{if } i = c_t \text{ and } a_t = \text{CONSUME} \\
\widetilde{R}_i(t) & \text{otherwise}  
\end{cases}  
$$

---

#### 13.5.5 Updated World State
The updated world state is therefore:

$$
s_{t+1}^{world} = (\mathcal{E}_{t+1}, p_{t+1})  
$$

with:

$$
\mathcal{E}_{t+1} = \bigl(R(t+1), R^{\max}, \alpha, O\bigr)  
$$

---

### 13.6 Observation Update
After the world has been updated, the new observation is computed by the sensor function:

$$
u_{t+1} = S(s_{t+1}^{world})  
$$

This ensures that the agent’s next internal update and memory entry are based on the **actually resulting local perceptual situation**, not on the previous one.

---

### 13.7 Agent Transition

#### 13.7.1 Internal State Structure
The internal agent state is defined as:

$$
x_t = (e_t, \xi_t)  
$$

where:

- $e_t$: internal energy level
- $\xi_t$: optional auxiliary internal variables

---

#### 13.7.2 Environmental Energy Transfer
The energy made available to the agent through successful consumption is defined by:

$$
\Delta e_t^{env} = \kappa \cdot \Delta R_t^{cons}  
$$

where:

- $\kappa > 0$: conversion factor from consumed environmental resource to internal agent energy

This term is zero unless actual resource was extracted from the current cell.

---

#### 13.7.3 Action Cost
Each action incurs an internal energy cost:

$$
c(a_t)  
$$

with a baseline definition of the form:

$$
c(a_t) =  
\begin{cases}  
c_{move} & \text{if } a_t \in {\text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}} \\  
c_{consume} & \text{if } a_t = \text{CONSUME} \\
c_{stay} & \text{if } a_t = \text{STAY}  
\end{cases}  
$$

where all costs satisfy:

$$  
c_{move}, c_{consume}, c_{stay} \ge 0  
$$

In the baseline system, action cost depends on the selected action itself, not on whether the action was successful.

---

#### 13.7.4 Energy Update
The internal energy update is defined as:

$$
e_{t+1} = \mathrm{clip}\Bigl(e_t - c(a_t) + \Delta e_t^{env}, 0, E_{\max}\Bigr)  
$$

where:

- $E_{\max}$: maximum internal energy level
- $\mathrm{clip}(\cdot)$: clipping to the interval $[0, E_{\max}]$

This equation ensures:

- energy decreases through metabolic or action-related expenditure
- energy increases only through actual environmental consumption
- the resulting value remains bounded

---

#### 13.7.5 Auxiliary Internal Variables
Auxiliary internal variables are updated by:

$$  
\xi_{t+1} = H(\xi_t, e_{t+1})  
$$

In the minimal baseline, no additional auxiliary dynamics are required. Therefore, $H$ may be treated as the identity function unless specific derived variables are explicitly stored.

If hunger is stored explicitly rather than derived on demand, it may be updated as:

$$  
h_{t+1} = 1 - \frac{e_{t+1}}{E_{\max}}  
$$

---

#### 13.7.6 Updated Agent State
The updated internal state is therefore:

$$
x_{t+1} = (e_{t+1}, \xi_{t+1})  
$$

---

### 13.8 Memory Update
The episodic perceptual memory is updated after the new observation has been computed:

$$
m_{t+1} = G_{mem}(m_t, u_{t+1})  
$$

In the baseline system:

$$
G_{mem}(m_t, u_{t+1}) = m_t \cup {u_{t+1}}  
$$

or, if a bounded-capacity implementation is used, by appending $u_{t+1}$ and removing the oldest entry when necessary.

---

#### Interpretation
This means that memory stores the **newly resulting local perceptual view** after the action has taken effect.

This is the appropriate baseline choice because:

- the stored memory entry corresponds to the actually realized next situation
- the memory remains aligned with the forward evolution of the system
- no lag between world transition and memory update is introduced

---

### 13.9 Terminal Condition
The baseline system defines death purely through internal energy collapse.

If:

$$
e_{t+1} = 0  
$$

then the agent is considered dead.

In this case:

- no further actions are admissible
- no further state evolution occurs

Thus, $e = 0$ acts as a terminal condition without requiring an additional explicit death state variable.

---

### 13.10 Final Joint Transition
Collecting all parts, the full transition is:

$$  
F(x_t, m_t, s_t^{world}, a_t)
=
\Bigl(  
x_{t+1},  
m_{t+1},  
s_{t+1}^{world}  
\Bigr)  
$$

with:

$$  
s_{t+1}^{world}
=
F_{world}(s_t^{world}, a_t)  
$$

$$  
u_{t+1}
=
S(s_{t+1}^{world})  
$$

$$ 
x_{t+1}
=
F_{agent}(x_t, a_t, s_t^{world}, s_{t+1}^{world})  
$$

$$  
m_{t+1}
=
G_{mem}(m_t, u_{t+1})  
$$

This defines a fully mechanistic and jointly consistent state transition for the baseline system.

---

### 13.11 Summary
The state transition function:

- updates the world and agent in a coordinated way
- ensures that energy transfer is grounded in actual environmental interaction
- preserves the separation between:
    
    - external world dynamics
    - internal agent dynamics
    - perceptual memory

It introduces no:

- planning
- world model
- semantic reasoning
- or hidden predictive structure

Instead, all temporal evolution arises from:

- action
- local interaction
- bounded resource dynamics
- and internal energy regulation

---

## 14. Execution Cycle

### 14.1 Overview
The execution cycle defines the temporal ordering of perception, decision-making, and state evolution in System A.

At each discrete time step $t$, the agent:

- receives sensory input from the environment
- evaluates internal drives
- selects and executes an action
- undergoes a state transition defined by the system dynamics
- updates its memory

The cycle is strictly causal and sequential.  
All computations at time $t$ depend only on information available at that time.

---

### 14.2 Temporal Structure
Let:

- $x_t$ be the internal state after the previous transition
- $u_t$ be the sensory input derived from the environment at time $t$
- $a_t$ be the action selected at time $t$
- $x_{t+1}$ be the next internal state
- $u_{t+1}$ be the next sensory input
- $m_t$ be the memory state

---

#### Cycle Definition
The execution cycle proceeds as follows:

---

#### Step 1: Perception

$$
u_t = S(s_t^{world})  
$$

The agent receives sensory input from the environment based on the current state.

---

#### Step 2: Drive Evaluation

$$
d_i(t) = D_i(x_t, u_t, m_t)  
$$

The internal drive system computes motivational signals based on the current state and perception.

In the baseline configuration, this consists solely of the hunger drive. And this has a reduced function (does not depend on memory or sensory data).

> In the present baseline instantiation, only the hunger drive is behaviorally active, and episodic memory is not yet consulted.

---

#### Step 3: Action Selection

$$
a_t \sim \pi(x_t, u_t, m_t, d_1(t), \dots, d_n(t))
$$

The policy selects an action based on:

- current internal state
- current sensory input
- current drive signals


> In the present baseline instantiation, this reduces operationally to a memory-inactive, hunger-driven policy over the modulated action scores.
---

#### Step 4: State Transition

$$
(x_{t+1}, m_{t+1}, s_{t+1}^{world}) = F(x_t, m_t, s_t^{world}, a_t)
$$

The system state evolves according to the state transition function.

This includes:

- effects of the action
- environmental interactions
- internal dynamics (e.g., energy consumption, regeneration)

The transition function is the only component that modifies the internal state.

---

#### Step 5: Termination Check
A termination condition is evaluated:

$$
\text{if } T(x_{t+1}) = \text{true} \rightarrow \text{stop}  
$$

For example:

- energy level reaches zero (agent "dies")

If the condition is not met, the next cycle begins with $t \leftarrow t + 1$.

---

### 14.3 Causality and Information Flow
The execution cycle enforces strict causality:

- No future information is used at time $t$
- All decisions depend only on $x_t, u_t, d_t$
- Memory does not influence the policy in the baseline system

This ensures that behavior emerges purely from:

- current state
- immediate perception
- internal drives

without planning, prediction, or historical reasoning.

---

### 14.4 Separation of Concerns
The execution cycle separates system responsibilities into distinct components:

| Component       | Role                         |
| --------------- | ---------------------------- |
| Observation $O$ | Maps state to perception     |
| Drives $D$      | Computes internal motivation |
| Policy $\pi$    | Selects actions              |
| Transition $F$  | Evolves system state         |
| Memory $M$      | Records observations         |

The transition function $F$ exclusively governs all state changes, including internal dynamics such as energy updates.

The execution cycle itself does not modify the state, but defines the order in which components are applied.

---

### 14.5 Determinism and Extensions
In the baseline configuration:

- All components may be deterministic or stochastic
- The execution order remains fixed

Future extensions may introduce:

- memory-based policies
- predictive models
- multi-agent interactions

without altering the fundamental structure of the execution cycle.

---

## 15. Example Behavioral Regimes

### 15.1 Purpose
This section illustrates the types of behavior that emerge from System A under different environmental and internal conditions.

The examples demonstrate that non-trivial, adaptive behavior arises solely from:

- local perception
- internal drive dynamics
- reactive action selection

without memory usage, planning, or world modeling.

---

### 15.2 Assumptions
All scenarios assume:

- a 2D grid environment
- local perception $u_t$ limited to a small neighborhood
- food sources that increase energy upon consumption
- energy decay over time (handled in $F$)
- a single drive: hunger

No additional mechanisms are introduced.

---

### 15.3 Regime 1: Stable Survival (Energy-Rich Environment)

#### Description
The environment contains sufficient food distributed such that the agent frequently encounters it within its local perception range.

---

#### Observed Behavior

- The agent moves through the environment with moderate variability
- When food is present at the current cell, the probability of **CONSUME** increases strongly and typically dominates local action selection
- Energy levels remain high and stable

---

#### Interpretation
This behavior emerges from:

- hunger drive decreasing as energy increases
- immediate perception-action coupling
- absence of long-term strategy

The agent appears stable, but:

- it does not seek food proactively
- it only reacts when food is locally observable

---

#### Consistency Check

✔ No memory usage  
✔ No prediction  
✔ Behavior fully determined by $x_t, u_t$

---

### 15.4 Regime 2: Reactive Foraging (Moderate Scarcity)

#### Description
Food is present but less frequent. The agent must move to encounter it.

---

#### Observed Behavior

- The agent moves continuously through the environment
- When food becomes visible in a specific neighboring direction, the corresponding movement action receives increased preference
* When food is present on the current cell, the (weighted) preference for **CONSUME** increases immediately
- Energy fluctuates but remains within viable bounds

---

#### Interpretation
The agent exhibits what appears to be **goal-directed behavior**, but:

- no explicit goal representation exists
- no path planning occurs

The behavior is a direct consequence of:

- hunger-modulated action preferences
- local perception

---

#### Important Clarification
What looks like “searching” is not true exploration:

- no novelty estimation
- no memory of visited locations
- no coverage strategy

The agent simply **moves and reacts**.

---

#### Consistency Check

✔ No hidden exploration mechanism  
✔ No dependence on $m_t$  
✔ Compatible with purely reactive policy $\pi(x_t, u_t, d_t)$

---

### 15.5 Regime 3: Starvation (Low Resource Density)

#### Description
Food is rare or spatially sparse beyond the agent’s local perception range.

---

#### Observed Behavior

- The agent continues to move according to its policy
- Food is rarely encountered
- Energy decreases steadily
- The system eventually reaches termination (death condition)

---

#### Interpretation
The agent fails to survive because:

- it has no mechanism to:
    
    - remember past food locations
    - plan movement toward expected resources
    - adapt behavior based on long-term outcomes

This regime highlights the limitations of the baseline system.

---

#### Consistency Check

✔ Death emerges naturally via $F$ and termination condition  
✔ No fallback strategies (correct for baseline)

---

### 15.6 Regime 4: Local Oscillation Around Resources

#### Description
Food appears in clusters or repeatedly in the same region.

---

#### Observed Behavior

- The agent remains within a local region for extended periods
- Movement becomes spatially constrained
- Frequent consumption maintains energy

---

#### Interpretation
This can create the appearance of:

- “preference” for a location
- “staying near food”

However:

- no location representation exists
- no memory of the region is stored

The behavior emerges because:

- food repeatedly appears within perception range
- the agent continuously reacts to local stimuli

---

#### Consistency Check

✔ No spatial memory required  
✔ Fully explained by repeated local perception $u_t$

---

### 15.7 Regime 5: Random Drift in Absence of Stimuli

#### Description
No food is present within perception for extended periods.

---

#### Observed Behavior

- The agent continues moving
- Movement appears random or weakly structured
- No directional persistence toward resources

---

#### Interpretation
In the absence of external stimuli:

- behavior is driven solely by the policy baseline
- hunger may modulate intensity but cannot create direction
    

This highlights:

- lack of exploration strategy
- absence of internal modeling

---

#### Consistency Check

✔ No implicit search algorithm  
✔ Movement arises from policy, not planning

---

### 15.8 Boundary of Capability
These regimes define the behavioral limits of System A.

---

#### What the system can do

- react to local stimuli
- maintain internal energy under favorable conditions
- exhibit adaptive-looking behavior

---

#### What the system cannot do

- plan ahead
- remember past states
- predict future outcomes
- build spatial or temporal models

---

### 15.9 Emergent Behavior Without Cognition
The key insight from these regimes is:

> Behavior that appears adaptive or goal-directed can emerge from purely reactive mechanisms.

This does not imply:

- understanding
- intention
- awareness

It is the result of:

- local coupling between perception, drives, and action

---

## 16. Minimal Configuration Parameters

### 16.1 Purpose
A concrete implementation of System A requires a finite set of initialization and control parameters. These parameters define the external environment, the agent’s initial internal condition, the perceptual scaling, the action-selection dynamics, and the memory mechanism.

The purpose of this section is to specify the minimal parameter set required to instantiate the baseline system in a fully explicit and experimentally controllable way.

The configuration remains deliberately small. It must be sufficient to:

- initialize the grid world,
- define local resource dynamics,
- define the sensor scaling,
- initialize the agent,
- compute hunger-based action scores,
- and execute the stochastic policy.

No parameters for planning, world modeling, semantic memory, or learned adaptation are included.

---

### 16.2 Environment Parameters
The external world is a discrete 2D grid with locally regenerating resources and optional obstacles. A minimal implementation must specify the following parameters.

### 16.2.1 Spatial Parameters

- $W$: grid width
- $H$: grid height

These determine the spatial extent of the world:

$$
\mathcal{G} = {(x,y)\mid x \in [0,W-1], y \in [0,H-1]}  
$$

#### 16.2.2 Cell-State Parameters
For each cell $i \in \mathcal{G}$, the world must define:

- $R_i^{\max} \ge 0$: maximum resource capacity
- $\alpha_i \in [0,1]$: regeneration rate
- $O_i \in {0,1}$: obstacle indicator

These determine whether the cell is traversable and how much renewable resource it can contain.

#### 16.2.3 Resource Initialization
A concrete initialization must specify the initial resource field:

$$
R_i(0) \in [0, R_i^{\max}]  
$$

This may be assigned randomly, procedurally, or manually, but must remain explicit.

#### 16.2.4 Consumption Parameter

- $c_{\max} > 0$: maximum amount of resource that can be consumed in one time step

This parameter determines the upper bound of resource extraction during the `CONSUME` action.

---

### 16.3 Sensor Parameters
The sensor model maps the local neighborhood into a fixed observation vector consisting of traversability and normalized resource intensity. A minimal implementation must specify:

#### 16.3.1 Neighborhood Structure
The baseline system uses a fixed local neighborhood:

$$
\mathcal{N}(p_t)=\{c_t,c_{up},c_{down},c_{left},c_{right}\}  
$$

Thus, the perceptual topology is a required part of the configuration.

#### 16.3.2 Resource Scaling Parameter

- $R_{\text{scale}} > 0$: normalization constant for resource intensity

The resource signal is defined as:

$$
r_j(t)=\frac{R_j(t)}{R_{\text{scale}}}  
$$

This parameter determines the numerical scale of the sensory resource signal and therefore directly affects the magnitude of the hunger modulation term.

---

### 16.4 Agent Initialization Parameters
The agent must be initialized with an internal state and a physical starting location in the world. Although the agent does not know its absolute position, the simulation must specify it externally as part of the world state.

#### 16.4.1 Internal Energy Initialization

- $E_{\max} > 0$: maximum internal energy
- $e_0 \in [0, E_{\max}]$: initial internal energy

The hunger signal is derived from energy as:

$$
d_H(t)=1-\frac{e_t}{E_{\max}}  
$$

Thus both $E_{\max}$ and $e_0$ are required.

#### 16.4.2 Initial Position

- $p_0 \in \mathcal{G}$: initial world position of the agent

This must satisfy:

- $p_0$ lies within the grid
- the corresponding cell is traversable

The position is part of the external world state, not the internal agent state.

---

### 16.5 Action and Energy-Transition Parameters
The baseline system requires explicit energetic parameters for action execution and for conversion of consumed environmental resource into internal energy.

#### 16.5.1 Action Cost Parameters
A cost function must be defined for all actions:

$$
c:\mathcal{A}\rightarrow \mathbb{R}_{\ge 0}  
$$

with the action set

$$  
\mathcal{A}=\{\text{UP},\text{DOWN},\text{LEFT},\text{RIGHT},\text{CONSUME},\text{STAY}\}  
$$

At minimum, the implementation must specify:

- movement cost for `UP`, `DOWN`, `LEFT`, `RIGHT`
- consume cost for `CONSUME`
- stay cost for `STAY`

These costs enter directly into the energy update.

#### 16.5.2 Resource-to-Energy Conversion

- $\kappa > 0$: conversion factor from consumed environmental resource to internal energy

The environmental transfer term is:

$$
\Delta e_t^{env} = \kappa \cdot \Delta R_t^{cons}  
$$

This parameter determines how strongly successful consumption replenishes the internal energy reserve.

---

### 16.6 Hunger Modulation Parameters
The baseline system uses a hunger-driven action modulation function based only on internal energy and current local observation. The following parameters must be specified.

#### 16.6.1 Hunger Function
The baseline choice is:

$$
d_H(t)=1-\frac{e_t}{E_{\max}}  
$$

This introduces no additional free parameter beyond $E_{\max}$, but if another monotonic hunger mapping is used in an implementation, its form must be specified explicitly.

#### 16.6.2 Heuristic Coupling Structure
The hunger-modulated score is based on a local heuristic coupling:

$$
\psi(a)=d_H(t)\cdot \phi_H(a,u_t)
$$

Thus, the implementation must specify the exact form of $\phi_H$.

In the baseline system, this coupling is action-specific and depends only on local observable resource intensities:

$$
\phi_H(\text{CONSUME}, u_t) = w_{\text{consume}} \cdot r_c(t)
$$

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

where:

- $w_{\text{consume}} > 1$ is the consumption priority weight

This parameter ensures that directly accessible resource can be behaviorally prioritized over equally strong neighboring resource signals.

#### 16.6.3 Consumption Priority Parameter

- $w_{\text{consume}} > 1$: consumption priority weight

This parameter scales the local current-cell resource signal used by the **CONSUME** action:

$$
\phi_H(\text{CONSUME}, u_t)=w_{\text{consume}} \cdot r_c(t)
$$

It expresses the baseline assumption that directly accessible resource is behaviorally more salient than equally strong neighboring resource signals.

#### 16.6.4 STAY Suppression Parameter

- $\lambda_{\text{stay}} > 0$: hunger-dependent suppression strength for the `STAY` action

The modified score is:

$$
\psi(\text{STAY})=-\lambda_{\text{stay}}\cdot d_H(t)  
$$

This parameter is essential, because it prevents passivity from dominating under strong energy deficit and enables stochastic outward motion in low-information states.

---

### 16.7 Policy Parameters
The action-selection mechanism is a Softmax policy over the hunger-modulated scores. The baseline implementation requires:

#### 16.7.1 Temperature Parameter

- $\beta > 0$: inverse temperature parameter
    

The policy is defined as:

$$
P(a\mid x_t,u_t)=  
\frac{\exp(\beta \cdot \psi(a))}  
{\sum_{a'}\exp(\beta \cdot \psi(a'))}  
$$

This parameter determines the trade-off between:

- randomness under weak score differences
- strong preference for higher-scoring actions when directional local signals are present

It is held constant in the baseline system.

---

### 16.8 Memory Parameters
The baseline system includes episodic perceptual memory as a maintained but behaviorally passive subsystem. It is updated after each transition but does not yet directly influence hunger-based action selection.

A minimal implementation must still specify the structural parameters of this memory.

#### 16.8.1 Memory Horizon or Capacity
Because memory is finite in practice, the implementation must define one of the following:

- fixed memory horizon $k$
- fixed memory capacity $M_{\max}$

This determines how many past observations are retained:

$$
m_t=(u_{t-k},u_{t-k+1},\dots,u_t)  
$$

#### 16.8.2 Memory Update Rule
The update rule must be fixed explicitly:

- append-only update with retention window
- FIFO replacement, if capacity is bounded
    

In the baseline system, only observations are stored. No action labels, energy outcomes, or semantic tags are included.

---

### 16.9 Termination Parameters
The baseline system requires at least one terminal viability condition:

- agent death when internal energy is fully depleted
    

Formally:

$$
e_{t+1}=0 \Rightarrow \text{termination}  
$$

Thus, the implementation must specify whether energy is clipped to the interval $[0,E_{\max}]$ and whether simulation halts immediately once depletion is reached. The current baseline assumes termination at zero energy.

---

### 16.10 Summary of the Minimal Parameter Set
A minimal implementation of System A therefore requires the explicit specification of:

#### World

- $W, H$
- $R_i^{\max}$
- $\alpha_i$
- $O_i$
- $R_i(0)$
- $c_{\max}$

#### Sensor

- neighborhood definition
- $R_{\text{scale}}$

#### Agent

- $E_{\max}$
- $e_0$
- $p_0$

#### Transition

- action cost function $c(a)$
- conversion factor $\kappa$
    

#### Behavior

- precise form of $\phi_H(a,u_t)$
- $\lambda_{\text{stay}}$
- $w_{consume}$
- $\beta$

#### Memory

- memory horizon or capacity
- memory update policy

#### Termination

- zero-energy termination rule

---

### 16.11 Design Rationale
This parameterization is intentionally minimal.

It is sufficient to:

- instantiate a non-trivial survival environment,
- produce hunger-modulated reactive behavior,
- enable stochastic movement under uncertainty,
- and maintain a passive episodic memory trace,

while avoiding the introduction of:

- world models,
- predictive search,
- semantic knowledge,
- learned valuation,
- or memory-driven decision rules.

In this sense, the parameter set defines the baseline system as an experimental laboratory for studying how much adaptive behavior can emerge from local perception, internal deficit, and explicit mechanistic coupling alone.

---

## 17. Validation Criteria

### 17.1 Purpose
This section defines the criteria used to validate the correctness and integrity of System A.

Validation serves two distinct goals:

1. Functional correctness
   The system behaves according to its formal definitions.

2. Conceptual integrity
   The system does not exhibit capabilities that exceed the intended baseline (e.g., memory-based reasoning, planning, or prediction).

Validation is therefore both:

* positive (what must happen)
* restrictive (what must not happen)

---

### 17.2 Structural Consistency Checks
These checks ensure that the system implementation adheres to the formal architecture.

---

#### 17.2.1 State Transition Integrity

Verify that:

$$
(x_{t+1}, m_{t+1}, s_{t+1}^{world}) = F(x_t, m_t, s_t^{world}, a_t)
$$

- All updates of the joint system state occur exclusively through \(F\)
- No other component modifies \(x_t\), \(m_t\), or \(s_t^{world}\) outside the defined transition

✔ Ensures a single source of truth for system dynamics

---

#### 17.2.2 Execution Order Consistency
Verify that the execution cycle strictly follows:

1. perception
2. drive evaluation
3. action selection
4. joint state transition
5. termination check

> Observation Update and Memory Update are part of the Joint Transition Function.

No step may be reordered or skipped.

✔ Ensures causal correctness

---

#### 17.2.3 Memory Isolation
Verify that:

- memory is updated as defined
- memory is not consulted by the policy $\pi$
- memory is not consulted by drive computation in the present baseline instantiation
- memory is not used for prediction, state evaluation, or navigation

✔ Ensures baseline remains non-learning

---

#### 17.2.4 Drive Scope Restriction
Verify that:

* only the hunger drive is active
* no additional drives influence action selection

✔ Prevents accidental reintroduction of exploration or other behaviors

---

### 17.3 Behavioral Validation
These criteria validate observable system behavior under controlled conditions.

---

#### 17.3.1 Survival Feasibility
In an environment with sufficient resource density:

* the agent should maintain non-zero energy over long horizons
* energy fluctuations remain bounded

✔ Confirms that the system can sustain itself under favorable conditions

---

#### 17.3.2 Starvation Under Scarcity
In an environment with low resource density:

* the agent must eventually reach the termination condition

✔ Confirms absence of hidden strategies or adaptive learning

---

#### 17.3.3 Immediate Reactivity
When a resource appears in local perception:

* the probability of selecting actions leading to consumption increases immediately

✔ Confirms correct coupling between perception and action

---

#### 17.3.4 No Long-Term Adaptation
Across repeated runs in identical environments:

* no improvement in survival time occurs
* behavior distributions remain statistically consistent

✔ Confirms absence of learning or memory-driven adaptation

---

### 17.4 Policy and Stochasticity Checks

---

#### 17.4.1 Softmax Consistency
Verify that action probabilities follow:

$$
P(a \mid x_t, u_t) =
\frac{\exp(\beta \cdot \psi(a))}
{\sum_{a'} \exp(\beta \cdot \psi(a'))}
$$

* probabilities sum to 1
* higher scores yield higher probabilities

✔ Confirms correct policy implementation

---

#### 17.4.2 Temperature Sensitivity
Vary $\beta$:

* low $\beta$ → near-random behavior
* high $\beta$ → near-deterministic behavior

✔ Confirms proper stochastic control

---

#### 17.4.3 STAY Suppression Effect
Under high hunger:

* probability of `STAY` decreases significantly

✔ Confirms correct implementation of passivity suppression

---

### 17.5 Energy Dynamics Validation

---

#### 17.5.1 Energy Conservation Structure
Verify that energy updates follow:

$$
e_{t+1} = e_t - c(a_t) + \kappa \cdot \Delta R_t^{cons}
$$

* movement reduces energy
* consumption increases energy

✔ Confirms correct internal-external coupling

---

#### 17.5.2 Boundary Conditions
Verify that:

* $e_t \in [0, E_{\max}]$
* energy is clipped or bounded appropriately

✔ Prevents invalid state values

---

#### 17.5.3 Termination Correctness
Verify that:

* $e_t = 0 \Rightarrow$ system stops

✔ Confirms proper death condition

---

### 17.6 Environment Interaction Checks

---

#### 17.6.1 Resource Consumption

Verify that:

* consumption reduces local resource
* consumed amount does not exceed $c_{\max}$

✔ Confirms local interaction correctness

---

#### 17.6.2 Resource Regeneration

Verify that:

* resources increase over time according to regeneration rule
* regeneration is independent of agent intention

✔ Confirms environment autonomy

---

### 17.7 Negative Capability Tests
These tests are critical and often overlooked.
They verify that the system does not exhibit unintended capabilities.

---

#### 17.7.1 No Path Planning
Test:

* place food outside perception range

Expected:

* no directed movement toward it

✔ Confirms absence of planning or spatial reasoning

---

#### 17.7.2 No Memory-Based Behavior
Test:

* repeatedly expose agent to food in same location

Expected:

* no improved return to that location over time

✔ Confirms memory is not used

---

#### 17.7.3 No Exploration Strategy
Test:

* large empty environment

Expected:

* movement remains undirected
* no systematic coverage pattern emerges

✔ Confirms absence of exploration drive

---

### 17.8 Reproducibility and Determinism

---

#### 17.8.1 Deterministic Mode
With fixed random seed:

* identical runs produce identical trajectories

✔ Confirms implementation correctness

---

#### 17.8.2 Statistical Stability
Across multiple stochastic runs:

* distributions of:

  * survival time
  * action frequencies
  * energy levels

remain stable

✔ Confirms robustness of behavior

---

### 17.9 Validation Summary
A valid implementation of System A must satisfy all of the following:

* correct execution order
* strict separation of system components
* purely reactive behavior
* absence of learning or planning
* correct energy-resource dynamics
* consistent stochastic policy behavior

---

### 17.10 Interpretation
Successful validation demonstrates that:

* complex, adaptive-looking behavior can emerge
* without invoking cognition, memory usage, or prediction

At the same time, validation clearly exposes the system’s limitations:

* inability to anticipate
* inability to learn
* inability to form internal models

This establishes System A as a controlled baseline for studying the minimal conditions under which adaptive behavior arises.

---
