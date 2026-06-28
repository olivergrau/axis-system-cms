# Documentation Vault Operations Plan

## Objective

Restructure the public `docs/` area into a more operational vault that supports:

1. thematic initiative work
2. historical logbook-style reporting
3. progress tracking and planning

This plan was approved before implementation and serves as the working reference
for the restructuring.

## Target Structure

```text
docs/
  initiatives/
  logbook/
  progress/
```

### Initiatives

Thematic, longer-running research and engineering strands.

Current intended initiatives:

- Neural Submodules in AXIS
- World-System Alignment

### Logbook

Chronological, blog-like records of findings, decisions, failures, and major
course corrections.

### Progress

Operational overview of active initiatives, completed initiatives, decisions,
postponements, and roadmap state.

## Naming and Roles

- `Initiatives` = thematic depth
- `Logbook` = historical chronology
- `Progress` = operational overview

## Initiative Cleanup Requirement

`Neural Submodules in AXIS` should only retain neural-relevant documents:

- Initial Draft
- Online Learning and Immediate Use
- Stabilization Principles
- Manual vs Neural Predictor in System C and C+W
- PyTorch Integration Architecture

Prediction-system analysis documents should move into a dedicated initiative:

- World-System Alignment

Moved documents:

- Prediction System Recap
- Prediction System World-Fit Analysis
- Prediction System World Assessment Matrix

## Metadata Conventions

### Initiative pages

Each initiative should expose a clear status block including:

- status
- phase
- objective
- current assessment
- next step
- tags
- last updated

### Logbook entries

Each logbook entry should include:

- date
- title
- tags
- related initiatives
- context
- findings
- consequences
- next questions

### Progress pages

Progress documents should emphasize compact operational tables and explicit
status snapshots.

## Initial Priority Work

1. create public `logbook/` and `progress/` sections
2. create initiative `World-System Alignment`
3. clean up `Neural Submodules in AXIS`
4. wire the new structure into MkDocs navigation
5. prepare the vault for later logbook and progress population

## Phases

### Phase 1

- create structure and navigation
- add base index and placeholder pages for `logbook/` and `progress/`
- create `World-System Alignment` initiative shell

### Phase 2

- move prediction-analysis documents out of the neural initiative
- update initiative indexes
- add status framing to both current initiatives

### Later Phases

- write first major logbook entry on prediction/world mismatch
- populate progress tracking pages
- reconstruct selected historical entries from git/docs

