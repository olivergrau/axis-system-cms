"""Handler for development / system_development workspaces."""

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
    from axis.framework.workspaces.validation import WorkspaceCheckIssue

_DEVELOPMENT_DIRS = ("concept", "engineering")


class SystemDevelopmentHandler(WorkspaceHandler):

    def create_directories(
        self, ws: Path, manifest: "WorkspaceManifest",
    ) -> None:
        for d in _DEVELOPMENT_DIRS:
            (ws / d).mkdir(exist_ok=True)

    def create_configs(
        self, ws: Path, manifest: "WorkspaceManifest",
    ) -> list[str]:
        from axis.framework.workspaces.scaffold import _write_placeholder_config

        artifact_name = manifest.artifact_under_development or "system_a"
        configs_dir = ws / "configs"
        filename = f"baseline-{artifact_name}.yaml"
        _write_placeholder_config(
            configs_dir / filename,
            system_type="system_a",
        )
        return [f"configs/{filename}"]

    def scaffold_manifest_fields(
        self, ws: Path, manifest: "WorkspaceManifest",
    ) -> dict:
        artifact_name = manifest.artifact_under_development or "system_a"
        return {
            "baseline_config": f"configs/baseline-{artifact_name}.yaml",
            "candidate_config": None,
            "baseline_results": [],
            "candidate_results": [],
            "current_candidate_result": None,
            "current_validation_comparison": None,
        }

    def resolve_run_targets(
        self,
        ws: Path,
        manifest: "WorkspaceManifest",
        configs: list[str],
        run_filter: str | None = None,
    ) -> list["WorkspaceRunTarget"]:
        from axis.framework.workspaces.resolution import WorkspaceRunTarget

        targets: list[WorkspaceRunTarget] = []

        baseline_cfg = manifest.baseline_config
        candidate_cfg = manifest.candidate_config

        if run_filter == "baseline":
            if baseline_cfg:
                targets.append(WorkspaceRunTarget(
                    config_path=baseline_cfg, role="baseline"))
            return targets

        if run_filter == "candidate":
            if candidate_cfg:
                targets.append(WorkspaceRunTarget(
                    config_path=candidate_cfg, role="candidate"))
            else:
                raise ValueError(
                    "No candidate_config set in workspace manifest. "
                    "Create a candidate config first."
                )
            return targets

        # No filter: run what's available
        if baseline_cfg:
            targets.append(WorkspaceRunTarget(
                config_path=baseline_cfg, role="baseline"))
        if candidate_cfg:
            targets.append(WorkspaceRunTarget(
                config_path=candidate_cfg, role="candidate"))

        # Fallback for legacy manifests without baseline_config
        if not targets:
            targets = [
                WorkspaceRunTarget(config_path=cfg, role="baseline")
                for cfg in configs
            ]

        return targets

    def resolve_comparison_targets(
        self,
        ws: Path,
        manifest: "WorkspaceManifest",
        repo: object,
        experiments: list[str],
    ) -> "WorkspaceComparisonPlan":
        from axis.framework.workspaces.compare_resolution import (
            WorkspaceCompareTarget,
            WorkspaceComparisonPlan,
        )

        # Development workflow: compare latest baseline vs current candidate
        if not manifest.current_candidate_result:
            raise ValueError(
                "No candidate result available. "
                "Run 'axis workspaces run --candidate-only' first."
            )

        if not manifest.baseline_results:
            raise ValueError(
                "No baseline results available. "
                "Run 'axis workspaces run --baseline-only' first."
            )

        ref_path = manifest.baseline_results[-1]  # latest baseline
        cand_path = manifest.current_candidate_result

        ref_eid, ref_rid = self._resolve_result_path(repo, ref_path, "reference")
        cand_eid, cand_rid = self._resolve_result_path(repo, cand_path, "candidate")

        return WorkspaceComparisonPlan(
            reference=WorkspaceCompareTarget(
                experiment_id=ref_eid, run_id=ref_rid, role="reference"),
            candidate=WorkspaceCompareTarget(
                experiment_id=cand_eid, run_id=cand_rid, role="candidate"),
        )

    @staticmethod
    def _resolve_result_path(repo, result_path: str, role: str) -> tuple[str, str]:
        """Extract experiment_id from a result path and resolve run via output abstraction.

        Handles both formats:
        - ``results/<eid>`` (experiment-root, new)
        - ``results/<eid>/runs/<rid>`` (legacy run-level)
        """
        from axis.framework.workspaces.compare_resolution import _resolve_run_from_output

        parts = result_path.split("/")
        if len(parts) >= 2:
            eid = parts[1]  # results/<eid>
        else:
            raise ValueError(
                f"Cannot parse {role} result path: {result_path}"
            )

        # Legacy path with explicit run — use it directly
        if len(parts) >= 4:
            runs = repo.list_runs(eid)
            rid = parts[3]
            if rid in runs:
                return eid, rid

        # Use output abstraction to resolve run
        rid = _resolve_run_from_output(repo, eid)
        return eid, rid

    def validate(
        self, ws: Path, manifest: "WorkspaceManifest",
    ) -> list["WorkspaceCheckIssue"]:
        from axis.framework.workspaces.validation import (
            WorkspaceCheckIssue,
            WorkspaceCheckSeverity,
        )

        issues: list[WorkspaceCheckIssue] = []
        for dname in _DEVELOPMENT_DIRS:
            if not (ws / dname).is_dir():
                issues.append(WorkspaceCheckIssue(
                    severity=WorkspaceCheckSeverity.ERROR,
                    message=f"Required directory for development workspace: {dname}/",
                    path=str(ws / dname),
                ))

        # Development state checks
        if manifest.baseline_config and not (ws / manifest.baseline_config).exists():
            issues.append(WorkspaceCheckIssue(
                severity=WorkspaceCheckSeverity.ERROR,
                message=f"Declared baseline_config does not exist: {manifest.baseline_config}",
                path=str(ws / manifest.baseline_config),
            ))

        if manifest.candidate_config and not (ws / manifest.candidate_config).exists():
            issues.append(WorkspaceCheckIssue(
                severity=WorkspaceCheckSeverity.ERROR,
                message=f"Declared candidate_config does not exist: {manifest.candidate_config}",
                path=str(ws / manifest.candidate_config),
            ))

        if not manifest.candidate_config:
            issues.append(WorkspaceCheckIssue(
                severity=WorkspaceCheckSeverity.INFO,
                message="Workspace is in pre-candidate state (no candidate_config set)",
            ))
        elif not manifest.candidate_results:
            issues.append(WorkspaceCheckIssue(
                severity=WorkspaceCheckSeverity.WARNING,
                message="Post-candidate state but no candidate results yet",
            ))

        return issues
