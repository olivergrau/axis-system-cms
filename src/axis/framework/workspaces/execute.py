"""Workspace-aware execution routing (WP-06).

Executes workspace configs using the standard ExperimentExecutor but
with a repository rooted at ``<workspace>/results/``, so artifacts
are written inside the workspace (workspace-owned mode).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from axis.framework.workspaces.resolution import (
    WorkspaceExecutionPlan,
    resolve_run_targets,
)

if TYPE_CHECKING:
    from axis.framework.experiment import ExperimentResult


class WorkspaceExecutionResult:
    """Pairs an ExperimentResult with the target that produced it."""

    __slots__ = ("experiment_result", "role", "config_path")

    def __init__(
        self,
        experiment_result: "ExperimentResult",
        role: str,
        config_path: str,
    ) -> None:
        self.experiment_result = experiment_result
        self.role = role
        self.config_path = config_path


def execute_workspace(
    workspace_path: Path,
    run_filter: str | None = None,
    *,
    config_overrides_by_role: dict[str, str] | None = None,
    progress: object | None = None,
    progress_description_prefix: str | None = None,
    show_workspace_progress: bool = True,
    results_root: Path | None = None,
) -> list[WorkspaceExecutionResult]:
    """Execute all run targets in a workspace (workspace-owned mode).

    Creates an ``ExperimentRepository`` rooted at
    ``<workspace_path>/results/`` so that all execution artifacts are
    written directly inside the workspace.

    Parameters
    ----------
    workspace_path:
        Path to the workspace root directory.

    Returns
    -------
    List of WorkspaceExecutionResult, one per target executed.
    """
    from axis.framework.experiment import ExperimentExecutor
    from axis.framework.persistence import ExperimentRepository
    from axis.framework.cli import _load_config_file
    from axis.framework.workspaces.validation import check_config_experiment_types
    from axis.framework.workspaces.types import load_manifest

    ws = Path(workspace_path)

    # --- Guardrail: reject unsupported experiment types ---
    plan = resolve_run_targets(ws, run_filter=run_filter)
    manifest = load_manifest(ws)
    config_paths = [t.config_path for t in plan.targets]
    type_issues = check_config_experiment_types(
        ws, config_paths,
        workspace_type=manifest.workspace_type.value,
    )
    if type_issues:
        raise ValueError(type_issues[0].message)

    results_dir = Path(results_root) if results_root is not None else (ws / "results")
    results_dir.mkdir(exist_ok=True)

    # Workspace-local repository: artifacts go under <workspace>/results/.
    repo = ExperimentRepository(results_dir)
    executor = ExperimentExecutor(repository=repo)
    workspace_task_id = None
    if progress is not None and show_workspace_progress and len(plan.targets) > 1:
        workspace_task_id = progress.add_task(
            "Workspace configs",
            total=len(plan.targets),
        )

    results: list[WorkspaceExecutionResult] = []

    for target in plan.targets:
        override_path = None
        if config_overrides_by_role is not None:
            override_path = config_overrides_by_role.get(target.role)
        config_path = Path(override_path) if override_path else (ws / target.config_path)
        config = _load_config_file(config_path)
        experiment_result = executor.execute(
            config,
            progress=progress,
            progress_description_prefix=progress_description_prefix,
        )
        results.append(WorkspaceExecutionResult(
            experiment_result=experiment_result,
            role=target.role,
            config_path=target.config_path,
        ))
        if progress is not None and workspace_task_id is not None:
            progress.advance(workspace_task_id)

    return results
