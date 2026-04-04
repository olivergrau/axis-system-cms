"""End-to-end CLI tests for the AXIS Experimentation Framework (WP16)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from axis_system_a import (
    ExperimentExecutor,
    ExperimentRepository,
    ExperimentStatus,
    RunStatus,
)
from axis_system_a.cli import main
from axis_system_a.run import RunConfig, RunExecutor
from tests.fixtures.scenario_fixtures import make_config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _single_run_config_dict() -> dict:
    """Return a dict suitable for writing as a JSON/YAML experiment config."""
    cfg = make_config(overrides={
        "world": {"grid_width": 3, "grid_height": 3},
        "execution": {"max_steps": 5},
        "logging": {"enabled": False},
    })
    return {
        "experiment_type": "single_run",
        "baseline": cfg.model_dump(mode="json"),
        "num_episodes_per_run": 2,
        "base_seed": 42,
        "name": "test-single",
    }


def _ofat_config_dict() -> dict:
    cfg = make_config(overrides={
        "world": {"grid_width": 3, "grid_height": 3},
        "execution": {"max_steps": 5},
        "logging": {"enabled": False},
    })
    return {
        "experiment_type": "ofat",
        "baseline": cfg.model_dump(mode="json"),
        "num_episodes_per_run": 2,
        "base_seed": 42,
        "name": "test-ofat",
        "parameter_path": "execution.max_steps",
        "parameter_values": [3, 5, 8],
    }


def _write_json_config(directory: Path, data: dict, name: str = "config.json") -> Path:
    path = directory / name
    path.write_text(json.dumps(data, indent=2))
    return path


def _write_yaml_config(directory: Path, data: dict, name: str = "config.yaml") -> Path:
    path = directory / name
    path.write_text(yaml.dump(data, default_flow_style=False))
    return path


def _run_cli(capsys, argv: list[str]) -> tuple[int, str, str]:
    """Run CLI main(), return (exit_code, stdout, stderr)."""
    code = main(argv)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


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


def _create_partial_ofat(tmp_path: Path) -> tuple[ExperimentRepository, str]:
    """Create an OFAT experiment that fails on run-0002, return (repo, eid)."""
    from axis_system_a.experiment import ExperimentConfig

    repo = ExperimentRepository(tmp_path / "repo")
    data = _ofat_config_dict()
    config = ExperimentConfig.model_validate(data)
    executor = ExperimentExecutor(repo, run_executor=_FailingRunExecutor(2))
    with pytest.raises(RuntimeError):
        executor.execute(config)
    return repo, config.name


# ---------------------------------------------------------------------------
# experiments list
# ---------------------------------------------------------------------------


class TestExperimentsList:
    def test_empty_repo(self, tmp_path, capsys):
        code, out, _ = _run_cli(capsys, [
            "--root", str(tmp_path / "repo"), "experiments", "list",
        ])
        assert code == 0
        assert "No experiments" in out

    def test_after_execution(self, tmp_path, capsys):
        config_path = _write_json_config(tmp_path, _single_run_config_dict())
        root = str(tmp_path / "repo")
        _run_cli(capsys, ["--root", root, "experiments", "run", str(config_path)])
        capsys.readouterr()  # clear
        code, out, _ = _run_cli(capsys, ["--root", root, "experiments", "list"])
        assert code == 0
        assert "test-single" in out
        assert "completed" in out

    def test_json_output(self, tmp_path, capsys):
        config_path = _write_json_config(tmp_path, _single_run_config_dict())
        root = str(tmp_path / "repo")
        _run_cli(capsys, ["--root", root, "experiments", "run", str(config_path)])
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "--output", "json", "experiments", "list",
        ])
        assert code == 0
        data = json.loads(out)
        assert len(data) == 1
        assert data[0]["experiment_id"] == "test-single"
        assert data[0]["status"] == "completed"


# ---------------------------------------------------------------------------
# experiments run
# ---------------------------------------------------------------------------


class TestExperimentsRun:
    def test_single_run(self, tmp_path, capsys):
        config_path = _write_json_config(tmp_path, _single_run_config_dict())
        root = str(tmp_path / "repo")
        code, out, _ = _run_cli(capsys, [
            "--root", root, "experiments", "run", str(config_path),
        ])
        assert code == 0
        assert "completed" in out
        # Artifacts exist
        repo = ExperimentRepository(Path(root))
        assert repo.load_experiment_status("test-single") == ExperimentStatus.COMPLETED

    def test_ofat(self, tmp_path, capsys):
        config_path = _write_json_config(tmp_path, _ofat_config_dict())
        root = str(tmp_path / "repo")
        code, out, _ = _run_cli(capsys, [
            "--root", root, "experiments", "run", str(config_path),
        ])
        assert code == 0
        repo = ExperimentRepository(Path(root))
        assert len(repo.list_runs("test-ofat")) == 3

    def test_already_exists(self, tmp_path, capsys):
        config_path = _write_json_config(tmp_path, _single_run_config_dict())
        root = str(tmp_path / "repo")
        _run_cli(capsys, ["--root", root, "experiments", "run", str(config_path)])
        capsys.readouterr()
        code, _, err = _run_cli(capsys, [
            "--root", root, "experiments", "run", str(config_path),
        ])
        assert code == 1
        assert "already exists" in err.lower() or "already exists" in err

    def test_missing_config_file(self, tmp_path, capsys):
        root = str(tmp_path / "repo")
        code, _, err = _run_cli(capsys, [
            "--root", root, "experiments", "run", str(tmp_path / "nope.json"),
        ])
        assert code == 1
        assert "not found" in err.lower()


# ---------------------------------------------------------------------------
# experiments resume
# ---------------------------------------------------------------------------


class TestExperimentsResume:
    def test_resume_partial(self, tmp_path, capsys):
        repo, eid = _create_partial_ofat(tmp_path)
        code, out, _ = _run_cli(capsys, [
            "--root", str(repo.root), "experiments", "resume", eid,
        ])
        assert code == 0
        assert "completed" in out
        assert repo.load_experiment_status(eid) == ExperimentStatus.COMPLETED

    def test_resume_completed(self, tmp_path, capsys):
        config_path = _write_json_config(tmp_path, _single_run_config_dict())
        root = str(tmp_path / "repo")
        _run_cli(capsys, ["--root", root, "experiments", "run", str(config_path)])
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "experiments", "resume", "test-single",
        ])
        assert code == 0

    def test_resume_nonexistent(self, tmp_path, capsys):
        root = str(tmp_path / "repo")
        code, _, err = _run_cli(capsys, [
            "--root", root, "experiments", "resume", "nope",
        ])
        assert code == 1
        assert "not found" in err.lower()


# ---------------------------------------------------------------------------
# experiments show
# ---------------------------------------------------------------------------


class TestExperimentsShow:
    def test_show_completed(self, tmp_path, capsys):
        config_path = _write_json_config(tmp_path, _single_run_config_dict())
        root = str(tmp_path / "repo")
        _run_cli(capsys, ["--root", root, "experiments", "run", str(config_path)])
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "experiments", "show", "test-single",
        ])
        assert code == 0
        assert "test-single" in out
        assert "completed" in out.lower()

    def test_show_json(self, tmp_path, capsys):
        config_path = _write_json_config(tmp_path, _single_run_config_dict())
        root = str(tmp_path / "repo")
        _run_cli(capsys, ["--root", root, "experiments", "run", str(config_path)])
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "--output", "json", "experiments", "show", "test-single",
        ])
        assert code == 0
        data = json.loads(out)
        assert data["experiment_id"] == "test-single"
        assert data["status"] == "completed"
        assert "summary" in data
        assert "runs" in data

    def test_show_nonexistent(self, tmp_path, capsys):
        root = str(tmp_path / "repo")
        code, _, err = _run_cli(capsys, [
            "--root", root, "experiments", "show", "nope",
        ])
        assert code == 1
        assert "not found" in err.lower()


# ---------------------------------------------------------------------------
# runs list
# ---------------------------------------------------------------------------


class TestRunsList:
    def test_list_ofat_runs(self, tmp_path, capsys):
        config_path = _write_json_config(tmp_path, _ofat_config_dict())
        root = str(tmp_path / "repo")
        _run_cli(capsys, ["--root", root, "experiments", "run", str(config_path)])
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "runs", "list", "--experiment", "test-ofat",
        ])
        assert code == 0
        assert "run-0000" in out
        assert "run-0001" in out
        assert "run-0002" in out

    def test_list_json(self, tmp_path, capsys):
        config_path = _write_json_config(tmp_path, _ofat_config_dict())
        root = str(tmp_path / "repo")
        _run_cli(capsys, ["--root", root, "experiments", "run", str(config_path)])
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "--output", "json", "runs", "list",
            "--experiment", "test-ofat",
        ])
        assert code == 0
        data = json.loads(out)
        assert len(data) == 3
        assert data[0]["run_id"] == "run-0000"

    def test_list_nonexistent_experiment(self, tmp_path, capsys):
        root = str(tmp_path / "repo")
        code, _, err = _run_cli(capsys, [
            "--root", root, "runs", "list", "--experiment", "nope",
        ])
        assert code == 1
        assert "not found" in err.lower()


# ---------------------------------------------------------------------------
# runs show
# ---------------------------------------------------------------------------


class TestRunsShow:
    def test_show_run(self, tmp_path, capsys):
        config_path = _write_json_config(tmp_path, _single_run_config_dict())
        root = str(tmp_path / "repo")
        _run_cli(capsys, ["--root", root, "experiments", "run", str(config_path)])
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "runs", "show", "run-0000",
            "--experiment", "test-single",
        ])
        assert code == 0
        assert "run-0000" in out
        assert "completed" in out.lower()

    def test_show_run_json(self, tmp_path, capsys):
        config_path = _write_json_config(tmp_path, _single_run_config_dict())
        root = str(tmp_path / "repo")
        _run_cli(capsys, ["--root", root, "experiments", "run", str(config_path)])
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "--output", "json", "runs", "show", "run-0000",
            "--experiment", "test-single",
        ])
        assert code == 0
        data = json.loads(out)
        assert data["run_id"] == "run-0000"
        assert data["status"] == "completed"
        assert "summary" in data
        assert data["num_episodes"] == 2

    def test_show_nonexistent_run(self, tmp_path, capsys):
        config_path = _write_json_config(tmp_path, _single_run_config_dict())
        root = str(tmp_path / "repo")
        _run_cli(capsys, ["--root", root, "experiments", "run", str(config_path)])
        capsys.readouterr()
        code, _, err = _run_cli(capsys, [
            "--root", root, "runs", "show", "run-9999",
            "--experiment", "test-single",
        ])
        assert code == 1
        assert "not found" in err.lower()


# ---------------------------------------------------------------------------
# End-to-end single-run workflow
# ---------------------------------------------------------------------------


class TestEndToEndSingleRun:
    def test_full_workflow(self, tmp_path, capsys):
        root = str(tmp_path / "repo")
        config_path = _write_json_config(tmp_path, _single_run_config_dict())

        # 1. Run experiment
        code, out, _ = _run_cli(capsys, [
            "--root", root, "experiments", "run", str(config_path),
        ])
        assert code == 0

        # 2. Show experiment
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "--output", "json", "experiments", "show", "test-single",
        ])
        assert code == 0
        data = json.loads(out)
        assert data["status"] == "completed"
        assert len(data["runs"]) == 1

        # 3. List runs
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "--output", "json", "runs", "list",
            "--experiment", "test-single",
        ])
        assert code == 0
        runs = json.loads(out)
        assert len(runs) == 1
        assert runs[0]["run_id"] == "run-0000"

        # 4. Show run
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "--output", "json", "runs", "show", "run-0000",
            "--experiment", "test-single",
        ])
        assert code == 0
        run_data = json.loads(out)
        assert run_data["status"] == "completed"
        assert run_data["num_episodes"] == 2


# ---------------------------------------------------------------------------
# End-to-end OFAT workflow
# ---------------------------------------------------------------------------


class TestEndToEndOfat:
    def test_full_workflow(self, tmp_path, capsys):
        root = str(tmp_path / "repo")
        config_path = _write_json_config(tmp_path, _ofat_config_dict())

        # 1. Run OFAT experiment
        code, _, _ = _run_cli(capsys, [
            "--root", root, "experiments", "run", str(config_path),
        ])
        assert code == 0

        # 2. Show experiment (JSON)
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "--output", "json", "experiments", "show", "test-ofat",
        ])
        data = json.loads(out)
        assert data["summary"]["num_runs"] == 3
        assert len(data["summary"]["run_entries"]) == 3

        # 3. List runs
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "--output", "json", "runs", "list",
            "--experiment", "test-ofat",
        ])
        runs = json.loads(out)
        assert len(runs) == 3
        assert runs[0]["variation_description"] == "execution.max_steps=3"


# ---------------------------------------------------------------------------
# End-to-end resume workflow
# ---------------------------------------------------------------------------


class TestEndToEndResume:
    def test_resume_via_cli(self, tmp_path, capsys):
        repo, eid = _create_partial_ofat(tmp_path)
        assert repo.load_experiment_status(eid) == ExperimentStatus.PARTIAL

        code, out, _ = _run_cli(capsys, [
            "--root", str(repo.root), "experiments", "resume", eid,
        ])
        assert code == 0
        assert "completed" in out
        assert repo.load_experiment_status(eid) == ExperimentStatus.COMPLETED
        assert len(repo.list_runs(eid)) == 3


# ---------------------------------------------------------------------------
# Malformed config tests
# ---------------------------------------------------------------------------


class TestMalformedConfig:
    def test_invalid_json_syntax(self, tmp_path, capsys):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{not valid json!!}")
        code, _, err = _run_cli(capsys, [
            "--root", str(tmp_path / "repo"), "experiments", "run", str(bad_file),
        ])
        assert code == 1
        assert "invalid" in err.lower() or "error" in err.lower()

    def test_missing_required_field(self, tmp_path, capsys):
        bad_config = {"experiment_type": "single_run"}  # missing baseline etc.
        bad_file = _write_json_config(tmp_path, bad_config, "bad.json")
        code, _, err = _run_cli(capsys, [
            "--root", str(tmp_path / "repo"), "experiments", "run", str(bad_file),
        ])
        assert code == 1
        assert "error" in err.lower()


# ---------------------------------------------------------------------------
# YAML config test
# ---------------------------------------------------------------------------


class TestYamlConfig:
    def test_yaml_config(self, tmp_path, capsys):
        config_path = _write_yaml_config(tmp_path, _single_run_config_dict())
        root = str(tmp_path / "repo")
        code, out, _ = _run_cli(capsys, [
            "--root", root, "experiments", "run", str(config_path),
        ])
        assert code == 0
        assert "completed" in out
        repo = ExperimentRepository(Path(root))
        assert repo.load_experiment_status("test-single") == ExperimentStatus.COMPLETED
