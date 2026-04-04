"""Integration tests for experiment resume (WP15)."""

from __future__ import annotations

import json

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
    is_run_complete,
    resume_experiment,
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


class _CountingRunExecutor(RunExecutor):
    """RunExecutor that counts how many runs were actually executed."""

    def __init__(self):
        self.executed_count = 0

    def execute(self, config: RunConfig):
        self.executed_count += 1
        return super().execute(config)


def _run_and_fail(tmp_path, fail_on_index, config=None):
    """Run an experiment that fails at a specific run, return (repo, experiment_id)."""
    repo = ExperimentRepository(tmp_path)
    cfg = config or _ofat_config()
    executor = ExperimentExecutor(repo, run_executor=_FailingRunExecutor(fail_on_index))
    experiment_id = cfg.name
    with pytest.raises(RuntimeError):
        executor.execute(cfg)
    return repo, experiment_id


# ---------------------------------------------------------------------------
# is_run_complete tests
# ---------------------------------------------------------------------------


class TestIsRunComplete:
    def test_completed_with_all_artifacts(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _single_run_config()
        ExperimentExecutor(repo).execute(config)
        assert is_run_complete(repo, "test-single", "run-0000") is True

    def test_failed_status(self, tmp_path):
        repo, eid = _run_and_fail(tmp_path, 0, config=_ofat_config())
        assert is_run_complete(repo, eid, "run-0000") is False

    def test_running_status(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _single_run_config()
        ExperimentExecutor(repo).execute(config)
        # Manually set status to RUNNING (simulating interrupted execution)
        repo.save_run_status("test-single", "run-0000", RunStatus.RUNNING)
        assert is_run_complete(repo, "test-single", "run-0000") is False

    def test_completed_but_missing_result(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _single_run_config()
        ExperimentExecutor(repo).execute(config)
        # Remove the run_result.json
        repo.run_result_path("test-single", "run-0000").unlink()
        assert is_run_complete(repo, "test-single", "run-0000") is False

    def test_nonexistent_run(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        assert is_run_complete(repo, "no-such-exp", "no-such-run") is False


# ---------------------------------------------------------------------------
# Completed experiment resume tests
# ---------------------------------------------------------------------------


class TestCompletedExperimentResume:
    def test_no_runs_re_executed(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _ofat_config()
        ExperimentExecutor(repo).execute(config)
        counting = _CountingRunExecutor()
        result = ExperimentExecutor(repo, run_executor=counting).resume("test-ofat")
        assert counting.executed_count == 0
        assert isinstance(result, ExperimentResult)

    def test_summary_matches_original(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _ofat_config()
        original = ExperimentExecutor(repo).execute(config)
        resumed = ExperimentExecutor(repo).resume("test-ofat")
        assert resumed.summary == original.summary

    def test_single_run_completed_is_noop(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _single_run_config()
        original = ExperimentExecutor(repo).execute(config)
        counting = _CountingRunExecutor()
        resumed = ExperimentExecutor(repo, run_executor=counting).resume("test-single")
        assert counting.executed_count == 0
        assert resumed.summary == original.summary


# ---------------------------------------------------------------------------
# Partial experiment resume tests
# ---------------------------------------------------------------------------


class TestPartialExperimentResume:
    def test_resumes_failed_run(self, tmp_path):
        repo, eid = _run_and_fail(tmp_path, 2)
        result = ExperimentExecutor(repo).resume(eid)
        assert len(result.run_results) == 3
        assert result.summary.num_runs == 3

    def test_completed_runs_not_re_executed(self, tmp_path):
        repo, eid = _run_and_fail(tmp_path, 2)
        # Record timestamps of completed run artifacts before resume
        r0_mtime = repo.run_result_path(eid, "run-0000").stat().st_mtime_ns
        r1_mtime = repo.run_result_path(eid, "run-0001").stat().st_mtime_ns
        counting = _CountingRunExecutor()
        ExperimentExecutor(repo, run_executor=counting).resume(eid)
        # Only 1 run should have been executed (run-0002)
        assert counting.executed_count == 1
        # Completed run artifacts unchanged
        assert repo.run_result_path(eid, "run-0000").stat().st_mtime_ns == r0_mtime
        assert repo.run_result_path(eid, "run-0001").stat().st_mtime_ns == r1_mtime

    def test_final_summary_includes_all_runs(self, tmp_path):
        repo, eid = _run_and_fail(tmp_path, 2)
        result = ExperimentExecutor(repo).resume(eid)
        run_ids = [rr.run_id for rr in result.run_results]
        assert run_ids == ["run-0000", "run-0001", "run-0002"]

    def test_ofat_deltas_correct_after_resume(self, tmp_path):
        repo, eid = _run_and_fail(tmp_path, 2)
        result = ExperimentExecutor(repo).resume(eid)
        # First entry should have delta=0 (baseline)
        first = result.summary.run_entries[0]
        assert first.delta_mean_steps == 0.0
        assert first.delta_death_rate == 0.0
        # Variation descriptions present
        descs = [e.variation_description for e in result.summary.run_entries]
        assert descs == [
            "execution.max_steps=3",
            "execution.max_steps=5",
            "execution.max_steps=8",
        ]


# ---------------------------------------------------------------------------
# Status lifecycle tests
# ---------------------------------------------------------------------------


class TestStatusLifecycle:
    def test_experiment_completed_after_resume(self, tmp_path):
        repo, eid = _run_and_fail(tmp_path, 2)
        assert repo.load_experiment_status(eid) == ExperimentStatus.PARTIAL
        ExperimentExecutor(repo).resume(eid)
        assert repo.load_experiment_status(eid) == ExperimentStatus.COMPLETED

    def test_re_executed_run_completed(self, tmp_path):
        repo, eid = _run_and_fail(tmp_path, 2)
        assert repo.load_run_status(eid, "run-0002") == RunStatus.FAILED
        ExperimentExecutor(repo).resume(eid)
        assert repo.load_run_status(eid, "run-0002") == RunStatus.COMPLETED

    def test_previously_completed_runs_stay_completed(self, tmp_path):
        repo, eid = _run_and_fail(tmp_path, 2)
        ExperimentExecutor(repo).resume(eid)
        assert repo.load_run_status(eid, "run-0000") == RunStatus.COMPLETED
        assert repo.load_run_status(eid, "run-0001") == RunStatus.COMPLETED


# ---------------------------------------------------------------------------
# Idempotency tests
# ---------------------------------------------------------------------------


class TestIdempotency:
    def test_resume_completed_twice_same_result(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _ofat_config()
        ExperimentExecutor(repo).execute(config)
        r1 = ExperimentExecutor(repo).resume("test-ofat")
        r2 = ExperimentExecutor(repo).resume("test-ofat")
        assert r1.summary == r2.summary

    def test_resume_partial_then_resume_again(self, tmp_path):
        repo, eid = _run_and_fail(tmp_path, 2)
        r1 = ExperimentExecutor(repo).resume(eid)
        counting = _CountingRunExecutor()
        r2 = ExperimentExecutor(repo, run_executor=counting).resume(eid)
        assert counting.executed_count == 0
        assert r1.summary == r2.summary

    def test_no_run_executed_twice(self, tmp_path):
        repo, eid = _run_and_fail(tmp_path, 2)
        counting = _CountingRunExecutor()
        ExperimentExecutor(repo, run_executor=counting).resume(eid)
        assert counting.executed_count == 1  # only run-0002


# ---------------------------------------------------------------------------
# Artifact integrity tests
# ---------------------------------------------------------------------------


class TestArtifactIntegrity:
    def test_completed_run_artifacts_unchanged(self, tmp_path):
        repo, eid = _run_and_fail(tmp_path, 2)
        summary_before = repo.load_run_summary(eid, "run-0000")
        ExperimentExecutor(repo).resume(eid)
        summary_after = repo.load_run_summary(eid, "run-0000")
        assert summary_before == summary_after

    def test_all_artifacts_loadable_after_resume(self, tmp_path):
        repo, eid = _run_and_fail(tmp_path, 2)
        ExperimentExecutor(repo).resume(eid)
        # Experiment level
        repo.load_experiment_config(eid)
        repo.load_experiment_metadata(eid)
        repo.load_experiment_status(eid)
        repo.load_experiment_summary(eid)
        # All runs
        for run_id in ["run-0000", "run-0001", "run-0002"]:
            repo.load_run_config(eid, run_id)
            repo.load_run_metadata(eid, run_id)
            repo.load_run_status(eid, run_id)
            repo.load_run_summary(eid, run_id)
            repo.load_run_result(eid, run_id)


# ---------------------------------------------------------------------------
# Failure propagation tests
# ---------------------------------------------------------------------------


class TestFailurePropagation:
    def test_resume_fails_again_partial(self, tmp_path):
        repo, eid = _run_and_fail(tmp_path, 2)
        # Resume but the re-executed run fails again
        failing = _FailingRunExecutor(0)  # first call to execute will fail
        executor = ExperimentExecutor(repo, run_executor=failing)
        with pytest.raises(RuntimeError):
            executor.resume(eid)
        # Experiment is still PARTIAL (had 2 completed runs already)
        assert repo.load_experiment_status(eid) == ExperimentStatus.PARTIAL

    def test_completed_runs_preserved_after_resume_failure(self, tmp_path):
        repo, eid = _run_and_fail(tmp_path, 2)
        failing = _FailingRunExecutor(0)
        executor = ExperimentExecutor(repo, run_executor=failing)
        with pytest.raises(RuntimeError):
            executor.resume(eid)
        # Completed runs still valid
        repo.load_run_result(eid, "run-0000")
        repo.load_run_result(eid, "run-0001")
        assert repo.load_run_status(eid, "run-0000") == RunStatus.COMPLETED
        assert repo.load_run_status(eid, "run-0001") == RunStatus.COMPLETED


# ---------------------------------------------------------------------------
# Single-run resume tests
# ---------------------------------------------------------------------------


class TestSingleRunResume:
    def test_single_run_fail_then_resume(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _single_run_config()
        executor = ExperimentExecutor(repo, run_executor=_FailingRunExecutor(0))
        with pytest.raises(RuntimeError):
            executor.execute(config)
        result = ExperimentExecutor(repo).resume("test-single")
        assert isinstance(result, ExperimentResult)
        assert result.summary.num_runs == 1

    def test_single_run_completed_resume_noop(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        config = _single_run_config()
        ExperimentExecutor(repo).execute(config)
        counting = _CountingRunExecutor()
        result = ExperimentExecutor(repo, run_executor=counting).resume("test-single")
        assert counting.executed_count == 0
        assert result.summary.num_runs == 1


# ---------------------------------------------------------------------------
# Convenience function test
# ---------------------------------------------------------------------------


class TestConvenienceFunction:
    def test_resume_experiment_function(self, tmp_path):
        repo, eid = _run_and_fail(tmp_path, 2)
        result = resume_experiment(eid, repo)
        assert isinstance(result, ExperimentResult)
        assert result.summary.num_runs == 3
