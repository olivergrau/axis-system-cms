# **WP6 Implementation Brief – Transition Engine**

## **Context**

We are implementing **System A (Baseline)** of the AXIS project.

This system is a **deterministic, mechanistic agent-environment simulation framework** with:

* explicit world state
* explicit agent state
* local observation model
* hunger-driven action modulation
* policy-based action selection
* deterministic transition execution under fixed seeds

The implementation follows a **specification-first architecture**.

Previous work packages established:

* **WP1**: configuration and foundational runtime types
* **WP2**: world representation and observation construction
* **WP3**: agent state and baseline memory
* **WP4**: hunger drive computation
* **WP5**: policy and decision pipeline

WP6 must now implement the **Transition Engine**, which is the only component allowed to evolve the runtime state from one step to the next.

This package must remain fully aligned with the baseline architecture and the engineering pre-specification. It must not drift into policy logic, execution loop orchestration, experiment logic, or logging concerns. The transition system must be explicit, deterministic, phase-ordered, and fail-hard on invalid conditions.

---

## **Objective**

Implement **WP6 – Transition Engine**.

The goal of this package is to create a correct, explicit, and testable implementation of the baseline state transition function:

$$
\Sigma_{t+1} = F(\Sigma_t, a_t)
$$

where the transition evolves:

* world state
* agent state
* memory state
* observation
* termination state

This package must provide the minimal but architecturally correct foundation required for later implementation of:

* episode execution
* step result construction
* deterministic end-to-end validation

The package must support:

* strict execution order
* explicit input/output state handling
* deterministic state evolution
* traceability of what changed in one step

---

## **Scope**

Implement only the following.

---

### **1. Transition Engine as Central Orchestrator**

Implement a dedicated `TransitionEngine` component responsible for executing one complete transition step.

The engine must be the **only component** that updates runtime state.

It must consume:

* current world state
* current agent state
* current memory state
* current observation
* selected action
* relevant configuration

It must produce:

* next world state
* next agent state
* next memory state
* next observation
* termination flag
* transition trace

Important:

* do not mutate global state
* prefer explicit input → output transformation
* do not let subcomponents evolve state independently outside the transition flow

This directly follows the architectural role of the Transition Engine as the sole state-evolving component. 

---

### **2. Strict Phase Ordering**

The transition must follow the exact baseline phase structure.

Implement these phases in order:

#### **Phase 1 – World Regeneration / World Update**

Apply the environment-side update that happens before action effects.

Important:

* only implement what is already defined in the baseline world model
* if the current world implementation does not yet support regeneration explicitly, implement the minimal baseline-compatible world update behavior required by the existing specifications
* keep this phase clearly separated from action application

#### **Phase 2 – Action Application**

Apply the selected action to the world-interaction layer.

This includes:

* movement intent handling
* blocked movement handling
* consume interaction on current cell
* no policy logic here

#### **Phase 3 – Next Observation Construction**

Build the next observation from the updated world state and updated position.

Use the same observation builder from WP2.
Do not duplicate observation logic.

#### **Phase 4 – Agent State Update**

Update agent-side internal state based on:

* action cost
* successful or unsuccessful consumption outcome
* resulting energy change

This must remain deterministic and explicit.

#### **Phase 5 – Memory Update**

Update memory using the **new observation**, not the old one.

This is important and already fixed in your specification:
memory records the post-transition perceptual state.

#### **Phase 6 – Termination Evaluation**

Evaluate whether the episode must terminate.

At minimum, termination must reflect baseline energy depletion semantics.

This phase ordering must not be changed.

---

### **3. World Update and Action Effects**

Implement the world-side transition behavior needed by the baseline.

This includes:

* movement attempt to neighboring cell
* blocked movement if target cell is non-traversable
* no silent rerouting
* consume affects the **current cell**
* resource change is explicit and local
* if no resource is available, consume has no positive effect

Important:

* world logic must stay world-local
* do not add reward semantics
* do not add planning hints
* do not let the world “correct” bad actions

---

### **4. Agent Energy Update**

Implement deterministic energy update logic based on the baseline state transition model.

This includes:

* action-dependent cost
* energy gain through successful consumption only
* clipping to valid energy bounds if required by the baseline state model

Important:

* energy update must not be hidden inside the world
* energy update must not be computed in the policy
* the Transition Engine must coordinate it explicitly

The result must remain consistent with the baseline definition of hunger and later drive recomputation.

---

### **5. Memory Update**

Integrate the memory-state-level behavior from WP3 into the transition sequence.

Important:

* memory must be updated with the **newly produced observation**
* memory remains behaviorally inactive
* no retrieval logic
* no inference
* no semantic enrichment

This is purely a structural runtime update.

---

### **6. Termination Criterion**

Implement the baseline termination criterion.

At minimum:

* termination when agent energy is depleted according to the baseline rules

Do not add:

* timeout logic beyond what belongs later to the execution loop
* external stop conditions
* experiment-level stopping rules

---

### **7. Transition Trace**

Implement a minimal but explicit `TransitionTrace`.

It should include enough information to support:

* debugging
* test assertions
* later observability integration

At minimum, the trace should include:

* input action
* pre-state summary
* post-state summary
* movement outcome
* resource consumption outcome
* energy before / after
* memory before / after summary
* termination flag

Keep the trace simple but structurally clear.

---

## **Out of Scope**

Do **not** implement any of the following in WP6:

* policy logic
* drive computation
* action selection
* execution loop orchestration
* multi-step episode control
* logging backend
* experiment framework
* visualization
* replay system
* learning
* planning
* stochastic world behavior unless explicitly already defined and seeded
* silent fallback or auto-correction logic

Do not let the Transition Engine become the execution loop or a policy substitute.

---

## **Architectural Constraints**

The implementation must follow these rules.

### **1. Transition Engine is the only state-evolving component**

No other component may apply runtime state changes outside this transition flow.

### **2. Fail-hard behavior**

Do not silently repair invalid conditions.

Examples:

* invalid positions
* impossible world state
* malformed action handling

These must raise explicit errors or fail explicitly according to the architecture. The pre-spec explicitly calls for fail-hard behavior here. 

### **3. No policy logic**

The Transition Engine must not:

* rescore actions
* choose alternative actions
* reinterpret the selected action

### **4. No hidden mutation**

Prefer explicit return of new state or clearly controlled state updates.
Do not rely on uncontrolled implicit mutation across components.

### **5. Reuse existing components**

The Transition Engine must reuse:

* world representation from WP2
* observation construction from WP2
* agent/memory state models from WP3

Do not duplicate those concerns.

### **6. Deterministic behavior**

Given:

* identical input state
* identical selected action
* identical configuration

the transition must produce identical output state.

---

## **Expected File Structure**

Extend the existing `src/` package in a simple and readable way.

A reasonable structure could be:

```text
src/axis_system_a/
    config.py
    enums.py
    types.py
    world.py
    observation.py
    agent_state.py
    memory.py
    drives.py
    policy.py
    transition.py
    __init__.py
```

If desired, you may split out a small `termination.py` only if it improves clarity without over-fragmentation.

Do not introduce a full runtime framework or plugin architecture here.

---

## **Testing Requirements**

Also create pytest tests for WP6.

At minimum include tests for the following.

### **Movement tests**

* valid movement changes position correctly
* blocked movement leaves position unchanged
* movement does not corrupt world state

### **Consume tests**

* consuming on a resource-bearing current cell updates resource correctly
* consuming on an empty cell yields no positive effect
* consume affects only the current cell

### **Energy update tests**

* energy decreases according to action cost
* energy increases only through successful consumption
* energy remains within valid bounds
* invalid energy handling fails explicitly if appropriate

### **Memory update tests**

* memory is updated using the new observation
* memory ordering remains correct
* capacity remains respected after transition

### **Termination tests**

* zero or depleted energy yields termination
* non-terminal states remain non-terminal

### **Transition trace tests**

* trace contains the required fields
* trace is consistent with actual state change

### **Determinism tests**

* same state + same action → same next state
* repeated identical transition inputs produce identical outputs

Use small handcrafted worlds and explicit states.
Do not rely on random generation.

---

## **Implementation Style**

* Python 3.11
* clear type hints
* explicit and readable phase structure
* concise docstrings where useful
* no unnecessary comments
* no speculative abstractions

If helper functions improve readability, that is fine.
But the transition order must remain obvious in the code.

---

## **Expected Deliverable**

Return:

1. the proposed file structure
2. the implementation for WP6
3. the corresponding pytest tests
4. a short explanation of any design decision that is not obvious

---

## **Important Final Constraint**

This package is the first one that makes the system **actually evolve in time**, but it must remain:

* phase-ordered
* deterministic
* explicit
* narrowly scoped

A modest but architecturally correct Transition Engine is preferred over a broader implementation that starts absorbing execution control, policy behavior, or observability concerns.

---

## What I would review very carefully in the WP6 plan

This is the critical checklist:

### Red flags

* transition engine recomputes policy or drive output
* transition engine silently replaces invalid actions
* memory updated with old observation instead of new one
* execution loop logic leaks into transition
* world update and action effects get mixed in an unclear order
* hidden in-place mutation all over the place
* consume affects neighboring cells or non-current cells

### Good signs

* explicit phase structure
* clear ownership of each state update
* reuse of WP2 and WP3 components
* minimal but explicit transition trace
* deterministic and fail-hard behavior

---

