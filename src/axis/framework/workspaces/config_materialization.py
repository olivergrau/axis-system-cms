"""Temporary config materialization helpers for experiment series execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from axis.framework.workspaces.types import config_entry_path, config_entry_role


@dataclass(frozen=True)
class MaterializedExperimentConfig:
    """Resolved temporary config for one experiment role."""

    role: str
    source_config_path: str
    temp_config_path: str
    resolved_config: dict[str, Any]


def resolve_base_config_paths(
    workspace_path: Path,
    manifest,
) -> dict[str, str]:
    """Return workspace-relative base config paths by role."""
    entries = manifest.primary_configs or []
    by_role: dict[str, str] = {}
    for entry in entries:
        role = config_entry_role(entry)
        if role is None:
            continue
        by_role[role] = config_entry_path(entry)

    workspace_type = getattr(manifest.workspace_type, "value", str(manifest.workspace_type))
    if workspace_type == "system_comparison":
        required = {"reference", "candidate"}
        missing = sorted(required - set(by_role))
        if missing:
            raise ValueError(
                "Experiment series requires primary_configs roles 'reference' and "
                "'candidate'. Missing: " + ", ".join(missing)
            )
    elif workspace_type == "single_system":
        if "system_under_test" not in by_role:
            entries = manifest.primary_configs or []
            if len(entries) == 1:
                by_role["system_under_test"] = config_entry_path(entries[0])
            else:
                raise ValueError(
                    "Experiment series for single_system requires one primary config "
                    "or an explicit role='system_under_test'."
                )
    return by_role


def materialize_candidate_config(
    workspace_path: Path,
    *,
    source_config_path: str,
    candidate_config_delta: dict[str, Any],
    temp_dir: Path,
    experiment_id: str,
) -> MaterializedExperimentConfig:
    """Create a temporary candidate config for one series experiment."""
    ws = Path(workspace_path)
    source_path = ws / source_config_path
    if not source_path.is_file():
        raise ValueError(f"Config file does not exist: {source_path}")

    loaded = yaml.safe_load(source_path.read_text())
    if not isinstance(loaded, dict):
        raise ValueError(f"Config file must contain a YAML mapping: {source_path}")

    merged = deep_merge_dicts(loaded, candidate_config_delta)
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / f"{experiment_id}-candidate.yaml"
    temp_path.write_text(
        yaml.dump(merged, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    return MaterializedExperimentConfig(
        role="candidate",
        source_config_path=source_config_path,
        temp_config_path=str(temp_path),
        resolved_config=merged,
    )


def materialize_role_config(
    workspace_path: Path,
    *,
    role: str,
    source_config_path: str,
    config_delta: dict[str, Any],
    temp_dir: Path,
    experiment_id: str,
) -> MaterializedExperimentConfig:
    """Create one temporary config for an arbitrary workspace role."""
    ws = Path(workspace_path)
    source_path = ws / source_config_path
    if not source_path.is_file():
        raise ValueError(f"Config file does not exist: {source_path}")

    loaded = yaml.safe_load(source_path.read_text())
    if not isinstance(loaded, dict):
        raise ValueError(f"Config file must contain a YAML mapping: {source_path}")

    merged = deep_merge_dicts(loaded, config_delta)
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / f"{experiment_id}-{role}.yaml"
    temp_path.write_text(
        yaml.dump(merged, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    return MaterializedExperimentConfig(
        role=role,
        source_config_path=source_config_path,
        temp_config_path=str(temp_path),
        resolved_config=merged,
    )


def deep_merge_dicts(
    base: dict[str, Any],
    patch: dict[str, Any],
) -> dict[str, Any]:
    """Return a deep-merged copy of *base* with values from *patch*."""
    merged: dict[str, Any] = {}
    for key, value in base.items():
        if isinstance(value, dict):
            merged[key] = deep_merge_dicts(value, {})
        elif isinstance(value, list):
            merged[key] = list(value)
        else:
            merged[key] = value

    for key, value in patch.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = deep_merge_dicts(merged[key], value)
            continue
        if isinstance(value, dict):
            merged[key] = deep_merge_dicts({}, value)
            continue
        if isinstance(value, list):
            merged[key] = list(value)
            continue
        merged[key] = value
    return merged
