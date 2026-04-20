"""CLI command for interactive visualization."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def cmd_visualize(args: argparse.Namespace, repo, catalogs: dict | None = None) -> None:
    """Launch the interactive visualization viewer."""
    from axis.visualization.launch import launch_visualization

    experiment = args.experiment
    run = args.run
    episode_index = args.episode

    # Workspace mode: resolve from workspace.
    if args.workspace:
        from axis.framework.workspaces.visualization import (
            resolve_visualization_target,
        )
        ws_experiment = args.experiment
        experiment, run, episode_index = resolve_visualization_target(
            Path(args.workspace), episode_index,
            role=args.role, experiment=ws_experiment, run=run,
        )
        # Visualization uses workspace-local repo.
        from axis.framework.persistence import ExperimentRepository
        repo = ExperimentRepository(Path(args.workspace) / "results")

    if not experiment or not run:
        print(
            "Error: Provide --experiment and --run, or --workspace.",
            file=sys.stderr,
        )
        sys.exit(1)

    sys.exit(launch_visualization(
        repo, experiment, run, episode_index,
        start_step=args.step, start_phase=args.phase,
        scale=args.scale,
        world_vis_catalog=catalogs.get("world_vis") if catalogs else None,
        system_vis_catalog=catalogs.get("system_vis") if catalogs else None,
    ))
