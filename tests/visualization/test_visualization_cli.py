"""CLI visualization end-to-end tests.

Tests the ``axis visualize`` subcommand: argument parsing, episode
resolution, start-coordinate passthrough, error handling, and full
run-then-visualize workflows.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from axis.framework.cli import main
from axis.framework.persistence import (
    ExperimentMetadata,
    ExperimentRepository,
    ExperimentStatus,
    RunMetadata,
    RunStatus,
)
from tests.builders.system_config_builder import SystemAConfigBuilder
from tests.visualization.e2e_helpers import run_and_persist_experiment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_cli(capsys, argv: list[str]) -> tuple[int, str, str]:
    """Run CLI main(), return (exit_code, stdout, stderr)."""
    try:
        code = main(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _persist_experiment(
    tmp_path: Path,
    system_type: str = "system_a",
    max_steps: int = 10,
) -> tuple[str, str, str]:
    """Create a persisted experiment, return (root, experiment_id, run_id)."""
    repo, eid = run_and_persist_experiment(
        tmp_path, system_type, max_steps=max_steps, seed=42,
    )
    return str(repo.root), eid, "run-0000"


# ---------------------------------------------------------------------------
# Module-scoped fixture for tests that only read the repo
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def populated_repo(tmp_path_factory):
    """Create a single persisted System A experiment for all resolution tests."""
    tmp_path = tmp_path_factory.mktemp("cli_viz")
    root, eid, rid = _persist_experiment(tmp_path)
    return root, eid, rid


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


class TestArgParsing:
    def test_missing_experiment_fails(self, capsys) -> None:
        code, _, _ = _run_cli(capsys, [
            "visualize", "--run", "run-0000", "--episode", "1",
        ])
        assert code != 0

    def test_missing_run_fails(self, capsys) -> None:
        code, _, _ = _run_cli(capsys, [
            "visualize", "--experiment", "exp", "--episode", "1",
        ])
        assert code != 0

    def test_missing_episode_fails(self, capsys) -> None:
        code, _, _ = _run_cli(capsys, [
            "visualize", "--experiment", "exp", "--run", "run-0000",
        ])
        assert code != 0

    def test_episode_requires_integer(self, capsys) -> None:
        code, _, _ = _run_cli(capsys, [
            "visualize", "--experiment", "E", "--run", "R",
            "--episode", "abc",
        ])
        assert code != 0


# ---------------------------------------------------------------------------
# Episode resolution (mock launch to avoid Qt event loop)
# ---------------------------------------------------------------------------


class TestEpisodeResolution:
    def test_nonexistent_experiment(self, populated_repo, capsys) -> None:
        root, _, rid = populated_repo
        code, _, err = _run_cli(capsys, [
            "--root", root,
            "visualize", "--experiment", "nope",
            "--run", rid, "--episode", "0",
        ])
        assert code == 1
        assert "not found" in err.lower() or "error" in err.lower()

    def test_nonexistent_run(self, populated_repo, capsys) -> None:
        root, eid, _ = populated_repo
        code, _, err = _run_cli(capsys, [
            "--root", root,
            "visualize", "--experiment", eid,
            "--run", "nope", "--episode", "0",
        ])
        assert code == 1
        assert "not found" in err.lower() or "error" in err.lower()

    def test_nonexistent_episode(self, populated_repo, capsys) -> None:
        root, eid, rid = populated_repo
        code, _, err = _run_cli(capsys, [
            "--root", root,
            "visualize", "--experiment", eid,
            "--run", rid, "--episode", "99",
        ])
        assert code == 1
        assert "error" in err.lower()

    @patch(
        "axis.visualization.launch.launch_visualization",
        return_value=0,
    )
    def test_valid_episode_resolves(
        self, mock_launch, populated_repo, capsys,
    ) -> None:
        root, eid, rid = populated_repo
        code, _, _ = _run_cli(capsys, [
            "--root", root,
            "visualize", "--experiment", eid,
            "--run", rid, "--episode", "0",
        ])
        assert code == 0
        mock_launch.assert_called_once()

    @patch(
        "axis.visualization.launch.launch_visualization",
        return_value=0,
    )
    def test_defaults_passed_through(
        self, mock_launch, populated_repo, capsys,
    ) -> None:
        root, eid, rid = populated_repo
        _run_cli(capsys, [
            "--root", root,
            "visualize", "--experiment", eid,
            "--run", rid, "--episode", "0",
        ])
        call_kwargs = mock_launch.call_args
        # start_step and start_phase should be None when not specified
        assert call_kwargs.kwargs.get("start_step") is None
        assert call_kwargs.kwargs.get("start_phase") is None


# ---------------------------------------------------------------------------
# Start coordinate passthrough
# ---------------------------------------------------------------------------


class TestStartCoordinatePassthrough:
    @patch(
        "axis.visualization.launch.launch_visualization",
        return_value=0,
    )
    def test_custom_step(
        self, mock_launch, populated_repo, capsys,
    ) -> None:
        root, eid, rid = populated_repo
        _run_cli(capsys, [
            "--root", root,
            "visualize", "--experiment", eid,
            "--run", rid, "--episode", "0", "--step", "2",
        ])
        assert mock_launch.call_args.kwargs["start_step"] == 2

    @patch(
        "axis.visualization.launch.launch_visualization",
        return_value=0,
    )
    def test_custom_phase(
        self, mock_launch, populated_repo, capsys,
    ) -> None:
        root, eid, rid = populated_repo
        _run_cli(capsys, [
            "--root", root,
            "visualize", "--experiment", eid,
            "--run", rid, "--episode", "0", "--phase", "1",
        ])
        assert mock_launch.call_args.kwargs["start_phase"] == 1

    @patch(
        "axis.visualization.launch.launch_visualization",
        return_value=0,
    )
    def test_both_step_and_phase(
        self, mock_launch, populated_repo, capsys,
    ) -> None:
        root, eid, rid = populated_repo
        _run_cli(capsys, [
            "--root", root,
            "visualize", "--experiment", eid,
            "--run", rid, "--episode", "0",
            "--step", "3", "--phase", "2",
        ])
        kwargs = mock_launch.call_args.kwargs
        assert kwargs["start_step"] == 3
        assert kwargs["start_phase"] == 2

    @patch(
        "axis.visualization.launch.launch_visualization",
        return_value=0,
    )
    def test_width_percent_passed_through(
        self, mock_launch, populated_repo, capsys,
    ) -> None:
        root, eid, rid = populated_repo
        _run_cli(capsys, [
            "--root", root,
            "visualize", "--experiment", eid,
            "--run", rid, "--episode", "0",
            "--width-percent", "80",
        ])
        assert mock_launch.call_args.kwargs["width_percent"] == 80.0


# ---------------------------------------------------------------------------
# Start coordinate errors (no mock — let real errors propagate)
# ---------------------------------------------------------------------------


class TestStartCoordinateErrors:
    def test_step_out_of_bounds(self, populated_repo, capsys) -> None:
        root, eid, rid = populated_repo
        code, _, err = _run_cli(capsys, [
            "--root", root,
            "visualize", "--experiment", eid,
            "--run", rid, "--episode", "0", "--step", "999",
        ])
        assert code == 1
        assert "out of bounds" in err.lower() or "error" in err.lower()

    def test_negative_step(self, populated_repo, capsys) -> None:
        root, eid, rid = populated_repo
        code, _, err = _run_cli(capsys, [
            "--root", root,
            "visualize", "--experiment", eid,
            "--run", rid, "--episode", "0", "--step", "-1",
        ])
        assert code == 1
        assert "out of bounds" in err.lower() or "error" in err.lower()

    def test_invalid_width_percent(self, populated_repo, capsys) -> None:
        root, eid, rid = populated_repo
        code, _, err = _run_cli(capsys, [
            "--root", root,
            "visualize", "--experiment", eid,
            "--run", rid, "--episode", "0", "--width-percent", "0",
        ])
        assert code == 1
        assert "width-percent" in err.lower()

    def test_light_trace_mode_is_rejected(self, tmp_path, capsys) -> None:
        repo = ExperimentRepository(tmp_path / "repo")
        repo.create_experiment_dir("exp-light")
        repo.save_experiment_metadata(
            "exp-light",
            ExperimentMetadata(
                experiment_id="exp-light",
                created_at="2026-04-24T00:00:00Z",
                experiment_type="single_run",
                system_type="system_a",
                output_form="point",
                trace_mode="light",
                primary_run_id="run-0000",
            ),
        )
        repo.save_experiment_status("exp-light", ExperimentStatus.COMPLETED)
        repo.create_run_dir("exp-light", "run-0000")
        repo.save_run_metadata(
            "exp-light",
            "run-0000",
            RunMetadata(
                run_id="run-0000",
                experiment_id="exp-light",
                created_at="2026-04-24T00:00:00Z",
                trace_mode="light",
            ),
        )
        repo.save_run_status("exp-light", "run-0000", RunStatus.COMPLETED)

        code, _, err = _run_cli(capsys, [
            "--root", str(repo.root),
            "visualize", "--experiment", "exp-light",
            "--run", "run-0000", "--episode", "0",
        ])
        assert code == 1
        assert "light trace mode" in err.lower()


# ---------------------------------------------------------------------------
# Full E2E workflows: run experiment via CLI, then visualize
# ---------------------------------------------------------------------------


def _write_json_config(directory: Path, data: dict) -> Path:
    path = directory / "config.json"
    path.write_text(json.dumps(data, indent=2))
    return path


def _system_a_experiment_config() -> dict:
    return {
        "system_type": "system_a",
        "experiment_type": "single_run",
        "general": {"seed": 42},
        "execution": {"max_steps": 10},
        "world": {"grid_width": 5, "grid_height": 5},
        "logging": {"enabled": False},
        "system": SystemAConfigBuilder().build(),
        "num_episodes_per_run": 1,
    }


def _system_b_experiment_config() -> dict:
    return {
        "system_type": "system_b",
        "experiment_type": "single_run",
        "general": {"seed": 42},
        "execution": {"max_steps": 10},
        "world": {"grid_width": 5, "grid_height": 5},
        "logging": {"enabled": False},
        "system": {
            "agent": {"initial_energy": 100.0, "max_energy": 100.0},
            "policy": {
                "selection_mode": "sample",
                "temperature": 1.0,
                "scan_bonus": 2.0,
            },
            "transition": {
                "move_cost": 1.0,
                "scan_cost": 0.5,
                "stay_cost": 0.5,
            },
        },
        "num_episodes_per_run": 1,
    }


class TestVisualizationE2EWorkflow:
    @patch(
        "axis.visualization.launch.launch_visualization",
        return_value=0,
    )
    def test_run_then_visualize(self, mock_launch, tmp_path, capsys) -> None:
        root = str(tmp_path / "repo")
        config_path = _write_json_config(
            tmp_path, _system_a_experiment_config())

        # 1. Run experiment via CLI
        code, _, _ = _run_cli(capsys, [
            "--root", root, "experiments", "run", str(config_path),
        ])
        assert code == 0

        # 2. Get experiment ID
        from axis.framework.persistence import ExperimentRepository
        repo = ExperimentRepository(Path(root))
        eid = repo.list_experiments()[0]

        # 3. Visualize via CLI
        capsys.readouterr()
        code, _, _ = _run_cli(capsys, [
            "--root", root,
            "visualize", "--experiment", eid,
            "--run", "run-0000", "--episode", "0",
        ])
        assert code == 0
        mock_launch.assert_called_once()

    @patch(
        "axis.visualization.launch.launch_visualization",
        return_value=0,
    )
    def test_visualize_system_b(self, mock_launch, tmp_path, capsys) -> None:
        root = str(tmp_path / "repo")
        config_path = _write_json_config(
            tmp_path, _system_b_experiment_config())

        code, _, _ = _run_cli(capsys, [
            "--root", root, "experiments", "run", str(config_path),
        ])
        assert code == 0

        from axis.framework.persistence import ExperimentRepository
        repo = ExperimentRepository(Path(root))
        eid = repo.list_experiments()[0]

        capsys.readouterr()
        code, _, _ = _run_cli(capsys, [
            "--root", root,
            "visualize", "--experiment", eid,
            "--run", "run-0000", "--episode", "0",
        ])
        assert code == 0
        mock_launch.assert_called_once()

    @patch(
        "axis.visualization.launch.launch_visualization",
        return_value=0,
    )
    def test_visualize_with_step_seeks(
        self, mock_launch, tmp_path, capsys,
    ) -> None:
        root = str(tmp_path / "repo")
        config_path = _write_json_config(
            tmp_path, _system_a_experiment_config())

        code, _, _ = _run_cli(capsys, [
            "--root", root, "experiments", "run", str(config_path),
        ])
        assert code == 0

        from axis.framework.persistence import ExperimentRepository
        repo = ExperimentRepository(Path(root))
        eid = repo.list_experiments()[0]

        capsys.readouterr()
        code, _, _ = _run_cli(capsys, [
            "--root", root,
            "visualize", "--experiment", eid,
            "--run", "run-0000", "--episode", "0",
            "--step", "3",
        ])
        assert code == 0
        assert mock_launch.call_args.kwargs["start_step"] == 3
