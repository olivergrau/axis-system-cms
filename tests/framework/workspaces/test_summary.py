"""Tests for WP-04: Workspace summary."""

from __future__ import annotations

import pytest
from pathlib import Path

import yaml

from axis.framework.workspaces.scaffold import scaffold_workspace
from axis.framework.workspaces.summary import summarize_workspace, ArtifactEntry
from axis.framework.workspaces.types import WorkspaceManifest, WorkspaceType


class TestSummarize:
    def test_summary_from_scaffolded_workspace(self, tmp_path):
        ws = tmp_path / "test-ws"
        manifest = WorkspaceManifest.model_validate({
            "workspace_id": "test-ws",
            "title": "Summary Test",
            "workspace_class": "investigation",
            "workspace_type": "single_system",
            "status": "draft",
            "lifecycle_stage": "idea",
            "created_at": "2026-01-01",
            "question": "Does summary work?",
            "system_under_test": "system_a",
        })
        scaffold_workspace(ws, manifest)
        summary = summarize_workspace(ws)
        assert summary.workspace_id == "test-ws"
        assert summary.workspace_type == WorkspaceType.SINGLE_SYSTEM
        assert summary.system_under_test == "system_a"
        assert summary.check_result is not None
        assert summary.check_result.is_valid

    def test_primary_results_tracked_with_existence(self, tmp_path):
        """primary_results paths are resolved and checked for existence."""
        ws = tmp_path / "test-ws"
        manifest = WorkspaceManifest.model_validate({
            "workspace_id": "test-ws",
            "title": "Artifact tracking test",
            "workspace_class": "investigation",
            "workspace_type": "single_system",
            "status": "draft",
            "lifecycle_stage": "idea",
            "created_at": "2026-01-01",
            "question": "Are artifacts tracked?",
            "system_under_test": "system_a",
            "primary_results": [
                {"path": "results/exp-001/runs/run-0000"},
                {"path": "results/missing-path"},
            ],
        })
        scaffold_workspace(ws, manifest)

        # Create one of the declared paths so it exists.
        real_path = ws / "results" / "exp-001" / "runs" / "run-0000"
        real_path.mkdir(parents=True)

        summary = summarize_workspace(ws)
        assert len(summary.primary_results) == 2
        found = {e.path: e.exists for e in summary.primary_results}
        assert found["results/exp-001/runs/run-0000"] is True
        assert found["results/missing-path"] is False

    def test_primary_measurements_tracked(self, tmp_path):
        ws = tmp_path / "test-ws"
        manifest = WorkspaceManifest.model_validate({
            "workspace_id": "test-ws",
            "title": "Measurement test",
            "workspace_class": "investigation",
            "workspace_type": "single_system",
            "status": "draft",
            "lifecycle_stage": "idea",
            "created_at": "2026-01-01",
            "question": "Measurements?",
            "system_under_test": "system_a",
            "primary_measurements": ["measurements/summary.md"],
        })
        scaffold_workspace(ws, manifest)
        # Don't create the file — should show as missing.
        summary = summarize_workspace(ws)
        assert len(summary.primary_measurements) == 1
        assert summary.primary_measurements[0].exists is False

    def test_empty_primary_fields(self, tmp_path):
        ws = tmp_path / "test-ws"
        manifest = WorkspaceManifest.model_validate({
            "workspace_id": "test-ws",
            "title": "Empty fields",
            "workspace_class": "investigation",
            "workspace_type": "single_system",
            "status": "draft",
            "lifecycle_stage": "idea",
            "created_at": "2026-01-01",
            "question": "Empty?",
            "system_under_test": "system_a",
        })
        scaffold_workspace(ws, manifest)
        summary = summarize_workspace(ws)
        assert summary.primary_results == []
        assert summary.primary_comparisons == []
        assert summary.primary_measurements == []


WORKSPACE_ROOT = Path(__file__).resolve().parents[3] / "workspaces"


class TestSummarizeExisting:
    @pytest.mark.skipif(
        not (WORKSPACE_ROOT / "system-c-baseline-grid2d").exists(),
        reason="workspace not present",
    )
    def test_existing_single_system(self):
        s = summarize_workspace(WORKSPACE_ROOT / "system-c-baseline-grid2d")
        assert s.workspace_type == WorkspaceType.SINGLE_SYSTEM
        assert s.system_under_test == "system_c"
        # Has declared primary_configs
        assert len(s.primary_configs) >= 1
