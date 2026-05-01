"""Typed manifest mutation operations.

Operates on ruamel.yaml roundtrip data structures (dicts) so that
YAML comments and formatting are preserved.  Each method encapsulates
a single business-level mutation rather than ad-hoc dictionary edits.
"""

from __future__ import annotations

from datetime import datetime, timezone


def _ensure_list(data: dict, key: str) -> list:
    """Ensure *key* exists in *data* as a list, creating it if needed."""
    if key not in data or data[key] is None:
        data[key] = []
    return data[key]


def _result_paths(entries: list) -> set[str]:
    """Extract path strings from result entries (str or dict)."""
    paths: set[str] = set()
    for e in entries:
        if isinstance(e, str):
            paths.add(e)
        elif isinstance(e, dict) and "path" in e:
            paths.add(e["path"])
    return paths


def _config_path(entry: object) -> str:
    """Extract a config path from either a plain or structured entry."""
    if isinstance(entry, dict):
        return str(entry["path"])
    return str(entry)


def _ensure_dict(data: dict, key: str) -> dict:
    """Ensure *key* exists in *data* as a dict, creating it if needed."""
    if key not in data or data[key] is None:
        data[key] = {}
    return data[key]


def _ensure_series_generated(data: dict, series_id: str) -> dict:
    """Return the generated-artifacts dict for one registered series."""
    registry = _ensure_dict(data, "experiment_series")
    entries = _ensure_list(registry, "entries")
    for entry in entries:
        if isinstance(entry, dict) and entry.get("id") == series_id:
            return _ensure_dict(entry, "generated")
    raise ValueError(f"Series '{series_id}' is not registered in workspace.yaml")


# -----------------------------------------------------------------------
# Primary result mutations
# -----------------------------------------------------------------------


def append_primary_result(
    data: dict,
    experiment_id: str,
    role: str | None = None,
    config_path: str | None = None,
    output_form: str | None = None,
    trace_mode: str | None = None,
    system_type: str | None = None,
    primary_run_id: str | None = None,
    baseline_run_id: str | None = None,
    run_notes: str | None = None,
    config_changes: dict | None = None,
) -> None:
    """Append an experiment-root result entry to ``primary_results``.

    Idempotent — skips if the result path already exists.
    """
    results = _ensure_list(data, "primary_results")
    existing = _result_paths(results)

    result_path = f"results/{experiment_id}"
    if result_path in existing:
        return

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    entry: dict = {
        "path": result_path,
        "timestamp": now,
        "config": f"{result_path}/experiment_config.json",
    }
    if role:
        entry["role"] = role
    if output_form:
        entry["output_form"] = output_form
    if trace_mode:
        entry["trace_mode"] = trace_mode
    if system_type:
        entry["system_type"] = system_type
    if primary_run_id:
        entry["primary_run_id"] = primary_run_id
    if baseline_run_id:
        entry["baseline_run_id"] = baseline_run_id
    if run_notes:
        entry["run_notes"] = run_notes
    if config_changes:
        entry["config_changes"] = config_changes

    results.append(entry)


# -----------------------------------------------------------------------
# Development-state mutations
# -----------------------------------------------------------------------


def update_development_results(
    data: dict,
    experiment_id: str,
    role: str | None = None,
) -> None:
    """Update baseline/candidate result lists for development workspaces.

    Only applies when ``workspace_type`` is ``system_development``.
    """
    if data.get("workspace_type") not in ("system_development",):
        return

    entry_path = f"results/{experiment_id}"

    if role == "baseline":
        baselines = _ensure_list(data, "baseline_results")
        if entry_path not in baselines:
            baselines.append(entry_path)
    elif role == "candidate":
        candidates = _ensure_list(data, "candidate_results")
        if entry_path not in candidates:
            candidates.append(entry_path)
        data["current_candidate_result"] = entry_path


# -----------------------------------------------------------------------
# Comparison mutations
# -----------------------------------------------------------------------


def append_primary_comparison(
    data: dict,
    comparison_output_path: str,
) -> None:
    """Append a comparison path to ``primary_comparisons``.

    Idempotent — skips if the path already exists.
    """
    comparisons = _ensure_list(data, "primary_comparisons")
    if comparison_output_path not in comparisons:
        comparisons.append(comparison_output_path)


def append_series_result(
    data: dict,
    *,
    series_id: str,
    result_path: str,
    role: str | None = None,
    output_form: str | None = None,
    trace_mode: str | None = None,
    system_type: str | None = None,
    primary_run_id: str | None = None,
    baseline_run_id: str | None = None,
    run_notes: str | None = None,
    config_changes: dict | None = None,
) -> None:
    """Append one structured result entry under one registered series."""
    generated = _ensure_series_generated(data, series_id)
    results = _ensure_list(generated, "results")
    existing = _result_paths(results)
    if result_path in existing:
        return
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    entry: dict = {
        "path": result_path,
        "timestamp": now,
        "config": f"{result_path}/experiment_config.json",
    }
    if role:
        entry["role"] = role
    if output_form:
        entry["output_form"] = output_form
    if trace_mode:
        entry["trace_mode"] = trace_mode
    if system_type:
        entry["system_type"] = system_type
    if primary_run_id:
        entry["primary_run_id"] = primary_run_id
    if baseline_run_id:
        entry["baseline_run_id"] = baseline_run_id
    if run_notes:
        entry["run_notes"] = run_notes
    if config_changes:
        entry["config_changes"] = config_changes
    results.append(entry)


def append_series_comparison(
    data: dict,
    *,
    series_id: str,
    comparison_output_path: str,
) -> None:
    """Append one comparison path under one registered series."""
    generated = _ensure_series_generated(data, series_id)
    comparisons = _ensure_list(generated, "comparisons")
    if comparison_output_path not in comparisons:
        comparisons.append(comparison_output_path)


def append_series_measurement_run(
    data: dict,
    *,
    series_id: str,
    measurement_path: str,
    label: str | None = None,
) -> None:
    """Append one measurement directory entry under one registered series."""
    generated = _ensure_series_generated(data, series_id)
    runs = _ensure_list(generated, "measurement_runs")
    existing_paths = {
        item["path"] for item in runs
        if isinstance(item, dict) and "path" in item
    }
    if measurement_path in existing_paths:
        return
    entry = {
        "path": measurement_path,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
    }
    if label:
        entry["label"] = label
    runs.append(entry)


def update_current_validation_comparison(
    data: dict,
    comparison_output_path: str,
) -> None:
    """Set ``current_validation_comparison`` for development workspaces."""
    if data.get("workspace_type") in ("system_development",):
        data["current_validation_comparison"] = comparison_output_path


# -----------------------------------------------------------------------
# Candidate config mutations
# -----------------------------------------------------------------------


def set_candidate_config(
    data: dict,
    config_path: str,
) -> None:
    """Set the candidate config for a development workspace.

    Validates workspace type, sets ``candidate_config``, and ensures
    the config path is in ``primary_configs``.

    Raises ``ValueError`` if the workspace type is not development.
    """
    wtype = data.get("workspace_type", "")
    if wtype not in ("system_development",):
        raise ValueError(
            f"set-candidate is only valid for development workspaces, "
            f"not '{wtype}'"
        )

    data["candidate_config"] = config_path

    primary_configs = _ensure_list(data, "primary_configs")
    if config_path not in {_config_path(entry) for entry in primary_configs}:
        primary_configs.append({"path": config_path, "role": "candidate"})


def close_workspace(data: dict) -> None:
    """Close a workspace by setting its final workflow state."""
    if data.get("status") == "closed":
        raise ValueError("Workspace is already closed.")

    data["status"] = "closed"
    data["lifecycle_stage"] = "final"


def reset_workspace_artifacts(data: dict) -> None:
    """Clear manifest fields that track generated workspace artifacts.

    This resets the workspace to a clean execution state without touching
    identity, purpose, configs, notes, or other authored metadata.
    """
    data["primary_results"] = []
    data["primary_comparisons"] = []
    series_registry = data.get("experiment_series")
    if isinstance(series_registry, dict):
        for entry in series_registry.get("entries") or []:
            if not isinstance(entry, dict):
                continue
            entry.pop("generated", None)

    if data.get("workspace_type") in ("system_development",):
        data["baseline_results"] = []
        data["candidate_results"] = []
        data["current_candidate_result"] = None
        data["current_validation_comparison"] = None


# -----------------------------------------------------------------------
# Scaffold mutations
# -----------------------------------------------------------------------


def set_primary_configs(data: dict, config_paths: list[object]) -> None:
    """Set ``primary_configs`` to the given path or structured entries."""
    data["primary_configs"] = list(config_paths)


def merge_scaffold_fields(data: dict, fields: dict) -> None:
    """Merge handler-provided scaffold fields into the manifest data.

    Used during initial workspace scaffolding to add type-specific
    fields (e.g. ``baseline_config``, ``development_state``).
    """
    data.update(fields)
