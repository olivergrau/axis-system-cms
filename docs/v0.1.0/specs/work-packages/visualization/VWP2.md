# **VWP2 – Replay Snapshot Model and Resolver**

---

## **1. Purpose and Scope**

### **Purpose**

Define a **deterministic, explicit, and minimal replay model** that maps validated episode data to **time-resolved snapshots**.

This work package introduces:

* the **Replay Coordinate System**
* the **Snapshot Data Model**
* the **Snapshot Resolver**

It establishes the **canonical way** to access state during replay.

---

### **Scope**

This package is responsible for:

* defining `(step_index, phase)` addressing
* constructing **immutable snapshot objects**
* resolving snapshots **strictly from persisted data**

This package must NOT:

* introduce ViewerState
* introduce playback logic
* introduce UI concepts
* recompute or infer missing data

---

## **2. Architectural Position**

VWP2 sits between:

```
VWP1 (Validated Data Access)
        ↓
VWP2 (Snapshot Resolution)   ← YOU ARE HERE
        ↓
VWP3 (Viewer State)
```

---

## **3. Core Concept: Replay Coordinate System**

Every replay state is uniquely defined by:

```
(step_index, phase)
```

Where:

```
step_index ∈ [0, N-1]
phase ∈ { BEFORE, AFTER_REGEN, AFTER_ACTION }
```

---

### **Important Constraint**

This is NOT a timeline.

It is a **2D coordinate system**:

* time dimension → `step_index`
* intra-step dimension → `phase`

No interpolation. No implicit transitions.

---

## **4. Phase Semantics**

Phases must be strictly defined and aligned with execution:

| Phase        | Meaning                    |
| ------------ | -------------------------- |
| BEFORE       | State at beginning of step |
| AFTER_REGEN  | After world regeneration   |
| AFTER_ACTION | After agent action         |

---

### **Critical Rule**

If a phase is missing in persisted data:

→ **FAIL** (no fallback, no inference)

---

## **5. Snapshot Model**

### **Purpose**

Represent a **fully materialized system state** at a specific coordinate.

---

### **Requirements**

A snapshot must:

* be **immutable**
* contain **all required state for rendering**
* be derived **only from validated replay data**
* not contain lazy or computed fields

---

### **Minimal Structure (Conceptual)**

```python
class Snapshot:
    step_index: int
    phase: Phase

    grid: GridState
    agent: AgentState

    metadata: Optional[dict]
```

---

### **Important Design Decision**

Do NOT reuse raw replay models directly.

Instead:

→ Create a **dedicated snapshot representation**

Reason:

* decouples replay schema from visualization
* stabilizes downstream layers
* prevents accidental coupling

---

## **6. Snapshot Resolver**

### **Purpose**

Provide a single entry point:

```
resolve(episode, step_index, phase) → Snapshot
```

---

### **Responsibilities**

* validate coordinate bounds
* retrieve correct step
* retrieve correct phase
* construct immutable snapshot
* propagate validated data only

---

### **Non-Responsibilities**

The resolver must NOT:

* modify data
* cache state (for now)
* interpolate or merge phases
* infer missing values

---

## **7. Boundary Conditions**

### **Step Bounds**

```
if step_index < 0 or step_index >= total_steps:
    → raise StepOutOfBoundsError
```

---

### **Phase Availability**

```
if phase not in step:
    → raise PhaseNotAvailableError
```

---

### **Episode Integrity**

Assume VWP1 already validated structure.

Still:

* do not silently trust data
* fail explicitly if something is inconsistent

---

## **8. API Design**

### **Primary Interface**

```python
class SnapshotResolver:

    def resolve(
        self,
        episode: ReplayEpisode,
        step_index: int,
        phase: Phase
    ) -> Snapshot:
        ...
```

---

### **Optional Extensions (NOT required now)**

* batch resolution
* prefetching
* caching

Do NOT implement these yet.

---

## **9. Error Model**

Extend VWP1 error hierarchy with:

* `StepOutOfBoundsError`
* `PhaseNotAvailableError`

Errors must:

* be explicit
* include coordinate context
* not be swallowed

---

## **10. Testing Strategy**

You must cover:

### **Happy Path**

* resolve first step, all phases
* resolve middle step
* resolve last step

---

### **Boundary Cases**

* step_index = -1
* step_index = N
* missing phase

---

### **Determinism**

* same input → identical snapshot

---

### **Immutability**

* snapshot cannot be modified

---

### **Integrity**

* snapshot reflects exactly underlying data
* no transformation drift

---

## **11. Implementation Constraints**

### **Strict Rules**

* no recomputation
* no mutation
* no caching
* no UI logic
* no ViewerState references

---

### **Design Principle**

The resolver must behave like:

> a pure projection from validated data → snapshot

---

## **12. Deliverables**

### **Source Files**

Suggested structure:

```
visualization/
  snapshot_models.py
  snapshot_resolver.py
```

---

### **Core Components**

* `Phase` enum
* `Snapshot` model (immutable)
* `SnapshotResolver`
* error extensions

---

### **Tests**

```
tests/visualization/
  test_snapshot_models.py
  test_snapshot_resolver.py
```

---

## **13. Definition of Done**

VWP2 is complete when:

* snapshot model is clearly defined and immutable
* resolver works for all valid coordinates
* all invalid inputs fail explicitly
* tests pass
* no coupling to UI or state layer exists

---

## **14. Critical Review (Important)**

This is the first place where architectural discipline matters.

Two typical failure modes:

### ❌ Hidden Logic

Resolver starts “fixing” missing data

→ must NEVER happen

---

### ❌ Leaking Execution Semantics

Resolver reimplements transition logic

→ strictly forbidden

---

If you see either during implementation, stop and correct.

---

## **Next Step**

After VWP2:

→ VWP3 will introduce **ViewerState**

That is where navigation and playback begin.

---
