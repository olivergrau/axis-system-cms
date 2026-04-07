# AXIS Configuration Reference Manual (v0.2.0)

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
| `experiment_type`      | string        | yes       | --               | `"single_run"` or `"ofat"`. See Section 7. |
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

### 3.2 `execution` -- Step budget

| Field       | Type           | Required | Description |
|-------------|----------------|----------|-------------|
| `max_steps` | integer (> 0)  | yes      | Maximum steps per episode. Episodes terminate after this many steps if the system hasn't terminated them first. |

```yaml
execution:
  max_steps: 200
```

An episode ends when either `max_steps` is reached (termination reason:
`"max_steps_reached"`) or the system signals termination (e.g.,
`"energy_depleted"` for System A).

### 3.3 `world` -- Grid structure

| Field              | Type               | Required | Default | Constraints |
|--------------------|--------------------|----------|---------|-------------|
| `grid_width`       | integer            | yes      | --      | > 0 |
| `grid_height`      | integer            | yes      | --      | > 0 |
| `obstacle_density` | float              | no       | `0.0`   | >= 0.0 and < 1.0 |

```yaml
world:
  grid_width: 10
  grid_height: 10
  obstacle_density: 0.1
```

The `world` section defines the physical grid. Obstacles are placed
randomly at initialization using the experiment seed.

**Important:** The `world` section only controls grid structure. Resource
regeneration parameters belong in the system-specific config (for
System A: `system.world_dynamics`). Placing regeneration fields under
`world` will cause a validation error. See Section 5.4 for details.

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
  world_dynamics: { ... }
```

If you register a custom system type, the `system` dict can contain
whatever fields your system factory expects.

---

## 5. System A configuration (`system_type: "system_a"`)

When `system_type` is `"system_a"`, the `system` dict is parsed into a
`SystemAConfig` with four sub-sections. All fields within each
sub-section are required unless a default is shown.

### 5.1 `system.agent` -- Agent initialization

| Field             | Type           | Required | Constraints | Description |
|-------------------|----------------|----------|-------------|-------------|
| `initial_energy`  | float          | yes      | > 0         | Starting energy at the beginning of each episode. |
| `max_energy`      | float          | yes      | > 0         | Maximum energy the agent can hold. Energy gains are capped at this value. |
| `memory_capacity` | integer        | yes      | > 0         | Number of recently visited cells the agent remembers. Affects action weighting. |

**Validation:** `initial_energy` must be <= `max_energy`.

```yaml
system:
  agent:
    initial_energy: 50.0
    max_energy: 100.0
    memory_capacity: 5
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
  samples stochastically. Lower temperature makes the distribution
  peakier (more deterministic); higher temperature makes it more uniform.

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

### 5.4 `system.world_dynamics` -- Resource regeneration

| Field                   | Type         | Required | Default             | Constraints | Description |
|-------------------------|--------------|----------|---------------------|-------------|-------------|
| `resource_regen_rate`   | float        | no       | `0.0`               | 0.0--1.0    | Per-step regeneration amount added to each eligible cell. |
| `regeneration_mode`     | string       | no       | `"all_traversable"` | see below   | Which cells can regenerate resources. |
| `regen_eligible_ratio`  | float or null| no       | `null`              | > 0 and <= 1.0 | Fraction of traversable cells that are eligible for regeneration. Required when mode is `"sparse_fixed_ratio"`. |

```yaml
system:
  world_dynamics:
    resource_regen_rate: 0.05
    regeneration_mode: "all_traversable"
```

#### Regeneration modes

- **`"all_traversable"`** (default) -- Every non-obstacle cell regenerates
  resources by `resource_regen_rate` per step. Simple and uniform.

- **`"sparse_fixed_ratio"`** -- Only a fixed fraction of traversable cells
  (determined by `regen_eligible_ratio`) can regenerate. The eligible
  cells are chosen randomly at world initialization using the experiment
  seed. This creates spatially uneven resource availability.

```yaml
# Sparse regeneration: only ~17% of traversable cells regenerate
system:
  world_dynamics:
    resource_regen_rate: 0.05
    regeneration_mode: "sparse_fixed_ratio"
    regen_eligible_ratio: 0.17
```

#### Common mistake: placing regeneration under `world`

The top-level `world` section only accepts `grid_width`, `grid_height`,
and `obstacle_density`. Regeneration parameters must go under
`system.world_dynamics`:

```yaml
# WRONG -- these fields are not recognized under world:
world:
  grid_width: 10
  grid_height: 10
  regeneration_mode: "sparse_fixed_ratio"    # ERROR
  regen_eligible_ratio: 0.17                 # ERROR

# CORRECT -- regeneration parameters go under system.world_dynamics:
world:
  grid_width: 10
  grid_height: 10

system:
  world_dynamics:
    resource_regen_rate: 0.05
    regeneration_mode: "sparse_fixed_ratio"
    regen_eligible_ratio: 0.17
```

This separation exists because regeneration behavior is system-specific.
Different system types may implement different regeneration strategies
(or none at all). The framework only manages the grid structure.

---

## 6. Complete field reference

### 6.1 All framework fields (system-agnostic)

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
| `logging.enabled`               | bool    | no       | `true`      |
| `logging.console_enabled`       | bool    | no       | `true`      |
| `logging.verbosity`             | string  | no       | `"compact"` |
| `logging.jsonl_enabled`         | bool    | no       | `false`     |
| `logging.jsonl_path`            | string  | no       | `null`      |
| `logging.include_decision_trace`| bool    | no       | `true`      |
| `logging.include_transition_trace`| bool  | no       | `true`      |
| `parameter_path`                 | string  | OFAT     | `null`      |
| `parameter_values`               | list    | OFAT     | `null`      |

### 6.2 All System A fields (`system_type: "system_a"`)

| Path                                     | Type   | Required | Default             |
|------------------------------------------|--------|----------|---------------------|
| `system.agent.initial_energy`            | float  | yes      | --                  |
| `system.agent.max_energy`               | float  | yes      | --                  |
| `system.agent.memory_capacity`          | int    | yes      | --                  |
| `system.policy.selection_mode`          | string | yes      | --                  |
| `system.policy.temperature`             | float  | yes      | --                  |
| `system.policy.stay_suppression`        | float  | yes      | --                  |
| `system.policy.consume_weight`          | float  | yes      | --                  |
| `system.transition.move_cost`           | float  | yes      | --                  |
| `system.transition.consume_cost`        | float  | yes      | --                  |
| `system.transition.stay_cost`           | float  | yes      | --                  |
| `system.transition.max_consume`         | float  | yes      | --                  |
| `system.transition.energy_gain_factor`  | float  | yes      | --                  |
| `system.world_dynamics.resource_regen_rate` | float | no   | `0.0`               |
| `system.world_dynamics.regeneration_mode`   | string | no  | `"all_traversable"` |
| `system.world_dynamics.regen_eligible_ratio`| float | conditional | `null`        |

---

## 7. OFAT experiments

### 7.1 How OFAT works

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

### 7.2 Parameter path format

Paths use 3 dot-separated segments: `<domain>.<section>.<field>`.

| Domain      | Addressable sections | Examples |
|-------------|----------------------|----------|
| `framework` | `general`, `execution`, `world`, `logging` | `framework.execution.max_steps`, `framework.world.grid_width` |
| `system`    | Any key in the `system` dict | `system.policy.temperature`, `system.transition.energy_gain_factor`, `system.world_dynamics.resource_regen_rate` |

### 7.3 Validation rules

- The path must have exactly 3 segments.
- The domain must be `"framework"` or `"system"`.
- For `framework` paths, the section must be one of: `general`,
  `execution`, `world`, `logging`.
- For `system` paths, the section must exist as a key in the `system` dict.

Invalid paths are rejected at config parsing time with a clear error
message.

### 7.4 Seed spacing

Each OFAT run gets an independent base seed:

| Run index | Base seed          |
|-----------|--------------------|
| 0         | `general.seed`     |
| 1         | `general.seed + 1000` |
| 2         | `general.seed + 2000` |
| n         | `general.seed + n * 1000` |

This ensures episodes across runs use independent random sequences.

### 7.5 OFAT examples

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
parameter_path: "system.world_dynamics.resource_regen_rate"
parameter_values: [0.0, 0.01, 0.05, 0.1, 0.2]
```

---

## 8. File formats: YAML and JSON

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
    memory_capacity: 5
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
      "memory_capacity": 5
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

## 9. Validation errors and troubleshooting

### 9.1 Common validation errors

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

### 9.2 Framework vs system ownership

The most common configuration mistake is placing system-specific fields
under a framework section (or vice versa). The ownership rules are:

| What | Owner | Config location |
|------|-------|-----------------|
| Grid dimensions (`grid_width`, `grid_height`) | Framework | `world:` |
| Obstacle density | Framework | `world:` |
| Resource regeneration | System | `system.world_dynamics:` |
| Agent energy parameters | System | `system.agent:` |
| Action selection strategy | System | `system.policy:` |
| Movement/consumption costs | System | `system.transition:` |
| Random seed | Framework | `general:` |
| Step budget | Framework | `execution:` |
| Console/file logging | Framework | `logging:` |

---

## 10. Shipped config files

The project includes two ready-to-use config files at
`experiments/configs/`:

### `baseline.yaml` -- Single-run experiment

Runs 5 episodes on a 10x10 grid with sparse regeneration. Suitable
as a starting point for custom experiments.

```
axis experiments run experiments/configs/baseline.yaml
```

### `energy-gain-sweep.yaml` -- OFAT experiment

Sweeps `system.transition.energy_gain_factor` across 4 values
(5.0, 10.0, 15.0, 20.0), producing 4 runs of 5 episodes each.

```
axis experiments run experiments/configs/energy-gain-sweep.yaml
```

To create a custom config, copy one of these files, modify the values
you want to change, and run it. See the CLI manual for details on
running, inspecting, and resuming experiments.
