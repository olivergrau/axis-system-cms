# **VWP6 – Main Visualization Window and Static Rendering**

## **Context**

We are implementing the **Visualization Layer** for **AXIS System A**.

The runtime and experimentation framework are already implemented up to **WP17**.
The visualization layer is being built incrementally according to the roadmap.

The previous visualization work packages established:

* **VWP1**: replay data contract validation and repository-backed artifact access
* **VWP2**: replay snapshot model and deterministic snapshot resolution
* **VWP3**: immutable centralized `ViewerState` and pure state transitions
* **VWP4**: deterministic playback and navigation controller
* **VWP5**: framework-neutral render-facing view models

At this point, the visualization system already has:

* validated replayable artifact access
* deterministic snapshot resolution
* centralized state and navigation semantics
* deterministic render-facing frame models

What is still missing is the first actual **desktop UI layer**.

The Visualization Architecture explicitly positions the UI as a **local desktop application launched via CLI**, implemented with **PySide6**, and requires strict separation between:

* data loading
* replay logic
* state management
* rendering
* interaction 

VWP6 must now introduce the first concrete UI shell and static rendering components, while remaining deliberately minimal.

---

## **Objective**

Implement **VWP6 – Main Visualization Window and Static Rendering**.

The goal of this package is to create a correct, explicit, and testable desktop UI foundation that:

1. provides a PySide6 application entry layer for visualization
2. introduces a main window with a stable structural layout
3. renders the current frame statically from view models
4. displays the world grid, agent position, and always-visible status information
5. remains fully aligned with the lower architectural layers
6. does not yet introduce interactive control logic beyond passive display

This package must provide the minimal but architecturally correct foundation required for later implementation of:

* replay controls
* interactive inspection
* detail panels
* configuration and metadata views
* debug overlays

---

## **Core Design Principle**

> The first UI must prove architectural correctness, not visual sophistication.

This means:

* consume the existing view model layer exactly as intended
* keep widgets dumb
* keep the window layout explicit and stable
* avoid premature interaction complexity
* prefer correctness and inspectability over polish

This aligns directly with the architecture’s principle of **clarity over aesthetics** and **debuggability over convenience**. 

---

## **Scope**

Implement only the following.

---

### **1. PySide6 Application Shell**

Introduce the minimal PySide6 application layer required to host the visualization window.

At minimum, provide:

* a visualization-specific application entry helper
* creation of `QApplication`
* creation and showing of the main window
* injection of an initial `ViewerState`, `SnapshotResolver`, and `ViewModelBuilder` or already-built frame model, depending on your final composition design

Important:

* keep application bootstrap minimal
* do not embed repository loading logic inside widgets
* do not embed CLI parsing here
* do not implement asynchronous startup logic yet

A reasonable design might include something like:

```python
def launch_visualization_app(...): ...
```

or:

```python
class VisualizationApplication:
    def run(...): ...
```

Equivalent naming is acceptable.

This package is not yet the CLI integration package. It only provides the UI shell that later CLI code can call into.

---

### **2. Main Window Skeleton**

Implement a first concrete `QMainWindow`-based visualization shell.

The window must establish a stable layout that reflects the architecture’s intended structure, while keeping interaction minimal.

At minimum, the main window should contain:

* a central world/grid display area
* an always-visible status/dashboard area
* a reserved side or lower area for future contextual inspection, even if initially populated with placeholder content

A good baseline conceptual layout would be:

```text
+---------------------------------------------------------+
|                     Dashboard                           |
+----------------------+----------------+------------------+
|                      |                |                  |
|     Grid View        | Detail Panel   |   Control Panel  |
|                      |                |                  |
|                      |                |                  |
+----------------------+----------------+------------------+
```

Equivalent layout choices are acceptable, but the structure must be explicit and future-ready.

Important:

* do not build a complex docking system yet
* do not introduce multiple floating panels
* do not use auto-generated UI files
* prefer direct, explicit widget construction in Python

---

### **3. Static Grid Rendering Widget**

Introduce a dedicated widget responsible for rendering the grid world.

This widget must consume the grid-related view model data from VWP5 and render it statically.

At minimum, it must render:

* the full grid
* cell boundaries
* obstacle cells
* resource-bearing cells in a distinguishable way
* selected cell indication, if present
* agent location

The widget may use a custom `QWidget` with `paintEvent(...)`, which is the preferred baseline choice here.

Important:

* do not use `QGraphicsView` unless there is a strong reason
* do not introduce scene graphs or advanced retained-mode rendering yet
* do not introduce interactive mouse behavior yet
* do not let the widget interpret replay semantics

The widget should receive a ready-to-render `GridViewModel` and draw it. Nothing more.

---

### **4. Agent Rendering**

Render the agent on top of or within the grid representation.

At minimum:

* the agent must appear at the correct grid coordinate
* the agent must be visually distinguishable from cells
* agent selection state, if available in the view model, may be represented visually in a simple explicit way

Important:

* agent rendering must be driven entirely by `AgentViewModel`
* do not query replay state directly inside the widget
* do not compute position logic inside the painter beyond straightforward view-model-to-pixel mapping

---

### **5. Always-Visible Status Area**

Introduce a passive status/dashboard area showing critical current-frame information.

The Visualization Architecture explicitly calls for always-visible critical signals such as:

* current step
* current phase
* playback state
* energy 

At minimum display:

* step index
* total steps
* current phase
* playback mode
* current energy
* boundary information such as “at start” / “at end”, if already available in the status view model

This may be implemented with a simple `QWidget` composed of labels or a small form-style layout.

Important:

* this is not yet an interactive control bar
* do not add playback buttons yet
* do not add timing/speed widgets yet

---

### **6. Placeholder Detail / Inspection Area**

Introduce a reserved UI region for future detail views.

At this stage, it may contain:

* placeholder labels
* static text such as “Detail view not implemented yet”
* minimal display of current selection type if already convenient

The goal is not functionality yet. The goal is layout stability and forward structural readiness.

Important:

* do not implement real detail panels yet
* do not introduce config inspection yet
* do not start rendering raw traces here unless clearly trivial

---

### **7. Frame Update / Refresh Integration**

Introduce a clean mechanism by which the main window can receive a new frame model and refresh its display.

A reasonable baseline API might be:

```python
def set_frame_model(self, frame: ViewerFrameViewModel) -> None:
    ...
```

or:

```python
def render_frame(self, frame: ViewerFrameViewModel) -> None:
    ...
```

This should:

* update the grid widget
* update the status area
* update any placeholder inspection text if relevant
* trigger repaint where necessary

Important:

* do not let child widgets rebuild replay state
* do not let widgets pull data from repositories or controllers
* propagate already-built view models downward

This preserves the architecture’s state ownership rules. 

---

### **8. Static Rendering Only**

This package must remain deliberately static.

That means:

* no playback buttons
* no next/previous step buttons
* no cell click handling
* no keyboard shortcuts
* no hover logic
* no timers
* no event-driven replay progression

The only allowed dynamic behavior is:

* receiving a frame model
* refreshing the rendered display accordingly

This keeps VWP6 focused on rendering correctness.

---

### **9. Widget Responsibility Separation**

Define widget responsibilities cleanly.

A recommended baseline split would be:

* `VisualizationMainWindow`
* `GridWidget`
* `StatusPanel`
* `DetailPlaceholderPanel`

Equivalent naming is acceptable.

Responsibilities:

#### **VisualizationMainWindow**

* owns layout
* routes frame models to child widgets
* does not perform replay logic

#### **GridWidget**

* draws world + agent from view model
* no replay/state logic

#### **StatusPanel**

* displays status fields from status view model
* no control logic

#### **DetailPlaceholderPanel**

* reserves UI space for future detail content
* minimal passive display only

This is strongly aligned with the architecture’s separation of concerns. 

---

### **10. Rendering Geometry Policy**

Define a simple, explicit geometry policy for the grid.

At minimum:

* each cell must map to a fixed rectangular area
* widget resizing may scale the rendering area in a simple way
* cell positions must remain deterministic and stable

A good baseline policy is:

* compute cell width and height from widget size and grid dimensions
* draw row/column aligned rectangles
* preserve exact coordinate mapping

Important:

* do not over-engineer zooming or panning yet
* do not introduce scrolling behavior unless absolutely necessary
* do not add coordinate axes unless trivially helpful

Keep it simple and inspectable.

---

### **11. Minimal Visual Semantics**

At this stage, use only simple, explicit visual distinctions.

For example:

* obstacle cells: filled solid
* resource cells: shaded according to resource intensity
* selected cell: visible border highlight
* agent: distinct filled shape or marker

Important:

* do not build a styling/theme subsystem
* do not over-design colors or palettes
* do not add animations
* do not smooth or interpolate values

This UI is still an engineering tool, not a polished product.

---

## **Out of Scope**

Do **not** implement any of the following in VWP6:

* playback controls
* next/previous buttons
* mouse-based selection
* keyboard navigation
* detail panels with real data
* configuration inspection
* metadata inspection
* debug overlays
* CLI integration
* asynchronous loading
* repository access from widgets
* timer-driven playback
* custom playback speed
* zooming/panning
* docking frameworks
* theme system
* scene graph rendering
* multi-window support
* multi-episode browsing in the UI

Do not let VWP6 drift into interaction or orchestration.

---

## **Architectural Constraints**

The implementation must follow these rules.

---

### **1. PySide6 must remain in the UI layer only**

All imports from `PySide6` must be confined to visualization UI modules.

Do not introduce Qt dependencies into:

* replay models
* viewer state
* playback controller
* view models
* repository access

This boundary must remain strict.

---

### **2. Widgets must consume view models, not replay internals**

Widgets must not directly inspect:

* replay artifacts
* repository objects
* snapshot resolver internals
* viewer state transitions

They must render already-prepared view models only.

---

### **3. Main window must remain thin**

The main window may coordinate child widgets and frame refresh, but must not become:

* a replay controller
* a repository client
* a business-logic container

---

### **4. Rendering must be deterministic**

Given the same frame model and widget size, rendering behavior must be stable and reproducible.

---

### **5. No interaction semantics yet**

Do not smuggle in early interactivity through mouse events or hidden widget state.

This package is static by design.

---

## **Expected File Structure**

A reasonable baseline extension could look like this:

```text
src/axis_system_a/visualization/ui/
    __init__.py
    app.py
    main_window.py
    grid_widget.py
    status_panel.py
    detail_placeholder_panel.py
```

Equivalent organization is acceptable, provided concerns remain clearly separated:

* application/bootstrap
* main window composition
* grid rendering
* status display
* placeholder detail area

Do not fragment excessively.

---

## **Testing Requirements**

Also create pytest tests for VWP6.

At minimum include the following.

---

### **A. UI construction tests**

Validate:

* main window can be constructed
* child widgets are created correctly
* layout contains the expected regions
* application/bootstrap layer can initialize without runtime errors in a test environment

Use minimal smoke-style UI tests.

---

### **B. Frame propagation tests**

Validate:

* setting a frame model updates grid widget state
* status panel displays correct values
* placeholder detail area updates consistently if applicable
* repaint/update hooks are triggered appropriately

---

### **C. Grid rendering model integration tests**

Validate:

* grid widget accepts valid `GridViewModel`
* agent marker is positioned consistently from the view model
* selected cell state is consumed correctly
* no replay logic is required inside the widget

These tests may stay lightweight and structural rather than pixel-perfect.

---

### **D. UI-independence boundary tests**

Validate, at least structurally, that non-UI layers do not import Qt.

This does not need to become an elaborate meta-framework, but the architectural boundary should remain test-visible.

---

### **E. Static behavior tests**

Validate:

* no playback controls exist yet
* no interactive actions are required for successful rendering
* the window can display a valid frame model passively

---

## **Implementation Style**

* Python 3.11
* PySide6 only in UI modules
* explicit widget construction
* no `.ui` files
* simple custom painting preferred
* deterministic rendering
* thin window class
* no hidden state
* no styling subsystem
* no premature interaction complexity

Be skeptical of any design move that feels “framework-clever”. This package should be boring in a good way.

---

## **Expected Deliverable**

1. PySide6 visualization application shell
2. main window with stable structural layout
3. custom static grid rendering widget
4. always-visible status panel
5. placeholder detail area
6. frame-model-based refresh/update flow
7. smoke and structural tests for UI construction and frame propagation

---

UI Boundary Rule:

The UI layer must only consume ViewerFrameViewModel.

It must not access:
- ViewerState
- SnapshotResolver
- ReplayEpisode
- PlaybackController

Any violation of this rule is considered an architectural error.

---

## **Important Final Constraint**

VWP6 must feel like:

> a **thin, static rendering shell over the existing architecture**, not the place where replay logic migrates upward.
