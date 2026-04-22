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
