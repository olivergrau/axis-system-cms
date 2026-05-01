"""Workspace manifest model and enumerations (WP-01)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


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
    run_notes: str | None = None
    config_changes: dict[str, Any] | None = None


class ConfigEntry(BaseModel, frozen=True):
    """Structured primary_configs entry with workspace role semantics."""

    path: str
    role: str | None = None


class MeasurementWorkflowConfig(BaseModel, frozen=True):
    """Optional workspace-local automation config for measurement workflows."""

    root_dir: str = "measurements"
    experiment_dir_pattern: str = "experiment_{number}"
    label_pattern: str = "config{number}"
    comparison_log_pattern: str = "{label}-comparison.log"
    run_summary_log_pattern: str = "{label}-{role}-run-summary.log"
    default_run_summary_role: str = "candidate"

    @field_validator("experiment_dir_pattern", "label_pattern")
    @classmethod
    def _require_number_placeholder(cls, value: str) -> str:
        if "{number}" not in value:
            raise ValueError("pattern must include '{number}'")
        return value

    @field_validator("root_dir")
    @classmethod
    def _validate_root_dir(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("root_dir must not be empty")
        return value

    @field_validator("default_run_summary_role")
    @classmethod
    def _validate_default_role(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("default_run_summary_role must not be empty")
        return value


class SeriesMeasurementRunEntry(BaseModel, frozen=True):
    """Structured series-local measurement tracking entry."""

    path: str
    label: str | None = None
    timestamp: str | None = None


class ExperimentSeriesGeneratedArtifacts(BaseModel, frozen=True):
    """Generated artifact tracking for one registered series."""

    results: list[ResultEntry] = Field(default_factory=list)
    comparisons: list[str] = Field(default_factory=list)
    measurement_runs: list[SeriesMeasurementRunEntry] = Field(default_factory=list)


class ExperimentSeriesEntry(BaseModel, frozen=True):
    """Registered experiment series entry in workspace.yaml."""

    id: str
    path: str
    title: str | None = None
    generated: ExperimentSeriesGeneratedArtifacts = Field(
        default_factory=ExperimentSeriesGeneratedArtifacts
    )

    @field_validator("id", "path")
    @classmethod
    def _require_non_empty_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be empty")
        return value

    @field_validator("path")
    @classmethod
    def _validate_series_path(cls, value: str) -> str:
        if value.startswith("/"):
            raise ValueError("series path must be workspace-relative")
        normalized = value.replace("\\", "/")
        if not normalized.startswith("series/"):
            raise ValueError("series path must live under 'series/'")
        if not normalized.endswith("experiment.yaml"):
            raise ValueError("series path must end with 'experiment.yaml'")
        return value


class ExperimentSeriesRegistry(BaseModel, frozen=True):
    """Workspace-level registry of available experiment series."""

    entries: list[ExperimentSeriesEntry]

    @model_validator(mode="after")
    def _validate_entries(self) -> "ExperimentSeriesRegistry":
        if not self.entries:
            raise ValueError("experiment_series.entries must not be empty")
        ids = [entry.id for entry in self.entries]
        if len(ids) != len(set(ids)):
            raise ValueError("experiment_series entry IDs must be unique")
        paths = [entry.path for entry in self.entries]
        if len(paths) != len(set(paths)):
            raise ValueError("experiment_series entry paths must be unique")
        return self


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
    primary_configs: list[ConfigEntry | str] | None = None
    primary_results: list[ResultEntry] | None = None
    primary_comparisons: list[str] | None = None
    experiment_series: ExperimentSeriesRegistry | None = None
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
    measurement_workflow: MeasurementWorkflowConfig | None = None

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

    @field_validator("experiment_series", mode="before")
    @classmethod
    def _normalize_empty_series_block(cls, value: Any) -> Any:
        if value in ({}, None):
            return None
        return value

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


def result_entry_notes(entry: ResultEntry | dict) -> str | None:
    """Extract optional run notes from a primary_results entry."""
    if isinstance(entry, ResultEntry):
        return entry.run_notes
    notes = entry.get("run_notes")
    return str(notes) if notes is not None else None


def config_entry_path(entry: ConfigEntry | str | dict) -> str:
    """Extract the path string from a primary_configs entry."""
    if isinstance(entry, ConfigEntry):
        return entry.path
    if isinstance(entry, dict):
        return str(entry["path"])
    return str(entry)


def config_entry_role(entry: ConfigEntry | str | dict) -> str | None:
    """Extract the role string from a primary_configs entry if present."""
    if isinstance(entry, ConfigEntry):
        return entry.role
    if isinstance(entry, dict):
        role = entry.get("role")
        return str(role) if role is not None else None
    return None


def series_entry_by_id(
    manifest: WorkspaceManifest,
    series_id: str,
) -> ExperimentSeriesEntry:
    """Return one registered series entry by ID or raise ValueError."""
    registry = manifest.experiment_series
    if registry is None:
        raise ValueError(
            "Workspace manifest does not define an 'experiment_series' registry."
        )
    for entry in registry.entries:
        if entry.id == series_id:
            return entry
    raise ValueError(f"Series '{series_id}' is not registered in workspace.yaml.")
