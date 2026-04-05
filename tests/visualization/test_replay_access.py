"""Tests for the ReplayAccessService."""

from __future__ import annotations

from pathlib import Path

import pytest

from axis_system_a.experiment import ExperimentConfig
from axis_system_a.repository import ExperimentMetadata, ExperimentRepository, RunMetadata
from axis_system_a.results import EpisodeResult
from axis_system_a.run import RunConfig, RunSummary
from axis_system_a.visualization.errors import (
    EpisodeNotFoundError,
    ExperimentNotFoundError,
    MalformedArtifactError,
    ReplayContractViolation,
    RunNotFoundError,
)
from axis_system_a.visualization.replay_access import ReplayAccessService
from axis_system_a.visualization.replay_models import (
    ReplayEpisodeHandle,
    ReplayExperimentHandle,
    ReplayRunHandle,
    ReplayValidationResult,
)


# ---------------------------------------------------------------------------
# Discovery tests
# ---------------------------------------------------------------------------


class TestDiscovery:
    def test_list_experiments_empty(self, tmp_path: Path):
        repo = ExperimentRepository(tmp_path)
        svc = ReplayAccessService(repo)
        assert svc.list_experiments() == ()

    def test_list_experiments(self, access_service: ReplayAccessService):
        exps = access_service.list_experiments()
        assert "test-exp" in exps

    def test_list_runs(self, access_service: ReplayAccessService):
        runs = access_service.list_runs("test-exp")
        assert "run-0000" in runs

    def test_list_runs_missing_experiment(
        self, access_service: ReplayAccessService,
    ):
        with pytest.raises(ExperimentNotFoundError):
            access_service.list_runs("nonexistent")

    def test_list_episode_indices(
        self, access_service: ReplayAccessService,
    ):
        indices = access_service.list_episode_indices("test-exp", "run-0000")
        assert 1 in indices

    def test_list_episode_indices_missing_run(
        self, access_service: ReplayAccessService,
    ):
        with pytest.raises(RunNotFoundError):
            access_service.list_episode_indices("test-exp", "nonexistent")


# ---------------------------------------------------------------------------
# Handle tests
# ---------------------------------------------------------------------------


class TestHandles:
    def test_experiment_handle(self, access_service: ReplayAccessService):
        h = access_service.get_experiment_handle("test-exp")
        assert isinstance(h, ReplayExperimentHandle)
        assert h.experiment_id == "test-exp"
        assert isinstance(h.experiment_config, ExperimentConfig)
        assert isinstance(h.experiment_metadata, ExperimentMetadata)
        assert "run-0000" in h.available_runs

    def test_experiment_handle_missing(
        self, access_service: ReplayAccessService,
    ):
        with pytest.raises(ExperimentNotFoundError):
            access_service.get_experiment_handle("missing")

    def test_run_handle(self, access_service: ReplayAccessService):
        h = access_service.get_run_handle("test-exp", "run-0000")
        assert isinstance(h, ReplayRunHandle)
        assert h.run_id == "run-0000"
        assert isinstance(h.run_config, RunConfig)
        assert isinstance(h.run_metadata, RunMetadata)
        assert isinstance(h.run_summary, RunSummary)
        assert 1 in h.available_episodes

    def test_run_handle_missing_run(
        self, access_service: ReplayAccessService,
    ):
        with pytest.raises(RunNotFoundError):
            access_service.get_run_handle("test-exp", "missing")


# ---------------------------------------------------------------------------
# Artifact loading tests
# ---------------------------------------------------------------------------


class TestArtifactLoading:
    def test_load_experiment_config(
        self, access_service: ReplayAccessService,
    ):
        cfg = access_service.load_experiment_config("test-exp")
        assert isinstance(cfg, ExperimentConfig)

    def test_load_experiment_config_missing(
        self, access_service: ReplayAccessService,
    ):
        with pytest.raises(ExperimentNotFoundError):
            access_service.load_experiment_config("missing")

    def test_load_run_config(self, access_service: ReplayAccessService):
        cfg = access_service.load_run_config("test-exp", "run-0000")
        assert isinstance(cfg, RunConfig)

    def test_load_run_config_missing_run(
        self, access_service: ReplayAccessService,
    ):
        with pytest.raises(RunNotFoundError):
            access_service.load_run_config("test-exp", "missing")

    def test_load_episode_result(self, access_service: ReplayAccessService):
        ep = access_service.load_episode_result("test-exp", "run-0000", 1)
        assert isinstance(ep, EpisodeResult)
        assert len(ep.steps) > 0

    def test_load_episode_missing(self, access_service: ReplayAccessService):
        with pytest.raises(EpisodeNotFoundError):
            access_service.load_episode_result("test-exp", "run-0000", 999)


# ---------------------------------------------------------------------------
# Replay loading + validation tests
# ---------------------------------------------------------------------------


class TestReplayLoading:
    def test_load_replay_episode(self, access_service: ReplayAccessService):
        h = access_service.load_replay_episode("test-exp", "run-0000", 1)
        assert isinstance(h, ReplayEpisodeHandle)
        assert h.validation.valid is True
        assert h.episode_index == 1
        assert isinstance(h.episode_result, EpisodeResult)

    def test_load_replay_episode_missing(
        self, access_service: ReplayAccessService,
    ):
        with pytest.raises(EpisodeNotFoundError):
            access_service.load_replay_episode("test-exp", "run-0000", 999)

    def test_validate_episode(self, access_service: ReplayAccessService):
        result = access_service.validate_episode("test-exp", "run-0000", 1)
        assert isinstance(result, ReplayValidationResult)
        assert result.valid is True


# ---------------------------------------------------------------------------
# Repository boundary tests
# ---------------------------------------------------------------------------


class TestRepositoryBoundary:
    """Verify no Path objects leak through the public API."""

    def test_list_experiments_returns_strings(
        self, access_service: ReplayAccessService,
    ):
        for exp in access_service.list_experiments():
            assert isinstance(exp, str)

    def test_list_runs_returns_strings(
        self, access_service: ReplayAccessService,
    ):
        for run in access_service.list_runs("test-exp"):
            assert isinstance(run, str)

    def test_list_episodes_returns_ints(
        self, access_service: ReplayAccessService,
    ):
        for idx in access_service.list_episode_indices("test-exp", "run-0000"):
            assert isinstance(idx, int)

    def test_exceptions_are_viz_typed(
        self, access_service: ReplayAccessService,
    ):
        """All errors raised are from the visualization error hierarchy."""
        from axis_system_a.visualization.errors import ReplayError

        with pytest.raises(ReplayError):
            access_service.load_experiment_config("nonexistent")

        with pytest.raises(ReplayError):
            access_service.load_run_config("test-exp", "nonexistent")

        with pytest.raises(ReplayError):
            access_service.load_episode_result("test-exp", "run-0000", 999)


# ---------------------------------------------------------------------------
# Optional metadata tests
# ---------------------------------------------------------------------------


class TestOptionalMetadata:
    def test_run_handle_without_metadata(
        self, populated_repo: ExperimentRepository,
    ):
        """Run handle works even if optional metadata is missing."""
        # Remove the metadata file
        meta_path = populated_repo.run_metadata_path("test-exp", "run-0000")
        meta_path.unlink()
        svc = ReplayAccessService(populated_repo)
        h = svc.get_run_handle("test-exp", "run-0000")
        assert h.run_metadata is None

    def test_experiment_handle_without_metadata(
        self, populated_repo: ExperimentRepository,
    ):
        """Experiment handle works even if optional metadata is missing."""
        meta_path = populated_repo.experiment_metadata_path("test-exp")
        meta_path.unlink()
        svc = ReplayAccessService(populated_repo)
        h = svc.get_experiment_handle("test-exp")
        assert h.experiment_metadata is None
