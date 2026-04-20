"""Workspace run target resolution (WP-05)."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from axis.framework.workspaces.types import (
    load_manifest,
)


class WorkspaceRunTarget(BaseModel, frozen=True):
    """A single resolved run target within a workspace."""

    config_path: str
    role: str  # reference, candidate, baseline, system_under_test


class WorkspaceExecutionPlan(BaseModel, frozen=True):
    """Resolved execution plan for a workspace."""

    workspace_path: str
    targets: list[WorkspaceRunTarget]


def resolve_run_targets(
    workspace_path: Path, run_filter: str | None = None,
) -> WorkspaceExecutionPlan:
    """Resolve workspace configs into executable run targets.

    Parameters
    ----------
    workspace_path:
        Path to the workspace root directory.

    Returns
    -------
    An execution plan with ordered targets.
    """
    from axis.framework.workspaces.handler import get_handler

    ws = Path(workspace_path)
    manifest = load_manifest(ws)

    if manifest.primary_configs:
        configs = manifest.primary_configs
    else:
        configs_dir = ws / "configs"
        configs = sorted(
            str(p.relative_to(ws))
            for p in configs_dir.glob("*.yaml")
        ) if configs_dir.is_dir() else []

    handler = get_handler(manifest.workspace_type)
    targets = handler.resolve_run_targets(ws, manifest, configs, run_filter=run_filter)

    return WorkspaceExecutionPlan(
        workspace_path=str(ws), targets=targets,
    )
