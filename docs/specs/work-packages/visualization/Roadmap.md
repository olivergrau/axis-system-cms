# AXIS System A – Visualization Layer Roadmap

## Context

The AXIS System A runtime and experimentation framework (WP1–WP17) are fully implemented.

This includes:

* deterministic episode execution
* run and experiment orchestration
* structured result artifacts
* repository-based persistence
* resume and fault tolerance

The system now produces **complete, reproducible execution artifacts**.

---

## Objective

Introduce a **Visualization Layer** that:

* operates strictly **downstream of execution and persistence**
* provides **deterministic replay and inspection**
* enables **debugging, validation, and analysis**
* remains **read-only and fully decoupled from execution**

The Visualization Layer must not introduce:

* simulation logic
* state mutation
* implicit recomputation

It must be a **pure replay system**.

---

## Architectural Principles

The implementation must follow these non-negotiable constraints:

### 1. Replay-Only System

All visualized states must be derived from persisted artifacts.

* No recomputation of transitions
* No inferred state
* No hidden logic

---

### 2. Deterministic Snapshot Model

The system operates on:

```
(step_index, phase) → snapshot
```

Where:

```
phase ∈ { BEFORE, AFTER_REGEN, AFTER_ACTION }
```

---

### 3. Single Source of Truth

A centralized **ViewerState** must control:

* current position (step + phase)
* playback state
* selection state

No UI component may maintain independent logical state.

---

### 4. Strict Separation of Concerns

The system must be layered as:

```
Data Access → Replay Logic → State Management → View Models → UI → CLI
```

No layer may bypass another.

---

### 5. Stateless Rendering

Rendering must be a pure function of ViewerState.

---

### 6. Read-Only Operation

The Visualization Layer must never modify:

* execution artifacts
* repository state

---

## Delivery Strategy

The Visualization Layer will be implemented through a sequence of **Visualization Work Packages (VWP)**.

Each package introduces a **well-defined architectural layer**.

The order is mandatory and must not be rearranged.

---

# Work Package Roadmap

## VWP1 – Replay Data Contract Validation and Artifact Access

### Objective

Provide reliable, validated access to persisted experiment artifacts.

### Responsibilities

* Load experiment, run, and episode data via repository
* Validate replay structure:

  * step ordering
  * required fields
  * phase availability
* Fail explicitly on invalid or incomplete artifacts

### Output

* Validated in-memory representation of episodes
* Strict validation layer for replay inputs

---

## VWP2 – Replay Snapshot Model and Resolver

### Objective

Implement deterministic resolution of replay states.

### Responsibilities

* Define replay coordinate system:

  ```
  (step_index, phase)
  ```
* Implement snapshot model
* Implement resolver:

  ```
  resolve(episode, step_index, phase) → snapshot
  ```
* Handle boundary conditions explicitly

### Output

* Deterministic snapshot resolution mechanism

---

## VWP3 – Viewer State Model

### Objective

Introduce a centralized state model as the single source of truth.

### Responsibilities

* Define `ViewerState`
* Include:

  * current step index
  * current phase
  * playback state
  * selection state
  * loaded episode context
* Implement state transitions as pure operations

### Output

* Fully controlled, explicit state model

---

## VWP4 – Playback and Navigation Controller

### Objective

Provide controlled time navigation and playback behavior.

### Responsibilities

* Step navigation:

  * next / previous
  * jump / seek
* Phase navigation:

  * cycle
  * direct selection
* Playback:

  * play / pause / stop
  * timer-driven progression
* Boundary enforcement

### Output

* Deterministic navigation and playback controller

---

## VWP5 – View Models for Rendering

### Objective

Bridge replay state to renderable structures.

### Responsibilities

* Map snapshot + ViewerState to:

  * grid representation
  * agent representation
  * dashboard data
  * detail panel data
* Keep UI-independent

### Output

* UI-ready, read-only view models

---

## VWP6 – Main Visualization Window and Static Rendering

### Objective

Introduce a functional desktop UI with static rendering.

### Responsibilities

* Implement PySide6 application
* Main window layout
* Grid visualization
* Agent rendering
* Always-visible metrics (e.g. energy)
* No interaction beyond basic display

### Output

* Working visualization UI (static)

---

## VWP7 – Interactive Inspection and Replay Controls

### Objective

Enable full interaction and inspection capabilities.

### Responsibilities

* Replay controls (playback UI)
* Step/phase navigation controls
* Entity selection:

  * cell
  * agent
* Detail panels
* Configuration and metadata inspection
* Debug overlays (optional, if stable)

### Output

* Fully interactive visualization tool

---

## VWP8 – CLI Integration and End-to-End Validation

### Objective

Integrate visualization into AXIS workflow and validate end-to-end behavior.

### Responsibilities

* CLI entry point:

  ```
  axis visualize --experiment-id ...
  ```
* Optional parameters:

  * run selection
  * episode selection
  * start position
* End-to-end tests
* Failure handling for invalid artifacts

### Output

* Operational visualization system integrated into CLI

---

# Execution Constraints

The following constraints apply across all VWPs:

### Determinism

Same artifacts must always produce identical visualization behavior.

---

### No Hidden State

All state must be explicit and inspectable.

---

### No Cross-Layer Leakage

Each VWP must respect architectural boundaries.

---

### Fail Fast

Invalid data must produce explicit errors.

---

### No Premature Optimization

Focus on correctness first.
Performance improvements may follow later.

---

# Final Outcome

After completing all VWPs, the system will provide:

* deterministic replay of experiments
* full inspection of agent and world state
* step-wise traceability of behavior
* a stable engineering tool for debugging and validation

---

