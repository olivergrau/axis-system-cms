"""Integration tests for ExperimentExecutor."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from axis_system_a import (
    ExperimentConfig,
    ExperimentExecutor,
    ExperimentRepository,
    ExperimentResult,
    ExperimentStatus,
    ExperimentType,
    RunConfig,
    RunStatus,
    execute_experiment,
)
from axis_system_a.run import RunExecutor
from tests.fixtures.scenario_fixtures import make_config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _baseline(**overrides):
    return make_config(overrides={
        "world": {"grid_width": 3, "grid_height": 3},
        "execution": {"max_steps": 5},
        "logging": {"enabled": False},
        **overrides,
    })


def _single_run_config(
    *, num_episodes: int = 2, base_seed: int = 42, name: str = "test-single",
) -> ExperimentConfig:
    return ExperimentConfig(
        experiment_type=ExperimentType.SINGLE_RUN,
        baseline=_baseline(),
        num_episodes_per_run=num_episodes,
        base_seed=base_seed,
        name=name,
    )


def _ofat_config(
    *, num_episodes: int = 2, base_seed: int = 42, name: str = "test-ofat",
) -> ExperimentConfig:
    return ExperimentConfig(
        experiment_type=ExperimentType.OFAT,
        baseline=_baseline(),
        num_episodes_per_run=num_episodes,
        base_seed=base_seed,
        name=name,
        parameter_path="execution.max_steps",
        parameter_values=(3, 5, 8),
    )


# ---------------------------------------------------------------------------
# Happy-path: single_run
# ---------------------------------------------------------------------------


class TestHappyPathSingleRun:
    def test_executes_successfully(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _single_run_config()
        result = ExperimentExecutor(repo).execute(config)
        assert isinstance(result, ExperimentResult)
        assert len(result.run_results) == 1
        assert result.summary.num_runs == 1

    def test_experiment_config_persisted(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _single_run_config()
        ExperimentExecutor(repo).execute(config)
        loaded = repo.load_experiment_config("test-single")
        assert loaded == config

    def test_experiment_summary_persisted(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _single_run_config()
        result = ExperimentExecutor(repo).execute(config)
        loaded = repo.load_experiment_summary("test-single")
        assert loaded == result.summary

    def test_run_artifacts_created(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _single_run_config()
        ExperimentExecutor(repo).execute(config)
        runs = repo.list_runs("test-single")
        assert len(runs) == 1
        # Run config and summary should be loadable
        run_id = runs[0]
        repo.load_run_config("test-single", run_id)
        repo.load_run_summary("test-single", run_id)
        repo.load_run_result("test-single", run_id)

    def test_episode_artifacts_created(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _single_run_config(num_episodes=3)
        ExperimentExecutor(repo).execute(config)
        run_id = repo.list_runs("test-single")[0]
        files = repo.list_episode_files("test-single", run_id)
        assert len(files) == 3
        assert files[0].name == "episode_0001.json"

    def test_convenience_function(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _single_run_config(name="test-conv")
        result = execute_experiment(config, repo)
        assert isinstance(result, ExperimentResult)
        assert result.summary.num_runs == 1


# ---------------------------------------------------------------------------
# Happy-path: ofat
# ---------------------------------------------------------------------------


class TestHappyPathOfat:
    def test_executes_all_runs(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _ofat_config()
        result = ExperimentExecutor(repo).execute(config)
        assert len(result.run_results) == 3
        assert result.summary.num_runs == 3

    def test_correct_number_of_run_dirs(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _ofat_config()
        ExperimentExecutor(repo).execute(config)
        runs = repo.list_runs("test-ofat")
        assert len(runs) == 3

    def test_varied_parameter_in_runs(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _ofat_config()
        result = ExperimentExecutor(repo).execute(config)
        max_steps = [
            rr.config.simulation.execution.max_steps
            for rr in result.run_results
        ]
        assert max_steps == [3, 5, 8]

    def test_summary_has_variation_descriptions(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _ofat_config()
        result = ExperimentExecutor(repo).execute(config)
        descs = [e.variation_description for e in result.summary.run_entries]
        assert descs == [
            "execution.max_steps=3",
            "execution.max_steps=5",
            "execution.max_steps=8",
        ]

    def test_ofat_has_baseline_deltas(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _ofat_config()
        result = ExperimentExecutor(repo).execute(config)
        # First entry (baseline) should have delta=0
        first = result.summary.run_entries[0]
        assert first.delta_mean_steps == 0.0
        assert first.delta_death_rate == 0.0


# ---------------------------------------------------------------------------
# Ordering tests
# ---------------------------------------------------------------------------


class TestOrdering:
    def test_runs_in_resolved_order(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _ofat_config()
        result = ExperimentExecutor(repo).execute(config)
        run_ids = [rr.run_id for rr in result.run_results]
        assert run_ids == ["run-0000", "run-0001", "run-0002"]

    def test_summary_preserves_order(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _ofat_config()
        result = ExperimentExecutor(repo).execute(config)
        entry_run_ids = [e.run_id for e in result.summary.run_entries]
        assert entry_run_ids == ["run-0000", "run-0001", "run-0002"]


# ---------------------------------------------------------------------------
# Status lifecycle tests
# ---------------------------------------------------------------------------


class TestStatusLifecycle:
    def test_experiment_completed(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _single_run_config()
        ExperimentExecutor(repo).execute(config)
        status = repo.load_experiment_status("test-single")
        assert status == ExperimentStatus.COMPLETED

    def test_run_completed(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _single_run_config()
        ExperimentExecutor(repo).execute(config)
        run_id = repo.list_runs("test-single")[0]
        status = repo.load_run_status("test-single", run_id)
        assert status == RunStatus.COMPLETED

    def test_all_ofat_runs_completed(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _ofat_config()
        ExperimentExecutor(repo).execute(config)
        for run_id in repo.list_runs("test-ofat"):
            status = repo.load_run_status("test-ofat", run_id)
            assert status == RunStatus.COMPLETED


# ---------------------------------------------------------------------------
# Failure handling tests
# ---------------------------------------------------------------------------


class _FailingRunExecutor(RunExecutor):
    """RunExecutor that fails on a specific run index."""

    def __init__(self, fail_on_index: int):
        self._call_count = 0
        self._fail_on_index = fail_on_index

    def execute(self, config: RunConfig):
        idx = self._call_count
        self._call_count += 1
        if idx == self._fail_on_index:
            raise RuntimeError(f"Simulated failure on run {idx}")
        return super().execute(config)


class TestFailureHandling:
    def test_first_run_fails_experiment_failed(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _ofat_config()
        executor = ExperimentExecutor(repo, run_executor=_FailingRunExecutor(0))
        with pytest.raises(RuntimeError, match="Simulated failure on run 0"):
            executor.execute(config)
        status = repo.load_experiment_status("test-ofat")
        assert status == ExperimentStatus.FAILED

    def test_second_run_fails_experiment_partial(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _ofat_config()
        executor = ExperimentExecutor(repo, run_executor=_FailingRunExecutor(1))
        with pytest.raises(RuntimeError, match="Simulated failure on run 1"):
            executor.execute(config)
        status = repo.load_experiment_status("test-ofat")
        assert status == ExperimentStatus.PARTIAL

    def test_failed_run_marked_failed(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _ofat_config()
        executor = ExperimentExecutor(repo, run_executor=_FailingRunExecutor(1))
        with pytest.raises(RuntimeError):
            executor.execute(config)
        # run-0000 completed, run-0001 failed
        assert repo.load_run_status("test-ofat", "run-0000") == RunStatus.COMPLETED
        assert repo.load_run_status("test-ofat", "run-0001") == RunStatus.FAILED

    def test_completed_runs_remain_valid(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _ofat_config()
        executor = ExperimentExecutor(repo, run_executor=_FailingRunExecutor(2))
        with pytest.raises(RuntimeError):
            executor.execute(config)
        # First two runs completed and are loadable
        repo.load_run_result("test-ofat", "run-0000")
        repo.load_run_result("test-ofat", "run-0001")

    def test_exception_propagates(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _single_run_config()
        executor = ExperimentExecutor(repo, run_executor=_FailingRunExecutor(0))
        with pytest.raises(RuntimeError):
            executor.execute(config)


# ---------------------------------------------------------------------------
# Determinism tests
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_config_same_summary(self, tmp_path):
        config = _single_run_config()
        repo1 = ExperimentRepository(tmp_path / "run1")
        repo2 = ExperimentRepository(tmp_path / "run2")
        r1 = ExperimentExecutor(repo1).execute(config)
        r2 = ExperimentExecutor(repo2).execute(config)
        assert r1.summary == r2.summary

    def test_same_ofat_same_ordering(self, tmp_path):
        config = _ofat_config()
        repo1 = ExperimentRepository(tmp_path / "run1")
        repo2 = ExperimentRepository(tmp_path / "run2")
        r1 = ExperimentExecutor(repo1).execute(config)
        r2 = ExperimentExecutor(repo2).execute(config)
        for i in range(3):
            assert r1.run_results[i].summary == r2.run_results[i].summary


# ---------------------------------------------------------------------------
# Repository integration tests
# ---------------------------------------------------------------------------


class TestRepositoryIntegration:
    def test_all_artifacts_loadable(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _single_run_config()
        ExperimentExecutor(repo).execute(config)
        eid = "test-single"
        # Experiment level
        repo.load_experiment_config(eid)
        repo.load_experiment_metadata(eid)
        repo.load_experiment_status(eid)
        repo.load_experiment_summary(eid)
        # Run level
        run_id = repo.list_runs(eid)[0]
        repo.load_run_config(eid, run_id)
        repo.load_run_metadata(eid, run_id)
        repo.load_run_status(eid, run_id)
        repo.load_run_summary(eid, run_id)
        repo.load_run_result(eid, run_id)

    def test_episode_results_loadable(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _single_run_config(num_episodes=3)
        ExperimentExecutor(repo).execute(config)
        run_id = repo.list_runs("test-single")[0]
        for i in range(1, 4):
            ep = repo.load_episode_result("test-single", run_id, i)
            assert ep.total_steps > 0

    def test_list_runs_returns_expected(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _ofat_config()
        ExperimentExecutor(repo).execute(config)
        runs = repo.list_runs("test-ofat")
        assert runs == ["run-0000", "run-0001", "run-0002"]

    def test_metadata_persisted_correctly(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _single_run_config()
        ExperimentExecutor(repo).execute(config)
        meta = repo.load_experiment_metadata("test-single")
        assert meta.experiment_id == "test-single"
        assert meta.experiment_type == "single_run"
        assert meta.name == "test-single"

    def test_run_metadata_persisted(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _ofat_config()
        ExperimentExecutor(repo).execute(config)
        meta = repo.load_run_metadata("test-ofat", "run-0001")
        assert meta.run_id == "run-0001"
        assert meta.experiment_id == "test-ofat"
        assert meta.variation_description == "execution.max_steps=5"
