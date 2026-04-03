# **WP8 Implementation Brief – Result and Trace Structures**

---

## **Context**

We are implementing **System A (Baseline)** of the AXIS project.

This system is a **deterministic, mechanistic agent-environment simulation framework** composed of:

* explicit world state (WP2)
* explicit agent state and memory (WP3)
* local observation model (WP2)
* hunger-driven action scoring (WP4)
* policy-based action selection (WP5)
* deterministic transition execution (WP6)
* episode execution loop (WP7)

At this point, the system already produces:

* intermediate traces (policy, transition)
* step-level outputs (implicit or partial)
* episode execution behavior

However, these outputs are not yet:

* formally standardized
* consistently structured
* fully serializable
* aligned across all components

---

## **Objective**

Implement **WP8 – Result and Trace Structures**.

The goal of this package is to define and implement a **consistent, explicit, and fully serializable runtime output model** for the entire system.

This includes:

1. **DecisionTrace** – output of the policy pipeline
2. **TransitionTrace** – output of the transition engine
3. **StepResult** – unified result of a single step
4. **EpisodeResult** – ordered collection of steps
5. **RunResult** – optional container for multiple episodes

This package must:

* consolidate all existing trace-like structures
* enforce strict structural relationships
* provide stable data contracts for:

  * testing (WP9)
  * logging (WP10)
  * analysis (future WPs)

---

## **Core Design Principle**

> The system must produce **structured truth**, not logs.

All runtime behavior must be captured in **explicit result objects**, not inferred later.

---

## **Scope**

Implement only the following.

---

### **1. DecisionTrace**

Represents the full output of the **policy pipeline (WP5)**.

It must include:

* `action_contributions` (from drive)
* `masked_contributions`
* `logits`
* `probabilities`
* `selected_action`
* `temperature`
* `selection_mode` (stochastic / deterministic)

Important constraints:

* must preserve **stable action ordering**
* must be fully serializable
* must not include world or agent references

---

### **2. TransitionTrace**

Represents the full output of the **transition engine (WP6)**.

It must include:

* `previous_state_snapshot` (minimal, not full object graph)
* `applied_action`
* `world_update_effects` (e.g. regeneration summary, optional)
* `agent_effects`:

  * energy change
* `resulting_state_snapshot`
* `termination_flag`
* `termination_reason` (if applicable)

Important constraints:

* must reflect **actual applied effects**, not predictions
* must follow transition phase ordering
* must not contain live references to mutable objects

---

### **3. StepResult**

Represents a **single execution step**.

It must unify:

* perception
* decision
* transition outcome

At minimum include:

* `timestep`
* `observation` (clearly defined as pre-step or post-step, must be consistent)
* `decision_trace: DecisionTrace`
* `transition_trace: TransitionTrace`
* `selected_action`
* `energy_after_step`
* `terminated` (bool)
* `energy_before_step`


Important constraints:

* must be **self-contained**
* must be usable independently in tests
* must not depend on external runtime context

---

### **4. EpisodeResult**

Represents a **complete episode execution**.

It must include:

* ordered list of `StepResult`
* `total_steps`
* `termination_reason`
* `final_state_snapshot` (minimal, serializable)

Optional but recommended:

* summary statistics:

  * average energy
  * min / max energy
  * number of consume actions

Important constraints:

* steps must be in strict chronological order
* must be fully serializable
* must not contain live references

---

## **Structural Relationships (Strict Rules)**

The following hierarchy must be enforced:

```text
RunResult (this comes later, a multiple episode runner is not implemented yet)
    └── EpisodeResult[]
            └── StepResult[]
                    ├── DecisionTrace
                    └── TransitionTrace
```

Constraints:

* every `StepResult` must contain exactly:

  * one `DecisionTrace`
  * one `TransitionTrace`
* no cross-references between steps
* no back-references to parent objects
* no circular structures

---

## **Serialization Requirements**

All result structures must:

* be convertible to:

  * `dict`
  * JSON-compatible representation
* avoid:

  * non-serializable objects
  * function references
  * class instances outside defined models

Provide minimal helper:

```python
to_dict()
```

Do not implement file writing yet.

---

## **Integration Requirements**

### **1. Policy (WP5)**

* must return `DecisionTrace`
* must not return raw primitives only

---

### **2. Transition Engine (WP6)**

* must return `TransitionTrace`
* must not hide internal effects

---

### **3. Episode Runner (WP7)**

* must construct `StepResult`
* must assemble `EpisodeResult`
* must not duplicate trace logic

---

## **Out of Scope**

Do **not** implement:

* logging system (WP10)
* file persistence
* metrics aggregation frameworks
* visualization
* dashboards
* experiment tracking systems
* performance profiling
* parallel execution support

---

## **Architectural Constraints**

### **1. Results are passive**

Result objects must:

* contain data only
* not execute logic
* not mutate system state

---

### **2. No duplication of logic**

Result structures must not:

* recompute values
* infer missing data
* derive behavior

They only capture outputs from existing components.

---

### **3. Deterministic structure**

Given identical execution:

* structure and values must be identical

---

### **4. Minimal but complete**

Avoid:

* bloated structures
* speculative fields

But ensure:

* no essential runtime information is missing

---

## **Expected File Structure**

```text
src/axis_system_a/
    ...
    results.py
    traces.py
    __init__.py
```

or (if preferred):

```text
results/
    __init__.py
    decision_trace.py
    transition_trace.py
    step_result.py
    episode_result.py
    run_result.py
```

Keep structure simple and readable.

---

## **Testing Requirements**

### **DecisionTrace tests**

* contains all required fields
* probabilities sum to 1
* selected action is consistent

---

### **TransitionTrace tests**

* reflects applied action
* energy changes are correct
* termination flags are correct

---

### **StepResult tests**

* contains both traces
* action consistency:

  * `selected_action == decision_trace.selected_action`
* energy_after matches transition result

---

### **EpisodeResult tests**

* step ordering is correct
* total_steps matches length
* termination reason is correct

---

### **Serialization tests**

* all result objects can be converted to dict
* JSON serialization succeeds
* no non-serializable fields

---

### **Integration tests**

* WP5 → DecisionTrace → StepResult works
* WP6 → TransitionTrace → StepResult works
* WP7 → EpisodeResult assembly works

---

## **Implementation Style**

* Python 3.11
* dataclasses or Pydantic (only if helpful)
* explicit typing
* no hidden magic
* no meta-programming
* no frameworks

---

## **Expected Deliverable**

1. file structure
2. implementation of all result/trace classes
3. integration into WP5–WP7
4. pytest test suite
5. short explanation of design decisions

---

## **Important Final Constraint**

This package defines the **data contract of the system**.

> If WP8 is unclear or inconsistent, all future work (testing, logging, analysis) will degrade.

A small, explicit, and strictly structured implementation is strongly preferred over a flexible but ambiguous one.

---

