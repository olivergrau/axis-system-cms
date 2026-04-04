# **WP4 Implementation Brief – Hunger Drive Module**

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

WP3 established:

* agent energy state
* memory state
* bounded baseline memory behavior

WP4 must now implement the **first active motivational component of the system**:

* the **Hunger Drive**

This drive is responsible for transforming:

* internal energy deficit
* local observation

into:

* a scalar hunger activation
* an action contribution vector over the full baseline action space

This package must remain fully aligned with the baseline architecture and must not drift into policy, transition, or reward logic. The Hunger Drive is a **local, reactive, deterministic scoring component**, not a decision-maker and not a planner.

---

## **Objective**

Implement **WP4 – Hunger Drive Module**.

The goal of this package is to create a correct, explicit, and testable implementation of the baseline hunger drive.

This includes:

1. **hunger activation computation**
2. **action contribution vector computation**
3. **support for consume weighting**
4. **support for stay suppression**
5. **strict alignment with the baseline action space and observation ordering**

This package must provide the minimal but architecturally correct foundation required for later implementation of:

* policy / decision pipeline
* action admissibility masking
* state transition effects
* episode execution

The package must be implemented in a way that supports:

* determinism
* inspectability
* explicit action ordering
* separation between drive scoring and action selection

---

## **Scope**

Implement only the following.

### **1. Hunger Activation**

Implement the baseline hunger activation as a scalar function of current energy.

The baseline definition is:

$$
d_H(t) = 1 - \frac{E_t}{E_{\max}}
$$

where:

* `E_t` is the current internal agent energy
* `E_max` is the configured maximum energy

The resulting activation must be bounded to the valid range:

$$
0 \le d_H(t) \le 1
$$

The implementation may expose this as:

* a pure function
* or part of a `HungerDrive` class

Prefer the clearest, smallest design.

Important:

* this is a **deterministic function**
* it depends only on allowed inputs
* it must not inspect world state directly
* it must not infer future consequences

---

### **2. Full Action Space Alignment**

The drive must compute contributions over the full baseline action space:

* `UP`
* `DOWN`
* `LEFT`
* `RIGHT`
* `CONSUME`
* `STAY`

The output ordering must be **stable and explicit**, because later policy logic depends on it.

If WP1 already defined a stable action enum, reuse that ordering exactly.

---

### **3. Movement Action Contributions**

Implement movement contributions using the directional local resource signals from the current observation.

For the baseline system:

$$
s_{up}(t) = d_H(t) \cdot r_{up}(t)
$$

$$
s_{down}(t) = d_H(t) \cdot r_{down}(t)
$$

$$
s_{left}(t) = d_H(t) \cdot r_{left}(t)
$$

$$
s_{right}(t) = d_H(t) \cdot r_{right}(t)
$$

These contributions preserve the local directional structure of the observation.

Important:

* the drive must use only the observation, not world internals
* do not perform admissibility masking here
* blocked movements still receive raw contributions from observation structure; masking belongs later in the policy stage

---

### **4. Consume Contribution**

Implement the contribution for `CONSUME` as:

$$
s_{consume}(t) = d_H(t) \cdot w_{consume} \cdot r_c(t)
$$

where:

* `r_c(t)` is the current-cell resource intensity from the observation
* `w_consume > 0` is the configured consume-weight parameter

Important:

* `CONSUME` remains part of the action space even when `r_c = 0`
* if `r_c = 0`, the contribution is simply zero
* do not mask or suppress `CONSUME` in this package

This is a strict baseline rule.

---

### **5. Stay Contribution**

Implement the baseline stay suppression as:

$$
s_{stay}(t) = - \lambda_{stay} \cdot d_H(t)
$$

where:

* `lambda_stay >= 0` is the configured stay-suppression parameter

This means:

* `STAY` is not given a positive attraction score
* it is explicitly suppressed as hunger increases

Important:

* do not treat `STAY` as invalid
* do not apply policy-level masking here
* this package only computes the raw drive contribution

---

### **6. Drive Output Structure**

Implement a clear output structure for the Hunger Drive.

At minimum, the drive should produce:

* hunger activation
* per-action contribution vector

A good output design might include something like:

* `activation`
* `action_contributions`

If that improves traceability, the result may also include named access to per-action values.

Prefer explicitness and readability over generic abstraction.

---

### **7. Configuration Integration**

The Hunger Drive must consume only the parameters actually needed for baseline scoring, such as:

* `max_energy`
* `consume_weight`
* `stay_suppression`

Do not inject unrelated configuration sections into the drive.

Keep configuration dependency narrow and explicit.

---

## **Out of Scope**

Do **not** implement any of the following in WP4:

* policy logic
* Softmax
* action selection
* tie-breaking
* admissibility masking
* transition engine
* movement execution
* consumption mechanics
* energy update
* episode loop
* logging
* experiment system
* visualization
* multi-drive aggregation frameworks
* alternative drives
* reward functions
* prediction of future gain
* memory-based behavior

Do not let the drive become a policy.

---

## **Architectural Constraints**

The implementation must follow these rules.

### **1. Drive is not policy**

The Hunger Drive computes motivational action contributions only.
It must not choose an action.

### **2. No world access**

The drive must not inspect world state directly.
It may only use:

* agent state
* observation
* relevant configuration parameters

### **3. No masking**

The drive must not:

* invalidate actions
* suppress blocked movement via masking
* remove actions from the action space

Masking belongs to the policy package later.

### **4. No prediction**

The drive must not:

* predict future energy gain
* estimate transition outcomes
* reason about hidden world structure

It is strictly reactive and local.

### **5. Explicit action ordering**

Contribution outputs must align exactly with the stable baseline action ordering.

### **6. No premature multi-drive framework**

You may structure the implementation so that later extension is possible, but do not build a plugin system, registry, or generic motivational framework here.

A small, explicit `HungerDrive` implementation is preferred.

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
    __init__.py
```

or:

```text
src/axis_system_a/
    ...
    drives/
        __init__.py
        hunger_drive.py
```

Only introduce a subpackage if it clearly improves readability.
Do not over-fragment the codebase at this stage.

---

## **Testing Requirements**

Also create pytest tests for WP4.

At minimum include tests for the following.

### **Hunger activation tests**

* maximal energy produces zero hunger activation
* zero energy produces maximal hunger activation
* intermediate energy produces the correct proportional activation
* activation remains within `[0,1]`

### **Movement contribution tests**

* movement contributions are computed from the correct directional observation fields
* contributions preserve action ordering
* equal neighboring resource values produce equal directional contributions
* zero neighboring resource values produce zero directional contributions

### **Consume contribution tests**

* current-cell resource contributes correctly to `CONSUME`
* `consume_weight` is applied correctly
* zero current-cell resource yields zero consume contribution

### **Stay contribution tests**

* `STAY` contribution is negative or zero
* stronger hunger produces stronger suppression
* zero hunger yields zero stay suppression

### **Structure and separation tests**

* drive output has the correct dimensionality
* action ordering matches baseline enum ordering
* drive does not require world state
* drive does not perform action masking
* drive does not mutate input state

Use explicit handcrafted observations and agent states.
Do not rely on random generation.

---

## **Implementation Style**

* Python 3.11
* clear type hints
* readable, explicit implementation
* concise docstrings where useful
* no unnecessary comments
* no speculative abstractions

If using classes, keep them small and focused.
If using dataclasses or Pydantic models for drive output, do so only where it clearly improves readability and validation.

---

## **Expected Deliverable**

Return:

1. the proposed file structure
2. the implementation for WP4
3. the corresponding pytest tests
4. a short explanation of any design decision that is not obvious

---

## **Important Final Constraint**

This package is the first **behaviorally active** package, but it is still **not** a decision package.

That means:

* it must remain small
* it must remain local and reactive
* it must preserve architectural boundaries
* it must not sneak in policy, transition, or prediction logic

A modest but architecturally correct drive implementation is preferred over a more ambitious implementation that blurs responsibilities.

---
