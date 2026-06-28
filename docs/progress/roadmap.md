# Roadmap

This roadmap is a living document. It does not lock the project into a rigid
sequence, but it records the current best ordering of work based on what is now
understood.

## Current Direction

The project is currently prioritizing world/system alignment over further
subsystem expansion.

The main reason is now explicit:

- the current explicit prediction subsystem has not shown robust value in the
  existing built-in world family
- the strongest interpretation is a world/system mismatch rather than a simple
  implementation failure
- neuralization is therefore postponed until an explicit subsystem has been
  shown to work in a well-matched setting

## Current Working Sequence

### 1. World-System Alignment

Current status: `active`

Immediate goal:

- understand why Prediction-A does not produce robust advantage in the existing
  built-in worlds
- classify current worlds into prediction-neutral, fragile, favorable, or misleading
- determine whether the current worlds, the current predictive subsystem, or both need revision

Current known outputs:

- prediction recap
- world-fit analysis
- world assessment matrix
- first major logbook entry on the mismatch

### 2. Refinement Options for Existing Worlds and Explicit Predictive Systems

Planned after the current analysis stabilizes.

Questions to answer:

- can the existing built-in worlds be improved so that Prediction-A gets a fairer test?
- is a Prediction-B system better suited to depletion, regrowth, and revisit-heavy worlds?
- which refinements are substantive, and which are only cosmetic?

Expected deliverables:

- world refinement options
- explicit predictor refinement options
- first-pass evaluation strategy

### 3. New World Classes for More Complex Behavioral Subsystems

Planned after the mismatch analysis produces clear design requirements.

Likely targets:

- stochastic local transition worlds
- deceptive local transition worlds
- richer partially hidden resource dynamics
- worlds with structured local unreliability rather than mere deterministic gradients

Rationale:

These world classes may be necessary if systems such as Prediction-A are to be
fairly evaluated.

### 4. Revisit Neural Submodules

Current status: `postponed`

Neural work should resume only when:

- at least one explicit predictive subsystem demonstrates real value in a
  clearly defined and well-matched world family
- the role of the predictor is conceptually stable enough that neuralization
  would extend a working subsystem rather than obscure a mismatch

## Near-Term Operational Priorities

```text
now
  -> continue World-System Alignment
  -> derive refinement options
  -> decide whether to adapt worlds, systems, or both first
later
  -> add fairer world classes for predictive subsystems
  -> revisit neural submodules only after explicit usefulness is established
```

## Not Yet Scheduled Rigidly

The following are intentionally left open until the current initiative yields
clearer answers:

- exact order of world redesign vs subsystem redesign
- whether Prediction-A should be refined or superseded by Prediction-B
- whether the next major implementation step should be in the worlds or the systems
- whether new world classes should be minimal variants or entirely new families
