# **VWP3 – Viewer State Model**

---

## **1. Purpose and Scope**

### **Purpose**

Introduce a **single, centralized state model** that governs the entire visualization.

This state:

* defines **what is currently being viewed**
* controls **navigation and playback context**
* acts as the **only source of truth** for all UI components

---

### **Scope**

This package defines:

* the `ViewerState` model
* state transitions (pure functions)
* selection and playback representation

---

### **Out of Scope**

This package must NOT include:

* UI components
* rendering logic
* timers or async playback execution
* direct repository access

---

## **2. Architectural Position**

```
VWP1 → Data Access
VWP2 → Snapshot Resolver
VWP3 → Viewer State   ← YOU ARE HERE
VWP4 → Playback Controller
VWP5 → View Models
```

---

## **3. Core Design Principle**

> There must be exactly ONE authoritative state.

---

### **Implication**

* No UI component may track its own step index
* No component may store its own phase
* No duplicated state anywhere

Everything must derive from `ViewerState`.

---

## **4. ViewerState Responsibilities**

The ViewerState must fully describe:

### **4.1 Position in Replay**

```python
coordinate: ReplayCoordinate
```

This is the **only definition of “where we are”**.

---

### **4.2 Episode Context**

```python
episode: ReplayEpisode
```

The state must always be tied to a specific loaded episode.

---

### **4.3 Playback State**

```python
playback_mode: PlaybackMode
```

Where:

```python
class PlaybackMode(Enum):
    STOPPED
    PLAYING
    PAUSED
```

---

### **4.4 Selection State**

Selection is optional but must be explicit:

```python
selected_cell: Optional[GridCoordinate]
selected_agent: Optional[bool]
```

No implicit selection.

---

### **4.5 Derived Snapshot (IMPORTANT)**

The ViewerState must NOT store the snapshot directly.

Instead:

```python
snapshot = resolver.resolve(episode, coordinate)
```

---

### **Critical Rule**

ViewerState stores:

* references
* coordinates

NOT:

* computed snapshots
* cached values

---

## **5. Immutability Model**

ViewerState must be:

* **immutable**
* updated only via **explicit transitions**

---

### **Reason**

* prevents hidden side effects
* ensures traceability
* aligns with deterministic replay philosophy

---

## **6. State Transitions**

All changes to ViewerState must happen via **pure functions**.

---

### **Examples**

#### **Move to next step**

```python
def next_step(state: ViewerState) -> ViewerState:
    ...
```

---

#### **Change phase**

```python
def set_phase(state: ViewerState, phase: ReplayPhase) -> ViewerState:
    ...
```

---

#### **Jump to coordinate**

```python
def seek(state: ViewerState, coordinate: ReplayCoordinate) -> ViewerState:
    ...
```

---

#### **Selection**

```python
def select_cell(state: ViewerState, cell: GridCoordinate) -> ViewerState:
    ...
```

---

### **Rules**

* no in-place mutation
* always return new instance
* always validate bounds

---

## **7. Boundary Handling**

All transitions must enforce:

* valid step range
* valid phase availability

Use SnapshotResolver where appropriate to validate.

---

## **8. Playback Semantics (Minimal Only)**

At this stage:

* ViewerState only **stores playback mode**
* it does NOT execute playback

That belongs to VWP4.

---

## **9. API Design**

### **ViewerState Model**

```python
class ViewerState:
    episode: ReplayEpisode
    coordinate: ReplayCoordinate
    playback_mode: PlaybackMode

    selected_cell: Optional[GridCoordinate]
    selected_agent: Optional[bool]
```

---

### **Transition Module**

```python
viewer_state_transitions.py
```

Contains all state-changing functions.

---

## **10. Invariants**

These must ALWAYS hold:

* coordinate is valid within episode
* phase exists for step
* episode is not None
* state is internally consistent

---

## **11. Testing Strategy**

### **State Construction**

* valid initial state
* invalid coordinate → fail

---

### **Transitions**

* next/previous step
* phase switching
* seek operations

---

### **Immutability**

* state cannot be modified
* transitions produce new objects

---

### **Consistency**

* resulting state always valid
* no invalid coordinates possible

---

## **12. Implementation Constraints**

### **Strict Rules**

* no snapshot caching
* no UI coupling
* no timers
* no async
* no repository calls

---

### **Important Design Decision**

Do NOT include resolver inside ViewerState.

Keep it external.

---

## **13. Deliverables**

### **Source Files**

```
visualization/
  viewer_state.py
  viewer_state_transitions.py
```

---

### **Core Components**

* `ViewerState`
* `PlaybackMode`
* transition functions

---

### **Tests**

```
tests/visualization/
  test_viewer_state.py
  test_viewer_state_transitions.py
```

---

## **14. Definition of Done**

VWP3 is complete when:

* ViewerState is immutable and complete
* all transitions are pure and validated
* no duplicate state exists anywhere
* tests fully cover transitions and invariants

---

## **15. Critical Review (Very Important)**

This layer is deceptively simple.

Typical failure modes:

---

### ❌ State Duplication

Example:

* UI stores its own step index
* ViewerState stores another

→ guaranteed bugs later

---

### ❌ Hidden Snapshot Storage

Storing snapshot inside state:

→ breaks determinism and separation

---

### ❌ Implicit Transitions

State changing without explicit function:

→ destroys traceability

---

If any of these appear, fix immediately.

---

## **Next Step**

After VWP3:

→ VWP4 introduces **actual playback behavior**

---
