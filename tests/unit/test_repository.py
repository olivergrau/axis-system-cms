"""Tests for the persistence layer and repository model."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from axis_system_a import (
    ExperimentConfig,
    ExperimentMetadata,
    ExperimentRepository,
    ExperimentResult,
    ExperimentStatus,
    ExperimentStatusRecord,
    ExperimentSummary,
    ExperimentType,
    Position,
    RunConfig,
    RunMetadata,
    RunResult,
    RunStatus,
    RunStatusRecord,
    RunSummary,
    RunSummaryEntry,
)
from axis_system_a.experiment import compute_experiment_summary
from axis_system_a.results import EpisodeResult
from axis_system_a.run import compute_run_summary
from axis_system_a.runner import run_episode
from axis_system_a.world import create_world
from tests.fixtures.scenario_fixtures import make_config
from tests.utils.assertions import assert_model_frozen


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _baseline():
    return make_config(overrides={
        "world": {"grid_width": 3, "grid_height": 3},
        "execution": {"max_steps": 5},
        "logging": {"enabled": False},
    })


def _make_experiment_config():
    return ExperimentConfig(
        experiment_type=ExperimentType.SINGLE_RUN,
        baseline=_baseline(),
        num_episodes_per_run=3,
        base_seed=42,
    )


def _make_run_config(run_id="run-0000"):
    return RunConfig(
        simulation=_baseline(),
        num_episodes=3,
        base_seed=42,
        run_id=run_id,
    )


def _make_run_summary():
    return RunSummary(
        num_episodes=1, mean_steps=5.0, std_steps=0.0,
        mean_final_energy=45.0, std_final_energy=0.0,
        death_rate=0.0, mean_consumption_count=0.0,
        std_consumption_count=0.0,
    )


def _make_episode_result():
    sim = _baseline()
    world = create_world(sim.world, Position(x=0, y=0))
    return run_episode(sim, world)


def _make_run_result(run_id="run-0000"):
    sim = _baseline()
    rc = RunConfig(simulation=sim, num_episodes=1, base_seed=42, run_id=run_id)
    world = create_world(sim.world, Position(x=0, y=0))
    ep = run_episode(sim, world)
    summary = compute_run_summary((ep,))
    return RunResult(
        run_id=run_id, num_episodes=1,
        episode_results=(ep,), summary=summary,
        seeds=(42,), config=rc,
    )


def _make_experiment_summary():
    entry = RunSummaryEntry(
        run_id="run-0000",
        variation_description="baseline",
        summary=_make_run_summary(),
    )
    return ExperimentSummary(num_runs=1, run_entries=(entry,))


def _make_experiment_result():
    cfg = _make_experiment_config()
    rr = _make_run_result()
    es = compute_experiment_summary((rr,), cfg)
    return ExperimentResult(
        experiment_config=cfg,
        run_results=(rr,),
        summary=es,
    )


def _make_experiment_metadata(experiment_id="exp-001"):
    return ExperimentMetadata(
        experiment_id=experiment_id,
        created_at="2026-01-01T00:00:00Z",
        experiment_type="single_run",
        name="test-exp",
    )


def _make_run_metadata(run_id="run-0000", experiment_id="exp-001"):
    return RunMetadata(
        run_id=run_id,
        experiment_id=experiment_id,
        variation_description="baseline",
        created_at="2026-01-01T00:00:00Z",
        base_seed=42,
    )


# ---------------------------------------------------------------------------
# Status enum tests
# ---------------------------------------------------------------------------


class TestExperimentStatus:
    def test_valid_values(self):
        assert ExperimentStatus.CREATED.value == "created"
        assert ExperimentStatus.RUNNING.value == "running"
        assert ExperimentStatus.COMPLETED.value == "completed"
        assert ExperimentStatus.FAILED.value == "failed"
        assert ExperimentStatus.PARTIAL.value == "partial"

    def test_invalid_value(self):
        with pytest.raises(ValueError):
            ExperimentStatus("unknown")


class TestRunStatus:
    def test_valid_values(self):
        assert RunStatus.PENDING.value == "pending"
        assert RunStatus.RUNNING.value == "running"
        assert RunStatus.COMPLETED.value == "completed"
        assert RunStatus.FAILED.value == "failed"

    def test_invalid_value(self):
        with pytest.raises(ValueError):
            RunStatus("unknown")


# ---------------------------------------------------------------------------
# Metadata model tests
# ---------------------------------------------------------------------------


class TestExperimentMetadata:
    def test_valid_construction(self):
        m = _make_experiment_metadata()
        assert m.experiment_id == "exp-001"
        assert m.experiment_type == "single_run"

    def test_frozen(self):
        m = _make_experiment_metadata()
        assert_model_frozen(m, "experiment_id", "other")

    def test_model_dump_roundtrip(self):
        m = _make_experiment_metadata()
        d = m.model_dump(mode="json")
        restored = ExperimentMetadata.model_validate(d)
        assert restored == m


class TestRunMetadata:
    def test_valid_construction(self):
        m = _make_run_metadata()
        assert m.run_id == "run-0000"
        assert m.experiment_id == "exp-001"

    def test_frozen(self):
        m = _make_run_metadata()
        assert_model_frozen(m, "run_id", "other")

    def test_model_dump_roundtrip(self):
        m = _make_run_metadata()
        d = m.model_dump(mode="json")
        restored = RunMetadata.model_validate(d)
        assert restored == m


# ---------------------------------------------------------------------------
# Status record wrapper tests
# ---------------------------------------------------------------------------


class TestStatusRecords:
    def test_experiment_status_record(self):
        r = ExperimentStatusRecord(status=ExperimentStatus.RUNNING)
        assert r.status == ExperimentStatus.RUNNING
        d = r.model_dump(mode="json")
        assert d == {"status": "running"}

    def test_run_status_record(self):
        r = RunStatusRecord(status=RunStatus.PENDING)
        assert r.status == RunStatus.PENDING
        d = r.model_dump(mode="json")
        assert d == {"status": "pending"}


# ---------------------------------------------------------------------------
# Path resolution tests
# ---------------------------------------------------------------------------


class TestPathResolution:
    def test_experiment_dir(self):
        repo = ExperimentRepository(Path("/data/experiments"))
        assert repo.experiment_dir("exp-001") == Path("/data/experiments/exp-001")

    def test_experiment_config_path(self):
        repo = ExperimentRepository(Path("/data/experiments"))
        p = repo.experiment_config_path("exp-001")
        assert p == Path("/data/experiments/exp-001/experiment_config.json")

    def test_experiment_metadata_path(self):
        repo = ExperimentRepository(Path("/data/experiments"))
        p = repo.experiment_metadata_path("exp-001")
        assert p == Path("/data/experiments/exp-001/experiment_metadata.json")

    def test_experiment_status_path(self):
        repo = ExperimentRepository(Path("/data/experiments"))
        p = repo.experiment_status_path("exp-001")
        assert p == Path("/data/experiments/exp-001/experiment_status.json")

    def test_experiment_summary_path(self):
        repo = ExperimentRepository(Path("/data/experiments"))
        p = repo.experiment_summary_path("exp-001")
        assert p == Path("/data/experiments/exp-001/experiment_summary.json")

    def test_runs_dir(self):
        repo = ExperimentRepository(Path("/data/experiments"))
        assert repo.runs_dir("exp-001") == Path("/data/experiments/exp-001/runs")

    def test_run_dir(self):
        repo = ExperimentRepository(Path("/data/experiments"))
        p = repo.run_dir("exp-001", "run-0000")
        assert p == Path("/data/experiments/exp-001/runs/run-0000")

    def test_run_config_path(self):
        repo = ExperimentRepository(Path("/data/experiments"))
        p = repo.run_config_path("exp-001", "run-0000")
        assert p == Path("/data/experiments/exp-001/runs/run-0000/run_config.json")

    def test_run_result_path(self):
        repo = ExperimentRepository(Path("/data/experiments"))
        p = repo.run_result_path("exp-001", "run-0000")
        assert p == Path("/data/experiments/exp-001/runs/run-0000/run_result.json")

    def test_episode_path_1_based(self):
        repo = ExperimentRepository(Path("/data/experiments"))
        p = repo.episode_path("exp-001", "run-0000", 1)
        assert p.name == "episode_0001.json"

    def test_episode_path_large_index(self):
        repo = ExperimentRepository(Path("/data/experiments"))
        p = repo.episode_path("exp-001", "run-0000", 42)
        assert p.name == "episode_0042.json"

    def test_run_log_path(self):
        repo = ExperimentRepository(Path("/data/experiments"))
        p = repo.run_log_path("exp-001", "run-0000")
        assert p == Path(
            "/data/experiments/exp-001/runs/run-0000/logs/run.log.jsonl"
        )

    def test_deterministic(self):
        repo = ExperimentRepository(Path("/data/experiments"))
        p1 = repo.experiment_config_path("exp-001")
        p2 = repo.experiment_config_path("exp-001")
        assert p1 == p2


# ---------------------------------------------------------------------------
# Directory creation tests
# ---------------------------------------------------------------------------


class TestDirectoryCreation:
    def test_create_experiment_dir(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        exp_dir = repo.create_experiment_dir("exp-001")
        assert exp_dir.is_dir()
        assert repo.runs_dir("exp-001").is_dir()

    def test_create_run_dir(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        run_dir = repo.create_run_dir("exp-001", "run-0000")
        assert run_dir.is_dir()
        assert repo.episodes_dir("exp-001", "run-0000").is_dir()

    def test_idempotent(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        repo.create_experiment_dir("exp-001")  # no error
        assert repo.experiment_dir("exp-001").is_dir()


# ---------------------------------------------------------------------------
# Save/load roundtrip tests
# ---------------------------------------------------------------------------


class TestSaveLoadRoundtrip:
    def test_experiment_config(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        cfg = _make_experiment_config()
        repo.save_experiment_config("exp-001", cfg)
        loaded = repo.load_experiment_config("exp-001")
        assert loaded == cfg

    def test_experiment_metadata(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        m = _make_experiment_metadata()
        repo.save_experiment_metadata("exp-001", m)
        loaded = repo.load_experiment_metadata("exp-001")
        assert loaded == m

    def test_experiment_status(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        repo.save_experiment_status("exp-001", ExperimentStatus.RUNNING)
        loaded = repo.load_experiment_status("exp-001")
        assert loaded == ExperimentStatus.RUNNING

    def test_experiment_summary(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        s = _make_experiment_summary()
        repo.save_experiment_summary("exp-001", s)
        loaded = repo.load_experiment_summary("exp-001")
        assert loaded == s

    def test_run_config(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        repo.create_run_dir("exp-001", "run-0000")
        cfg = _make_run_config()
        repo.save_run_config("exp-001", "run-0000", cfg)
        loaded = repo.load_run_config("exp-001", "run-0000")
        assert loaded == cfg

    def test_run_metadata(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        repo.create_run_dir("exp-001", "run-0000")
        m = _make_run_metadata()
        repo.save_run_metadata("exp-001", "run-0000", m)
        loaded = repo.load_run_metadata("exp-001", "run-0000")
        assert loaded == m

    def test_run_status(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        repo.create_run_dir("exp-001", "run-0000")
        repo.save_run_status("exp-001", "run-0000", RunStatus.COMPLETED)
        loaded = repo.load_run_status("exp-001", "run-0000")
        assert loaded == RunStatus.COMPLETED

    def test_run_summary(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        repo.create_run_dir("exp-001", "run-0000")
        s = _make_run_summary()
        repo.save_run_summary("exp-001", "run-0000", s)
        loaded = repo.load_run_summary("exp-001", "run-0000")
        assert loaded == s

    def test_run_result(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        repo.create_run_dir("exp-001", "run-0000")
        rr = _make_run_result()
        repo.save_run_result("exp-001", "run-0000", rr)
        loaded = repo.load_run_result("exp-001", "run-0000")
        assert loaded == rr

    def test_episode_result(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        repo.create_run_dir("exp-001", "run-0000")
        ep = _make_episode_result()
        repo.save_episode_result("exp-001", "run-0000", 1, ep)
        loaded = repo.load_episode_result("exp-001", "run-0000", 1)
        assert loaded == ep

    def test_experiment_result(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        repo.create_run_dir("exp-001", "run-0000")
        er = _make_experiment_result()
        # ExperimentResult doesn't have a dedicated save, but we can
        # verify the individual components roundtrip cleanly.
        # Save the config and summary.
        repo.save_experiment_config("exp-001", er.experiment_config)
        repo.save_experiment_summary("exp-001", er.summary)
        loaded_cfg = repo.load_experiment_config("exp-001")
        loaded_summary = repo.load_experiment_summary("exp-001")
        assert loaded_cfg == er.experiment_config
        assert loaded_summary == er.summary


# ---------------------------------------------------------------------------
# Immutable write semantics tests
# ---------------------------------------------------------------------------


class TestImmutableWriteSemantics:
    def test_experiment_config_no_overwrite(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        cfg = _make_experiment_config()
        repo.save_experiment_config("exp-001", cfg)
        with pytest.raises(FileExistsError):
            repo.save_experiment_config("exp-001", cfg)

    def test_run_config_no_overwrite(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        repo.create_run_dir("exp-001", "run-0000")
        cfg = _make_run_config()
        repo.save_run_config("exp-001", "run-0000", cfg)
        with pytest.raises(FileExistsError):
            repo.save_run_config("exp-001", "run-0000", cfg)

    def test_run_result_no_overwrite(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        repo.create_run_dir("exp-001", "run-0000")
        rr = _make_run_result()
        repo.save_run_result("exp-001", "run-0000", rr)
        with pytest.raises(FileExistsError):
            repo.save_run_result("exp-001", "run-0000", rr)

    def test_episode_result_no_overwrite(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        repo.create_run_dir("exp-001", "run-0000")
        ep = _make_episode_result()
        repo.save_episode_result("exp-001", "run-0000", 1, ep)
        with pytest.raises(FileExistsError):
            repo.save_episode_result("exp-001", "run-0000", 1, ep)

    def test_run_summary_no_overwrite(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        repo.create_run_dir("exp-001", "run-0000")
        s = _make_run_summary()
        repo.save_run_summary("exp-001", "run-0000", s)
        with pytest.raises(FileExistsError):
            repo.save_run_summary("exp-001", "run-0000", s)

    def test_experiment_summary_no_overwrite(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        s = _make_experiment_summary()
        repo.save_experiment_summary("exp-001", s)
        with pytest.raises(FileExistsError):
            repo.save_experiment_summary("exp-001", s)

    def test_overwrite_true_succeeds(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        cfg = _make_experiment_config()
        repo.save_experiment_config("exp-001", cfg)
        repo.save_experiment_config("exp-001", cfg, overwrite=True)
        loaded = repo.load_experiment_config("exp-001")
        assert loaded == cfg

    def test_metadata_defaults_to_overwrite(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        m = _make_experiment_metadata()
        repo.save_experiment_metadata("exp-001", m)
        repo.save_experiment_metadata("exp-001", m)  # no error
        loaded = repo.load_experiment_metadata("exp-001")
        assert loaded == m

    def test_status_defaults_to_overwrite(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        repo.save_experiment_status("exp-001", ExperimentStatus.CREATED)
        repo.save_experiment_status("exp-001", ExperimentStatus.RUNNING)
        loaded = repo.load_experiment_status("exp-001")
        assert loaded == ExperimentStatus.RUNNING

    def test_metadata_explicit_no_overwrite(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        m = _make_experiment_metadata()
        repo.save_experiment_metadata("exp-001", m, overwrite=False)
        with pytest.raises(FileExistsError):
            repo.save_experiment_metadata("exp-001", m, overwrite=False)


# ---------------------------------------------------------------------------
# Discovery tests
# ---------------------------------------------------------------------------


class TestDiscovery:
    def test_list_experiments_empty(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        assert repo.list_experiments() == []

    def test_list_experiments_nonexistent_root(self, tmp_path):
        repo = ExperimentRepository(tmp_path / "nonexistent")
        assert repo.list_experiments() == []

    def test_list_experiments_populated(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-003")
        repo.create_experiment_dir("exp-001")
        repo.create_experiment_dir("exp-002")
        result = repo.list_experiments()
        assert result == ["exp-001", "exp-002", "exp-003"]

    def test_list_runs_empty(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        assert repo.list_runs("exp-001") == []

    def test_list_runs_populated(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        repo.create_run_dir("exp-001", "run-0002")
        repo.create_run_dir("exp-001", "run-0000")
        repo.create_run_dir("exp-001", "run-0001")
        result = repo.list_runs("exp-001")
        assert result == ["run-0000", "run-0001", "run-0002"]

    def test_list_episode_files_empty(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        repo.create_run_dir("exp-001", "run-0000")
        assert repo.list_episode_files("exp-001", "run-0000") == []

    def test_list_episode_files_sorted(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        repo.create_run_dir("exp-001", "run-0000")
        ep = _make_episode_result()
        repo.save_episode_result("exp-001", "run-0000", 3, ep)
        repo.save_episode_result("exp-001", "run-0000", 1, ep)
        repo.save_episode_result("exp-001", "run-0000", 2, ep)
        files = repo.list_episode_files("exp-001", "run-0000")
        assert len(files) == 3
        assert files[0].name == "episode_0001.json"
        assert files[1].name == "episode_0002.json"
        assert files[2].name == "episode_0003.json"

    def test_artifact_exists_true(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        repo.save_experiment_status("exp-001", ExperimentStatus.CREATED)
        p = repo.experiment_status_path("exp-001")
        assert repo.artifact_exists(p) is True

    def test_artifact_exists_false(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        p = repo.experiment_config_path("exp-nonexistent")
        assert repo.artifact_exists(p) is False


# ---------------------------------------------------------------------------
# Failure case tests
# ---------------------------------------------------------------------------


class TestFailureCases:
    def test_load_missing_file(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        with pytest.raises(FileNotFoundError):
            repo.load_experiment_config("exp-nonexistent")

    def test_load_malformed_json(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        p = repo.experiment_config_path("exp-001")
        p.write_text("not valid json{{{")
        with pytest.raises(json.JSONDecodeError):
            repo.load_experiment_config("exp-001")

    def test_load_invalid_model_fields(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        p = repo.experiment_metadata_path("exp-001")
        p.write_text(json.dumps({"wrong_field": "value"}))
        with pytest.raises(ValidationError):
            repo.load_experiment_metadata("exp-001")

    def test_load_missing_required_fields(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        p = repo.experiment_metadata_path("exp-001")
        # ExperimentMetadata requires experiment_id, created_at, experiment_type
        p.write_text(json.dumps({"experiment_id": "exp-001"}))
        with pytest.raises(ValidationError):
            repo.load_experiment_metadata("exp-001")

    def test_load_invalid_status(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-001")
        p = repo.experiment_status_path("exp-001")
        p.write_text(json.dumps({"status": "invalid_status"}))
        with pytest.raises(ValidationError):
            repo.load_experiment_status("exp-001")
