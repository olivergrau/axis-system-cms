# **WP3 Implementation Brief – Agent State and Baseline Memory**

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

WP1 established:

* configuration structures
* core enums
* foundational runtime types
* minimal validation

WP2 established:

* world representation
* cell structure
* agent position in world state
* observation construction as the only permitted perception channel

WP3 must now implement the **agent-side runtime state** more concretely, with particular focus on:

* internal energy representation
* memory state representation
* bounded memory behavior
* memory update rules at the data-structure level

This package must remain fully aligned with the baseline architecture and must not drift into policy, drive, or transition behavior. In particular, memory must exist as a real subsystem, but it must remain **behaviorally inactive** in the baseline system.

---

## **Objective**

Implement **WP3 – Agent State and Baseline Memory**.

The goal of this package is to create a correct, explicit, and testable representation of the internal agent-side runtime state required by later packages.

This includes:

1. **Agent energy state**
2. **Memory state**
3. **Memory entry structure**
4. **Bounded memory behavior**
5. **Minimal validation and update behavior for agent-side state**

This package must provide the minimal but architecturally correct foundation required for later implementation of:

* hunger drive computation
* transition-driven memory update integration
* episode execution
* deterministic runtime validation

The package must be implemented in a way that supports:

* explicit state handling
* serialization
* deterministic behavior
* strict separation between passive state representation and later runtime logic

---

## **Scope**

Implement only the following.

### **1. Agent State**

Implement a concrete `AgentState` model representing the internal state of the baseline agent.

At minimum it must contain:

* `energy: float`
* `memory_state: MemoryState`

Important architectural rule:

* `AgentState` must **not** contain:

  * absolute world position
  * world references
  * observation
  * policy state
  * drive state as persisted internal runtime state unless explicitly required later

The agent state must remain minimal and explicit. This is a strict architectural constraint.

---

### **2. Energy Representation**

Implement energy as a bounded scalar quantity.

Requirements:

* continuous numeric representation
* bounded by:

  * lower bound `0`
  * upper bound `max_energy`
* explicit validation of valid initialization
* easy to inspect and serialize

At WP3 stage, do **not** implement full transition-based energy update logic yet.
However, the structure should already support later deterministic update through the transition engine.

You may provide small helper validation or clipping utilities if they remain clearly scoped to agent-state integrity.

---

### **3. Memory Entry Structure**

Implement a minimal memory entry structure suitable for the baseline system.

The architecture and pre-spec define memory as a bounded sequence of observation-derived records.
A memory entry should therefore be based only on perception-derived information.

At minimum, each entry should contain:

* timestep index
* observation

A simple structure such as:

* `MemoryEntry(timestep, observation)`

is sufficient and preferred.

Important constraint:

A memory entry must **not** contain:

* absolute position
* world state references
* hidden environment variables
* inferred semantics
* future prediction
* action outcomes unless explicitly required later

Memory must remain a passive perceptual record in the baseline system.

---

### **4. Memory State**

Implement a concrete `MemoryState` model representing the baseline episodic memory.

Requirements:

* stores an ordered bounded sequence of memory entries
* preserves chronological ordering
* supports empty initialization
* supports later deterministic append/update

The memory must behave conceptually as a **FIFO bounded buffer**.

At minimum, the state should support:

* access to entries
* size / capacity
* empty initialization

The internal representation should remain simple and explicit.

---

### **5. Memory Update Function**

Implement a minimal deterministic update function for memory state.

The update rule should reflect the baseline requirement:

* append the new observation-derived entry
* if capacity is exceeded, remove the oldest entry

This can be implemented as:

* a function
* a method on `MemoryState`
* or a small helper module

Choose the clearest option.

Important constraint:

This update mechanism must remain **purely structural** at WP3 stage.

It must not:

* consult policy
* consult drives
* alter observations
* infer structure
* mutate world or agent state outside memory state itself

The actual integration of memory update into the transition order belongs later. WP3 should only implement the memory-state-level behavior itself.

---

### **6. Minimal Validation**

Implement validation rules such as:

* `0 <= energy <= max_energy`
* `memory_capacity > 0`
* all memory entries contain valid observations
* memory size never exceeds configured capacity after update
* timestep is non-negative

Validation must fail explicitly.

---

## **Out of Scope**

Do **not** implement any of the following in WP3:

* hunger drive computation
* policy logic
* action masking
* transition engine
* full energy transition rules
* movement or consumption effects
* episode loop
* logging
* experiment system
* visualization
* memory retrieval logic for decision-making
* memory-based scoring or planning
* semantic memory
* learned memory compression
* hidden state beyond energy and memory

Do not let memory become behaviorally active in this package.

---

## **Architectural Constraints**

The implementation must follow these rules.

### **1. Memory is real, but inactive**

Memory must exist as part of runtime state, but must not influence behavior in the baseline system.

### **2. No world knowledge inside agent state**

Do not place:

* absolute position
* world handles
* grid references
  inside `AgentState` or `MemoryState`.

### **3. Observation-derived memory only**

Memory entries must be based only on observations and minimal structural metadata such as timestep.

### **4. Explicitness over cleverness**

Use readable, strongly typed structures.
Do not introduce retrieval engines, indexing systems, embedding layers, or generic memory frameworks.

### **5. Serialization readiness**

All models must remain easy to serialize to JSON-compatible structures later.

### **6. No premature transition logic**

WP3 may support energy validation and memory update behavior, but it must not implement transition orchestration or physics-like system behavior.

---

## **Expected File Structure**

Extend the existing `src/` package from WP1 and WP2 in a simple and readable way.

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
    __init__.py
```

If the existing `types.py` already contains some of these structures from WP1, it is acceptable to refactor carefully, but do not fragment the codebase excessively.

---

## **Testing Requirements**

Also create pytest tests for WP3.

At minimum include tests for the following.

### **Agent state tests**

* valid `AgentState` can be created
* invalid energy initialization fails
* `AgentState` contains only allowed internal state fields

### **Memory entry tests**

* valid memory entry can be created from timestep + observation
* invalid timestep fails
* invalid observation shape or structure fails if validation exists

### **Memory state tests**

* memory initializes empty
* memory capacity is respected
* append/update preserves chronological ordering
* append/update drops oldest entry when full
* memory size never exceeds capacity

### **Separation tests**

* memory entries do not contain world position
* agent state does not store absolute position
* memory update does not depend on policy or world internals

Use small, explicit observations in tests.
Do not rely on random generation.

---

## **Implementation Style**

* Python 3.11
* clear type hints
* strongly typed, readable models
* concise docstrings where useful
* no unnecessary comments
* no speculative abstractions

If Pydantic is used, use it where it improves validation clarity.
Do not force Pydantic everywhere if normal dataclasses or explicit classes are clearer.

---

## **Expected Deliverable**

Return:

1. the proposed file structure
2. the implementation for WP3
3. the corresponding pytest tests
4. a short explanation of any design decision that is not obvious

---

## **Important Final Constraint**

This package is still a **foundation package**.

That means:

* it must remain small
* it must remain correct
* it must preserve architectural boundaries
* it must not sneak in drive behavior, policy behavior, or transition orchestration

A modest but architecturally correct implementation is preferred over a broader implementation that makes memory or energy handling more sophisticated than the baseline requires.

---

# **Optional shorter Plan Mode variant**

If you want a shorter first-pass prompt for Copilot Plan Mode before asking for implementation:

```text
Implement WP3 for AXIS System A.

First read and understand the existing specifications, especially:
- System A Baseline
- The Sensor Model
- Engineering Pre-Specification
- Implementation Architecture and Delivery Plan

Then focus only on WP3: Agent State and Baseline Memory.

Scope:
- implement AgentState
- implement MemoryEntry and MemoryState
- implement bounded FIFO-like memory behavior
- implement energy validation
- implement minimal memory update behavior
- add pytest tests

Constraints:
- memory must be real runtime state but behaviorally inactive
- AgentState must not contain world position
- memory entries must be observation-derived only
- no hunger logic, no policy logic, no transition engine, no episode loop
- no premature abstractions
- keep file structure simple under src/

Do not generate code yet.
First produce a plan with:
1. understanding summary
2. WP3 scope interpretation
3. proposed file structure
4. agent/memory model design
5. implementation order
6. testing plan
7. scope boundaries
8. open questions or risks
```

---

