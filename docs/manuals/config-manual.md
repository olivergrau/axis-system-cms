# AXIS Configuration Reference Manual (v0.2.0)

> **Related manuals:**
> [CLI User Manual](cli-manual.md) |
> [Visualization Manual](visualization-manual.md) |
> [System Developer Manual](system-dev-manual.md) |
> [World Developer Manual](world-dev-manual.md)
>
> **Tutorials:**
> [Building a System](../tutorials/building-a-system.md) |
> [Building a World](../tutorials/building-a-world.md)

## Overview

Every experiment is defined by a single configuration file (YAML or JSON).
The v0.2.0 config format separates **framework-owned** settings from
**system-owned** settings, so the framework never needs to know the
internal structure of a system's configuration.

This manual documents every configurable field, its type, default,
constraints, and effect.

---

## 1. Architecture: two-layer configuration

A config file has two layers:

```
┌─────────────────────────────────────────────┐
│  Experiment-level fields                    │
│  system_type, experiment_type,              │
│  num_episodes_per_run, agent_start_position │
├─────────────────────────────────────────────┤
│  Framework sections (identical for all      │
│  system types)                              │
│  general, execution, world, logging         │
├─────────────────────────────────────────────┤
│  System section (opaque dict)               │
│  system: { ... }                            │
│  Structure depends on system_type.          │
│  The framework passes it through without    │
│  inspecting it.                             │
└─────────────────────────────────────────────┘
```

The framework validates its own sections (`general`, `execution`, `world`,
`logging`) using typed Pydantic models. The `system` dict is passed
verbatim to the registered system factory, which validates it internally.

This means:
- Framework sections have a **fixed schema** documented below.
- The `system` dict schema **depends on `system_type`**. This manual
  documents the schema for `system_type: "system_a"` in Section 5.

---

## 2. Experiment-level fields

These top-level fields control experiment identity, type, and structure.

| Field                  | Type          | Required  | Default          | Description |
|------------------------|---------------|-----------|------------------|-------------|
| `system_type`          | string        | yes       | --               | Registered system type (e.g. `"system_a"`). Determines which system implementation handles the `system` dict. |
| `experiment_type`      | string        | yes       | --               | `"single_run"` or `"ofat"`. See Section 8. |
| `num_episodes_per_run` | integer (> 0) | yes       | --               | Number of episodes per run. |
| `agent_start_position` | `{x, y}`     | no        | `{"x": 0, "y": 0}` | Grid position where the agent starts each episode. |

### OFAT-only fields

These are required when `experiment_type` is `"ofat"` and must be absent
(or null) when it is `"single_run"`.

| Field              | Type         | Required     | Description |
|--------------------|--------------|--------------|-------------|
| `parameter_path`   | string       | OFAT only    | 3-segment dot-path to the parameter to vary (see Section 7). |
| `parameter_values` | list (non-empty) | OFAT only | Values to sweep. Each value produces one run. |

### Validation rules

- `experiment_type: "single_run"` with `parameter_path` or
  `parameter_values` set raises `ValueError`.
- `experiment_type: "ofat"` with `parameter_path` or `parameter_values`
  missing or empty raises `ValueError`.

---

## 3. Framework sections

### 3.1 `general` -- Seed and reproducibility

| Field  | Type    | Required | Description |
|--------|---------|----------|-------------|
| `seed` | integer | yes      | Base random seed for deterministic execution. All episode seeds are derived from this value. |

```yaml
general:
  seed: 42
```

For OFAT experiments, each run receives a base seed spaced by 1000:
run 0 gets `seed`, run 1 gets `seed + 1000`, run 2 gets `seed + 2000`,
and so on. This ensures statistical independence between runs.

### 3.2 `execution` -- Runtime and trace policy

| Field              | Type           | Required | Default        | Description |
|--------------------|----------------|----------|----------------|-------------|
| `max_steps`        | integer (> 0)  | yes      | --             | Maximum steps per episode. Episodes terminate after this many steps if the system hasn't terminated them first. |
| `trace_mode`       | string         | no       | `"full"`       | Trace richness mode: `"full"`, `"delta"`, or `"light"`. |
| `parallelism_mode` | string         | no       | `"sequential"` | Parallelization strategy: `"sequential"`, `"episodes"`, or `"runs"`. |
| `max_workers`      | integer (>= 1) | no       | `1`            | Maximum worker count used by parallel execution modes. |

```yaml
execution:
  max_steps: 200
  trace_mode: "delta"
  parallelism_mode: "episodes"
  max_workers: 4
```

An episode ends when either `max_steps` is reached (termination reason:
`"max_steps_reached"`) or the system signals termination (e.g.,
`"energy_depleted"` for System A).

#### 3.2.1 Trace modes

- **`"full"`** -- Persist the richest replay artifacts. Best when you want the
  most detailed replay/debugging surface.

- **`"delta"`** -- Persist replay-compatible compact traces. This mode remains
  visualizable and replay-comparable, but typically uses less storage and
  runtime overhead than `full`.

- **`"light"`** -- Persist only summary-oriented outputs. This mode is the
  fastest option, but it is not replay-compatible. `light` executions cannot be
  visualized and cannot be used for replay-based comparison.

#### 3.2.2 Parallelization modes

- **`"sequential"`** -- Execute everything serially. Baseline behavior.

- **`"episodes"`** -- Parallelize episodes within a run. Good when one run has
  many episodes and the workload per episode is large enough to amortize worker
  overhead.

- **`"runs"`** -- Parallelize runs within an OFAT/sweep experiment. Intended
  for experiments with multiple independent runs.

#### 3.2.3 Practical guidance

- Use `full` when replay fidelity matters most.
- Use `delta` when you still want the visualizer or replay-based comparison,
  but want lower artifact cost.
- Use `light` when you only need summaries and throughput.
- Start with `max_workers` near your available CPU cores, then benchmark on
  your real workload.

#### 3.2.4 System C prediction modulation modes

`system_c` additionally supports multiple prediction modulation modes in its
own `system.prediction` section:

- `multiplicative` -- legacy behavior. Prediction only scales an existing
  drive score.
- `additive` -- prediction contributes a small bounded correction term and can
  therefore influence actions whose current drive score is `0`.
- `hybrid` -- combines reliability scaling with the bounded additive
  correction.

These modes are system-specific configuration, not framework-level execution
settings.

### 3.3 `world` -- Grid structure

| Field              | Type               | Required | Default | Constraints |
|--------------------|--------------------|----------|---------|-------------|
| `grid_width`       | integer            | yes      | --      | > 0 |
| `grid_height`      | integer            | yes      | --      | > 0 |
| `obstacle_density` | float              | no       | `0.0`   | >= 0.0 and < 1.0 |
| `resource_regen_rate` | float           | no       | `0.0`   | 0.0--1.0 |
| `resource_regen_cooldown_steps` | integer | no | `0` | >= 0 |
| `topology`         | string             | no       | `"bounded"` | `"bounded"` or `"toroidal"` |
| `regeneration_mode` | string            | no       | `"all_traversable"` | see Section 3.3.1 |
| `regen_eligible_ratio` | float or null  | no       | `null`  | > 0 and <= 1.0 |
| `world_type`       | string             | no       | `"grid_2d"` | Registered world type: `"grid_2d"`, `"toroidal"`, or `"signal_landscape"` |

```yaml
world:
  grid_width: 10
  grid_height: 10
  obstacle_density: 0.1
  resource_regen_rate: 0.05
  resource_regen_cooldown_steps: 0
  topology: "bounded"
```

The `world` section defines the physical grid and its dynamics.
Obstacles are placed randomly at initialization using the experiment
seed. Regeneration parameters control how resources recover over time
and are a property of the world, not the system.

`resource_regen_cooldown_steps` delays regeneration after a resource cell
is fully depleted. A value of `0` preserves the historical behavior:
eligible empty cells can begin regenerating on the next world tick.

`topology` controls boundary behavior for the default grid world.
`"bounded"` blocks movement and sensing at the edges. `"toroidal"`
wraps positions across opposite edges while keeping the same grid
geometry and cell semantics.

> **Architecture note:** At the SDK level, `BaseWorldConfig` is a minimal
> type with only `world_type: str` defined. All other fields (`grid_width`,
> `grid_height`, etc.) pass through as Pydantic extras via `extra="allow"`.
> The world factory for the `"grid_2d"` world type validates these extras
> against a typed `Grid2DWorldConfig`. Custom world types can define their
> own configuration fields.

#### 3.3.1 Regeneration modes

- **`"all_traversable"`** (default) -- Every non-obstacle cell regenerates
  resources by `resource_regen_rate` per step. Simple and uniform.

- **`"sparse_fixed_ratio"`** -- Only a fixed fraction of traversable cells
  (determined by `regen_eligible_ratio`) can regenerate. The eligible
  cells are chosen randomly at world initialization using the experiment
  seed. This creates spatially uneven resource availability.

#### 3.3.2 World type-specific fields

The fields above apply to the default `"grid_2d"` world type. Other
world types accept additional fields through the `BaseWorldConfig`
extras mechanism:

**`"grid_2d"`** -- Supports both bounded and wrapping grids through the
`topology` field. Use `topology: "bounded"` for the standard grid and
`topology: "toroidal"` for wraparound edges.

**`"toroidal"`** -- Legacy alias for a wrapping grid. Accepts the same
fields as `"grid_2d"` and behaves like `world_type: "grid_2d"` with
`topology: "toroidal"`.

**`"signal_landscape"`** -- A dynamic signal-based world with drifting
Gaussian hotspots. Accepts these additional fields:

| Field              | Type  | Default | Description |
|--------------------|-------|---------|-------------|
| `num_hotspots`     | int   | --      | Number of signal hotspots |
| `hotspot_radius`   | float | --      | Radius of each hotspot |
| `drift_speed`      | float | --      | How fast hotspots drift per tick |
| `decay_rate`       | float | --      | Signal decay rate |
| `signal_intensity` | float | --      | Peak signal intensity |

See the World Developer Manual for full details on each world type and
how to create custom world types.

### 3.4 `logging` -- Runtime observability

All logging fields are optional. If the `logging` section is omitted
entirely, defaults produce compact console output with no file logging.

| Field                      | Type    | Default     | Description |
|----------------------------|---------|-------------|-------------|
| `enabled`                  | bool    | `true`      | Master switch. `false` suppresses all logging. |
| `console_enabled`          | bool    | `true`      | Print step and episode output to the console. |
| `verbosity`                | string  | `"compact"` | `"compact"` or `"verbose"`. |
| `jsonl_enabled`            | bool    | `false`     | Write JSONL output to a file. |
| `jsonl_path`               | string  | `null`      | File path for JSONL output. **Required** when `jsonl_enabled` is `true`. |
| `include_decision_trace`   | bool    | `true`      | Include system decision trace in JSONL output. |
| `include_transition_trace` | bool    | `true`      | Include system transition trace in JSONL output. |

```yaml
# Silent operation (recommended for batch experiments)
logging:
  enabled: false
```

```yaml
# Full verbose logging with JSONL file output
logging:
  enabled: true
  console_enabled: true
  verbosity: "verbose"
  jsonl_enabled: true
  jsonl_path: "output/experiment.jsonl"
  include_decision_trace: true
  include_transition_trace: true
```

### Validation rules

- Setting `jsonl_enabled: true` without providing `jsonl_path` raises
  `ValueError`.
- `trace_mode` must be one of `"full"`, `"delta"`, or `"light"`.
- `parallelism_mode` must be one of `"sequential"`, `"episodes"`, or `"runs"`.
- `max_workers` must be at least `1`.

---

## 4. The `system` section

The `system` key holds a dictionary whose structure is defined by the
system implementation identified by `system_type`. The framework does
not inspect or validate this dictionary -- it passes it directly to the
system factory registered under `system_type`.

```yaml
system_type: "system_a"
system:
  agent: { ... }
  policy: { ... }
  transition: { ... }
```

If you register a custom system type, the `system` dict can contain
whatever fields your system factory expects.

> **System A+W:** When `system_type` is `"system_aw"`, the system
> section includes `curiosity` and `arbitration` sub-sections in
> addition to `agent`, `policy`, and `transition`. See the
> [System A+W Manual](system-aw-manual.md) for the full configuration
> reference.

---

## 5. System A configuration (`system_type: "system_a"`)

When `system_type` is `"system_a"`, the `system` dict is parsed into a
`SystemAConfig` with three sub-sections. All fields within each
sub-section are required unless a default is shown.

### 5.1 `system.agent` -- Agent initialization

| Field             | Type           | Required | Constraints | Description |
|-------------------|----------------|----------|-------------|-------------|
| `initial_energy`  | float          | yes      | > 0         | Starting energy at the beginning of each episode. |
| `max_energy`      | float          | yes      | > 0         | Maximum energy the agent can hold. Energy gains are capped at this value. |
| `buffer_capacity` | integer        | yes      | > 0         | Number of recently visited cells the agent remembers. Affects action weighting. |

**Validation:** `initial_energy` must be <= `max_energy`.

```yaml
system:
  agent:
    initial_energy: 50.0
    max_energy: 100.0
    buffer_capacity: 5
```

### 5.2 `system.policy` -- Action selection

| Field              | Type    | Required | Constraints | Description |
|--------------------|---------|----------|-------------|-------------|
| `selection_mode`   | string  | yes      | `"sample"` or `"argmax"` | Action selection strategy. |
| `temperature`      | float   | yes      | > 0         | Softmax temperature for probability distribution. Only used in `"sample"` mode. |
| `stay_suppression` | float   | yes      | >= 0        | Weight penalty applied to the "stay" action, discouraging idling. |
| `consume_weight`   | float   | yes      | > 0         | Weight bonus applied to "consume" when the agent is on a cell with resources. |

```yaml
system:
  policy:
    selection_mode: "sample"
    temperature: 1.0
    stay_suppression: 0.1
    consume_weight: 2.5
```

#### Selection modes explained

- **`"sample"`** -- Computes a softmax probability distribution over all
  6 actions (up, down, left, right, stay, consume) using temperature, then
  samples stochastically. Lower temperature flattens the distribution;
  higher temperature makes it sharper (more deterministic).

- **`"argmax"`** -- Always selects the action with the highest weight.
  Fully deterministic given the same state. The `temperature` field is
  ignored in this mode but must still be provided (set to any positive
  value).

### 5.3 `system.transition` -- Energy dynamics

| Field               | Type  | Required | Constraints | Description |
|---------------------|-------|----------|-------------|-------------|
| `move_cost`         | float | yes      | > 0         | Energy deducted per movement action (up/down/left/right). |
| `consume_cost`      | float | yes      | > 0         | Energy deducted when performing the "consume" action. |
| `stay_cost`         | float | yes      | >= 0        | Energy deducted for the "stay" action. Can be 0. |
| `max_consume`       | float | yes      | > 0         | Maximum resource fraction consumed per consume action (0.0--1.0 typical). |
| `energy_gain_factor`| float | yes      | >= 0        | Multiplier converting consumed resource value to energy gained. Energy gained = `resource_consumed * energy_gain_factor`. |

```yaml
system:
  transition:
    move_cost: 1.0
    consume_cost: 1.0
    stay_cost: 0.5
    max_consume: 1.0
    energy_gain_factor: 10.0
```

#### Energy flow per step

Each step:
1. The agent selects an action.
2. The action cost is deducted (`move_cost`, `consume_cost`, or
   `stay_cost` depending on the action).
3. If the action is "consume" and the cell has resources, the agent gains
   `min(resource_value, max_consume) * energy_gain_factor` energy (capped
   at `max_energy`).
4. If energy reaches 0, the episode terminates with reason
   `"energy_depleted"`.

---

## 6. System B configuration (`system_type: "system_b"`)

When `system_type` is `"system_b"`, the `system` dict is parsed into a
`SystemBConfig` with three sub-sections. System B is a "scout" agent
that replaces the `consume` action with a `scan` action for detecting
nearby resources without consuming them.

### 6.1 `system.agent` -- Agent initialization

| Field             | Type           | Required | Constraints | Description |
|-------------------|----------------|----------|-------------|-------------|
| `initial_energy`  | float          | yes      | > 0         | Starting energy at the beginning of each episode. |
| `max_energy`      | float          | yes      | > 0         | Maximum energy the agent can hold. |

**Validation:** `initial_energy` must be <= `max_energy`.

### 6.2 `system.policy` -- Action selection

| Field              | Type    | Required | Default    | Description |
|--------------------|---------|----------|------------|-------------|
| `selection_mode`   | string  | no       | `"sample"` | `"sample"` (stochastic) or `"argmax"` (deterministic). |
| `temperature`      | float   | no       | `1.0`      | Softmax temperature. Only used in `"sample"` mode. |
| `scan_bonus`       | float   | no       | `2.0`      | Weight bonus applied to the "scan" action when no prior scan data exists. |

### 6.3 `system.transition` -- Energy dynamics

| Field        | Type  | Required | Default | Description |
|--------------|-------|----------|---------|-------------|
| `move_cost`  | float | no       | `1.0`   | Energy deducted per movement action. |
| `scan_cost`  | float | no       | `0.5`   | Energy deducted when performing the "scan" action. |
| `stay_cost`  | float | no       | `0.5`   | Energy deducted for the "stay" action. |

System B has 6 actions: up, down, left, right, scan, stay. Unlike
System A, there is no `consume` action -- the agent gathers
information by scanning instead.

See the System Developer Manual for the full System B implementation
walkthrough.

---

## 7. Complete field reference

### 7.1 All framework fields (system-agnostic)

| Path                             | Type    | Required | Default     |
|----------------------------------|---------|----------|-------------|
| `system_type`                    | string  | yes      | --          |
| `experiment_type`                | string  | yes      | --          |
| `num_episodes_per_run`           | int     | yes      | --          |
| `agent_start_position.x`        | int     | no       | `0`         |
| `agent_start_position.y`        | int     | no       | `0`         |
| `general.seed`                   | int     | yes      | --          |
| `execution.max_steps`            | int     | yes      | --          |
| `world.grid_width`              | int     | yes      | --          |
| `world.grid_height`             | int     | yes      | --          |
| `world.obstacle_density`        | float   | no       | `0.0`       |
| `world.resource_regen_rate`     | float   | no       | `0.0`       |
| `world.regeneration_mode`       | string  | no       | `"all_traversable"` |
| `world.regen_eligible_ratio`    | float   | no       | `null`      |
| `world.world_type`              | string  | no       | `"grid_2d"` |
| `logging.enabled`               | bool    | no       | `true`      |
| `logging.console_enabled`       | bool    | no       | `true`      |
| `logging.verbosity`             | string  | no       | `"compact"` |
| `logging.jsonl_enabled`         | bool    | no       | `false`     |
| `logging.jsonl_path`            | string  | no       | `null`      |
| `logging.include_decision_trace`| bool    | no       | `true`      |
| `logging.include_transition_trace`| bool  | no       | `true`      |
| `parameter_path`                 | string  | OFAT     | `null`      |
| `parameter_values`               | list    | OFAT     | `null`      |

### 7.2 All System A fields (`system_type: "system_a"`)

| Path                                     | Type   | Required | Default             |
|------------------------------------------|--------|----------|---------------------|
| `system.agent.initial_energy`            | float  | yes      | --                  |
| `system.agent.max_energy`               | float  | yes      | --                  |
| `system.agent.buffer_capacity`          | int    | yes      | --                  |
| `system.policy.selection_mode`          | string | yes      | --                  |
| `system.policy.temperature`             | float  | yes      | --                  |
| `system.policy.stay_suppression`        | float  | yes      | --                  |
| `system.policy.consume_weight`          | float  | yes      | --                  |
| `system.transition.move_cost`           | float  | yes      | --                  |
| `system.transition.consume_cost`        | float  | yes      | --                  |
| `system.transition.stay_cost`           | float  | yes      | --                  |
| `system.transition.max_consume`         | float  | yes      | --                  |
| `system.transition.energy_gain_factor`  | float  | yes      | --                  |

---

## 8. OFAT experiments

### 8.1 How OFAT works

An OFAT (One-Factor-At-a-Time) experiment varies a single parameter
across a list of values. Each value produces one independent run, while
all other parameters remain at their baseline values from the config.

```yaml
experiment_type: "ofat"
parameter_path: "system.policy.temperature"
parameter_values: [0.1, 0.5, 1.0, 2.0, 5.0]
```

This produces 5 runs. The experiment summary includes delta values
comparing each run to the first run (baseline).

### 8.2 Parameter path format

Paths use 3 dot-separated segments: `<domain>.<section>.<field>`.

| Domain      | Addressable sections | Examples |
|-------------|----------------------|----------|
| `framework` | `general`, `execution`, `world`, `logging` | `framework.execution.max_steps`, `framework.world.grid_width`, `framework.world.resource_regen_rate` |
| `system`    | Any key in the `system` dict | `system.policy.temperature`, `system.transition.energy_gain_factor` |

### 8.3 Validation rules

- The path must have exactly 3 segments.
- The domain must be `"framework"` or `"system"`.
- For `framework` paths, the section must be one of: `general`,
  `execution`, `world`, `logging`.
- For `system` paths, the section must exist as a key in the `system` dict.

Invalid paths are rejected at config parsing time with a clear error
message.

### 8.4 Seed spacing

Each OFAT run gets an independent base seed:

| Run index | Base seed          |
|-----------|--------------------|
| 0         | `general.seed`     |
| 1         | `general.seed + 1000` |
| 2         | `general.seed + 2000` |
| n         | `general.seed + n * 1000` |

This ensures episodes across runs use independent random sequences.

### 8.5 OFAT examples

**Sweep a framework parameter (max steps):**

```yaml
experiment_type: "ofat"
parameter_path: "framework.execution.max_steps"
parameter_values: [50, 100, 200, 500]
```

**Sweep a system parameter (energy gain factor):**

```yaml
experiment_type: "ofat"
parameter_path: "system.transition.energy_gain_factor"
parameter_values: [5.0, 10.0, 15.0, 20.0]
```

**Sweep regeneration rate:**

```yaml
experiment_type: "ofat"
parameter_path: "framework.world.resource_regen_rate"
parameter_values: [0.0, 0.01, 0.05, 0.1, 0.2]
```

---

## 9. File formats: YAML and JSON

Both YAML and JSON are supported. The CLI detects the format by file
extension: `.yaml` or `.yml` for YAML, anything else is treated as JSON.

### YAML (recommended for hand-editing)

```yaml
system_type: "system_a"
experiment_type: "single_run"

general:
  seed: 42
execution:
  max_steps: 200
world:
  grid_width: 10
  grid_height: 10
num_episodes_per_run: 5

system:
  agent:
    initial_energy: 50.0
    max_energy: 100.0
    buffer_capacity: 5
  policy:
    selection_mode: "sample"
    temperature: 1.0
    stay_suppression: 0.1
    consume_weight: 2.5
  transition:
    move_cost: 1.0
    consume_cost: 1.0
    stay_cost: 0.5
    max_consume: 1.0
    energy_gain_factor: 10.0
```

### JSON equivalent

```json
{
  "system_type": "system_a",
  "experiment_type": "single_run",
  "general": { "seed": 42 },
  "execution": { "max_steps": 200 },
  "world": { "grid_width": 10, "grid_height": 10 },
  "num_episodes_per_run": 5,
  "system": {
    "agent": {
      "initial_energy": 50.0,
      "max_energy": 100.0,
      "buffer_capacity": 5
    },
    "policy": {
      "selection_mode": "sample",
      "temperature": 1.0,
      "stay_suppression": 0.1,
      "consume_weight": 2.5
    },
    "transition": {
      "move_cost": 1.0,
      "consume_cost": 1.0,
      "stay_cost": 0.5,
      "max_consume": 1.0,
      "energy_gain_factor": 10.0
    }
  }
}
```

---

## 10. Validation errors and troubleshooting

### 10.1 Common validation errors

| Error | Cause | Fix |
|-------|-------|-----|
| `initial_energy must be <= max_energy` | `initial_energy` exceeds `max_energy` in `system.agent` | Increase `max_energy` or decrease `initial_energy`. |
| `parameter_path and parameter_values are required for ofat` | `experiment_type: "ofat"` without OFAT fields | Add `parameter_path` and `parameter_values`. |
| `parameter_path and parameter_values must be None for single_run` | OFAT fields present in a `single_run` config | Remove `parameter_path` and `parameter_values`. |
| `parameter_values must be non-empty for ofat` | Empty `parameter_values: []` | Add at least one value to sweep. |
| `Parameter path must have exactly 3 segments` | Path like `"temperature"` or `"system.policy"` | Use full 3-segment path: `"system.policy.temperature"`. |
| `Parameter path domain must be 'framework' or 'system'` | Path starts with an invalid domain | Use `framework.` or `system.` prefix. |
| `Invalid framework section` | Path like `"framework.agent.energy"` | `agent` is not a framework section. Use `system.agent.initial_energy`. |
| `jsonl_path must be set when jsonl_enabled is True` | JSONL enabled without file path | Set `jsonl_path` or disable `jsonl_enabled`. |
| `Field required` (Pydantic) | A required field is missing | Add the missing field to the config. |
| `Input should be greater than 0` (Pydantic) | A field constrained to > 0 received 0 or negative | Use a positive value. |

### 10.2 Framework vs system ownership

The most common configuration mistake is placing system-specific fields
under a framework section (or vice versa). The ownership rules are:

| What | Owner | Config location |
|------|-------|-----------------|
| Grid dimensions (`grid_width`, `grid_height`) | Framework | `world:` |
| Obstacle density | Framework | `world:` |
| Resource regeneration | Framework | `world:` |
| Agent energy parameters | System | `system.agent:` |
| Action selection strategy | System | `system.policy:` |
| Movement/consumption costs | System | `system.transition:` |
| Random seed | Framework | `general:` |
| Step budget | Framework | `execution:` |
| Console/file logging | Framework | `logging:` |

---

## 11. Shipped config files

The project includes four ready-to-use config files at
`experiments/configs/`:

### `system-a-baseline.yaml` -- Single-run experiment

Runs 5 episodes on a 10x10 grid with sparse regeneration. Suitable
as a starting point for custom experiments.

```
axis experiments run experiments/configs/system-a-baseline.yaml
```

### `system-a-energy-gain-sweep.yaml` -- OFAT experiment

Sweeps `system.transition.energy_gain_factor` across 4 values
(5.0, 10.0, 15.0, 20.0), producing 4 runs of 5 episodes each.

```
axis experiments run experiments/configs/system-a-energy-gain-sweep.yaml
```

### `system-b-sdk-demo.yaml` -- System B SDK demo

System B SDK demo with signal landscape world. Runs 5 episodes with
the scout agent on a signal-based world.

```
axis experiments run experiments/configs/system-b-sdk-demo.yaml
```

### `system-a-toroidal-demo.yaml` -- Toroidal grid demo

System A on a toroidal (wraparound) grid world. Runs 5 episodes on a
10x10 toroidal grid with 5% obstacles and 3% regeneration.

```
axis experiments run experiments/configs/system-a-toroidal-demo.yaml
```

### `system-aw-exploration-demo.yaml` -- System A+W exploration demo

System A+W dual-drive agent on a 20x20 grid with sparse regeneration.
Runs 3 episodes with curiosity-driven exploration and Maslow-like
drive arbitration. See the [System A+W Manual](system-aw-manual.md)
for parameter details.

```
axis experiments run experiments/configs/system-aw-exploration-demo.yaml
```

To create a custom config, copy one of these files, modify the values
you want to change, and run it. See the CLI Manual for details on
running, inspecting, and resuming experiments. See the System Developer
Manual for building custom system types and the World Developer Manual
for creating custom world types.
