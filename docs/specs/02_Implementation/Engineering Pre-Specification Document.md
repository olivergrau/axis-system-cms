# AXIS Project – System A (Baseline)

## **Engineering Pre-Specification Document (Draft)**

## Metadata
- Project: AXIS – Complex Mechanistic Systems Experiment
- Author: Oliver Grau
- Type: Engineering Document
- Status: Draft v1.0
- Scope: Implementation of a baseline agent with modular drive-based action modulation

---

## 1. Purpose of This Document
This document defines the **engineering-level open questions, constraints, and design decisions** required before implementing **System A (Baseline)**.

The goal is to:

- Ensure **full consistency** between theoretical specification and implementation
- Enable **semi-autonomous code generation** (e.g. via coding assistants)
- Establish a **minimal, testable, and extensible implementation foundation**
- Identify **critical ambiguities or underspecified aspects** in the current model

This document does **not** define final solutions yet.  
It enumerates the **decision space** that must be resolved prior to implementation.

---

## 2. Scope
This document applies strictly to:

> **System A (Baseline)**

Constraints:

- No world model
- No planning
- No learning
- No exploration drive
- Single drive: **Hunger**

Future extensions (e.g. search, world model, multi-drive) are **explicitly out of scope**.

---

## 3. Guiding Engineering Principles
The implementation must satisfy:

### 3.1 Deterministic Reproducibility (where required)

- Runs must be reproducible under controlled conditions
- Randomness must be controllable via explicit seeds

### 3.2 Full Observability of Internal State

- All relevant internal variables must be inspectable
- No hidden or implicit state

### 3.3 Strict Separation of Concerns

- World, Agent, Sensor, Policy, and Transition must be separable components

### 3.4 Parameter Transparency

- All parameters must be externally configurable
- No hardcoded behavioral constants

### 3.5 Minimality

- No functionality beyond the baseline specification
- No implicit intelligence

---

## 4. System Decomposition (Engineering View)
The theoretical model must be mapped into the following components:

### 4.1 World Module

- Grid representation
- Resource dynamics
- Obstacle handling

### 4.2 Sensor Module

- Local observation extraction
- Normalization logic

### 4.3 Agent Module

- State representation
- Energy tracking
- Drive computation

### 4.4 Behavior / Policy Module

- Action scoring
- Hunger modulation
- Softmax transformation

### 4.5 State Transition Module

- Movement logic
- Energy updates
- Resource consumption
- Memory update

### 4.6 Memory Module

- Storage structure
- Update rules
- Capacity constraints

### 4.7 Execution Engine

- Simulation loop
- Step-wise progression
- Termination conditions

### 4.8 Experiment / Run Controller

- Parameter injection
- Run execution
- Logging and result collection

### 4.9 Visualization (Optional but Supported)

- Grid rendering
- Agent trajectory
- Energy over time

---

## 5. Core Engineering Questions (To Be Resolved)

---

### 5.1 Determinism vs. Stochasticity

#### Objective
Define how actions are selected from the policy distribution, ensuring:

- Reproducibility of simulation runs
- Bias-free action selection
- Support for both analysis and behavioral simulation

---

#### Action Selection Modes
The system shall support two action selection modes:

##### 1. Stochastic Mode (`sample`)

- Actions are sampled from the Softmax probability distribution:
    
    $$  
    P(a \mid x_t, u_t)  
    $$
    
- This mode represents the **default behavioral execution** of the agent
    
- It enables:
    
    - variability in trajectories
    - non-deterministic behavior under equal or weak signals

---

##### 2. Deterministic Mode (`argmax`)

- The action with the highest probability is selected:
    
    $$
    a_t = \arg\max_a P(a \mid x_t, u_t)  
    $$
    
- This mode is primarily intended for:
    
    - debugging
    - validation
    - verification against worked examples


---

#### Tie-Breaking Strategy (Deterministic Mode)
In cases where multiple actions have equal maximum probability:

- The system shall perform a **random selection among all maximal actions**
- This randomness:
    
    - is required to avoid structural bias
    - is controlled via the global random seed (see below)


Implication:

- The deterministic mode is not strictly deterministic in the presence of ties
- However, it remains **reproducible under fixed seed conditions**

---

#### Unified Policy Pipeline
The action selection process shall follow a unified pipeline:

1. Compute action scores
2. Apply hunger modulation
3. Compute Softmax probabilities
4. Apply selection mode (`sample` or `argmax`)

There shall be **no alternative policy pathways** depending on selection mode.

---

#### Randomness and Reproducibility

- A **global random seed** shall control all stochastic elements of the system
    
- This includes:
    
    - stochastic sampling (`sample` mode)
    - tie-breaking in deterministic mode
        
- The system must ensure:
    
    - identical seeds → identical trajectories
    - no hidden or uncontrolled sources of randomness


---

#### Configuration
The action selection behavior shall be configurable via:

- `selection_mode ∈ {sample, argmax}`
- `random_seed ∈ ℕ`

---

#### Design Rationale

- **Stochastic mode** reflects the intended behavior of the baseline agent
- **Deterministic mode** enables controlled analysis and debugging
- Random tie-breaking avoids introducing implicit directional biases
- A unified pipeline preserves conceptual clarity and implementation simplicity

---

### 5.2 Parameter Management

#### Objective
Define a consistent and extensible mechanism for:

- specifying all system parameters
- ensuring reproducibility of runs
- enabling controlled experimentation (e.g. parameter sweeps)

---

#### General Principle
All parameters of the system shall be:

- externally configurable
- explicitly defined
- fully decoupled from the implementation logic

No behavioral or system-relevant parameter shall be hardcoded.

---

#### Configuration Format
The system shall use a **JSON-based configuration file** as the primary parameter source.

##### Rationale

- simple and widely supported
- human-readable
- compatible with automated tooling and code generation
- no additional dependencies required

---

#### Configuration Structure
The configuration must be **hierarchically structured** and reflect the system decomposition.

At minimum, the following sections shall be present:

- `world`
- `sensor`
- `agent`
- `behavior`
- `policy`
- `transition`
- `memory`
- `execution`
- `experiment`

Each section shall contain only parameters relevant to its respective module.

---

#### Parameter Categories
Parameters fall into the following categories:

##### 1. Structural Parameters
Define system structure:

- grid size
- memory capacity
- neighborhood definition

##### 2. Behavioral Parameters
Define agent dynamics:

- hunger scaling
- action weights
- temperature (β)
- stay suppression (λ)

##### 3. Physical Parameters
Define environment dynamics:

- resource regeneration rate
- consumption scaling (κ)
- action costs


##### 4. Execution Parameters
Define runtime behavior:

- selection mode (`sample` / `argmax`)
- random seed
- maximum episode length

##### 5. Experiment Parameters
Define run-level control:

- number of runs
- parameter overrides (optional)

---

#### Parameter Injection

- The configuration file shall be loaded **once at initialization**
- All modules shall receive only the subset of parameters relevant to them
- No module shall access global configuration state directly

---

#### Reproducibility Requirements
A complete configuration must uniquely define a run.

This includes:

- all system parameters
- random seed
- selection mode

Two runs with identical configurations must produce identical results.

---

#### Parameter Overrides (for Experiments)
The system shall support parameter overrides at runtime, without modifying the base configuration file.

This enables:

- parameter sweeps
- controlled experiments

Overrides may be applied:

- programmatically
- via additional configuration layers (e.g. secondary JSON)

---

#### Parameter Validation
The system shall validate all parameters before execution.

Validation must include:

- type checks (e.g. float, integer)
- value ranges (e.g. non-negative energy)
- structural completeness (all required fields present)

Invalid configurations must result in explicit errors.

---

#### Serialization and Logging
For every run, the full effective configuration must be:

- stored
- logged
- reproducible

This includes all overrides.

---

#### Design Rationale

- JSON ensures simplicity and compatibility with tooling
- strict separation of configuration and logic improves maintainability
- hierarchical structure mirrors system architecture
- explicit parameter handling enables systematic experimentation

---

#### Open Considerations

- exact schema definition (optional strict schema vs. flexible parsing)
- format for parameter sweep specification
- handling of default values

---

### 5.3 Action Selection Pipeline

#### Objective
Define a precise and implementation-ready action selection pipeline that:

- remains fully consistent with the baseline formal model
- is modular and inspectable
- supports debugging and validation
- allows future extension without structural redesign

The action selection mechanism shall be implemented as a dedicated **Policy object**, while returning a full **Decision Trace** for each decision step.

---

#### General Design Principle
The action selection process shall be encapsulated in a dedicated policy component.
This component is responsible for transforming:

- internal state
- current observation
- passive memory state
- policy configuration

into:

- action scores
- action probabilities
- final selected action
- full decision trace

The policy implementation shall remain internally modular, even if externally exposed through a single decision method.

---

#### Policy Object
The system shall provide a dedicated **Policy class** responsible for action selection.

Its responsibilities include:

- drive evaluation relevant for policy execution
- computation of action scores
- admissibility masking for locally invalid movement actions
- Softmax probability computation
- final action selection according to the configured selection mode
- generation of a structured decision result

The policy object shall not modify world state, internal agent state, or memory.  
It is a pure decision component.

---

#### Drive Modularity and Integration

##### Objective
Ensure that the policy is not tightly coupled to any specific drive (e.g. hunger), but instead supports a modular and extensible drive architecture.

---

##### General Principle
The policy shall not contain hardcoded logic for specific drives.

Instead, all drives shall be implemented as **independent, pluggable components** that:

- receive relevant inputs (e.g. internal state, observation)
- compute drive-specific activations and/or action modulations
- expose their outputs through a standardized interface

The policy is responsible only for:

- orchestrating these drive modules
- aggregating their contributions into action scores

---

##### Drive Module Interface
Each drive module shall define a consistent interface.

At minimum, a drive module must:

- accept:
    
    - internal state $x_t$
    - observation $u_t$
    - optional memory $m_t$

- produce:
    
    - a drive activation signal (e.g. scalar)
    - an action modulation vector over all actions

This allows each drive to contribute independently to the final action scores.

---

##### Drive Aggregation Mechanism
The policy shall support a configurable mechanism for combining multiple drive contributions.

For the baseline system:

- only a single drive (**Hunger**) is active
- aggregation reduces to a direct mapping of that drive’s output

However, the architecture must already support:

- multiple concurrent drives
- combination of their action influences

The exact aggregation rule (e.g. multiplicative or additive combination) shall be defined explicitly and remain configurable for future extensions.

---

##### Baseline Instantiation

In **System A (Baseline)**:

- exactly one drive module is instantiated: **Hunger Drive**
- the policy integrates this drive through the generic drive interface
- no special-case logic for hunger shall exist inside the policy

Thus, even in the baseline:

- hunger is treated as a **plugin module**
- not as a hardcoded internal mechanism

---

##### Pipeline Integration
Within the action selection pipeline:

- the **Drive Evaluation stage** shall invoke all registered drive modules
- each drive produces its modulation signal
- the policy aggregates these signals into the final action score vector

This replaces any direct, hardcoded computation such as:

$$
d_H(t) = 1 - \frac{e_t}{E_{\max}}  
$$

inside the policy.

Instead, this computation belongs entirely to the **Hunger Drive module**.

---

##### Configuration
The set of active drives shall be configurable.

At minimum, the configuration must define:

- which drive modules are active
- their parameters

This ensures that future systems can:

- add new drives
- remove drives
- experiment with combinations

without modifying policy logic.

---

##### Decision Trace Integration
The DecisionTrace must include:

- individual drive activations
- per-drive action contributions (if applicable)
- aggregated action scores

This ensures full transparency of how each drive influenced the decision.

---

##### Design Rationale
This design is chosen to:

- avoid tight coupling between policy and specific drives
- enable incremental system evolution (e.g. adding search or curiosity)
- preserve clarity of responsibility between modules
- allow controlled experimentation with different drive configurations

---

#### Decision Trace Requirement
Each policy decision shall return a structured **DecisionTrace** object.
This object must support detailed inspection and debugging.

At minimum, it shall contain:

- current observation
- relevant internal decision inputs
- drive activation values
- raw action scores
- admissibility information
- effective action scores after masking
- action probabilities
- selection mode
- selected action
- tie-breaking information, if applicable

This trace is required for:

- debugging
- worked-example verification
- test assertions
- run analysis
- optional visualization support

---

#### Pipeline Stages
The policy decision pipeline shall follow the stages below.

---

##### Stage 1: Input Reception
The policy receives:

- internal agent state $x_t$
- current observation $u_t$
- episodic memory $m_t$

In the baseline system:

- memory is passed through the interface
- but it is not behaviorally consulted

This preserves interface stability for future extensions.

---

##### Stage 2: Drive Evaluation
The policy computes the currently relevant drive activations.

In the baseline system, this consists only of the hunger drive:

$$  
d_H(t) = 1 - \frac{e_t}{E_{\max}}  
$$

The computed drive activation shall be explicitly stored in the decision trace.

> Please make sure that drives are implemented and designed with modularity in mind.

---

##### Stage 3: Raw Action Score Computation
The policy computes a full raw score vector over the complete action set:

$$  
\mathcal{A} = \{ \text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}, \text{CONSUME}, \text{STAY} \}  
$$

The raw score computation follows the baseline model:

$$
\psi(a) = d_H(t)\cdot \phi_H(a,u_t)  
$$

with the special case:

$$
\psi(\text{STAY}) = -\lambda_{stay}\cdot d_H(t)  
$$

A raw score shall be computed for **every action**, including actions that may later be masked.

This ensures maximal transparency and allows full inspection of the decision structure.

---

##### Stage 4: Local Admissibility Masking
After raw scores are computed, the policy shall apply a local admissibility check for movement actions.

##### Movement Actions
If the sensor indicates that a movement direction is locally blocked, that movement action shall be treated as **inadmissible**.

Examples include:

- obstacle cell
- out-of-bounds cell represented as non-traversable

Thus, movement admissibility is determined directly from the local traversability signals:

$$
b_{dir} \in {0,1}  
$$

If:

$$
b_{dir} = 0  
$$

then the corresponding movement action shall not be selectable.

---

###### Consume Action
The action `CONSUME` shall **not** be masked merely because the current cell contains no resource.

Thus, `CONSUME` remains an admissible action even when:

$$  
r_c = 0  
$$

This is consistent with the baseline design, where ineffective consumption attempts remain possible.

---

###### Stay Action
The action `STAY` always remains admissible.

---

###### Masking Representation
The system shall preserve the full raw score vector, but also produce an **effective score vector** in which inadmissible movement actions are encoded as non-selectable.

This masking must guarantee that inadmissible actions receive zero selection probability.

The implementation may use a conventional numerical representation for this purpose, such as negative infinity or an equivalent sufficiently suppressive value, as long as the resulting probability is exactly zero in practice and the behavior remains numerically stable.

The admissibility status of each action must be recorded in the decision trace.

---

##### Stage 5: Probability Computation
The policy shall compute action probabilities from the effective score vector using the Softmax function.

To ensure numerical stability, the implementation shall use the standard stabilized Softmax formulation:

$$ 
P(a \mid x_t,u_t)=  
\frac{\exp\bigl(\beta(\psi(a)-\psi_{\max})\bigr)}  
{\sum_{a'} \exp\bigl(\beta(\psi(a')-\psi_{\max})\bigr)}  
$$

where:

$$  
\psi_{\max} = \max_{a'} \psi(a')  
$$

computed over the effective score vector of admissible actions.
This stabilized form shall be used as the standard implementation rule.

The resulting probabilities must satisfy:

- all admissible actions receive valid probabilities
- all inadmissible actions receive probability zero
- the full distribution sums to 1

---

##### Stage 6: Action Selection
The final action is selected from the probability distribution according to the configured selection mode.

Supported modes are:

- `sample`
- `argmax`

These modes are defined in Section 5.1.

---

###### Argmax Mode
In `argmax` mode, the action with the highest probability is selected.

If multiple actions share the same maximal probability, the policy shall perform a random tie-break among those maximal actions.

This tie-break must be controlled by the global random seed.

---

###### Sample Mode
In `sample` mode, the action is sampled from the probability distribution.

Sampling must also be controlled by the global random seed.

---

#### Internal Modularity
Although exposed as a single Policy object, the implementation shall separate the following internal concerns:

- drive computation
- raw score computation
- action admissibility masking
- probability computation
- action selection
- trace construction

This separation may be implemented through internal helper methods or equivalent object-oriented decomposition.

The goal is to preserve:

- testability
- readability
- future extensibility

---

#### DecisionTrace as a First-Class Output
The policy shall not return only a bare action.

Instead, the decision output shall always include the full structured decision result.

This enables:

- exact traceability of why an action was selected
- direct comparison with worked examples
- easier integration with run logging and visualization

If a caller only needs the selected action, it may read it from the returned decision object.

---

#### Design Rationale
This pipeline design is chosen because it provides:

- a clean object-oriented implementation unit
- explicit separation between scoring, masking, probability calculation, and selection
- direct support for debugging and inspection
- consistency with the baseline system constraints
- compatibility with future policy extensions

The masking rule for blocked movement actions is justified because traversability is already part of the local observation and therefore constitutes information the baseline system is explicitly allowed to use.

The decision not to mask `CONSUME` on empty cells preserves the minimal mechanistic character of the baseline system and allows ineffective but locally admissible actions to remain possible.

---

#### Implementation Consequence
Any implementation of the baseline policy must therefore provide:

- a dedicated policy object
- a structured decision result object
- a stable Softmax implementation
- admissibility masking for blocked movement actions
- seeded tie-breaking and stochastic sampling
- full traceability of the decision process

---

### 5.4 State Representation

#### Objective
Define a precise and implementation-consistent representation of system state, ensuring:

- strict adherence to the baseline formal model
- clear separation between agent-internal and environment state
- explicit integration of memory as an agent-side subsystem
- full transparency and inspectability
- compatibility with future extensions

---

#### General Principle
The system state shall be decomposed into distinct components:

- **Agent-maintained state**
- **World state**
- **Observation (derived, not persistent)**

These components must remain strictly separated in terms of responsibility and access.

The agent shall not have direct access to world state variables beyond what is provided through the observation function.

---

#### Agent-Maintained State $(x_t, m_t)$
From an implementation perspective, the agent maintains an internal state composed of:

- **Core internal state $x_t$**
- **Memory subsystem $m_t$**

These together form the **agent-maintained state**, while remaining conceptually distinct.

---

#### Core Agent State $(x_t)$
The internal agent state $x_t$ shall contain only variables that are:

- internally maintained by the agent
- directly relevant to internal dynamics
- explicitly defined in the baseline model

##### Baseline Definition
In System A (Baseline), the core agent state consists of:

- **Energy**  
    $$
    e_t \in [0, E_{\max}]  
    $$

No additional internal variables are present in the baseline system.

---

#### Energy Representation
Energy shall be represented as a **continuous scalar quantity**.

##### Properties

- type: real-valued scalar (implementation: floating-point)
    
- bounded:  
    $$
    0 \leq e_t \leq E_{\max}  
    $$
    
- updated through:
    
    - action-dependent cost
    - resource consumption


##### Numerical Handling

- energy values must be **clipped** to the valid interval after each update
- terminal condition (agent death) shall be evaluated using:
    
    $$  
    e_t \leq 0  
    $$
    
- implementations must avoid reliance on exact floating-point equality

---

#### Memory Subsystem $(m_t)$
The agent shall include an explicit **memory subsystem** as part of its maintained state.

##### Role in Baseline System
In System A (Baseline), memory is:

- implemented and persistently maintained
- updated at every timestep
- fully inspectable

but:

- not consulted by the policy
- not used by any drive module
- not used for prediction, planning, or evaluation

Memory is therefore a **present but behaviorally inactive subsystem**.

---

##### Stored Content
The memory shall store **observation-derived perceptual entries only**.

In the baseline system, this includes:

- past observations $u_t$
- or equivalent structured observation records

The memory must not store:

- absolute position
- full world state
- hidden environment parameters
- inferred spatial maps
- predicted future states

---

##### Structure and Capacity
The memory shall be implemented as a bounded structure.

Typical implementation options include:

- fixed-size buffer
- ring buffer

The capacity must be configurable via system parameters.

---

##### Update Rule
Memory shall be updated after each timestep using the newly computed observation:

- the stored entry corresponds to the **post-transition observation**

This ensures temporal consistency with the system dynamics.

---

##### Behavioral Constraint
The following constraint is mandatory:

> Memory must not influence action selection or drive computation in the baseline system.

This constraint must be explicitly preserved in the implementation.

---

#### Explicit Exclusion: Position from Agent State
The agent’s spatial position shall **not** be part of the agent-maintained state.

##### Rationale

- the baseline agent has no self-localization capability
- position is not part of $x_t$
- spatial awareness must arise solely from observation

Thus:

- the agent does not have access to absolute position
- no implicit coordinate system is available internally
- no hidden state may encode position

---

#### World State $(s_t^{world})$
The world state contains all environment-related variables, including:

- spatial grid structure
- resource distribution
- obstacle layout
- agent position

##### Agent Position
The agent’s position:

- is maintained exclusively within the world state
- is updated by the state transition function
- is not directly accessible to the agent

---

#### Observation $(u_t)$
The observation is a **derived quantity**, computed from:

- world state
- agent position

It is not stored as part of persistent system state.

##### Properties

- local (neighborhood-based)
- partial (no global information)
- stateless (recomputed each timestep)

The observation function is the only interface through which the agent perceives the environment.

---

#### Implementation Structure
The system shall define separate data structures for:

- agent core state $(x_t)$
- memory subsystem $(m_t)$
- world state $(s_t^{world})$
- observation $(u_t)$

These structures must not be implicitly merged or conflated.

---

#### Design Rationale
This representation enforces a strict separation between:

- internal dynamics (energy)
- stored perceptual history (memory)
- external environment (world state)
- perception (observation)

At the same time, it allows memory to exist as a real subsystem from the beginning, enabling:

- incremental system evolution
- architectural stability
- consistent extension toward more complex agents

---

#### Implementation Consequence
Any implementation must ensure:

- the agent state contains only energy and memory
- the policy has no access to agent position
- memory is updated but not used for decisions
- observation remains the sole perception channel
- all components are cleanly separated and inspectable

---

### 5.5 World Representation

#### Objective
Define a clear, explicit, and fully inspectable representation of the environment in which the agent operates, ensuring:

- strict separation from agent-internal state
- high transparency and debuggability
- direct correspondence to the conceptual model
- readiness for controlled future extensions

Performance optimization is explicitly **not** a priority in this baseline specification.

---

#### General Structure
The environment shall be represented as a **finite two-dimensional grid world**, composed of discrete spatial cells.

The world state is defined as:

$$ 
s_t^{world} = (\mathcal{G}, p_t)  
$$

where:

- $\mathcal{G}$ is the grid structure
- $p_t$ is the agent’s position within the grid

---

#### Grid Representation $(\mathcal{G})$
The grid shall be implemented as a **two-dimensional collection of cell objects**, indexed by integer coordinates.

##### Properties

- finite dimensions:  
    $$  
    width, height \in \mathbb{N}  
    $$
    
- coordinate system:  
    $$ 
    (x, y), \quad x \in [0, width-1], \quad y \in [0, height-1]  
    $$
    
- each coordinate maps to exactly one cell:  
    $$ 
    \mathcal{G}[x, y] \rightarrow \text{Cell}  
    $$
    

---

#### Cell Representation
Each grid location shall be represented by an explicit **Cell object**.

##### Cell State Variables
Each cell contains:

- **Resource Level**  
    $$  
    r_t \in [0, r_{\max}]  
    $$
    
- **Maximum Resource Capacity**  
    $$ 
    r_{\max} > 0  
    $$
    
- **Regeneration Rate**  
    $$ 
    \rho \geq 0  
    $$
    
- **Obstacle Flag**  
    $$ 
    o \in {0, 1}  
    $$

---

#### Cell Semantics

- If $o = 1$, the cell is **non-traversable**
- If $o = 0$, the cell is **traversable**
- Resource values apply only to traversable cells
- Resource dynamics (consumption and regeneration) are defined externally via the transition function

---

#### Agent Position $(p_t)$
The agent’s position is part of the world state:

$$
p_t = (x_t, y_t)  
$$

##### Properties

- discrete integer coordinates
- must always satisfy grid bounds
- must refer to a traversable cell

---

#### Representation Constraint
The agent’s position:

- is stored exclusively in the world state
- is not part of the agent state $x_t$
- is not directly accessible to the agent

All spatial awareness must arise through observation.

---

#### Position Representation
Positions shall be represented using a dedicated **value object**:

$$  
p = (x, y)  
$$

##### Requirements

- immutable or treated as immutable
- no embedded world logic
- used consistently across:
    
    - world state
    - observation computation
    - transition logic

---

#### Access Model
The world representation shall provide explicit access functions, including:

- retrieval of a cell at a given position
- boundary checks
- traversal validation
- neighbor computation based on action

These functions must be:

- deterministic
- side-effect free (for read operations)

---

#### Separation of Concerns
The world representation must not contain:

- agent logic
- policy logic
- drive computations
- memory interaction

It is strictly responsible for:

- maintaining environmental state
- exposing structured access to that state

---

#### Debugging and Transparency Requirement
The world representation must support:

- full inspection of all cells
    
- direct visualization or logging of:
    
    - resource distributions
    - obstacle layout
    - agent position

The structure must be:

- human-readable
- easily serializable
- stable across timesteps

---

#### Explicit Design Decision
The world is represented using **explicit cell objects within a structured grid**, rather than compressed or vectorized representations.

##### Rationale

- improves debuggability
- preserves semantic clarity
- reduces indexing errors
- aligns directly with conceptual model
- supports incremental system extension

---

#### Exclusion of Optimized Representations
The following are intentionally excluded in the baseline system:

- flattened arrays
- multi-channel tensor representations
- implicit encoding of cell properties
- GPU-oriented layouts

Such representations may be introduced in future system variants, but are not compatible with the transparency goals of System A (Baseline).

---

#### Design Rationale
This representation enforces a clear structural distinction between:

- **environmental state (world)**
- **internal state (agent)**
- **perception (observation)**

It ensures that:

- spatial information remains external
- the agent remains epistemically limited
- all environment dynamics remain traceable and controllable

---

#### Implementation Consequence
Any implementation must ensure:

- the grid is explicitly represented as a collection of cells
- each cell exposes its full state
- agent position is stored only in the world
- no hidden coupling exists between world and agent internals
- the entire world state can be inspected at any timestep

---

### 5.6 Transition Function Implementation

#### Objective
Define a concrete, modular, and fully traceable implementation of the state transition function:

$$
(x_{t+1}, m_{t+1}, s_{t+1}^{world}) = F(x_t, m_t, s_t^{world}, a_t)  
$$

ensuring:

- strict adherence to the baseline model
- deterministic and phase-structured execution
- full observability via transition tracing
- strong modularity and controlled extensibility
- absence of unintended side effects

---

#### Core Design Principle
The transition function shall be implemented as a **centrally orchestrated process**, executed by a dedicated component:

> **Transition Engine**

This engine is responsible for:

- enforcing execution order
- coordinating all submodules
- producing a complete and consistent next state
- generating a full transition trace

No individual subsystem may independently perform uncontrolled state transitions.

---

#### Result-Based Transition
The transition function shall follow a **result-based design**:

- input state remains unchanged
- output state is constructed explicitly

$$
(x_{t+1}, m_{t+1}, s_{t+1}^{world}) = F(...)  
$$

##### Constraint

- no implicit in-place mutation of input state
- all state changes must be explicitly represented in the output

This ensures:

- reproducibility
- testability
- temporal consistency
- elimination of hidden side effects

---

#### Execution Phases
The transition shall be executed in strictly defined phases:

---

##### Phase 1 – World Regeneration

- apply environmental dynamics (e.g. resource regeneration)
- operates only on world state

$$  
s_t^{world} \rightarrow s_t^{world,regen}  
$$

---

##### Phase 2 – Action Application

- apply action $a_t$ to the world
    
- includes:
    
    - movement
    - resource consumption (if applicable)

$$
s_t^{world,regen} \rightarrow s_t^{world,post}  
$$

##### Constraint

- invalid actions must result in a **fail-hard error**
- no fallback or silent correction is allowed

---

##### Phase 3 – Observation Computation

- compute new observation based on updated world state

$$  
u_{t+1} = O(s_t^{world,post})  
$$

---

##### Phase 4 – Agent State Update

- update internal agent state (baseline: energy)

$$  
x_t \rightarrow x_{t+1}  
$$

based on:

- action cost
- resource consumption outcome

---

##### Phase 5 – Memory Update

- update memory using the new observation

$$  
m_t \rightarrow m_{t+1}  
$$

##### Constraint

- memory remains behaviorally inactive
- no influence on decision-making

---

##### Phase 6 – Termination Evaluation

- evaluate terminal conditions (e.g. energy depletion)

$$  
\text{done} = (e_{t+1} \leq 0)  
$$

---

#### Module Decomposition
The Transition Engine shall delegate phase logic to dedicated modules:

---

##### WorldTransitionModule
Responsible for:

- regeneration logic
- action effects on the world

---

##### ObservationBuilder
Responsible for:

- computing (u_t) and (u_{t+1})
- strictly read-only access to world state

---

##### AgentTransitionModule
Responsible for:

- updating internal agent variables
- handling energy dynamics

---

##### MemoryModule
Responsible for:

- maintaining memory state
- updating stored observations

---

##### TerminationCriterion
Responsible for:

- evaluating terminal conditions

---

#### Plugin Architecture (Minimal System)
The system shall support controlled extensibility via interchangeable modules:

- `WorldTransitionModule`
- `AgentTransitionModule`
- `TerminationCriterion`

These modules must:

- conform to defined interfaces
- operate deterministically
- avoid hidden side effects

---

#### Hook System (Prepared Extension Point)
The Transition Engine shall provide optional hook points at phase boundaries:

- before / after regeneration
- before / after action application
- before / after agent update
- before / after memory update
- before termination evaluation

##### Purpose

- debugging
- logging
- visualization
- future extensibility

##### Constraint

- hooks must be side-effect free in baseline configuration

---

#### Transition Trace
Each transition must produce a complete **Transition Trace** object.

##### Contents
At minimum:

- action $a_t$
- observation $u_t$ (pre-action)
- observation $u_{t+1}$ (post-action)
- world state snapshots:
    
    - before transition
    - after regeneration
    - after action

- agent state:
    
    - before
    - after

- memory state:
    
    - before
    - after

- resource consumption details
- termination flag

---

#### Determinism Requirement
The transition function must be:

- deterministic given identical inputs
- free from hidden randomness
- reproducible across runs

---

#### Error Handling Policy
The system shall follow a **fail-hard strategy**:

- invalid actions must raise an explicit error
- no silent corrections
- no fallback behavior

##### Rationale

- prevents hidden inconsistencies
- ensures correctness of upstream components (policy)

---

#### Separation of Responsibilities
The following constraints must hold:

- world logic remains in world modules
- agent logic remains in agent modules
- memory remains isolated
- observation is purely derived
- transition orchestration is centralized

No module may violate these boundaries.

---

#### Design Rationale
This architecture enforces:

- explicit temporal causality
- full transparency of system dynamics
- strict separation between subsystems
- controlled extensibility without loss of clarity

It balances:

- engineering rigor
- conceptual purity
- practical debuggability

---

#### Implementation Consequence
Any implementation must ensure:

- a central Transition Engine controls execution
- all phases are explicitly implemented and ordered
- no implicit state mutation occurs
- full transition traces are generated
- module boundaries are strictly enforced
- plugin interfaces are respected
- hook points are available (even if unused)

---

### 5.7 Memory Implementation

#### Objective
Define a modular, bounded, and fully inspectable implementation of the memory subsystem $m_t$, ensuring:

- strict adherence to the baseline model
- explicit separation from agent decision-making
- deterministic and side-effect-free updates
- controlled extensibility via a pluggable module design
- strong support for debugging and inspection

---

#### Role of Memory in the Baseline System
In System A (Baseline), memory is:

- **implemented as a real subsystem**
- **updated at every timestep**
- **persistently maintained across transitions**

but:

- **not used for action selection**
- **not used by any drive or evaluation mechanism**
- **not used for prediction or planning**

Memory is therefore:

> a structurally present, but behaviorally inactive component

---

#### Memory Representation
The memory state $m_t$ shall be represented as a **bounded sequence of perceptual records**:

$$  
m_t = [e_1, e_2, ..., e_k], \quad k \leq C  
$$

where:

- $e_i$ is a memory entry
- $C$ is the configured memory capacity

---

#### Memory Entry Structure
Each memory entry shall be a **structured observation record**, derived exclusively from perception.

##### Minimum Required Fields

- **timestep index**  
    $$  
    t \in \mathbb{N}  
    $$
- **observation**  
    $$ 
    u_t  
    $$

---

##### Constraints
Memory entries must not contain:

- agent position
- world state variables
- hidden environment parameters
- inferred or predicted information
- any data not directly derived from observation

---

#### Memory Capacity
Memory shall have a **fixed, configurable capacity**:

$$  
C \in \mathbb{N}, \quad C > 0  
$$

##### Capacity Metric

- measured in **number of entries**
- independent of observation size

---

#### Overflow Handling
When memory reaches capacity:

- the **oldest entry is removed**
- the new entry is appended

This results in a **FIFO (First-In-First-Out)** behavior.

---

#### Initialization
Memory shall be initialized as an **empty sequence**:

$$  
m_0 = []  
$$

##### Constraint

- no implicit insertion of initial observation
- first entry is created only after the first transition step

---

#### Update Rule
Memory shall be updated in **Phase 5 of the transition** using the newly computed observation:

$$  
m_{t+1} = \text{append}(m_t, (t+1, u_{t+1}))  
$$

##### Properties

- strictly chronological
- no reordering
- no modification of past entries

---

#### Result-Based Update
Memory updates must follow a **result-based design**:

$$ 
m_{t+1} = M(m_t, u_{t+1})  
$$

##### Constraint

- no in-place mutation of $m_t$
- a new memory instance must be returned

This ensures:

- consistency with transition design
- testability
- absence of hidden side effects

---

#### Memory Module Design
Memory shall be implemented as a dedicated, pluggable component:

> **MemoryModule**

---

##### Responsibilities

- maintain memory state
- handle insertion logic
- enforce capacity constraints
- provide read access for inspection

---

##### Required Interface (Conceptual)
The module shall provide at least:

- `update(memory, observation, timestep) -> new_memory`
- `get_entries(memory) -> list`
- `latest(memory) -> entry or null`
- `size(memory) -> int`
- `clear() -> empty_memory`

---

##### Constraints

- must be deterministic
- must not access world state
- must not influence agent behavior in baseline
- must operate only on provided inputs

---

#### Integration with Transition System
Memory updates occur strictly in:

> **Phase 5 – Memory Update**

and depend only on:

- previous memory state $m_t$
- new observation $u_{t+1}$
- timestep index

Memory must not:

- access the action directly
- access world state directly
- depend on agent internal state beyond observation

---

#### Transition Trace Integration
Memory changes must be reflected in the **Transition Trace**.

##### Required Information

- memory summary before update
- memory summary after update

##### Summary Definition
At minimum:

- number of stored entries
- timestep range (oldest → newest)

---

##### Optional Detail Access
Full memory content:

- may be included optionally
- must be accessible for debugging and inspection

---

#### Determinism Requirement
The memory update process must be:

- fully deterministic
- reproducible given identical inputs

---

#### Design Rationale
This design ensures that memory:

- exists as a real system component
- evolves consistently with experience
- remains fully observable and testable
- does not interfere with baseline behavior

It provides a foundation for future extensions such as:

- learning mechanisms
- state estimation
- planning systems

without requiring structural changes.

---

#### Implementation Consequence
Any implementation must ensure:

- memory is explicitly represented as a bounded sequence
- entries are structured and observation-derived only
- updates are result-based
- capacity constraints are enforced deterministically
- no behavioral dependency exists in baseline
- memory is fully inspectable at all times

---

### 5.8 Logging and Observability

#### Objective
Define a structured and configurable observability layer for the baseline system, ensuring:

- full traceability of runs, episodes, and steps
- support for debugging, validation, and later analysis
- compatibility with parameter sweeps and batch execution
- strict separation between simulation logic and logging concerns
- optional persistence to file-based outputs

Logging and observability are considered essential engineering capabilities of the baseline implementation.

---

#### General Principle
The system shall use an **existing logging framework** for technical logging, message routing, log levels, and output targets.

However, the simulation itself shall expose its internal execution state through dedicated **structured observability records**.

Thus, the observability design consists of two layers:

##### 1. Logging Framework Layer
Responsible for:

- log levels
- console/file output
- formatting
- technical runtime messages

##### 2. Structured Observability Layer
Responsible for:

- simulation records
- decision traces
- transition traces
- run/episode/step summaries

This separation must be preserved.

---

#### Observability Levels
The system shall support observability on three distinct levels:

---

##### 1. Run Level
Covers the full execution context of a run.

At minimum, run-level observability must include:

- run identifier
- configuration reference or effective configuration snapshot
- random seed
- execution mode
- start timestamp
- end timestamp
- total number of episodes
- run-level result summary

---

##### 2. Episode Level
Episode-level observability is mandatory.

Although an episode summary may be constructed from step records, the system shall explicitly support episode-level aggregation.

At minimum, episode-level observability must include:

- episode identifier
- run identifier
- episode start/end markers
- number of steps
- terminal condition
- final energy
- aggregate action statistics
- aggregate resource statistics (if available)

---

##### 3. Step Level
Step-level observability is mandatory.

At minimum, step-level observability must include:

- timestep index
- position before transition
- position after transition
- observation before transition
- observation after transition
- selected action
- decision result or decision summary
- transition trace or transition summary
- energy before / after
- memory summary before / after
- termination flag

---

#### Structured Logging Requirement
Simulation observability shall be based on **structured records**, not only textual log messages.
The system shall define dedicated structured objects for:

- run records
- episode records
- step records
- decision traces
- transition traces

These structures must be suitable for:

- in-memory inspection
- serialization
- test assertions
- post-run analysis

---

#### Logging Modes and Verbosity
Logging and observability shall be configurable.
The system shall support at least:

- logging enabled / disabled
- configurable observability depth
- standard logging levels provided by the chosen framework

---

##### Observability Depth
The observability layer shall support configurable detail levels, for example:

- `none`
- `summary`
- `full`

This is necessary because:

- debug runs require high visibility
- parameter sweeps require more compact logging

---

#### Optional Logging Disablement
Structured logging must be **optionally disableable**.

This is required for:

- performance-conscious batch runs
- parameter sweeps
- reduced storage usage

Even when structured observability is reduced or disabled, technical runtime logging through the logging framework may still remain active depending on configuration.

---

#### **Persistence**
Observability data shall be maintained primarily in structured in-memory form during execution.
Additionally, the system shall support optional persistence to file.
Persistence must be configurable and not mandatory for every run.

---

#### Preferred Output Formats
The preferred serialization formats are:

- **JSON** for run-level and episode-level records
- **JSONL** for step-level records and trace-oriented outputs

##### Rationale

- simple and widely supported
- compatible with downstream analysis tools
- appropriate for incremental record writing
- easy to inspect and archive

---

#### World State Logging Policy
The system shall not require full world snapshots at every step by default.

Instead, the default observability mode shall record:

- relevant world changes
- agent position
- resource interaction outcomes
- other transition-relevant state summaries

Full world snapshots may be supported optionally for deep debugging or visualization, but they are not required as the default step-level logging behavior.

---

#### Position Logging
Although the agent does not internally know its absolute position, the observability layer shall log agent position at step level.

This is required for:

- debugging
- trace reconstruction
- trajectory inspection
- visualization support

This does not violate the baseline constraints, because observability is an external engineering facility, not an agent capability.

---

#### Observability Module
The system shall provide a dedicated observability component, for example:

> **ObservabilityService** or **RunLogger**

This component is responsible for:

- receiving structured records from the simulation
- forwarding them to the configured logging/persistence backend
- maintaining run / episode / step aggregation where required

The simulation core must not directly manage logging details.

---

#### Separation from Visualization
Logging and observability must remain strictly separate from visualization.

##### Constraint

- visualization may consume observability records
- observability must not depend on visualization components

This preserves modularity and prevents unnecessary coupling between runtime diagnostics and presentation.

---

#### Construction of Episode-Level Summaries
Episode-level summaries shall be derivable from step-level data.

However, the system must provide explicit support for episode aggregation, so that episode summaries are available without requiring ad hoc reconstruction by the caller.

---

#### Integration with Existing Traces
The observability system must integrate naturally with:

- `DecisionTrace`
- `TransitionTrace`

These structures shall be reused or referenced, rather than duplicated in incompatible formats.

---

#### Design Rationale
This design is chosen because it provides:

- strong debugging support
- high transparency of system execution
- scalability from single-step debugging to batch experimentation
- compatibility with standard logging infrastructure
- clean separation between domain state and technical output handling

It also ensures that the baseline system remains inspectable without forcing verbose logging in all execution modes.

---

#### Implementation Consequence
Any implementation must ensure:

- structured observability records exist
- run, episode, and step observability are supported
- logging verbosity is configurable
- structured logging can be disabled when needed
- file persistence is optionally supported
- JSON / JSONL serialization is available
- position is included in external logs
- observability is handled by a dedicated module
- visualization remains a separate concern

---

### 5.9 Execution Model

#### Objective
Define a clear, structured, and fully controllable execution model for the baseline system, ensuring:

- explicit separation of step, episode, and run levels
- deterministic and reproducible execution under fixed seed conditions
- compatibility with debugging, visualization, and statistical evaluation
- support for both run-to-completion and stepwise execution
- strict avoidance of unintended coupling between episodes

The execution model defines how the system is actually run over time.

---

#### Execution Levels
The execution model shall explicitly distinguish between three levels:

- **Step**
- **Episode**
- **Run**

These levels must remain conceptually and structurally separate.

---

##### Step
A step is the smallest execution unit.

A single step consists of:

- observation availability
- policy decision
- transition execution
- observability update

Each step corresponds to one complete application of the baseline execution cycle.

---

##### Episode
An episode is a bounded execution sequence of steps starting from a freshly initialized system state.

An episode represents:

> one complete experimental realization of the system under fixed initial conditions and configuration

Episodes are independent from one another.

---

##### Run
A run is a higher-level execution unit containing one or more episodes executed under the same configuration.

A run represents:

- one coherent experiment setup
- one effective configuration
- one random seed context
- one set of aggregated results

The number of episodes per run shall be configurable.

---

#### Run Structure
A run shall consist of:

$$  
\text{Run} = \{ \text{Episode}_1, \text{Episode}_2, \dots, \text{Episode}_N \}  
$$

where:

- $N \geq 1$
- $N$ is configurable

This allows:

- single-episode debugging runs
- multi-episode statistical runs

---

#### Episode Independence
Each episode within a run must begin from a freshly initialized state.

This includes:

- fresh world state
- fresh agent core state
- fresh memory state
- fresh position
- fresh derived observation

##### Constraint
Episodes must not share internal state.

This prevents:

- hidden carryover effects
- contamination of results
- conceptual blurring between episode and continuous simulation

---

#### Episode Termination Conditions
An episode shall terminate when either of the following conditions is met:

##### 1. Terminal Condition
The agent reaches the baseline death condition:

$$ 
e_t \leq 0  
$$

##### 2. Step Limit
A configured maximum number of steps is reached.

Thus, the effective termination rule is:

> terminate at whichever condition occurs first

This is mandatory for:

- bounded experiments
- debugging
- sweep execution
- prevention of runaway episodes

---

#### Execution Style
The baseline execution model shall be:

- **synchronous**
- **sequential**
- **single-threaded at the core execution level**

##### Constraint
No parallelism shall be part of the baseline execution model itself.

Parallelism, if introduced later, belongs only to higher-level orchestration layers (e.g. experiment sweeps).

---

#### Execution Engine
The system shall provide a dedicated execution orchestrator, for example:

> **ExecutionEngine** or **RunExecutor**

This component is responsible for:

- managing run lifecycle
- creating and resetting episodes
- advancing steps
- invoking policy and transition components
- producing structured results
- coordinating observability output

The execution engine shall be the central entry point for simulation execution.

---

#### Execution Results
The execution model shall produce explicit structured results at multiple levels.

At minimum, the following result types shall exist:

- **StepResult**
- **EpisodeResult**
- **RunResult**

These result objects shall support:

- debugging
- post-run analysis
- statistics
- logging integration
- visualization

---

#### Stepwise Execution Support
The execution model must support both:

#### 1. Run-to-Completion Execution
The system executes a full run or episode automatically until termination.

#### 2. Stepwise Execution
The system can be advanced one step at a time.

This is required for:

- debugging
- manual inspection
- worked-example verification
- interactive visualization

---

#### Execution Hooks
The execution model shall provide hook points at all major execution boundaries.
At minimum, hooks shall be supported for:

- `before_run`
- `after_run`
- `before_episode`
- `after_episode`
- `before_step`
- `after_step`

##### Purpose

- debugging
- logging
- visualization
- controlled future extensions

##### Constraint
Hooks must be side-effect free in the baseline configuration unless explicitly extended later.

---

#### Seed and Randomness Model
The execution model shall use a **single run-level random seed**.
This seed defines the random context of the run as a whole.

##### Constraint

- no independent episode-level seed management in the baseline execution model
- randomness shall evolve deterministically from the run seed through sequential execution

This preserves:

- simplicity
- reproducibility
- clarity of random-state handling

---

#### Run-Level Reproducibility
Two runs with:

- identical configuration
- identical random seed

must produce identical execution behavior and identical aggregated results.

This includes:

- action sampling
- tie-breaking
- episode progression

---

#### Separation from Experiment Layer
Parameter sweeps and higher-level experiment orchestration are **not part of the execution model** itself.

They belong to a separate layer above the execution model.

##### Rationale

- keeps execution semantics simple
- avoids mixing experiment design with system runtime behavior
- preserves clarity of responsibilities

The execution model is therefore responsible for:

- running one configured run
- not for managing multi-run experiment grids

---

#### Design Rationale
This execution model is chosen because it provides:

- clear temporal structure
- strict episode independence
- clean run-level aggregation
- direct support for debugging and visualization
- strong reproducibility guarantees
- compatibility with future experiment orchestration

It reflects the baseline philosophy:

- minimal system dynamics
- maximal engineering transparency

---

#### Implementation Consequence
Any implementation must ensure:

- explicit step, episode, and run abstractions exist
- runs can contain multiple episodes
- every episode starts from a fresh initialization
- episodes terminate on death or max-step limit
- execution remains sequential
- a dedicated execution engine exists
- structured results are produced at all levels
- stepwise execution is supported
- hooks are available at run, episode, and step boundaries
- randomness is controlled solely by the run seed
- parameter sweeps are handled outside the execution model

---

### 5.10 Parameter Sensitivity & Stability

#### Objective
Define a structured framework for analyzing, understanding, and controlling the sensitivity and stability of the system with respect to:

- agent parameters
- environment parameters
- interaction dynamics

The goal is to ensure that the system:

- operates within meaningful behavioral regimes
- avoids trivial or degenerate outcomes
- remains reproducible and interpretable across runs

---

#### General Principle
The behavior of System A is highly dependent on parameter choices.

Due to:

- stochastic action selection
- nonlinear interaction between energy dynamics and environment
- local perception constraints

the system must be treated as an **empirically analyzable system**, not a fully analytically predictable one.

##### Constraint
System behavior must be validated through:

- controlled runs
- parameter variation
- structured observation

---

#### Parameter Categories
Sensitivity shall be analyzed across multiple parameter groups.

---

##### Agent Parameters
Examples include:

- action selection parameters (e.g. $\beta$)
- action preference weights (e.g. $w_{consume}, \lambda_{stay}$)
- energy dynamics parameters:
    
    - action costs
    - consumption gain
        
- normalization or scaling factors (e.g. $\kappa, c_{\max}$)

---

##### Environment Parameters
Examples include:

- grid size
- resource distribution
- regeneration rates
- obstacle density and placement
- initial world configuration

---

##### Initial Conditions
Examples include:

- initial energy level
- initial agent position
- initial resource distribution (if stochastic)

---

#### Baseline Reference Configuration
The system shall define a **baseline reference configuration**.

This configuration serves as:

- a starting point for experimentation
- a comparison anchor for parameter variation
- a reproducibility reference

##### Constraint

- the baseline configuration must be fully specified
- all parameters must be explicitly defined
- no implicit defaults are allowed

---

#### No Implicit Parameter Changes
All runs must operate under explicitly defined configurations.

##### Constraints

- no hidden parameter changes
- no implicit defaults without visibility
- all parameter values must be:
    
    - logged
    - reproducible
    - comparable across runs

---

#### Undesirable Behavioral Regimes
The system shall explicitly recognize and detect undesirable regimes.

These include, but are not limited to:

---

##### 1. Trivial Starvation

- agent dies consistently after very few steps
- survival time is minimal and highly concentrated

---

##### 2. Trivial Survival

- agent survives almost always regardless of behavior
- environment provides effectively unlimited energy

---

##### 3. Behavioral Collapse

- agent strongly favors a single action
- action diversity is extremely low

---

##### 4. Excessive Randomness

- action distribution remains near-uniform
- no consistent behavior patterns emerge

---

##### 5. Unstable Oscillation

- energy or behavior fluctuates strongly without stabilization
- system fails to reach any consistent regime

---

#### Stability Dimensions
Stability shall be evaluated along two complementary dimensions:

---

##### 1. Debug Stability
Concerns technical and numerical correctness.

Includes:

- deterministic reproducibility under fixed seed
- absence of runtime errors
- consistent state transitions
- no unintended divergence due to implementation artifacts

---

##### 2. Behavioral Stability
Concerns qualitative system behavior.

Includes:

- avoidance of trivial regimes
- emergence of interpretable behavior patterns
- consistent response to environmental conditions

---

#### Minimum Observables for Stability Analysis
The following metrics shall be observable and analyzable:

- survival time distribution per episode
- action distribution over time
- energy trajectory (per step and aggregated)
- resource consumption success rate
- episode termination causes
- position trajectories (for spatial analysis)

These observables must be derivable from the structured observability system.

---

#### Sensitivity Analysis Methodology
Parameter sensitivity shall be analyzed using structured experimentation.

---

##### Recommended Approach

- start from baseline reference configuration
- vary one parameter at a time (local sensitivity)
- perform controlled multi-parameter variation where necessary
- run multiple episodes per configuration
- compare distributions, not single trajectories

---

##### Execution Requirement
The system must support:

- repeated runs under identical configuration
- reproducible stochastic behavior via fixed seed
- efficient execution of multiple configurations (sweep capability)

---

#### Sweep Capability Requirement
The system shall support parameter sweeps as a core engineering capability.
Although sweeps are not part of the execution model itself, the system must enable:

- systematic variation of parameters
- batch execution of runs
- structured result comparison

---

#### No Fixed Optimality Criteria in Baseline
The baseline system shall not define fixed numerical thresholds for “good” behavior.

##### Rationale

- behavior depends on parameter interactions
- environment configuration influences outcomes
- premature thresholds risk invalid conclusions

Instead, the system defines:

- observable metrics
- identifiable regimes
- evaluation methodology

---

#### Design Rationale
This approach ensures that:

- the system remains scientifically analyzable
- parameter effects are made explicit
- undesirable configurations can be detected early
- experimentation is structured and reproducible

It reflects the nature of the system:

- simple in structure
- complex in emergent behavior

---

#### Implementation Consequence
Any implementation must ensure:

- all parameters are explicitly defined and logged
- baseline configuration exists and is reproducible
- observability supports required metrics
- multiple episodes per run are supported
- parameter variation is feasible and controlled
- undesirable regimes can be identified from logs
- no hidden parameter dependencies exist

---

### 5.11 Experimentation Framework

#### Objective
Define a structured framework for conducting reproducible experiments on the baseline system, ensuring:

- systematic comparison of configurations
- controlled execution of multiple runs
- support for parameter sweeps
- clean aggregation of results
- strict separation from the execution model
- reconstructability of all experiment outcomes

The experimentation framework is a higher-level orchestration layer above the execution model.

---

#### General Principle
An experiment shall be defined as a **structured collection of runs** executed under a shared experimental context.

Formally:

$$  
\text{Experiment} = \{\text{Run}_1, \text{Run}_2, \dots, \text{Run}_N\}  
$$

where each run may itself contain one or more episodes.

This establishes a strict hierarchy:

- **Step**: smallest execution unit
- **Episode**: one complete realization
- **Run**: one configured execution containing 1..n episodes
- **Experiment**: a collection of runs for comparison and analysis

---

#### Experiment Configuration
The experimentation framework shall use explicit configuration objects.

At minimum, the following conceptual configuration types shall exist:

- **RunConfig**
- **ExperimentConfig**

---

##### RunConfig
Defines the full configuration required to execute one run, including:

- system parameters
- environment parameters
- number of episodes
- maximum steps per episode
- random seed
- logging / observability settings

---

##### ExperimentConfig
Defines the higher-level structure of an experiment, including:

- experiment identifier
- collection of run configurations
- sweep definitions (if applicable)
- aggregation options
- persistence settings

---

#### Declarative Sweep Definition
Parameter sweeps shall be defined **declaratively**, not implicitly through ad hoc loops in code.

This means that the framework must support explicit specification of parameter variation such as:

- parameter name
- candidate values
- sweep strategy

The experimentation framework is responsible for expanding these definitions into concrete run configurations.

---

#### Supported Sweep Types
The baseline experimentation framework shall support at least:

##### 1. Grid Sweep
Cartesian expansion over explicitly provided parameter sets.

##### 2. One-Factor-at-a-Time Sweep
Variation of one parameter while holding all others fixed relative to a reference configuration.

---

#### Deferred Optimization Frameworks
The baseline experimentation framework shall not depend on advanced external optimization frameworks such as Optuna.

##### Rationale
At the baseline stage, the main goal is:

- interpretability
- regime discovery
- controlled comparison

not automatic optimization toward a single scalar objective.

However, the experimentation framework should be designed such that external optimization tools may be integrated later through adapters or higher-level orchestration layers.

---

#### Separation from Execution Model
The experimentation framework must remain strictly separate from the execution model.

##### Constraint

- the `ExecutionEngine` or `RunExecutor` shall know nothing about experiments
- the experimentation framework may invoke the execution model, but not vice versa

This preserves:

- architectural clarity
- testability
- modularity

---

#### Experiment Result Structure
The experimentation framework shall produce an explicit **ExperimentResult** structure.

At minimum, it shall contain:

- experiment identifier
- effective experiment configuration
- collection of `RunResult` objects
- references to associated logs / observability records
- lightweight aggregate summaries

---

#### Aggregation Requirements
The framework shall support lightweight result aggregation.

This includes:

- per-run summaries
- cross-run comparisons
- basic aggregate metrics across runs

Examples include:

- mean survival time
- action distribution summaries
- terminal condition frequencies
- resource consumption summaries

---

##### Constraint
The experimentation framework is not required to implement advanced statistical analysis internally.

Its primary responsibility is to:

- preserve raw results
- expose simple aggregates
- support later offline analysis

---

#### Reproducibility Requirement
The experimentation framework must ensure that experiments are reproducible.

This requires:

- explicit storage of all run configurations
- explicit storage of all seeds
- deterministic expansion of sweep definitions
- preservation of execution order where relevant

Two experiments with identical configuration and seed definitions must yield identical results.

---

#### Experiment Reconstruction
An experiment must be fully reconstructable.

This means the framework shall preserve:

- `ExperimentConfig`
- generated `RunConfig` objects
- associated seeds
- produced `RunResult` objects
- references to observability outputs

This enables:

- rerunning experiments
- comparing historical runs
- resuming analysis later

---

#### Observability Integration
The experimentation framework shall integrate with the structured observability system.

This includes:

- collecting references to run-level logs
- associating episode and step records with runs
- preserving experiment-level context for later analysis

The experimentation layer does not replace observability, but organizes it at experiment scope.

---

#### Execution Strategy
The baseline experimentation framework shall execute runs sequentially by default.

Parallel execution may be conceptually anticipated for future extensions, but is not part of the baseline implementation.

---

#### Parallelization Readiness
The experimentation framework should be designed such that future parallel execution is possible.

This means the framework should avoid assumptions that would prevent later support for:

- parallel run execution
- distributed sweep execution
- integration with external orchestration systems

However, such capabilities are explicitly deferred beyond the baseline implementation.

---

#### Design Rationale
This design is chosen because it provides:

- a clean separation between runtime execution and experimentation
- explicit reproducibility
- structured handling of parameter sweeps
- compatibility with future tooling
- preservation of raw and aggregated results

It also reflects the scientific purpose of the baseline system:

- not merely to run
- but to be studied systematically

---

#### Implementation Consequence
Any implementation must ensure:

- experiments are represented as collections of runs
- explicit configuration objects exist
- sweep definitions are declarative
- grid and one-factor-at-a-time sweeps are supported
- execution and experimentation remain strictly separated
- experiment results are explicitly represented
- lightweight aggregation is available
- all raw results remain accessible
- experiments are reconstructable
- observability integrates cleanly at experiment scope
- advanced optimization tooling is optional and external
- future parallelization remains structurally possible

---

### 5.12 Visualization Requirements

#### Objective
Define the visualization requirements for the baseline system, ensuring:

- replay-based inspection of recorded episodes
- strong support for debugging and interpretation
- strict separation from execution and experiment logic
- use of an existing visualization framework
- modularity for future extension

Visualization is considered a **supporting engineering capability**, not part of the simulation core.

---

#### General Principle
Visualization in the baseline system shall be based on **posterior replay** of recorded execution data.

This means:

- the simulation is executed first
- relevant results and logs are stored
- episodes are visualized afterward based on recorded data

Live visualization during execution is explicitly **out of scope** for the baseline implementation.

---

#### Visualization Mode
The baseline system shall support:

> **Posterior episode visualization**

The visualization shall consume structured experiment results, including:

- run-level results
- episode-level results
- step-level records

The primary purpose is to allow the user to:

- inspect completed episodes
- replay behavior step by step
- understand agent behavior in spatial context
- debug and interpret system dynamics

---

#### Strict Read-Only Constraint
The visualization layer must be strictly **read-only**.

It shall:

- display recorded simulation state
- navigate through previously recorded episode data
- provide inspection and replay controls

It shall not:

- modify simulation state
- trigger new decisions
- interact with the execution engine as a control mechanism
- alter agent or world behavior

This separation is mandatory.

---

#### Visualization Scope
The visualization shall operate primarily at the **episode level**.

The user shall be able to:

- select a run
- select an episode within that run
- replay that episode visually

Thus, the visualization system must support:

- run selection
- episode selection
- full episode playback

Step-level navigation is required as part of episode replay.

---

#### Minimum Visualized Content
The visualization shall display, at minimum:

- the grid world
- obstacles
- resource distribution / resource intensity
- agent position
- current action
- current energy value
- step counter
- episode identifier
- run identifier

These are considered core baseline visualization elements.

---

#### Debug Overlay Support
The visualization should support optional **debug overlays** for paused inspection.

Possible overlay content includes:

- detailed step information
- decision-related metadata
- memory summary
- additional state annotations

These overlays are optional but strongly encouraged for debugging support.

---

#### Playback Controls
The visualization shall support the following playback controls:

- **play**
- **pause**
- **step forward**
- optional **step backward**, if directly supported by stored records

Pause functionality is mandatory.

This is required to allow detailed inspection of specific moments in an episode.

---

#### Playback Speed Control
The visualization shall support adjustable playback speed.

For the baseline system, a simple discrete speed model is sufficient, for example:

- slow
- normal
- fast

This is considered adequate for initial replay functionality.

---

#### Data Source
The visualization shall operate primarily on:

- structured results
- recorded logs / traces

It shall not depend on live access to simulation internals.

This implies that the logging and observability system must capture all information required for replay.

---

#### Framework Choice
The baseline visualization shall use an **existing visualization framework**, with:

> **`pygame` as the baseline implementation target**

##### **Rationale**

- sufficient for 2D grid-based replay
- widely available
- simple enough for the baseline use case
- avoids unnecessary custom visualization infrastructure

---

#### Framework Abstraction Strategy
The baseline system shall not introduce a heavy multi-backend visualization abstraction layer.

However, visualization must still be implemented as a separate module so that future replacement or extension remains possible.

Thus:

- the baseline implementation is `pygame`-based
- the visualization logic remains modular and isolated
- backend interchangeability is not required in the first implementation, but is not structurally blocked

---

#### Visualization Module
The system shall provide a dedicated visualization component, for example:

- `VisualizationModule`
- `EpisodeReplayViewer`

This component is responsible for:

- loading or receiving recorded episode data
- rendering replay frames
- handling playback controls
- showing debug overlays

It must remain independent from:

- execution engine
- transition engine
- policy logic
- experimentation framework

except through structured results and observability records.

---

#### Dependency on Observability
The visualization layer depends on the structured observability layer.

Therefore, the system must ensure that episode and step records contain all information required for replay, including:

- spatial state
- agent position
- resource representation
- selected action
- energy state
- timing / ordering information

If necessary, visualization-specific replay data may be derived from the existing observability records, but no separate simulation pathway shall be introduced.

---

#### Design Rationale
This design is chosen because it provides:

- strong replay-based debugging support
- direct visual inspection of agent behavior
- no coupling between UI and simulation core
- compatibility with the modular architecture already defined
- a practical implementation path using an existing 2D framework

It also keeps the baseline focused:

- simulation first
- replay and analysis afterward

---

#### Implementation Consequence
Any implementation must ensure:

- visualization is posterior, not live
- replay is episode-based
- run and episode selection are supported
- playback controls include pause
- playback speed is adjustable
- the visualization layer is read-only
- `pygame` is used as the baseline framework
- visualization is implemented as a separate module
- required replay data is available through structured results and logs


---

### 5.13 Testing Strategy

#### Objective
Define a comprehensive and efficient testing strategy for the baseline system, ensuring:

- correctness of isolated components
- correctness of component interaction
- correctness of end-to-end execution
- reproducibility under controlled randomness
- early detection of regressions and invalid states
- strong support for implementation with coding assistants and LLM-based tooling

Testing is considered a core engineering requirement of the baseline system.

---

#### General Principle
The testing strategy shall be multi-layered and explicitly aligned with the modular system architecture.

The goal is not merely to detect failures after implementation, but to:

- guide implementation
- constrain incorrect agent-generated code
- preserve conceptual integrity during refactoring
- support safe extension of the system over time

---

#### Test Levels
The system shall explicitly support the following testing levels:

---

##### 1. Unit Tests
Unit tests validate isolated components in controlled conditions.

These tests must focus on:

- deterministic module behavior
- input/output correctness
- boundary conditions
- error handling

---

##### 2. Integration Tests
Integration tests validate the correct interaction of multiple components.

These tests must ensure that:

- interfaces align
- orchestration order is correct
- combined state transitions remain valid
- structured traces and results are produced consistently

---

##### 3. System / End-to-End Tests
System tests validate complete execution flows, such as:

- full episode execution
- run execution with multiple episodes
- structured observability generation
- reconstruction of results from complete runs

These tests verify that the system works as a coherent whole.

---

##### 4. Regression Tests
Regression tests preserve previously verified behavior and known edge-case fixes.

These tests must ensure that:

- previously resolved defects do not reappear
- critical invariants remain protected during refactoring
- agent-generated implementation changes do not silently break established behavior

---

#### Deterministic Testing Requirement
Tests shall be deterministic by default.

##### **Constraint**

- fixed seeds shall be used wherever randomness is involved
- test results must be reproducible

This applies especially to:

- action sampling
- tie-breaking
- multi-step execution traces

---

#### Testing of Stochastic Components
Stochastic behavior shall be tested explicitly.

This includes:

- reproducibility under fixed seeds
- consistency of seeded sampling behavior
- plausibility of distributions over repeated samples

##### Constraint
Stochastic tests must remain controlled and non-flaky.

This may be achieved through:

- fixed seed sequences
- bounded tolerance checks
- repeated-run distribution checks under controlled conditions

---

#### Numerical Tolerance
All floating-point comparisons in tests shall use explicit numerical tolerances where appropriate.

This applies especially to:

- Softmax probabilities
- energy values
- normalized observation values
- aggregated metrics

##### Constraint

Tests must not rely on exact floating-point equality where numerical approximation is expected.

---

#### Minimum Unit Test Scope
At minimum, unit tests shall exist for the following components:

- Hunger Drive module
- policy score computation
- Softmax probability computation
- action admissibility masking
- world regeneration logic
- resource consumption logic
- agent energy update logic
- memory update logic
- termination criterion
- configuration validation

---

#### Integration Test Scope
At minimum, integration tests shall exist for the following interactions:

- policy decision pipeline and `DecisionTrace`
- transition engine and its submodules
- execution engine across step / episode / run levels
- observability system integration with execution results
- replay-data preparation for visualization

These tests must confirm that module boundaries work correctly in combination.

---

#### System / End-to-End Test Scope
End-to-end tests shall validate complete baseline flows, such as:

- full episode execution from initialization to termination
- multi-episode run execution
- deterministic replayability under fixed seed
- logging and result generation under configured observability modes
- reconstruction and inspection of completed experiment outputs

---

#### Visualization Testing
Visualization shall be tested only in a lightweight functional manner in the baseline system.

This includes verifying that:

- replay data can be loaded correctly
- run and episode selection works
- playback logic functions correctly
- pause and replay controls do not raise errors

The baseline testing strategy does not require:

- pixel-perfect UI tests
- visual snapshot testing
- heavy GUI automation

---

#### Coverage Principle
Test coverage is considered important, but no rigid numeric threshold is mandated in this specification.

##### Rationale

- meaningful coverage is more important than formal percentage targets
- coverage should support confidence, not become a dogmatic metric

The testing strategy should aim for broad and practical coverage across:

- core logic
- interfaces
- failure modes
- invariants

---

#### Property-Based Testing
Property-based testing shall be considered a supported testing approach for baseline invariants.

Examples include:

- probabilities sum to 1
- inadmissible actions receive zero probability
- energy remains within valid bounds
- memory never exceeds configured capacity
- deterministic seeds reproduce identical traces

This form of testing is especially useful for guarding structural invariants across broader input spaces.

---

#### Fail-Hard Behavior Testing
The fail-hard design of the baseline system must be tested explicitly.

This includes tests ensuring that explicit errors are raised for cases such as:

- invalid actions reaching the transition layer
- invalid configurations
- inconsistent or corrupted state structures
- missing required parameters

These tests are mandatory.

---

#### Regression Testing Requirement
Regression tests are required.

They shall be used to preserve correctness around:

- previously identified defects
- subtle edge cases
- known failure modes
- behaviorally sensitive configurations

Examples include:

- incorrect STAY suppression
- masked movement actions becoming selectable
- memory being consulted unintentionally
- biased tie-breaking behavior

---

#### Reference Worlds and Fixtures
The test strategy shall include explicit reusable fixtures and reference worlds.

Examples include:

- small empty world
- no-resource world
- single-food world
- corridor world
- obstacle-blocked world

These fixtures must be:

- deterministic
- easy to inspect
- stable across test runs

They serve as a shared basis for:

- unit tests
- integration tests
- regression tests

---

#### Tooling and Automation
The testing strategy shall support efficient implementation using modern tooling, including coding assistants and LLM-based development workflows.

This implies:

- clear test structure
- deterministic fixtures
- modular assertions
- explicit expected behaviors

Tests should be easy to generate, inspect, and maintain.

---

#### Continuous Integration
Automated test execution shall be anticipated as part of the engineering workflow.

This includes support for:

- automated unit and integration test execution
- regression checks on changes
- repeatable validation in CI environments

The exact CI setup is outside the scope of this section, but CI-readiness is a required engineering consequence.

---

#### Design Rationale
This testing strategy is chosen because it provides:

- strong control over correctness
- broad protection against regressions
- good compatibility with modular architecture
- support for reproducible stochastic systems
- practical guidance for implementation with coding assistants

It reflects the engineering philosophy of the baseline system:

- minimal in behavior
- rigorous in structure
- transparent in verification

---

#### Implementation Consequence
Any implementation must ensure:

- all major test levels are present
- tests are deterministic by default
- stochastic behavior is tested in controlled form
- numerical tolerances are used where appropriate
- all core modules receive unit tests
- major integration boundaries are tested
- fail-hard behavior is verified
- regression tests are maintained
- reusable reference worlds and fixtures exist
- visualization is tested functionally
- CI integration remains possible and natural

---

## 6. Open Issues Summary
This section will later contain:

- Final decisions
- Trade-offs
- Justifications

---
