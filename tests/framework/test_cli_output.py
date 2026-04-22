from __future__ import annotations

import io

from axis.framework.cli.output import CLITextOutput
from axis.framework.cli.commands.workspaces import _print_changed_config_summary


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
