# **WP7 Implementation Brief – Episode Execution Loop**

## **Context**

We are implementing **System A (Baseline)** of the AXIS project.

This system is a **deterministic, mechanistic agent-environment simulation framework** with:

* explicit world state
* explicit agent state
* local observation model
* hunger-driven action modulation
* policy-based action selection
* deterministic transition execution

Previous work packages established:

* **WP1–WP3**: structural foundation
* **WP4**: Hunger Drive (motivational scoring)
* **WP5**: Policy (decision pipeline)
* **WP6**: Transition Engine (state evolution)

WP7 must now implement the **Episode Execution Loop**, which repeatedly applies:

$$
\text{Observation} \rightarrow \text{Drive} \rightarrow \text{Policy} \rightarrow \text{Transition}
$$

until termination.

This package must remain strictly aligned with the architecture and must not absorb responsibilities from other components.

---

## **Objective**

Implement **WP7 – Episode Execution Loop**.

The goal of this package is to create a correct, explicit, and testable implementation of:

1. **single-step orchestration**
2. **multi-step episode execution**
3. **termination handling**
4. **step result tracking**
5. **deterministic execution control**

This package must provide the minimal but correct foundation for:

* simulation runs
* debugging and validation
* later logging/observability integration

---

## **Scope**

---

### **1. Step Function (Single Iteration)**

Implement a `step(...)` function that performs exactly one full cycle:

1. current observation (already available from previous state)
2. compute drive output (WP4)
3. compute action via policy (WP5)
4. apply transition (WP6)
5. return next state + step result

Important:

* **do not recompute observation outside transition**
* next observation must come from Transition Engine output
* no duplicated logic

---

### **2. Episode Execution Loop**

Implement an `EpisodeRunner` (or similar) that repeatedly executes steps.

Loop structure:

```text
initialize state
while not terminated:
    step()
```

Termination must come **only from Transition Engine output**.

---

### **3. Initial State Construction**

Provide a clean way to initialize:

* world state
* agent state
* memory state
* initial observation

Important:

* initial observation must be built using the observation system (WP2)
* do not hardcode observation
* do not skip perception layer

---

### **4. Step Result Structure**

Implement a structured `StepResult`.

At minimum it should contain:

* timestep index
* observation (pre or post, choose explicitly and stay consistent)
* selected action
* policy trace (optional but recommended)
* transition trace
* resulting agent energy
* termination flag

Keep structure explicit and inspectable.

---

### **5. Episode Result Structure**

Implement an `EpisodeResult`:

* sequence of step results
* total number of steps
* termination reason (minimal baseline: energy depletion)
* final state snapshot

Do not over-engineer.

---

### **6. Determinism and Seeding**

The execution loop must support deterministic runs.

Requirements:

* RNG seed must be configurable
* seed must be applied to policy sampling
* identical seed + initial state → identical trajectory

Do not introduce additional randomness.

---

### **7. Maximum Step Guard (Optional but Controlled)**

Support an optional:

* `max_steps`

If present:

* loop terminates after max_steps
* termination reason must be explicit

Important:

* this is a **safety guard**, not core termination logic
* must not replace energy-based termination

---

## **Out of Scope**

Do **not** implement:

* learning
* training loops
* batch execution
* multi-agent support
* logging backend (only local structures)
* visualization
* replay systems
* experiment tracking
* metrics aggregation
* reward accumulation
* planning
* lookahead
* parallel execution

---

## **Architectural Constraints**

### **1. Thin Orchestrator Only**

The loop must not:

* implement drive logic
* implement policy logic
* implement transition logic

It must only call existing components.

---

### **2. No Logic Duplication**

Do not:

* recompute observation manually
* reimplement masking
* recompute energy updates

Everything must go through WP4–WP6.

---

### **3. Deterministic Execution**

Given:

* same initial state
* same config
* same seed

→ identical episode

---

### **4. Explicit State Flow**

State must flow explicitly:

```text
state_t → step → state_t+1
```

No hidden global state.

---

### **5. Fail-Hard Behavior**

If something invalid happens:

* do not silently continue
* raise explicit errors

---

## **Expected File Structure**

```text
src/axis_system_a/
    ...
    drives.py
    policy.py
    transition.py
    runner.py
    results.py
    __init__.py
```

Keep it simple.

---

## **Testing Requirements**

### **Single-step tests**

* step produces valid next state
* action is consistent with policy output
* transition result is correctly applied

---

### **Episode tests**

* episode terminates when energy is depleted
* episode runs multiple steps correctly
* step count matches expected behavior

---

### **Determinism tests**

* same seed → identical trajectories
* different seed → different trajectories (if stochastic)

---

### **Integration tests**

* full pipeline WP2–WP6 works together
* no component bypassed

---

### **Max-step tests**

* loop stops at max_steps
* termination reason is correct

---

## **Implementation Style**

* Python 3.11
* explicit, readable loop
* no hidden magic
* no premature abstractions
* no orchestration frameworks

---

## **Expected Deliverable**

1. file structure
2. implementation
3. pytest tests
4. short explanation of design decisions

---

## **Important Final Constraint**

This package must feel like:

> a **wiring layer**, not a thinking system

If WP7 contains logic that “decides things”, something is wrong.

---

# What I would check in the WP7 plan

### 🚨 Red flags

* loop recomputes observation manually
* policy or drive logic duplicated
* hidden global state
* transition not used properly
* termination logic outside transition
* step result inconsistent

---

### ✅ Good signs

* clean loop structure
* explicit state passing
* reuse of all previous modules
* simple result structures
* deterministic seed handling

---
