# 7. Resume and Fault Tolerance

## Resume Flow

The `ExperimentExecutor.resume(experiment_id)` method provides idempotent resume for partially completed experiments.

### Step-by-Step Resume Process

```
1. Load persisted ExperimentConfig from repository
2. Set experiment status → RUNNING
3. Re-resolve all RunConfigs from loaded config (deterministic)
4. For each RunConfig:
   ├── Check: is_run_complete(repo, experiment_id, run_id)?
   │   ├── YES → Load existing RunResult from repository (skip execution)
   │   └── NO  → Re-execute from scratch via RunExecutor
   └── Append RunResult to results list
5. Compute experiment summary (with overwrite=True)
6. Set experiment status → COMPLETED
```

### Run Completion Detection

`is_run_complete(repo, experiment_id, run_id) -> bool` performs a strict four-check validation:

1. `load_run_status()` returns `RunStatus.COMPLETED`
2. `load_run_config()` loads and validates successfully
3. `load_run_summary()` loads and validates successfully
4. `load_run_result()` loads and validates successfully

If **any** check fails (including exceptions from missing files, corrupt JSON, or validation errors), the run is classified as **incomplete** and will be re-executed.

### What is Skipped vs. Re-Executed

| Run State | Resume Behavior |
|-----------|-----------------|
| Status = COMPLETED + all artifacts valid | **Skipped** -- existing RunResult loaded from disk |
| Status = COMPLETED but artifact missing/corrupt | **Re-executed** -- `is_run_complete` returns `False` |
| Status = RUNNING, PENDING, or FAILED | **Re-executed** from scratch |
| Run directory doesn't exist | **Re-executed** -- directory created fresh |

Re-execution uses `overwrite=True` on all artifact saves, so corrupt or partial artifacts from a previous failed attempt are replaced.

### Resume Boundary

Resume operates at the **run level** -- individual episodes within a run are not resumable. If a run is classified as incomplete, all of its episodes are re-executed. This simplifies the contract: a run is either fully complete or fully re-executed.

### Status Lifecycle

**Normal execution:**
```
Experiment: CREATED → RUNNING → COMPLETED
Run:        PENDING → RUNNING → COMPLETED
```

**Failure during execution:**
```
Experiment: CREATED → RUNNING → PARTIAL (if some runs completed) or FAILED (if zero completed)
Run:        PENDING → RUNNING → FAILED
```

**Resume:**
```
Experiment: {any} → RUNNING → COMPLETED  (or PARTIAL/FAILED if resume also fails)
Run (incomplete):  PENDING → RUNNING → COMPLETED
Run (complete):    (untouched — loaded from disk)
```

### Error Handling

On run failure during execution or resume:
1. The failing run's status is set to `FAILED`
2. If `completed_count > 0`: experiment status -> `PARTIAL`
3. If `completed_count == 0`: experiment status -> `FAILED`
4. The exception is re-raised to the caller

### Deterministic Config Resolution

Resume correctness relies on `resolve_run_configs()` being deterministic: the same `ExperimentConfig` always produces the same run configs in the same order with the same run IDs. This is guaranteed because:
- `single_run` always produces `run-0000`
- `ofat` produces `run-{i:04d}` for `i in range(len(parameter_values))`
- Seeds are derived arithmetically: `base_seed + i * 1000`

### Idempotency

Resuming an already-completed experiment is a safe no-op: all runs pass `is_run_complete`, no re-execution occurs, the summary is recomputed (producing the same result), and status is set to COMPLETED (already COMPLETED).
