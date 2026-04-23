"""CLI application context — the composition root for AXIS CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class CLIContext:
    """Shared application context assembled at the CLI edge.

    All services and repositories that command handlers need are
    constructed once in ``build_context`` and passed through here.
    This keeps construction logic at the boundary and avoids
    service-locator patterns inside domain code.

    The context will grow as later work packages introduce
    manifest mutators and catalog integration.
    """

    repo: object
    """The experiment repository (``ExperimentRepository`` instance)."""

    root: Path
    """The repository root directory."""

    catalogs: dict = field(default_factory=dict)
    """Plugin-provided capability catalogs (populated after discovery)."""

    run_service: object = field(default=None)
    """``WorkspaceRunService`` instance."""

    compare_service: object = field(default=None)
    """``WorkspaceCompareService`` instance."""

    inspection_service: object = field(default=None)
    """``WorkspaceInspectionService`` instance."""

    workflow_service: object = field(default=None)
    """``WorkspaceWorkflowService`` instance."""


def build_context(root: Path) -> CLIContext:
    """Assemble the application context from the given root path.

    This is the single composition point for CLI commands.  Every
    dependency a handler needs is constructed here.
    """
    from axis.framework.catalogs import build_catalogs_from_registries
    from axis.framework.persistence import ExperimentRepository
    from axis.framework.workspaces.compare import compare_workspace
    from axis.framework.workspaces.drift import detect_drift
    from axis.framework.workspaces.execute import execute_workspace
    from axis.framework.workspaces.manifest_mutator import (
        close_workspace,
        set_candidate_config,
    )
    from axis.framework.workspaces.services.compare_service import (
        WorkspaceCompareService,
    )
    from axis.framework.workspaces.services.inspection_service import (
        WorkspaceInspectionService,
    )
    from axis.framework.workspaces.services.run_service import (
        WorkspaceRunService,
    )
    from axis.framework.workspaces.services.workflow_service import (
        WorkspaceWorkflowService,
    )
    from axis.framework.workspaces.summary import summarize_workspace
    from axis.framework.workspaces.run_summary import (
        resolve_run_summary_target,
    )
    from axis.framework.workspaces.sweep_result import resolve_sweep_result
    from axis.framework.workspaces.sync import (
        _load_yaml_roundtrip,
        _save_yaml_roundtrip,
        sync_manifest_after_compare,
        sync_manifest_after_run,
    )
    from axis.framework.workspaces.validation import check_workspace

    repo = ExperimentRepository(root)
    catalogs = build_catalogs_from_registries()
    return CLIContext(
        repo=repo,
        root=root,
        catalogs=catalogs,
        run_service=WorkspaceRunService(
            execute_fn=execute_workspace,
            sync_fn=sync_manifest_after_run,
            set_candidate_config_fn=set_candidate_config,
            load_yaml_roundtrip_fn=_load_yaml_roundtrip,
            save_yaml_roundtrip_fn=_save_yaml_roundtrip,
        ),
        compare_service=WorkspaceCompareService(
            compare_fn=compare_workspace,
            sync_fn=sync_manifest_after_compare,
        ),
        inspection_service=WorkspaceInspectionService(
            summarize_fn=summarize_workspace,
            check_fn=check_workspace,
            drift_fn=detect_drift,
            sweep_result_fn=resolve_sweep_result,
            run_summary_target_fn=resolve_run_summary_target,
        ),
        workflow_service=WorkspaceWorkflowService(
            close_workspace_fn=close_workspace,
            load_yaml_roundtrip_fn=_load_yaml_roundtrip,
            save_yaml_roundtrip_fn=_save_yaml_roundtrip,
        ),
    )
