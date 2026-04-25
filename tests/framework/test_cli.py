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
from tests.builders.system_config_builder import SystemAConfigBuilder


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
        code, out, _ = _run_cli(
            capsys, ["--root", root, "experiments", "list"])
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
        assert repo.load_experiment_status(
            eids[0]) == ExperimentStatus.COMPLETED

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
            "--root", str(tmp_path /
                          "repo"), "experiments", "run", str(bad_file),
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
        assert "Behavioral Metrics" in out

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
        assert "behavior_metrics" in data
        assert data["behavior_metrics"] is not None
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


class TestRunsMetrics:
    def test_metrics_run_text(self, tmp_path, capsys):
        root, eid = _run_experiment(tmp_path)
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "runs", "metrics", "run-0000",
            "--experiment", eid,
        ])
        assert code == 0
        assert "Behavioral Metrics For run-0000" in out
        assert "Behavioral Metrics" in out

    def test_metrics_run_json(self, tmp_path, capsys):
        root, eid = _run_experiment(tmp_path)
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root, "--output", "json", "runs", "metrics", "run-0000",
            "--experiment", eid,
        ])
        assert code == 0
        data = json.loads(out)
        assert data["run_id"] == "run-0000"
        assert data["experiment_id"] == eid
        assert "standard_metrics" in data

    def test_metrics_run_text_shows_six_decimals(self, tmp_path, capsys):
        from axis.framework.cli.commands.runs import _render_behavior_metrics_text

        payload = {
            "standard_metrics": {
                "resource_gain_per_step": {"mean": 0.588},
                "net_energy_efficiency": {"mean": 0.635},
                "successful_consume_rate": {"mean": 0.8},
                "failed_movement_rate": {"mean": 0.0},
                "action_entropy": {"mean": 1.518},
                "policy_sharpness": {"mean": 0.325},
                "unique_cells_visited": {"mean": 49.62},
                "coverage_efficiency": {"mean": 0.321},
                "revisit_rate": {"mean": 0.666},
            },
            "system_specific_metrics": {
                "system_c_prediction": {
                    "mean_prediction_error": 0.036,
                    "prediction_modulation_strength": 0.0004,
                    "prediction_step_count": 8236,
                }
            },
        }

        _render_behavior_metrics_text(payload)
        out = capsys.readouterr().out
        assert "resource_gain_per_step=0.588000" in out
        assert "unique_cells_visited=49.620000" in out
        assert "prediction_modulation_strength=0.000400" in out


# ---------------------------------------------------------------------------
# compare
# ---------------------------------------------------------------------------


class TestCompare:
    def test_mismatched_episode_flags(self, tmp_path, capsys):
        root, eid = _run_experiment(tmp_path)
        capsys.readouterr()
        code, _, err = _run_cli(capsys, [
            "--root", root,
            "compare",
            "--reference-experiment", eid,
            "--reference-run", "run-0000",
            "--reference-episode", "0",
            "--candidate-experiment", eid,
            "--candidate-run", "run-0000",
        ])
        assert code == 1
        assert "both be provided" in err.lower()

    def test_compare_runs_text(self, tmp_path, capsys):
        root, eid = _run_experiment(tmp_path)
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root,
            "compare",
            "--reference-experiment", eid,
            "--reference-run", "run-0000",
            "--candidate-experiment", eid,
            "--candidate-run", "run-0000",
        ])
        assert code == 0
        assert "Run Comparison" in out
        assert "Per-episode Results" in out
        assert "Statistical Summary" in out

    def test_compare_episode_text(self, tmp_path, capsys):
        root, eid = _run_experiment(tmp_path)
        capsys.readouterr()
        code, out, _ = _run_cli(capsys, [
            "--root", root,
            "compare",
            "--reference-experiment", eid,
            "--reference-run", "run-0000",
            "--reference-episode", "1",
            "--candidate-experiment", eid,
            "--candidate-run", "run-0000",
            "--candidate-episode", "1",
        ])
        assert code == 0
        assert "Comparison" in out
        assert "Alignment" in out or "Metrics" in out


# ---------------------------------------------------------------------------
# visualize stub
# ---------------------------------------------------------------------------


class TestVisualize:
    def test_visualize_stub(self, tmp_path, capsys):
        code, out, _ = _run_cli(capsys, [
            "--root", str(tmp_path / "repo"),
            "visualize", "--experiment", "exp", "--run", "run", "--episode", "1",
        ])
        # With Phase V-4 implemented, the visualize command now attempts
        # to launch a real session. With an invalid experiment path, it
        # should return error code 1.
        assert code == 1


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
