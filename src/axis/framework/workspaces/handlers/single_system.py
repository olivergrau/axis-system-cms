"""Handler for investigation / single_system workspaces."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from axis.framework.workspaces.handler import WorkspaceHandler

if TYPE_CHECKING:
    from axis.framework.workspaces.compare_resolution import (
        WorkspaceComparisonPlan,
    )
    from axis.framework.workspaces.resolution import WorkspaceRunTarget
    from axis.framework.workspaces.types import WorkspaceManifest


class SingleSystemHandler(WorkspaceHandler):

    def create_configs(
        self, ws: Path, manifest: "WorkspaceManifest",
    ) -> list[str]:
        from axis.framework.workspaces.scaffold import (
            _write_investigation_config,
        )

        configs_dir = ws / "configs"
        system = manifest.system_under_test or "system_a"

        # Create a point baseline config (default scaffold).
        baseline_name = f"{system}-baseline.yaml"
        _write_investigation_config(
            configs_dir / baseline_name,
            system_type=system,
        )

        # Only declare the baseline as primary.
        return [f"configs/{baseline_name}"]

    def resolve_run_targets(
        self,
        ws: Path,
        manifest: "WorkspaceManifest",
        configs: list[str],
        run_filter: str | None = None,
    ) -> list["WorkspaceRunTarget"]:
        from axis.framework.workspaces.resolution import WorkspaceRunTarget

        return [
            WorkspaceRunTarget(config_path=cfg, role="system_under_test")
            for cfg in configs
        ]

    def resolve_comparison_targets(
        self,
        ws: Path,
        manifest: "WorkspaceManifest",
        repo: object,
        experiments: list[str],
    ) -> "WorkspaceComparisonPlan":
        from axis.framework.workspaces.compare_resolution import (
            _resolve_by_manifest_order,
        )

        return _resolve_by_manifest_order(repo, manifest, experiments)
