# **WP5 Implementation Brief – Policy and Decision Pipeline**

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

Previous work packages:

* **WP1–WP3**: structural foundation (config, types, world, agent state, memory)
* **WP4**: Hunger Drive (motivational action contribution vector)

WP5 must now implement the **decision layer**, which transforms:

* drive output
  into
* a selected action

This must be done **strictly according to the defined policy pipeline**, without introducing additional intelligence, prediction, or planning.

---

## **Objective**

Implement **WP5 – Policy and Decision Pipeline**.

The goal of this package is to create a correct, explicit, and testable implementation of:

1. **action admissibility masking**
2. **policy logits construction**
3. **Softmax transformation**
4. **action selection (sampling or deterministic)**
5. **tie-breaking behavior**
6. **decision trace output (for debugging and later observability)**

This package is the first one that produces an **actual chosen action**, but it must remain:

* local
* reactive
* stateless (except RNG)
* strictly aligned with prior components

---

## **Scope**

Implement only the following.

---

### **1. Policy Input**

The policy must consume:

* action contribution vector from WP4
* observation (for admissibility checks)
* configuration parameters

The policy must **not** recompute drive logic.

---

### **2. Action Admissibility Mask**

Implement admissibility masking based on observation.

Movement actions must be disabled if:

* the corresponding `b_j = 0` (blocked cell)

Mapping must follow observation ordering:

* up → UP
* down → DOWN
* left → LEFT
* right → RIGHT

Rules:

* blocked actions must be **masked out**
* masked actions must not be selectable
* do not remove them from the vector, use masking

`CONSUME`:

* always admissible

`STAY`:

* always admissible

Important:
Masking happens **before Softmax**.

---

### **3. Logit Construction**

Use the drive contributions as logits.

Apply masking:

* masked actions must receive a value equivalent to **−∞** (or a very large negative number)

Do not renormalize manually.
Softmax handles normalization.

---

### **4. Softmax Transformation**

Implement Softmax with temperature parameter `β`:

$$
P(a_i) = \frac{\exp(\beta \cdot s_i)}{\sum_j \exp(\beta \cdot s_j)}
$$

Requirements:

* numerically stable implementation (subtract max trick)
* supports configurable temperature
* preserves action ordering

---

### **5. Action Selection**

Support two modes (configurable):

#### **A. Stochastic Sampling**

* sample from probability distribution
* use seeded RNG for determinism

#### **B. Deterministic Mode**

* select argmax

If multiple actions share the same maximum:

→ apply deterministic tie-breaking

---

### **6. Tie-Breaking**

Implement deterministic tie-breaking:

* fixed ordering (e.g. enum order)
* or configurable ordering

Must be:

* deterministic
* reproducible

No randomness in tie-breaking.

---

### **7. Decision Trace**

Implement a structured trace output.

This is important for:

* debugging
* later observability (WP logging)
* validation

Trace should include:

* raw contributions
* masked contributions
* logits
* probabilities
* selected action

Keep it simple but explicit.

---

## **Out of Scope**

Do **not** implement:

* transition engine
* state updates
* energy updates
* movement execution
* consumption logic
* episode loop
* logging system (only local trace object)
* multi-agent logic
* learning
* reward modeling
* planning
* lookahead
* memory usage in decision

---

## **Architectural Constraints**

### **1. Policy ≠ Drive**

Policy must not recompute or modify drive logic.

---

### **2. Policy ≠ Transition**

Policy must not:

* simulate outcomes
* predict rewards
* apply effects

---

### **3. Strict Pipeline Order**

Must follow:

1. contributions (WP4)
2. masking
3. logits
4. Softmax
5. selection

No reordering.

---

### **4. Determinism**

Given:

* same inputs
* same RNG seed

→ same action must be selected

---

### **5. No Hidden Intelligence**

No heuristics like:

* “prefer consume if available”
* “prefer higher reward actions”
* “avoid staying too long”

Everything must come from:

* drive contributions
* masking
* Softmax

---

## **Expected File Structure**

```text
src/axis_system_a/
    ...
    drives.py
    policy.py
    __init__.py
```

or:

```text
policy/
    policy.py
    softmax.py
```

Keep it simple.

---

## **Testing Requirements**

### **Masking tests**

* blocked directions are masked
* valid directions remain selectable
* consume always valid

---

### **Softmax tests**

* probabilities sum to 1
* temperature affects distribution correctly
* identical logits → uniform distribution

---

### **Selection tests**

* deterministic mode returns argmax
* stochastic mode respects probabilities
* seed produces reproducible results

---

### **Tie-breaking tests**

* equal logits → deterministic outcome
* ordering respected

---

### **End-to-end policy tests**

Given:

* observation
* agent state
* drive output

→ selected action is correct

---

### **Trace tests**

* trace contains all required fields
* values are consistent

---

## **Implementation Style**

* Python 3.11
* explicit typing
* clean separation of steps
* no over-abstraction
* no premature frameworks

---

## **Expected Deliverable**

1. file structure
2. implementation
3. pytest tests
4. short explanation of decisions

---

## **Important Final Constraint**

This is the **first decision-making component**, but:

> it must still behave like a **mechanical transformation pipeline**, not an intelligent system.

A correct but simple policy is far more valuable than a clever one.

---
