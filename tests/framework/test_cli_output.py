from __future__ import annotations

import io
import json
from unittest.mock import MagicMock

from axis.framework.cli.output import CLITextOutput
from axis.framework.cli.commands.workspaces import (
    _format_workspace_lifecycle,
    _format_workspace_status,
    _print_artifact_section,
    _print_changed_config_summary,
    cmd_workspaces_close,
)


def test_cli_text_output_renders_plain_text_sections_and_fields():
    stream = io.StringIO()
    out = CLITextOutput(stream=stream, style=False)

    out.title("Runs")
    out.kv("Status", "completed")
    out.section("Summary")
    out.list_row("run-0000", "[completed]", "summary=yes")

    assert stream.getvalue() == (
        "Runs\n"
        "  Status: completed\n"
        "\n"
        "Summary\n"
        "  run-0000  [completed]  summary=yes\n"
    )


def test_cli_text_output_renders_error_and_hint():
    stream = io.StringIO()
    out = CLITextOutput(stream=stream, style=False)

    out.error("Experiment not found: exp-123", hint="Run `axis experiments list`.")

    assert stream.getvalue() == (
        "Error: Experiment not found: exp-123\n"
        "  Hint: Run `axis experiments list`.\n"
    )


def test_cli_text_output_can_style_diff_text():
    stream = io.StringIO()
    out = CLITextOutput(stream=stream, style=True)

    rendered = out.styled("system.alpha: 0.2", role="diff")

    assert rendered.startswith("\x1b[1;33m")
    assert rendered.endswith("\x1b[0m")


def test_changed_config_summary_uses_diff_styling():
    stream = io.StringIO()
    out = CLITextOutput(stream=stream, style=True)

    _print_changed_config_summary(
        {"execution": {"max_steps": 150}, "system": {"policy": {"temperature": 2.0}}},
        out=out,
    )

    rendered = stream.getvalue()
    assert "\x1b[1;33m" in rendered
    assert "execution.max_steps: 150" in rendered
    assert "system.policy.temperature: 2.0" in rendered


def test_workspaces_close_text_output(capsys):
    workflow_service = MagicMock()
    workflow_service.close.return_value = MagicMock(
        workspace_path="/tmp/ws",
        status="closed",
        lifecycle_stage="final",
    )

    cmd_workspaces_close("/tmp/ws", "text", workflow_service=workflow_service)

    captured = capsys.readouterr()
    assert "workspace closed: ws" in captured.out
    assert "Status: closed" in captured.out
    assert "Lifecycle: final" in captured.out


def test_workspaces_close_json_output(capsys):
    workflow_service = MagicMock()
    workflow_service.close.return_value = MagicMock(
        workspace_path="/tmp/ws",
        status="closed",
        lifecycle_stage="final",
    )

    cmd_workspaces_close("/tmp/ws", "json", workflow_service=workflow_service)

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["workspace_path"] == "/tmp/ws"
    assert data["status"] == "closed"
    assert data["lifecycle_stage"] == "final"


def test_workspace_status_formatting_uses_semantic_styling():
    stream = io.StringIO()
    out = CLITextOutput(stream=stream, style=True)

    rendered = _format_workspace_status("closed", out=out)

    assert rendered.startswith("\x1b[1;31m")
    assert "CLOSED" in rendered
    assert rendered.endswith("\x1b[0m")


def test_workspace_lifecycle_formatting_uses_emphasis_styling():
    stream = io.StringIO()
    out = CLITextOutput(stream=stream, style=True)

    rendered = _format_workspace_lifecycle("implementation", out=out)

    assert rendered.startswith("\x1b[1m")
    assert "IMPLEMENTATION" in rendered
    assert rendered.endswith("\x1b[0m")


def test_workspace_artifact_section_shows_trace_mode():
    stream = io.StringIO()
    out = CLITextOutput(stream=stream, style=False)
    entry = MagicMock(
        exists=True,
        path="results/exp-001",
        config="results/exp-001/experiment_config.json",
        output_form="point",
        trace_mode="light",
        role="reference",
        timestamp="2026-04-24T00:00:00",
        reference_experiment_id=None,
        candidate_experiment_id=None,
        comparison_config_changes=None,
        config_changes=None,
    )

    _print_artifact_section("Primary results", [entry], out=out)

    rendered = stream.getvalue()
    assert "trace=light" in rendered
