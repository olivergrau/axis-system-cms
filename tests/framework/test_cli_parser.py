from __future__ import annotations

from axis.framework.cli.parser import build_parser


def test_parser_help_epilog_has_no_duplicate_run_example():
    parser = build_parser()
    help_text = parser.format_help()
    assert help_text.count("axis experiments run config.yaml") == 1
    assert "axis workspaces show <workspace-path>" in help_text


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
