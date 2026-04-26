"""Workspace compare service — orchestrates comparison + manifest sync."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CompareServiceResult:
    """Summary of a workspace comparison."""

    comparison_number: int
    output_path: str


class WorkspaceCompareService:
    """Coordinates workspace comparison and post-compare manifest sync.

    Dependencies are injected via the constructor so that the
    composition root (``build_context``) controls wiring.
    """

    def __init__(
        self,
        compare_fn: Callable[..., Any],
        sync_fn: Callable[..., None],
    ) -> None:
        self._compare_fn = compare_fn
        self._sync_fn = sync_fn

    def compare(
        self,
        workspace_path: Path,
        reference_experiment: str | None = None,
        candidate_experiment: str | None = None,
        *,
        allow_world_changes: bool = False,
        extension_catalog: object | None = None,
        progress: object | None = None,
    ) -> CompareServiceResult:
        """Run a comparison and sync the manifest.

        Returns summary information about the produced comparison.
        """
        from axis.framework.workspaces.types import load_manifest

        ws = Path(workspace_path)
        manifest = load_manifest(ws)
        if manifest.status.value == "closed":
            raise ValueError(
                "Workspace is closed; no further comparisons are allowed."
            )
        compare_kwargs = {"allow_world_changes": allow_world_changes}
        if extension_catalog is not None:
            compare_kwargs["extension_catalog"] = extension_catalog
        if progress is not None:
            compare_kwargs["progress"] = progress
        envelope, ws_relative_path = self._compare_fn(
            ws,
            reference_experiment,
            candidate_experiment,
            **compare_kwargs,
        )
        self._sync_fn(ws, ws_relative_path)

        return CompareServiceResult(
            comparison_number=envelope.comparison_number,
            output_path=ws_relative_path,
        )
