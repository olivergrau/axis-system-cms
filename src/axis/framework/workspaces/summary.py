"""Workspace read-only summary (WP-04)."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from axis.framework.workspaces.types import (
    WorkspaceClass,
    WorkspaceLifecycleStage,
    WorkspaceManifest,
    WorkspaceStatus,
    WorkspaceType,
    load_manifest,
)
from axis.framework.workspaces.validation import (
    WorkspaceCheckResult,
    check_workspace,
)


class ArtifactEntry(BaseModel, frozen=True):
    """A declared primary artifact with its existence status."""

    path: str
    exists: bool
    config: str | None = None
    role: str | None = None
    timestamp: str | None = None
    output_form: str | None = None
    system_type: str | None = None
    primary_run_id: str | None = None
    baseline_run_id: str | None = None
    config_changes: dict[str, object] | None = None


class WorkspaceSummary(BaseModel, frozen=True):
    """Structured workspace summary for presentation."""

    workspace_id: str
    title: str
    workspace_class: WorkspaceClass
    workspace_type: WorkspaceType
    status: WorkspaceStatus
    lifecycle_stage: WorkspaceLifecycleStage
    description: str | None = None

    # Purpose
    question: str | None = None
    development_goal: str | None = None

    # Key artifact info
    system_under_test: str | None = None
    reference_system: str | None = None
    candidate_system: str | None = None
    artifact_under_development: str | None = None

    # Primary artifacts with existence checks
    primary_configs: list[ArtifactEntry] = []
    primary_results: list[ArtifactEntry] = []
    primary_comparisons: list[ArtifactEntry] = []
    primary_measurements: list[ArtifactEntry] = []

    # Checker result
    check_result: WorkspaceCheckResult | None = None

    # Development workflow fields (system_development only)
    baseline_config: str | None = None
    candidate_config: str | None = None
    baseline_results: list[ArtifactEntry] = []
    candidate_results: list[ArtifactEntry] = []
    current_candidate_result: ArtifactEntry | None = None
    current_validation_comparison: ArtifactEntry | None = None
    development_state: str | None = None  # "pre-candidate" or "post-candidate"


def _resolve_artifacts(
    ws: Path, paths: list | None,
) -> list[ArtifactEntry]:
    """Build artifact entries with existence checks.

    Handles plain string entries, annotated dict entries
    (with ``path``, ``config``, ``role``, ``timestamp`` keys),
    and ``ResultEntry`` objects.
    """
    if not paths:
        return []

    from axis.framework.workspaces.types import ResultEntry

    entries: list[ArtifactEntry] = []
    for item in paths:
        if isinstance(item, ResultEntry):
            entries.append(ArtifactEntry(
                path=item.path,
                exists=(ws / item.path).exists(),
                config=item.config,
                role=item.role,
                timestamp=item.timestamp,
                output_form=item.output_form,
                system_type=item.system_type,
                primary_run_id=item.primary_run_id,
                baseline_run_id=item.baseline_run_id,
                config_changes=item.config_changes,
            ))
        elif isinstance(item, dict):
            p = item["path"]
            entries.append(ArtifactEntry(
                path=p,
                exists=(ws / p).exists(),
                config=item.get("config"),
                role=item.get("role"),
                timestamp=item.get("timestamp"),
                output_form=item.get("output_form"),
                system_type=item.get("system_type"),
                primary_run_id=item.get("primary_run_id"),
                baseline_run_id=item.get("baseline_run_id"),
                config_changes=item.get("config_changes"),
            ))
        else:
            entries.append(ArtifactEntry(
                path=item, exists=(ws / item).exists()))
    return entries


def summarize_workspace(workspace_path: Path) -> WorkspaceSummary:
    """Build a read-only summary of a workspace.

    Parameters
    ----------
    workspace_path:
        Path to the workspace root directory.
    """
    ws = Path(workspace_path)
    manifest = load_manifest(ws)
    check_result = check_workspace(ws)

    # Development-specific fields
    dev_kwargs: dict = {}
    if manifest.workspace_type in (
        WorkspaceType.SYSTEM_DEVELOPMENT,
    ):
        dev_kwargs["baseline_config"] = manifest.baseline_config
        dev_kwargs["candidate_config"] = manifest.candidate_config
        dev_kwargs["baseline_results"] = _resolve_artifacts(
            ws, manifest.baseline_results)
        dev_kwargs["candidate_results"] = _resolve_artifacts(
            ws, manifest.candidate_results)
        if manifest.current_candidate_result:
            dev_kwargs["current_candidate_result"] = ArtifactEntry(
                path=manifest.current_candidate_result,
                exists=(ws / manifest.current_candidate_result).exists(),
            )
        if manifest.current_validation_comparison:
            dev_kwargs["current_validation_comparison"] = ArtifactEntry(
                path=manifest.current_validation_comparison,
                exists=(ws / manifest.current_validation_comparison).exists(),
            )
        dev_kwargs["development_state"] = (
            "post-candidate" if manifest.candidate_config
            else "pre-candidate"
        )

    return WorkspaceSummary(
        workspace_id=manifest.workspace_id,
        title=manifest.title,
        workspace_class=manifest.workspace_class,
        workspace_type=manifest.workspace_type,
        status=manifest.status,
        lifecycle_stage=manifest.lifecycle_stage,
        description=manifest.description,
        question=manifest.question,
        development_goal=manifest.development_goal,
        system_under_test=manifest.system_under_test,
        reference_system=manifest.reference_system,
        candidate_system=manifest.candidate_system,
        artifact_under_development=manifest.artifact_under_development,
        primary_configs=_resolve_artifacts(ws, manifest.primary_configs),
        primary_results=_resolve_artifacts(ws, manifest.primary_results),
        primary_comparisons=_resolve_artifacts(ws, manifest.primary_comparisons),
        primary_measurements=_resolve_artifacts(
            ws, manifest.primary_measurements),
        check_result=check_result,
        **dev_kwargs,
    )
