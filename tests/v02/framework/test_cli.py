"""Tests for the framework CLI (WP-3.5)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from axis.framework.cli import main
from axis.framework.persistence import (
    ExperimentRepository,
    ExperimentStatus,
)
from tests.v02.builders.system_config_builder import SystemAConfigBuilder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _single_run_config_dict() -> dict:
    """Return a dict suitable for writing as a JSON/YAML experiment config."""
    return {
        "system_type": "system_a",
        "experiment_type": "single_run",
        "general": {"seed": 42},
        "execution": {"max_steps": 10},
        "world": {"grid_width": 5, "grid_height": 5},
        "logging": {"enabled": False},
        "system": SystemAConfigBuilder().build(),
        "num_episodes_per_run": 2,
    }


def _ofat_config_dict() -> dict:
    return {
        "system_type": "system_a",
        "experiment_type": "ofat",
        "general": {"seed": 42},
        "execution": {"max_steps": 10},
        "world": {"grid_width": 5, "grid_height": 5},
        "logging": {"enabled": False},
        "system": SystemAConfigBuilder().build(),
        "num_episodes_per_run": 2,
        "parameter_path": "framework.execution.max_steps",
        "parameter_values": [5, 8, 10],
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


def _run_experiment(tmp_path: Path) -> tuple[str, str]:
    """Run a single-run experiment and return (root, experiment_id)."""
    config_path = _write_json_config(tmp_path, _single_run_config_dict())
    root = str(tmp_path / "repo")
    main(["--root", root, "experiments", "run", str(config_path)])
    repo = ExperimentRepository(Path(root))
    eid = repo.list_experiments()[0]
    return root, eid


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
        root, eid = _run_experiment(tmp_path)
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, ["--root", root, "experiments", "list"])
        assert code == 0
        assert eid in out
        assert "completed" in out


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
        assert "completed" in out.lower()
        repo = ExperimentRepository(Path(root))
        eids = repo.list_experiments()
        assert len(eids) == 1
        assert repo.load_experiment_status(eids[0]) == ExperimentStatus.COMPLETED

    def test_ofat(self, tmp_path, capsys):
        config_path = _write_json_config(tmp_path, _ofat_config_dict())
        root = str(tmp_path / "repo")
        code, out, _ = _run_cli(capsys, [
            "--root", root, "experiments", "run", str(config_path),
        ])
        assert code == 0
        repo = ExperimentRepository(Path(root))
        eid = repo.list_experiments()[0]
        assert len(repo.list_runs(eid)) == 3

    def test_missing_config_file(self, tmp_path, capsys):
        root = str(tmp_path / "repo")
        code, _, err = _run_cli(capsys, [
            "--root", root, "experiments", "run", str(tmp_path / "nope.json"),
        ])
        assert code == 1
        assert "not found" in err.lower()

    def test_invalid_config(self, tmp_path, capsys):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{not valid json!!}")
        code, _, err = _run_cli(capsys, [
            "--root", str(tmp_path / "repo"), "experiments", "run", str(bad_file),
        ])
        assert code == 1
        assert "error" in err.lower()


# ---------------------------------------------------------------------------
# experiments resume
# ---------------------------------------------------------------------------


class TestExperimentsResume:
    def test_resume_completed(self, tmp_path, capsys):
        root, eid = _run_experiment(tmp_path)
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "experiments", "resume", eid,
        ])
        assert code == 0
        assert "completed" in out.lower()

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
        root, eid = _run_experiment(tmp_path)
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "experiments", "show", eid,
        ])
        assert code == 0
        assert eid in out
        assert "completed" in out.lower()

    def test_show_json(self, tmp_path, capsys):
        root, eid = _run_experiment(tmp_path)
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "--output", "json", "experiments", "show", eid,
        ])
        assert code == 0
        data = json.loads(out)
        assert data["experiment_id"] == eid
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
    def test_list_runs(self, tmp_path, capsys):
        root, eid = _run_experiment(tmp_path)
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "runs", "list", "--experiment", eid,
        ])
        assert code == 0
        assert "run-0000" in out

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
        root, eid = _run_experiment(tmp_path)
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "runs", "show", "run-0000",
            "--experiment", eid,
        ])
        assert code == 0
        assert "run-0000" in out
        assert "completed" in out.lower()

    def test_show_run_json(self, tmp_path, capsys):
        root, eid = _run_experiment(tmp_path)
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "--output", "json", "runs", "show", "run-0000",
            "--experiment", eid,
        ])
        assert code == 0
        data = json.loads(out)
        assert data["run_id"] == "run-0000"
        assert data["status"] == "completed"
        assert "summary" in data
        assert data["num_episodes"] == 2

    def test_show_nonexistent_run(self, tmp_path, capsys):
        root, eid = _run_experiment(tmp_path)
        capsys.readouterr()
        code, _, err = _run_cli(capsys, [
            "--root", root, "runs", "show", "run-9999",
            "--experiment", eid,
        ])
        assert code == 1
        assert "not found" in err.lower()


# ---------------------------------------------------------------------------
# visualize stub
# ---------------------------------------------------------------------------


class TestVisualize:
    def test_visualize_stub(self, tmp_path, capsys):
        code, out, _ = _run_cli(capsys, [
            "--root", str(tmp_path / "repo"),
            "visualize", "--experiment", "exp", "--run", "run", "--episode", "1",
        ])
        assert code == 0
        assert "not yet available" in out.lower() or "phase 4" in out.lower()


# ---------------------------------------------------------------------------
# YAML config
# ---------------------------------------------------------------------------


class TestYamlConfig:
    def test_yaml_config(self, tmp_path, capsys):
        config_path = _write_yaml_config(tmp_path, _single_run_config_dict())
        root = str(tmp_path / "repo")
        code, out, _ = _run_cli(capsys, [
            "--root", root, "experiments", "run", str(config_path),
        ])
        assert code == 0
        assert "completed" in out.lower()


# ---------------------------------------------------------------------------
# Unknown system type
# ---------------------------------------------------------------------------


class TestUnknownSystem:
    def test_unknown_system_type(self, tmp_path, capsys):
        data = _single_run_config_dict()
        data["system_type"] = "nonexistent_system"
        config_path = _write_json_config(tmp_path, data)
        root = str(tmp_path / "repo")
        code, _, err = _run_cli(capsys, [
            "--root", root, "experiments", "run", str(config_path),
        ])
        assert code == 1
        assert "error" in err.lower()


# ---------------------------------------------------------------------------
# End-to-end workflow
# ---------------------------------------------------------------------------


class TestEndToEnd:
    def test_full_workflow(self, tmp_path, capsys):
        root = str(tmp_path / "repo")
        config_path = _write_json_config(tmp_path, _single_run_config_dict())

        # 1. Run experiment
        code, out, _ = _run_cli(capsys, [
            "--root", root, "experiments", "run", str(config_path),
        ])
        assert code == 0

        # Get the experiment ID
        repo = ExperimentRepository(Path(root))
        eid = repo.list_experiments()[0]

        # 2. Show experiment
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "--output", "json", "experiments", "show", eid,
        ])
        assert code == 0
        data = json.loads(out)
        assert data["status"] == "completed"
        assert len(data["runs"]) == 1

        # 3. List runs
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "--output", "json", "runs", "list",
            "--experiment", eid,
        ])
        assert code == 0
        runs = json.loads(out)
        assert len(runs) == 1
        assert runs[0]["run_id"] == "run-0000"

        # 4. Show run
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "--output", "json", "runs", "show", "run-0000",
            "--experiment", eid,
        ])
        assert code == 0
        run_data = json.loads(out)
        assert run_data["status"] == "completed"
        assert run_data["num_episodes"] == 2
