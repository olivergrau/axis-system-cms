# WP-3.5 Implementation Brief -- CLI Adaptation

> **Updated:** This spec has been updated to reflect the final implementation.
> Key changes from the original spec:
> - The baseline YAML example no longer includes `system.world_dynamics`.
>   Regeneration parameters belong in the `world:` section.
> - `BaseWorldConfig` uses `extra="allow"`, so world-specific fields
>   like `grid_width` pass through as extras.

## Context

We are implementing **Phase 3 -- Framework Alignment**. WP-3.1 through WP-3.4 provided the system registry, episode runner, executors, and persistence layer. This work package adapts the CLI to use the new framework components, making it system-agnostic.

### Predecessor State (After WP-3.4)

```
src/axis/
    framework/
        config.py            # ExperimentConfig (system_type, system: dict, 3-segment OFAT paths)
        registry.py          # register_system, create_system
        runner.py            # run_episode(), setup_episode()
        run.py               # RunExecutor, RunConfig, RunResult, RunSummary
        experiment.py        # ExperimentExecutor (with persistence + resume), resolve_run_configs
        persistence.py       # ExperimentRepository, statuses, metadata

Legacy (still intact):
    axis_system_a/
        cli.py               # Single-file CLI (584 lines), hardcoded to System A
```

The legacy CLI is a single file (`axis_system_a/cli.py`) that imports directly from `axis_system_a` types. It must be replaced with a CLI that routes through the framework's system-agnostic components.

### Architectural Decisions (Binding)

- **Q11 = Explicit registry**: System types resolved via registry
- **Q6 = Flat sections + opaque system dict**: Config files use the new `ExperimentConfig` format
- **Q13 = Clean break**: New CLI works with new config format only

### Reference Documents

- `docs/architecture/evolution/modular-architecture-roadmap.md` -- WP-3.5 definition
- `src/axis_system_a/cli.py` -- Legacy CLI (reference implementation)

---

## Objective

Implement a system-agnostic CLI that:

1. Mirrors the legacy command structure (`experiments list/run/resume/show`, `runs list/show`, `visualize`)
2. Uses the new `ExperimentConfig` (with `system_type` and `system: dict`)
3. Routes through the framework registry, executors, and repository
4. Never imports from `axis.systems.system_a` or any specific system package

---

## Scope

### 1. CLI Module (`axis/framework/cli.py`)

A single-file CLI following the same pattern as the legacy. Uses `argparse` for argument parsing, dispatches to handler functions.

#### Command Structure (unchanged from legacy)

```
axis experiments list              # List all experiments
axis experiments run <config>      # Run a new experiment
axis experiments resume <id>       # Resume a partial experiment
axis experiments show <id>         # Show experiment details

axis runs list --experiment <id>   # List runs in an experiment
axis runs show <id> --experiment <eid>  # Show run details

axis visualize --experiment <id> --run <rid> --episode <n>  # Launch visualization
```

#### Global Flags

- `--root <path>` (default `./experiments/results`) -- repository root
- `--output text|json` (default `text`) -- output format

#### Config File Format Change

The new `ExperimentConfig` format (JSON or YAML):

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
  obstacle_density: 0.0
system:
  agent:
    initial_energy: 50.0
    max_energy: 100.0
    buffer_capacity: 5
  policy:
    selection_mode: "sample"
    temperature: 1.0
    stay_suppression: 0.1
    consume_weight: 1.5
  transition:
    move_cost: 1.0
    consume_cost: 1.0
    stay_cost: 0.5
    max_consume: 1.0
    energy_gain_factor: 10.0
num_episodes_per_run: 5
```

**Key difference from legacy**: No nested `baseline: { ... SimulationConfig ... }`. Framework sections are flat at top level. System section is an opaque dict. `system_type` is explicit.

#### Config Loading

```python
def _load_config_file(path: Path) -> ExperimentConfig:
    """Load an ExperimentConfig from a JSON or YAML file."""
    text = path.read_text()
    if path.suffix in (".yaml", ".yml"):
        import yaml
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    return ExperimentConfig.model_validate(data)
```

Uses the new `axis.framework.config.ExperimentConfig` for validation.

### 2. Command Handlers

#### `experiments run`

```python
def _cmd_experiments_run(repo, args) -> int:
    config = _load_config_file(Path(args.config_path))

    if args.redo:
        experiment_id = config.name or ...
        experiment_dir = repo.experiment_dir(experiment_id)
        if experiment_dir.exists():
            shutil.rmtree(experiment_dir)

    result = ExperimentExecutor(repository=repo).execute(config)
    _print_experiment_result(result, args.output)
    return 0
```

Routes through framework `ExperimentExecutor` (not legacy). System resolution happens inside the executor via registry.

#### `experiments resume`

```python
def _cmd_experiments_resume(repo, args) -> int:
    result = ExperimentExecutor(repository=repo).resume(args.experiment_id)
    _print_experiment_result(result, args.output)
    return 0
```

The executor loads the persisted config (which includes `system_type`), resolves the system via registry, and resumes.

#### `experiments list`

```python
def _cmd_experiments_list(repo, args) -> int:
    experiments = repo.list_experiments()
    # Print each experiment_id with status and system_type from metadata
```

#### `experiments show`

```python
def _cmd_experiments_show(repo, args) -> int:
    config = repo.load_experiment_config(args.experiment_id)
    metadata = repo.load_experiment_metadata(args.experiment_id)
    status = repo.load_experiment_status(args.experiment_id)
    # Print experiment details including system_type
```

#### `runs list` / `runs show`

Same as legacy, but loads new-format `RunConfig` and `RunSummary` (vitality-based).

#### `visualize`

```python
def _cmd_visualize(repo, args) -> int:
    # Deferred to WP-4.x -- for now, print a message that visualization
    # will be available after Phase 4
    # OR: delegate to legacy visualization if available
```

**Design decision**: The `visualize` command is a **stub** in WP-3.5. It validates arguments and prints a placeholder message. Full visualization integration requires Phase 4 (WP-4.1 through WP-4.3). The legacy `visualize` command continues to work for legacy experiments.

**Rationale**: The visualization subsystem depends on `ReplayAccessService` which reads `EpisodeResult` (legacy type). Adapting it requires the visualization adapter pattern (WP-4.2) and System A visualization adapter (WP-4.3). Attempting to wire visualization now would force premature Phase 4 work.

### 3. Output Formatting

Two output modes: `text` (human-readable tables) and `json` (machine-readable).

**Text output**: Same style as legacy -- formatted strings with alignment.

**JSON output**: `json.dumps(data, indent=2)` with `model_dump(mode="json")`.

**Key change for `runs show`**: Shows `mean_final_vitality` instead of `mean_final_energy`. The label adapts based on what the summary contains.

### 4. Entry Point

```toml
# pyproject.toml -- update or add entry point
[project.scripts]
axis = "axis.framework.cli:main"
```

**Important**: The legacy entry point `axis = "axis_system_a.cli:main"` must be replaced. Both cannot coexist under the same name. The legacy CLI remains importable via `python -m axis_system_a.cli` but loses the `axis` console script.

**Alternative**: Keep `axis` pointing to the new CLI and add `axis-legacy` for the old one during the transition. But per Q13 (clean break), we simply replace it.

### 5. Example Config Files

Create updated example config files under `experiments/configs/v02/`:

```
experiments/configs/v02/baseline.yaml          # Single-run with new format
experiments/configs/v02/energy-gain-sweep.yaml  # OFAT with new 3-segment paths
```

These serve as documentation and test fixtures.

---

## Out of Scope

Do **not** implement any of the following in WP-3.5:

- Visualization integration (WP-4.x) -- `visualize` is a stub
- Interactive config construction from CLI arguments (users provide config files)
- Multiple system types per experiment
- Parallel run execution
- Config file generation/scaffolding commands

---

## Architectural Constraints

### 1. System-Agnostic Imports

The CLI module imports only from:
- `axis.framework.config` (ExperimentConfig)
- `axis.framework.experiment` (ExperimentExecutor)
- `axis.framework.persistence` (ExperimentRepository)
- `axis.framework.registry` (for system type validation, if needed)
- Standard library (`argparse`, `json`, `shutil`, `pathlib`)
- `pyyaml` (optional, for YAML config loading)

Never imports from `axis.systems.system_a` or `axis_system_a`.

### 2. System Registry Auto-Import

When the CLI is invoked, the system registry must have System A registered. Since `axis.framework.registry` auto-registers System A at import time (WP-3.1), this happens automatically when the executor imports the registry.

### 3. Error Handling

Same pattern as legacy:
- Missing config file: `FileNotFoundError` -> exit code 1
- Invalid config: `ValidationError` -> exit code 1
- Missing experiment for resume: clear error message -> exit code 1
- System type not registered: `KeyError` from registry -> exit code 1

### 4. Testability

`main(argv: list[str] | None = None)` accepts an argv list for testing without spawning subprocesses. Returns integer exit code.

---

## Expected File Structure

After WP-3.5, these files are **new**:

```
src/axis/framework/cli.py                       # NEW (CLI module)
tests/framework/test_cli.py                  # NEW (CLI tests)
experiments/configs/v02/baseline.yaml            # NEW (example config)
experiments/configs/v02/energy-gain-sweep.yaml   # NEW (example OFAT config)
```

These files are **modified**:

```
pyproject.toml                    # MODIFIED (update axis entry point)
src/axis/framework/__init__.py    # MODIFIED (optionally export main)
tests/test_scaffold.py        # MODIFIED (update framework exports if needed)
```

---

## Testing Requirements

### CLI Tests (`tests/framework/test_cli.py`)

Tests invoke `main(argv)` directly with `capsys` capture, following the legacy `tests/e2e/test_cli.py` pattern.

| Test | Description |
|------|-------------|
| `test_experiments_list_empty` | Empty repository -> "No experiments found" |
| `test_experiments_run_single` | Single-run config -> experiment completes |
| `test_experiments_run_ofat` | OFAT config -> multiple runs complete |
| `test_experiments_run_redo` | `--redo` flag deletes existing experiment |
| `test_experiments_run_missing_config` | Nonexistent config file -> exit code 1 |
| `test_experiments_run_invalid_config` | Malformed config -> exit code 1 |
| `test_experiments_resume` | Resume partial experiment |
| `test_experiments_resume_nonexistent` | Nonexistent experiment -> exit code 1 |
| `test_experiments_show` | Show completed experiment details |
| `test_experiments_show_json` | `--output json` produces valid JSON |
| `test_runs_list` | List runs in experiment |
| `test_runs_show` | Show run details with vitality metrics |
| `test_visualize_stub` | Visualize command prints placeholder message |
| `test_yaml_config` | YAML config file loading |
| `test_unknown_system_type` | Config with unregistered system -> exit code 1 |
| `test_end_to_end_workflow` | run -> show -> list runs -> show run |

All existing tests must continue to pass.

---

## Implementation Style

- Python 3.11+
- Single-file CLI module (same as legacy pattern)
- `argparse` for argument parsing
- `main(argv=None)` for testability
- Handler functions prefixed with `_cmd_`
- `yaml` import guarded (optional dependency)

---

## Expected Deliverable

1. CLI module at `src/axis/framework/cli.py`
2. Updated `pyproject.toml` entry point
3. Example config files under `experiments/configs/v02/`
4. CLI tests at `tests/framework/test_cli.py`
5. Updated `tests/test_scaffold.py` if needed
6. Confirmation that all tests pass
