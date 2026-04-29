"""Workspace workflow service — mutating workflow state transitions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import shutil
from typing import Any


@dataclass(frozen=True)
class WorkflowServiceResult:
    """Summary of a workflow mutation."""

    workspace_path: str
    status: str
    lifecycle_stage: str


@dataclass(frozen=True)
class WorkspaceResetResult:
    """Summary of a workspace artifact reset."""

    workspace_path: str
    cleared_results: int
    cleared_comparisons: int
    cleared_measurements: int


class WorkspaceWorkflowService:
    """Coordinates manifest-backed workflow mutations."""

    def __init__(
        self,
        close_workspace_fn: Callable[..., None],
        reset_workspace_artifacts_fn: Callable[..., None],
        load_yaml_roundtrip_fn: Callable[..., Any],
        save_yaml_roundtrip_fn: Callable[..., None],
    ) -> None:
        self._close_workspace_fn = close_workspace_fn
        self._reset_workspace_artifacts_fn = reset_workspace_artifacts_fn
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

    def reset(self, workspace_path: Path) -> WorkspaceResetResult:
        """Delete generated artifacts and clear their manifest references."""
        ws = Path(workspace_path)
        manifest_path = ws / "workspace.yaml"
        yaml, data = self._load_yaml_roundtrip_fn(manifest_path)

        cleared_results = self._reset_directory(ws / "results")
        cleared_comparisons = self._reset_directory(ws / "comparisons")
        cleared_measurements = self._reset_directory(ws / "measurements")

        self._reset_workspace_artifacts_fn(data)
        self._save_yaml_roundtrip_fn(manifest_path, yaml, data)

        return WorkspaceResetResult(
            workspace_path=str(ws),
            cleared_results=cleared_results,
            cleared_comparisons=cleared_comparisons,
            cleared_measurements=cleared_measurements,
        )

    @staticmethod
    def _reset_directory(directory: Path) -> int:
        """Remove all children from *directory* and recreate it if missing."""
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            return 0

        cleared = 0
        for child in directory.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
            cleared += 1
        return cleared
