"""Workspace manifest model and enumerations (WP-01)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, field_validator, model_validator


class WorkspaceClass(StrEnum):
    DEVELOPMENT = "development"
    INVESTIGATION = "investigation"


class WorkspaceType(StrEnum):
    SYSTEM_DEVELOPMENT = "system_development"
    SINGLE_SYSTEM = "single_system"
    SYSTEM_COMPARISON = "system_comparison"


class WorkspaceStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    CLOSED = "closed"


class WorkspaceLifecycleStage(StrEnum):
    IDEA = "idea"
    DRAFT = "draft"
    SPEC = "spec"
    IMPLEMENTATION = "implementation"
    ANALYSIS = "analysis"
    DOCUMENTATION = "documentation"
    FINAL = "final"


class ArtifactKind(StrEnum):
    SYSTEM = "system"


_VALID_CLASS_TYPE_COMBINATIONS: set[tuple[WorkspaceClass, WorkspaceType]] = {
    (WorkspaceClass.DEVELOPMENT, WorkspaceType.SYSTEM_DEVELOPMENT),
    (WorkspaceClass.INVESTIGATION, WorkspaceType.SINGLE_SYSTEM),
    (WorkspaceClass.INVESTIGATION, WorkspaceType.SYSTEM_COMPARISON),
}


class LinkedArtifactRef(BaseModel, frozen=True):
    """Freeform reference to a linked artifact."""

    id: str
    role: str | None = None
    description: str | None = None


class ResultEntry(BaseModel, frozen=True):
    """Structured primary_results entry with output semantics."""

    path: str
    output_form: str | None = None      # "point" or "sweep"
    trace_mode: str | None = None       # "full" or "light"
    system_type: str | None = None
    role: str | None = None
    created_at: str | None = None
    primary_run_id: str | None = None   # for point outputs
    baseline_run_id: str | None = None  # for sweep outputs
    config: str | None = None
    timestamp: str | None = None
    config_changes: dict[str, Any] | None = None


class WorkspaceManifest(BaseModel, frozen=True):
    """Authoritative workspace manifest model.

    Validates required fields, class/type combinations, and
    type-specific required fields per the v1 specification.
    """

    # --- Required fields (Section 8) ---
    workspace_id: str
    title: str
    workspace_class: WorkspaceClass
    workspace_type: WorkspaceType
    status: WorkspaceStatus
    lifecycle_stage: WorkspaceLifecycleStage
    created_at: str

    # --- Purpose fields (Sections 9) ---
    question: str | None = None
    development_goal: str | None = None

    # --- Artifact fields (Section 10) ---
    artifact_kind: ArtifactKind | None = None
    artifact_under_development: str | None = None
    system_under_test: str | None = None
    reference_system: str | None = None
    candidate_system: str | None = None

    # --- Optional fields (Section 11) ---
    description: str | None = None
    tags: list[str] | None = None
    baseline_artifacts: list[str] | None = None
    validation_scenarios: list[str] | None = None
    primary_configs: list[str] | None = None
    primary_results: list[ResultEntry] | None = None
    primary_comparisons: list[str] | None = None
    # --- Development workflow fields (system_development only) ---
    baseline_config: str | None = None
    candidate_config: str | None = None
    baseline_results: list[str] | None = None
    candidate_results: list[str] | None = None
    current_candidate_result: str | None = None
    current_validation_comparison: str | None = None

    linked_experiments: list[LinkedArtifactRef | str] | None = None
    linked_runs: list[LinkedArtifactRef | str] | None = None
    linked_comparisons: list[LinkedArtifactRef | str] | None = None

    @field_validator("primary_results", mode="before")
    @classmethod
    def _reject_string_result_entries(cls, v: Any) -> Any:
        if v is None:
            return v
        for i, item in enumerate(v):
            if isinstance(item, str):
                raise ValueError(
                    f"primary_results[{i}]: plain string entries are not "
                    f"supported. Use a dict with at least a 'path' key."
                )
        return v

    @model_validator(mode="after")
    def _validate_class_type_and_required_fields(self) -> WorkspaceManifest:
        cls = self.workspace_class
        wtype = self.workspace_type

        if (cls, wtype) not in _VALID_CLASS_TYPE_COMBINATIONS:
            raise ValueError(
                f"Invalid class/type combination: {cls}/{wtype}"
            )

        # Investigation requires question
        if cls == WorkspaceClass.INVESTIGATION and not self.question:
            raise ValueError(
                "Investigation workspaces must define 'question'"
            )

        # Development requires development_goal
        if cls == WorkspaceClass.DEVELOPMENT and not self.development_goal:
            raise ValueError(
                "Development workspaces must define 'development_goal'"
            )

        # system_development requires artifact fields
        if wtype == WorkspaceType.SYSTEM_DEVELOPMENT:
            if not self.artifact_kind:
                raise ValueError(
                    f"{wtype} workspaces must define 'artifact_kind'"
                )
            if not self.artifact_under_development:
                raise ValueError(
                    f"{wtype} workspaces must define "
                    "'artifact_under_development'"
                )
            if self.artifact_kind != ArtifactKind.SYSTEM:
                raise ValueError(
                    f"{wtype} requires artifact_kind='system', "
                    f"got '{self.artifact_kind}'"
                )

        # single_system requires system_under_test
        if wtype == WorkspaceType.SINGLE_SYSTEM and not self.system_under_test:
            raise ValueError(
                "single_system workspaces must define 'system_under_test'"
            )

        # system_comparison requires reference + candidate
        if wtype == WorkspaceType.SYSTEM_COMPARISON:
            if not self.reference_system:
                raise ValueError(
                    "system_comparison workspaces must define "
                    "'reference_system'"
                )
            if not self.candidate_system:
                raise ValueError(
                    "system_comparison workspaces must define "
                    "'candidate_system'"
                )

        return self


def load_manifest(workspace_path: Any) -> WorkspaceManifest:
    """Load and validate a workspace manifest from disk.

    Parameters
    ----------
    workspace_path:
        Path to the workspace root directory (containing workspace.yaml).
    """
    from pathlib import Path

    import yaml

    manifest_file = Path(workspace_path) / "workspace.yaml"
    data = yaml.safe_load(manifest_file.read_text())
    return WorkspaceManifest.model_validate(data)


def result_entry_path(entry: ResultEntry) -> str:
    """Extract the path string from a primary_results entry."""
    return entry.path
