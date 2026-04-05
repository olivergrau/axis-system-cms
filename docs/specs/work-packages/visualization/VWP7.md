# **VWP7 – Interactive Inspection and Replay Controls**

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
* **VWP6**: PySide6 main window and static rendering shell

At this point, the visualization system already has:

* validated replayable episode access
* deterministic replay resolution
* centralized state and navigation semantics
* deterministic view model projection
* a working static desktop UI

What is still missing is the first real **interactive control and inspection layer**.

The Visualization Architecture explicitly requires:

* time navigation (play, pause, step, seek)
* entity selection (cell, agent)
* contextual inspection
* progressive disclosure of information
* strict separation between interaction, state management, and rendering 

VWP7 must now introduce these capabilities without breaking the established architecture.

---

## **Objective**

Implement **VWP7 – Interactive Inspection and Replay Controls**.

The goal of this package is to create a correct, explicit, and testable interaction layer that:

1. introduces replay control widgets for navigation and playback
2. enables cell and agent selection through the UI
3. updates the UI through the existing state/control/projection layers
4. replaces placeholder inspection with meaningful contextual information
5. keeps widgets thin and free of replay/business logic
6. preserves deterministic replay semantics at all times

This package must provide the minimal but architecturally correct foundation required for later implementation of:

* richer detail panels
* configuration and metadata inspection
* debug overlays
* CLI-driven launched sessions with specific start positions

---

## **Core Design Principle**

> User interaction must be modeled as explicit state transformation, not widget-local behavior.

This means:

* widgets emit interaction intent
* a top-level visualization controller or coordinator applies state transitions
* the resulting frame model is rebuilt
* widgets re-render from the new frame model

No widget may become a hidden source of truth.

---

## **Scope**

Implement only the following.

---

### **1. UI Interaction Coordinator**

Introduce a thin, explicit coordination layer between UI events and the lower-level visualization logic.

This layer should connect:

* `ViewerState`
* `PlaybackController`
* `ViewModelBuilder`
* UI widgets

A reasonable design would be something like:

```python
class VisualizationSessionController:
    def __init__(...): ...
    def current_state(self) -> ViewerState: ...
    def current_frame(self) -> ViewerFrameViewModel: ...

    def step_forward(self) -> None: ...
    def step_backward(self) -> None: ...
    def play(self) -> None: ...
    def pause(self) -> None: ...
    def stop(self) -> None: ...
    def tick(self) -> None: ...
    def set_phase(self, phase: ReplayPhase) -> None: ...
    def select_cell(self, x: int, y: int) -> None: ...
    def select_agent(self) -> None: ...
    def clear_selection(self) -> None: ...
```

Equivalent naming is acceptable.

Important:

* this is not a replacement for `PlaybackController`
* it is a UI-facing coordination shell
* it owns current `ViewerState`
* it rebuilds frame models after state changes
* it must remain thin and explicit

This is the right place for session-level orchestration that should not live in widgets.

---

### **2. Replay Control Panel**

Replace static-only status usage with a real replay control surface.

At minimum introduce controls for:

* step backward
* step forward
* play
* pause
* stop
* current phase display
* optional direct phase selection

A good baseline could be a dedicated `ReplayControlsPanel` widget containing:

* push buttons
* a phase selector (`QComboBox` or equivalent)
* optional coordinate display

Important:

* the panel emits intent only
* it must not directly manipulate replay internals
* button handlers should call into the session controller or main window coordinator layer

Do not embed playback progression rules inside the panel.

---

### **3. Timer-Driven Playback Integration**

Integrate playback progression into the UI using a timer-driven mechanism.

The Visualization Architecture explicitly requires non-blocking playback and responsiveness under continuous interaction. Playback must therefore be timer-based rather than blocking. 

At this stage:

* use a Qt timer (`QTimer`)
* on each timer event, call the existing controller/session progression logic
* refresh the frame model and UI

Important:

* timer behavior must delegate to the existing deterministic `tick(...)` semantics from VWP4
* timer must not implement replay logic itself
* no custom threads
* no asynchronous loading

A reasonable baseline behavior:

* when entering play mode, start timer
* when paused or stopped, stop timer
* when terminal state is reached, timer stops automatically

Keep playback speed simple and fixed for now.

---

### **4. Grid Selection via Mouse Interaction**

Enable cell selection through the grid widget.

At minimum:

* clicking on a valid cell selects that cell
* selected cell updates the centralized visualization state
* updated frame model propagates selection highlight and detail content

Important:

* the grid widget may translate pixel coordinates to grid coordinates
* but it must not modify ViewerState directly
* it should emit a signal or call a callback carrying the selected grid coordinate

This preserves the interaction-as-state-transformation principle.

Do not introduce drag, hover, or multi-select behavior yet.

---

### **5. Agent Selection**

Enable agent selection through the UI.

A baseline implementation may support one of these two acceptable approaches:

#### **Option A**

Clicking the cell containing the agent selects the agent if no cell-specific selection semantics take precedence.

#### **Option B**

Provide a separate UI action, for example a button in the detail or control area, that explicitly selects the agent.

Either is acceptable, but whichever choice is made must be:

* explicit
* deterministic
* documented
* consistent with the mutual exclusion rules already established in `ViewerState`

Do not leave cell-vs-agent selection ambiguous.

---

### **6. Replace Placeholder Detail Panel with Contextual Inspection**

Replace the static placeholder detail panel with a real contextual inspection panel.

The Visualization Architecture calls for contextual inspection with progressive disclosure:

* always-visible critical signals remain outside
* detailed inspection appears contextually on selection 

At minimum, the detail panel must support:

#### **A. No selection**

Display a neutral message such as:

* “No entity selected”

#### **B. Cell selected**

Display relevant cell information, such as:

* grid coordinate
* obstacle/traversability state
* resource value
* whether the agent is currently located there

#### **C. Agent selected**

Display relevant agent information, such as:

* current position
* current energy
* current phase
* optional action context if already clearly available from the frame model

Important:

* the panel must consume existing view models or selection context
* do not query replay internals directly inside the panel
* do not let the panel perform replay resolution or repository access

---

### **7. Frame Refresh Pipeline**

Introduce a stable refresh/update pipeline for interactive changes.

The expected flow should now be:

```text
UI event
  → session controller / coordinator
  → ViewerState update
  → ViewModelBuilder rebuild
  → MainWindow propagates new frame to widgets
  → widgets repaint
```

This pipeline must remain explicit and centralized.

Important:

* no widget should independently rebuild frame models
* no widget should update only “its own local interpretation”
* keep refresh behavior deterministic and full-frame-oriented for now

Do not optimize with partial updates yet unless trivially safe.

---

### **8. Main Window Integration of Interactive Components**

Extend the main window so it composes:

* replay control panel
* status panel
* grid widget
* contextual detail panel

A good baseline high-level layout might be:

```text
+--------------------------------------------------------------+
| Replay Controls                                              |
|--------------------------------------------------------------|
| Status                                                       |
|--------------------------------------------------------------|
| Grid View                      | Detail / Inspection Panel   |
+--------------------------------------------------------------+
```

Equivalent composition is acceptable, but the structure must remain clear and future-ready.

Important:

* main window routes signals/callbacks
* main window does not become replay engine logic
* keep responsibilities explicit

---

### **9. Initial Interaction Set Only**

Limit interaction to the essential baseline set.

Support only:

* play
* pause
* stop
* step forward
* step backward
* phase selection
* cell selection
* agent selection
* clear selection if needed

Do not implement:

* drag navigation
* zoom
* panning
* keyboard shortcuts
* scrubbing timeline
* hover previews
* multi-selection
* annotations

This package must stay focused.

---

### **10. UI State vs. Visualization State Boundary**

The UI may still have minor ephemeral widget state, such as:

* button pressed visual state
* Qt focus state

But it must not maintain logical replay state outside the centralized session/viewer-state flow.

In particular, no widget may own:

* current step index
* current phase
* current selected entity
* playback truth

Those belong to the visualization state/session layer only.

This is a hard architectural rule derived from the central Viewer State ownership model. 

---

### **11. Minimal Action Context Display**

If `ActionContextViewModel` from VWP5 is already stable and available, the detail panel may display a minimal subset of it, such as:

* action taken
* relevant current action label
* limited summary context

Keep this minimal.

Do not turn VWP7 into a full trace browser yet.

If this would complicate the design excessively, show only a very small stable subset or defer the rest.

---

### **12. Fixed Playback Interval**

Use a single fixed playback interval for now.

Do not implement:

* playback speed controls
* variable frame rate
* timeline scaling

A simple fixed interval is sufficient for VWP7.
The goal is correctness and architectural cleanliness, not UX sophistication.

---

## **Out of Scope**

Do **not** implement any of the following in VWP7:

* configuration inspection panels
* run metadata inspection
* experiment selection inside the UI
* debug overlays
* raw trace browser
* keyboard shortcuts
* zoom / pan
* advanced timeline/scrubber widgets
* playback speed controls
* custom themes
* multiple simultaneous episodes
* background loading
* multi-window coordination
* direct repository access from widgets
* replay caching/prefetching
* pixel-perfect rendering tests

Do not let VWP7 drift into advanced tooling or data browsing.

---

## **Architectural Constraints**

The implementation must follow these rules.

---

### **1. Interaction must flow through the centralized control path**

Widgets emit intent.
They must not directly mutate ViewerState.

---

### **2. `PlaybackController` remains the source of replay progression semantics**

The UI may trigger playback progression, but must not redefine replay advancement rules.

---

### **3. `ViewerState` remains the single source of truth**

Selections, phase, step, and playback mode must continue to live in the centralized state/session flow only.

---

### **4. Widgets must remain thin**

Widgets may:

* display
* emit interactions
* forward callbacks/signals

Widgets must not:

* resolve replay snapshots
* compute replay traversal rules
* query repositories
* build their own alternative state

---

### **5. Timer logic must remain thin**

`QTimer` is only a trigger mechanism for deterministic `tick(...)` calls.

It must not become a hidden replay state machine.

---

### **6. Contextual inspection must remain view-model-driven**

The detail panel must consume prepared data, not reconstruct domain meaning from raw snapshot internals.

---

## **Expected File Structure**

A reasonable baseline extension could look like this:

```text
src/axis_system_a/visualization/ui/
    replay_controls_panel.py
    detail_panel.py
    session_controller.py
```

and updates to:

```text
src/axis_system_a/visualization/ui/
    grid_widget.py
    main_window.py
    app.py
```

Equivalent organization is acceptable, provided concerns remain clear:

* session/control coordination
* replay controls widget
* contextual detail widget
* updated window wiring

Do not fragment excessively.

---

## **Testing Requirements**

Also create pytest tests for VWP7.

At minimum include the following.

---

### **A. Session controller tests**

Validate:

* state changes are applied correctly
* frame model is rebuilt after transitions
* play/pause/stop behavior is correct
* tick integration is deterministic
* selection updates work correctly

---

### **B. Replay controls tests**

Validate:

* buttons trigger the correct control actions
* phase selector updates correctly
* playback controls do not embed replay logic locally
* play starts timer-driven progression through the central path

Use UI-appropriate smoke/behavior tests, not pixel-perfect tests.

---

### **C. Grid click/selection tests**

Validate:

* clicking a cell emits/selects the correct grid coordinate
* selection flows through centralized state updates
* selected cell highlight updates correctly
* agent selection behavior is deterministic and documented

---

### **D. Detail panel tests**

Validate:

* no selection shows neutral content
* cell selection shows cell details
* agent selection shows agent details
* detail content updates correctly when frame changes

---

### **E. Timer/playback integration tests**

Validate:

* timer starts in play mode
* timer stops in pause/stop mode
* terminal playback stops automatically
* no wrap-around occurs

Keep these tests robust and simple.

---

### **F. Architectural boundary tests**

Validate, at least structurally, that:

* widgets do not directly import non-UI control internals unnecessarily
* replay logic remains below the UI layer
* Qt usage remains confined to UI modules

---

### **G. Static-to-interactive regression tests**

Ensure VWP6 behavior still works:

* window constructs correctly
* frame propagation still works
* passive rendering still works without interaction

---

## **Implementation Style**

* Python 3.11
* PySide6 only in UI modules
* thin widgets
* explicit signals/callbacks
* timer-based playback only through deterministic controller logic
* no hidden state duplication
* no repository access from widgets
* no clever event abstractions
* clear, boring wiring is preferred

Be skeptical of UI convenience shortcuts here. They tend to smuggle architectural violations into the codebase.

---

## **Expected Deliverable**

1. UI-facing session/control coordinator
2. replay controls panel
3. timer-driven playback integration
4. grid-based cell selection
5. deterministic agent selection path
6. real contextual detail panel
7. updated main window composition and frame refresh wiring
8. tests for control flow, interaction, selection, detail display, and timer behavior

---

## **Important Final Constraint**

VWP7 must feel like:

> a **thin interactive shell over the existing visualization architecture**, not the place where replay logic migrates into widgets.

