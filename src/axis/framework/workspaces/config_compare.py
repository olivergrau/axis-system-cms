"""Compare scaffolded workspace config files by manifest role."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from axis.framework.workspaces.config_changes import diff_current_values
from axis.framework.workspaces.types import (
    WorkspaceType,
    config_entry_path,
    config_entry_role,
    load_manifest,
)


class WorkspaceConfigCompareResult(BaseModel, frozen=True):
    """Result of comparing reference and candidate workspace configs."""

    workspace_path: str
    reference_config: str
    candidate_config: str
    candidate_delta: dict[str, Any]
    reference_values: dict[str, Any]


def compare_workspace_configs(
    workspace_path: Path,
) -> WorkspaceConfigCompareResult:
    """Compare reference and candidate config files in a workspace.

    The command is intentionally limited to ``system_comparison`` workspaces,
    where the reference/candidate roles are meaningful at config time.
    """
    ws = Path(workspace_path)
    manifest = load_manifest(ws)

    if manifest.workspace_type != WorkspaceType.SYSTEM_COMPARISON:
        raise ValueError(
            "compare-configs is only supported for "
            "investigation/system_comparison workspaces. "
            f"Workspace '{manifest.workspace_id}' has type "
            f"'{manifest.workspace_type}'."
        )

    entries = manifest.primary_configs or []
    if len(entries) != 2:
        raise ValueError(
            "compare-configs requires exactly two primary_configs entries "
            "for a system_comparison workspace: one role='reference' and "
            "one role='candidate'."
        )

    by_role: dict[str, str] = {}
    missing_role: list[str] = []
    duplicate_roles: list[str] = []
    for entry in entries:
        path = config_entry_path(entry)
        role = config_entry_role(entry)
        if role is None:
            missing_role.append(path)
            continue
        if role in by_role:
            duplicate_roles.append(role)
            continue
        by_role[role] = path

    if missing_role:
        raise ValueError(
            "compare-configs requires role annotations on primary_configs. "
            "Missing role for: " + ", ".join(missing_role)
        )
    if duplicate_roles:
        raise ValueError(
            "compare-configs found duplicate primary_configs roles: "
            + ", ".join(sorted(set(duplicate_roles)))
        )

    missing_expected = [
        role for role in ("reference", "candidate") if role not in by_role
    ]
    if missing_expected:
        raise ValueError(
            "compare-configs requires primary_configs roles 'reference' and "
            "'candidate'. Missing: " + ", ".join(missing_expected)
        )

    reference_path = by_role["reference"]
    candidate_path = by_role["candidate"]
    reference_config = _load_yaml_dict(ws / reference_path)
    candidate_config = _load_yaml_dict(ws / candidate_path)

    diff = diff_current_values(reference_config, candidate_config)
    candidate_delta = diff if isinstance(diff, dict) else {}
    reference_values = _project_existing_values(reference_config, candidate_delta)

    return WorkspaceConfigCompareResult(
        workspace_path=str(ws),
        reference_config=reference_path,
        candidate_config=candidate_path,
        candidate_delta=candidate_delta,
        reference_values=reference_values,
    )


def _load_yaml_dict(path: Path) -> dict[str, Any]:
    """Load a YAML mapping from *path* with a command-oriented error."""
    import yaml

    if not path.exists():
        raise ValueError(f"Config file does not exist: {path}")

    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"Config file must contain a YAML mapping: {path}")
    return data


def _project_existing_values(
    source: dict[str, Any],
    shape: dict[str, Any],
) -> dict[str, Any]:
    """Return source values for leaves present in the candidate delta shape."""
    projected: dict[str, Any] = {}
    for key, value in shape.items():
        if key not in source:
            continue
        source_value = source[key]
        if isinstance(value, dict):
            if isinstance(source_value, dict):
                child = _project_existing_values(source_value, value)
                if child:
                    projected[key] = child
            continue
        projected[key] = source_value
    return projected
