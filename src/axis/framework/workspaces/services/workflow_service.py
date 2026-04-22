"""Workspace workflow service — mutating workflow state transitions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WorkflowServiceResult:
    """Summary of a workflow mutation."""

    workspace_path: str
    status: str
    lifecycle_stage: str


class WorkspaceWorkflowService:
    """Coordinates manifest-backed workflow mutations."""

    def __init__(
        self,
        close_workspace_fn: Callable[..., None],
        load_yaml_roundtrip_fn: Callable[..., Any],
        save_yaml_roundtrip_fn: Callable[..., None],
    ) -> None:
        self._close_workspace_fn = close_workspace_fn
        self._load_yaml_roundtrip_fn = load_yaml_roundtrip_fn
        self._save_yaml_roundtrip_fn = save_yaml_roundtrip_fn

    def close(self, workspace_path: Path) -> WorkflowServiceResult:
        """Close a workspace and persist the updated manifest."""
        ws = Path(workspace_path)
        manifest_path = ws / "workspace.yaml"
        yaml, data = self._load_yaml_roundtrip_fn(manifest_path)
        self._close_workspace_fn(data)
        self._save_yaml_roundtrip_fn(manifest_path, yaml, data)
        return WorkflowServiceResult(
            workspace_path=str(ws),
            status=data["status"],
            lifecycle_stage=data["lifecycle_stage"],
        )
