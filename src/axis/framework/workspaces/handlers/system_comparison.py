"""Handler for investigation / system_comparison workspaces."""

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


class SystemComparisonHandler(WorkspaceHandler):

    def create_configs(
        self, ws: Path, manifest: "WorkspaceManifest",
    ) -> list[str]:
        from axis.framework.workspaces.scaffold import _write_investigation_config

        configs_dir = ws / "configs"
        ref_name = f"reference-{manifest.reference_system}.yaml"
        cand_name = f"candidate-{manifest.candidate_system}.yaml"
        _write_investigation_config(
            configs_dir / ref_name,
            system_type=manifest.reference_system or "system_a",
        )
        _write_investigation_config(
            configs_dir / cand_name,
            system_type=manifest.candidate_system or "system_a",
        )
        return [f"configs/{ref_name}", f"configs/{cand_name}"]

    def resolve_run_targets(
        self,
        ws: Path,
        manifest: "WorkspaceManifest",
        configs: list[str],
        run_filter: str | None = None,
    ) -> list["WorkspaceRunTarget"]:
        from axis.framework.workspaces.resolution import WorkspaceRunTarget

        targets: list[WorkspaceRunTarget] = []
        for i, cfg in enumerate(configs):
            if i == 0:
                role = "reference"
            elif i == 1:
                role = "candidate"
            else:
                role = "candidate" if "candidate" in cfg else "reference"
            targets.append(WorkspaceRunTarget(config_path=cfg, role=role))
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
            _resolve_latest_by_role,
            _resolve_by_manifest_order,
            _resolve_by_system,
        )

        ref_system = manifest.reference_system
        cand_system = manifest.candidate_system

        if not ref_system or not cand_system:
            raise ValueError(
                "Cannot auto-resolve comparison: manifest does not declare "
                "both reference_system and candidate_system."
            )

        # Same system → resolve latest reference/candidate outputs by manifest role,
        # falling back to the latest two point outputs overall.
        if ref_system == cand_system:
            return _resolve_by_manifest_order(repo, manifest, experiments)

        # Different systems → prefer latest role-tagged workspace outputs,
        # then fall back to system-type lookup if needed.
        ref_resolved = _resolve_latest_by_role(
            repo, manifest, experiments, "reference")
        cand_resolved = _resolve_latest_by_role(
            repo, manifest, experiments, "candidate")

        if ref_resolved is None:
            ref_resolved = _resolve_by_system(
                repo, experiments, ref_system, "reference")
        if cand_resolved is None:
            cand_resolved = _resolve_by_system(
                repo, experiments, cand_system, "candidate")

        ref_eid, ref_rid = ref_resolved
        cand_eid, cand_rid = cand_resolved

        return WorkspaceComparisonPlan(
            reference=WorkspaceCompareTarget(
                experiment_id=ref_eid, run_id=ref_rid, role="reference"),
            candidate=WorkspaceCompareTarget(
                experiment_id=cand_eid, run_id=cand_rid, role="candidate"),
        )

    def validate(
        self, ws: Path, manifest: "WorkspaceManifest",
    ) -> list["WorkspaceCheckIssue"]:
        from axis.framework.workspaces.validation import (
            WorkspaceCheckIssue,
            WorkspaceCheckSeverity,
        )

        issues: list[WorkspaceCheckIssue] = []
        configs_dir = ws / "configs"
        if configs_dir.is_dir():
            yaml_files = (
                list(configs_dir.glob("*.yaml"))
                + list(configs_dir.glob("*.yml"))
            )
            if len(yaml_files) < 2:
                issues.append(WorkspaceCheckIssue(
                    severity=WorkspaceCheckSeverity.WARNING,
                    message="system_comparison workspace should have at least 2 configs",
                    path=str(configs_dir),
                ))
        return issues
