# 5. Experimentation Framework Architecture

## Layer Structure

```
ExperimentConfig (what to run)
        │
        v
ExperimentExecutor (orchestration + persistence)
        │
        ├── resolve_run_configs() ──► tuple[RunConfig, ...]
        │
        └── for each RunConfig:
                │
                v
            RunExecutor (multi-episode execution)
                │
                ├── resolve_episode_seeds()
                │
                └── for each seed:
                        │
                        v
                    create_world() + run_episode() ──► EpisodeResult
```

## Configuration Model (`config.py`)

All config models use `ConfigDict(frozen=True)`.

### SimulationConfig (top-level)

```
SimulationConfig
  ├── general: GeneralConfig     { seed: int }
  ├── world: WorldConfig         { grid_width, grid_height, resource_regen_rate,
  │                                obstacle_density, regeneration_mode, regen_eligible_ratio }
  ├── agent: AgentConfig         { initial_energy, max_energy, memory_capacity }
  ├── policy: PolicyConfig       { selection_mode, temperature, stay_suppression, consume_weight }
  ├── transition: TransitionConfig  { move_cost, consume_cost, stay_cost, max_consume,
  │                                   energy_gain_factor }
  ├── execution: ExecutionConfig { max_steps }
  └── logging: LoggingConfig     { enabled, console_enabled, jsonl_enabled, jsonl_path,
                                   include_decision_trace, include_transition_trace, verbosity }
```

### Key Validators

- `WorldConfig.check_sparse_ratio_required`: `regen_eligible_ratio` required when `regeneration_mode == SPARSE_FIXED_RATIO`
- `AgentConfig.check_energy_bounds`: `initial_energy <= max_energy`
- `LoggingConfig.check_jsonl_path_required`: `jsonl_path` required when `jsonl_enabled`

## Experiment Config (`experiment.py`)

### ExperimentConfig

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `experiment_type` | `ExperimentType` | required | `single_run` or `ofat` |
| `baseline` | `SimulationConfig` | required | Base configuration |
| `name` | `str \| None` | `None` | Experiment identifier (used as directory name) |
| `base_seed` | `int \| None` | `None` | Deterministic seed base |
| `num_episodes_per_run` | `int` | required | Episodes per run |
| `agent_start_position` | `Position` | `(0, 0)` | Agent starting cell |
| `parameter_path` | `str \| None` | `None` | OFAT: dot-path to varied parameter |
| `parameter_values` | `tuple[Any, ...] \| None` | `None` | OFAT: values to sweep |

### Experiment Types

**`single_run`**: One run with the baseline config. `parameter_path` and `parameter_values` must be `None`.

**`ofat`**: Multiple runs, each varying one parameter. For each value in `parameter_values`, `set_config_value(baseline, parameter_path, value)` produces a new `SimulationConfig`. Seeds are offset: `base_seed + i * 1000`.

### Parameter Addressing

The `set_config_value(config, path, value)` function supports dot-paths like `"transition.energy_gain_factor"`. It uses `model_copy(update={...})` on the section and top-level config, producing a new frozen instance without mutating the original.

Addressable sections: `general`, `world`, `agent`, `policy`, `transition`, `execution`, `logging`.

### Run Config Resolution

```python
resolve_run_configs(config: ExperimentConfig) -> tuple[RunConfig, ...]
```

- `single_run`: returns one `RunConfig` with `run_id="run-0000"`
- `ofat`: returns N configs, one per parameter value, with `run_id=f"run-{i:04d}"` and seed `base_seed + i * 1000`

## Run Execution (`run.py`)

### RunConfig

| Field | Type | Purpose |
|-------|------|---------|
| `simulation` | `SimulationConfig` | Per-run config (may have varied parameter) |
| `num_episodes` | `int` | Episode count |
| `base_seed` | `int \| None` | Seed base for episode seed derivation |
| `agent_start_position` | `Position` | Starting position |
| `run_id` | `str \| None` | Run identifier |

### Seed Resolution

```python
resolve_episode_seeds(num_episodes: int, base_seed: int | None) -> tuple[int, ...]
```

- Seeded: `(base_seed, base_seed+1, ..., base_seed+num_episodes-1)`
- Unseeded: draws from system entropy via `np.random.default_rng()`, captured in result for reproducibility

### RunExecutor.execute()

For each episode:
1. Create per-episode `SimulationConfig` with the episode's seed overriding `general.seed`
2. `create_world(config.simulation.world, agent_start_position, seed=seed)`
3. `run_episode(episode_config, world)` -> `EpisodeResult`

After all episodes: `compute_run_summary()` -> `RunSummary` with aggregate statistics (mean/std steps, mean/std energy, death rate, consumption stats).

## Experiment Execution (`experiment_executor.py`)

### ExperimentExecutor.execute()

```
1. experiment_id = config.name or uuid
2. Create experiment directory
3. Save config + metadata
4. Status: CREATED → RUNNING
5. resolve_run_configs(config)
6. For each run_config:
   a. Create run directory
   b. Save run config + metadata
   c. Status: PENDING → RUNNING
   d. RunExecutor.execute(run_config) → RunResult
   e. Persist: run_result, run_summary, episode files
   f. Status: COMPLETED
7. Compute experiment summary (with OFAT deltas if applicable)
8. Save experiment summary
9. Status: COMPLETED
```

### Summary Computation

`compute_experiment_summary()` builds `RunSummaryEntry` per run with:
- `variation_description`: `"baseline"` for single_run, `"param.path=value"` for OFAT
- `summary`: the run's `RunSummary`
- Delta fields (OFAT only): difference from first run's summary in `mean_steps`, `mean_final_energy`, `death_rate`

## Result Types

| Type | Contains | Level |
|------|----------|-------|
| `EpisodeResult` | Steps, final state, summary | Single episode |
| `RunSummary` | Aggregate stats over episodes | Single run |
| `RunResult` | All episode results + summary + seeds + config | Single run |
| `ExperimentSummary` | Run entries with deltas | Experiment |
| `ExperimentResult` | All run results + summary + config | Experiment |
