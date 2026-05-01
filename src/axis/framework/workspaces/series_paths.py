"""Helpers for resolving registered experiment series paths."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from axis.framework.workspaces.types import load_manifest, series_entry_by_id


@dataclass(frozen=True)
class ResolvedSeriesPaths:
    """Resolved canonical paths for one registered series."""

    series_id: str
    series_root: Path
    experiment_manifest_path: Path
    results_root: Path
    measurements_root: Path
    comparisons_root: Path
    notes_path: Path


def resolve_series_paths(
    workspace_path: Path | str,
    *,
    series_id: str,
) -> ResolvedSeriesPaths:
    """Resolve the canonical path set for one registered series."""
    ws = Path(workspace_path)
    manifest = load_manifest(ws)
    entry = series_entry_by_id(manifest, series_id)
    experiment_manifest_path = ws / entry.path
    series_root = experiment_manifest_path.parent
    return ResolvedSeriesPaths(
        series_id=series_id,
        series_root=series_root,
        experiment_manifest_path=experiment_manifest_path,
        results_root=series_root / "results",
        measurements_root=series_root / "measurements",
        comparisons_root=series_root / "comparisons",
        notes_path=series_root / "notes.md",
    )
