# **VWP5 – View Models for Rendering**

## **Context**

We are implementing the **Visualization Layer** for **AXIS System A**.

The runtime and experimentation framework are already implemented up to **WP17**.
The visualization layer is being built incrementally according to the roadmap.

The previous visualization work packages established:

* **VWP1**: replay data contract validation and repository-backed artifact access
* **VWP2**: replay snapshot model and deterministic snapshot resolution
* **VWP3**: immutable centralized `ViewerState` and pure state transitions
* **VWP4**: deterministic playback and navigation controller

At this point, the visualization system already has:

* validated replayable episode access
* deterministic replay coordinate resolution
* centralized viewer state
* canonical navigation and playback progression

What is still missing is the layer that transforms replay state into **renderable, UI-friendly structures**.

The Visualization Architecture explicitly requires a strict separation between:

* replay logic
* state management
* rendering

It also states that rendering components must behave as **pure functions of the current ViewerState** and that UI components must not carry business logic or hidden semantic state. 

VWP5 must therefore introduce a **View Model Layer** that sits between replay/state logic and the future PySide6 UI.

---

## **Objective**

Implement **VWP5 – View Models for Rendering**.

The goal of this package is to create a correct, explicit, and testable projection layer that:

1. maps replay state into renderable structures
2. provides stable, UI-oriented models for grid, agent, and summary information
3. keeps rendering concerns separate from replay/state logic
4. prevents semantic logic from leaking into widgets
5. remains fully deterministic and read-only

This package must provide the minimal but architecturally correct foundation required for later implementation of:

* the main visualization window
* grid rendering
* agent rendering
* dashboard/status displays
* detail panels and contextual inspection

---

## **Core Design Principle**

> Widgets must render data, not interpret replay logic.

This means:

* replay semantics stay below
* rendering semantics are expressed through view models
* widgets consume view models and display them
* widgets must not reconstruct state meaning from raw snapshots

---

## **Scope**

Implement only the following.

---

### **1. View Model Projection Layer**

Introduce a dedicated projection layer that transforms:

```text
ReplayEpisode + ViewerState + SnapshotResolver
    ↓
ReplaySnapshot
    ↓
Render View Models
```

This layer must be the **only place** where snapshot data is translated into UI-oriented structures.

A reasonable design would be something like:

```python
class ViewModelBuilder:
    def build(self, state: ViewerState) -> ViewerFrameViewModel: ...
```

or:

```python
class RenderViewModelFactory:
    def build_frame(...): ...
```

Equivalent naming is acceptable, but the role must be clear:

* consumes replay-facing models
* produces render-facing models
* remains UI-framework-independent

Important:

* do not put this mapping into widgets
* do not make ViewerState responsible for producing view models
* do not mix repository or playback logic into this layer

---

### **2. Frame-Level View Model**

Introduce a top-level view model representing the current renderable frame.

A good baseline structure would be:

```python
class ViewerFrameViewModel:
    coordinate: ReplayCoordinate
    phase: ReplayPhase

    grid: GridViewModel
    agent: AgentViewModel
    status: StatusBarViewModel
    selection: SelectionViewModel
```

Equivalent naming is acceptable.

This top-level model must be:

* immutable
* self-contained for one frame
* derived deterministically from current replay state

Important:

* this is not the same as `ReplaySnapshot`
* it is a UI-oriented projection of snapshot + state context
* it may include display-oriented grouping, but not hidden business logic

---

### **3. Grid View Model**

Provide a render-ready representation of the world grid.

At minimum, this must include:

* grid dimensions
* per-cell structures
* obstacle/traversability information
* resource value per cell
* agent occupancy indicator
* selected-cell indicator

A reasonable baseline shape might include:

```python
class GridCellViewModel:
    x: int
    y: int
    resource_value: float
    is_obstacle: bool
    is_agent_here: bool
    is_selected: bool
```

and:

```python
class GridViewModel:
    width: int
    height: int
    cells: list[GridCellViewModel]
```

Equivalent structures are acceptable.

Important:

* preserve explicit coordinates
* do not encode visual styling decisions yet
* do not compute layout geometry yet
* keep it descriptive and render-oriented

The grid view model must provide enough information for a widget to render the world without understanding replay internals.

---

### **4. Agent View Model**

Provide a render-ready representation of the current agent state.

At minimum include:

* current position
* current energy
* currently selected status
* optional additional baseline fields if directly available and stable

A reasonable baseline shape might include:

```python
class AgentViewModel:
    x: int
    y: int
    energy: float
    is_selected: bool
```

Optional additional fields may include:

* hunger, if this is already directly available in the snapshot or trivially derived and clearly defined
* current action context if useful for later detail display

Important:

* do not invent agent semantics
* do not infer hidden internal state
* only expose what is either present or explicitly, deterministically derived

---

### **5. Status / Dashboard View Model**

Provide a compact view model for always-visible state information.

The Visualization Architecture explicitly calls for always-visible critical signals such as:

* current step
* current phase
* playback state
* energy 

At minimum include:

* step index
* phase
* playback mode
* current energy
* total number of steps
* whether current coordinate is initial/final

A reasonable shape might include:

```python
class StatusBarViewModel:
    step_index: int
    total_steps: int
    phase: ReplayPhase
    playback_mode: PlaybackMode
    energy: float
    at_start: bool
    at_end: bool
```

Important:

* keep this model display-oriented
* do not embed timing logic
* do not mix selection details here

---

### **6. Selection View Model**

Provide an explicit model of current selection context.

The Visualization Architecture defines selection as part of ViewerState and distinguishes between:

* CELL
* AGENT
* NONE 

At minimum represent:

* selection type
* selected cell coordinates, if any
* whether the agent is selected

A reasonable baseline shape might include:

```python
class SelectionViewModel:
    selected_entity_type: SelectionType
    selected_cell: Optional[GridCoordinate]
    agent_selected: bool
```

If you choose a different representation, keep it explicit and unambiguous.

Important:

* do not couple this to detail-panel rendering yet
* do not make selection implicit through widget focus or hover state

---

### **7. Action / Trace Context View Model (Optional but Recommended)**

If the snapshot model from VWP2 already exposes stable action context, you may introduce a small additional view model for later replay inspection.

Examples:

* selected action at current frame
* previous action
* action probabilities or trace summary, if explicitly available and stable

However, keep this limited.

This package is not yet the full detail-panel system.
Only include this if it is already directly supported by the snapshot contract and can be expressed cleanly without speculative abstraction.

If this would make the design messy, leave it for VWP7.

---

### **8. Builder Purity and Determinism**

The view model builder must behave as a pure projection:

```text
(ViewerState, SnapshotResolver, ReplayEpisode) → View Models
```

Given the same inputs:

* identical view models must be produced
* no internal mutable state may influence results
* no caching is required yet

Important:

* no repository access here
* no UI callbacks here
* no playback progression here
* no hidden memoization that changes semantics

---

### **9. Explicit Selection Projection Rules**

Selection must be projected consistently into view models.

At minimum define and implement rules such as:

#### **Cell selection**

If `ViewerState.selected_cell` is set:

* exactly that cell is marked `is_selected=True`
* no other cell is selected
* agent selection must be false if mutual exclusion already exists in ViewerState

#### **Agent selection**

If the agent is selected:

* `AgentViewModel.is_selected=True`
* no grid cell is marked as selected unless your architecture explicitly allows simultaneous highlighting, which it currently should not

Do not leave these rules ambiguous.

---

### **10. No Visual Styling Policy Yet**

This package must stop before actual widget styling decisions.

Do not encode:

* colors
* brushes
* pixel geometry
* fonts
* Qt-specific painter objects
* layout rectangles

This layer must remain framework-neutral and semantic.

A widget may later decide how to display:

* a selected cell
* an obstacle
* a low-energy state

But this package should only expose the underlying render-relevant facts.

---

## **Out of Scope**

Do **not** implement any of the following in VWP5:

* PySide6 widgets
* window layout
* painting code
* timers
* keyboard controls
* mouse handlers
* detail panel widgets
* config inspection widgets
* debug overlays
* CLI commands
* repository access
* replay navigation
* ViewerState transitions
* playback speed handling
* actual selection interactions
* visual themes or styling
* snapshot caching or prefetching

Do not let VWP5 drift into UI implementation.

---

## **Architectural Constraints**

The implementation must follow these rules.

---

### **1. View models are projections, not sources of truth**

The source of truth remains:

* replay artifacts
* ViewerState
* SnapshotResolver

View models are derived, read-only structures.

---

### **2. Widgets must stay dumb**

Widgets should later be able to render the output of this package without understanding:

* replay phase semantics
* artifact structure
* repository layout
* navigation rules

That logic must not leak upward.

---

### **3. No hidden state**

The builder must not keep internal semantic state between builds.

Stateless builder design is strongly preferred.

---

### **4. Framework neutrality is mandatory**

This package must be fully testable without PySide6 initialized.

No Qt objects or toolkit-specific types may appear in view model definitions.

---

### **5. Minimal derived state only**

Derived fields are allowed only if they are:

* deterministic
* cheap
* clearly defined
* useful for rendering

Do not start building analytics into this layer.

This aligns directly with the architecture’s rule of allowing only minimal, explicit derived state. 

---

## **Expected File Structure**

A reasonable baseline extension could look like this:

```text
src/axis_system_a/visualization/
    view_models.py
    view_model_builder.py
```

Equivalent organization is acceptable, provided concerns remain clear:

* immutable view model types
* deterministic builder/projection logic
* no UI dependencies

Do not fragment excessively.

---

## **Testing Requirements**

Also create pytest tests for VWP5.

At minimum include the following.

---

### **A. Frame view model construction tests**

Validate:

* a valid `ViewerFrameViewModel` is built from a valid `ViewerState`
* frame coordinate and phase match current state
* top-level grouping is correct and complete

---

### **B. Grid projection tests**

Validate:

* all cells are projected
* grid dimensions are correct
* resource values are projected correctly
* obstacle/traversability semantics are preserved
* agent occupancy is marked on exactly one cell when appropriate
* selected cell projection is correct

---

### **C. Agent projection tests**

Validate:

* agent position is correct
* energy is correct
* agent selection is projected correctly
* no hidden fields are invented

---

### **D. Status/dashboard projection tests**

Validate:

* current step index is correct
* total steps are correct
* phase is correct
* playback mode is correct
* energy is correct
* initial/final boundary flags are correct

---

### **E. Selection projection tests**

Validate:

* no selection → explicit “none” state
* selected cell → correct selection model and cell projection
* selected agent → correct selection model and agent projection
* selection mutual exclusion is respected

---

### **F. Determinism and purity tests**

Validate:

* same input state produces identical view models
* builder does not mutate input state
* builder does not mutate snapshots or episode data
* builder is UI-independent

---

### **G. Framework-independence tests**

At minimum ensure the module can be imported and used in a pure unit-test environment without Qt initialization.

---

## **Implementation Style**

* Python 3.11
* explicit typing
* immutable Pydantic models or equivalent
* stateless builder preferred
* no GUI framework dependencies
* no styling concerns
* deterministic projection only
* no hidden caching
* no permissive fallback behavior

Be skeptical of convenience fields that smell like future UI logic. Only include them if they are clearly justified now.

---

## **Expected Deliverable**

1. immutable render-facing view model types
2. deterministic view model builder/projection layer
3. grid, agent, status, and selection view models
4. explicit projection rules for selection and occupancy
5. framework-neutral implementation
6. pytest coverage for projection correctness, purity, and determinism

---

## **Important Final Constraint**

VWP5 must feel like:

> a **semantic rendering projection layer**, not a widget toolkit layer and not a second replay model.
