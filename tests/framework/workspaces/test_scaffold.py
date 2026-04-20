"""Tests for WP-03: Workspace scaffolder."""

from __future__ import annotations

import pytest
from pathlib import Path

from axis.framework.workspaces.scaffold import scaffold_workspace
from axis.framework.workspaces.types import WorkspaceManifest, WorkspaceType
from axis.framework.workspaces.validation import check_workspace


def _make_manifest(**overrides) -> WorkspaceManifest:
    base = {
        "workspace_id": "test-scaffold",
        "title": "Scaffold Test",
        "workspace_class": "investigation",
        "workspace_type": "single_system",
        "status": "draft",
        "lifecycle_stage": "idea",
        "created_at": "2026-01-01",
        "question": "Does scaffolding work?",
        "system_under_test": "system_a",
    }
    base.update(overrides)
    return WorkspaceManifest.model_validate(base)


class TestScaffold:
    def test_creates_valid_single_system(self, tmp_path):
        ws = tmp_path / "my-ws"
        manifest = _make_manifest()
        result = scaffold_workspace(ws, manifest)
        assert result == ws
        assert (ws / "workspace.yaml").exists()
        assert (ws / "README.md").exists()
        assert (ws / "notes.md").exists()
        for d in ("configs", "results", "comparisons", "measurements", "exports"):
            assert (ws / d).is_dir()
        # Should have 1 baseline config
        configs = list((ws / "configs").glob("*.yaml"))
        assert len(configs) == 1
        # Checker should validate it
        check = check_workspace(ws)
        assert check.is_valid

    def test_creates_valid_comparison(self, tmp_path):
        ws = tmp_path / "cmp-ws"
        manifest = WorkspaceManifest.model_validate({
            "workspace_id": "cmp-ws",
            "title": "Comparison",
            "workspace_class": "investigation",
            "workspace_type": "system_comparison",
            "status": "draft",
            "lifecycle_stage": "idea",
            "created_at": "2026-01-01",
            "question": "Which is better?",
            "reference_system": "system_a",
            "candidate_system": "system_c",
        })
        scaffold_workspace(ws, manifest)
        configs = list((ws / "configs").glob("*.yaml"))
        assert len(configs) >= 2
        assert check_workspace(ws).is_valid

    def test_creates_valid_development(self, tmp_path):
        ws = tmp_path / "dev-ws"
        manifest = WorkspaceManifest.model_validate({
            "workspace_id": "dev-ws",
            "title": "Dev",
            "workspace_class": "development",
            "workspace_type": "system_development",
            "status": "draft",
            "lifecycle_stage": "idea",
            "created_at": "2026-01-01",
            "development_goal": "Build it",
            "artifact_kind": "system",
            "artifact_under_development": "system_d",
        })
        scaffold_workspace(ws, manifest)
        assert (ws / "concept").is_dir()
        assert (ws / "engineering").is_dir()
        assert check_workspace(ws).is_valid

    def test_fails_if_path_exists(self, tmp_path):
        ws = tmp_path / "existing"
        ws.mkdir()
        with pytest.raises(FileExistsError):
            scaffold_workspace(ws, _make_manifest())
