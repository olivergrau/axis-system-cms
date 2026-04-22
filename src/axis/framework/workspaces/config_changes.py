"""Helpers for comparing workspace result configs across iterations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_NO_CHANGE = object()


def entry_role(entry: object) -> str | None:
    """Return a result entry role from a manifest item."""
    if isinstance(entry, dict):
        role = entry.get("role")
        return str(role) if role is not None else None
    role = getattr(entry, "role", None)
    return str(role) if role is not None else None


def entry_config_path(entry: object) -> str | None:
    """Return a result entry config path from a manifest item."""
    if isinstance(entry, dict):
        config = entry.get("config")
        return str(config) if config is not None else None
    config = getattr(entry, "config", None)
    return str(config) if config is not None else None


def find_previous_comparable_entry(
    entries: list[object], role: str | None,
) -> dict | None:
    """Return the previous result entry to compare against.

    If a role is available, prefer the most recent prior entry with the same
    role so comparison/development workspaces don't compare across roles.
    If no role is available, fall back to the immediately previous structured
    result entry.
    """
    if role is not None:
        for entry in reversed(entries):
            if entry_role(entry) == role:
                return entry
        return None

    for entry in reversed(entries):
        if entry_config_path(entry) is not None:
            return entry
    return None


def load_json_dict(path: Path) -> dict[str, Any] | None:
    """Load a JSON dict from disk, returning None on failure."""
    try:
        data = json.loads(path.read_text())
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def diff_current_values(previous: object, current: object) -> object:
    """Return only the current values that changed from *previous*.

    Removed keys are intentionally omitted. This keeps the diff compact and
    focused on what the current run changed.
    """
    if isinstance(previous, dict) and isinstance(current, dict):
        changed: dict[str, object] = {}
        for key, value in current.items():
            if key not in previous:
                changed[key] = value
                continue
            child = diff_current_values(previous[key], value)
            if child is not _NO_CHANGE:
                changed[key] = child
        return changed if changed else _NO_CHANGE

    return current if previous != current else _NO_CHANGE


def compute_config_changes(
    workspace_path: Path,
    existing_results: list[object],
    experiment_id: str,
    role: str | None,
) -> dict[str, Any] | None:
    """Compute config changes relative to the previous comparable result."""
    current_path = workspace_path / "results" / experiment_id / "experiment_config.json"
    current_config = load_json_dict(current_path)
    if current_config is None:
        return None

    previous_entry = find_previous_comparable_entry(existing_results, role)
    if previous_entry is None:
        return None

    previous_config_path = entry_config_path(previous_entry)
    if previous_config_path is None:
        return None

    previous_config = load_json_dict(workspace_path / previous_config_path)
    if previous_config is None:
        return None

    diff = diff_current_values(previous_config, current_config)
    return diff if isinstance(diff, dict) else None


def has_same_config_as_previous_result(
    workspace_path: Path,
    current_config: dict[str, Any],
    manifest_results: list[object],
    role: str | None,
    *,
    ignore_world: bool = False,
) -> bool:
    """Return True if *current_config* matches the previous comparable result."""
    previous_entry = find_previous_comparable_entry(manifest_results, role)
    if previous_entry is None:
        return False

    previous_config_path = entry_config_path(previous_entry)
    if previous_config_path is None:
        return False

    previous_config = load_json_dict(workspace_path / previous_config_path)
    if previous_config is None:
        return False

    if ignore_world:
        current_config = {
            key: value for key, value in current_config.items() if key != "world"
        }
        previous_config = {
            key: value for key, value in previous_config.items() if key != "world"
        }

    return previous_config == current_config
