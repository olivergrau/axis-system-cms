# **WP1 Implementation Brief – Core Configuration and Fundamental Runtime Types**

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
This work package is the **first MVP package** and must establish the foundational runtime structures on which all later packages depend.

This is **not** a prototype for quick experimentation.
It is the first implementation slice of the actual architecture.

---

## **Objective**
Implement **WP1 – Core Configuration and Fundamental Runtime Types**.

The goal of this package is to create the minimal but stable foundation required for all later work packages.

This includes:

* configuration structures
* shared runtime enums
* core immutable or near-immutable value types
* minimal validation rules
* serialization-friendly data structures

The package must be implemented in a way that supports:

* deterministic execution
* explicit state handling
* later testing
* later extension without premature abstraction

---

## **Scope**
Implement only the following:

### **1. Configuration Model**
Create a minimal structured runtime configuration model for the MVP with these sections:

* `general`
* `world`
* `agent`
* `policy`
* `execution`

Each section should contain only the parameters required for early MVP runtime initialization.

You may use **Pydantic models** for validation and explicit typing.

At minimum, support fields such as:

#### `general`

* `seed: int`

#### `world`

* `grid_width: int`
* `grid_height: int`

#### `agent`

* `initial_energy: float`
* `max_energy: float`
* `memory_capacity: int`

#### `policy`

* `selection_mode`
* `temperature: float`
* `stay_suppression: float`
* `consume_weight: float`

#### `execution`

* `max_steps: int`

Do **not** add experiment/sweep configuration.

---

### **2. Action Enum**
Create a stable action enum containing exactly:

* `UP`
* `DOWN`
* `LEFT`
* `RIGHT`
* `CONSUME`
* `STAY`

The ordering must be stable and reusable across later policy and drive modules.

---

### **3. Fundamental Runtime Types**
Create typed foundational runtime structures for later packages.

At minimum define:

* `Position`
* `Observation`
* `MemoryState`
* `AgentState`

These should be explicit and serialization-friendly.

#### `Position`

* `x: int`
* `y: int`

#### `Observation`
Should represent the baseline fixed observation vector structure.
At WP1 stage it does not need full sensor logic yet, but the type must already exist.

A good approach is either:

* a dedicated typed record with named fields
* or a strict wrapper around a fixed-length vector

Prefer clarity over compactness.

#### `MemoryState`

* bounded list-like state holder
* at WP1 only the structural representation is required, not full update behavior

#### `AgentState`

* `energy: float`
* `memory_state: MemoryState`

Important:

* absolute world position must **not** be part of `AgentState`

---

### **4. Minimal Validation**
Implement basic validation rules, such as:

* grid dimensions > 0
* `0 < initial_energy <= max_energy`
* `memory_capacity > 0`
* `temperature > 0`
* `max_steps > 0`
* `stay_suppression >= 0`
* `consume_weight > 0`

Validation must fail explicitly.

---

## **Out of Scope**
Do **not** implement any of the following in WP1:

* world grid or cell behavior
* observation construction logic
* hunger drive computation
* policy logic
* transition engine
* episode loop
* logging
* experiment system
* visualization
* advanced plugin systems
* alternative policy families
* memory update behavior
* YAML-based config loading unless trivially small

Do not anticipate future systems beyond what is needed structurally.

---

## **Architectural Constraints**
The implementation must follow these rules:

### **1. No hidden global state**
Do not use module-level mutable state.

### **2. No premature abstraction**
Do not introduce plugin frameworks, registries, factories, or inheritance hierarchies that are not needed for WP1.

### **3. Explicitness over cleverness**
Prefer readable, strongly typed structures over compressed or generic meta-programming solutions.

### **4. Serialization readiness**
All types should be easy to serialize later to JSON-compatible structures.

### **5. Agent/world separation**
Do not place world information, especially position, inside `AgentState`.

---

## **Expected File Structure**
You may choose a clean Python package layout under `src/`, but keep it simple.

A reasonable target would be something like:

```text
src/axis_system_a/
    config.py
    enums.py
    types.py
    __init__.py
```

You may refine the layout slightly if it improves clarity, but do not fragment the package into too many files.

---

## **Testing Requirements**
Also create initial tests for WP1.

At minimum include tests for:

### Configuration validation

* valid config passes
* invalid grid size fails
* invalid energy bounds fail
* invalid memory capacity fails
* invalid policy parameters fail

### Enum correctness

* action enum contains exactly the required actions
* ordering is stable

### Type structure sanity

* `Position` can be instantiated correctly
* `AgentState` contains energy and memory only
* `Observation` enforces expected structure
* objects are serializable or easily dumpable

Use **pytest**.

Keep the tests simple, deterministic, and focused on structure and validation.

---

## **Implementation Style**

* Python 3.11
* clear type hints
* small, readable modules
* concise docstrings where useful
* no unnecessary comments
* no speculative features

---

## **Expected Deliverable**
Return:

1. the proposed file structure
2. the implementation for WP1
3. the corresponding pytest tests
4. a short explanation of any design decision that is not obvious

---

## **Important Final Constraint**
This package is a **foundation package**.

That means:

* it must be small
* it must be correct
* it must be stable
* it must not try to “jump ahead” into WP2 or later packages

A modest but architecturally correct implementation is preferred over a larger but speculative one.

---

