"""CLI argument parser construction."""

from __future__ import annotations

import argparse
import os
import sys

from axis.version import __version__

ASCII_BANNER = """\
   █████╗ ██╗  ██╗██╗███████╗
  ██╔══██╗╚██╗██╔╝██║██╔════╝
  ███████║ ╚███╔╝ ██║███████╗
  ██╔══██║ ██╔██╗ ██║╚════██║
  ██║  ██║██╔╝ ██╗██║███████║
  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚══════╝

        C M S
  Complex Mechanistic Systems
"""


def _build_cli_header() -> str:
    """Render the top-level CLI header shown in root help output."""
    return f"{ASCII_BANNER}\nVersion {__version__}\n"


def _style_enabled() -> bool:
    """Return whether ANSI emphasis should be applied to help output."""
    if os.getenv("NO_COLOR"):
        return False
    isatty = getattr(sys.stdout, "isatty", None)
    return bool(isatty and isatty())


def _decorate(text: str, *, role: str) -> str:
    """Decorate help text for terminal output when styling is enabled."""
    if not _style_enabled():
        return text
    code = {
        "title": "1",
        "section": "1;36",
        "secondary": "2",
        "accent": "1;33",
    }.get(role)
    if not code:
        return text
    return f"\033[{code}m{text}\033[0m"


def _replace_section_label(line: str, label: str) -> str:
    """Convert argparse section labels into visually stronger headings."""
    if line == f"{label}:":
        return _decorate(label.title(), role="section")
    return line


class AxisArgumentParser(argparse.ArgumentParser):
    """ArgumentParser with branded top-level help output."""

    def format_help(self) -> str:
        separator = _decorate("=" * 78, role="secondary")
        title = _decorate("AXIS Experimentation Framework CLI", role="title")

        help_lines = super().format_help().splitlines()
        filtered_lines: list[str] = []
        for line in help_lines:
            if line == "AXIS Experimentation Framework CLI":
                continue
            line = _replace_section_label(line, "options")
            line = _replace_section_label(line, "commands")
            line = _replace_section_label(line, "examples")
            filtered_lines.append(line)

        docs_lines = [
            _decorate("Documentation", role="section"),
            f"  Start local docs: {_decorate('make docs-serve', role='accent')}",
            f"  Open in browser:  {_decorate('http://localhost:8000', role='accent')}",
        ]

        parts = [
            _build_cli_header().rstrip(),
            separator,
            title,
            separator,
            "\n".join(filtered_lines).rstrip(),
            separator,
            "\n".join(docs_lines),
        ]
        return "\n".join(parts) + "\n"


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--root", default=argparse.SUPPRESS,
        help="Path to experiment repository root (default: ./experiments/results)",
    )
    common.add_argument(
        "--output", choices=["text", "json"], default=argparse.SUPPRESS,
        help="Output format (default: text)",
    )

    parser = AxisArgumentParser(
        prog="axis",
        description="AXIS Experimentation Framework CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  axis experiments list                         List all experiments
  axis experiments run config.yaml              Run experiment from config
  axis experiments show <experiment_id>         Inspect experiment details
  axis experiments resume <experiment_id>       Resume incomplete experiment

  axis runs list --experiment <experiment_id>   List runs in an experiment
  axis runs show <run_id> --experiment <eid>    Inspect a specific run
  axis runs metrics <run_id> --experiment <eid> Compute or inspect behavioral metrics

  axis visualize --experiment <eid> --run <rid> --episode 1

  axis compare --reference-experiment <eid> --reference-run <rid> --reference-episode 0 \\
               --candidate-experiment <eid2> --candidate-run <rid2> --candidate-episode 0

  axis workspaces show <workspace-path>         Inspect workspace state
  axis workspaces reset <workspace-path>        Clear workspace results and comparisons
  axis workspaces run-metrics <workspace-path>  Inspect metrics for one resolved run
  axis workspaces compare <workspace-path>      Run a workspace comparison
  axis workspaces run-series <workspace-path>   Run a declarative experiment series

  Use --output json on any command for machine-readable output.
  Use --root <path> to point to a non-default repository location.
""",
    )
    parser.add_argument(
        "--root", default="./experiments/results",
        help="Path to experiment repository root (default: ./experiments/results)",
    )
    parser.add_argument(
        "--output", choices=["text", "json"], default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"axis {__version__}",
        help="Show the AXIS CLI version and exit",
    )

    entity_sub = parser.add_subparsers(dest="entity", title="commands")

    # -- experiments ---------------------------------------------------------
    exp_parser = entity_sub.add_parser(
        "experiments",
        help="Manage experiments (list, run, resume, show)",
    )
    exp_action = exp_parser.add_subparsers(dest="action", title="actions")

    exp_action.add_parser(
        "list", parents=[common], help="List all experiments")

    run_p = exp_action.add_parser(
        "run", parents=[common],
        help="Execute a new experiment from a YAML/JSON config file",
    )
    run_p.add_argument(
        "config_path", help="Path to experiment config (YAML or JSON)")

    resume_p = exp_action.add_parser(
        "resume", parents=[common], help="Resume an incomplete experiment")
    resume_p.add_argument(
        "experiment_id", help="ID of the experiment to resume")

    show_p = exp_action.add_parser(
        "show", parents=[common], help="Show experiment details")
    show_p.add_argument(
        "experiment_id", help="ID of the experiment to inspect")

    # -- runs ----------------------------------------------------------------
    runs_parser = entity_sub.add_parser(
        "runs",
        help="Inspect runs within an experiment (list, show, metrics)",
    )
    runs_action = runs_parser.add_subparsers(dest="action", title="actions")

    list_runs_p = runs_action.add_parser(
        "list", parents=[common], help="List all runs in an experiment")
    list_runs_p.add_argument(
        "--experiment", required=True, help="Experiment ID",
    )

    show_run_p = runs_action.add_parser(
        "show", parents=[common], help="Show run details",
    )
    show_run_p.add_argument("run_id", help="ID of the run to inspect")
    show_run_p.add_argument(
        "--experiment", required=True, help="Experiment ID the run belongs to",
    )

    metrics_run_p = runs_action.add_parser(
        "metrics", parents=[common], help="Compute or show run behavioral metrics",
    )
    metrics_run_p.add_argument("run_id", help="ID of the run to inspect")
    metrics_run_p.add_argument(
        "--experiment", required=True, help="Experiment ID the run belongs to",
    )

    # -- compare -------------------------------------------------------------
    cmp_parser = entity_sub.add_parser(
        "compare", parents=[common],
        help="Compare two episode traces or full runs (paired trace comparison)",
    )
    cmp_parser.add_argument(
        "--reference-experiment", required=True, help="Reference experiment ID")
    cmp_parser.add_argument(
        "--reference-run", required=True, help="Reference run ID")
    cmp_parser.add_argument(
        "--reference-episode", type=int, default=None,
        help="Reference episode index (omit for full-run comparison)")
    cmp_parser.add_argument(
        "--candidate-experiment", required=True, help="Candidate experiment ID")
    cmp_parser.add_argument(
        "--candidate-run", required=True, help="Candidate run ID")
    cmp_parser.add_argument(
        "--candidate-episode", type=int, default=None,
        help="Candidate episode index (omit for full-run comparison)")
    cmp_parser.add_argument(
        "--allow-world-changes",
        action="store_true",
        default=False,
        help=(
            "Allow comparisons when only the world configuration differs. "
            "World type, start position, seed, and action-space validation "
            "still remain strict."
        ),
    )

    # -- visualize -----------------------------------------------------------
    viz_parser = entity_sub.add_parser(
        "visualize", parents=[common],
        help="Launch interactive episode viewer",
    )
    viz_parser.add_argument(
        "--experiment", default=None, help="Experiment ID")
    viz_parser.add_argument(
        "--run", default=None, help="Run ID within the experiment")
    viz_parser.add_argument(
        "--workspace", default=None,
        help="Workspace path (alternative to --experiment/--run)")
    viz_parser.add_argument(
        "--role", default=None,
        help="Role filter for workspace visualization (reference/candidate)")
    viz_parser.add_argument(
        "--episode", type=int, required=True, help="Episode index (1-based)",
    )
    viz_parser.add_argument(
        "--step", type=int, default=None, help="Initial step (0-based)",
    )
    viz_parser.add_argument(
        "--phase", type=int, default=None, help="Initial phase index",
    )
    viz_parser.add_argument(
        "--scale", type=float, default=1.0,
        help="UI scale factor (default: 1.0). E.g. 1.5 for a larger window.",
    )
    viz_parser.add_argument(
        "--width-percent", type=float, default=None,
        help=(
            "Initial viewer width as a percentage of the primary screen width. "
            "Example: 80 for 80%% of the current resolution."
        ),
    )

    # -- workspaces ------------------------------------------------------------
    ws_parser = entity_sub.add_parser(
        "workspaces",
        help=(
            "Manage experiment workspaces "
            "(scaffold, close, reset, check, show, run, compare, measure, run-series, compare-configs)"
        ),
    )
    ws_action = ws_parser.add_subparsers(dest="action", title="actions")

    ws_action.add_parser(
        "scaffold", parents=[common],
        help="Interactively create a new workspace",
    )

    ws_close_p = ws_action.add_parser(
        "close", parents=[common], help="Close a workspace",
    )
    ws_close_p.add_argument(
        "workspace_path", help="Path to workspace directory")

    ws_reset_p = ws_action.add_parser(
        "reset", parents=[common],
        help="Delete workspace results/comparisons and clear manifest tracking",
    )
    ws_reset_p.add_argument(
        "workspace_path", help="Path to workspace directory")

    ws_check_p = ws_action.add_parser(
        "check", parents=[common], help="Validate a workspace",
    )
    ws_check_p.add_argument(
        "workspace_path", help="Path to workspace directory")

    ws_show_p = ws_action.add_parser(
        "show", parents=[common], help="Show workspace summary",
    )
    ws_show_p.add_argument(
        "workspace_path", help="Path to workspace directory")

    ws_run_p = ws_action.add_parser(
        "run", parents=[common], help="Execute workspace configs",
    )
    ws_run_p.add_argument(
        "workspace_path", help="Path to workspace directory")
    ws_run_p.add_argument(
        "--baseline-only", action="store_true", default=False,
        help="Run only the baseline config (system_development)")
    ws_run_p.add_argument(
        "--candidate-only", action="store_true", default=False,
        help="Run only the candidate config (system_development)")
    ws_run_p.add_argument(
        "--allow-world-changes",
        action="store_true",
        default=False,
        help=(
            "Treat world-only config changes as intentional and allow the run. "
            "Without this flag, world-only edits do not bypass duplicate-run protection."
        ),
    )
    ws_run_p.add_argument(
        "--override-guard",
        action="store_true",
        default=False,
        help=(
            "Bypass the duplicate-run guard and execute even when no relevant "
            "config changes are detected."
        ),
    )
    ws_run_p.add_argument(
        "--notes",
        default=None,
        help=(
            "Optional run note to store with each resulting primary_results "
            "entry in the workspace manifest."
        ),
    )

    ws_cmp_p = ws_action.add_parser(
        "compare", parents=[common], help="Run workspace comparison",
    )
    ws_cmp_p.add_argument(
        "workspace_path", help="Path to workspace directory")
    ws_cmp_p.add_argument(
        "--reference-experiment", default=None,
        help="Experiment ID for reference side (must exist in workspace results)")
    ws_cmp_p.add_argument(
        "--candidate-experiment", default=None,
        help="Experiment ID for candidate side (must exist in workspace results)")
    ws_cmp_p.add_argument(
        "--allow-world-changes",
        action="store_true",
        default=False,
        help=(
            "Allow comparisons when only the world configuration differs. "
            "Useful for comparing world-state manipulations explicitly."
        ),
    )

    ws_measure_p = ws_action.add_parser(
        "measure", parents=[common],
        help="Run the system_comparison measurement workflow and export logs",
    )
    ws_measure_p.add_argument(
        "workspace_path", help="Path to workspace directory")
    ws_measure_p.add_argument(
        "--label",
        default=None,
        help=(
            "Optional filename label override for this measurement run. "
            "Overrides the manifest-derived label token but keeps the next "
            "measurement directory number."
        ),
    )
    ws_measure_p.add_argument(
        "--allow-world-changes",
        action="store_true",
        default=False,
        help=(
            "Treat world-only config changes as intentional for both run and "
            "compare during the measurement workflow."
        ),
    )
    ws_measure_p.add_argument(
        "--override-guard",
        action="store_true",
        default=False,
        help=(
            "Bypass the duplicate-run guard during the measurement workflow."
        ),
    )
    ws_measure_p.add_argument(
        "--notes",
        default=None,
        help=(
            "Optional run note to store with each resulting primary_results "
            "entry created by the measurement workflow."
        ),
    )

    ws_series_p = ws_action.add_parser(
        "run-series", parents=[common],
        help="Run a declarative experiment series for a system_comparison workspace",
    )
    ws_series_p.add_argument(
        "workspace_path", help="Path to workspace directory")
    ws_series_p.add_argument(
        "--allow-world-changes",
        action="store_true",
        default=False,
        help=(
            "Treat world-only config changes as intentional during series execution."
        ),
    )
    ws_series_p.add_argument(
        "--override-guard",
        action="store_true",
        default=False,
        help=(
            "Bypass the duplicate-run guard while executing the experiment series."
        ),
    )
    ws_series_p.add_argument(
        "--update-notes",
        action="store_true",
        default=False,
        help=(
            "Overwrite notes.md with a regenerated scaffold after the series completes."
        ),
    )

    ws_cmp_cfg_p = ws_action.add_parser(
        "compare-configs",
        parents=[common],
        help="Show reference/candidate config deltas for a system_comparison workspace",
    )
    ws_cmp_cfg_p.add_argument(
        "workspace_path", help="Path to workspace directory")

    ws_cr_p = ws_action.add_parser(
        "comparison-summary", parents=[common],
        help="Display stored workspace comparison summary result(s)",
    )
    ws_cr_p.add_argument(
        "workspace_path", help="Path to workspace directory")
    ws_cr_p.add_argument(
        "--number", type=int, default=None,
        help="Comparison number to display (e.g. 1, 2). "
             "If omitted, lists all or shows the only one.")
    ws_cr_p.add_argument(
        "--allow-world-changes",
        action="store_true",
        default=False,
        help=(
            "Recompute the stored comparison for display while allowing "
            "world-configuration differences."
        ),
    )

    ws_sc_p = ws_action.add_parser(
        "set-candidate", parents=[common],
        help="Set the candidate config for a development workspace",
    )
    ws_sc_p.add_argument(
        "workspace_path", help="Path to workspace directory")
    ws_sc_p.add_argument(
        "config_path",
        help="Workspace-relative path to the candidate config file "
             "(e.g. configs/candidate-system_demo.yaml)")

    ws_sr_p = ws_action.add_parser(
        "run-summary", parents=[common],
        help="Inspect one resolved run in a workspace",
    )
    ws_sr_p.add_argument(
        "workspace_path", help="Path to workspace directory")
    ws_sr_p.add_argument(
        "--role", default=None,
        help="Role selector for comparison/development workspaces "
             "(reference, candidate, baseline)")
    ws_sr_p.add_argument(
        "--experiment", default=None,
        help="Explicit experiment ID in workspace results")
    ws_sr_p.add_argument(
        "--run", default=None,
        help="Explicit run ID (required for sweep outputs)")

    ws_rm_p = ws_action.add_parser(
        "run-metrics", parents=[common],
        help="Inspect behavioral metrics for one resolved run in a workspace",
    )
    ws_rm_p.add_argument(
        "workspace_path", help="Path to workspace directory")
    ws_rm_p.add_argument(
        "--role", default=None,
        help="Role selector for comparison/development workspaces "
             "(reference, candidate, baseline)")
    ws_rm_p.add_argument(
        "--experiment", default=None,
        help="Explicit experiment ID in workspace results")
    ws_rm_p.add_argument(
        "--run", default=None,
        help="Explicit run ID (required for sweep outputs)")

    ws_sr_p = ws_action.add_parser(
        "sweep-result", parents=[common],
        help="Inspect a sweep (OFAT) result in a workspace",
    )
    ws_sr_p.add_argument(
        "workspace_path", help="Path to workspace directory")
    ws_sr_p.add_argument(
        "--experiment", default=None,
        help="Explicit experiment ID (defaults to newest sweep)")

    return parser
