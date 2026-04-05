"""Tests for visualization CLI integration (VWP8)."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from axis_system_a.cli import build_parser, main
from axis_system_a.repository import ExperimentRepository


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


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


class TestArgParsing:
    def test_missing_experiment_fails(self, capsys):
        code, _, err = _run_cli(capsys, [
            "visualize", "--run", "run-0000", "--episode", "1",
        ])
        assert code != 0

    def test_missing_run_fails(self, capsys):
        code, _, err = _run_cli(capsys, [
            "visualize", "--experiment", "test-exp", "--episode", "1",
        ])
        assert code != 0

    def test_missing_episode_fails(self, capsys):
        code, _, err = _run_cli(capsys, [
            "visualize", "--experiment", "test-exp", "--run", "run-0000",
        ])
        assert code != 0

    def test_episode_requires_integer(self, capsys):
        code, _, err = _run_cli(capsys, [
            "visualize", "--experiment", "E", "--run", "R", "--episode", "abc",
        ])
        assert code != 0

    def test_invalid_phase_rejected(self, capsys):
        code, _, err = _run_cli(capsys, [
            "visualize", "--experiment", "E", "--run", "R",
            "--episode", "1", "--start-phase", "INVALID",
        ])
        assert code != 0

    def test_valid_phase_names_accepted(self):
        parser = build_parser()
        for phase in ["BEFORE", "AFTER_REGEN", "AFTER_ACTION"]:
            args = parser.parse_args([
                "visualize", "--experiment", "E", "--run", "R",
                "--episode", "1", "--start-phase", phase,
            ])
            assert args.start_phase == phase


# ---------------------------------------------------------------------------
# Episode resolution (mock the UI launch to avoid Qt event loop)
# ---------------------------------------------------------------------------


class TestEpisodeResolution:
    def test_nonexistent_experiment(self, populated_repo, capsys):
        code, _, err = _run_cli(capsys, [
            "--root", str(populated_repo.root),
            "visualize", "--experiment", "nope", "--run", "run-0000",
            "--episode", "1",
        ])
        assert code == 1
        assert "not found" in err.lower()

    def test_nonexistent_run(self, populated_repo, capsys):
        code, _, err = _run_cli(capsys, [
            "--root", str(populated_repo.root),
            "visualize", "--experiment", "test-exp", "--run", "nope",
            "--episode", "1",
        ])
        assert code == 1
        assert "not found" in err.lower()

    def test_nonexistent_episode(self, populated_repo, capsys):
        code, _, err = _run_cli(capsys, [
            "--root", str(populated_repo.root),
            "visualize", "--experiment", "test-exp", "--run", "run-0000",
            "--episode", "99",
        ])
        assert code == 1
        assert "not found" in err.lower()

    @patch(
        "axis_system_a.visualization.launch.launch_visualization_from_cli",
        return_value=0,
    )
    def test_valid_episode_resolves(self, mock_launch, populated_repo, capsys):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        code, _, _ = _run_cli(capsys, [
            "--root", str(populated_repo.root),
            "visualize", "--experiment", "test-exp", "--run", "run-0000",
            "--episode", "1",
        ])
        assert code == 0
        mock_launch.assert_called_once()

    @patch(
        "axis_system_a.visualization.launch.launch_visualization_from_cli",
        return_value=0,
    )
    def test_defaults_passed_through(self, mock_launch, populated_repo, capsys):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        _run_cli(capsys, [
            "--root", str(populated_repo.root),
            "visualize", "--experiment", "test-exp", "--run", "run-0000",
            "--episode", "1",
        ])
        _, kwargs = mock_launch.call_args
        assert kwargs.get("start_step") is None
        assert kwargs.get("start_phase") is None


# ---------------------------------------------------------------------------
# Start coordinate passthrough
# ---------------------------------------------------------------------------


class TestStartCoordinatePassthrough:
    @patch(
        "axis_system_a.visualization.launch.launch_visualization_from_cli",
        return_value=0,
    )
    def test_custom_step(self, mock_launch, populated_repo, capsys):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        _run_cli(capsys, [
            "--root", str(populated_repo.root),
            "visualize", "--experiment", "test-exp", "--run", "run-0000",
            "--episode", "1", "--start-step", "2",
        ])
        _, kwargs = mock_launch.call_args
        assert kwargs["start_step"] == 2

    @patch(
        "axis_system_a.visualization.launch.launch_visualization_from_cli",
        return_value=0,
    )
    def test_custom_phase(self, mock_launch, populated_repo, capsys):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from axis_system_a.visualization.snapshot_models import ReplayPhase

        _run_cli(capsys, [
            "--root", str(populated_repo.root),
            "visualize", "--experiment", "test-exp", "--run", "run-0000",
            "--episode", "1", "--start-phase", "AFTER_REGEN",
        ])
        _, kwargs = mock_launch.call_args
        assert kwargs["start_phase"] == ReplayPhase.AFTER_REGEN

    @patch(
        "axis_system_a.visualization.launch.launch_visualization_from_cli",
        return_value=0,
    )
    def test_both_step_and_phase(self, mock_launch, populated_repo, capsys):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from axis_system_a.visualization.snapshot_models import ReplayPhase

        _run_cli(capsys, [
            "--root", str(populated_repo.root),
            "visualize", "--experiment", "test-exp", "--run", "run-0000",
            "--episode", "1", "--start-step", "3", "--start-phase", "AFTER_ACTION",
        ])
        _, kwargs = mock_launch.call_args
        assert kwargs["start_step"] == 3
        assert kwargs["start_phase"] == ReplayPhase.AFTER_ACTION


# ---------------------------------------------------------------------------
# Start coordinate errors (no mock — let real errors propagate)
# ---------------------------------------------------------------------------


class TestStartCoordinateErrors:
    def test_step_out_of_bounds(self, populated_repo, capsys):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        code, _, err = _run_cli(capsys, [
            "--root", str(populated_repo.root),
            "visualize", "--experiment", "test-exp", "--run", "run-0000",
            "--episode", "1", "--start-step", "999",
        ])
        assert code == 1
        assert "out of bounds" in err.lower()

    def test_negative_step(self, populated_repo, capsys):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        code, _, err = _run_cli(capsys, [
            "--root", str(populated_repo.root),
            "visualize", "--experiment", "test-exp", "--run", "run-0000",
            "--episode", "1", "--start-step", "-1",
        ])
        assert code == 1
        assert "out of bounds" in err.lower() or "error" in err.lower()
