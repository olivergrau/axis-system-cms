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


@dataclass(frozen=True)
class WorkspaceResetPlan:
    """Preview of generated artifacts that would be cleared by reset."""

    workspace_path: str
    workspace_global_paths: list[str]
    series_paths_by_id: dict[str, list[str]]
    manifest_fields_to_clear: list[str]
    workspace_global_counts: dict[str, int]
    series_counts_by_id: dict[str, dict[str, int]]
    total_paths: int
    total_entries: int
    total_files: int
    total_directories: int


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
        from axis.framework.workspaces.types import load_manifest

        ws = Path(workspace_path)
        manifest_path = ws / "workspace.yaml"
        yaml, data = self._load_yaml_roundtrip_fn(manifest_path)
        manifest = load_manifest(ws)

        cleared_results = self._reset_directory(ws / "results")
        cleared_comparisons = self._reset_directory(ws / "comparisons")
        cleared_measurements = self._reset_directory(ws / "measurements")
        if manifest.experiment_series is not None:
            for entry in manifest.experiment_series.entries:
                series_root = ws / Path(entry.path).parent
                self._reset_directory(series_root / "results")
                self._reset_directory(series_root / "comparisons")
                self._reset_directory(series_root / "measurements")

        self._reset_workspace_artifacts_fn(data)
        self._save_yaml_roundtrip_fn(manifest_path, yaml, data)

        return WorkspaceResetResult(
            workspace_path=str(ws),
            cleared_results=cleared_results,
            cleared_comparisons=cleared_comparisons,
            cleared_measurements=cleared_measurements,
        )

    def plan_reset(self, workspace_path: Path) -> WorkspaceResetPlan:
        """Return a preview of generated artifact scopes affected by reset."""
        from axis.framework.workspaces.types import load_manifest

        ws = Path(workspace_path)
        manifest = load_manifest(ws)
        workspace_global_paths = []
        workspace_global_counts: dict[str, int] = {}
        total_entries = 0
        total_files = 0
        total_directories = 0
        for path in (ws / "results", ws / "comparisons", ws / "measurements"):
            rel = str(path.relative_to(ws))
            workspace_global_paths.append(rel)
            counts = self._count_directory_contents(path)
            workspace_global_counts[rel] = counts["entries"]
            total_entries += counts["entries"]
            total_files += counts["files"]
            total_directories += counts["directories"]

        series_paths_by_id: dict[str, list[str]] = {}
        series_counts_by_id: dict[str, dict[str, int]] = {}
        if manifest.experiment_series is not None:
            for entry in manifest.experiment_series.entries:
                series_root = Path(entry.path).parent
                series_paths = [
                    str(series_root / "results"),
                    str(series_root / "comparisons"),
                    str(series_root / "measurements"),
                ]
                series_paths_by_id[entry.id] = series_paths
                series_counts: dict[str, int] = {}
                for rel in series_paths:
                    counts = self._count_directory_contents(ws / rel)
                    series_counts[rel] = counts["entries"]
                    total_entries += counts["entries"]
                    total_files += counts["files"]
                    total_directories += counts["directories"]
                series_counts_by_id[entry.id] = series_counts
        manifest_fields_to_clear = [
            "primary_results",
            "primary_comparisons",
        ]
        if manifest.experiment_series is not None:
            for entry in manifest.experiment_series.entries:
                prefix = f"experiment_series.entries[{entry.id}].generated"
                manifest_fields_to_clear.extend([
                    f"{prefix}.results",
                    f"{prefix}.comparisons",
                    f"{prefix}.measurement_runs",
                ])
        if manifest.workspace_type.value == "system_development":
            manifest_fields_to_clear.extend([
                "baseline_results",
                "candidate_results",
                "current_candidate_result",
                "current_validation_comparison",
            ])
        return WorkspaceResetPlan(
            workspace_path=str(ws),
            workspace_global_paths=workspace_global_paths,
            series_paths_by_id=series_paths_by_id,
            manifest_fields_to_clear=manifest_fields_to_clear,
            workspace_global_counts=workspace_global_counts,
            series_counts_by_id=series_counts_by_id,
            total_paths=len(workspace_global_paths) + sum(
                len(paths) for paths in series_paths_by_id.values()
            ),
            total_entries=total_entries,
            total_files=total_files,
            total_directories=total_directories,
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

    @staticmethod
    def _count_directory_contents(directory: Path) -> dict[str, int]:
        """Return counts for one generated-artifact root."""
        if not directory.exists():
            return {"entries": 0, "files": 0, "directories": 0}

        entries = 0
        files = 0
        directories = 0
        for child in directory.iterdir():
            entries += 1
            if child.is_dir():
                directories += 1
                for nested in child.rglob("*"):
                    if nested.is_dir():
                        directories += 1
                    else:
                        files += 1
            else:
                files += 1
        return {"entries": entries, "files": files, "directories": directories}
