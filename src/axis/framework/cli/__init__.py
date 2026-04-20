"""
System-agnostic CLI for the AXIS Experimentation Framework.

Provides a thin, stateless command-line interface over the execution
and repository layers.  Every command reconstructs state from persisted
artifacts -- no hidden caches or session state.

Usage::

    axis experiments list                         List all experiments
    axis experiments run  <config_path>           Run from config file
    axis experiments resume <experiment_id>       Resume incomplete experiment
    axis experiments show <experiment_id>         Inspect experiment details

    axis runs list --experiment <experiment_id>   List runs in an experiment
    axis runs show <run_id> --experiment <eid>    Inspect a specific run

    axis visualize --experiment <eid> --run <rid> --episode 1
                                                   (stub -- Phase 4)
"""

from __future__ import annotations

from axis.framework.cli.commands.experiments import _load_config_file
from axis.framework.cli.parser import build_parser

__all__ = ["main", "build_parser"]


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns exit code (0=success, 1=error)."""
    from pathlib import Path

    from axis.framework.cli.context import build_context
    from axis.framework.cli.dispatch import dispatch
    from axis.plugins import discover_plugins

    discover_plugins()

    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.entity:
        parser.print_help()
        return 1

    ctx = build_context(Path(args.root))

    return dispatch(args, ctx, parser)


if __name__ == "__main__":
    import sys

    sys.exit(main())
