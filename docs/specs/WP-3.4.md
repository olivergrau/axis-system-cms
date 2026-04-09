# WP-3.4 Implementation Brief -- Persistence Layer Adaptation

## Context

We are implementing **Phase 3 -- Framework Alignment** of the AXIS modular architecture evolution. WP-3.3 provided system-agnostic `RunExecutor` and `ExperimentExecutor` that produce in-memory results (`RunResult`, `ExperimentResult`). This work package adapts the persistence layer (`ExperimentRepository`) to work with the new framework types and integrates it with the experiment executor to enable persistence and resume.

### Predecessor State (After WP-3.3)

```
src/axis/
    framework/
        config.py            # ExperimentConfig (system_type, system: dict, framework sections)
        registry.py          # System registry
        runner.py            # run_episode(), setup_episode()
        run.py               # RunConfig, RunExecutor, RunResult, RunSummary (vitality-based)
        experiment.py        # resolve_run_configs, ExperimentExecutor, ExperimentResult

    sdk/
        trace.py             # BaseStepTrace, BaseEpisodeTrace

Legacy (still intact):
    axis_system_a/
        repository.py        # ExperimentRepository (works with legacy types)
        experiment_executor.py  # Legacy ExperimentExecutor with persistence + resume
```

The new `ExperimentExecutor` (WP-3.3) is a pure computation layer with no persistence. The legacy `ExperimentRepository` serializes legacy types (`SimulationConfig`, `RunConfig` with `simulation: SimulationConfig`, `EpisodeResult`, etc.). We need a repository that serializes the new framework types.

### Architectural Decisions (Binding)

- **Q13 = Clean break**: No need to read/write legacy artifact formats
- **Q8 = Base trace + system_data**: All persisted episode data uses `BaseStepTrace` / `BaseEpisodeTrace`
- Directory layout and immutable/mutable artifact semantics are **stability boundaries** (carry forward from legacy)

### Reference Documents

- `docs/architecture/evolution/modular-architecture-roadmap.md` -- WP-3.4 definition
- `src/axis_system_a/repository.py` -- Legacy repository (reference implementation)
- `src/axis_system_a/experiment_executor.py` -- Legacy persistence integration pattern

---

## Objective

1. **Adapt `ExperimentRepository`** to serialize/deserialize the new framework types (`ExperimentConfig`, `RunConfig`, `RunResult`, `RunSummary`, `BaseEpisodeTrace`, `ExperimentResult`, `ExperimentSummary`)
2. **Integrate persistence into `ExperimentExecutor`** with execute-and-persist and resume semantics
3. **Preserve the directory layout** and immutable/mutable artifact conventions from the legacy repository

---

## Scope

### 1. Repository Module (`axis/framework/persistence.py`)

The new repository follows the same structural pattern as the legacy one: a single class with path resolution, save/load methods, and discovery methods. The only change is the types it serializes.

#### Status Enums and Metadata (carry forward)

```python
class ExperimentStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ExperimentMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)
    experiment_id: str
    created_at: str
    experiment_type: str
    system_type: str          # NEW: from ExperimentConfig.system_type
    name: str | None = None
    description: str | None = None

class RunMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)
    run_id: str
    experiment_id: str
    variation_description: str | None = None
    created_at: str
    base_seed: int | None = None

class ExperimentStatusRecord(BaseModel):
    model_config = ConfigDict(frozen=True)
    status: ExperimentStatus

class RunStatusRecord(BaseModel):
    model_config = ConfigDict(frozen=True)
    status: RunStatus
```

**Key change from legacy**: `ExperimentMetadata` gains a `system_type` field.

#### Directory Layout (unchanged)

```
<root>/
  <experiment_id>/
    experiment_config.json
    experiment_metadata.json
    experiment_status.json
    experiment_summary.json
    runs/
      <run_id>/
        run_config.json
        run_metadata.json
        run_status.json
        run_summary.json
        run_result.json
        episodes/
          episode_0001.json
          episode_0002.json
          ...
```

#### ExperimentRepository Class

Same structure as legacy. Constructor takes `root: Path`.

**Path resolution methods** (pure, no IO): Identical to legacy -- `experiment_dir()`, `experiment_config_path()`, `experiment_metadata_path()`, `experiment_status_path()`, `experiment_summary_path()`, `runs_dir()`, `run_dir()`, `run_config_path()`, `run_metadata_path()`, `run_status_path()`, `run_summary_path()`, `run_result_path()`, `episodes_dir()`, `episode_path()`.

**Directory creation methods**: `create_experiment_dir()`, `create_run_dir()` -- unchanged.

**Save methods**: Same immutable/mutable semantics. Types change:

| Artifact | Legacy type | New type |
|----------|-------------|----------|
| `experiment_config.json` | `axis_system_a.experiment.ExperimentConfig` | `axis.framework.config.ExperimentConfig` |
| `run_config.json` | `axis_system_a.run.RunConfig` | `axis.framework.run.RunConfig` |
| `run_summary.json` | `axis_system_a.run.RunSummary` | `axis.framework.run.RunSummary` |
| `run_result.json` | `axis_system_a.run.RunResult` | `axis.framework.run.RunResult` |
| `episode_NNNN.json` | `axis_system_a.results.EpisodeResult` | `axis.sdk.trace.BaseEpisodeTrace` |
| `experiment_summary.json` | `axis_system_a.experiment.ExperimentSummary` | `axis.framework.experiment.ExperimentSummary` |

Metadata, status types are defined locally in the persistence module (same structure as legacy).

**Load methods**: Same pattern -- `json.loads()` -> `Model.model_validate()`.

**Discovery methods**: `list_experiments()`, `list_runs()`, `list_episode_files()`, `artifact_exists()` -- unchanged.

#### Serialization

Same approach as legacy:
- **Write**: `model.model_dump(mode="json")` -> `json.dumps(data, indent=2)` -> `Path.write_text()`
- **Read**: `Path.read_text()` -> `json.loads()` -> `Model.model_validate(data)`
- **No pickle, no binary formats**

### 2. Executor Persistence Integration

WP-3.3's `ExperimentExecutor` is extended to accept an optional `ExperimentRepository`. When provided, it persists artifacts during execution and supports resume.

**Option A**: Modify `ExperimentExecutor` in `axis/framework/experiment.py` to accept a repository.
**Option B**: Create a `PersistentExperimentExecutor` that wraps `ExperimentExecutor`.

**Choice: (A)**. This matches the legacy pattern where the executor owns persistence. The executor works without a repository (pure computation) or with one (persistence + resume).

```python
class ExperimentExecutor:
    def __init__(
        self,
        run_executor: RunExecutor | None = None,
        repository: ExperimentRepository | None = None,
    ) -> None:
        self._run_executor = run_executor or RunExecutor()
        self._repository = repository

    def execute(self, config: ExperimentConfig) -> ExperimentResult:
        """Execute with optional persistence."""

    def resume(self, experiment_id: str) -> ExperimentResult:
        """Resume a persisted experiment. Requires repository."""
```

When `repository` is `None`, `execute()` works as in WP-3.3 (no persistence). When provided:
- Creates experiment dir, saves config/metadata/status
- For each run: creates run dir, saves run config/metadata/status, executes, saves result/summary/episodes, marks COMPLETED
- On failure: marks run/experiment FAILED or PARTIAL
- Finalizes with experiment summary

`resume()` requires a repository. It:
1. Loads experiment config from repository
2. Resolves run configs
3. For each run: checks `is_run_complete()` (status COMPLETED + artifacts loadable), skips if complete, re-executes otherwise
4. Finalizes with summary

**`is_run_complete()`** (module-level helper): Same as legacy -- checks status and tries loading config/summary/result.

### 3. Resume System Type Safety

When resuming, the executor verifies that the system type from the persisted config matches a registered system type. This prevents resuming an experiment with a different system or when the required system is not registered.

### 4. Convenience Functions

```python
def execute_experiment(
    config: ExperimentConfig,
    repository: ExperimentRepository,
) -> ExperimentResult:
    """Execute an experiment with persistence. Convenience wrapper."""
    return ExperimentExecutor(repository=repository).execute(config)

def resume_experiment(
    experiment_id: str,
    repository: ExperimentRepository,
) -> ExperimentResult:
    """Resume an experiment. Convenience wrapper."""
    return ExperimentExecutor(repository=repository).resume(experiment_id)
```

---

## Out of Scope

Do **not** implement any of the following in WP-3.4:

- CLI adaptation (WP-3.5)
- Visualization `ReplayAccessService` adaptation (WP-4.x)
- Migration tools for legacy artifacts
- Database backends or non-filesystem storage
- Compression or binary serialization
- Logging/JSONL file management

---

## Architectural Constraints

### 1. System-Agnostic

The persistence module never imports from `axis.systems.system_a`. It serializes `BaseEpisodeTrace` (which contains `system_data: dict` for system-specific data) without knowing what the system-specific data means.

### 2. JSON-Only Serialization

All artifacts are JSON with `indent=2`. Pydantic `model_dump(mode="json")` for writes, `model_validate()` for reads. `system_data` in `BaseStepTrace` is a `dict[str, Any]` and serializes naturally to JSON.

### 3. Episode Data Storage

Episode traces are stored both:
- **Embedded** in `run_result.json` (as part of `RunResult.episode_traces`)
- **Individually** as `episode_NNNN.json` files (for granular access by visualization)

This matches the legacy pattern. Episode indices are **1-based** in filenames.

### 4. Immutable/Mutable Semantics Preserved

- **Immutable** (raises `FileExistsError` on double-write): config, summary, result, episode files
- **Mutable** (overwrites by default): metadata, status files
- Save methods accept `overwrite: bool` parameter for resume safety

### 5. Backward Compatibility

Per Q13, there is **no** backward compatibility with legacy artifacts. The new repository reads/writes only new-format configs and results. Old experiments under `axis_system_a` remain accessible through the legacy repository.

---

## Expected File Structure

After WP-3.4, these files are **new**:

```
src/axis/framework/persistence.py               # NEW (ExperimentRepository, statuses, metadata)
tests/framework/test_persistence.py          # NEW (repository unit tests)
tests/framework/test_executor_persistence.py # NEW (executor + persistence integration)
```

These files are **modified**:

```
src/axis/framework/experiment.py    # MODIFIED (add repository param, resume method)
src/axis/framework/__init__.py      # MODIFIED (add persistence exports)
tests/test_scaffold.py          # MODIFIED (update framework exports)
```

---

## Testing Requirements

### Repository Unit Tests (`tests/framework/test_persistence.py`)

Follow the same test structure as legacy `tests/unit/test_repository.py`:

| Test | Description |
|------|-------------|
| `test_experiment_status_enum` | All enum values exist |
| `test_run_status_enum` | All enum values exist |
| `test_experiment_metadata_construction` | Includes `system_type` field |
| `test_path_resolution` | All path methods produce correct paths |
| `test_directory_creation` | `create_experiment_dir` and `create_run_dir` idempotent |
| `test_save_load_experiment_config` | Roundtrip with new `ExperimentConfig` |
| `test_save_load_run_config` | Roundtrip with new `RunConfig` |
| `test_save_load_run_summary` | Roundtrip with vitality-based `RunSummary` |
| `test_save_load_run_result` | Roundtrip with `RunResult` containing `BaseEpisodeTrace` |
| `test_save_load_episode_trace` | Roundtrip with `BaseEpisodeTrace` |
| `test_save_load_experiment_summary` | Roundtrip with `ExperimentSummary` |
| `test_save_load_status` | Roundtrip for both experiment and run status |
| `test_save_load_metadata` | Roundtrip for both experiment and run metadata |
| `test_immutable_write_semantics` | Double-write raises `FileExistsError` |
| `test_overwrite_flag` | `overwrite=True` succeeds on double-write |
| `test_list_experiments` | Empty and populated discovery |
| `test_list_runs` | Empty and populated discovery |
| `test_list_episode_files` | Sorted file list |
| `test_artifact_exists` | True and false cases |
| `test_missing_file_raises` | `FileNotFoundError` on load |
| `test_malformed_json_raises` | `JSONDecodeError` on corrupt file |

### Executor Persistence Integration Tests (`tests/framework/test_executor_persistence.py`)

| Test | Description |
|------|-------------|
| `test_execute_creates_experiment_dir` | Experiment directory exists after execution |
| `test_execute_saves_config` | `experiment_config.json` loadable |
| `test_execute_saves_metadata` | `experiment_metadata.json` has `system_type` |
| `test_execute_saves_status_completed` | Final status is COMPLETED |
| `test_execute_saves_run_artifacts` | Run config, summary, result, episodes all exist |
| `test_execute_episode_count` | Correct number of episode files |
| `test_execute_episode_naming` | 1-based: `episode_0001.json` |
| `test_resume_skips_completed_runs` | Completed runs not re-executed |
| `test_resume_reexecutes_incomplete` | Failed/incomplete runs re-executed |
| `test_resume_requires_repository` | `resume()` without repository raises |
| `test_resume_deterministic` | Resume produces same summary as original |
| `test_is_run_complete` | Checks status + artifact integrity |
| `test_execute_without_repository` | Works as pure computation (no persistence) |

All existing tests must continue to pass.

---

## Implementation Style

- Python 3.11+
- Frozen Pydantic models for all metadata/status types
- JSON-only serialization (same pattern as legacy)
- `ExperimentRepository` is a class (same API shape as legacy)
- Private `_save_json()` / `_load_json()` helpers
- Tests use `tmp_path` fixture for filesystem isolation

---

## Expected Deliverable

1. Persistence module at `src/axis/framework/persistence.py`
2. Updated `src/axis/framework/experiment.py` (repository param + resume)
3. Updated `src/axis/framework/__init__.py` with persistence exports
4. Updated `tests/test_scaffold.py`
5. Repository tests at `tests/framework/test_persistence.py`
6. Integration tests at `tests/framework/test_executor_persistence.py`
7. Confirmation that all tests pass
