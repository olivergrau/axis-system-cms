"""Typed model and loader for workspace-local experiment series files."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from axis.framework.workspaces.series_paths import resolve_series_paths
from axis.framework.workspaces.types import WorkspaceType


_FROZEN = ConfigDict(frozen=True)


class ExperimentSeriesExportConfig(BaseModel):
    """Optional export toggles for one experiment series."""

    model_config = _FROZEN

    comparison_summary: bool = True
    candidate_run_summary: bool = True
    reference_run_summary: bool = False


class ExperimentSeriesNotesConfig(BaseModel):
    """Optional notes scaffolding settings for one series."""

    model_config = _FROZEN

    scaffold_notes: bool = True


class ExperimentSeriesLabelsConfig(BaseModel):
    """Optional label generation settings for one series."""

    model_config = _FROZEN

    measurement_label_pattern: str = "{experiment_id}"

    @field_validator("measurement_label_pattern")
    @classmethod
    def _require_experiment_id_placeholder(cls, value: str) -> str:
        if "{experiment_id}" not in value:
            raise ValueError("measurement_label_pattern must include '{experiment_id}'")
        return value


class ExperimentSeriesDefaults(BaseModel):
    """Optional defaults block for a series manifest."""

    model_config = _FROZEN

    export: ExperimentSeriesExportConfig = Field(
        default_factory=ExperimentSeriesExportConfig
    )
    notes: ExperimentSeriesNotesConfig = Field(
        default_factory=ExperimentSeriesNotesConfig
    )
    labels: ExperimentSeriesLabelsConfig = Field(
        default_factory=ExperimentSeriesLabelsConfig
    )


class ExperimentSeriesBaseConfigs(BaseModel):
    """Optional explicit base-config overrides for a series."""

    model_config = _FROZEN

    reference: str | None = None
    candidate: str | None = None
    system_under_test: str | None = None

    @field_validator("reference", "candidate", "system_under_test")
    @classmethod
    def _validate_relative_paths(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not value.strip():
            raise ValueError("base config path must not be empty")
        if value.startswith("/"):
            raise ValueError("base config path must be workspace-relative")
        return value


class ExperimentSeriesExperiment(BaseModel):
    """One declared experiment entry in a series."""

    model_config = _FROZEN

    id: str
    label: str | None = None
    title: str
    enabled: bool = True
    notes: str | None = None
    hypothesis: list[str] | None = None
    reference_config_delta: dict[str, Any] | None = None
    candidate_config_delta: dict[str, Any]

    @field_validator("id", "title")
    @classmethod
    def _require_non_empty_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be empty")
        return value

    @field_validator("label")
    @classmethod
    def _validate_label(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not value.strip():
            raise ValueError("label must not be empty")
        if "/" in value or "\\" in value:
            raise ValueError("label must not contain path separators")
        return value

    @field_validator("candidate_config_delta")
    @classmethod
    def _require_mapping(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict) or not value:
            raise ValueError("candidate_config_delta must be a non-empty mapping")
        return value

    @field_validator("reference_config_delta")
    @classmethod
    def _validate_optional_reference_mapping(
        cls, value: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if value is None:
            return value
        if not isinstance(value, dict) or not value:
            raise ValueError("reference_config_delta must be a non-empty mapping")
        return value


class ExperimentSeriesManifest(BaseModel):
    """Workspace-local declaration of an experiment series."""

    model_config = _FROZEN

    version: int
    workflow_type: Literal["experiment_series"]
    workspace_type: WorkspaceType | str
    title: str | None = None
    description: str | None = None
    base_configs: ExperimentSeriesBaseConfigs | None = None
    defaults: ExperimentSeriesDefaults = Field(default_factory=ExperimentSeriesDefaults)
    experiments: list[ExperimentSeriesExperiment]

    @field_validator("version")
    @classmethod
    def _validate_version(cls, value: int) -> int:
        if value != 1:
            raise ValueError("only experiment series version 1 is supported")
        return value

    @model_validator(mode="after")
    def _validate_experiments(self) -> "ExperimentSeriesManifest":
        if not self.experiments:
            raise ValueError("experiments must not be empty")

        ids = [experiment.id for experiment in self.experiments]
        if len(ids) != len(set(ids)):
            raise ValueError("experiment IDs must be unique")

        if not any(experiment.enabled for experiment in self.experiments):
            raise ValueError("at least one experiment must be enabled")

        return self


def load_experiment_series(
    workspace_path: Path | str,
    *,
    series_id: str,
) -> ExperimentSeriesManifest:
    """Load and validate one registered series manifest."""
    series_path = resolve_series_paths(
        workspace_path,
        series_id=series_id,
    ).experiment_manifest_path
    if not series_path.is_file():
        raise ValueError(
            f"Experiment series file not found: {series_path}. "
            "Create the registered series manifest first."
        )

    data = yaml.safe_load(series_path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"Experiment series file must contain a YAML mapping: {series_path}")
    return ExperimentSeriesManifest.model_validate(data)
