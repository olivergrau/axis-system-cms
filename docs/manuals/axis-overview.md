# AXIS -- Autonomous Experimentation Framework

**Version 0.2.0** | Python 3.11+

---

## What is AXIS?

AXIS is a modular experimentation framework for building, running, and
analyzing autonomous agents in grid-based environments. It provides the
full pipeline from experiment configuration to interactive visual replay,
with a clean separation between agent logic, environment dynamics, and
framework orchestration.

The framework is designed around a single principle: **agents, worlds,
and the framework itself should know nothing about each other's internals.**
This is enforced through protocol-based contracts, opaque agent state,
and adapter-driven visualization. The result is a system where new agent
architectures and new environment types can be developed, tested, and
visualized without modifying a single line of framework code.

---

## Core Architecture

AXIS separates concerns into three independent layers, with a reusable
component library available within the System layer:

```
+------------------------------------------------------+
|                    Framework Layer                    |
|  Experiment orchestration, episode execution loop,   |
|  configuration, persistence, CLI, visualization      |
+------------------------------------------------------+
        |                               |
  SystemInterface                MutableWorldProtocol
  (agent logic)                  (environment dynamics)
        |                               |
+------------------+          +--------------------+
|  System Layer    |          |   World Layer      |
|  Sensor, Drives, |          |   Grid topology,   |
|  Policy, State   |          |   Resources, Regen |
+--+---------------+          +--------------------+
   |
   | imports (composition, not inheritance)
   |
+--+-----------------------------+
|  System Construction Kit       |
|  Reusable building blocks:     |
|  Sensors, Drives, Policy,      |
|  Arbitration, Energy, Memory   |
+--------------------------------+
```

The **System Construction Kit** (`systems/construction_kit/`) provides
tested, reusable implementations of common system-internal mechanisms:
sensors, drives, policies, arbitration, energy utilities, and memory
structures. Concrete systems compose these components via plain Python
construction -- no inheritance hierarchies. Systems may also implement
their own components from scratch where the kit does not cover their
needs (e.g., System B implements its own policy and action handler).

All contracts are Python `Protocol` types (structural typing). There are
no abstract base classes and no inheritance hierarchies. A system is
anything that satisfies ``SystemInterface``; a world is anything that
satisfies ``MutableWorldProtocol``. The framework validates these
contracts at runtime.

### Key Design Decisions

- **Immutable data throughout.** All configuration, state snapshots, and
  trace data use Pydantic v2 frozen models. Nothing is mutated in place;
  variations produce new objects.
- **Deterministic by default.** All randomness flows through seeded
  NumPy generators. Every experiment is fully reproducible from its
  configuration.
- **Three-snapshot step traces.** Each step captures world state at three
  points (BEFORE, AFTER_REGEN, AFTER_ACTION), enabling detailed phase-by-phase
  replay in the visualization viewer.
- **Opaque agent state.** The framework never inspects agent internals.
  The only metric it reads is ``vitality()`` -- a normalized health value
  the system defines.

---

## Agent Systems

AXIS ships with three agent systems that demonstrate increasing levels
of cognitive complexity.

### System A -- Energy-Driven Forager

A reactive agent that senses its immediate neighborhood, evaluates
actions through a hunger drive, and selects behavior via softmax policy.

System A composes its pipeline from **System Construction Kit** components:

- **Sensor:** `VonNeumannSensor` (from `construction_kit.observation`) --
  Reads resource value and traversability for the current
  cell and four cardinal neighbors.
- **Hunger drive:** `HungerDrive` (from `construction_kit.drives`) --
  Single drive that scores actions based on resource
  availability and energy need. Activation rises as energy drops.
- **Policy:** `SoftmaxPolicy` (from `construction_kit.policy`) --
  Softmax selection over drive-produced action scores with
  configurable temperature. Supports both stochastic sampling and argmax
  modes.
- **Observation buffer:** `ObservationBuffer` (from `construction_kit.memory`) --
  Bounded FIFO ring buffer of recent observations,
  giving the agent short-term memory of what it has seen.
- **Config types:** `AgentConfig`, `PolicyConfig`, `TransitionConfig`
  (from `construction_kit.types`) -- shared configuration models.
- **Consume action:** `handle_consume` (from `construction_kit.types`) --
  custom action handler for resource extraction.
- **Actions:** move (4 directions), consume (extract resource from
  current cell), stay
- **Energy model:** Movement costs energy. Consuming resources gains
  energy. Episode terminates when energy reaches zero.

System A adds its own `SystemATransition` (energy update + buffer update +
termination check) and `AgentState` type.

### System A+W -- Dual-Drive Agent with Curiosity and World Model

Extends System A with a second drive (curiosity) and a spatial world
model, implementing a minimal motivational hierarchy. Like System A,
it composes components from the Construction Kit.

- **Everything from System A** (same kit components), plus:
- **Curiosity drive:** `CuriosityDrive` (from `construction_kit.drives`) --
  Scores actions by novelty -- a composite of
  spatial novelty (how often a neighboring cell has been visited) and
  sensory novelty (how different current observations are from past
  experience). Tunable alpha blending between the two signals.
- **Spatial world model:** `create_world_model`, `update_world_model`
  (from `construction_kit.memory`) -- Dead-reckoning visit-count map maintained
  in agent-relative coordinates. Tracks where the agent has been without
  requiring absolute position knowledge.
- **Dynamic drive arbitration:** `compute_maslow_weights`, `combine_drive_scores`
  (from `construction_kit.arbitration`) -- Maslow-like gating -- hunger suppresses
  curiosity when energy is low.
- **Reduction property:** When curiosity weight is set to zero, System
  A+W produces identical behavior to System A. This is verified by
  automated tests.

### System B -- Scout Agent

A minimal agent designed as an SDK reference implementation, demonstrating
how to build a custom system from scratch.

- **Actions:** move (4 directions), scan (senses a 3x3 neighborhood
  without consuming), stay
- **Policy:** Heuristic -- boosts scan action when no scan data exists;
  boosts movement toward resource-rich neighbors.
- **Purpose:** Demonstrates the system development API: custom action
  registration, action context, and visualization adapter integration.

### System C -- Predictive Action Modulation

System C extends System A with a prediction-based modulation factor
that learns action reliability from experience. Like System A, it
composes components from the Construction Kit.

- **Everything from System A** (same kit components), plus:
- **Predictive memory:** `PredictiveMemory` (from `construction_kit.prediction`) --
  Stores expected next-step features per (context, action) pair.
  Context is a 5-bit binary encoding of local resource availability.
- **Dual traces:** `TraceState`, `update_traces` (from `construction_kit.traces`) --
  Frustration and confidence traces that accumulate from signed
  prediction errors via asymmetric EMA learning.
- **Exponential modulation:** `compute_modulation`, `modulate_action_scores`
  (from `construction_kit.modulation`) -- Loss-averse exponential
  modulation that suppresses unreliable actions and reinforces
  positively surprising ones.
- **Reduction property:** When prediction sensitivities are zeroed
  (λ+ = λ- = 0), System C produces identical behavior to System A.
  This is verified by automated tests.

### Building Custom Systems

Any Python class that satisfies the ``SystemInterface`` protocol can be
registered as a new system type. The SDK provides:

- Protocol definitions for ``SystemInterface`` and optional sub-protocols
  (``SensorInterface``, ``DriveInterface``, ``PolicyInterface``,
  ``TransitionInterface``)
- Typed result containers (``DecideResult``, ``TransitionResult``,
  ``PolicyResult``)
- Custom action registration via ``action_handlers()``
- A system developer manual with step-by-step guidance

The **System Construction Kit** (`systems/construction_kit/`) provides
ready-to-use implementations of common components. New systems can
compose kit components (sensor, drives, policy, memory, energy utilities)
instead of building everything from scratch. See the system developer
manual for guidance on when and how to use kit components.

No framework code needs to be modified.

---

## Environments (Worlds)

Three world types are included, each with different spatial properties.

### Grid 2D -- Standard Rectangular Grid

Flat 2D grid with walls. Configurable obstacle density. Two resource
regeneration modes: ``all_traversable`` (resources appear on any open
cell) and ``sparse_fixed_ratio`` (fixed fraction of cells carry
resources).

### Toroidal -- Wraparound Grid

Same cell model as Grid 2D, but edges connect: walking off the right
side appears on the left; walking off the top appears on the bottom.
Creates environments with no dead-ends.

### Signal Landscape -- Dynamic Hotspot Fields

Grid with drifting Gaussian hotspots that produce signal values.
Resources are non-extractive -- the agent can sense but not consume them.
Hotspots move over time, creating a dynamic landscape. Designed for
sensor-based agents like System B.

### Building Custom Worlds

The world protocol is independent of any specific system. A custom world
needs to implement ``MutableWorldProtocol`` (cell access, agent position,
resource extraction, tick/regeneration, snapshots) and register with the
world registry. A world developer manual is included.

---

## Experiment Management

### Configuration

Experiments are defined in YAML (or JSON) config files with Pydantic v2
validation. The configuration has two layers:

- **Framework section:** Fixed schema covering execution parameters
  (max steps, episodes per run, seeds), world type and settings,
  and logging options.
- **System section:** Opaque dictionary passed directly to the system
  factory. The framework does not validate or interpret system parameters.

### Execution Modes

- **Single run:** One run with N episodes, all using the same configuration.
- **OFAT sweep:** One-factor-at-a-time parameter variation. Define a baseline
  and a list of parameter variations. AXIS generates one run per variation,
  each with independent seeds. Supports sweeping both framework parameters
  (e.g., ``framework.execution.max_steps``) and system parameters
  (e.g., ``system.policy.temperature``).

### Running Experiments

```
axis experiments run experiments/configs/system-a-baseline.yaml
axis experiments run experiments/configs/system-aw-curiosity-sweep.yaml
```

### Resuming Failed Experiments

If an experiment is interrupted, ``resume`` picks up where it left off:

```
axis experiments resume <experiment-id>
```

Only incomplete runs are re-executed. Completed runs are preserved.

### Inspecting Results

```
axis experiments list                              # all experiments
axis experiments show <experiment-id>              # summary with metrics
axis runs list <experiment-id>                     # runs within experiment
axis runs show <run-id> --experiment <eid>         # run-level metrics
```

All commands support ``--output json`` for scripted analysis.

---

## Data Persistence

All experiment data is persisted as structured JSON files in a
filesystem-based repository:

```
experiments/results/
  <experiment-id>/
    experiment_config.json      # full config snapshot
    experiment_metadata.json    # timestamps, system info
    experiment_summary.json     # aggregate metrics + OFAT deltas
    runs/
      <run-id>/
        run_config.json
        run_summary.json        # mean_steps, death_rate, ...
        episodes/
          episode_0001.json     # full step-by-step trace
          episode_0002.json
```

Every artifact is a Pydantic model serialized as JSON, loadable in Python
scripts and notebooks. Episode traces contain the complete execution
record: world snapshots at three phases per step, agent position and
vitality, and all system-specific decision data.

### Aggregate Metrics

- **Per run:** mean/std steps survived, mean/std final vitality, death rate
- **Per OFAT experiment:** delta calculations comparing each variation
  against the baseline (delta mean steps, delta mean final vitality,
  delta death rate)

---

## Interactive Visualization

AXIS includes a Qt-based replay viewer that renders recorded episodes
step-by-step with full system-specific decision overlays.

```
axis visualize --experiment <eid> --run <rid> --episode 1
```

### Viewer Layout

The viewer assembles a system-agnostic shell from adapter-contributed
parts:

| Panel | Content |
|-------|---------|
| **Replay Controls** | Step forward/backward, play/pause/stop, phase selector |
| **Status Bar** | Step count, phase name, playback mode, vitality |
| **Grid Canvas** | World grid with cell colors, agent marker, topology indicators, overlay graphics |
| **Step Analysis** | System-specific decision internals (monospace text panel) |
| **Overlay Panel** | Toggle checkboxes for overlay layers with legends |
| **Detail Panel** | Zoomed agent cell view + selected cell/agent info |

### System-Contributed Visualization

Each system type provides its own visualization content through an
adapter. The viewer does not contain any system-specific code.

**System A** contributes 6 analysis sections (step overview, observation,
observation buffer, drive output, decision pipeline, outcome) and 4
overlay types (action preference arrows, drive contribution bar chart,
consumption opportunity indicators, buffer saturation ring).

**System A+W** contributes 9 analysis sections (adding hunger drive,
curiosity drive, drive arbitration, and world model with ASCII visit map)
and 6 overlay types (adding visit count heatmap and novelty field arrows).

**System B** contributes 5 analysis sections and 2 overlay types (action
weight arrows and scan result circle).

**System C** contributes up to 7 analysis sections (adding prediction &
modulation and predictive update sections) and 5 overlay types (adding
modulated score bar chart and modulation factor display).

### Overlays

Overlays are semi-transparent graphical indicators drawn on top of the
grid. They make agent decision internals visible at a glance:

- **Directional arrows** -- action probabilities (length = probability,
  gold = selected action)
- **Bar charts** -- per-action drive contributions rendered inside the
  agent's cell (full labels in zoomed view)
- **Resource indicators** -- diamonds for resource at current cell, green
  dots for neighbor resources, red X for blocked neighbors
- **Heatmap** -- visit count coloring across explored cells (System A+W)
- **Novelty arrows** -- green-tinted directional novelty indicators
  (System A+W)
- **Saturation ring** -- color-coded observation buffer state (blue = low
  resource history, green = high, thickness = buffer fill)
- **Scan circle** -- dashed radius showing scan area with resource total
  (System B)

### Agent Cell Zoom

The detail panel includes a 150-pixel zoomed rendering of the agent's
cell with all overlays, making overlay details like bar chart labels and
arrow lengths easy to read even on dense grids.

### Scaling

The ``--scale`` flag uniformly scales the entire UI (fonts, buttons,
panels, grid) via Qt's scale factor mechanism.

---

## Extensibility

AXIS is built for extension at every layer. The plugin system discovers
extensions through two mechanisms:

1. **Setuptools entry points** -- `pip install axis-system-foo` automatically
   registers the package as a plugin. No config file edits needed.
2. **`axis-plugins.yaml`** -- lists plugin modules for local development
   and unpackaged systems.

Both sources feed registry-based factories with protocol validation:

| Extension Point | Register With | Protocol |
|-----------------|---------------|----------|
| New agent system | ``register_system()`` | ``SystemInterface`` |
| New world type | ``register_world()`` | ``MutableWorldProtocol`` |
| System visualization | ``register_system_visualization()`` | ``SystemVisualizationAdapter`` |
| World visualization | ``register_world_visualization()`` | ``WorldVisualizationAdapter`` |
| Comparison extension | ``register_extension()`` | ``ComparisonExtensionProtocol`` |
| Custom actions | ``action_handlers()`` | Handler function |

Each plugin package provides a `register()` function in its `__init__.py`.
The framework calls this function during startup to populate all registries.
Idempotency guards prevent conflicts when both discovery sources list the
same plugin.

### Packaging an External Plugin

```toml
# In your package's pyproject.toml:
[project.entry-points."axis.plugins"]
my_system = "my_package.my_system"
```

After `pip install`, the system is immediately available to the CLI
and visualizer. No framework source modifications required. Protocol
satisfaction is checked at runtime.

Developer manuals are included for both system development and world
development, covering the full development cycle from protocol
implementation through testing to visualization adapter integration.
Step-by-step tutorials walk through building System A and the Grid 2D
world from scratch.

---

## Testing

The project includes a comprehensive test suite with 1800+ tests
covering all layers:

- **Framework tests:** CLI, configuration parsing, experiment execution,
  OFAT integration, persistence, registry, runner, error handling
- **System tests:** Per-system unit and integration tests covering
  config, sensor, drives, policy, transition, pipeline, and
  visualization adapters. Includes mathematical worked examples and
  the System A+W reduction property verification.
- **Construction kit tests:** Component-level tests for all kit modules
  plus architectural dependency constraint tests that verify no
  cross-layer imports.
- **World tests:** Action dispatch, dynamics, topology (toroidal wrap,
  signal landscape drift)
- **Visualization tests:** Adapter protocols, overlay rendering, replay
  access/validation, UI panels, viewer state machine, end-to-end tests
  for all system+world combinations

---

## Included Experiment Configurations

Eight ready-to-run configurations ship with the framework:

| Config File | Description |
|-------------|-------------|
| ``system-a-baseline.yaml`` | Single-run baseline on 10x10 sparse grid |
| ``system-a-energy-gain-sweep.yaml`` | OFAT sweep over energy gain factor |
| ``system-a-toroidal-demo.yaml`` | System A on toroidal wraparound grid |
| ``system-aw-baseline.yaml`` | System A+W dual-drive baseline |
| ``system-aw-curiosity-sweep.yaml`` | OFAT sweep over curiosity strength |
| ``system-aw-exploration-demo.yaml`` | 20x20 exploration demo (high curiosity) |
| ``system-b-sdk-demo.yaml`` | System B scout on signal landscape |
| ``system-c-baseline.yaml`` | System C predictive modulation baseline |

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Data models | Pydantic v2 (frozen, validated) |
| Numerics | NumPy |
| Visualization | PySide6 (Qt 6) |
| Configuration | YAML / JSON |
| Persistence | Filesystem (structured JSON) |
| CLI | argparse |
| Testing | pytest |

---

## Summary

AXIS provides a complete, self-contained environment for autonomous agent
research. It supports the full experimental lifecycle:

1. **Design** an agent system by implementing a protocol.
2. **Configure** experiments in YAML with single-run or OFAT sweeps.
3. **Run** experiments from the CLI with deterministic reproducibility.
4. **Inspect** results via CLI queries or direct JSON access.
5. **Visualize** recorded episodes step-by-step with interactive overlays
   that reveal decision internals.
6. **Iterate** by adding new systems, worlds, or visualization adapters
   without touching framework code.

The framework is at version 0.2.0 and under active development.
