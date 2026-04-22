from __future__ import annotations

from axis.framework.cli.parser import build_parser


def test_parser_help_epilog_has_no_duplicate_run_example():
    parser = build_parser()
    help_text = parser.format_help()
    assert help_text.count("axis experiments run config.yaml") == 1
    assert "axis workspaces show <workspace-path>" in help_text
