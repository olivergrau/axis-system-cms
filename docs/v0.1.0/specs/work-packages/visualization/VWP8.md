# **VWP8 – CLI Integration and End-to-End Validation**

## **Context**

We are implementing the **Visualization Layer** for **AXIS System A**.

The runtime and experimentation framework are already implemented up to **WP17**, including:

* deterministic runtime execution
* run and experiment orchestration
* repository-based persistence
* resume and fault tolerance
* CLI support for experimentation workflows

The visualization layer has already established:

* **VWP1**: replay data contract validation and repository-backed artifact access
* **VWP2**: replay snapshot model and deterministic snapshot resolution
* **VWP3**: immutable centralized `ViewerState`
* **VWP4**: deterministic playback and navigation controller
* **VWP5**: framework-neutral render-facing view models
* **VWP6**: PySide6 main window and static rendering shell
* **VWP7**: interactive inspection and replay controls

At this point, the visualization system is already functionally usable as an interactive local desktop tool.

What is still missing is:

1. a proper **CLI integration boundary**
2. a deterministic way to launch the visualization from persisted experiment/run/episode artifacts
3. end-to-end validation that the full path from repository → replay access → resolver → state → view model → UI startup works correctly

The Visualization Architecture explicitly requires that the visualization be launched through the existing AXIS CLI and that the UI itself must not become responsible for discovery of experiments or file system navigation. 

VWP8 must now implement this integration layer and prove the complete system works end to end.

---

## **Objective**

Implement **VWP8 – CLI Integration and End-to-End Validation**.

The goal of this package is to create a correct, explicit, and testable operational entry layer that:

1. integrates visualization into the AXIS CLI
2. resolves persisted experiment/run/episode targets through the repository-backed visualization access layer
3. constructs an initial interactive visualization session from CLI input
4. supports deterministic startup at a specified replay position
5. validates the end-to-end integration path through automated tests
6. preserves all architectural boundaries established in previous visualization work packages

This package must provide the final baseline visualization delivery for the current roadmap.

---

## **Core Design Principle**

> The CLI selects persisted artifacts and startup parameters.
> The visualization system renders and interacts.
> These responsibilities must remain separate.

The CLI must not:

* implement replay logic
* interpret widget behavior
* rebuild state transitions
* bypass repository-backed loading

The UI must not:

* discover experiments on its own
* perform repository search on its own
* parse arbitrary filesystem paths on its own

This separation is a hard architectural requirement.

---

## **Scope**

Implement only the following.

---

### **1. CLI Entry Point for Visualization**

Integrate visualization into the existing `axis` CLI as a new command family.

A baseline command shape should be:

```bash
axis visualize --experiment-id <experiment_id>
```

and support additional selection arguments as needed.

A more explicit baseline command surface should include support for selecting:

* experiment
* run
* episode

For example:

```bash
axis visualize --experiment-id EXP_001 --run-id RUN_001 --episode-id episode_0001
```

Equivalent naming is acceptable, but the semantics must be explicit and deterministic.

Important:

* visualization command must fit into the existing AXIS CLI style
* no interactive prompts
* no ad hoc file-picker behavior
* no raw filesystem browsing in the UI

This aligns with the CLI-driven entry model defined in the Visualization Architecture.

---

### **2. Required and Optional CLI Arguments**

Implement a minimal, explicit visualization command interface.

At minimum, support:

#### **Required selection arguments**

Either:

* `--experiment-id`, `--run-id`, `--episode-id`

or an equivalent explicit selection scheme that uniquely identifies one episode.

Do not guess if identifiers are ambiguous.

#### **Optional startup arguments**

Support a minimal set of startup-position arguments such as:

* `--start-step <int>`
* `--start-phase <BEFORE|AFTER_REGEN|AFTER_ACTION>`

Optional support for:

* defaulting to step `0`
* defaulting to phase `BEFORE`

Important:

* startup defaults must be explicit and documented
* invalid startup coordinates must fail explicitly
* CLI argument parsing must not silently clamp invalid values

This keeps startup deterministic and consistent with replay semantics.

---

### **3. Repository-Backed Episode Resolution from CLI**

Implement a CLI-to-visualization startup path that resolves the requested target episode strictly through the existing replay access layer from VWP1.

Expected flow:

```text
CLI args
  → repository-backed replay access
  → load experiment / run / episode
  → replay validation already enforced by VWP1
  → initial ViewerState creation
  → view model build
  → launch interactive visualization session
```

Important:

* do not reimplement repository path logic
* do not parse episode files directly in CLI code
* do not bypass replay validation
* do not let CLI instantiate replay internals from raw JSON

This must remain aligned with the repository-first and validation-first architecture.

---

### **4. Initial Visualization Session Construction**

Define and implement the canonical startup pipeline for a visualization session launched from the CLI.

At minimum, startup must:

1. load the requested replayable episode
2. resolve the requested startup coordinate
3. create the initial `ViewerState`
4. instantiate the session/controller layer
5. build the initial frame model
6. launch the interactive visualization UI

This startup path must remain explicit and deterministic.

A reasonable design might involve a small helper such as:

```python
def create_visualization_session_from_cli_args(...) -> VisualizationSessionController: ...
```

or a similarly scoped launcher/coordinator function.

Equivalent naming is acceptable.

Important:

* keep startup orchestration thin
* do not move this into widgets
* do not let CLI code directly manipulate low-level UI objects beyond initialization

---

### **5. Startup Coordinate Semantics**

Define explicit startup semantics.

If no startup position is provided:

* default to the initial valid replay coordinate

Recommended baseline:

* `step_index = 0`
* `phase = BEFORE`

If startup position is provided:

* validate step against replay bounds
* validate phase against available replay phases
* fail explicitly on invalid step or phase

Do not:

* silently clamp invalid `--start-step`
* silently replace unavailable phases
* infer a “nearest valid position”

This must remain strict and consistent with the replay architecture’s failure transparency principle. 

---

### **6. CLI Output Philosophy**

The visualization command should remain operationally clear but lightweight.

At minimum, CLI behavior should:

* fail explicitly on invalid IDs or invalid startup coordinates
* produce clear error messages
* not dump excessive internal diagnostics by default

Examples of acceptable failure cases:

* experiment not found
* run not found
* episode not found
* replay contract violation
* invalid start step
* invalid start phase

The CLI should surface these errors cleanly and deterministically.

Do not add rich TUI formatting or interactive menus.

---

### **7. Integration with Existing CLI Structure**

This package must integrate into the existing AXIS CLI architecture rather than creating a second standalone executable.

Important:

* reuse current CLI conventions where they already exist
* keep the visualization command aligned with the broader experiment tooling
* do not duplicate unrelated experiment/run listing logic unless truly required

If the existing CLI currently uses a top-level entry point like:

```bash
axis experiments ...
axis runs ...
```

then `axis visualize ...` or a similarly consistent subcommand is the correct direction. 

---

### **8. End-to-End Validation**

Add end-to-end tests covering the full startup path from persisted artifacts to visualization session creation.

At minimum, prove:

* CLI argument parsing selects the correct episode
* repository-backed replay access is used
* initial replay coordinate is applied correctly
* session/controller initializes correctly
* initial frame model is built correctly
* UI startup path can be invoked without architectural boundary violations

Important:

* these tests do not need to verify pixel-perfect drawing
* focus on startup correctness and cross-layer wiring
* use temporary repositories and small persisted episodes

This is the first place where the entire visualization stack should be validated as one integrated path.

---

### **9. Non-Interactive Session Startup Testing**

Provide tests for visualization startup without requiring full manual GUI interaction.

At minimum, validate that:

* application/session launcher can be called from test code
* the main window is constructed
* the initial frame corresponds to the requested startup state
* interactive controls exist after launch wiring
* no startup-time repository bypassing occurs

Use lightweight smoke/integration tests.

---

### **10. Preserve Architectural Boundaries Across the Full Stack**

VWP8 is especially sensitive because it touches CLI, repository-backed loading, replay resolution, state creation, controller setup, and UI launch.

You must preserve the previously established boundaries:

* CLI selects and validates startup intent
* VWP1 handles repository-backed replay access and validation
* VWP2 resolves snapshots
* VWP3 owns viewer state structure
* VWP4 owns replay progression semantics
* VWP5 builds render-facing view models
* VWP6/VWP7 handle UI composition and interaction

Do not collapse these layers into a single startup blob.

---

## **Out of Scope**

Do **not** implement any of the following in VWP8:

* experiment browsing inside the UI
* repository explorer widgets
* file open dialogs
* rich terminal UI
* visualization of multiple episodes at once
* startup profiles or saved sessions
* keyboard shortcut systems beyond what already exists
* custom playback speed CLI options
* remote visualization
* web-based viewer
* trace export from UI
* screenshot/export features
* optimization layers like prefetching or background loading

Do not let VWP8 drift into productization features.

---

## **Architectural Constraints**

The implementation must follow these rules.

---

### **1. CLI is an entry boundary only**

The CLI may parse arguments and assemble startup inputs, but must not absorb visualization business logic.

---

### **2. Repository-backed access is mandatory**

All artifact resolution must go through the existing replay access layer from VWP1.

No direct filesystem loading in CLI or UI code is allowed.

---

### **3. Replay validation must remain in VWP1 path**

CLI startup must not weaken or bypass replay contract validation.

If persisted data is not replay-valid, startup must fail.

---

### **4. Startup semantics must be explicit**

No guessing, no silent fallback, no magical resolution of missing identifiers.

---

### **5. UI must still consume view models only**

Even in integrated startup, widgets must remain consumers of prepared frame models, not of replay internals.

---

### **6. End-to-end tests must prove the layered design still holds**

This package is not complete unless tests validate the actual integrated flow.

---

## **Expected File Structure**

A reasonable baseline extension could look like this:

```text
src/axis_system_a/
    cli.py                # or existing CLI module updated
    visualization/
        launch.py         # optional thin startup orchestration helper
```

and test additions such as:

```text
tests/visualization/
    test_visualization_cli.py
    test_visualization_e2e.py
```

Equivalent organization is acceptable, provided concerns remain clear:

* CLI command integration
* startup/session assembly
* end-to-end tests

Do not fragment excessively.

---

## **Testing Requirements**

Also create pytest tests for VWP8.

At minimum include the following.

---

### **A. CLI parsing tests**

Validate:

* visualization command parses required arguments correctly
* startup defaults are applied correctly
* invalid/missing arguments fail explicitly
* invalid phase names fail explicitly

---

### **B. Episode resolution tests**

Validate:

* CLI startup resolves the correct experiment/run/episode
* invalid IDs fail explicitly
* ambiguous or missing targets do not silently guess

---

### **C. Startup coordinate tests**

Validate:

* default start coordinate is `(0, BEFORE)`
* valid custom start step works
* valid custom start phase works
* invalid step fails explicitly
* invalid phase fails explicitly
* unavailable phase fails explicitly if relevant

---

### **D. End-to-end startup tests**

Validate the full flow:

```text
CLI args
  → repository-backed access
  → validated replay episode
  → initial ViewerState
  → session controller
  → initial frame model
  → interactive UI launch path
```

Use smoke/integration assertions rather than pixel-perfect UI checks.

---

### **E. Architectural boundary tests**

Validate, at least structurally, that:

* CLI does not parse raw episode files directly
* UI does not discover artifacts directly
* repository-backed visualization access remains the single artifact gateway
* Qt usage remains confined to UI modules

---

### **F. Regression tests**

Ensure previously implemented visualization layers still behave correctly under integrated startup.

At minimum:

* VWP6 static rendering shell still initializes
* VWP7 controls still exist after CLI-launched startup
* initial frame is consistent with startup coordinate

---

## **Implementation Style**

* Python 3.11
* minimal explicit CLI integration
* repository-first access
* no direct filesystem loading
* no rich terminal UI
* deterministic startup semantics
* thin orchestration helpers
* clear errors
* end-to-end tests over clever abstractions

Be skeptical of anything that smells like “just make startup easier by bypassing the architecture”. That is exactly how these systems decay.

---

## **Expected Deliverable**

1. visualization CLI command integrated into the existing AXIS CLI
2. repository-backed resolution of target experiment/run/episode
3. explicit startup coordinate support
4. deterministic session startup pipeline
5. end-to-end startup validation tests
6. architectural boundary tests proving no layer bypass occurs

---

## **Important Final Constraint**

VWP8 must feel like:

> a **clean operational entry layer for the existing visualization architecture**, not a shortcut that collapses repository, replay, state, and UI into one startup script.
