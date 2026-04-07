# 10. Execution and Data Flow

## End-to-End Flow

This section traces the complete lifecycle from config file to inspectable results.

### Step 1: Config File

An experiment config file (JSON or YAML) defines:
- `experiment_type`: `single_run` or `ofat`
- `baseline`: complete `SimulationConfig` with all runtime parameters
- `parameter_path` + `parameter_values`: the parameter to sweep (OFAT only)
- `num_episodes_per_run`, `base_seed`, `agent_start_position`

Example (OFAT):
```json
{
  "experiment_type": "ofat",
  "name": "energy-gain-sweep",
  "base_seed": 42,
  "num_episodes_per_run": 10,
  "parameter_path": "transition.energy_gain_factor",
  "parameter_values": [5.0, 10.0, 20.0],
  "baseline": { ... }
}
```

### Step 2: Experiment Execution

```
CLI: axis experiments run energy-gain-sweep.json
  │
  v
_load_config_file("energy-gain-sweep.json") → ExperimentConfig
  │
  v
ExperimentExecutor(repository).execute(config)
  │
  ├── experiment_id = "energy-gain-sweep"
  ├── repo.create_experiment_dir("energy-gain-sweep")
  ├── repo.save_experiment_config(...)
  ├── repo.save_experiment_metadata(...)
  ├── repo.save_experiment_status(CREATED)
  ├── repo.save_experiment_status(RUNNING)
  │
  ├── resolve_run_configs(config)
  │     → [RunConfig(run_id="run-0000", seed=42,    energy_gain_factor=5.0),
  │        RunConfig(run_id="run-0001", seed=1042,   energy_gain_factor=10.0),
  │        RunConfig(run_id="run-0002", seed=2042,   energy_gain_factor=20.0)]
  │
  └── for each RunConfig: _execute_and_persist_run(...)
```

### Step 3: Run Execution

```
_execute_and_persist_run("energy-gain-sweep", run_config, config, index)
  │
  ├── repo.create_run_dir(...)
  ├── repo.save_run_config(...)
  ├── repo.save_run_metadata(variation_description="transition.energy_gain_factor=10.0")
  ├── repo.save_run_status(PENDING)
  ├── repo.save_run_status(RUNNING)
  │
  ├── RunExecutor().execute(run_config)
  │     │
  │     ├── resolve_episode_seeds(10, 1042)
  │     │     → (1042, 1043, 1044, ..., 1051)
  │     │
  │     └── for each seed: ──────────────────────── [Step 4]
  │
  ├── repo.save_run_result(...)
  ├── repo.save_run_summary(...)
  ├── repo.save_episode_result(..., episode_index=1..10)
  └── repo.save_run_status(COMPLETED)
```

### Step 4: Episode Execution

```
For seed=1042:
  │
  ├── _make_episode_config(simulation, seed=1042)
  │     → SimulationConfig with general.seed=1042
  │
  ├── create_world(config.world, agent_start_position=(0,0), seed=1042)
  │     ├── Create 10x10 EMPTY grid
  │     ├── _apply_obstacles(grid, config, position, seed)  [if density > 0]
  │     └── _apply_sparse_eligibility(grid, config, seed)   [if sparse mode]
  │     → World (mutable)
  │
  └── run_episode(episode_config, world)
        │
        ├── rng = np.random.default_rng(1042)
        ├── agent_state = AgentState(energy=50.0, memory=empty)
        ├── observation = build_observation(world, (0,0))
        ├── logger = AxisLogger(config.logging)
        │
        ├── for timestep in range(200):  ──────── [Step 5]
        │     │
        │     ├── episode_step(world, agent_state, observation, timestep, config, rng)
        │     │     → (new_agent_state, new_observation, StepResult)
        │     │
        │     ├── logger.log_step(step_result)
        │     │
        │     └── if step_result.terminated: break (ENERGY_DEPLETED)
        │
        ├── else: termination_reason = MAX_STEPS_REACHED
        │
        ├── compute_episode_summary(steps)
        └── → EpisodeResult
```

### Step 5: Single Step Execution

```
episode_step(world, agent_state, observation, timestep, config, rng)
  │
  │  [1] DRIVE
  ├── compute_hunger_drive(energy=agent_state.energy, max_energy=100.0,
  │       observation, consume_weight=1.5, stay_suppression=0.1)
  │   → HungerDriveOutput {
  │       activation: 0.5,
  │       action_contributions: (0.15, 0.0, 0.03, 0.07, 0.52, -0.05)
  │     }
  │
  │  [2] POLICY
  ├── select_action(contributions=(0.15, 0.0, 0.03, 0.07, 0.52, -0.05),
  │       observation, mode=SAMPLE, temperature=1.0, rng)
  │   ├── admissibility_mask: (True, False, True, True, True, True)
  │   ├── masked_contributions: (0.15, -inf, 0.03, 0.07, 0.52, -0.05)
  │   ├── probabilities: (0.17, 0.00, 0.15, 0.16, 0.37, 0.14)
  │   └── selected_action: CONSUME (sampled)
  │   → DecisionTrace
  │
  │  [3] TRANSITION
  └── transition.step(world, agent_state, CONSUME, timestep, ...)
      ├── snapshot_world(world)  [before]
      ├── Phase 1: _apply_regeneration(world, regen_rate)
      ├── snapshot_world(world)  [after_regen]
      ├── Phase 2: _apply_consume(world, max_consume=1.0) → (True, 0.7)
      ├── snapshot_world(world)  [after_action]
      ├── Phase 3: build_observation(world, agent_position) → new Observation
      ├── Phase 4: energy = clip(50.0 - 1.0 + 10.0*0.7, 100.0) = 56.0
      ├── Phase 5: update_memory(memory, new_observation, timestep)
      ├── Phase 6: terminated = (56.0 <= 0.0) → False
      │
      → TransitionStepResult {
          agent_state: AgentState(energy=56.0, memory=...),
          observation: Observation(...),
          terminated: False,
          trace: TransitionTrace(...)  [3 world snapshots, 2 agent snapshots]
        }
```

### Step 6: Persistence

After all episodes complete:
```
RunResult persisted:
  ├── run_result.json           Complete RunResult with all 10 EpisodeResults
  ├── run_summary.json          Aggregate: mean_steps, death_rate, etc.
  └── episodes/
      ├── episode_0001.json     Individual EpisodeResult
      ├── episode_0002.json
      └── ...

After all runs complete:
  └── experiment_summary.json   Cross-run summary with OFAT deltas
```

### Step 7: Resume

```
CLI: axis experiments resume energy-gain-sweep
  │
  ├── Load ExperimentConfig from experiment_config.json
  ├── Re-resolve RunConfigs (deterministic → same 3 runs)
  ├── run-0000: is_run_complete? → True (skip)
  ├── run-0001: is_run_complete? → False (status=FAILED)
  │     └── Re-execute from scratch → RunResult
  ├── run-0002: is_run_complete? → True (skip)
  └── Recompute experiment summary
```

### Step 8: Inspection

```
CLI: axis experiments show energy-gain-sweep --output json
  → experiment_config.json + experiment_metadata.json + experiment_summary.json

CLI: axis runs show run-0001 --experiment energy-gain-sweep
  → run_config.json + run_metadata.json + run_summary.json + episode count

CLI: axis visualize --experiment energy-gain-sweep --run run-0001 --episode 1
  → Interactive PySide6 viewer for episode 1 of run-0001
  → Step-by-step replay with phase granularity
  → Decision analysis panel showing probabilities, contributions, etc.
```
