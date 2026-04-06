# 4. Runtime Architecture

## Data Flow Overview

A single simulation step follows this pipeline:

```
┌─────────────────────────────────────────────────────────────────┐
│                     run_episode() loop                          │
│                                                                 │
│   Observation(t)                                                │
│       │                                                         │
│       ├──► compute_hunger_drive()  ──► HungerDriveOutput        │
│       │         activation + 6 action contributions             │
│       │                   │                                     │
│       │                   v                                     │
│       └──► select_action()  ──► DecisionTrace                   │
│                 mask → softmax → sample/argmax                  │
│                           │                                     │
│                           v                                     │
│             transition.step()  ──► TransitionStepResult          │
│               ┌───────────────────────────────┐                 │
│               │ Phase 1: World regeneration    │                 │
│               │ Phase 2: Action application    │                 │
│               │ Phase 3: New observation       │                 │
│               │ Phase 4: Energy update         │                 │
│               │ Phase 5: Memory update         │                 │
│               │ Phase 6: Termination check     │                 │
│               └───────────────────────────────┘                 │
│                           │                                     │
│                           v                                     │
│             StepResult (complete trace)                          │
│             New AgentState + Observation(t+1) ──► next step     │
└─────────────────────────────────────────────────────────────────┘
```

## World Model (`world.py`)

### Cell

Frozen Pydantic model representing a single grid cell.

| Field | Type | Constraints |
|-------|------|-------------|
| `cell_type` | `CellType` | `EMPTY`, `RESOURCE`, `OBSTACLE` |
| `resource_value` | `float` | `[0.0, 1.0]` |
| `regen_eligible` | `bool` | default `True`, forced `False` for obstacles |

Invariants enforced by model validator:
- `OBSTACLE` cells must have `resource_value == 0.0` and `regen_eligible` is auto-corrected to `False`
- `RESOURCE` cells must have `resource_value > 0.0`
- `EMPTY` cells must have `resource_value == 0.0`

Property `is_traversable` returns `cell_type != CellType.OBSTACLE`.

### World

Plain Python class (not a Pydantic model). The sole mutable container in the runtime.

- Constructor validates: non-empty grid, uniform row widths, agent position in bounds and traversable
- Methods: `get_cell()`, `set_cell()`, `is_within_bounds()`, `is_traversable()`, `is_regen_eligible()`
- `agent_position` property with setter (validates bounds and traversability)

### World Factory (`create_world`)

```python
create_world(config: WorldConfig, agent_position: Position,
             grid: list[list[Cell]] | None = None, *, seed: int | None = None) -> World
```

Pipeline:
1. If `grid is None`, creates an all-EMPTY grid of `config.grid_width x config.grid_height`
2. If `grid` is provided, validates dimensions against config
3. If `config.obstacle_density > 0`, calls `_apply_obstacles()` -- places obstacles deterministically using `np.random.default_rng(seed)`, excluding the agent's starting position
4. If `config.regeneration_mode == SPARSE_FIXED_RATIO`, calls `_apply_sparse_eligibility()` -- marks a deterministic subset of traversable cells as regen-eligible

Obstacle placement runs before sparse eligibility, so obstacle cells are correctly excluded from the eligible set.

## Observation Model (`observation.py`)

```python
build_observation(world: World, position: Position) -> Observation
```

Pure stateless projection. Samples the Von Neumann neighborhood (current + 4 cardinal neighbors):

- In-bounds cells: `traversability = 1.0 if traversable else 0.0`, `resource = cell.resource_value`
- Out-of-bounds cells: `traversability = 0.0, resource = 0.0`

Result is an `Observation` with five `CellObservation` fields (`current`, `up`, `down`, `left`, `right`). Can be flattened to a 10-element vector via `to_vector()`.

**Coordinate convention**: `up = (x, y-1)`, `down = (x, y+1)`, `left = (x-1, y)`, `right = (x+1, y)`.

## Memory Model (`memory.py`)

```python
update_memory(memory: MemoryState, observation: Observation, timestep: int) -> MemoryState
```

Pure function. Creates a `MemoryEntry(timestep, observation)`, appends to the entries tuple, and evicts the oldest if capacity is exceeded (FIFO). Returns a new `MemoryState` (no mutation).

Important: the observation stored in memory is the **post-action** observation (what the agent sees after acting), not the pre-action observation that drove the decision.

## Hunger Drive (`drives.py`)

```python
compute_hunger_drive(energy, max_energy, observation, consume_weight, stay_suppression)
    -> HungerDriveOutput
```

Produces:
- `activation = clamp(1 - energy/max_energy, 0, 1)` -- scalar hunger level, higher when energy is lower
- 6 action contributions indexed by `Action` enum order:
  - Movement (UP/DOWN/LEFT/RIGHT): `activation * neighbor_resource_value`
  - CONSUME: `activation * consume_weight * current_resource_value`
  - STAY: `-stay_suppression * activation` (always negative)

## Policy / Decision Pipeline (`policy.py`)

```python
select_action(contributions, observation, selection_mode, temperature, rng=None)
    -> DecisionTrace
```

Four-stage pipeline:

```
contributions (6 floats from drive)
        │
        v
[1] Admissibility Mask
    UP/DOWN/LEFT/RIGHT: admissible iff neighbor is traversable
    CONSUME: always admissible
    STAY: always admissible
        │
        v
[2] Masking (for trace)
    Non-admissible → -inf
        │
        v
[3] Softmax (numerically stable)
    P(a_i) = exp(β(s_i - s_max)) / Σ exp(β(s_j - s_max))
    where β = temperature, only over admissible actions
    Non-admissible actions get probability 0
        │
        v
[4] Action Selection
    ARGMAX: first index with max probability (deterministic tie-breaking)
    SAMPLE: rng.choice(6, p=probabilities) (stochastic)
```

The `DecisionTrace` captures all intermediate values: `raw_contributions`, `admissibility_mask`, `masked_contributions`, `probabilities`, `selected_action`, `temperature`, `selection_mode`.

## Transition Engine (`transition.py`)

```python
step(world, agent_state, action, timestep, *, max_energy, move_cost, consume_cost,
     stay_cost, max_consume, energy_gain_factor, resource_regen_rate=0.0,
     observation_before=None) -> TransitionStepResult
```

Six-phase pipeline:

| Phase | Operation | Mutations |
|-------|-----------|-----------|
| 1 | **Regeneration**: increment resource values on eligible cells by `regen_rate` | World grid mutated |
| 2 | **Action**: movement (update agent position), consumption (reduce cell resource), or stay (no-op) | World grid + position mutated |
| 3 | **Observation**: `build_observation()` from post-action world state | None (read-only) |
| 4 | **Energy**: `clip_energy(E - cost + gain_factor * consumed, max_energy)` | None (computed) |
| 5 | **Memory**: `update_memory()` with new observation and timestep | None (new AgentState) |
| 6 | **Termination**: `energy <= 0.0` triggers `ENERGY_DEPLETED` | None (flag) |

Three `WorldSnapshot` instances are captured per step (before, after-regen, after-action) plus two `AgentSnapshot` instances (before, after). These form the `TransitionTrace` -- the richest audit structure in the system.

### Action Cost Model

| Action | Cost |
|--------|------|
| UP, DOWN, LEFT, RIGHT | `move_cost` |
| CONSUME | `consume_cost` |
| STAY | `stay_cost` |

### Consumption Mechanics

- `delta_r = min(cell.resource_value, max_consume)`
- Cell resource reduced by `delta_r`; becomes EMPTY if fully consumed
- Energy gained: `energy_gain_factor * delta_r`
- CONSUME on a cell with `resource_value == 0` is a failed consume (no energy gain, cost still applies)

## Episode Runner (`runner.py`)

### `run_episode(config: SimulationConfig, world: World) -> EpisodeResult`

1. Initialize: `rng = np.random.default_rng(config.general.seed)`, create `AgentState`, build initial observation
2. Loop `for timestep in range(max_steps)`:
   - Call `episode_step()` which chains drive -> policy -> transition
   - Append `StepResult` to step list
   - If terminated, break (reason: `ENERGY_DEPLETED`)
3. If loop completes without break: reason = `MAX_STEPS_REACHED`
4. Compute `EpisodeSummary`, construct `EpisodeResult`

### `episode_step` -- The Orchestration Chain

```python
episode_step(world, agent_state, observation, timestep, config, rng)
    -> (AgentState, Observation, StepResult)
```

This single function chains the three core computations:
1. `compute_hunger_drive(...)` -> `HungerDriveOutput`
2. `select_action(drive_output.action_contributions, ...)` -> `DecisionTrace`
3. `transition.step(world, agent_state, decision_result.selected_action, ...)` -> `TransitionStepResult`

Returns the new agent state, new observation (for next step), and the complete `StepResult`.

## Result Structures (`results.py`)

### StepResult

Complete trace of one simulation step:

| Field | Source |
|-------|--------|
| `timestep` | Loop counter |
| `observation` | Pre-step observation (input to drive/policy) |
| `selected_action` | From DecisionTrace |
| `drive_output` | HungerDriveOutput |
| `decision_result` | DecisionTrace |
| `transition_trace` | TransitionTrace (with 3 world snapshots, 2 agent snapshots) |
| `energy_before`, `energy_after` | From transition |
| `terminated` | From transition |

### EpisodeSummary

Aggregate statistics: `survival_length`, `action_counts` (by name), `total_consume_events`, `total_failed_consumes`, `mean_energy`, `min_energy`, `max_energy`.

### EpisodeResult

Complete episode trace: `steps` tuple, `total_steps`, `termination_reason`, `final_agent_state`, `final_position`, `final_observation`, `summary`.

## Immutable Snapshots (`snapshots.py`)

- `WorldSnapshot`: frozen grid as nested tuples of `Cell`, plus agent position and dimensions
- `AgentSnapshot`: energy, position, memory entry count, memory timestep range
- `RegenSummary`: cells updated count and regen rate

`snapshot_world()` and `snapshot_agent()` capture the mutable world/agent state at a point in time. Called by `transition.step()` to produce before/after snapshots for the trace.
