# **WP9 Implementation Brief – Test Support and Fixtures**

---

## **Context**

We are implementing **System A (Baseline)** of the AXIS project.

At this stage:

* Core system behavior is implemented (WP1–WP7)
* Result and trace structures are standardized (WP8)
* A large number of tests (~300) already exist and pass

However, the current test suite:

* is likely fragmented
* may contain duplication
* may mix concerns
* may be difficult to navigate and extend

WP9 must now transform the test suite into a:

* structured
* reusable
* human-readable
* extensible testing system

---

## **Objective**

Implement **WP9 – Test Support and Fixtures**.

The goal of this package is to:

1. **consolidate and restructure existing tests**
2. **introduce reusable fixtures and builders**
3. **establish a clear test taxonomy**
4. **improve readability and maintainability**
5. **ensure alignment with WP8 result structures**

This package must not change system behavior.

It must only improve:

* how tests are written
* how tests are organized
* how test inputs are constructed
* how results are asserted

---

## **Core Design Principle**

> Tests must describe behavior, not construct infrastructure.

A test should read like:

```text
Given a world with food above
And low agent energy
→ the agent prefers UP or CONSUME
```

Not like:

```text
construct 12 objects manually, wire them, then assert something
```

---

## **Scope**

---

### **1. Test Taxonomy and Structure**

Restructure the test suite into clear categories.

Recommended structure:

```text
tests/
    unit/
        test_world.py
        test_observation.py
        test_drive.py
        test_policy.py
        test_transition.py

    integration/
        test_step_pipeline.py
        test_episode_execution.py

    behavioral/
        test_behavior_regimes.py

    fixtures/
        world_fixtures.py
        agent_fixtures.py
        observation_fixtures.py
        scenario_fixtures.py

    builders/
        world_builder.py
        agent_state_builder.py
        memory_builder.py

    utils/
        assertions.py
        trace_assertions.py
```

Important:

* no flat test directory
* no mixing of unit and integration tests

---

### **2. World Fixtures**

Provide reusable, minimal world configurations.

Examples:

* empty world
* single food at center
* food in one direction
* obstacle blocking movement

Fixtures must:

* be small
* be deterministic
* avoid randomness

Example:

```python
def world_with_food_up():
    ...
```

---

### **3. Agent State Fixtures**

Provide reusable agent states.

Examples:

* full energy
* low energy
* zero energy
* mid-range energy

Must include:

* energy
* empty or minimal memory

---

### **4. Builder Utilities**

Introduce simple builders to reduce boilerplate.

#### **WorldBuilder**

```python
WorldBuilder()
    .with_size(5, 5)
    .with_agent_at(2, 2)
    .with_food(2, 1, value=1.0)
    .with_obstacle(1, 2)
    .build()
```

#### **AgentStateBuilder**

```python
AgentStateBuilder()
    .with_energy(0.2)
    .with_empty_memory()
    .build()
```

#### **MemoryBuilder**

Only if needed. Keep minimal.

---

### **5. Scenario Fixtures (High-Level)**

Provide reusable **behavioral scenarios**.

Examples:

* food directly above agent
* no food anywhere
* obstacle blocking food

These must be:

* readable
* composable
* used in integration and behavioral tests

---

### **6. Assertion Helpers**

Introduce reusable assertion utilities.

Examples:

#### **Action Assertions**

```python
assert_action_selected(step_result, Action.UP)
```

#### **Trace Assertions**

```python
assert_valid_decision_trace(trace)
assert_valid_transition_trace(trace)
```

#### **Energy Assertions**

```python
assert_energy_decreased(step_result)
```

Important:

* avoid repeating assertion logic across tests
* keep helpers small and explicit

---

### **7. Alignment with WP8 Structures**

All tests must:

* use `StepResult`, `EpisodeResult`
* validate against `DecisionResult` and `TransitionTrace`

Remove:

* tests that inspect internal implementation details unnecessarily
* tests that bypass result structures

---

### **8. Refactoring Existing Tests**

Systematically:

* remove duplication
* replace manual setup with fixtures/builders
* simplify test bodies
* rename tests for clarity

Bad:

```text
test_case_17_variant_b
```

Good:

```text
test_agent_moves_towards_higher_resource
```

---

### **9. Behavioral Tests (Important Layer)**

Introduce a clear behavioral test layer.

Examples:

* agent prefers direction with higher resource
* agent consumes when food is present
* agent energy decreases over time
* agent dies when energy reaches zero

These tests validate:

> system-level behavior, not implementation details

---

### **10. Determinism Tests**

Ensure:

* same seed → identical results
* different seed → variation (if stochastic mode)

These tests should use:

* EpisodeRunner
* RunResult

---

## **Out of Scope**

Do **not** implement:

* property-based testing frameworks
* fuzz testing
* performance benchmarking
* coverage tooling
* CI pipelines
* mutation testing

---

## **Architectural Constraints**

### **1. Tests must not redefine logic**

Do not:

* reimplement drive formulas
* reimplement policy logic

Tests must validate outputs, not replicate internals.

---

### **2. Fixtures must remain simple**

Avoid:

* very complex factory systems
* hidden logic in fixtures

---

### **3. Builders must remain lightweight**

No:

* DSLs
* meta-builders
* configuration engines

---

### **4. No randomness unless explicit**

All fixtures:

* deterministic by default

---

## **Expected File Structure**

```text
tests/
    unit/
    integration/
    behavioral/
    fixtures/
    builders/
    utils/
```

Keep naming consistent and explicit.

---

## **Testing Requirements (Meta)**

After refactoring:

* all existing tests still pass (if they have not been removed already)
* no reduction in coverage of core behavior
* reduced duplication
* improved readability

---

## **Implementation Style**

* pytest
* clear function names
* minimal fixtures
* no magic
* explicit data setup

---

## **Expected Deliverable**

1. restructured test directory
2. reusable fixtures
3. builder utilities
4. assertion helpers
5. refactored test suite
6. short explanation of structure and decisions

---

## **Important Final Constraint**

This package defines how humans interact with the system during development.

> If WP9 is done well, new tests become trivial to write.
> If done poorly, the system becomes hard to validate and extend.

A smaller, cleaner, more expressive test suite is preferred over a large but chaotic one.

---

