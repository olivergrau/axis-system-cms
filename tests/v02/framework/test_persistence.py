"""Tests for the persistence layer (WP-3.4)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from axis.framework.config import (
    ExperimentConfig,
    ExperimentType,
    ExecutionConfig,
    GeneralConfig,
    LoggingConfig,
)
from axis.framework.experiment import ExperimentSummary, RunSummaryEntry
from axis.framework.persistence import (
    ExperimentMetadata,
    ExperimentRepository,
    ExperimentStatus,
    RunMetadata,
    RunStatus,
)
from axis.framework.run import (
    RunConfig,
    RunExecutor,
    RunResult,
    RunSummary,
)
from axis.sdk.position import Position
from axis.sdk.trace import BaseEpisodeTrace
from axis.sdk.world_types import BaseWorldConfig
from tests.v02.builders.config_builder import FrameworkConfigBuilder
from tests.v02.builders.system_config_builder import SystemAConfigBuilder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _experiment_config() -> ExperimentConfig:
    return ExperimentConfig(
        system_type="system_a",
        experiment_type=ExperimentType.SINGLE_RUN,
        general=GeneralConfig(seed=42),
        execution=ExecutionConfig(max_steps=10),
        world=BaseWorldConfig(grid_width=5, grid_height=5),
        logging=LoggingConfig(enabled=False),
        system=SystemAConfigBuilder().build(),
        num_episodes_per_run=1,
    )


def _run_config() -> RunConfig:
    return RunConfig(
        system_type="system_a",
        system_config=SystemAConfigBuilder().build(),
        framework_config=FrameworkConfigBuilder().with_max_steps(10).build(),
        num_episodes=1,
        base_seed=42,
    )


def _run_result() -> RunResult:
    """Run a real episode and return the result."""
    executor = RunExecutor()
    return executor.execute(_run_config())


# ---------------------------------------------------------------------------
# Status enum tests
# ---------------------------------------------------------------------------


class TestStatusEnums:
    """Status enum completeness."""

    def test_experiment_status_enum(self) -> None:
        assert ExperimentStatus.CREATED == "created"
        assert ExperimentStatus.RUNNING == "running"
        assert ExperimentStatus.COMPLETED == "completed"
        assert ExperimentStatus.FAILED == "failed"
        assert ExperimentStatus.PARTIAL == "partial"

    def test_run_status_enum(self) -> None:
        assert RunStatus.PENDING == "pending"
        assert RunStatus.RUNNING == "running"
        assert RunStatus.COMPLETED == "completed"
        assert RunStatus.FAILED == "failed"


# ---------------------------------------------------------------------------
# Metadata tests
# ---------------------------------------------------------------------------


class TestMetadata:
    """Metadata model construction."""

    def test_experiment_metadata_construction(self) -> None:
        meta = ExperimentMetadata(
            experiment_id="test-001",
            created_at="2024-01-01T00:00:00Z",
            experiment_type="single_run",
            system_type="system_a",
        )
        assert meta.system_type == "system_a"
        assert meta.experiment_id == "test-001"


# ---------------------------------------------------------------------------
# Path resolution tests
# ---------------------------------------------------------------------------


class TestPathResolution:
    """All path methods produce correct paths."""

    def test_path_resolution(self, tmp_path: Path) -> None:
        repo = ExperimentRepository(tmp_path)
        eid = "exp-001"
        rid = "run-0000"

        assert repo.experiment_dir(eid) == tmp_path / eid
        assert repo.experiment_config_path(eid) == tmp_path / eid / "experiment_config.json"
        assert repo.experiment_metadata_path(eid) == tmp_path / eid / "experiment_metadata.json"
        assert repo.experiment_status_path(eid) == tmp_path / eid / "experiment_status.json"
        assert repo.experiment_summary_path(eid) == tmp_path / eid / "experiment_summary.json"
        assert repo.runs_dir(eid) == tmp_path / eid / "runs"
        assert repo.run_dir(eid, rid) == tmp_path / eid / "runs" / rid
        assert repo.run_config_path(eid, rid) == tmp_path / eid / "runs" / rid / "run_config.json"
        assert repo.episodes_dir(eid, rid) == tmp_path / eid / "runs" / rid / "episodes"
        assert repo.episode_path(eid, rid, 1) == tmp_path / eid / "runs" / rid / "episodes" / "episode_0001.json"


# ---------------------------------------------------------------------------
# Directory creation
# ---------------------------------------------------------------------------


class TestDirectoryCreation:
    """Directory creation methods."""

    def test_directory_creation(self, tmp_path: Path) -> None:
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        assert repo.experiment_dir("exp-001").is_dir()
        assert repo.runs_dir("exp-001").is_dir()

        repo.create_run_dir("exp-001", "run-0000")
        assert repo.run_dir("exp-001", "run-0000").is_dir()
        assert repo.episodes_dir("exp-001", "run-0000").is_dir()

        # Idempotent
        repo.create_experiment_dir("exp-001")
        repo.create_run_dir("exp-001", "run-0000")


# ---------------------------------------------------------------------------
# Save/load roundtrip tests
# ---------------------------------------------------------------------------


class TestRoundtrip:
    """Save/load roundtrips for all artifact types."""

    def test_experiment_config(self, tmp_path: Path) -> None:
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp")
        config = _experiment_config()
        repo.save_experiment_config("exp", config)
        loaded = repo.load_experiment_config("exp")
        assert loaded.system_type == config.system_type

    def test_run_config(self, tmp_path: Path) -> None:
        repo = ExperimentRepository(tmp_path)
        repo.create_run_dir("exp", "run")
        config = _run_config()
        repo.save_run_config("exp", "run", config)
        loaded = repo.load_run_config("exp", "run")
        assert loaded.system_type == config.system_type

    def test_run_summary(self, tmp_path: Path) -> None:
        repo = ExperimentRepository(tmp_path)
        repo.create_run_dir("exp", "run")
        summary = RunSummary(
            num_episodes=2, mean_steps=10.0, std_steps=1.0,
            mean_final_vitality=0.5, std_final_vitality=0.1,
            death_rate=0.25,
        )
        repo.save_run_summary("exp", "run", summary)
        loaded = repo.load_run_summary("exp", "run")
        assert loaded.mean_final_vitality == 0.5

    def test_run_result(self, tmp_path: Path) -> None:
        repo = ExperimentRepository(tmp_path)
        repo.create_run_dir("exp", "run")
        result = _run_result()
        repo.save_run_result("exp", "run", result)
        loaded = repo.load_run_result("exp", "run")
        assert loaded.num_episodes == result.num_episodes

    def test_episode_trace(self, tmp_path: Path) -> None:
        repo = ExperimentRepository(tmp_path)
        repo.create_run_dir("exp", "run")
        result = _run_result()
        trace = result.episode_traces[0]
        repo.save_episode_trace("exp", "run", 1, trace)
        loaded = repo.load_episode_trace("exp", "run", 1)
        assert loaded.system_type == trace.system_type

    def test_experiment_summary(self, tmp_path: Path) -> None:
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp")
        summary = ExperimentSummary(num_runs=1, run_entries=())
        repo.save_experiment_summary("exp", summary)
        loaded = repo.load_experiment_summary("exp")
        assert loaded.num_runs == 1

    def test_status(self, tmp_path: Path) -> None:
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp")
        repo.create_run_dir("exp", "run")
        repo.save_experiment_status("exp", ExperimentStatus.RUNNING)
        assert repo.load_experiment_status("exp") == ExperimentStatus.RUNNING
        repo.save_run_status("exp", "run", RunStatus.COMPLETED)
        assert repo.load_run_status("exp", "run") == RunStatus.COMPLETED

    def test_metadata(self, tmp_path: Path) -> None:
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp")
        repo.create_run_dir("exp", "run")
        exp_meta = ExperimentMetadata(
            experiment_id="exp", created_at="now",
            experiment_type="single_run", system_type="system_a",
        )
        repo.save_experiment_metadata("exp", exp_meta)
        loaded_exp = repo.load_experiment_metadata("exp")
        assert loaded_exp.experiment_id == "exp"

        run_meta = RunMetadata(
            run_id="run", experiment_id="exp", created_at="now",
        )
        repo.save_run_metadata("exp", "run", run_meta)
        loaded_run = repo.load_run_metadata("exp", "run")
        assert loaded_run.run_id == "run"


# ---------------------------------------------------------------------------
# Immutability semantics
# ---------------------------------------------------------------------------


class TestImmutability:
    """Immutable/mutable write semantics."""

    def test_immutable_write_semantics(self, tmp_path: Path) -> None:
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp")
        config = _experiment_config()
        repo.save_experiment_config("exp", config)
        with pytest.raises(FileExistsError):
            repo.save_experiment_config("exp", config)

    def test_overwrite_flag(self, tmp_path: Path) -> None:
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp")
        config = _experiment_config()
        repo.save_experiment_config("exp", config)
        repo.save_experiment_config("exp", config, overwrite=True)


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


class TestDiscovery:
    """Discovery/listing methods."""

    def test_list_experiments(self, tmp_path: Path) -> None:
        repo = ExperimentRepository(tmp_path)
        assert repo.list_experiments() == []
        repo.create_experiment_dir("exp-b")
        repo.create_experiment_dir("exp-a")
        assert repo.list_experiments() == ["exp-a", "exp-b"]

    def test_list_runs(self, tmp_path: Path) -> None:
        repo = ExperimentRepository(tmp_path)
        assert repo.list_runs("exp") == []
        repo.create_run_dir("exp", "run-0001")
        repo.create_run_dir("exp", "run-0000")
        assert repo.list_runs("exp") == ["run-0000", "run-0001"]

    def test_list_episode_files(self, tmp_path: Path) -> None:
        repo = ExperimentRepository(tmp_path)
        repo.create_run_dir("exp", "run")
        result = _run_result()
        repo.save_episode_trace("exp", "run", 1, result.episode_traces[0])
        files = repo.list_episode_files("exp", "run")
        assert len(files) == 1

    def test_artifact_exists(self, tmp_path: Path) -> None:
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp")
        p = repo.experiment_config_path("exp")
        assert not repo.artifact_exists(p)
        repo.save_experiment_config("exp", _experiment_config())
        assert repo.artifact_exists(p)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrors:
    """Error cases."""

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        repo = ExperimentRepository(tmp_path)
        with pytest.raises(FileNotFoundError):
            repo.load_experiment_config("nonexistent")

    def test_malformed_json_raises(self, tmp_path: Path) -> None:
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp")
        p = repo.experiment_config_path("exp")
        p.write_text("not valid json {{{")
        with pytest.raises(json.JSONDecodeError):
            repo.load_experiment_config("exp")
