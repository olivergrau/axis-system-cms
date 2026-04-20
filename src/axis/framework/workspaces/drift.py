"""Drift detection for workspace consistency (WP-11)."""

from __future__ import annotations

from pathlib import Path

from axis.framework.workspaces.types import WorkspaceType, load_manifest, result_entry_path
from axis.framework.workspaces.validation import (
    WorkspaceCheckIssue,
    WorkspaceCheckSeverity,
)


def detect_drift(workspace_path: Path) -> list[WorkspaceCheckIssue]:
    """Detect drift between manifest declarations and actual workspace state.

    Checks for:
    - Declared primary artifacts that no longer exist on disk.
    - Undeclared files in results/ or comparisons/ that look like
      primary artifacts.
    - Incomplete comparison roles (reference without candidate or vice versa).

    Parameters
    ----------
    workspace_path:
        Path to the workspace root.

    Returns
    -------
    List of drift-related issues (warnings or errors).
    """
    ws = Path(workspace_path)
    issues: list[WorkspaceCheckIssue] = []

    try:
        manifest = load_manifest(ws)
    except Exception:
        return issues  # Can't detect drift without a valid manifest.

    # --- Missing declared artifacts ---
    for field_name, paths in [
        ("primary_configs", manifest.primary_configs),
        ("primary_results", manifest.primary_results),
        ("primary_comparisons", manifest.primary_comparisons),
        ("primary_measurements", manifest.primary_measurements),
    ]:
        if not paths:
            continue
        for entry in paths:
            p = result_entry_path(entry) if field_name == "primary_results" else entry
            if not (ws / p).exists():
                issues.append(WorkspaceCheckIssue(
                    severity=WorkspaceCheckSeverity.ERROR,
                    message=f"Declared {field_name} artifact missing: {p}",
                    path=str(ws / p),
                ))

    # --- Undeclared files in results/ and comparisons/ ---
    declared_results = {result_entry_path(e) for e in (manifest.primary_results or [])}
    declared_comparisons = set(manifest.primary_comparisons or [])

    # Build a set of "covered" directory prefixes: declared paths plus
    # their parent experiment directories.  Files anywhere under a
    # covered prefix are expected and should not trigger warnings.
    def _covered_prefixes(declared: set[str]) -> set[str]:
        prefixes = set()
        for dp in declared:
            prefixes.add(dp + "/")
            # For experiment-root paths like "results/<eid>", cover
            # the entire experiment directory.
            # Also handle legacy run paths like "results/<eid>/runs/<rid>".
            parts = dp.split("/")
            if len(parts) >= 2:
                prefixes.add("/".join(parts[:2]) + "/")
        return prefixes

    for subdir, declared in [
        ("results", declared_results),
        ("comparisons", declared_comparisons),
    ]:
        d = ws / subdir
        if not d.is_dir():
            continue
        prefixes = _covered_prefixes(declared)
        for f in d.rglob("*"):
            if not f.is_file():
                continue
            rel = str(f.relative_to(ws))
            if rel in declared:
                continue
            if any(rel.startswith(p) for p in prefixes):
                continue
            issues.append(WorkspaceCheckIssue(
                severity=WorkspaceCheckSeverity.WARNING,
                message=f"Undeclared artifact in {subdir}/: {rel}",
                path=str(f),
            ))

    # --- Comparison role completeness ---
    if manifest.workspace_type == WorkspaceType.SYSTEM_COMPARISON:
        configs_dir = ws / "configs"
        if configs_dir.is_dir():
            config_names = [p.name for p in configs_dir.glob("*.yaml")]
            has_ref = any("reference" in n for n in config_names)
            has_cand = any("candidate" in n for n in config_names)
            if has_ref and not has_cand:
                issues.append(WorkspaceCheckIssue(
                    severity=WorkspaceCheckSeverity.WARNING,
                    message="Reference config found but no candidate config",
                    path=str(configs_dir),
                ))
            elif has_cand and not has_ref:
                issues.append(WorkspaceCheckIssue(
                    severity=WorkspaceCheckSeverity.WARNING,
                    message="Candidate config found but no reference config",
                    path=str(configs_dir),
                ))

    return issues
