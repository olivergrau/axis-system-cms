# AXIS Solution Overview

## Purpose

AXIS is a modular experimentation framework for building, running, comparing,
and visualizing autonomous agents in grid-based environments.

The architectural goal is to separate:

- system behavior
- world behavior
- framework execution/orchestration
- replay visualization

This separation allows multiple systems of increasing cognitive complexity to
run under the same experiment, persistence, comparison, and visualization
machinery.

## Mental Model

Think of the repository as five cooperating layers:

1. `sdk`
   Defines contracts and shared immutable types.
2. `framework`
   Executes experiments, runs, workspaces, persistence, CLI, and comparison.
3. `systems`
   Agent implementations such as `system_a`, `system_aw`, `system_c`.
4. `world`
   Environment implementations such as `grid_2d`, `toroidal`,
   `signal_landscape`.
5. `visualization`
   Replay-time adapter and UI layer for inspecting persisted traces.

## Core Execution Contract

The fundamental runtime contract is a two-phase step:

1. System decides an action from a read-only world view and opaque agent state.
2. Framework applies the action to the mutable world, then the system
   transitions its internal state from the resulting outcome.

This contract is defined by `SystemInterface` in
`src/axis/sdk/interfaces.py`.

The framework-owned episode loop is implemented in
`src/axis/framework/runner.py`.

Important consequence:

- systems do not mutate the world directly
- the framework does not inspect system internals except `vitality()`

## Key Design Principles

- Protocol-based boundaries instead of inheritance-heavy coupling
- Frozen Pydantic models for configs, traces, and results
- Deterministic seeded execution by default
- Replayable step traces with intermediate snapshots
- Visualization treated as an analysis tool, not only as a demo UI
- Workspaces treated as structured containers for investigations and
  development loops

## Major Built-In Systems

### System A

Baseline hunger-driven forager. Built from construction-kit components:

- `VonNeumannSensor`
- `HungerDrive`
- `SoftmaxPolicy`
- observation buffer memory

Primary role: baseline system and reference architecture.

## System A+W

Extends System A with:

- curiosity drive
- spatial world model
- dynamic arbitration between hunger and curiosity

Primary role: exploration-oriented system with a minimal motivational
hierarchy.

## System C

Extends System A with:

- predictive memory
- frustration/confidence traces
- action-score modulation based on prediction outcomes

Primary role: predictive modulation and comparison against the baseline.

## Distinctive Repository Capabilities

Beyond just running experiments, AXIS has three standout capabilities:

### Workspaces

Workspaces package configs, results, comparisons, notes, and execution state
 into one directory. This supports iterative investigation and development.

### Paired Trace Comparison

The comparison layer answers: "What changed when one system replaced another?"
It operates on persisted traces, not on live reruns.

### Interactive Replay Visualization

Visualization is built from replay artifacts plus system/world adapters,
allowing system-specific overlays and analysis while keeping the base viewer
generic.

## Architecture Evolution Note

The internal architecture history documents a transition from a single-system
codebase toward a modular framework. Some older internal design docs describe
planned constraints that the current implementation has already surpassed.

Example:

- older architecture notes said there would be no plugin system
- current code now includes plugin discovery and injectable catalogs via
  `src/axis/plugins.py` and `src/axis/framework/catalogs.py`

For current truth, prefer source code and public manuals over older roadmap
language.
