"""Tests for executor + persistence integration (WP-3.4)."""

from __future__ import annotations

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
from axis.framework.experiment import (
    ExperimentExecutor,
    ExperimentResult,
    is_run_complete,
)
from axis.framework.persistence import (
    ExperimentRepository,
    ExperimentStatus,
    RunStatus,
)
from axis.sdk.world_types import BaseWorldConfig
from tests.v02.builders.system_config_builder import SystemAConfigBuilder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _single_run_config(
    *, num_episodes: int = 2, max_steps: int = 10,
) -> ExperimentConfig:
    return ExperimentConfig(
        system_type="system_a",
        experiment_type=ExperimentType.SINGLE_RUN,
        general=GeneralConfig(seed=42),
        execution=ExecutionConfig(max_steps=max_steps),
        world=BaseWorldConfig(grid_width=5, grid_height=5),
        logging=LoggingConfig(enabled=False),
        system=SystemAConfigBuilder().build(),
        num_episodes_per_run=num_episodes,
    )


def _execute(tmp_path: Path, config: ExperimentConfig | None = None) -> tuple[ExperimentResult, ExperimentRepository]:
    """Execute with persistence and return (result, repo)."""
    repo = ExperimentRepository(tmp_path)
    executor = ExperimentExecutor(repository=repo)
    cfg = config or _single_run_config()
    result = executor.execute(cfg)
    return result, repo


# ---------------------------------------------------------------------------
# Execute with persistence tests
# ---------------------------------------------------------------------------


class TestExecuteWithPersistence:
    """Persistence during execution."""

    def test_execute_creates_experiment_dir(self, tmp_path: Path) -> None:
        result, repo = _execute(tmp_path)
        experiments = repo.list_experiments()
        assert len(experiments) == 1

    def test_execute_saves_config(self, tmp_path: Path) -> None:
        result, repo = _execute(tmp_path)
        eid = repo.list_experiments()[0]
        loaded = repo.load_experiment_config(eid)
        assert loaded.system_type == "system_a"

    def test_execute_saves_metadata(self, tmp_path: Path) -> None:
        result, repo = _execute(tmp_path)
        eid = repo.list_experiments()[0]
        meta = repo.load_experiment_metadata(eid)
        assert meta.system_type == "system_a"

    def test_execute_saves_status_completed(self, tmp_path: Path) -> None:
        result, repo = _execute(tmp_path)
        eid = repo.list_experiments()[0]
        status = repo.load_experiment_status(eid)
        assert status == ExperimentStatus.COMPLETED

    def test_execute_saves_run_artifacts(self, tmp_path: Path) -> None:
        result, repo = _execute(tmp_path)
        eid = repo.list_experiments()[0]
        runs = repo.list_runs(eid)
        assert len(runs) == 1
        rid = runs[0]
        # All artifacts exist
        assert repo.artifact_exists(repo.run_config_path(eid, rid))
        assert repo.artifact_exists(repo.run_summary_path(eid, rid))
        assert repo.artifact_exists(repo.run_result_path(eid, rid))

    def test_execute_episode_count(self, tmp_path: Path) -> None:
        cfg = _single_run_config(num_episodes=3)
        result, repo = _execute(tmp_path, cfg)
        eid = repo.list_experiments()[0]
        rid = repo.list_runs(eid)[0]
        files = repo.list_episode_files(eid, rid)
        assert len(files) == 3

    def test_execute_episode_naming(self, tmp_path: Path) -> None:
        result, repo = _execute(tmp_path)
        eid = repo.list_experiments()[0]
        rid = repo.list_runs(eid)[0]
        files = repo.list_episode_files(eid, rid)
        assert files[0].name == "episode_0001.json"


# ---------------------------------------------------------------------------
# Resume tests
# ---------------------------------------------------------------------------


class TestResume:
    """Resume functionality."""

    def test_resume_skips_completed_runs(self, tmp_path: Path) -> None:
        result, repo = _execute(tmp_path)
        eid = repo.list_experiments()[0]

        # Resume should succeed and return same summary
        executor = ExperimentExecutor(repository=repo)
        resumed = executor.resume(eid)
        assert resumed.summary.num_runs == result.summary.num_runs

    def test_resume_reexecutes_incomplete(self, tmp_path: Path) -> None:
        # Execute normally
        result, repo = _execute(tmp_path)
        eid = repo.list_experiments()[0]
        rid = repo.list_runs(eid)[0]

        # Corrupt the run status to simulate incomplete
        repo.save_run_status(eid, rid, RunStatus.FAILED)

        # Resume should re-execute
        executor = ExperimentExecutor(repository=repo)
        resumed = executor.resume(eid)
        assert resumed.summary.num_runs == 1

        # Status should be completed again
        assert repo.load_run_status(eid, rid) == RunStatus.COMPLETED

    def test_resume_requires_repository(self) -> None:
        executor = ExperimentExecutor()
        with pytest.raises(RuntimeError, match="requires a repository"):
            executor.resume("some-id")

    def test_resume_deterministic(self, tmp_path: Path) -> None:
        result, repo = _execute(tmp_path)
        eid = repo.list_experiments()[0]

        executor = ExperimentExecutor(repository=repo)
        resumed = executor.resume(eid)

        # Summaries should match (resumed uses cached results)
        assert (
            resumed.summary.run_entries[0].summary.mean_steps
            == result.summary.run_entries[0].summary.mean_steps
        )


# ---------------------------------------------------------------------------
# is_run_complete
# ---------------------------------------------------------------------------


class TestIsRunComplete:
    """Run completion checking."""

    def test_is_run_complete(self, tmp_path: Path) -> None:
        result, repo = _execute(tmp_path)
        eid = repo.list_experiments()[0]
        rid = repo.list_runs(eid)[0]
        assert is_run_complete(repo, eid, rid) is True

    def test_is_run_complete_false_no_status(self, tmp_path: Path) -> None:
        repo = ExperimentRepository(tmp_path)
        assert is_run_complete(repo, "nope", "nope") is False


# ---------------------------------------------------------------------------
# Without repository (pure computation)
# ---------------------------------------------------------------------------


class TestWithoutRepository:
    """Executor works without repository (pure in-memory)."""

    def test_execute_without_repository(self) -> None:
        executor = ExperimentExecutor()
        result = executor.execute(_single_run_config())
        assert isinstance(result, ExperimentResult)
        assert result.summary.num_runs == 1
