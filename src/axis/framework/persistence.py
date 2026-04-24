"""Persistence layer: filesystem-backed artifact storage for experiments."""

from __future__ import annotations

import enum
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from axis.framework.config import ExperimentConfig
from axis.framework.experiment import ExperimentSummary
from axis.framework.execution_results import (
    DeltaRunResult,
    LightEpisodeResult,
    LightRunResult,
)
from axis.framework.metrics.types import RunBehaviorMetrics
from axis.framework.run import RunConfig, RunResult, RunSummary
from axis.sdk.trace import (
    BaseEpisodeTrace,
    DeltaEpisodeTrace,
    reconstruct_episode_trace,
)


# ---------------------------------------------------------------------------
# Status enums
# ---------------------------------------------------------------------------


class ExperimentStatus(str, enum.Enum):
    """Lifecycle statuses for an experiment."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class RunStatus(str, enum.Enum):
    """Lifecycle statuses for a run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Metadata models
# ---------------------------------------------------------------------------


class ExperimentMetadata(BaseModel):
    """Experiment-level metadata artifact."""

    model_config = ConfigDict(frozen=True)

    experiment_id: str
    created_at: str
    experiment_type: str
    system_type: str
    name: str | None = None
    description: str | None = None

    # --- Experiment Output Abstraction fields ---
    output_form: str | None = None          # "point" or "sweep"
    trace_mode: str | None = None           # "full", "light", or "delta"
    primary_run_id: str | None = None       # for point outputs
    baseline_run_id: str | None = None      # for sweep outputs


class RunMetadata(BaseModel):
    """Run-level metadata artifact."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    experiment_id: str
    variation_description: str | None = None
    created_at: str
    base_seed: int | None = None
    trace_mode: str | None = None

    # --- Experiment Output Abstraction fields (sweep runs) ---
    variation_index: int | None = None
    variation_value: Any | None = None
    is_baseline: bool | None = None


# ---------------------------------------------------------------------------
# Status record wrappers
# ---------------------------------------------------------------------------


class ExperimentStatusRecord(BaseModel):
    """Wrapper so status files contain {"status": "..."} rather than bare strings."""

    model_config = ConfigDict(frozen=True)

    status: ExperimentStatus


class RunStatusRecord(BaseModel):
    """Wrapper so status files contain {"status": "..."} rather than bare strings."""

    model_config = ConfigDict(frozen=True)

    status: RunStatus


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _save_json(path: Path, data: dict, *, overwrite: bool) -> None:
    """Write a dict as JSON. Raises FileExistsError if overwrite is False and file exists."""
    if not overwrite and path.exists():
        raise FileExistsError(
            f"Artifact already exists and overwrite=False: {path}"
        )
    path.write_text(json.dumps(data, indent=2))


def _load_json(path: Path) -> dict:
    """Read a JSON file and return the parsed dict."""
    return json.loads(path.read_text())


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class ExperimentRepository:
    """Filesystem-backed repository for experiment artifacts.

    All path methods are pure (no IO). Save/load methods perform IO.
    """

    def __init__(self, root: Path) -> None:
        self._root = root

    @property
    def root(self) -> Path:
        return self._root

    # -- Experiment-level path resolution -----------------------------------

    def experiment_dir(self, experiment_id: str) -> Path:
        return self._root / experiment_id

    def experiment_config_path(self, experiment_id: str) -> Path:
        return self.experiment_dir(experiment_id) / "experiment_config.json"

    def experiment_metadata_path(self, experiment_id: str) -> Path:
        return self.experiment_dir(experiment_id) / "experiment_metadata.json"

    def experiment_status_path(self, experiment_id: str) -> Path:
        return self.experiment_dir(experiment_id) / "experiment_status.json"

    def experiment_summary_path(self, experiment_id: str) -> Path:
        return self.experiment_dir(experiment_id) / "experiment_summary.json"

    def runs_dir(self, experiment_id: str) -> Path:
        return self.experiment_dir(experiment_id) / "runs"

    # -- Run-level path resolution ------------------------------------------

    def run_dir(self, experiment_id: str, run_id: str) -> Path:
        return self.runs_dir(experiment_id) / run_id

    def run_config_path(self, experiment_id: str, run_id: str) -> Path:
        return self.run_dir(experiment_id, run_id) / "run_config.json"

    def run_metadata_path(self, experiment_id: str, run_id: str) -> Path:
        return self.run_dir(experiment_id, run_id) / "run_metadata.json"

    def run_status_path(self, experiment_id: str, run_id: str) -> Path:
        return self.run_dir(experiment_id, run_id) / "run_status.json"

    def run_summary_path(self, experiment_id: str, run_id: str) -> Path:
        return self.run_dir(experiment_id, run_id) / "run_summary.json"

    def run_result_path(self, experiment_id: str, run_id: str) -> Path:
        return self.run_dir(experiment_id, run_id) / "run_result.json"

    def behavior_metrics_path(self, experiment_id: str, run_id: str) -> Path:
        return self.run_dir(experiment_id, run_id) / "behavior_metrics.json"

    def episodes_dir(self, experiment_id: str, run_id: str) -> Path:
        return self.run_dir(experiment_id, run_id) / "episodes"

    def episode_path(
        self, experiment_id: str, run_id: str, episode_index: int,
    ) -> Path:
        return (
            self.episodes_dir(experiment_id, run_id)
            / f"episode_{episode_index:04d}.json"
        )

    # -- Directory creation -------------------------------------------------

    def create_experiment_dir(self, experiment_id: str) -> Path:
        """Create the experiment directory and its runs/ subdirectory."""
        exp_dir = self.experiment_dir(experiment_id)
        exp_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir(experiment_id).mkdir(exist_ok=True)
        return exp_dir

    def create_run_dir(self, experiment_id: str, run_id: str) -> Path:
        """Create the run directory and its episodes/ subdirectory."""
        r_dir = self.run_dir(experiment_id, run_id)
        r_dir.mkdir(parents=True, exist_ok=True)
        self.episodes_dir(experiment_id, run_id).mkdir(exist_ok=True)
        return r_dir

    # -- Save: immutable artifacts (overwrite=False) ------------------------

    def save_experiment_config(
        self, experiment_id: str, config: ExperimentConfig,
        *, overwrite: bool = False,
    ) -> Path:
        p = self.experiment_config_path(experiment_id)
        _save_json(p, config.model_dump(mode="json"), overwrite=overwrite)
        return p

    def save_experiment_summary(
        self, experiment_id: str, summary: ExperimentSummary,
        *, overwrite: bool = False,
    ) -> Path:
        p = self.experiment_summary_path(experiment_id)
        _save_json(p, summary.model_dump(mode="json"), overwrite=overwrite)
        return p

    def save_run_config(
        self, experiment_id: str, run_id: str, config: RunConfig,
        *, overwrite: bool = False,
    ) -> Path:
        p = self.run_config_path(experiment_id, run_id)
        _save_json(p, config.model_dump(mode="json"), overwrite=overwrite)
        return p

    def save_run_summary(
        self, experiment_id: str, run_id: str, summary: RunSummary,
        *, overwrite: bool = False,
    ) -> Path:
        p = self.run_summary_path(experiment_id, run_id)
        _save_json(p, summary.model_dump(mode="json"), overwrite=overwrite)
        return p

    def save_run_result(
        self,
        experiment_id: str,
        run_id: str,
        result: RunResult | LightRunResult | DeltaRunResult,
        *, overwrite: bool = False,
    ) -> Path:
        p = self.run_result_path(experiment_id, run_id)
        _save_json(p, result.model_dump(mode="json"), overwrite=overwrite)
        return p

    def save_behavior_metrics(
        self,
        experiment_id: str,
        run_id: str,
        metrics: RunBehaviorMetrics,
        *,
        overwrite: bool = False,
    ) -> Path:
        p = self.behavior_metrics_path(experiment_id, run_id)
        _save_json(p, metrics.model_dump(mode="json"), overwrite=overwrite)
        return p

    def save_episode_trace(
        self, experiment_id: str, run_id: str, episode_index: int,
        trace: BaseEpisodeTrace, *, overwrite: bool = False,
    ) -> Path:
        p = self.episode_path(experiment_id, run_id, episode_index)
        _save_json(p, trace.model_dump(mode="json"), overwrite=overwrite)
        return p

    def save_light_episode_result(
        self,
        experiment_id: str,
        run_id: str,
        episode_index: int,
        result: LightEpisodeResult,
        *,
        overwrite: bool = False,
    ) -> Path:
        p = self.episodes_dir(experiment_id, run_id) / f"episode_{episode_index:04d}.light.json"
        _save_json(p, result.model_dump(mode="json"), overwrite=overwrite)
        return p

    def save_delta_episode_trace(
        self,
        experiment_id: str,
        run_id: str,
        episode_index: int,
        trace: DeltaEpisodeTrace,
        *,
        overwrite: bool = False,
    ) -> Path:
        p = self.episode_path(experiment_id, run_id, episode_index)
        _save_json(p, trace.model_dump(mode="json"), overwrite=overwrite)
        return p

    # -- Save: mutable artifacts (overwrite=True) ---------------------------

    def save_experiment_metadata(
        self, experiment_id: str, metadata: ExperimentMetadata,
        *, overwrite: bool = True,
    ) -> Path:
        p = self.experiment_metadata_path(experiment_id)
        _save_json(p, metadata.model_dump(mode="json"), overwrite=overwrite)
        return p

    def save_experiment_status(
        self, experiment_id: str, status: ExperimentStatus,
        *, overwrite: bool = True,
    ) -> Path:
        p = self.experiment_status_path(experiment_id)
        record = ExperimentStatusRecord(status=status)
        _save_json(p, record.model_dump(mode="json"), overwrite=overwrite)
        return p

    def save_run_metadata(
        self, experiment_id: str, run_id: str, metadata: RunMetadata,
        *, overwrite: bool = True,
    ) -> Path:
        p = self.run_metadata_path(experiment_id, run_id)
        _save_json(p, metadata.model_dump(mode="json"), overwrite=overwrite)
        return p

    def save_run_status(
        self, experiment_id: str, run_id: str, status: RunStatus,
        *, overwrite: bool = True,
    ) -> Path:
        p = self.run_status_path(experiment_id, run_id)
        record = RunStatusRecord(status=status)
        _save_json(p, record.model_dump(mode="json"), overwrite=overwrite)
        return p

    # -- Load ---------------------------------------------------------------

    def load_experiment_config(self, experiment_id: str) -> ExperimentConfig:
        return ExperimentConfig.model_validate(
            _load_json(self.experiment_config_path(experiment_id)),
        )

    def load_experiment_metadata(self, experiment_id: str) -> ExperimentMetadata:
        return ExperimentMetadata.model_validate(
            _load_json(self.experiment_metadata_path(experiment_id)),
        )

    def load_experiment_status(self, experiment_id: str) -> ExperimentStatus:
        record = ExperimentStatusRecord.model_validate(
            _load_json(self.experiment_status_path(experiment_id)),
        )
        return record.status

    def load_experiment_summary(self, experiment_id: str) -> ExperimentSummary:
        return ExperimentSummary.model_validate(
            _load_json(self.experiment_summary_path(experiment_id)),
        )

    def load_run_config(self, experiment_id: str, run_id: str) -> RunConfig:
        return RunConfig.model_validate(
            _load_json(self.run_config_path(experiment_id, run_id)),
        )

    def load_run_metadata(self, experiment_id: str, run_id: str) -> RunMetadata:
        return RunMetadata.model_validate(
            _load_json(self.run_metadata_path(experiment_id, run_id)),
        )

    def load_run_status(self, experiment_id: str, run_id: str) -> RunStatus:
        record = RunStatusRecord.model_validate(
            _load_json(self.run_status_path(experiment_id, run_id)),
        )
        return record.status

    def load_run_summary(self, experiment_id: str, run_id: str) -> RunSummary:
        return RunSummary.model_validate(
            _load_json(self.run_summary_path(experiment_id, run_id)),
        )

    def load_run_result(
        self,
        experiment_id: str,
        run_id: str,
    ) -> RunResult | LightRunResult | DeltaRunResult:
        data = _load_json(self.run_result_path(experiment_id, run_id))
        if data.get("result_type") == "light_run":
            return LightRunResult.model_validate(data)
        if data.get("result_type") == "delta_run":
            return DeltaRunResult.model_validate(data)
        return RunResult.model_validate(data)

    def load_behavior_metrics(
        self,
        experiment_id: str,
        run_id: str,
    ) -> RunBehaviorMetrics:
        return RunBehaviorMetrics.model_validate(
            _load_json(self.behavior_metrics_path(experiment_id, run_id)),
        )

    def load_episode_trace(
        self, experiment_id: str, run_id: str, episode_index: int,
    ) -> BaseEpisodeTrace:
        data = _load_json(self.episode_path(experiment_id, run_id, episode_index))
        if data.get("result_type") == "delta_episode":
            delta_trace = DeltaEpisodeTrace.model_validate(data)
            return reconstruct_episode_trace(delta_trace)
        return BaseEpisodeTrace.model_validate(data)

    # -- Discovery ----------------------------------------------------------

    def list_experiments(self) -> list[str]:
        """Return sorted experiment IDs (subdirectory names under root)."""
        if not self._root.exists():
            return []
        return sorted(
            d.name for d in self._root.iterdir() if d.is_dir()
        )

    def list_runs(self, experiment_id: str) -> list[str]:
        """Return sorted run IDs within one experiment."""
        runs = self.runs_dir(experiment_id)
        if not runs.exists():
            return []
        return sorted(d.name for d in runs.iterdir() if d.is_dir())

    def list_episode_files(
        self, experiment_id: str, run_id: str,
    ) -> list[Path]:
        """Return sorted episode artifact file paths."""
        ep_dir = self.episodes_dir(experiment_id, run_id)
        if not ep_dir.exists():
            return []
        return sorted(ep_dir.glob("episode_*.json"))

    def artifact_exists(self, path: Path) -> bool:
        """Check whether an artifact file exists."""
        return path.exists()
