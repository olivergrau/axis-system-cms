# 11. Key Domain Models and Contracts

## Foundation Types (`types.py`)

All frozen Pydantic `BaseModel` instances.

| Model | Fields | Role |
|-------|--------|------|
| `Position` | `x: int`, `y: int` | Grid coordinate. Part of World, NOT AgentState. |
| `CellObservation` | `traversability: float [0,1]`, `resource: float [0,1]` | Per-cell sensory vector |
| `Observation` | `current`, `up`, `down`, `left`, `right` (5 CellObservation) | Von Neumann neighborhood |
| `MemoryEntry` | `timestep: int >= 0`, `observation: Observation` | Single episodic record |
| `MemoryState` | `entries: tuple[MemoryEntry, ...]`, `capacity: int > 0` | Bounded FIFO buffer |
| `AgentState` | `energy: float >= 0`, `memory_state: MemoryState` | Internal agent state (no position) |

Utility: `clip_energy(energy, max_energy) -> float` clips to `[0, max_energy]`.

## World Model (`world.py`)

| Model | Fields | Role |
|-------|--------|------|
| `Cell` | `cell_type`, `resource_value [0,1]`, `regen_eligible` | Single grid cell (frozen) |
| `World` | `_grid`, `_agent_position`, `_width`, `_height` | Mutable world container |

## Execution Trace (`results.py`, `policy.py`, `transition.py`, `drives.py`)

| Model | Key Fields | Role |
|-------|------------|------|
| `HungerDriveOutput` | `activation [0,1]`, `action_contributions (6-tuple)` | Drive computation output |
| `DecisionTrace` | `raw_contributions`, `admissibility_mask`, `masked_contributions`, `probabilities`, `selected_action`, `temperature`, `selection_mode` | Full decision pipeline trace |
| `TransitionTrace` | `action`, positions (before/after), `moved`, `consumed`, `resource_consumed`, energies (before/after/delta), 3 world snapshots, 2 agent snapshots, memory states, observations, `regen_summary`, `termination_reason` | Full transition trace |
| `StepResult` | `timestep`, `observation`, `selected_action`, `drive_output`, `decision_result`, `transition_trace`, energies, `terminated` | Complete single-step record |
| `EpisodeSummary` | `survival_length`, `action_counts`, `total_consume_events`, `total_failed_consumes`, energy stats | Episode-level aggregates |
| `EpisodeResult` | `steps`, `total_steps`, `termination_reason`, `final_agent_state`, `final_position`, `final_observation`, `summary` | Complete episode record |

## Snapshot Types (`snapshots.py`)

| Model | Key Fields | Role |
|-------|------------|------|
| `WorldSnapshot` | `grid (nested tuples)`, `agent_position`, `width`, `height` | Immutable world state capture |
| `AgentSnapshot` | `energy`, `position`, `memory_entry_count`, `memory_timestep_range` | Immutable agent state capture |
| `RegenSummary` | `cells_updated`, `regen_rate` | Regen phase summary |

## Run and Experiment Models

| Model | Key Fields | Role |
|-------|------------|------|
| `RunConfig` | `simulation`, `num_episodes`, `base_seed`, `agent_start_position`, `run_id` | Per-run execution config |
| `RunSummary` | `num_episodes`, `mean_steps`, `std_steps`, `mean_final_energy`, `std_final_energy`, `death_rate`, consumption stats | Aggregate run stats |
| `RunResult` | `run_id`, `num_episodes`, `episode_results`, `summary`, `seeds`, `config` | Complete run record |
| `ExperimentConfig` | `experiment_type`, `baseline`, `name`, `base_seed`, `num_episodes_per_run`, `parameter_path`, `parameter_values` | Experiment definition |
| `ExperimentSummary` | `num_runs`, `run_entries (with deltas)` | Cross-run summary |
| `ExperimentResult` | `experiment_config`, `run_results`, `summary` | Complete experiment record |

## Repository Models (`repository.py`)

| Model | Role |
|-------|------|
| `ExperimentStatus` | Enum: `CREATED`, `RUNNING`, `COMPLETED`, `FAILED`, `PARTIAL` |
| `RunStatus` | Enum: `PENDING`, `RUNNING`, `COMPLETED`, `FAILED` |
| `ExperimentMetadata` | `experiment_id`, `created_at`, `experiment_type`, `name` |
| `RunMetadata` | `run_id`, `experiment_id`, `variation_description`, `created_at`, `base_seed` |
| `ExperimentStatusRecord` | Wrapper: `{"status": "..."}` serialization |
| `RunStatusRecord` | Wrapper: `{"status": "..."}` serialization |

## Visualization Models

| Model | Key Fields | Role |
|-------|------------|------|
| `ReplayPhase` | IntEnum: BEFORE=0, AFTER_REGEN=1, AFTER_ACTION=2 | Phase within a step |
| `ReplayCoordinate` | `step_index`, `phase` | Replay timeline position |
| `ReplaySnapshot` | Grid, agent position/energy, action context | World state at one point |
| `ViewerState` | `episode_handle`, `coordinate`, `playback_mode`, selections, overlay config | UI source of truth |
| `ViewerFrameViewModel` | `grid`, `agent`, `status`, `selection`, `action_context`, `debug_overlay`, `step_analysis` | Complete UI frame |
| `StepAnalysisViewModel` | All decision pipeline data (observation, drive, decision trace, outcome) | Decision readout |
| `DebugOverlayConfig` | `master_enabled`, 3 per-type booleans | Overlay toggle state |

## Key Design Contracts

1. **Agent/World separation**: `AgentState` contains no position. Position lives in `World`. This enforces the principle that the agent has no direct world access.

2. **Observation is the sole interface**: The agent (drive + policy) only receives `Observation`, never raw world state. All information flows through the sensor projection.

3. **Frozen models everywhere**: All value types, configs, results, traces, and view models are frozen Pydantic models. Only `World` is mutable.

4. **6-tuple convention**: Drive contributions, admissibility masks, probabilities, and masked contributions are all 6-element tuples indexed by `Action` enum order (UP=0, DOWN=1, LEFT=2, RIGHT=3, CONSUME=4, STAY=5).

5. **Three world snapshots per step**: `world_before`, `world_after_regen`, `world_after_action` provide complete auditability of each transition phase.

6. **Observation timing**: The observation used for decisions is the **pre-step** observation. The observation stored in memory is the **post-step** observation (after acting and regeneration).
