"""Workspace structural and semantic validation (WP-02)."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel

from axis.framework.workspaces.types import (
    WorkspaceClass,
    WorkspaceManifest,
    load_manifest,
)


class WorkspaceCheckSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class WorkspaceCheckIssue(BaseModel, frozen=True):
    severity: WorkspaceCheckSeverity
    message: str
    path: str | None = None


class WorkspaceCheckResult(BaseModel, frozen=True):
    workspace_path: str
    issues: list[WorkspaceCheckIssue] = []

    @property
    def is_valid(self) -> bool:
        return not any(
            i.severity == WorkspaceCheckSeverity.ERROR for i in self.issues
        )


# Required top-level items (files and directories) per spec Section 12.
_REQUIRED_FILES = ("README.md", "notes.md")
_REQUIRED_DIRS = ("configs", "results", "comparisons",
                  "measurements", "exports")


def check_workspace(workspace_path: Path) -> WorkspaceCheckResult:
    """Validate an Experiment Workspace against the v1 specification.

    Returns a result containing errors, warnings, and informational
    messages. The workspace is considered valid when no errors are
    present.
    """
    from axis.framework.workspaces.handler import get_handler

    issues: list[WorkspaceCheckIssue] = []
    ws = Path(workspace_path)

    # --- workspace.yaml must exist ---
    manifest_path = ws / "workspace.yaml"
    if not manifest_path.exists():
        issues.append(WorkspaceCheckIssue(
            severity=WorkspaceCheckSeverity.ERROR,
            message="workspace.yaml not found",
            path=str(manifest_path),
        ))
        return WorkspaceCheckResult(
            workspace_path=str(ws), issues=issues,
        )

    # --- Parse manifest ---
    manifest: WorkspaceManifest | None = None
    try:
        manifest = load_manifest(ws)
    except Exception as exc:
        issues.append(WorkspaceCheckIssue(
            severity=WorkspaceCheckSeverity.ERROR,
            message=f"Failed to parse workspace.yaml: {exc}",
            path=str(manifest_path),
        ))
        return WorkspaceCheckResult(
            workspace_path=str(ws), issues=issues,
        )

    # --- Required files ---
    for fname in _REQUIRED_FILES:
        if not (ws / fname).exists():
            issues.append(WorkspaceCheckIssue(
                severity=WorkspaceCheckSeverity.ERROR,
                message=f"Required file missing: {fname}",
                path=str(ws / fname),
            ))

    # --- Required directories ---
    for dname in _REQUIRED_DIRS:
        if not (ws / dname).is_dir():
            issues.append(WorkspaceCheckIssue(
                severity=WorkspaceCheckSeverity.ERROR,
                message=f"Required directory missing: {dname}/",
                path=str(ws / dname),
            ))

    # --- Type-specific validation (delegated to handler) ---
    handler = get_handler(manifest.workspace_type)
    issues.extend(handler.validate(ws, manifest))

    # --- Configs check (generic: at least one config expected) ---
    configs_dir = ws / "configs"
    if configs_dir.is_dir():
        yaml_files = list(configs_dir.glob("*.yaml")) + \
            list(configs_dir.glob("*.yml"))
        if not yaml_files:
            issues.append(WorkspaceCheckIssue(
                severity=WorkspaceCheckSeverity.WARNING,
                message="No config files found in configs/",
                path=str(configs_dir),
            ))

    # --- Declared primary artifact paths ---
    _check_declared_paths(ws, manifest.primary_configs,
                          "primary_configs", issues)
    _check_declared_paths(ws, manifest.primary_results,
                          "primary_results", issues)
    _check_declared_paths(ws, manifest.primary_comparisons,
                          "primary_comparisons", issues)
    _check_declared_paths(ws, manifest.primary_measurements,
                          "primary_measurements", issues)

    # --- Config experiment_type guardrail ---
    issues.extend(check_config_experiment_types(
        ws, manifest.primary_configs,
        workspace_type=manifest.workspace_type.value,
    ))

    # --- Warnings for empty investigation dirs ---
    if manifest.workspace_class == WorkspaceClass.INVESTIGATION:
        for dname in ("comparisons", "measurements"):
            d = ws / dname
            if d.is_dir() and not any(d.iterdir()):
                issues.append(WorkspaceCheckIssue(
                    severity=WorkspaceCheckSeverity.INFO,
                    message=f"{dname}/ is empty",
                    path=str(d),
                ))

    return WorkspaceCheckResult(workspace_path=str(ws), issues=issues)


def _check_declared_paths(
    ws: Path,
    paths: list | None,
    field_name: str,
    issues: list[WorkspaceCheckIssue],
) -> None:
    if not paths:
        return
    from axis.framework.workspaces.types import result_entry_path
    for entry in paths:
        p = result_entry_path(entry) if field_name == "primary_results" else entry
        full = ws / p
        if not full.exists():
            issues.append(WorkspaceCheckIssue(
                severity=WorkspaceCheckSeverity.WARNING,
                message=f"Declared {field_name} path does not exist: {p}",
                path=str(full),
            ))


def check_config_experiment_types(
    ws: Path,
    config_paths: list[str] | None,
    workspace_type: str | None = None,
) -> list[WorkspaceCheckIssue]:
    """Validate experiment types in workspace configs.

    For ``single_system`` workspaces both ``single_run`` and ``ofat``
    are allowed.  All other workspace types require ``single_run``.

    Returns a list of ERROR-level issues for invalid configs.
    """
    import yaml

    if not config_paths:
        return []

    allowed: set[str] = {"single_run"}
    if workspace_type == "single_system":
        allowed.add("ofat")

    issues: list[WorkspaceCheckIssue] = []
    for rel_path in config_paths:
        config_file = ws / rel_path
        if not config_file.exists():
            continue  # missing file is reported elsewhere
        try:
            data = yaml.safe_load(config_file.read_text())
        except Exception:
            continue  # parse errors are not our concern here
        if not isinstance(data, dict):
            continue
        experiment_type = data.get("experiment_type", "single_run")
        if experiment_type not in allowed:
            if experiment_type == "ofat" and workspace_type != "single_system":
                msg = (
                    f"Config '{rel_path}' uses experiment_type='ofat'. "
                    f"OFAT is only supported in 'single_system' workspaces, "
                    f"not in '{workspace_type}'."
                )
            else:
                msg = (
                    f"Config '{rel_path}' uses experiment_type='{experiment_type}'. "
                    f"Workspace mode supports only: {sorted(allowed)}."
                )
            issues.append(WorkspaceCheckIssue(
                severity=WorkspaceCheckSeverity.ERROR,
                message=msg,
                path=str(config_file),
            ))
        elif experiment_type == "ofat":
            # Validate OFAT-specific fields.
            pp = data.get("parameter_path")
            pv = data.get("parameter_values")
            if not pp:
                issues.append(WorkspaceCheckIssue(
                    severity=WorkspaceCheckSeverity.ERROR,
                    message=(
                        f"Config '{rel_path}' is OFAT but missing "
                        f"'parameter_path'."
                    ),
                    path=str(config_file),
                ))
            if not pv or not isinstance(pv, list) or len(pv) == 0:
                issues.append(WorkspaceCheckIssue(
                    severity=WorkspaceCheckSeverity.ERROR,
                    message=(
                        f"Config '{rel_path}' is OFAT but "
                        f"'parameter_values' is missing or empty."
                    ),
                    path=str(config_file),
                ))
    return issues
