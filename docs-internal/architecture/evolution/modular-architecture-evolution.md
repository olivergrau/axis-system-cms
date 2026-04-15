# AXIS – Modular Architecture Evolution

## 1. Purpose

This document defines the next major evolution step of the AXIS project:

> Transition from a **single-system implementation (System A)** to a **modular, extensible framework** that supports multiple independent systems (A, A+W, …).

The goal is to establish a clean architectural foundation that enables:

* development of new systems without refactoring existing code
* separation of concerns between system logic and experimentation infrastructure
* long-term extensibility of the framework

This document serves as a **guiding reference for the next milestone**, not as a detailed implementation specification.

---

## 2. Motivation

The current implementation is centered around **System A (Baseline)** and tightly integrates:

* agent logic
* execution flow
* world interaction
* experimentation framework

While functional and well-structured, this approach has a fundamental limitation:

> It does not scale well to multiple system implementations.

Future development requires:

* adding new systems with different behaviors and internal structures
* evolving system complexity (e.g. world model, additional drives)
* running comparable experiments across systems

This requires a shift towards a **modular architecture with explicit contracts**.

---

## 3. Target Architecture Vision

The system will be restructured into clearly separated layers:

```
[ System SDK (Contracts & Interfaces) ]
              ↑
[ System Construction Kit (Reusable Components) ]
              ↑
[ System Implementations (A, A+W, ...) ]

[ Experimentation Framework ]
              ↑
[ Persistence Layer ]
              ↑
[ Visualization (Replay-based) ]
```

Additionally:

```
[ World Framework ]
        ↑
[ Systems interact via defined world interfaces ]
```

The **System Construction Kit** sits between the SDK and concrete
system implementations. It provides tested, reusable building blocks
(sensors, drives, policies, arbitration, energy utilities, memory
structures) that concrete systems compose via plain construction.
The kit depends only on the SDK; concrete systems import from both
the SDK and the kit but never from each other.

---

## 4. Core Architectural Principles

### 4.1 Separation of System and Execution

A **System** defines:

* agent
* policy
* drives
* transition logic
* sensor model

A System does **not** define:

* episode execution
* experiment orchestration
* persistence

Execution is fully handled by the **Experimentation Framework**.

---

### 4.2 Systems as Composable Units

A System is not a black box.

It is a **structured composition of components**, each defined via explicit interfaces:

* Agent
* Policy
* Drive(s)
* Transition Engine
* Sensor

This enables:

* inspection
* replacement of sub-components
* controlled evolution of system design

---

### 4.3 World as a Framework Concern

The **World** is owned by the framework.

Systems interact with the world only through defined interfaces.

Implications:

* consistent environment across systems
* controlled experimentation conditions
* possibility to introduce multiple world implementations later

---

### 4.4 Explicit System Contracts (SDK Approach)

All systems must implement a set of **well-defined interfaces (SDK)**.

These interfaces define:

* how systems receive observations
* how decisions are made
* how transitions are executed
* how traces are produced

No implicit behavior or duck typing is allowed.

---

### 4.5 Global Replay Contract

All systems must produce data compatible with a **global replay contract**.

This ensures:

* visualization works across all systems
* experiments are comparable
* trace analysis is standardized

---

### 4.6 Experiment Framework as Orchestrator

The Experimentation Framework is responsible for:

* execution of episodes
* sequencing of steps
* seed handling
* run and experiment management

It interacts with systems only through defined interfaces.

---

### 4.7 Visualization as Pure Consumer

The visualization layer:

* operates only on persisted data
* does not interact with live execution
* depends exclusively on the replay contract

This keeps visualization independent and stable.

---

## 5. Definition of a System

A System is defined as:

> A composition of components that maps:
>
> (current_state, observation) → (action, next_state, trace)

It includes:

* Agent state representation
* Sensor model
* Decision pipeline (policy + drives)
* Transition function

It excludes:

* world ownership
* execution loop
* persistence

---

## 6. Key Architectural Components

### 6.1 System SDK

Defines all interfaces required to implement a system:

* `AgentInterface`
* `PolicyInterface`
* `DriveInterface`
* `TransitionInterface`
* `SensorInterface`

Responsibilities:

* enforce structure
* enable plug-in systems
* provide development guidance

---

### 6.2 World Framework

Provides:

* standardized environment representation
* world state management
* interaction primitives

Responsibilities:

* ensure consistent simulation space
* expose controlled interaction API to systems

---

### 6.3 Experimentation Framework

Provides:

* execution loop (episodes, steps)
* experiment orchestration
* configuration handling
* result aggregation

Responsibilities:

* system-agnostic execution
* reproducibility
* statistical evaluation

---

### 6.4 Persistence Layer

Provides:

* storage of all artifacts
* structured experiment data
* replay-compatible traces

Responsibilities:

* immutability
* traceability
* reproducibility

---

### 6.5 Visualization Layer

Provides:

* replay-based inspection
* state visualization
* debugging support

Responsibilities:

* strict read-only behavior
* alignment with replay contract

---

## 7. High-Level Data Flow

```
Config
  ↓
Experiment Framework
  ↓
System (via SDK interfaces)
  ↓
World (via world interface)
  ↓
Transition + Trace
  ↓
Persistence
  ↓
Visualization (Replay)
```

---

## 8. Development Goals

### 8.1 Primary Goals

* Enable development of new systems without modifying framework code
* Introduce explicit, stable interfaces (SDK)
* Decouple execution from system implementation
* Standardize data contracts across systems

---

### 8.2 Secondary Goals

* Improve testability of individual components
* Enable comparative experiments across systems
* Prepare foundation for future complexity (e.g. world models)

---

## 9. Non-Goals (for this milestone)

* Full plugin system
* Dynamic runtime system loading
* Performance optimization
* Multi-agent systems
* Learning systems

---

## 10. Implementation Strategy (High-Level)

### Phase 1 – Interface Definition

* Define System SDK interfaces (Agent, Policy, Drive, Transition, Sensor)
* Define World interface
* Define minimal contracts required by Experiment Framework

---

### Phase 2 – Extraction

* Decouple System A implementation from current runtime
* Refactor System A to conform to SDK interfaces

---

### Phase 3 – Framework Alignment

* Adapt Experimentation Framework to operate purely via interfaces
* Remove direct dependencies on System A internals

---

### Phase 4 – Contract Stabilization

* Align replay contract with multi-system support
* Validate compatibility with visualization layer

---

### Phase 5 – Validation via Second System

* Implement a second system (e.g. System A+W)
* Validate extensibility assumptions

---

## 11. Success Criteria

This milestone is successful if:

* System A runs fully via SDK interfaces
* A second system can be implemented without modifying framework code
* Experiment execution is system-agnostic
* Replay data remains compatible with visualization
* No hidden coupling between system and framework remains

---

## 12. Guiding Principle

> Systems define behavior.
> Frameworks define execution.
> Contracts define integration.

The quality of the system will depend on how strictly this separation is maintained.
