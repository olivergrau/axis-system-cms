"""Manifest synchronization – comment-preserving updates (WP-10).

After workspace-aware run or compare, updates ``workspace.yaml`` so
that ``primary_results`` and ``primary_comparisons`` reflect the
actual artifacts produced inside the workspace.

Semantic mutations are delegated to ``manifest_mutator``; this module
handles only YAML roundtrip IO coordination.
"""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from axis.framework.workspaces.config_changes import compute_config_changes


def _load_yaml_roundtrip(manifest_path: Path) -> tuple[YAML, dict]:
    """Load workspace.yaml preserving comments and ordering."""
    yaml = YAML()
    yaml.preserve_quotes = True
    data = yaml.load(manifest_path)
    return yaml, data


def _save_yaml_roundtrip(
    manifest_path: Path, yaml: YAML, data: dict,
) -> None:
    """Write workspace.yaml preserving comments and ordering."""
    yaml.dump(data, manifest_path)


def sync_manifest_after_run(
    workspace_path: Path,
    experiment_id: str,
    run_ids: list[str],
    role: str | None = None,
    config_path: str | None = None,
    output_form: str | None = None,
    trace_mode: str | None = None,
    system_type: str | None = None,
    primary_run_id: str | None = None,
    baseline_run_id: str | None = None,
) -> None:
    """Update workspace.yaml after an execution run.

    Records experiment-root result entries (``results/<experiment-id>``)
    with output semantics rather than run-level paths.

    Parameters
    ----------
    workspace_path:
        Path to the workspace root.
    experiment_id:
        ID of the completed experiment.
    run_ids:
        IDs of the completed runs within that experiment.
    role:
        Optional role label (reference, candidate, etc.).
    config_path:
        Optional workspace-relative config path that produced this run.
    output_form:
        Output form of the experiment ("point" or "sweep").
    system_type:
        System type of the experiment.
    trace_mode:
        Trace mode of the experiment ("full" or "light").
    primary_run_id:
        Primary run ID for point outputs.
    baseline_run_id:
        Baseline run ID for sweep outputs.
    """
    from axis.framework.workspaces.manifest_mutator import (
        append_primary_result,
        update_development_results,
    )

    ws = Path(workspace_path)
    manifest_path = ws / "workspace.yaml"
    yaml, data = _load_yaml_roundtrip(manifest_path)
    existing_results = list(data.get("primary_results") or [])
    config_changes = compute_config_changes(
        ws, existing_results, experiment_id, role,
    )

    append_primary_result(
        data, experiment_id,
        role=role,
        config_path=config_path,
        output_form=output_form,
        trace_mode=trace_mode,
        system_type=system_type,
        primary_run_id=primary_run_id,
        baseline_run_id=baseline_run_id,
        config_changes=config_changes,
    )
    update_development_results(data, experiment_id, role=role)

    _save_yaml_roundtrip(manifest_path, yaml, data)


def sync_manifest_after_compare(
    workspace_path: Path,
    comparison_output_path: str,
) -> None:
    """Update workspace.yaml after a comparison.

    Appends to ``primary_comparisons`` with the workspace-relative
    path to the produced comparison output file.

    Parameters
    ----------
    workspace_path:
        Path to the workspace root.
    comparison_output_path:
        Workspace-relative path to the comparison output file
        (must already exist under the workspace).
    """
    from axis.framework.workspaces.manifest_mutator import (
        append_primary_comparison,
        update_current_validation_comparison,
    )

    ws = Path(workspace_path)
    manifest_path = ws / "workspace.yaml"
    yaml, data = _load_yaml_roundtrip(manifest_path)

    append_primary_comparison(data, comparison_output_path)
    update_current_validation_comparison(data, comparison_output_path)

    _save_yaml_roundtrip(manifest_path, yaml, data)
