"""Workspace inspection service — read-only queries about workspaces."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any


class WorkspaceInspectionService:
    """Provides read-only workspace queries (show, check, sweep-result).

    Dependencies are injected via the constructor so that the
    composition root (``build_context``) controls wiring.
    """

    def __init__(
        self,
        summarize_fn: Callable[..., Any],
        check_fn: Callable[..., Any],
        drift_fn: Callable[..., Any],
        sweep_result_fn: Callable[..., Any],
        run_summary_target_fn: Callable[..., Any],
    ) -> None:
        self._summarize_fn = summarize_fn
        self._check_fn = check_fn
        self._drift_fn = drift_fn
        self._sweep_result_fn = sweep_result_fn
        self._run_summary_target_fn = run_summary_target_fn

    def summarize(self, workspace_path: Path):
        """Return a ``WorkspaceSummary`` for the workspace."""
        return self._summarize_fn(workspace_path)

    def check(self, workspace_path: Path):
        """Return validation result and drift issues."""
        ws = Path(workspace_path)
        result = self._check_fn(ws)
        drift_issues = self._drift_fn(ws)
        return result, drift_issues

    def sweep_result(
        self,
        workspace_path: Path,
        experiment: str | None = None,
    ) -> dict[str, Any]:
        """Resolve and return sweep result data."""
        return self._sweep_result_fn(workspace_path, experiment=experiment)

    def run_summary_target(
        self,
        workspace_path: Path,
        *,
        role: str | None = None,
        experiment: str | None = None,
        run: str | None = None,
    ):
        """Resolve and return one concrete run target for workspace inspection."""
        return self._run_summary_target_fn(
            workspace_path,
            role=role,
            experiment=experiment,
            run=run,
        )
