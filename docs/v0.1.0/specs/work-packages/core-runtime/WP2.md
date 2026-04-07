# **WP2 Implementation Brief – World Model and Observation Construction**

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
This work package is **WP2** and builds directly on WP1.

WP1 already established:

* configuration structures
* core runtime enums
* foundational runtime types
* minimal validation

WP2 must now implement the **external environment representation** and the **local observation construction** used by all later runtime components. It must remain strictly aligned with the baseline architecture and must not jump ahead into drive, policy, or transition behavior. The world and sensor are already defined as part of the Core Runtime Architecture, and the sensor must remain the only permitted information channel from world to agent.

---

## **Objective**

Implement **WP2 – World Model and Observation Construction**.

The goal of this package is to create a correct, explicit, and testable representation of:

1. the **world state**
2. the **cell structure**
3. the **agent position as part of world state**
4. the **observation builder / sensor projection**

This package must provide the minimal but architecturally correct foundation required for later implementation of:

* hunger drive computation
* admissibility masking in policy
* state transition logic
* episode execution

The package must be implemented in a way that supports:

* deterministic behavior
* explicit state handling
* later testing
* strict separation between world, observation, and agent internals

---

## **Scope**

Implement only the following.

### **1. Cell Representation**

Create an explicit `Cell` model for the grid world.

The world representation in the architecture uses explicit cells with:

* traversability / obstacle semantics
* resource value
* clear invariants

A reasonable implementation may use either:

* a `CellType` enum plus `resource_value`
* or an explicit obstacle flag plus `resource_value`

but the resulting semantics must remain fully aligned with the baseline documents.

At minimum, each cell must support:

* whether it is traversable
* whether it is blocked / obstacle
* current resource intensity or value

The representation must remain **clear and inspectable**, not compressed or tensor-like.

---

### **2. World Representation**

Create a `World` model representing the external environment as a **finite two-dimensional grid**.

The world must include:

* `width`
* `height`
* grid storage of cells
* agent position stored in world state, not in agent state

Implement minimal, side-effect-free access operations such as:

* get cell by position
* bounds checking
* traversability checks

The world must remain a **passive state container**.
Do not place behavior, policy knowledge, or transition logic into the world object.

---

### **3. Position Use Within World State**

Use the `Position` type already created in WP1.

The agent position must be represented as part of world state.

Important constraint:

* `AgentState` must **not** contain absolute position
* observation must derive local information from world state + position
* no hidden coordinate leakage to the agent

This separation is a hard architectural rule.

---

### **4. Observation / Sensor Construction**

Implement the baseline observation builder.

The observation must be derived from the **von Neumann neighborhood** around the current agent position:

* center
* up
* down
* left
* right

For each observed cell, construct the local tuple:

* `b_j`: traversability signal
* `r_j`: resource intensity signal

The full observation must follow the fixed order:

* center
* up
* down
* left
* right

The final observation must match the baseline structure and remain stable across all later packages.

Important:

* out-of-bounds neighbors must be represented as `(0, 0)`
* no gradients
* no semantic labels
* no derived directional summaries
* no access to hidden world parameters such as regeneration rate or max resource capacity

The observation builder must remain a **pure projection component**, not a decision component.

---

### **5. Normalization Rule**

If the world stores resource values already normalized to `[0,1]`, the observation builder may pass them through directly.

If not, explicit normalization must be applied in the observation layer.

For WP2, prefer the simpler implementation:

* store world resource values already in `[0,1]`
* pass them through directly into observation

This keeps the MVP simpler while remaining fully consistent with the baseline model.

---

### **6. Minimal World Initialization**

Provide a minimal deterministic way to construct a valid world instance.

This can be simple and explicit.

Examples:

* build from dimensions + default empty cells
* optionally allow a handcrafted grid input for tests

Do not implement complex world generation strategies yet.

---

## **Out of Scope**

Do **not** implement any of the following in WP2:

* hunger drive computation
* policy logic
* action masking
* Softmax
* transition engine
* movement application
* consumption mechanics
* regeneration update logic
* episode loop
* logging
* experiment system
* visualization
* random world generation frameworks
* complex scenario DSLs
* memory behavior
* learned or semantic observation features

Do not anticipate WP3+ behavior in this package.

---

## **Architectural Constraints**

The implementation must follow these rules.

### **1. World is passive**

The world must not:

* update itself
* evaluate actions
* compute transitions
* encode reward or desirability semantics

### **2. Observation is pure**

The observation builder must:

* depend only on world state and position
* construct local observations deterministically
* add no higher-order interpretation

### **3. No leakage of global information**

The observation must not expose:

* absolute position
* full grid
* distant cells
* hidden world parameters
* future information

### **4. Explicitness over compactness**

Prefer:

* readable classes / models
* explicit field names
* inspectable structures

Avoid:

* overly compressed encodings
* premature vectorization
* tensor-first designs

### **5. Stable ordering**

Observation field ordering must be explicit and stable, because later drive and policy modules depend on it.

---

## **Expected File Structure**

Extend the existing `src/` package from WP1 in a simple and readable way.

A reasonable structure could be:

```text
src/axis_system_a/
    config.py
    enums.py
    types.py
    world.py
    observation.py
    __init__.py
```

If desired, `Cell` may live in `world.py` unless a separate `cells.py` is clearly justified.

Do not fragment the world layer into too many small files.

---

## **Testing Requirements**

Also create pytest tests for WP2.

At minimum include tests for the following.

### **World structure tests**

* valid world can be created from config
* width / height are correct
* agent position is valid
* cells can be retrieved correctly
* out-of-bounds access is handled explicitly or safely, depending on chosen API

### **Cell invariant tests**

* obstacle / blocked cells behave as non-traversable
* resource values remain within valid range
* invalid cell configurations fail explicitly if validation is implemented

### **Observation construction tests**

* observation contains exactly the expected neighborhood structure
* field ordering is correct and stable
* center / up / down / left / right mapping is correct
* out-of-bounds neighbors are mapped to `(0,0)`
* blocked cells produce the correct traversability signal
* resource values propagate correctly into observation

### **Separation tests**

* agent position is not stored in `AgentState`
* observation builder uses world state + position only
* no hidden world information is included in observation

Use **small handcrafted worlds** for tests.
Do not rely on random generation.

---

## **Implementation Style**

* Python 3.11
* clear type hints
* strongly typed, readable models
* concise docstrings where useful
* no unnecessary comments
* no speculative abstractions

If Pydantic is used for world-side models, use it only where it improves validation clarity.
Do not force Pydantic everywhere if normal dataclasses or explicit classes are clearer.

---

## **Expected Deliverable**

Return:

1. the proposed file structure
2. the implementation for WP2
3. the corresponding pytest tests
4. a short explanation of any design decision that is not obvious

---

## **Important Final Constraint**

This package is still a **foundation package**.

That means:

* it must remain small
* it must remain correct
* it must preserve architectural boundaries
* it must not sneak transition logic or policy logic into the world / observation layer

A modest but architecturally correct implementation is preferred over a broader implementation that begins to blur component responsibilities.

---

