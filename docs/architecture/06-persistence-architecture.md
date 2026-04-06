# 6. Persistence Architecture

## ExperimentRepository (`repository.py`)

File-based persistence layer with no external dependencies. Provides structured save/load for all experiment artifacts.

### Design Principles

- **JSON-only**: All artifacts serialized as indented JSON via Pydantic's `model_dump(mode="json")`
- **Immutable by default**: Config, summary, and result artifacts use `overwrite=False` (raise `FileExistsError` on collision)
- **Mutable status/metadata**: Status and metadata files use `overwrite=True` for lifecycle transitions
- **Resume-safe**: Executor passes `overwrite=True` when re-executing failed runs during resume
- **Conventional paths**: All artifact locations derived from experiment/run IDs via pure path-resolution methods

### Filesystem Layout

```
{repository_root}/
└── {experiment_id}/
    ├── experiment_config.json        ExperimentConfig (immutable)
    ├── experiment_metadata.json      ExperimentMetadata (mutable)
    ├── experiment_status.json        {"status": "created|running|completed|failed|partial"}
    ├── experiment_summary.json       ExperimentSummary (written at finalization)
    └── runs/
        └── {run_id}/
            ├── run_config.json       RunConfig (immutable)
            ├── run_metadata.json     RunMetadata (mutable)
            ├── run_status.json       {"status": "pending|running|completed|failed"}
            ├── run_summary.json      RunSummary (immutable)
            ├── run_result.json       RunResult (full, includes episode_results)
            └── episodes/
                ├── episode_0001.json EpisodeResult (1-indexed, immutable)
                ├── episode_0002.json
                └── ...
```

Note: `run_result.json` contains the complete `RunResult` with all episode results embedded. The individual `episode_NNNN.json` files are redundant but useful for targeted loading (e.g., loading a single episode for visualization without deserializing all episodes).

### Artifact Categories

| Category | Files | Overwrite Default | Lifecycle |
|----------|-------|-------------------|-----------|
| **Config** | `experiment_config.json`, `run_config.json` | `False` | Written once at creation |
| **Metadata** | `experiment_metadata.json`, `run_metadata.json` | `True` | Written at creation, may update |
| **Status** | `experiment_status.json`, `run_status.json` | `True` | Updated at each lifecycle transition |
| **Results** | `run_result.json`, `episode_NNNN.json` | `False` | Written once at completion |
| **Summaries** | `experiment_summary.json`, `run_summary.json` | `False` | Written once at finalization |

### Status Enums

**ExperimentStatus**: `CREATED` -> `RUNNING` -> `COMPLETED` | `FAILED` | `PARTIAL`

**RunStatus**: `PENDING` -> `RUNNING` -> `COMPLETED` | `FAILED`

Status is serialized via wrapper models (`ExperimentStatusRecord`, `RunStatusRecord`) to produce `{"status": "..."}` JSON rather than bare strings.

### Repository API

**Path resolution** (pure, no IO): `experiment_dir()`, `run_dir()`, `episodes_dir()`, and per-artifact `*_path()` methods.

**Save methods**: One per artifact type. Accept the Pydantic model, serialize via `model_dump(mode="json")`, write through `_save_json()`.

**Load methods**: One per artifact type. Read via `_load_json()`, deserialize via `model_validate()`. Status loaders unwrap the `StatusRecord` wrapper.

**Discovery**: `list_experiments()`, `list_runs()`, `list_episode_files()` -- sorted directory/file listings.

### Metadata Models

**ExperimentMetadata**: `experiment_id`, `created_at` (ISO 8601), `experiment_type`, `name`, `description`

**RunMetadata**: `run_id`, `experiment_id`, `variation_description`, `created_at`, `base_seed`
