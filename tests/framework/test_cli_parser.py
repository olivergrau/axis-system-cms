from __future__ import annotations

import pytest

from axis.framework.cli.parser import build_parser
from axis.version import __version__


def test_parser_help_epilog_has_no_duplicate_run_example():
    parser = build_parser()
    help_text = parser.format_help()
    assert "Complex Mechanistic Systems" in help_text
    assert f"Version {__version__}" in help_text
    assert "Documentation" in help_text
    assert "make docs-serve" in help_text
    assert "http://localhost:8000" in help_text
    assert help_text.count("axis experiments run config.yaml") == 1
    assert "axis workspaces show <workspace-path>" in help_text


def test_parser_help_contains_ascii_banner():
    parser = build_parser()
    help_text = parser.format_help()
    assert "█████╗" in help_text
    assert "C M S" in help_text
    assert "=" * 78 in help_text


def test_parser_version_flag_exits_with_version(capsys):
    parser = build_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--version"])
    captured = capsys.readouterr()
    assert exc.value.code == 0
    assert captured.out.strip() == f"axis {__version__}"


def test_parser_accepts_workspaces_close_subcommand():
    parser = build_parser()
    args = parser.parse_args(["workspaces", "close", "/tmp/ws"])
    assert args.entity == "workspaces"
    assert args.action == "close"
    assert args.workspace_path == "/tmp/ws"


def test_parser_accepts_compare_allow_world_changes():
    parser = build_parser()
    args = parser.parse_args([
        "compare",
        "--reference-experiment", "ref-exp",
        "--reference-run", "run-1",
        "--candidate-experiment", "cand-exp",
        "--candidate-run", "run-1",
        "--allow-world-changes",
    ])
    assert args.entity == "compare"
    assert args.allow_world_changes is True


def test_parser_accepts_workspace_comparison_result_allow_world_changes():
    parser = build_parser()
    args = parser.parse_args([
        "workspaces", "comparison-summary", "/tmp/ws", "--allow-world-changes",
    ])
    assert args.entity == "workspaces"
    assert args.action == "comparison-summary"
    assert args.allow_world_changes is True


def test_parser_accepts_workspace_run_allow_world_changes():
    parser = build_parser()
    args = parser.parse_args([
        "workspaces", "run", "/tmp/ws", "--allow-world-changes",
    ])
    assert args.entity == "workspaces"
    assert args.action == "run"
    assert args.allow_world_changes is True


def test_parser_accepts_workspace_run_override_guard():
    parser = build_parser()
    args = parser.parse_args([
        "workspaces", "run", "/tmp/ws", "--override-guard",
    ])
    assert args.entity == "workspaces"
    assert args.action == "run"
    assert args.override_guard is True


def test_parser_accepts_workspace_run_notes():
    parser = build_parser()
    args = parser.parse_args([
        "workspaces", "run", "/tmp/ws", "--notes", "My notes for this run",
    ])
    assert args.entity == "workspaces"
    assert args.action == "run"
    assert args.notes == "My notes for this run"


def test_parser_accepts_workspace_compare_configs():
    parser = build_parser()
    args = parser.parse_args([
        "workspaces", "compare-configs", "/tmp/ws",
    ])
    assert args.entity == "workspaces"
    assert args.action == "compare-configs"
    assert args.workspace_path == "/tmp/ws"


def test_parser_accepts_workspace_run_summary_arguments():
    parser = build_parser()
    args = parser.parse_args([
        "workspaces", "run-summary", "/tmp/ws",
        "--role", "reference",
        "--experiment", "exp-123",
        "--run", "run-0001",
    ])
    assert args.entity == "workspaces"
    assert args.action == "run-summary"
    assert args.workspace_path == "/tmp/ws"
    assert args.role == "reference"
    assert args.experiment == "exp-123"
    assert args.run == "run-0001"


def test_parser_accepts_runs_metrics_arguments():
    parser = build_parser()
    args = parser.parse_args([
        "runs", "metrics", "run-0001", "--experiment", "exp-123",
    ])
    assert args.entity == "runs"
    assert args.action == "metrics"
    assert args.run_id == "run-0001"
    assert args.experiment == "exp-123"


def test_parser_accepts_workspace_run_metrics_arguments():
    parser = build_parser()
    args = parser.parse_args([
        "workspaces", "run-metrics", "/tmp/ws",
        "--role", "reference",
        "--experiment", "exp-123",
        "--run", "run-0001",
    ])
    assert args.entity == "workspaces"
    assert args.action == "run-metrics"
    assert args.workspace_path == "/tmp/ws"
    assert args.role == "reference"
    assert args.experiment == "exp-123"
    assert args.run == "run-0001"


def test_parser_accepts_visualize_width_percent():
    parser = build_parser()
    args = parser.parse_args([
        "visualize",
        "--experiment", "exp-123",
        "--run", "run-0001",
        "--episode", "0",
        "--width-percent", "80",
    ])
    assert args.entity == "visualize"
    assert args.width_percent == 80.0
