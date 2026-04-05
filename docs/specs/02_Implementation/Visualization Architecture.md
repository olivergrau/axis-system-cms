# AXIS System A – Replay Visualization Architecture (Draft)

## Metadata

* Project: AXIS – Complex Mechanistic Systems Experiment
* Author: Oliver Grau
* Type: Architecture Document
* Status: Draft v0.1
* Scope: Replay-based visualization architecture for persisted AXIS System A experiment artifacts

---

## 1. Purpose and Scope

### 1.1 Purpose
The purpose of the Visualization System is to provide a **deterministic, inspectable, and replayable interface** for analyzing the behavior of **AXIS System A (Baseline)** during episode execution.

The visualization is not a simulation environment. It is a **pure replay and inspection tool** operating on persisted execution artifacts.

It enables:

* Step-wise reconstruction of agent–environment interaction
* Inspection of internal agent state (e.g. energy, hunger)
* Inspection of world state (grid, resources, regeneration effects)
* Traceability of decision-making across time
* Debugging and validation of system behavior against specification

The system is designed as an **engineering tool**, not a user-facing product.

---

### 1.2 Scope
The Visualization System covers:

#### A. Episode Replay

* Deterministic replay of persisted episodes
* Navigation across:

  * Experiments
  * Runs
  * Episodes
  * Steps within an episode

#### B. State Inspection

* World state (grid, resources, obstacles)
* Agent state (energy, internal variables)
* Step-level transitions (before / after phases)

#### C. Interaction

* Time navigation (play, pause, step, seek)
* Selection of entities:

  * Grid cells
  * Agent
* Contextual inspection via detail panel

#### D. Monitoring Information

* Episode-level metrics
* Current step information
* Always-visible critical signals (e.g. energy)

#### E. Configuration Access

* Inspection of the configuration used for the run
* Presented in a separate, non-intrusive view

---

### 1.3 Out of Scope
The Visualization System explicitly does **not** include:

* Any form of simulation or environment execution
* Modification of agent or world state
* Training, optimization, or learning logic
* Real-time environment interaction
* Multi-agent support (reserved for future extensions)

---

### 1.4 Design Goals
The system is guided by the following principles:

#### Determinism
All visualized states must directly correspond to persisted artifacts.
No derived or inferred state is allowed unless explicitly defined.

#### Traceability
Every visual state must be traceable to a specific:

* Step index
* Transition phase
* Persisted data structure

#### Clarity over Aesthetics
The visualization prioritizes:

* correctness
* inspectability
  over visual polish.

#### Modularity
The system must be decomposable into:

* data loading
* state management
* rendering
* interaction

#### Reproducibility
Given the same artifacts, the visualization must behave identically.

---

### 1.5 Execution Model
The Visualization System operates as:

> **An offline, local desktop application launched via CLI**

It consumes:

* persisted experiment data
* run results
* episode traces

and reconstructs system behavior without any dependency on the execution pipeline.

---

## 2. Architectural Position in the Overall System

### 2.1 System Context
The Visualization System is part of the **AXIS System A engineering toolchain** and is positioned strictly **downstream of execution and persistence**.

High-level flow:

```
[ Configuration ]
        ↓
[ Experiment Execution ]
        ↓
[ Persistence Layer ]
        ↓
[ Visualization System ]
```

---

### 2.2 Separation of Concerns
The system enforces a strict separation between:

#### Execution Layer
Responsible for:

* running experiments
* generating episodes
* producing step traces

#### Persistence Layer
Responsible for:

* storing:

  * experiment configs
  * run summaries
  * episode traces

#### Visualization Layer
Responsible for:

* loading persisted artifacts
* reconstructing state over time
* rendering and interaction

---

### 2.3 No Feedback Loop
The Visualization System is:

> **read-only**

It does not:

* influence execution
* modify stored data
* trigger new experiments

This guarantees:

* reproducibility
* isolation
* safety for debugging

---

### 2.4 Integration via CLI
The visualization is integrated into the existing **axis CLI tool**.

Example (conceptual):

```bash
axis visualize --experiment-id EXP_001
```

Optional parameters:

```bash
--run-id
--episode-id
--start-step
--config-view
```

The CLI is responsible for:

* resolving paths
* selecting artifacts
* initializing the visualization process

---

### 2.5 Data Dependency Model
The Visualization System depends on:

#### Required

* Experiment configuration
* Run results
* Episode traces (step-level data)

#### Optional

* aggregated summaries
* debug traces (if available)

All dependencies are:

> **immutable inputs**

---

### 2.6 Architectural Role
Within the AXIS project, the Visualization System fulfills three critical roles:

#### 1. Debugging Tool

* inspect unexpected behavior
* trace decision inconsistencies

#### 2. Validation Instrument

* verify that implementation matches specification
* validate worked examples against execution

#### 3. Analysis Interface

* observe emergent behavior over time
* compare runs and configurations

---

### 2.7 Technology Positioning
The system is implemented as a:

> **Python-based desktop application using PySide6**

Rationale:

* native UI capabilities
* structured component model
* event-driven interaction
* compatibility with WSL + Ubuntu environments

---

### 2.8 Non-Functional Constraints

* Must run locally without external dependencies
* Must operate on large episode traces efficiently
* Must not block UI during playback or loading
* Must remain responsive under continuous interaction


---

## 3. Design Principles

### 3.1 Deterministic Replay as First-Class Concept
The visualization is fundamentally a **replay system**, not a simulation.

All displayed states must be derived exclusively from persisted data:

* No recomputation of transitions
* No inferred world state
* No hidden logic outside recorded traces

Each visual frame corresponds exactly to:

> *(episode_id, step_index, transition_phase)*

This ensures:

* reproducibility
* debuggability
* consistency with execution artifacts

---

### 3.2 Explicit State Ownership
The system must maintain a **single, explicit Viewer State** as the source of truth.

No UI component is allowed to maintain its own implicit state that affects behavior.

All interactive elements must:

* read from the central state
* emit events that update the central state

This prevents:

* desynchronization between components
* hidden coupling
* inconsistent playback behavior

---

### 3.3 Strict Separation of Concerns
The system must be decomposed into clearly separated responsibilities:

#### A. Data Layer

* loading persisted artifacts
* providing structured access to traces

#### B. Replay Logic

* mapping (step_index, phase) → state snapshot
* navigation through time

#### C. State Management

* maintaining current selection, playback state, position

#### D. Rendering Layer

* visual representation only
* no business logic

#### E. Interaction Layer

* translating user input into state updates

No layer may bypass another.

---

### 3.4 Stateless Rendering
All rendering components must be:

> **pure functions of the current Viewer State**

This implies:

* no caching of semantic state inside widgets
* no incremental mutation logic
* full redraw based on current state

Rendering may cache **visual primitives** (e.g. brushes), but not logical state.

---

### 3.5 Temporal Consistency
Time navigation must be:

* discrete
* index-based
* reversible

Supported operations:

* step forward
* step backward
* jump to index
* continuous playback

There must be no ambiguity about:

* current step
* current phase

Playback must never skip or interpolate states.

---

### 3.6 Phase-Aware Visualization
Each step may consist of multiple conceptual phases (e.g. regeneration, action).

The system must explicitly model:

> **transition_phase ∈ { BEFORE, AFTER_REGEN, AFTER_ACTION }**

The visualization must:

* always reflect the selected phase
* allow switching between phases if required

This avoids mixing:

* cause (regeneration)
* effect (agent action)

---

### 3.7 Minimal Derived State
Derived values are allowed only if:

* they are deterministic
* they are cheap to compute
* they are clearly defined

Example:

* “cell consumed count up to current step”

Derived state must:

* depend only on persisted data and current position
* never introduce ambiguity

---

### 3.8 Interaction as State Transformation
All user interactions must be modeled as:

> **pure transformations of Viewer State**

Examples:

* Play → `is_playing = True`
* Click Cell → `selected_entity = CELL`
* Seek → `current_step_index = N`

No interaction may:

* directly manipulate UI components
* bypass the state model

---

### 3.9 Non-Blocking Execution
The UI must remain responsive under all conditions.

This requires:

* asynchronous or timer-based playback
* non-blocking data loading
* avoidance of long-running operations in UI thread

Heavy computations (if any) must be:

* precomputed
* or executed outside the main thread

---

### 3.10 Progressive Disclosure
Information must be structured hierarchically:

#### Always Visible:

* current step
* energy
* playback state

#### Contextual:

* cell details (on selection)
* agent details (on selection)

#### On Demand:

* configuration
* full trace data

This prevents:

* UI overload
* cognitive clutter

---

### 3.11 Debuggability over Convenience
The system is an engineering tool.

Therefore:

* correctness is preferred over visual smoothness
* explicitness is preferred over automation
* transparency is preferred over abstraction

Examples:

* show exact values instead of smoothed representations
* expose raw config instead of summarized views

---

### 3.12 Extensibility without Premature Abstraction
The system must allow future extensions such as:

* multi-agent visualization
* additional drives
* extended state variables

However:

* no generic plugin system at this stage
* no speculative abstractions

Extensions should be enabled through:

* clear interfaces
* modular components

---

### 3.13 CLI-Driven Entry Point
The visualization must always be launched via CLI.

This ensures:

* reproducibility
* integration with experiment workflow
* scriptability

The UI is not responsible for:

* discovery of experiments
* file system navigation

---

### 3.14 Failure Transparency
If data is missing or inconsistent:

* the system must fail explicitly
* errors must be visible and traceable

No silent fallback behavior.

---

## 4. Replay Data Contract

### 4.1 Purpose
The Replay Data Contract defines the **structure and semantics of persisted execution artifacts** required by the Visualization System.

Its purpose is to ensure that:

* episode replay is deterministic
* state reconstruction is unambiguous
* visualization logic remains decoupled from execution logic

The contract acts as:

> **the sole interface between the Persistence Layer and the Visualization System**

---

### 4.2 Contract Philosophy
The Replay Data Contract follows a **data-first, implementation-aligned approach**:

* It is **derived from actual persisted artifacts**, not abstract schema design
* It reflects **real execution output**, not theoretical structures
* It evolves alongside the execution system

This implies:

* The contract is **descriptive**, not prescriptive
* The Visualization System must tolerate **forward-compatible extensions**
* Strict validation is preferred over silent assumptions

---

### 4.3 Sources of Truth
The contract is defined through two complementary sources:

#### A. Formal Specification (This Document)
Provides:

* semantic meaning of fields
* required vs optional elements
* interpretation rules

#### B. Artifact Inspection (Ground Truth)
The definitive structure is given by:

> persisted result files (e.g. episode traces)

These can be inspected programmatically, for example via automated analysis tools.

This enables:

* schema discovery
* validation against real data
* adaptation to changes without breaking the system

---

### 4.4 Core Artifact Hierarchy
The Visualization System operates on the following hierarchy:

```
Experiment
 └── Run
      └── Episode
           └── Steps[]
```

Each level provides context:

* **Experiment** → global configuration space
* **Run** → specific parameterization
* **Episode** → single execution instance
* **Step** → atomic unit of replay

---

### 4.5 Episode Structure
An episode is the **primary unit of replay**.

It must contain:

* metadata (episode_id, run_id, etc.)
* ordered sequence of steps
* optional summary information

Conceptual structure:

```json
{
  "episode_id": "...",
  "run_id": "...",
  "steps": [ ... ],
  "summary": { ... }
}
```

---

### 4.6 Step Structure
A step represents a **single transition cycle** of the agent–environment system.

Each step must be:

* **fully self-contained**
* **ordered**
* **index-addressable**

Minimum conceptual structure:

```json
{
  "step_index": 0,
  "phases": {
    "before": { ... },
    "after_regen": { ... },
    "after_action": { ... }
  }
}
```

---

### 4.7 Phase Semantics
Each step may include multiple phases:

#### BEFORE

* state at the beginning of the step
* reflects previous step outcome

#### AFTER_REGEN

* state after world regeneration
* before agent action

#### AFTER_ACTION

* final state after agent action
* input to next step

The Visualization System must treat phases as:

> **distinct, explicitly selectable snapshots**

---

### 4.8 State Components
Each phase snapshot must contain sufficient information to reconstruct:

#### A. World State

* grid representation
* resource values per cell
* obstacle indicators (if applicable)

#### B. Agent State

* position
* energy
* internal variables (e.g. hunger)

#### C. Optional Trace Data

* action taken
* decision scores / probabilities
* intermediate values

---

### 4.9 Minimal Required Fields
For the Visualization System to function, the following must be present:

* ordered steps
* at least one valid phase per step
* world state (grid-level information)
* agent state (position + energy)

If any of these are missing:

> visualization must fail explicitly

---

### 4.10 Derived Metrics
The Visualization System may compute derived values such as:

* number of times a cell has been consumed up to current step
* cumulative resource usage
* simple counters

These must:

* be computed **on demand**
* depend only on past steps up to current index
* never modify persisted data

---

### 4.11 Ordering Guarantees
Steps must satisfy:

* strict monotonic ordering by `step_index`
* no gaps or duplicates

If violated:

* the Visualization System must reject the episode

---

### 4.12 Immutability
All replay data is treated as:

> **immutable**

The Visualization System must:

* never modify loaded artifacts
* never persist derived data back into source files

---

### 4.13 Forward Compatibility
The contract must allow:

* additional fields
* extended trace data
* new state variables

The Visualization System must:

* ignore unknown fields
* avoid hard assumptions about structure beyond required fields

---

### 4.14 Validation Strategy
Upon loading an episode, the system must perform:

#### Structural Validation

* required keys exist
* correct hierarchy

#### Semantic Validation

* valid step ordering
* consistent dimensions (e.g. grid size)

#### Failure Handling

* fail fast
* provide explicit error messages

---

### 4.15 Practical Contract Discovery
In practice, the contract can be:

> **directly inferred from existing result files**

Recommended workflow:

1. Load a representative episode file
2. Inspect structure programmatically
3. Validate assumptions against multiple runs
4. align visualization logic accordingly

This allows:

* rapid iteration
* alignment with real system behavior
* reduced risk of spec drift

---

### 4.16 Contract Stability Expectations
The contract is expected to:

* stabilize after initial implementation
* evolve only through controlled changes

Changes must be:

* backward compatible whenever possible
* reflected in both:

  * execution system
  * visualization system

---

## 5. Supported Replay Model

### 5.1 Purpose
The Supported Replay Model defines how persisted episode data is:

* interpreted
* navigated
* exposed to the Visualization System

It specifies the **temporal and structural access model** used to reconstruct system behavior during replay.

---

### 5.2 Replay as Indexed State Sequence
At its core, replay is modeled as a **discrete, index-based sequence of states**:

> A replayable episode is a finite sequence of steps, each containing phase-specific snapshots.

Formally:

```
Episode = [Step_0, Step_1, ..., Step_N]
```

Each step is addressable via:

```
(step_index, phase)
```

---

### 5.3 Replay Coordinate System
The visualization operates on a **two-dimensional coordinate system**:

#### 1. Step Index

* integer index into the episode sequence
* range: `[0, N]`

#### 2. Transition Phase

* discrete phase within a step

```
phase ∈ { BEFORE, AFTER_REGEN, AFTER_ACTION }
```

Together:

> **Replay Position = (step_index, phase)**

This coordinate uniquely identifies a visualizable state.

---

### 5.4 Snapshot Resolution
Given a replay position:

```
(step_index, phase)
```

the system resolves a **single, deterministic snapshot**:

```
Snapshot = resolve(episode, step_index, phase)
```

The snapshot must contain:

* world state
* agent state
* optional trace data

No interpolation or reconstruction is allowed.

---

### 5.5 Navigation Model
The replay system supports the following navigation operations:

#### Step Navigation

* next step
* previous step

#### Phase Navigation

* cycle through phases within a step
* direct phase selection

#### Direct Access

* jump to arbitrary step index
* jump to specific phase

All navigation must:

* be deterministic
* never skip states implicitly

---

### 5.6 Playback Model
Playback is defined as:

> **sequential advancement of replay position over time**

#### Playback Behavior

* advances step index at fixed intervals
* optionally respects phase transitions

#### Modes

* step-only playback (default)
* optional phase-aware playback

#### Control

* play
* pause
* resume
* stop

Playback must:

* never alter underlying data
* be interruptible at any time

---

### 5.7 Replay Boundaries
The system must define clear boundaries:

* minimum: `(0, BEFORE)`
* maximum: `(N, AFTER_ACTION)`

Behavior at boundaries:

* no wrap-around
* playback stops at end
* navigation clamps to valid range

---

### 5.8 Consistency Guarantees
The replay model guarantees:

#### Determinism
Same input → same sequence of snapshots

#### Referential Transparency
Resolving the same `(step_index, phase)` always yields identical state

#### No Hidden Transitions
All visible changes must correspond to explicit steps and phases

---

### 5.9 Derived Timeline Metrics
The replay model supports derived metrics over time, such as:

* cumulative cell consumption count
* agent energy trajectory
* action frequency

These are:

* computed relative to current step index
* strictly based on past data

---

### 5.10 Selection Model
The replay system supports selection of entities:

#### Entity Types

* CELL
* AGENT
* NONE

Selections are:

* independent of replay position
* updated via user interaction

Selection does not modify replay state.

---

### 5.11 Replay State Independence
The replay model is independent of:

* rendering
* UI layout
* visualization framework

It is a **pure logical model** that can be:

* tested independently
* reused across interfaces

---

### 5.12 Error Handling
Invalid replay positions must be handled explicitly:

* out-of-bounds step index → error or clamp
* missing phase → explicit failure

The system must not:

* silently skip invalid states
* substitute missing data

---

### 5.13 Performance Considerations
The replay model assumes:

* episodes may contain large numbers of steps
* navigation must remain responsive

Recommended strategies:

* index-based access
* lazy loading (if needed)
* caching of recent snapshots

---

### 5.14 Minimal Replay Interface
Conceptually, the replay system exposes:

```python
class ReplayController:
    def get_snapshot(step_index: int, phase: Phase) -> Snapshot
    def next_step()
    def prev_step()
    def set_step(index: int)
    def set_phase(phase: Phase)
```

This interface must be:

* side-effect controlled
* consistent with Viewer State

---

### 5.15 Relationship to Viewer State
The replay model is driven by:

> **ViewerState.current_step_index**
> **ViewerState.current_phase**

The ReplayController acts as:

* a resolver
* a navigator

but not as the source of truth.

---

### 5.16 Non-Simulation Guarantee
The replay system must not:

* execute transition logic
* recompute agent behavior
* simulate world dynamics

It only:

> **replays recorded transitions**

---

## 6. Technology Choice

### 6.1 Purpose
This section defines the **technology stack** used to implement the Visualization System and provides the rationale for each choice.

The goal is not to select the most feature-rich tools, but to ensure:

* stability
* maintainability
* compatibility with the AXIS development environment
* effective implementation using LLM-assisted workflows

---

### 6.2 Primary Technology Stack
The Visualization System is implemented using:

#### Programming Language

* **Python (≥ 3.10)**

#### UI Framework

* **PySide6 (Qt for Python)**

#### Execution Model

* Local desktop application
* CLI-triggered entry point

---

### 6.3 Rationale for Python
Python is selected due to:

* alignment with the existing AXIS codebase
* direct compatibility with persisted artifacts (JSON, Python structures)
* strong ecosystem for data handling
* seamless integration with CLI tooling

Additionally:

* minimizes context switching between execution and visualization
* enables rapid iteration and inspection

---

### 6.4 Rationale for PySide6
PySide6 is chosen as the UI framework based on the following considerations:

#### A. Structured UI Model

* clear separation between widgets, layouts, and events
* supports modular component design

#### B. Rich Native UI Capabilities

* built-in widgets (buttons, sliders, dialogs, tables)
* layout management
* event-driven architecture

#### C. Custom Rendering Support

* QPainter enables efficient custom drawing
* suitable for grid-based visualization

#### D. Cross-Platform Compatibility

* works reliably on:

  * Linux
  * Windows
  * WSL environments

#### E. Deterministic Event Handling

* explicit signal/slot mechanism
* predictable UI updates

---

### 6.5 Rejected Alternatives

#### A. pygame

Rejected due to:

* lack of structured UI components
* manual handling of all interactions
* poor support for complex layouts (dashboard, panels)

While suitable for simple visualizations, it does not scale to:

* multi-panel interfaces
* interactive inspection workflows

---

#### B. Web-Based Frameworks (e.g. React, Dash)

Rejected due to:

* increased architectural complexity
* requirement for backend/frontend separation
* dependency on browser environment

Additionally:

* introduces unnecessary overhead for a local engineering tool
* complicates CLI-based integration

---

#### C. Jupyter-Based Visualization
Rejected due to:

* limited interactivity for complex UI
* poor support for continuous playback
* lack of structured application state

---

### 6.6 Rendering Approach
The visualization uses:

> **Custom rendering via PySide6 QWidget + QPainter**

Specifically:

* grid rendered as a custom widget
* agent overlay rendered within the same canvas
* color mapping applied per cell

This allows:

* full control over visualization
* efficient redraws
* precise click detection

---

### 6.7 Event and Interaction Model
The system uses:

> **Qt’s signal/slot mechanism**

Interaction flow:

```
User Input → UI Event → State Update → Re-render
```

No direct coupling between:

* UI elements
* business logic

All interactions must propagate through:

* ViewerState updates

---

### 6.8 Concurrency Model
The system avoids complex concurrency.

Primary mechanisms:

* Qt event loop (main thread)
* QTimer for playback

Optional:

* background loading using worker threads (if needed)

Constraints:

* no blocking operations in UI thread
* deterministic playback timing

---

### 6.9 Data Handling
Data is loaded using:

* standard Python JSON handling
* lightweight in-memory structures

Design choice:

> **Prefer simple Python data structures over heavy frameworks**

No dependency on:

* ORM systems
* external databases
* serialization frameworks beyond JSON

---

### 6.10 Integration with CLI
The visualization is integrated into the existing CLI tool:

```bash
axis visualize --experiment-id EXP_001
```

The CLI is responsible for:

* resolving file paths
* selecting artifacts
* passing parameters to the visualization process

The UI application receives:

* resolved paths
* initial selection parameters

---

### 6.11 Development Constraints
The chosen stack must support:

* development in WSL + Ubuntu
* execution without GPU dependencies
* minimal external dependencies

Additionally:

* installation must be straightforward (pip-based)
* no system-level configuration required beyond Qt

---

### 6.12 LLM-Assisted Development Compatibility
The technology stack is selected to align with:

> **LLM-assisted code generation workflows (e.g. Claude Code)**

PySide6 provides:

* explicit structure
* predictable patterns
* well-defined component boundaries

This enables:

* incremental implementation via work packages
* reliable generation of UI components
* reduced ambiguity in interaction logic

---

### 6.13 Long-Term Considerations
The current choice prioritizes:

* rapid implementation
* clarity of architecture
* engineering usability

Future evolution may include:

* migration to alternative frontends
* remote visualization capabilities

However:

* no abstraction is introduced prematurely
* current implementation remains concrete and focused

---

## 7. UI Architecture Overview

### 7.1 Purpose
This section defines the **structural organization of the user interface** and the responsibilities of its major components.

The UI architecture is designed to:

* reflect the replay model clearly
* separate visualization from control logic
* support efficient inspection and navigation
* remain extensible without over-engineering

---

### 7.2 Architectural Style
The UI follows a **component-based, state-driven architecture**:

* A single **central ViewerState** drives all UI updates
* UI components are **loosely coupled** and communicate via state changes
* Rendering is **stateless** and derived from current state

Interaction flow:

```id="s2v7ml"
User Input → UI Component → State Update → Global Refresh → Re-render
```

---

### 7.3 High-Level Layout Structure
The application window is divided into **four primary regions**:

```
+---------------------------------------------------------+
|                     Dashboard                           |
+----------------------+----------------+------------------+
|                      |                |                  |
|     Grid View        | Detail Panel   |   Control Panel  |
|                      |                |                  |
|                      |                |                  |
+----------------------+----------------+------------------+
```

---

### 7.4 Component Overview

#### A. Dashboard (Top Section)

**Purpose:**

* display high-level episode and replay information

**Responsibilities:**

* current step index
* current phase
* agent energy (always visible)
* episode metadata (IDs, duration)
* playback state (playing / paused)

**Constraints:**

* read-only
* no interaction logic beyond display

---

#### B. Grid View (Primary Visualization Area)

**Purpose:**

* render the world state (grid + agent)

**Responsibilities:**

* display cell values (resources, obstacles)
* render agent position
* apply color mapping
* handle mouse interaction (cell selection, agent selection)

**Constraints:**

* no business logic
* rendering strictly derived from snapshot
* click events translated into state updates

---

#### C. Detail Panel (Contextual Inspection)

**Purpose:**

* display detailed information about selected entity

**Supports:**

* selected cell
* selected agent

**Responsibilities:**

* show:

  * cell properties (resource value, consumption count up to current step)
  * agent state (energy, internal variables)

**Behavior:**

* updates dynamically based on:

  * selection
  * replay position

---

#### D. Control Panel (Interaction Controls)

**Purpose:**

* control replay navigation

**Responsibilities:**

* play / pause
* step forward / backward
* jump to start / end
* seek via slider (scrubber)
* optional playback speed control

**Constraints:**

* does not manipulate data directly
* only updates ViewerState

---

### 7.5 Secondary UI Elements

#### Configuration Viewer (Modal / Separate Window)

**Purpose:**

* display full configuration of the current run

**Access:**

* triggered via button in Dashboard

**Behavior:**

* opens separate window or modal dialog
* shows raw configuration (structured view or JSON)

---

### 7.6 Layout Management
The UI uses Qt layout primitives:

* vertical layout for main structure
* horizontal split for main panels
* optional resizable splitters

Requirements:

* panels must be resizable
* layout must remain stable under resizing
* no overlapping components

---

### 7.7 Component Communication Model
All components communicate **indirectly via ViewerState**.

No direct dependencies between:

* Grid View ↔ Control Panel
* Detail Panel ↔ Dashboard

Instead:

```id="rpf8zl"
Component → emits event → ViewerState updated → all components react
```

---

### 7.8 Update Strategy
The UI follows a **reactive update model**:

* any change in ViewerState triggers:

  * snapshot resolution
  * re-render of affected components

Update rules:

* Grid View updates on:

  * step change
  * phase change

* Detail Panel updates on:

  * selection change
  * step change

* Dashboard updates on:

  * any replay state change

---

### 7.9 Selection Flow
Selection originates from the Grid View:

#### Cell Selection

* user clicks on a cell
* state updated:

  * `selected_entity = CELL`
  * `selected_cell_position = (x, y)`

#### Agent Selection

* user clicks on agent
* state updated:

  * `selected_entity = AGENT`

The Detail Panel reacts accordingly.

---

### 7.10 Replay Synchronization
All UI components must remain synchronized with:

> **(current_step_index, current_phase)**

There must never be:

* partial updates
* inconsistent visual states

---

### 7.11 Rendering Responsibility Boundaries

#### Grid View

* responsible for:

  * spatial rendering
* not responsible for:

  * replay logic
  * state transitions

#### Panels

* responsible for:

  * formatted display
* not responsible for:

  * computation of core state

---

### 7.12 Minimal Coupling Principle
Each UI component must:

* depend only on:

  * ViewerState
  * resolved Snapshot (if needed)

This ensures:

* testability
* replaceability
* clarity of behavior

---

### 7.13 Scalability Considerations
The layout must allow future extensions such as:

* additional panels
* multi-agent visualization
* extended metrics

Without requiring:

* redesign of core layout
* breaking changes to existing components

---

## 8. Main Window Layout

### 8.1 Purpose
This section defines the **concrete layout structure** of the main application window, including:

* spatial arrangement of UI components
* layout hierarchy
* resizing behavior
* integration of primary panels

The goal is to provide a **deterministic and implementable layout specification**.

---

### 8.2 Main Window Structure
The application is implemented as a:

> **QMainWindow-based application**

The central UI is composed within the **central widget** using nested layouts and splitters.

High-level structure:

```
QMainWindow
 └── CentralWidget (QWidget)
      └── MainVerticalLayout
           ├── DashboardWidget
           └── MainHorizontalSplitter
                ├── GridViewWidget
                ├── DetailPanelWidget
                └── ControlPanelWidget
```

---

### 8.3 Layout Hierarchy

#### A. Root Layout

* Type: `QVBoxLayout`
* Assigned to: CentralWidget

Structure:

* Top: Dashboard
* Bottom: Main content area

---

#### B. Main Content Area

* Type: `QSplitter (Horizontal)`

Contains three primary panels:

1. Grid View (left, dominant)
2. Detail Panel (center)
3. Control Panel (right)

---

### 8.4 Component Placement

#### 8.4.1 Dashboard (Top Section)

* Position: top of main window
* Layout behavior:

  * fixed or minimal height
  * spans full width

Responsibilities:

* display global state
* provide access to configuration viewer

---

#### 8.4.2 Grid View (Left Panel)

* Position: left section of horizontal splitter
* Layout behavior:

  * takes majority of available width
  * fully resizable

Constraints:

* must maintain aspect ratio of grid (if applicable)
* must scale with window size

---

#### 8.4.3 Detail Panel (Center Panel)

* Position: middle section
* Layout behavior:

  * moderate width
  * resizable

Purpose:

* contextual inspection
* dynamically updated content

---

#### 8.4.4 Control Panel (Right Panel)

* Position: right section
* Layout behavior:

  * minimal width
  * optionally fixed or semi-fixed

Purpose:

* user interaction controls
* playback management

---

### 8.5 Splitter Configuration
The main horizontal splitter must:

* allow dynamic resizing of panels
* preserve relative proportions

Initial size ratios (conceptual):

```
Grid View      : 60–70%
Detail Panel   : 20–25%
Control Panel  : 10–15%
```

Constraints:

* panels must not collapse completely
* minimum widths must be enforced

---

### 8.6 Resizing Behavior
The layout must support:

#### Window Resize

* all components adjust proportionally
* Grid View expands/shrinks dynamically

#### Splitter Interaction

* user can manually resize panels
* resizing persists during session

---

### 8.7 Scroll and Overflow Handling

#### Grid View

* no scrollbars
* scales to available space

#### Detail Panel

* may include scrollable content
* must handle long data gracefully

#### Control Panel

* vertical layout
* may include scroll if content grows

---

### 8.8 Configuration Viewer Integration
The configuration viewer is **not embedded** in the main layout.

Instead:

* triggered via Dashboard button
* opens as:

  * modal dialog or separate window

This ensures:

* main layout remains uncluttered
* configuration does not interfere with replay

---

### 8.9 Layout Stability Requirements
The layout must:

* remain stable under all interactions
* avoid dynamic reflow of major components
* prevent overlapping or hidden elements

No component may:

* change position dynamically
* alter layout structure at runtime

---

### 8.10 Initialization Behavior
On application startup:

* layout is constructed once
* default splitter sizes are applied
* no delayed layout modifications

Optional:

* restore last layout state (future extension)

---

### 8.11 Separation from Logic
The Main Window is responsible only for:

* assembling UI components
* defining layout structure

It must not:

* contain replay logic
* contain state management logic

All behavior must be delegated to:

* ViewerState
* Controllers
* Individual components

---

### 8.12 Minimal Implementation Blueprint
Conceptual structure:

```python
class MainWindow(QMainWindow):
    def __init__(self):
        self.dashboard = DashboardWidget()
        self.grid_view = GridViewWidget()
        self.detail_panel = DetailPanelWidget()
        self.control_panel = ControlPanelWidget()

        self._build_layout()
```

Layout assembly:

```python
def _build_layout(self):
    central = QWidget()
    main_layout = QVBoxLayout(central)

    main_layout.addWidget(self.dashboard)

    splitter = QSplitter(Qt.Horizontal)
    splitter.addWidget(self.grid_view)
    splitter.addWidget(self.detail_panel)
    splitter.addWidget(self.control_panel)

    main_layout.addWidget(splitter)

    self.setCentralWidget(central)
```

---

### 8.13 Extensibility Considerations
The layout must allow:

* insertion of additional panels
* replacement of individual components
* extension of Dashboard content

Without requiring:

* structural redesign
* breaking existing component contracts

---

## 9. Grid Visualization Model

### 9.1 Purpose
This section defines how the **world state (grid)** is:

* represented
* rendered
* interacted with

within the Visualization System.

The Grid Visualization Model translates:

> **world state → visual representation**

in a deterministic and inspectable manner.

---

### 9.2 Conceptual Model
The world is represented as a:

> **2D discrete grid**

Formally:

```text
Grid ∈ ℝ^(H × W)
```

Where:

* `H` = number of rows
* `W` = number of columns

Each cell represents a **world location** and contains:

* resource value
* optional attributes (e.g. obstacle flag)

---

### 9.3 Rendering Responsibilities
The Grid View is responsible for:

* spatial rendering of all cells
* visual encoding of resource values
* rendering of the agent
* handling click interaction

It is not responsible for:

* replay logic
* state transitions
* data loading

---

### 9.4 Coordinate System
The grid uses a **row-major coordinate system**:

```text
(row, col)
```

Mapping:

* `(0, 0)` = top-left cell
* increasing `row` → downward
* increasing `col` → right

This coordinate system must be consistent with:

* persisted data
* click detection
* selection logic

---

### 9.5 Cell Geometry
Each cell is rendered as a:

> **rectangular region of equal size**

Given:

* widget width = `W_px`
* widget height = `H_px`

Cell dimensions:

```text
cell_width  = W_px / W
cell_height = H_px / H
```

Constraints:

* cells must fully tile the available area
* no gaps or overlaps
* floating-point rounding must be handled deterministically

---

### 9.6 Resource Value Mapping
Each cell’s resource value is mapped to a **visual color**.

Requirements:

* deterministic mapping
* monotonic relationship between value and intensity

Example mapping (conceptual):

```text
low value  → light color  
high value → saturated color
```

Constraints:

* color scale must be fixed for a given visualization session
* no dynamic rescaling per frame

---

### 9.7 Agent Rendering
The agent is rendered as an **overlay element** on top of the grid.

#### Position

* derived from agent state in snapshot
* mapped to corresponding cell

#### Representation

* distinct visual marker (e.g. filled circle or highlighted cell)

#### Constraints

* must be visually distinguishable from cell background
* must not obscure grid structure entirely

---

### 9.8 Rendering Order
Rendering must follow a strict order:

1. background
2. grid cells
3. grid lines (optional)
4. agent overlay
5. selection highlight

This ensures:

* consistent layering
* clear visual hierarchy

---

### 9.9 Selection Model (Grid-Level)
The grid supports selection of:

* individual cells
* the agent

#### Cell Selection

* triggered by mouse click
* updates ViewerState:

  * `selected_entity = CELL`
  * `selected_cell_position = (row, col)`

#### Agent Selection

* triggered by clicking on agent location
* updates:

  * `selected_entity = AGENT`

---

### 9.10 Click Detection
Mouse coordinates must be mapped to grid coordinates:

```text
col = floor(x / cell_width)
row = floor(y / cell_height)
```

Constraints:

* mapping must be deterministic
* out-of-bounds clicks must be ignored

---

### 9.11 Selection Highlighting
Selected elements must be visually indicated:

#### Cell

* border or overlay highlight

#### Agent

* distinct highlight (e.g. thicker outline or color change)

Constraints:

* highlight must not interfere with base rendering
* must update immediately on selection

---

### 9.12 Temporal Rendering Consistency
At any replay position:

> **the grid must represent exactly the resolved snapshot**

No interpolation between steps is allowed.

Changes between steps must appear as:

* discrete transitions

---

### 9.13 Derived Cell Metrics
The grid may display or provide access to derived metrics such as:

> **number of times a cell has been consumed up to current step**

These values:

* are computed on demand
* depend only on:

  * steps `[0 … current_step_index]`

They must not:

* be stored in the grid
* alter rendering unless explicitly enabled

---

### 9.14 Performance Considerations
Rendering must be efficient for:

* large grids
* continuous playback

Guidelines:

* redraw entire grid per update (acceptable due to simplicity)
* avoid per-cell object allocation during rendering
* reuse brushes, pens, and colors

---

### 9.15 Scaling Behavior
The grid must:

* scale with window size
* maintain proportional cell sizes

Optional:

* enforce square cells (if required by domain)

---

### 9.16 Rendering Technology
Implementation must use:

> **PySide6 QWidget with QPainter**

Responsibilities:

* override `paintEvent()`
* perform all rendering within painter context

No external rendering frameworks are used.

---

### 9.17 Error Handling
If grid data is invalid:

* inconsistent dimensions
* missing values

The system must:

* fail explicitly
* not attempt partial rendering

---

### 9.18 Extensibility
The model must allow future extensions such as:

* obstacle visualization
* heatmaps
* multi-agent overlays

Without breaking:

* coordinate system
* rendering pipeline

---

## 10. Dashboard Information Model**

### 10.1 Purpose
The Dashboard Information Model defines the set of information that must be displayed in the **always-visible dashboard region** of the Visualization System.

Its purpose is to provide:

* continuous situational awareness during replay
* immediate access to the most important episode and replay state
* contextual interpretation of the currently displayed grid state
* a compact summary of current and cumulative execution behavior

The dashboard is a **read-only monitoring surface**. It does not define replay behavior itself. It reflects the current replay position and related derived values.

This is aligned with the original visualization requirement that core episode information and agent state, especially energy, must remain visible during replay.

---

### 10.2 General Principle
The dashboard shall expose information at three different levels:

#### A. Replay Context
Information about where the user currently is in the replay hierarchy.

#### B. Current Step State
Information about the currently selected replay position.

#### C. Running Episode Statistics
Cumulative values derived from the episode up to the current replay position.

This structure ensures that the user can answer three distinct questions at all times:

* **What am I looking at?**
* **What is happening right now?**
* **What has happened so far?**

---

### 10.3 Always-Visible Information
The following information shall always be visible in the dashboard.

### 10.3.1 Experiment Context

* experiment ID
* run ID
* episode ID

These identifiers define the current replay context and allow the user to locate the current episode within the persisted experiment hierarchy.

### 10.3.2 Replay Position

* current step index
* total number of steps
* current transition phase

The phase must be displayed explicitly, because one timestep may contain multiple distinct visual states.

### 10.3.3 Playback State

* playback mode: playing or paused
* current playback speed

This ensures that replay behavior remains transparent and debuggable.

### 10.3.4 Core Agent State

* current energy

Energy is the most critical agent signal and must remain visible at all times, independent of selection state.

### 10.3.5 Current Action Context

* selected action of the current step

This helps interpret the relationship between the current world state and the recorded agent behavior.

### 10.3.6 Current Position

* current agent position

Although position is not part of the agent’s internal knowledge, it is part of the observability and replay surface and must remain visible for debugging and interpretation. This is consistent with the earlier observability requirements that external engineering tooling may expose position information for analysis and visualization.

### 10.3.7 Termination State

* terminated: yes/no
* termination reason, if available

This allows the user to understand whether the current replay position corresponds to a terminal state.

---

### 10.4 Current-Step Information
In addition to always-visible context, the dashboard shall display detailed information for the currently selected replay position.

### 10.4.1 Current Drive Information

* hunger activation

This exposes the motivational state associated with the current step and supports behavioral interpretation.

### 10.4.2 Current Transition Outcome

* moved: yes/no
* consumed: yes/no
* resource consumed in current step
* energy delta in current step

These values summarize the local effect of the selected action and the resulting transition.

### 10.4.3 Current Replay Phase
The dashboard must reflect clearly which phase is currently displayed:

* before
* after_regen
* after_action

This is especially important because the same timestep may correspond to different visible world states depending on the chosen phase.

---

### 10.5 Running Episode Statistics
The dashboard should also include lightweight cumulative statistics up to the current replay position.

These values are not global episode summaries independent of replay time. They are:

> **prefix-based statistics over steps [0 … current_step_index]**

This is an important design rule.

### 10.5.1 Action-Based Running Statistics

* consume count so far
* movement count so far
* optional action counts per action type

### 10.5.2 Energy-Based Running Statistics

* mean energy so far

This provides a compact view of how stable or unstable the agent’s internal state has been across the episode prefix.

### 10.5.3 Consumption-Related Running Statistics
Where useful and derivable cheaply, the dashboard may include:

* total resource consumed so far

These values must be derived deterministically from persisted step data and the current replay position.

---

### 10.6 Data Origin Rules
The dashboard may display only data that is:

* directly present in persisted artifacts
* or deterministically derived from persisted artifacts and current replay position

The dashboard must not display:

* inferred internal state not present in the replay model
* recomputed simulation outcomes
* speculative values

This is consistent with the broader replay principle that visualization is artifact-driven and does not simulate or reconstruct hidden execution state.

---

### 10.7 Layout and Presentation Principles
The dashboard should remain compact, legible, and stable.

#### 10.7.1 Stability
The set and order of dashboard fields should remain fixed during replay.
Values may change, but the structure should not shift dynamically.

#### 10.7.2 Readability
Critical values such as energy, step index, phase, and action should be easy to identify quickly.

#### 10.7.3 Grouping
The dashboard should visually group information into sections such as:

* Replay Context
* Current Step
* Running Statistics

This improves clarity without changing the underlying data model.

---

### 10.8 Relationship to Other UI Regions
The dashboard is complementary to, but distinct from, other UI components.

#### Dashboard vs. Grid

* Grid shows spatial state
* Dashboard shows contextual and temporal state

#### Dashboard vs. Detail Panel

* Dashboard shows always-relevant information
* Detail Panel shows selection-specific information

#### Dashboard vs. Debug Overlay

* Dashboard contains baseline monitoring information
* Debug Overlay contains optional engineering detail

This prevents the dashboard from becoming overloaded with highly technical trace content by default.

---

### 10.9 Interaction Requirements
The dashboard is primarily read-only.

However, it may contain lightweight interaction elements such as:

* button to open configuration / metadata window
* toggle for debug overlay, if placed there
* phase selector, if placed there rather than in the control panel

Any interactive element placed in the dashboard must still follow the general rule:

> UI interaction changes Viewer State, not runtime or persisted data.

---

### 10.10 Validation and Consistency
Dashboard values must remain consistent with the current replay position.

For any visible value, it must be possible to trace it back to:

* current step index
* current phase
* current persisted episode data
* or a clearly defined prefix-based deterministic aggregation rule

This is critical for debugging and trustworthiness.

---

### 10.11 Extensibility
The Dashboard Information Model should allow future extension with additional fields such as:

* richer action summaries
* trajectory statistics
* energy trend indicators
* compact plot widgets

However, the baseline implementation should remain conservative and include only information that is clearly useful during replay and inspection.

---

### 10.12 Architectural Consequence
Any implementation based on this model must therefore provide a dashboard that:

* is always visible
* exposes stable replay context
* keeps energy permanently visible
* shows current step and phase explicitly
* includes local transition outcome information
* supports deterministic running episode statistics up to the current replay position
* remains read-only except for explicitly defined viewer controls

---

## 11. Replay Controls

### 11.1 Purpose
This section defines the **control mechanisms** used to navigate and interact with the replay timeline.

The Replay Controls provide:

* deterministic navigation through episode steps
* control over playback execution
* direct access to arbitrary replay positions

They operate exclusively by updating:

> **ViewerState (step_index, phase, playback state)**

No control directly manipulates data or UI components.

---

### 11.2 Control Categories
Replay controls are grouped into three categories:

#### A. Playback Controls

* control temporal progression

#### B. Navigation Controls

* discrete movement through steps

#### C. Direct Access Controls

* jump to arbitrary positions

---

### 11.3 Playback Controls

#### 11.3.1 Play
Sets:

```text
is_playing = True
```

Behavior:

* advances replay position automatically
* continues until:

  * paused
  * end of episode reached

---

#### 11.3.2 Pause
Sets:

```text
is_playing = False
```

Behavior:

* halts playback immediately
* preserves current replay position

---

#### 11.3.3 Resume
Equivalent to Play from current position.

---

#### 11.3.4 Stop
Sets:

```text
is_playing = False
current_step_index = 0
current_phase = BEFORE
```

Behavior:

* resets replay to initial position

---

### 11.4 Navigation Controls

#### 11.4.1 Step Forward
Advances to next step:

```text
current_step_index += 1
```

Constraints:

* must not exceed maximum step index
* clamps at episode end

---

#### 11.4.2 Step Backward
Moves to previous step:

```text
current_step_index -= 1
```

Constraints:

* must not go below 0

---

#### 11.4.3 Jump to Start

```text
current_step_index = 0
current_phase = BEFORE
```

---

#### 11.4.4 Jump to End

```text
current_step_index = N
current_phase = AFTER_ACTION
```

---

### 11.5 Phase Controls

#### 11.5.1 Phase Selection

Allows direct selection of:

```text
phase ∈ { BEFORE, AFTER_REGEN, AFTER_ACTION }
```

Behavior:

* updates only phase
* does not change step index

---

#### 11.5.2 Optional Phase Cycling

Optional control:

* cycle through phases within current step

Order:

```text
BEFORE → AFTER_REGEN → AFTER_ACTION → BEFORE
```

---

### 11.6 Direct Access Controls

#### 11.6.1 Scrubber (Timeline Slider)**
Allows continuous navigation across steps.

Behavior:

* maps slider position → step index
* updates:

```text
current_step_index = mapped_value
```

Constraints:

* must be deterministic
* must not skip internal states implicitly

---

#### 11.6.2 Numeric Step Input (Optional)
Allows direct entry of step index.

Constraints:

* input must be validated
* out-of-range values must be clamped or rejected

---

### 11.7 Playback Speed Control
Optional but recommended:

```text
playback_speed ∈ ℝ⁺
```

Behavior:

* controls time interval between step updates

Constraints:

* must not affect replay logic
* only affects timing

---

### 11.8 Playback Execution Model
Playback is implemented via:

> **timer-driven updates (e.g. QTimer)**

Loop:

```text
if is_playing:
    advance_step()
    update_state()
```

Constraints:

* must be interruptible
* must not block UI thread

---

### 11.9 Boundary Behavior

#### At Start

* cannot step backward
* playback begins from `(0, BEFORE)`

#### At End

* playback stops automatically
* no wrap-around

---

### 11.10 State Transition Rules
All controls must modify only:

* `current_step_index`
* `current_phase`
* `is_playing`
* `playback_speed`

No control may:

* modify snapshot data
* alter derived metrics directly

---

### 11.11 Interaction Consistency
All control actions must:

* produce immediate and visible effect
* keep all UI components synchronized

There must be no:

* delayed updates
* partial refreshes
* inconsistent states

---

### 11.12 Conflict Handling
If multiple inputs occur simultaneously:

* last input wins
* state must remain valid

Example:

* user drags scrubber while playing
  → playback continues from new position

---

### 11.13 Error Handling
Invalid operations must be handled explicitly:

* stepping beyond bounds → clamp
* invalid input → reject or correct

No silent failures.

---

### 11.14 Minimal Control Interface
Conceptual interface:

```python
class ReplayControls:
    def play()
    def pause()
    def stop()

    def next_step()
    def prev_step()

    def set_step(index: int)
    def set_phase(phase: Phase)

    def set_speed(speed: float)
```

---

### 11.15 Relationship to Viewer State
Replay Controls are:

> **pure state mutators**

They do not:

* resolve snapshots
* trigger rendering directly

Instead:

```text
Control → ViewerState Update → ReplayController → UI Refresh
```

---

### 11.16 Non-Simulation Guarantee
Replay Controls must not:

* execute environment logic
* recompute transitions

They operate strictly on:

> **recorded timeline navigation**

---

## 12. Interaction Model

### 12.1 Purpose
The Interaction Model defines how **user input** is:

* captured
* interpreted
* translated into state changes

within the Visualization System.

It establishes a consistent mapping from:

> **User Action → State Transformation → UI Update**

The goal is to ensure:

* predictability
* consistency across components
* strict alignment with the Viewer State Model

---

### 12.2 Core Principle
All interactions are modeled as:

> **pure transformations of ViewerState**

No interaction may:

* directly manipulate UI elements
* bypass the state model
* modify persisted data

---

### 12.3 Interaction Flow
All user interactions follow the same pipeline:

```text id="i2pxxk"
User Input → UI Event → Interaction Handler → ViewerState Update → Global Refresh
```

This ensures:

* uniform behavior
* traceability of changes
* decoupling of UI and logic

---

### 12.4 Interaction Categories
The system supports four primary categories of interaction:

#### A. Spatial Interaction

* interaction with the grid

#### B. Temporal Interaction

* navigation through time

#### C. Selection Interaction

* choosing entities for inspection

#### D. UI Interaction

* interaction with controls and dialogs

---

### 12.5 Spatial Interaction (Grid)

#### 12.5.1 Cell Selection
Trigger:

* user clicks on a grid cell

Effect:

```text id="4l5zv2"
selected_entity = CELL
selected_cell_position = (row, col)
```

Behavior:

* Detail Panel updates to show cell data
* selection persists across time navigation

---

#### 12.5.2 Agent Selection
Trigger:

* user clicks on the agent

Effect:

```text id="vqbt7v"
selected_entity = AGENT
```

Behavior:

* Detail Panel shows agent state
* overrides previous cell selection

---

#### 12.5.3 Click Priority
If a click occurs on a cell containing the agent:

* agent selection takes precedence

---

#### 12.5.4 Out-of-Bounds Interaction
Clicks outside the grid:

* must be ignored
* must not alter ViewerState

---

### 12.6 Temporal Interaction
Temporal interaction is defined via Replay Controls (Section 11), but follows the same interaction model.

Examples:

* step forward
* scrub timeline
* change phase

Each interaction updates:

```text id="k9ebhp"
current_step_index
current_phase
is_playing
```

---

### 12.7 Selection Interaction
Selection is a **persistent state**, independent of replay position.

#### 12.7.1 Persistence Across Time

* selected cell remains selected when stepping
* selected agent remains selected

#### 12.7.2 Selection Validity
If a selected entity becomes invalid:

Example:

* agent selection at a step where agent data is missing

Behavior:

* selection must be cleared or invalidated explicitly

---

#### 12.7.3 Clearing Selection
Trigger:

* optional user action (e.g. clicking empty space)

Effect:

```text id="v5czns"
selected_entity = NONE
```

---

### 12.8 UI Interaction

#### 12.8.1 Control Panel Interaction
Examples:

* play / pause
* step navigation
* slider movement

Effect:

* update ViewerState only

---

#### 12.8.2 Dashboard Interaction
Limited interaction allowed:

* open configuration viewer
* optional toggles

Must follow:

* same state-driven update model

---

#### 12.8.3 Modal Interaction
Example:

* configuration dialog

Behavior:

* does not block or alter replay state
* read-only access to data

---

### 12.9 Interaction Consistency Rules
All interactions must satisfy:

#### Immediate Feedback

* visible result after each interaction

#### Determinism

* same interaction → same result

#### No Hidden Effects

* no implicit state changes

---

### 12.10 Conflict Resolution
If multiple interactions occur:

* last interaction defines state
* system must remain consistent

Example:

* user scrubs while playing
  → playback continues from new position

---

### 12.11 Interaction Scope Boundaries
Interactions must not:

* trigger execution logic
* recompute environment state
* modify persisted artifacts

They are strictly limited to:

> **navigation and inspection**

---

### 12.12 Error Handling
Invalid interactions must be handled explicitly:

* invalid coordinates → ignore
* invalid step index → clamp or reject
* invalid phase → reject

No silent failures.

---

### 12.13 Extensibility
The interaction model must support future additions such as:

* multi-agent selection
* multi-cell selection
* advanced inspection tools

Without breaking:

* state-driven architecture
* deterministic behavior

---

### 12.14 Minimal Interaction Interface
Conceptual abstraction:

```python id="q4gl7u"
class InteractionHandler:
    def on_cell_click(row: int, col: int)
    def on_agent_click()

    def on_play()
    def on_pause()

    def on_step_forward()
    def on_step_backward()

    def on_scrub(step_index: int)

    def on_select_phase(phase: Phase)
```

---

### 12.15 Relationship to Other Models
The Interaction Model connects:

* **Replay Controls (Section 11)** → temporal interaction
* **Grid Visualization Model (Section 9)** → spatial interaction

It acts as:

> **the bridge between user intent and system state**

---

## 13. Detail Views

### 13.1 Purpose
Detail Views provide **focused inspection capabilities** for selected entities.

They allow the user to:

* inspect internal state of the agent
* analyze properties of specific grid cells
* understand local context beyond the main visualization

They are strictly:

> **read-only projections of ViewerState**

---

### 13.2 Design Goals
Detail Views must:

* reflect the current ViewerState precisely
* update immediately on selection change
* remain compact and readable
* avoid overwhelming the user with raw data

---

### 13.3 Supported Detail Views
The system supports two primary detail contexts:

#### A. Agent Detail View

* activated when agent is selected

#### B. Cell Detail View

* activated when a grid cell is selected

---

### 13.4 Agent Detail View

#### 13.4.1 Trigger

```text
selected_entity = AGENT
```

---

#### 13.4.2 Displayed Information
The Agent Detail View should expose:

**Core State**

* current energy $e_t$
* hunger level $h_t$

**Action Context**

* last selected action
* action probabilities (optional but very valuable for debugging)

**Position**

* current grid coordinates

**Internal Signals (optional but recommended)**

* drive contributions
* value function output

---

#### 13.4.3 Visualization Style

* structured key-value layout
* optional small bar indicators for:

  * energy
  * hunger

Avoid:

* raw JSON dumps
* overly technical formatting

---

### 13.5 Cell Detail View

#### 13.5.1 Trigger

```text
selected_entity = CELL
selected_cell_position = (row, col)
```

---

#### 13.5.2 Displayed Information

**Cell Properties**

* resource value $r$
* obstacle flag

**Derived Meaning**

* whether consumable
* relative attractiveness

---

#### 13.5.3 Context Awareness
Cell data must reflect:

* current step
* current phase

This is important because:

* world state may differ between phases

---

### 13.6 Empty / No Selection State

If:

```text
selected_entity = NONE
```

The Detail View must:

* display a neutral placeholder
* optionally guide the user:

> “Select a cell or the agent to inspect details”

---

### 13.7 Update Behavior
Detail Views must update when:

* selection changes
* current step changes
* current phase changes

This ensures:

> **temporal + spatial consistency**

---

### 13.8 Performance Considerations
Detail Views must:

* avoid heavy recomputation
* use already parsed Replay Data

Updates should be:

* lightweight
* immediate

---

### 13.9 Extensibility
The Detail View system should support future extensions:

* memory inspection (episodic memory $m_t$)
* trajectory traces
* comparative views across steps

---

### 13.10 Separation from Core Logic
Detail Views must not:

* modify ViewerState
* trigger replay changes
* execute logic

They are strictly:

> **passive observers of system state**

---

### 13.11 Minimal Interface
Conceptual structure:

```python
class DetailView(QWidget):
    def update_from_state(viewer_state):
        pass
```

Specializations:

```python
class AgentDetailView(DetailView):
    ...

class CellDetailView(DetailView):
    ...
```

---

### 13.12 Relationship to Other Components

Detail Views depend on:

* **Interaction Model (Section 12)** → selection
* **Replay Model (Section 5)** → data source
* **Viewer State Model (upcoming)** → authoritative state

They are part of:

> **the inspection layer of the UI**

---

## 14. Debug Overlay Mode

### 14.1 Purpose
The Debug Overlay Mode provides **deep introspection capabilities** by visualizing internal decision-making signals directly on top of the grid.

It enables the user to:

* understand *why* an action was selected
* inspect local decision structure
* validate model behavior against expectations

It is designed primarily for:

> **debugging, validation, and analysis of agent behavior**

---

### 14.2 Core Principle
The Debug Overlay is:

* **read-only**
* **state-driven**

It must never:

* influence agent behavior
* modify ViewerState beyond visualization flags
* introduce additional computation beyond already available replay data

---

### 14.3 Activation
The overlay is controlled via UI toggle:

```text
debug_overlay_enabled = True | False
```

Optional extensions:

* multiple overlay modes
* layer selection

---

### 14.4 Overlay Types
The system should support multiple overlay layers, configurable independently.

---

#### 14.4.1 Action Preference Overlay
Displays the **action scoring or probability distribution** over possible actions.

Visualization ideas:

* arrows indicating direction
* intensity based on score
* optional numeric labels

Purpose:

* validate policy behavior
* detect unexpected action biases

---

#### 14.4.2 Resource Gradient Overlay
Displays local resource values $r$ across the grid.

Visualization:

* heatmap
* color gradient (low → high resource)

Purpose:

* correlate agent movement with environment structure

---

#### 14.4.3 Consumption Opportunity Overlay
Highlights cells where:

* consumption is possible
* resource is present

Purpose:

* verify correctness of CONSUME action triggering

---

#### 14.4.4 Drive Contribution Overlay
Displays contributions of internal drives to decision-making.

Example:

* hunger contribution
* directional bias

Purpose:

* inspect internal decision mechanics
* validate weighting parameters

---

#### 14.4.5 Value Function Overlay
Displays computed value $V$ across local actions or positions.

Purpose:

* understand evaluation landscape
* debug unexpected decisions

---

### 14.5 Overlay Rendering Model
Overlays are rendered:

* on top of the grid
* synchronized with current step and phase

Rendering must:

* not obscure core information
* remain visually interpretable

---

### 14.6 Layering and Composition
If multiple overlays are active:

* rendering order must be defined
* visual conflict must be minimized

Example layering:

1. base grid
2. resource heatmap
3. action arrows
4. agent marker

---

### 14.7 Performance Considerations
Debug overlays must:

* use precomputed replay data
* avoid recomputation of policy or drives

Rendering must remain:

* real-time
* responsive during playback

---

### 14.8 Interaction with Replay
Overlay must update when:

* step changes
* phase changes
* playback progresses

No caching inconsistencies allowed.

---

### 14.9 UI Controls
The UI should provide:

* toggle Debug Mode
* optional overlay selection

Example:

* checkbox: "Show Action Preferences"
* checkbox: "Show Resource Heatmap"

---

### 14.10 Minimal Configuration Interface
Conceptual structure:

```python
class DebugOverlayConfig:
    enabled: bool
    show_action_preferences: bool
    show_resource_gradient: bool
    show_consumption: bool
    show_drive_contributions: bool
```

---

### 14.11 Visual Encoding Guidelines
Overlays must follow consistent encoding:

* color gradients → scalar values
* arrows → directional values
* opacity → confidence or strength

Avoid:

* cluttered visuals
* overlapping unreadable elements

---

### 14.12 Failure Handling
If overlay data is missing:

* overlay must be disabled gracefully
* UI must not crash

Optional:

* display warning in dashboard

---

### 14.13 Extensibility
The overlay system should allow:

* new overlay types
* custom debug signals

Without changes to:

* core rendering pipeline
* interaction model

---

### 14.14 Separation of Concerns
Debug overlays must remain:

> **strictly a visualization layer**

They must not:

* introduce logic into replay
* alter simulation outcomes

---

### 14.15 Relationship to Other Components
Debug Overlay Mode builds upon:

* **Replay Data Contract (Section 4)** → source of internal signals
* **Grid Visualization Model (Section 9)** → rendering surface
* **Interaction Model (Section 12)** → toggle and control
* **Detail Views (Section 13)** → complementary inspection

It acts as:

> **a bridge between internal model signals and spatial visualization**

---

## 15. Config and Metadata Inspection

### 15.1 Purpose
The Config and Metadata Inspection module provides **transparent access to experiment configuration and contextual information** associated with replay data.

It enables the user to:

* understand under which conditions a run was executed
* verify parameter settings
* correlate behavior with configuration

It is essential for:

> **reproducibility, validation, and comparative analysis**

---

### 15.2 Scope of Inspection
The system must support inspection of:

#### A. Experiment Configuration

* global parameters
* environment setup
* agent parameters

#### B. Run Metadata

* experiment ID
* run ID
* timestamps
* execution context

#### C. Optional Extended Metadata

* software version
* random seeds
* hardware/environment info

---

### 15.3 Data Sources
Configuration and metadata are obtained from:

* replay artifacts (episode files)
* experiment-level summary files
* optional metadata files

---

### 15.4 Expected Structure
Typical configuration categories include:

#### 15.4.1 Agent Configuration

* initial energy
* hunger parameters
* policy parameters (e.g. temperature $\beta$)
* action weights (e.g. $w_{consume}$)

---

#### 15.4.2 Environment Configuration

* grid size
* resource distribution rules
* regeneration parameters

---

#### 15.4.3 Execution Configuration

* number of steps
* number of episodes
* seed values

---

### 15.5 Metadata Content
Metadata should include:

* experiment identifier
* run identifier
* creation timestamp
* duration (optional)

---

### 15.6 Access Model
Inspection is:

* **read-only**
* **non-blocking**
* **independent of replay controls**

The data must not:

* influence visualization state
* alter replay behavior

---

### 15.7 UI Representation

#### 15.7.1 Access Mechanism
Config and metadata should be accessible via:

* button or menu entry
* optional keyboard shortcut

---

#### 15.7.2 Presentation Format
The data should be displayed as:

* structured tree view (preferred)
* or collapsible sections

Example:

```text id="tw3pdt"
Agent
  - initial_energy: 100
  - beta: 1.5

Environment
  - grid_size: 20x20
  - regeneration_rate: 0.1
```

---

#### 15.7.3 Readability Requirements
The UI must:

* group logically related parameters
* avoid raw, unstructured dumps
* support large configurations

---

### 15.8 Integration with Replay
Configuration and metadata are:

* tied to the currently loaded replay
* static across all steps of that replay

Switching replay:

* updates displayed config

---

### 15.9 Performance Considerations
Config inspection must:

* load once per replay
* be cached in memory

No repeated file parsing during interaction.

---

### 15.10 Error Handling
If config or metadata is missing:

* show partial data if available
* indicate missing sections explicitly

Example:

```text id="1gq4z6"
Environment: NOT AVAILABLE
```

No silent failure.

---

### 15.11 Extensibility
The system should support:

* new configuration sections
* custom metadata fields

Without requiring:

* UI restructuring
* code changes in core components

---

### 15.12 Minimal Interface
Conceptual structure:

```python id="d0c4qg"
class ConfigInspector:
    def load(config_dict: dict, metadata_dict: dict)
    def get_tree_representation()
```

---

### 15.13 Relationship to Other Components
This module interacts with:

* **Replay Data Contract (Section 4)** → data source
* **Dashboard (Section 10)** → summary context
* **Detail Views (Section 13)** → complementary inspection

It is conceptually separate from:

* replay navigation
* visualization logic

---

### 15.14 Design Constraint
The module must enforce:

> **full transparency without adding complexity to the interaction model**

---

## 16. Viewer State Model

### 16.1 Purpose
The Viewer State Model defines the **single source of truth** for the entire visualization system.

It represents:

* current replay position
* current selection
* current playback state
* visualization flags

All UI components must:

> **derive their state exclusively from ViewerState**

---

### 16.2 Core Principle
The system follows a strict rule:

> **No UI component owns state. All state is centralized.**

This guarantees:

* determinism
* reproducibility
* consistent UI behavior

---

### 16.3 Conceptual Definition
The ViewerState is an immutable (or effectively immutable) data structure:

```text id="p7w5ux"
ViewerState_t → ViewerState_{t+1} via pure transitions
```

It captures:

* where we are in the replay
* what is selected
* how the system is being viewed

---

### 16.4 State Dimensions
ViewerState consists of four main domains:

---

#### 16.4.1 Replay Position State
Defines **where in the data we are**.

```text id="ajk2m4"
current_step_index: int
current_phase: Phase
```

Constraints:

* step index must be within bounds
* phase must be valid for the selected step

---

#### 16.4.2 Playback State
Defines **how time evolves**.

```text id="fnpwle"
is_playing: bool
playback_speed: float
```

Optional:

```text id="4x5v3p"
auto_loop: bool
```

---

#### 16.4.3 Selection State
Defines **what the user is inspecting**.

```text id="n1k8vd"
selected_entity: NONE | AGENT | CELL
selected_cell_position: (row, col) | None
```

Constraints:

* cell position only valid if entity = CELL

---

#### 16.4.4 Visualization State
Defines **how the data is rendered**.

```text id="cskc5b"
debug_overlay_enabled: bool

overlay_flags:
    show_action_preferences: bool
    show_resource_gradient: bool
    show_consumption: bool
    show_drive_contributions: bool
```

---

### 16.5 Complete ViewerState Structure
Conceptual model:

```python
class ViewerState:
    # Replay
    current_step_index: int
    current_phase: Phase

    # Playback
    is_playing: bool
    playback_speed: float

    # Selection
    selected_entity: EntityType
    selected_cell_position: Optional[Tuple[int, int]]

    # Visualization
    debug_overlay_enabled: bool
    overlay_flags: OverlayConfig
```

---

### 16.6 State Transition Model
All changes to ViewerState must occur via:

> **explicit, controlled transitions**

No direct mutation from UI components.

---

#### 16.6.1 Transition Principle

```text id="vqlv5f"
ViewerState_new = reduce(ViewerState_old, Event)
```

Where:

* Event = user interaction or system tick

---

#### 16.6.2 Example Events

```text id="p7ybk2"
STEP_FORWARD
STEP_BACKWARD
SET_STEP(index)

PLAY
PAUSE

SELECT_CELL(row, col)
SELECT_AGENT
CLEAR_SELECTION

TOGGLE_DEBUG
SET_OVERLAY(flag, value)
```

---

### 16.7 Immutability vs Mutability
Preferred model:

* **immutable state updates** (functional style)

Alternative (acceptable for PySide6):

* controlled mutation via a central controller

But must enforce:

* no uncontrolled writes
* no shared mutable access

---

### 16.8 State Controller
A dedicated component manages state transitions:

```python
class ViewerStateController:
    def get_state() -> ViewerState
    def dispatch(event)
```

Responsibilities:

* validate transitions
* update state
* trigger UI refresh

---

### 16.9 UI Binding Model
UI components must:

* subscribe to state updates
* re-render based on current state

They must not:

* store derived state
* cache outdated values

---

### 16.10 Derived State
UI components may compute:

> **derived values from ViewerState**

Example:

* current grid snapshot
* agent position
* overlay visualization

But must not store them globally.

---

### 16.11 Consistency Rules
The ViewerState must always satisfy:

#### Valid Replay Position

* step index within bounds

#### Valid Selection

* selected cell within grid

#### Coherent Phase

* phase exists for current step

---

### 16.12 Synchronization Guarantees
All components must observe:

> **the same ViewerState at any point in time**

No partial updates allowed.

---

### 16.13 Error Handling
Invalid transitions must be:

* rejected
* corrected (clamped)

Examples:

* step index < 0 → clamp to 0
* step index > max → clamp to max

---

### 16.14 Persistence Boundary
ViewerState is:

* **not persisted**
* **not part of experiment artifacts**

It is strictly:

> **runtime UI state**

---

### 16.15 Extensibility
ViewerState must support future extensions:

* multi-agent selection
* comparison mode (two steps side-by-side)
* annotation layers

Without breaking:

* existing transitions
* UI consistency

---

### 16.16 Relationship to Other Components
ViewerState is the central hub connecting:

* **Interaction Model (Section 12)** → events
* **Replay Model (Section 5)** → data source
* **Grid Visualization (Section 9)** → rendering
* **Detail Views (Section 13)** → inspection
* **Debug Overlay (Section 14)** → visualization flags

It is:

> **the backbone of the entire visualization architecture**

---

### 16.17 Design Warning (important)
If violated, the system will degrade into:

* inconsistent UI states
* hard-to-debug behavior
* implicit coupling between components

The most common failure patterns:

* UI components storing their own state
* partial updates
* hidden side effects

---

## 17. Repository and Artifact Access

### 17.1 Purpose
This section defines the architectural constraint that all experiment data must be accessed through the existing Repository System.

---

### 17.2 Core Constraint
All data access must follow:

> **Visualization System → Repository → Artifacts**

Direct file system access is strictly forbidden.

---

### 17.3 Rationale
This constraint ensures:

* consistency of data access
* decoupling from file structure
* reuse of existing infrastructure
* future compatibility with alternative storage backends

---

### 17.4 Scope of Access
The Visualization System retrieves all required data via the Repository, including:

* replay data (episodes)
* run results
* experiment configuration
* metadata

The Visualization System does not:

* parse raw files directly
* assume directory structures
* manage artifact storage

---

### 17.5 Responsibilities

#### Repository System

* handles file access
* validates and parses artifacts
* exposes structured data

#### Visualization System

* consumes structured data
* does not perform I/O operations

---

### 17.6 Integration Point
The Repository is injected or provided to the Visualization System as a dependency:

```python
class VisualizationApp:
    def __init__(self, repository: ArtifactRepository):
        self.repository = repository
```

---

### 17.7 Design Constraint
The Visualization System must remain:

> **fully agnostic to storage implementation**

This includes:

* file system layout
* serialization format
* storage location

---

### 17.8 Failure Handling
All errors related to artifact access must:

* originate from the Repository
* be propagated to the UI layer

The Visualization System must not attempt:

* recovery via direct file access
* fallback logic outside the repository

---

### 17.9 Extensibility
By enforcing this boundary, the system can later support:

* remote repositories
* database-backed storage
* streaming replay data

Without changes to:

* UI components
* Viewer State Model

---

## 18. Non-Goals and Explicit Exclusions
The baseline visualization architecture explicitly excludes:

* live follow mode
* direct coupling to runtime execution
* editing of episode data
* starting new simulations from the viewer
* direct experiment execution from the viewer
* multi-episode comparison views in the baseline version

The architecture should not prevent these from being considered later, but they are out of scope here.

---

## 19. Extension Readiness
Although the baseline viewer remains focused, the architecture should remain open to future extensions.

### 19.1 Potential Future Additions

* energy-over-time plots
* action distribution plots
* spatial trajectory overlays
* cell visitation heatmaps
* outlier episode identification
* richer experiment browser views
* side-by-side comparison of episodes
* migration to more advanced UI structures if needed

### 19.2 Immediate Extension Candidates
Even in the first architecture version, the following should be anticipated structurally:

* energy curve visualization
* spatial heatmaps
* action summaries over time

These features are not required for the baseline implementation, but the layout and state model should not block them.

---

## 20. Testing Strategy for the Visualization Layer
The visualization layer requires its own testing strategy, distinct from runtime execution tests.

### 20.1 Test Categories
The following categories should be covered:

#### Artifact Loading Tests

* valid experiment/run/episode loading
* malformed artifact failure behavior
* missing artifact handling

#### Replay Navigation Tests

* direct step jumps
* forward/backward stepping
* start/end jumps
* scrubbing
* phase switching

#### Viewer State Tests

* selection state behavior
* playback state behavior
* debug overlay toggling
* episode switching

#### Derived Information Tests

* cumulative consume count up to current timestep
* dashboard mini-statistics up to current timestep
* consistency between selected step and displayed values

#### Rendering Semantics Tests

* obstacle color semantics
* empty traversable color semantics
* resource intensity mapping
* agent visibility
* terminated marker visibility

#### CLI Launch Tests

* replay command opens expected target episode
* optional startup flags are respected

### 20.2 Read-Only Guarantee
A specific architectural test concern is that replay operations must never mutate persisted artifacts or execution state.

---

## 21. Architectural Consequence
Any implementation based on this architecture must therefore provide:

* a dedicated replay viewer above persisted artifacts
* strict read-only replay behavior
* episode-level replay with step-level and phase-level navigation
* a grid visualization with dashboard, controls, and detail pane
* click-based cell and agent inspection
* repository-based selection of experiment artifacts
* a separate config/metadata inspection window
* optional debug overlays
* explicit viewer state handling
* no dependency on live runtime execution

---

