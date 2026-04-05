# VWP4 – Playback and Navigation Controller**

## Context**

We are implementing the **Visualization Layer** for **AXIS System A**.

The runtime and experimentation framework are already implemented up to **WP17**.
The visualization layer is being built incrementally according to the roadmap.

The previous visualization work packages established:

* **VWP1**: replay data contract validation and repository-backed artifact access
* **VWP2**: replay snapshot model and deterministic snapshot resolution
* **VWP3**: immutable centralized `ViewerState` and pure state transitions

At this point, the system already has:

* validated replayable episode access
* a deterministic replay coordinate model
* a strict centralized state object
* pure, bounded coordinate transitions

What is still missing is the logic that governs **temporal navigation and playback progression**.

The Visualization Architecture defines replay as an **indexed sequence of discrete replay positions**:

```text
(step_index, phase)
```

with explicit navigation and optional playback over those positions. Playback must remain deterministic, reversible, and free of interpolation or hidden simulation logic. 

VWP4 must now introduce a dedicated **Playback and Navigation Controller** layer.

This package must remain strictly below the UI and strictly above raw ViewerState transitions.

---

## Objective**

Implement **VWP4 – Playback and Navigation Controller**.

The goal of this package is to create a correct, explicit, and testable control layer that:

1. provides deterministic navigation across replay coordinates
2. defines canonical stepping behavior across steps and phases
3. governs playback progression independently of UI widgets
4. exposes a clean controller API for later UI integration
5. preserves all replay invariants and architectural boundaries

This package must provide the minimal but architecturally correct foundation required for later implementation of:

* replay controls in the desktop UI
* timer-based playback integration
* phase-aware navigation
* seek/jump interactions from the interface layer

---

## Core Design Principle**

> Playback is not simulation. Playback is controlled advancement through a deterministic replay coordinate space.

The controller must therefore:

* operate only on validated replay state
* use explicit state transitions
* never compute future state outside replay coordinates
* never invent missing intermediate states

---

## Scope**

Implement only the following.

---

### 1. Replay Position Advancement Policy**

Introduce a canonical policy for how replay advances through time.

The replay model is two-dimensional:

* `step_index`
* `phase`

The controller must define how “forward” and “backward” movement works across these coordinates.

At minimum, support:

* advance forward by one replay unit
* advance backward by one replay unit

A replay unit must be based on the actual supported phase model.

For the baseline visualization, the canonical phase order is:

```text
BEFORE → AFTER_REGEN → AFTER_ACTION
```

within each step. 

Therefore, forward advancement should conceptually behave like:

```text
(step i, BEFORE)
    → (step i, AFTER_REGEN)
    → (step i, AFTER_ACTION)
    → (step i+1, BEFORE)
```

And backward navigation should reverse that order.

Important:

* do not skip phases implicitly
* do not jump from one step to the next without respecting phase order
* do not interpolate
* do not recompute anything

If a required phase is unavailable for a step, fail explicitly rather than silently degrading playback behavior.

---

### 2. Navigation Controller Abstraction**

Implement a dedicated controller abstraction for replay navigation.

A reasonable design would be something like:

```python
class PlaybackController:
    def step_forward(self, state: ViewerState) -> ViewerState: ...
    def step_backward(self, state: ViewerState) -> ViewerState: ...
    def seek_to_step(self, state: ViewerState, step_index: int) -> ViewerState: ...
    def seek_to_coordinate(self, state: ViewerState, coordinate: ReplayCoordinate) -> ViewerState: ...
    def set_phase(self, state: ViewerState, phase: ReplayPhase) -> ViewerState: ...
```

Equivalent naming is acceptable, but the separation must be clear:

* ViewerState remains passive and immutable
* transition helpers remain low-level
* controller defines canonical replay navigation semantics

Important:

* do not move navigation policy into UI widgets
* do not let the UI decide phase traversal rules
* do not duplicate raw transition logic unnecessarily

The controller should orchestrate existing ViewerState transition primitives, not replace them.

---

### 3. Boundary Behavior**

Define explicit behavior at replay boundaries.

The replay architecture requires clear start and end boundaries and explicitly forbids wrap-around. Playback must stop at the end, and navigation must remain clamped or explicit depending on the command semantics. 

At minimum, define and implement behavior for:

#### A. Forward boundary**

When the current coordinate is the final valid replay position, `step_forward` must not advance beyond it.

Acceptable baseline behavior:

* return the unchanged state
* keep playback semantics consistent for later UI integration

#### B. Backward boundary**

When the current coordinate is the first valid replay position, `step_backward` must not move before it.

Acceptable baseline behavior:

* return the unchanged state

#### C. Explicit seek**

Explicit seek operations such as `seek_to_step` or `seek_to_coordinate` must fail if the target is invalid.

This should remain aligned with the stricter semantics already established in VWP3.

Important:

* no wrap-around
* no “snap to nearest valid phase” guessing unless explicitly defined
* no hidden repairs

---

### 4. Playback Progression Model**

Implement a minimal playback progression model that is UI-independent.

At this stage, the controller must support the logical notion of:

* play
* pause
* stop
* advance one playback tick

However, this package must not implement real timers or asynchronous event loops yet.

Instead, introduce a controller-level progression method such as:

```python
def tick(self, state: ViewerState) -> ViewerState:
    ...
```

Semantics:

* if playback mode is `PLAYING`, advance to the next replay position
* if playback mode is `PAUSED` or `STOPPED`, do not advance
* if already at final replay position, remain there and stop advancing

Optional but recommended:

* at terminal replay position, `tick(...)` may set playback mode to `PAUSED` or `STOPPED`, but whichever choice is made must be explicit and consistent

Important:

* `tick(...)` is not a timer
* `tick(...)` is a deterministic state transformation
* later UI code will call it from a timer or event loop

This is exactly the kind of non-blocking, timer-driven playback architecture the visualization document points toward, while keeping logic outside the UI layer. 

---

### 5. Phase-Aware Navigation Helpers**

Provide explicit helpers for navigating within or across phases.

At minimum, support:

* next phase within replay order
* previous phase within replay order
* direct phase selection when valid

These helpers should remain aligned with the canonical baseline phase order.

Important:

* do not let different parts of the system define their own local phase ordering
* define phase ordering once in the controller or a closely related helper
* use the same ordering everywhere

This is critical because phase ordering is part of replay semantics, not just UI presentation.

---

### 6. Initial and Terminal Replay Position Helpers**

Provide helpers to derive canonical boundaries for an episode.

At minimum:

* `get_initial_coordinate(episode) -> ReplayCoordinate`
* `get_final_coordinate(episode) -> ReplayCoordinate`

The replay architecture defines clear minimum and maximum replay positions. These helpers should centralize that logic rather than scattering it later across UI code. 

Important:

* initial position should correspond to the earliest valid replay position
* final position should correspond to the latest valid replay position
* final phase must be computed from the actual supported replay structure, not assumed blindly if validation model already encodes availability

Given the baseline architecture, the conceptual expectation is:

* initial = `(0, BEFORE)`
* final = `(last_step, AFTER_ACTION)`

But the implementation should still be consistent with validated episode semantics, not magical assumptions.

---

### 7. Controller Independence from UI Framework**

The playback/navigation controller must remain completely independent of PySide6 or any other UI framework.

Do not introduce:

* QWidget references
* Qt timers
* signals/slots
* event loop logic
* rendering callbacks

The controller is a pure control layer.
Later UI components will call into it.

This is a hard architectural rule derived from the strict separation of concerns in the Visualization Architecture. 

---

### 8. Read-Only State Semantics**

The controller must not mutate replay artifacts or cached snapshots.

It may only:

* consume `ViewerState`
* produce new `ViewerState`

It must not:

* modify `ReplayEpisode`
* modify repository-backed objects
* store hidden playback cursors
* embed mutable internal state unless there is a compelling need, which there should not be at this stage

A stateless controller design is strongly preferred.

---

## Out of Scope**

Do **not** implement any of the following in VWP4:

* PySide6 widgets
* visual replay controls
* keyboard shortcuts
* actual timers or async loops
* dashboard rendering
* cell rendering
* selection rendering
* detail panels
* view models
* config inspection panels
* CLI visualization entry points
* snapshot caching
* prefetching
* performance optimizations
* custom playback speeds
* scrubbing UI
* interpolation
* multi-episode switching in UI

Do not let VWP4 drift into UI implementation.

---

## Architectural Constraints**

The implementation must follow these rules.

---

### 1. ViewerState remains the single source of truth**

The controller may transform ViewerState, but must not create parallel control state elsewhere.

No duplicate replay position tracking is allowed.

---

### 2. Controller defines navigation semantics**

Replay traversal policy belongs here, not in widgets and not in raw transition helpers.

This is the layer where canonical forward/backward progression must live.

---

### 3. Playback remains discrete**

No interpolation, smoothing, or derived intermediate states are allowed. Replay is step-and-phase indexed only. 

---

### 4. No hidden automation**

The controller must not try to “fix” missing phase data or infer replay structure from neighboring states.

If replay structure is invalid for the required operation, fail explicitly.

---

### 5. UI independence is mandatory**

This package must be fully unit-testable without any GUI framework initialized.

---

## Expected File Structure**

A reasonable baseline extension could look like this:

```text
src/axis_system_a/visualization/
    playback_controller.py
    playback_navigation.py
```

Equivalent organization is acceptable, provided concerns remain clear:

* controller logic
* phase ordering / coordinate helpers
* no UI dependencies

Do not fragment excessively.

---

## Testing Requirements**

Also create pytest tests for VWP4.

At minimum include the following.

---

### A. Forward navigation tests**

Validate:

* `step_forward` advances through phases in correct order
* advancing from `AFTER_ACTION` moves to next step’s `BEFORE`
* advancing at final replay position returns unchanged state

---

### B. Backward navigation tests**

Validate:

* `step_backward` reverses phase order correctly
* moving backward from `BEFORE` moves to previous step’s `AFTER_ACTION`
* moving backward at initial replay position returns unchanged state

---

### C. Seek tests**

Validate:

* `seek_to_step` moves to explicit step with a clearly defined resulting phase
* `seek_to_coordinate` works for valid targets
* invalid coordinates fail explicitly

Important:
If `seek_to_step` does not include an explicit phase argument, define and document the default phase semantics clearly.
A good baseline choice is:

* seek to `BEFORE` of the requested step

But do not leave this ambiguous.

---

### D. Tick / playback progression tests**

Validate:

* `tick(...)` advances only in `PLAYING` mode
* `tick(...)` does nothing in `PAUSED`
* `tick(...)` does nothing in `STOPPED`
* repeated ticks eventually reach final replay position
* terminal playback behavior is explicit and stable

---

### E. Boundary tests**

Validate:

* no forward overflow
* no backward underflow
* no wrap-around
* explicit errors for invalid seek operations

---

### F. Determinism and purity tests**

Validate:

* same input state → same output state
* controller operations do not mutate input state
* returned state is new where appropriate
* operations are fully deterministic

---

### G. UI-independence tests**

At minimum ensure the controller can be imported and used in a pure unit-test environment without any GUI initialization.

---

## Implementation Style**

* Python 3.11
* explicit typing
* pure state transformations
* stateless controller preferred
* no GUI dependencies
* no hidden caching
* explicit boundary semantics
* canonical phase ordering defined once
* no permissive fallback behavior

Be skeptical of “helpful” shortcuts here. They usually become bugs later.

---

## Expected Deliverable**

1. dedicated playback/navigation controller layer
2. canonical replay progression policy across steps and phases
3. deterministic forward/backward navigation
4. explicit seek helpers and replay boundary helpers
5. UI-independent tick/progression mechanism
6. unit tests for traversal, boundaries, determinism, and purity

---

## Important Final Constraint**

VWP4 must feel like:

> a **deterministic replay control layer**, not a widget helper and not a mini state machine hidden inside the UI.
