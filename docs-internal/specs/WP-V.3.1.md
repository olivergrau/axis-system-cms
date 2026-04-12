# WP-V.3.1 Implementation Brief -- Replay Access and Validation

## Context

With Phase V-2 complete (all adapters implemented and registered), the visualization system has the building blocks to render any world/system combination. Phase V-3 extracts and generalizes the v0.1.0 replay infrastructure to work with the v0.2.0 framework's `BaseEpisodeTrace` / `BaseStepTrace` replay contract.

This work package ports the replay access service, validation logic, replay models, and error types from `axis_system_a.visualization` to `axis.visualization`. The v0.1.0 code reads `EpisodeResult` with System A-specific `TransitionTrace` and `StepResult` types; the v0.2.0 version reads `BaseEpisodeTrace` with generic `BaseStepTrace` steps.

### Predecessor State (After Phase V-2)

```
src/axis/visualization/
    __init__.py
    types.py                             # Supporting types
    protocols.py                         # Adapter protocols
    registry.py                          # Registration/resolution
    adapters/
        default_world.py                 # DefaultWorldVisualizationAdapter
        null_system.py                   # NullSystemVisualizationAdapter
```

The `ExperimentRepository` (in `axis.framework.persistence`) already provides:
- `load_episode_trace(experiment_id, run_id, episode_index) -> BaseEpisodeTrace`
- `load_experiment_config(experiment_id) -> ExperimentConfig`
- `load_run_config(experiment_id, run_id) -> RunConfig`
- `list_experiments() -> list[str]`
- `list_runs(experiment_id) -> list[str]`
- `list_episode_files(experiment_id, run_id) -> list[Path]`
- `artifact_exists(path) -> bool`

### v0.1.0 Source Files Being Migrated

| v0.1.0 file | v0.2.0 destination |
|---|---|
| `axis_system_a/visualization/errors.py` | `axis/visualization/errors.py` |
| `axis_system_a/visualization/replay_models.py` | `axis/visualization/replay_models.py` |
| `axis_system_a/visualization/replay_validation.py` | `axis/visualization/replay_validation.py` |
| `axis_system_a/visualization/replay_access.py` | `axis/visualization/replay_access.py` |

### Reference Documents

- `docs/architecture/evolution/visualization-architecture.md` -- Sections 12.3, 14.1
- `docs/architecture/evolution/visualization-architecture-roadmap.md` -- WP-V.3.1

---

## Objective

Implement the replay access service, validation pipeline, replay handle models, and error hierarchy for the v0.2.0 visualization system, working with `BaseEpisodeTrace` and the v0.2.0 `ExperimentRepository`.

---

## Scope

### 1. Error Types

**File**: `src/axis/visualization/errors.py` (new)

Port the v0.1.0 error hierarchy. The types are framework-generic -- no System A references to remove.

```python
"""Exception hierarchy for the Visualization Layer.

All visualization-specific errors inherit from ReplayError,
allowing callers to catch broadly or narrowly as needed.
"""

from __future__ import annotations


class ReplayError(Exception):
    """Base exception for all visualization replay errors."""


class ExperimentNotFoundError(ReplayError):
    """Raised when a requested experiment does not exist in the repository."""


class RunNotFoundError(ReplayError):
    """Raised when a requested run does not exist within an experiment."""


class EpisodeNotFoundError(ReplayError):
    """Raised when a requested episode does not exist within a run."""


class ReplayContractViolation(ReplayError):
    """Raised when an episode fails replay contract validation.

    Carries a tuple of human-readable violation descriptions.
    """

    def __init__(self, violations: tuple[str, ...], *args: object) -> None:
        self.violations = violations
        msg = f"{len(violations)} replay contract violation(s): {'; '.join(violations)}"
        super().__init__(msg, *args)


class MalformedArtifactError(ReplayError):
    """Raised when a persisted artifact cannot be deserialized."""


class StepOutOfBoundsError(ReplayError):
    """Raised when step_index is outside the valid range [0, total_steps-1]."""

    def __init__(self, step_index: int, total_steps: int) -> None:
        self.step_index = step_index
        self.total_steps = total_steps
        super().__init__(
            f"Step index {step_index} out of bounds "
            f"(valid range: 0..{total_steps - 1})"
        )


class PhaseNotAvailableError(ReplayError):
    """Raised when the requested phase has no valid snapshot at the given step."""

    def __init__(self, step_index: int, phase_index: int) -> None:
        self.step_index = step_index
        self.phase_index = phase_index
        super().__init__(
            f"Phase index {phase_index} not available at step index {step_index}"
        )


class CellOutOfBoundsError(ReplayError):
    """Raised when cell coordinates are outside the valid grid bounds."""

    def __init__(
        self, row: int, col: int, grid_width: int, grid_height: int,
    ) -> None:
        self.row = row
        self.col = col
        self.grid_width = grid_width
        self.grid_height = grid_height
        super().__init__(
            f"Cell ({row}, {col}) out of bounds "
            f"(grid: {grid_height} rows x {grid_width} cols)"
        )
```

**Changes from v0.1.0**:
- `PhaseNotAvailableError` takes `phase_index: int` instead of `phase: object` (supports variable phase counts)
- All other error types are identical

### 2. Replay Models

**File**: `src/axis/visualization/replay_models.py` (new)

The v0.1.0 replay models have three System A-specific problems:
1. `ReplayPhaseAvailability` has hard-coded `before`, `after_regen`, `after_action` fields
2. `ReplayEpisodeHandle` wraps `EpisodeResult` (System A type)
3. Handle types import `ExperimentConfig`, `RunConfig`, etc. from `axis_system_a`

The v0.2.0 models generalize all three.

```python
"""Read-only data models for the Visualization Layer.

Frozen Pydantic models providing a stable access boundary between
the repository and later visualization components (replay logic,
viewer state, rendering).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from axis.framework.config import ExperimentConfig
from axis.framework.persistence import ExperimentMetadata, RunMetadata
from axis.framework.run import RunConfig, RunSummary
from axis.sdk.trace import BaseEpisodeTrace


class ReplayStepDescriptor(BaseModel):
    """Lightweight replay-readiness metadata for a single step."""

    model_config = ConfigDict(frozen=True)

    step_index: int
    has_world_before: bool
    has_world_after: bool
    has_intermediate_snapshots: tuple[str, ...]
    has_agent_position: bool
    has_vitality: bool
    has_world_state: bool


class ReplayValidationResult(BaseModel):
    """Outcome of validating an episode against the replay contract."""

    model_config = ConfigDict(frozen=True)

    valid: bool
    total_steps: int
    grid_width: int | None = None
    grid_height: int | None = None
    violations: tuple[str, ...] = ()
    step_descriptors: tuple[ReplayStepDescriptor, ...] = ()


class ReplayEpisodeHandle(BaseModel):
    """Validated episode ready for replay consumption."""

    model_config = ConfigDict(frozen=True)

    experiment_id: str
    run_id: str
    episode_index: int
    episode_trace: BaseEpisodeTrace
    validation: ReplayValidationResult


class ReplayRunHandle(BaseModel):
    """Run-level handle exposing config, metadata, and episode listing."""

    model_config = ConfigDict(frozen=True)

    experiment_id: str
    run_id: str
    run_config: RunConfig
    run_metadata: RunMetadata | None = None
    run_summary: RunSummary | None = None
    available_episodes: tuple[int, ...]


class ReplayExperimentHandle(BaseModel):
    """Experiment-level handle exposing config, metadata, and run listing."""

    model_config = ConfigDict(frozen=True)

    experiment_id: str
    experiment_config: ExperimentConfig
    experiment_metadata: ExperimentMetadata | None = None
    available_runs: tuple[str, ...]
```

**Key changes from v0.1.0**:
- `ReplayPhaseAvailability` removed entirely -- phase availability is now dynamic (varies by system), handled by the SnapshotResolver in WP-V.3.2
- `ReplayStepDescriptor` generalized: `has_world_before`, `has_world_after`, `has_intermediate_snapshots: tuple[str, ...]` (names of available intermediate snapshots) instead of fixed phase booleans
- `ReplayEpisodeHandle.episode_result` renamed to `episode_trace` and typed as `BaseEpisodeTrace`
- All imports point to `axis.framework.*` and `axis.sdk.*` instead of `axis_system_a.*`

### 3. Replay Validation

**File**: `src/axis/visualization/replay_validation.py` (new)

Validates `BaseEpisodeTrace` for replay readiness. The v0.1.0 version accesses `step.transition_trace.world_before/world_after_regen/world_after_action` -- System A-specific fields. The v0.2.0 version validates `step.world_before`, `step.world_after`, and `step.intermediate_snapshots`.

```python
"""Replay contract validation for episode traces.

Validates that a BaseEpisodeTrace satisfies all requirements for
deterministic replay: step ordering, world state presence, agent
state, and grid dimension consistency.
"""

from __future__ import annotations

from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseEpisodeTrace

from axis.visualization.replay_models import (
    ReplayStepDescriptor,
    ReplayValidationResult,
)


def _is_valid_snapshot(snapshot: WorldSnapshot) -> bool:
    """Check that a WorldSnapshot has a non-empty, well-dimensioned grid."""
    return (
        snapshot.width > 0
        and snapshot.height > 0
        and len(snapshot.grid) > 0
        and len(snapshot.grid[0]) > 0
    )


def validate_episode_for_replay(
    episode: BaseEpisodeTrace,
) -> ReplayValidationResult:
    """Validate an episode trace against the replay contract.

    Returns a ReplayValidationResult with valid=True if all checks pass,
    or valid=False with a tuple of human-readable violation descriptions.
    """
    violations: list[str] = []
    step_descriptors: list[ReplayStepDescriptor] = []
    grid_width: int | None = None
    grid_height: int | None = None

    steps = episode.steps

    # 1. Non-empty steps
    if len(steps) == 0:
        return ReplayValidationResult(
            valid=False,
            total_steps=0,
            violations=("Episode contains no steps",),
        )

    # 2. Step ordering: monotonic, contiguous, no duplicates
    seen_timesteps: set[int] = set()
    base_timestep = steps[0].timestep

    for i, step in enumerate(steps):
        t = step.timestep

        if t in seen_timesteps:
            violations.append(f"Duplicate timestep {t}")
        seen_timesteps.add(t)

        if i > 0 and t <= steps[i - 1].timestep:
            violations.append(
                f"Step ordering violation at index {i}: "
                f"timestep {t} is not greater than {steps[i - 1].timestep}"
            )

        expected = base_timestep + i
        if t != expected:
            violations.append(
                f"Step index gap: expected timestep {expected} "
                f"at index {i}, got {t}"
            )

    # 3. Per-step validation
    for i, step in enumerate(steps):
        # World state validation
        before_ok = _is_valid_snapshot(step.world_before)
        after_ok = _is_valid_snapshot(step.world_after)

        if not before_ok:
            violations.append(
                f"Missing or invalid world_before at step {i}"
            )
        if not after_ok:
            violations.append(
                f"Missing or invalid world_after at step {i}"
            )

        # Intermediate snapshots (check each if present)
        intermediate_names: list[str] = []
        for name, snapshot in step.intermediate_snapshots.items():
            if _is_valid_snapshot(snapshot):
                intermediate_names.append(name)

        # Vitality validation
        has_vitality = (
            0.0 <= step.vitality_before <= 1.0
            and 0.0 <= step.vitality_after <= 1.0
        )
        if not has_vitality:
            violations.append(
                f"Invalid vitality at step {i}: "
                f"before={step.vitality_before}, after={step.vitality_after}"
            )

        # Agent position (always present by model constraint)
        has_position = True

        # World state present (at least one valid snapshot)
        has_world = before_ok or after_ok

        step_descriptors.append(
            ReplayStepDescriptor(
                step_index=i,
                has_world_before=before_ok,
                has_world_after=after_ok,
                has_intermediate_snapshots=tuple(sorted(intermediate_names)),
                has_agent_position=has_position,
                has_vitality=has_vitality,
                has_world_state=has_world,
            )
        )

        # Grid dimension consistency
        for phase_name, snapshot, phase_ok in [
            ("world_before", step.world_before, before_ok),
            ("world_after", step.world_after, after_ok),
        ]:
            if not phase_ok:
                continue
            w, h = snapshot.width, snapshot.height
            if grid_width is None:
                grid_width = w
                grid_height = h
            elif (w, h) != (grid_width, grid_height):
                violations.append(
                    f"Inconsistent grid dimensions: expected "
                    f"{grid_width}x{grid_height}, got {w}x{h} "
                    f"at step {i}, phase {phase_name}"
                )

    return ReplayValidationResult(
        valid=len(violations) == 0,
        total_steps=len(steps),
        grid_width=grid_width,
        grid_height=grid_height,
        violations=tuple(violations),
        step_descriptors=tuple(step_descriptors),
    )
```

**Key changes from v0.1.0**:
- Validates `step.world_before` and `step.world_after` (BaseStepTrace fields) instead of `step.transition_trace.world_before/world_after_regen/world_after_action` (System A TransitionTrace fields)
- Validates `step.vitality_before/after` (normalized float) instead of `step.energy_before/after` (raw float)
- Records `has_intermediate_snapshots` as a tuple of snapshot names instead of fixed `ReplayPhaseAvailability`
- Uses `step_index=i` (list position) instead of `step_index=step.timestep` (corrects a subtle v0.1.0 inconsistency where step_descriptors used timestep as index)

### 4. Replay Access Service

**File**: `src/axis/visualization/replay_access.py` (new)

```python
"""Repository-backed access layer for the Visualization Layer.

Wraps ExperimentRepository to provide visualization-oriented read-only
access with replay-specific validation and error signaling.
"""

from __future__ import annotations

import re

from pydantic import ValidationError

from axis.framework.config import ExperimentConfig
from axis.framework.persistence import (
    ExperimentMetadata,
    ExperimentRepository,
    RunMetadata,
)
from axis.framework.run import RunConfig, RunSummary
from axis.sdk.trace import BaseEpisodeTrace

from axis.visualization.errors import (
    EpisodeNotFoundError,
    ExperimentNotFoundError,
    MalformedArtifactError,
    ReplayContractViolation,
    RunNotFoundError,
)
from axis.visualization.replay_models import (
    ReplayEpisodeHandle,
    ReplayExperimentHandle,
    ReplayRunHandle,
    ReplayValidationResult,
)
from axis.visualization.replay_validation import (
    validate_episode_for_replay,
)

_EPISODE_RE = re.compile(r"^episode_(\d+)\.json$")


class ReplayAccessService:
    """Read-only visualization gateway to the experiment repository.

    All data access delegates to ExperimentRepository. This service
    adds replay-oriented validation, typed error mapping, and
    discovery helpers.
    """

    def __init__(self, repository: ExperimentRepository) -> None:
        self._repo = repository

    # -- internal helpers ---------------------------------------------------

    def _require_experiment(self, experiment_id: str) -> None:
        if experiment_id not in self._repo.list_experiments():
            raise ExperimentNotFoundError(
                f"Experiment not found: {experiment_id}"
            )

    def _require_run(self, experiment_id: str, run_id: str) -> None:
        self._require_experiment(experiment_id)
        if run_id not in self._repo.list_runs(experiment_id):
            raise RunNotFoundError(
                f"Run not found: {run_id} in experiment {experiment_id}"
            )

    # -- discovery ----------------------------------------------------------

    def list_experiments(self) -> tuple[str, ...]:
        """Return sorted experiment IDs available in the repository."""
        return tuple(self._repo.list_experiments())

    def list_runs(self, experiment_id: str) -> tuple[str, ...]:
        """Return sorted run IDs for *experiment_id*."""
        self._require_experiment(experiment_id)
        return tuple(self._repo.list_runs(experiment_id))

    def list_episode_indices(
        self, experiment_id: str, run_id: str,
    ) -> tuple[int, ...]:
        """Return sorted episode indices for a run."""
        self._require_run(experiment_id, run_id)
        paths = self._repo.list_episode_files(experiment_id, run_id)
        indices: list[int] = []
        for p in paths:
            m = _EPISODE_RE.match(p.name)
            if m:
                indices.append(int(m.group(1)))
        return tuple(sorted(indices))

    # -- handles ------------------------------------------------------------

    def get_experiment_handle(
        self, experiment_id: str,
    ) -> ReplayExperimentHandle:
        """Load experiment config/metadata and list available runs."""
        config = self.load_experiment_config(experiment_id)
        metadata = self._load_optional_experiment_metadata(experiment_id)
        runs = self.list_runs(experiment_id)
        return ReplayExperimentHandle(
            experiment_id=experiment_id,
            experiment_config=config,
            experiment_metadata=metadata,
            available_runs=runs,
        )

    def get_run_handle(
        self, experiment_id: str, run_id: str,
    ) -> ReplayRunHandle:
        """Load run config/metadata/summary and list available episodes."""
        run_config = self.load_run_config(experiment_id, run_id)
        run_metadata = self._load_optional_run_metadata(
            experiment_id, run_id,
        )
        run_summary = self._load_optional_run_summary(
            experiment_id, run_id,
        )
        episodes = self.list_episode_indices(experiment_id, run_id)
        return ReplayRunHandle(
            experiment_id=experiment_id,
            run_id=run_id,
            run_config=run_config,
            run_metadata=run_metadata,
            run_summary=run_summary,
            available_episodes=episodes,
        )

    # -- artifact loading ---------------------------------------------------

    def load_experiment_config(
        self, experiment_id: str,
    ) -> ExperimentConfig:
        """Load and return the experiment configuration."""
        self._require_experiment(experiment_id)
        return self._safe_load(
            lambda: self._repo.load_experiment_config(experiment_id),
            f"experiment config for {experiment_id}",
        )

    def load_run_config(
        self, experiment_id: str, run_id: str,
    ) -> RunConfig:
        """Load and return the run configuration."""
        self._require_run(experiment_id, run_id)
        return self._safe_load(
            lambda: self._repo.load_run_config(experiment_id, run_id),
            f"run config for {experiment_id}/{run_id}",
        )

    def load_episode_trace(
        self, experiment_id: str, run_id: str, episode_index: int,
    ) -> BaseEpisodeTrace:
        """Load raw episode trace without validation."""
        self._require_run(experiment_id, run_id)
        if episode_index not in self.list_episode_indices(
            experiment_id, run_id,
        ):
            raise EpisodeNotFoundError(
                f"Episode {episode_index} not found in "
                f"{experiment_id}/{run_id}"
            )
        return self._safe_load(
            lambda: self._repo.load_episode_trace(
                experiment_id, run_id, episode_index,
            ),
            f"episode {episode_index} for {experiment_id}/{run_id}",
        )

    # -- replay loading (primary API) ---------------------------------------

    def load_replay_episode(
        self, experiment_id: str, run_id: str, episode_index: int,
    ) -> ReplayEpisodeHandle:
        """Load and validate an episode for replay.

        Returns a ReplayEpisodeHandle with validation attached.
        Raises ReplayContractViolation if the episode fails validation.
        """
        episode = self.load_episode_trace(
            experiment_id, run_id, episode_index,
        )
        validation = validate_episode_for_replay(episode)
        if not validation.valid:
            raise ReplayContractViolation(validation.violations)
        return ReplayEpisodeHandle(
            experiment_id=experiment_id,
            run_id=run_id,
            episode_index=episode_index,
            episode_trace=episode,
            validation=validation,
        )

    def validate_episode(
        self, experiment_id: str, run_id: str, episode_index: int,
    ) -> ReplayValidationResult:
        """Load and validate an episode, returning the result
        (never raises ReplayContractViolation)."""
        episode = self.load_episode_trace(
            experiment_id, run_id, episode_index,
        )
        return validate_episode_for_replay(episode)

    # -- optional loaders ---------------------------------------------------

    def _load_optional_experiment_metadata(
        self, experiment_id: str,
    ) -> ExperimentMetadata | None:
        path = self._repo.experiment_metadata_path(experiment_id)
        if not self._repo.artifact_exists(path):
            return None
        return self._safe_load(
            lambda: self._repo.load_experiment_metadata(experiment_id),
            f"experiment metadata for {experiment_id}",
        )

    def _load_optional_run_metadata(
        self, experiment_id: str, run_id: str,
    ) -> RunMetadata | None:
        path = self._repo.run_metadata_path(experiment_id, run_id)
        if not self._repo.artifact_exists(path):
            return None
        return self._safe_load(
            lambda: self._repo.load_run_metadata(experiment_id, run_id),
            f"run metadata for {experiment_id}/{run_id}",
        )

    def _load_optional_run_summary(
        self, experiment_id: str, run_id: str,
    ) -> RunSummary | None:
        path = self._repo.run_summary_path(experiment_id, run_id)
        if not self._repo.artifact_exists(path):
            return None
        return self._safe_load(
            lambda: self._repo.load_run_summary(experiment_id, run_id),
            f"run summary for {experiment_id}/{run_id}",
        )

    # -- safe-load wrapper --------------------------------------------------

    @staticmethod
    def _safe_load(loader, description: str):  # noqa: ANN001, ANN205
        """Call *loader()* and wrap non-visualization exceptions."""
        try:
            return loader()
        except (FileNotFoundError, ValidationError, KeyError) as exc:
            raise MalformedArtifactError(
                f"Failed to load {description}: {exc}"
            ) from exc
```

**Key changes from v0.1.0**:
- `load_episode_result()` replaced by `load_episode_trace()` -- calls `self._repo.load_episode_trace()` which returns `BaseEpisodeTrace`
- `ReplayEpisodeHandle` field is `episode_trace` (not `episode_result`)
- All imports point to `axis.framework.*` and `axis.sdk.*`
- No `EpisodeResult` or `StepResult` references anywhere

---

## Out of Scope

- Snapshot resolution (WP-V.3.2)
- Viewer state management (WP-V.3.3)
- View model building (WP-V.3.4)
- Any PySide6 code
- Modifications to `ExperimentRepository` or SDK trace types

---

## Architectural Constraints

### 1. Read-Only Access

`ReplayAccessService` is strictly read-only. It wraps `ExperimentRepository` for loading, never for saving. All mutations happen through the framework runner.

### 2. Validation Collects All Violations

`validate_episode_for_replay()` never fails on the first violation. It collects all violations and returns them in `ReplayValidationResult.violations`. This gives complete diagnostics for invalid artifacts.

### 3. No System-Specific Knowledge

The validation logic validates `BaseStepTrace` fields only (`world_before`, `world_after`, `intermediate_snapshots`, `vitality_before/after`, positions). It never accesses `system_data` or any system-specific type.

### 4. Error Hierarchy is the Contract

Other visualization modules catch `ReplayError` subtypes. The error hierarchy must be stable. `PhaseNotAvailableError` is the only change (takes `phase_index: int` instead of `phase: object`).

---

## Testing Requirements

**File**: `tests/visualization/test_replay_access.py` (new)
**File**: `tests/visualization/test_replay_validation.py` (new)

### Validation tests (`test_replay_validation.py`)

1. **`test_valid_episode_passes`**: Create a `BaseEpisodeTrace` with 3 valid steps, assert `valid=True`, `total_steps=3`
2. **`test_empty_episode_fails`**: Episode with 0 steps, assert `valid=False`, violation mentions "no steps"
3. **`test_duplicate_timestep`**: Two steps with same timestep, assert violation mentions "Duplicate"
4. **`test_non_monotonic_timesteps`**: Steps with decreasing timesteps, assert violation
5. **`test_timestep_gap`**: Steps with gap (0, 2, 3), assert violation mentions "gap"
6. **`test_invalid_world_before`**: Step with 0-width world_before, assert violation
7. **`test_invalid_world_after`**: Step with 0-height world_after, assert violation
8. **`test_invalid_vitality`**: Step with vitality > 1.0 or < 0.0, assert violation
9. **`test_grid_dimension_consistency`**: Step 0 is 10x10, step 1 is 8x8, assert violation
10. **`test_step_descriptors_populated`**: Assert correct count and fields
11. **`test_intermediate_snapshots_recorded`**: Step with `intermediate_snapshots={"after_regen": valid_snapshot}`, assert descriptor has `has_intermediate_snapshots=("after_regen",)`
12. **`test_multiple_violations_collected`**: Episode with 3 different problems, assert all 3 violations present

### Access service tests (`test_replay_access.py`)

Use a `tmp_path` fixture to create a minimal `ExperimentRepository` with fixture data.

13. **`test_list_experiments`**: Populate repo with 2 experiments, assert correct listing
14. **`test_list_runs`**: Assert correct run listing
15. **`test_list_episode_indices`**: Save 3 episodes, assert indices returned correctly
16. **`test_experiment_not_found`**: Assert `ExperimentNotFoundError` raised
17. **`test_run_not_found`**: Assert `RunNotFoundError` raised
18. **`test_episode_not_found`**: Assert `EpisodeNotFoundError` raised
19. **`test_load_episode_trace`**: Save and load a `BaseEpisodeTrace`, assert round-trip
20. **`test_load_replay_episode_valid`**: Load validated episode, assert `ReplayEpisodeHandle` returned
21. **`test_load_replay_episode_invalid`**: Episode with empty steps, assert `ReplayContractViolation` raised
22. **`test_validate_episode_no_raise`**: `validate_episode()` returns result without raising even for invalid episodes
23. **`test_get_experiment_handle`**: Assert fields populated correctly
24. **`test_get_run_handle`**: Assert fields populated correctly
25. **`test_malformed_artifact_error`**: Corrupt JSON file, assert `MalformedArtifactError`

### Error tests (inline in either file)

26. **`test_replay_contract_violation_message`**: Assert violation count in message string
27. **`test_step_out_of_bounds_message`**: Assert range in message
28. **`test_phase_not_available_error`**: Assert phase_index preserved
29. **`test_cell_out_of_bounds_error`**: Assert grid dimensions in message

---

## Expected Deliverable

1. `src/axis/visualization/errors.py`
2. `src/axis/visualization/replay_models.py`
3. `src/axis/visualization/replay_validation.py`
4. `src/axis/visualization/replay_access.py`
5. `tests/visualization/test_replay_access.py`
6. `tests/visualization/test_replay_validation.py`
7. Confirmation that all existing tests still pass

---

## Expected File Structure

```
src/axis/visualization/
    __init__.py                          # UNCHANGED
    types.py                             # UNCHANGED
    protocols.py                         # UNCHANGED
    registry.py                          # UNCHANGED
    errors.py                            # NEW
    replay_models.py                     # NEW
    replay_validation.py                 # NEW
    replay_access.py                     # NEW
    adapters/
        default_world.py                 # UNCHANGED
        null_system.py                   # UNCHANGED

tests/visualization/
    test_replay_access.py                # NEW
    test_replay_validation.py            # NEW
```
