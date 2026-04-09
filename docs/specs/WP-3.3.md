# WP-3.3 Implementation Brief -- Run and Experiment Executors

> **Updated:** This spec has been updated to reflect the final implementation.
> Key changes from the original spec:
> - `_run_single_episode` no longer extracts regen params from
>   `config.system_config["world_dynamics"]`. Regeneration is world-owned:
>   `World.tick()` handles dynamics internally.
> - `setup_episode()` no longer takes `regen_rate`, `regeneration_mode`,
>   or `regen_eligible_ratio` parameters. They are read from
>   `BaseWorldConfig` by the world factory.
> - `run_episode()` no longer takes a `regen_rate` parameter.

## Context

We are implementing **Phase 3 -- Framework Alignment** of the AXIS modular architecture evolution. WP-3.1 provided the system registry. WP-3.2 provided the framework-owned episode runner (`run_episode()`). This work package implements the system-agnostic **RunExecutor** and **ExperimentExecutor** that wire together registry lookup, world creation, episode execution, config resolution, and result aggregation.

### Predecessor State (After WP-3.2)

```
src/axis/
    sdk/
        interfaces.py       # SystemInterface (decide/transition/observe/action_handlers/etc.)
        types.py             # DecideResult, TransitionResult
        world_types.py       # WorldView, ActionOutcome, BaseWorldConfig
        trace.py             # BaseStepTrace, BaseEpisodeTrace
        snapshot.py          # WorldSnapshot, snapshot_world
    framework/
        config.py            # FrameworkConfig, ExperimentConfig, OFAT utilities
        registry.py          # register_system, create_system, registered_system_types
        runner.py            # run_episode(), setup_episode()
    world/
        factory.py           # create_world()
        actions.py           # ActionRegistry, create_action_registry()
        dynamics.py          # apply_regeneration()
        model.py             # World, Cell, CellType
    systems/system_a/
        system.py            # SystemA (implements SystemInterface)
        config.py            # SystemAConfig (agent, policy, transition, world_dynamics)
        ...
```

The framework has a registry, a runner, but no run/experiment executors. The legacy equivalents live in `axis_system_a.run` (RunExecutor/RunConfig/RunResult/RunSummary) and `axis_system_a.experiment_executor` (ExperimentExecutor) with `axis_system_a.experiment` (ExperimentConfig/resolve_run_configs/ExperimentResult/ExperimentSummary).

### Architectural Decisions (Binding)

- **Q6 = (C) Flat sections + opaque system dict**: `ExperimentConfig` already implemented in `axis/framework/config.py` with `system_type`, framework sections flat, `system: dict[str, Any]`
- **Q7 = (A) Prefixed 3-segment OFAT paths**: `parse_parameter_path()`, `get_config_value()`, `set_config_value()` already implemented for the new `ExperimentConfig`
- **Q11 = Explicit registry**: System resolved via `create_system(system_type, system_config)`
- **Q12 = Framework owns world structure**: `BaseWorldConfig` (grid_width, grid_height, obstacle_density) is framework-level; system owns dynamics (regen params in `system.world_dynamics`)
- **Q13 = Clean break**: No backward compatibility with legacy `SimulationConfig` / `RunConfig`

### Reference Documents

- `docs/architecture/evolution/modular-architecture-roadmap.md` -- WP-3.3 definition
- `src/axis_system_a/run.py` -- Legacy RunExecutor, RunConfig, RunResult, RunSummary
- `src/axis_system_a/experiment_executor.py` -- Legacy ExperimentExecutor
- `src/axis_system_a/experiment.py` -- Legacy ExperimentConfig, resolve_run_configs, ExperimentResult

---

## Objective

Implement system-agnostic run and experiment executors that:

1. **RunExecutor**: Executes N episodes under a shared config, aggregates results into a `RunSummary`, produces a `RunResult`
2. **ExperimentExecutor**: Resolves `ExperimentConfig` into run configs, delegates to `RunExecutor`, handles OFAT expansion
3. **Config resolution**: `resolve_run_configs()` expands the new `ExperimentConfig` into concrete `RunConfig` instances using 3-segment OFAT paths
4. **System-agnostic summaries**: `RunSummary` uses vitality (not energy) and drops System-A-specific metrics

---

## Scope

### 1. RunConfig (`axis/framework/run.py`)

A run config bundles all the information needed to execute N episodes under identical settings.

```python
class RunConfig(BaseModel):
    """Configuration for a multi-episode run."""
    model_config = ConfigDict(frozen=True)

    system_type: str
    system_config: dict[str, Any]         # Opaque system config dict
    framework_config: FrameworkConfig     # Framework settings (seed, steps, world, logging)
    num_episodes: int = Field(..., gt=0)
    base_seed: int | None = None
    agent_start_position: Position = Field(default_factory=lambda: Position(x=0, y=0))
    run_id: str | None = None
    description: str | None = None
```

**Key difference from legacy**: The legacy `RunConfig` wraps a monolithic `SimulationConfig`. The new one separates `system_config` (opaque dict) from `framework_config` (typed FrameworkConfig).

### 2. RunSummary and RunResult (`axis/framework/run.py`)

```python
class RunSummary(BaseModel):
    """Aggregated statistics for a run. System-agnostic."""
    model_config = ConfigDict(frozen=True)

    num_episodes: int = Field(..., ge=0)
    mean_steps: float
    std_steps: float = Field(..., ge=0.0)
    mean_final_vitality: float
    std_final_vitality: float = Field(..., ge=0.0)
    death_rate: float = Field(..., ge=0.0, le=1.0)
```

**Key change from legacy**: Replaces `mean_final_energy` / `std_final_energy` with `mean_final_vitality` / `std_final_vitality` (normalized [0, 1]). Removes System-A-specific `mean_consumption_count` / `std_consumption_count`. Uses vitality-based death detection (`final_vitality <= 0.0`).

```python
class RunResult(BaseModel):
    """Complete result of a multi-episode run."""
    model_config = ConfigDict(frozen=True)

    run_id: str
    num_episodes: int = Field(..., gt=0)
    episode_traces: tuple[BaseEpisodeTrace, ...]
    summary: RunSummary
    seeds: tuple[int, ...]
    config: RunConfig
```

**Key change from legacy**: Uses `episode_traces: tuple[BaseEpisodeTrace, ...]` instead of `episode_results: tuple[EpisodeResult, ...]`. The framework stores system-agnostic episode traces, not System-A-specific results.

### 3. RunExecutor (`axis/framework/run.py`)

```python
class RunExecutor:
    """Execute multiple episodes under a shared configuration."""

    def execute(self, config: RunConfig) -> RunResult:
        """Execute a complete run: N episodes, aggregate results."""
```

The executor:

1. Generates a `run_id` (UUID if not provided)
2. Derives episode seeds via `resolve_episode_seeds(num_episodes, base_seed)`
3. Creates the system via `create_system(config.system_type, config.system_config)` -- **once per run** (all episodes share the same system instance type, but state is reset per episode)
4. For each episode seed:
   a. Creates a fresh world via `setup_episode()` from WP-3.2 (world + registry)
   b. Runs `run_episode(system, world, registry, ...)` from WP-3.2
   c. Collects the `BaseEpisodeTrace`
5. Computes `RunSummary` from all traces via `compute_run_summary()`
6. Returns `RunResult`

**Episode seed derivation**: Uses `resolve_episode_seeds()` from the legacy pattern:
- If `base_seed` is provided: `seeds = (base_seed, base_seed + 1, ..., base_seed + N - 1)`
- If `base_seed` is `None`: random seeds from system entropy

**World creation per episode**: Each episode gets a fresh world created with its episode seed. The system's `world_dynamics` config section provides regen parameters for `setup_episode()`.

```python
def _run_single_episode(
    self,
    system: SystemInterface,
    config: RunConfig,
    episode_seed: int,
) -> BaseEpisodeTrace:
    """Run one episode and return its trace."""
    world, registry = setup_episode(
        system,
        config.framework_config.world,
        config.agent_start_position,
        seed=episode_seed,
    )

    return run_episode(
        system, world, registry,
        max_steps=config.framework_config.execution.max_steps,
        seed=episode_seed,
    )
```

### 4. compute_run_summary (`axis/framework/run.py`)

System-agnostic summary computation from episode traces.

```python
def compute_run_summary(
    episode_traces: tuple[BaseEpisodeTrace, ...],
) -> RunSummary:
    """Compute run-level summary from episode traces."""
    n = len(episode_traces)
    if n == 0:
        return RunSummary(
            num_episodes=0, mean_steps=0.0, std_steps=0.0,
            mean_final_vitality=0.0, std_final_vitality=0.0,
            death_rate=0.0,
        )

    steps = [t.total_steps for t in episode_traces]
    vitalities = [t.final_vitality for t in episode_traces]
    deaths = sum(1 for t in episode_traces if t.final_vitality <= 0.0)

    mean_s = sum(steps) / n
    mean_v = sum(vitalities) / n

    std_s = sqrt(sum((x - mean_s) ** 2 for x in steps) / n)
    std_v = sqrt(sum((x - mean_v) ** 2 for x in vitalities) / n)

    return RunSummary(
        num_episodes=n,
        mean_steps=mean_s, std_steps=std_s,
        mean_final_vitality=mean_v, std_final_vitality=std_v,
        death_rate=deaths / n,
    )
```

### 5. resolve_run_configs (`axis/framework/experiment.py`)

Expands an `ExperimentConfig` into concrete `RunConfig` instances.

```python
def resolve_run_configs(config: ExperimentConfig) -> tuple[RunConfig, ...]:
    """Expand an ExperimentConfig into concrete RunConfig instances."""
```

**For SINGLE_RUN**:
```python
def _resolve_single_run(config: ExperimentConfig) -> tuple[RunConfig, ...]:
    framework = extract_framework_config(config)
    return (
        RunConfig(
            system_type=config.system_type,
            system_config=dict(config.system),
            framework_config=framework,
            num_episodes=config.num_episodes_per_run,
            base_seed=config.general.seed,
            agent_start_position=config.agent_start_position,
            run_id="run-0000",
        ),
    )
```

**For OFAT**:
```python
def _resolve_ofat(config: ExperimentConfig) -> tuple[RunConfig, ...]:
    runs = []
    for i, value in enumerate(config.parameter_values):
        varied_config = set_config_value(config, config.parameter_path, value)
        varied_framework = extract_framework_config(varied_config)
        base_seed = config.general.seed + i * 1000

        runs.append(RunConfig(
            system_type=config.system_type,
            system_config=dict(varied_config.system),
            framework_config=varied_framework,
            num_episodes=config.num_episodes_per_run,
            base_seed=base_seed,
            agent_start_position=config.agent_start_position,
            run_id=f"run-{i:04d}",
            description=f"{config.parameter_path}={value}",
        ))
    return tuple(runs)
```

**Key change from legacy**: Uses the new `ExperimentConfig` (with `system_type`, `system: dict`, 3-segment OFAT paths) instead of the legacy `ExperimentConfig` (with `baseline: SimulationConfig`, 2-segment paths). The `set_config_value()` from `config.py` already handles both framework and system paths.

### 6. ExperimentExecutor (`axis/framework/experiment.py`)

The experiment executor wires together config resolution, run execution, and result aggregation. **No persistence in this WP** -- persistence is WP-3.4's concern.

```python
class ExperimentExecutor:
    """Orchestrate one complete experiment from config to results."""

    def __init__(self, run_executor: RunExecutor | None = None) -> None:
        self._run_executor = run_executor or RunExecutor()

    def execute(self, config: ExperimentConfig) -> ExperimentResult:
        """Execute a complete experiment."""
```

The executor:

1. Resolves run configs via `resolve_run_configs(config)`
2. Executes each run via `self._run_executor.execute(run_config)`
3. Computes `ExperimentSummary` from all run results
4. Returns `ExperimentResult`

### 7. ExperimentSummary and ExperimentResult (`axis/framework/experiment.py`)

```python
class RunSummaryEntry(BaseModel):
    """Per-run entry within an ExperimentSummary."""
    model_config = ConfigDict(frozen=True)

    run_id: str
    variation_description: str
    summary: RunSummary
    delta_mean_steps: float | None = None
    delta_mean_final_vitality: float | None = None
    delta_death_rate: float | None = None


class ExperimentSummary(BaseModel):
    """Aggregated summary across all runs."""
    model_config = ConfigDict(frozen=True)

    num_runs: int = Field(..., ge=0)
    run_entries: tuple[RunSummaryEntry, ...]


class ExperimentResult(BaseModel):
    """Complete result of an experiment."""
    model_config = ConfigDict(frozen=True)

    experiment_config: ExperimentConfig
    run_results: tuple[RunResult, ...]
    summary: ExperimentSummary
```

**Key change from legacy**: `RunSummaryEntry.delta_mean_final_energy` becomes `delta_mean_final_vitality`. Delta computation uses the same pattern: difference from baseline (first run in OFAT).

### 8. Variation Description

```python
def variation_description(config: ExperimentConfig, run_index: int) -> str:
    """Generate a human-readable description for a run."""
    if config.experiment_type == ExperimentType.SINGLE_RUN:
        return "baseline"
    assert config.parameter_path is not None
    assert config.parameter_values is not None
    return f"{config.parameter_path}={config.parameter_values[run_index]}"
```

### 9. resolve_episode_seeds (carried forward)

```python
def resolve_episode_seeds(
    num_episodes: int, base_seed: int | None,
) -> tuple[int, ...]:
    """Derive deterministic episode seeds from a base seed."""
    if base_seed is not None:
        return tuple(base_seed + i for i in range(num_episodes))
    rng = np.random.default_rng()
    return tuple(int(rng.integers(0, 2**31)) for _ in range(num_episodes))
```

---

## Out of Scope

Do **not** implement any of the following in WP-3.3:

- Persistence layer / ExperimentRepository (WP-3.4) -- the executor produces in-memory results only
- Resume functionality (WP-3.4 -- requires persistence)
- CLI (WP-3.5)
- Logging during run/experiment execution
- System-specific summary fields (consumption counts, etc.) -- these live in system_data within traces
- Multiple system types in one experiment

---

## Architectural Constraints

### 1. System-Agnostic

The run and experiment modules must **never** import from `axis.systems.system_a` or any specific system package. System resolution goes through the registry (`create_system()`).

### 2. No Persistence

Unlike the legacy `ExperimentExecutor` which is tightly coupled to `ExperimentRepository`, the new executor is a pure computation layer. It takes config, runs episodes, returns results. Persistence is layered on top in WP-3.4.

### 3. ExperimentConfig Already Exists

The new `ExperimentConfig` is already defined in `axis/framework/config.py` with all the features needed (`system_type`, `system: dict`, OFAT paths, etc.). WP-3.3 consumes it, does not redefine it.

### 4. FrameworkConfig Extraction

The `extract_framework_config()` function already exists. `RunConfig` stores a `FrameworkConfig` (not a full `ExperimentConfig`) because it's the minimal info needed to execute episodes.

### 5. World Owns Its Dynamics

Regeneration parameters are part of `BaseWorldConfig` and are handled internally by the world via `World.tick()`. The framework runner does not extract or pass regen parameters -- it simply calls `world.tick()` each step.

### 6. One System Per Experiment

An experiment uses a single `system_type`. All runs within an OFAT experiment use the same system. The OFAT parameter can vary either framework or system parameters, but not the system type itself.

---

## Expected File Structure

After WP-3.3, these files are **new**:

```
src/axis/framework/run.py                    # NEW (RunConfig, RunExecutor, RunResult, RunSummary)
src/axis/framework/experiment.py             # NEW (resolve_run_configs, ExperimentExecutor, ExperimentResult)
tests/framework/test_run.py              # NEW (run executor tests)
tests/framework/test_experiment.py       # NEW (experiment executor tests)
```

These files are **modified**:

```
src/axis/framework/__init__.py               # MODIFIED (add run + experiment exports)
tests/test_scaffold.py                   # MODIFIED (update framework exports)
```

---

## Testing Requirements

### Run Tests (`tests/framework/test_run.py`)

| Test | Description |
|------|-------------|
| `test_run_config_construction` | `RunConfig` builds from valid inputs |
| `test_run_config_frozen` | Cannot mutate fields |
| `test_resolve_episode_seeds_deterministic` | Same `base_seed` -> same seeds |
| `test_resolve_episode_seeds_sequential` | Seeds are `base_seed + i` |
| `test_resolve_episode_seeds_none` | `None` base_seed -> non-deterministic |
| `test_run_executor_returns_run_result` | `executor.execute()` returns `RunResult` |
| `test_run_result_episode_count` | `len(result.episode_traces) == num_episodes` |
| `test_run_result_seeds` | `len(result.seeds) == num_episodes` |
| `test_run_summary_mean_steps` | `summary.mean_steps > 0` |
| `test_run_summary_vitality_based` | `summary.mean_final_vitality` in `[0, 1]` |
| `test_run_summary_death_rate` | Death rate reflects terminated episodes |
| `test_run_deterministic` | Same config + seed -> identical RunResult |
| `test_run_executor_uses_registry` | System resolved via registry (tested indirectly) |
| `test_compute_run_summary_empty` | 0 episodes -> all-zero summary |

### Experiment Tests (`tests/framework/test_experiment.py`)

| Test | Description |
|------|-------------|
| `test_resolve_single_run` | SINGLE_RUN config -> 1 RunConfig |
| `test_resolve_ofat` | OFAT with 3 values -> 3 RunConfigs |
| `test_ofat_framework_path` | `"framework.execution.max_steps"` -> varied `RunConfig.framework_config` |
| `test_ofat_system_path` | `"system.policy.temperature"` -> varied `RunConfig.system_config` |
| `test_ofat_run_ids` | Run IDs are `"run-0000"`, `"run-0001"`, etc. |
| `test_ofat_seed_spacing` | Seeds spaced by 1000: `base_seed`, `base_seed + 1000`, ... |
| `test_variation_description_single` | Returns `"baseline"` for SINGLE_RUN |
| `test_variation_description_ofat` | Returns `"system.policy.temperature=2.0"` |
| `test_experiment_executor_single_run` | Full execution returns `ExperimentResult` |
| `test_experiment_executor_ofat` | OFAT execution with 2 values |
| `test_experiment_result_structure` | Has `experiment_config`, `run_results`, `summary` |
| `test_experiment_summary_num_runs` | `summary.num_runs` matches run count |
| `test_experiment_summary_deltas_ofat` | OFAT deltas computed relative to first run |
| `test_experiment_summary_no_deltas_single` | SINGLE_RUN has `None` deltas |

All existing tests must continue to pass.

---

## Implementation Style

- Python 3.11+
- Frozen Pydantic models for all data types
- `RunExecutor` is a class (matches legacy pattern, allows DI of dependencies)
- `ExperimentExecutor` is a class (same reason)
- `resolve_run_configs()` is a module-level function
- `compute_run_summary()` is a module-level function
- Tests use System A via registry (not direct import) to validate system-agnostic behavior
- Tests use the `FrameworkConfigBuilder` and `SystemAConfigBuilder` for config construction

---

## Expected Deliverable

1. Run module at `src/axis/framework/run.py`
2. Experiment module at `src/axis/framework/experiment.py`
3. Updated `src/axis/framework/__init__.py` with new exports
4. Updated `tests/test_scaffold.py`
5. Run tests at `tests/framework/test_run.py`
6. Experiment tests at `tests/framework/test_experiment.py`
7. Confirmation that all tests pass
