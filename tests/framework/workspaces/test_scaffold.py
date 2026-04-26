"""Tests for WP-03: Workspace scaffolder."""

from __future__ import annotations

import pytest
import yaml
from pathlib import Path

from axis.framework.workspaces.scaffold import scaffold_workspace
from axis.framework.workspaces.types import WorkspaceManifest, WorkspaceType
from axis.framework.workspaces.validation import check_workspace
from axis.framework.cli.commands.experiments import _load_config_file


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
        readme = (ws / "README.md").read_text()
        notes = (ws / "notes.md").read_text()
        assert "Primary purpose:" in readme
        assert "system_a" in readme
        assert "single system" in notes
        assert "axis workspaces compare" in notes
        for d in ("configs", "results", "comparisons", "exports"):
            assert (ws / d).is_dir()
        # Should have 1 baseline config
        configs = list((ws / "configs").glob("*.yaml"))
        assert len(configs) == 1
        manifest_data = yaml.safe_load((ws / "workspace.yaml").read_text())
        assert manifest_data["primary_configs"] == [
            {"path": "configs/system_a-baseline.yaml", "role": "reference"},
        ]
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
        readme = (ws / "README.md").read_text()
        notes = (ws / "notes.md").read_text()
        assert "compare `system_a` as reference against `system_c`" in readme
        assert "Reference: `system_a`" in notes
        assert "Candidate: `system_c`" in notes
        manifest_data = yaml.safe_load((ws / "workspace.yaml").read_text())
        assert manifest_data["primary_configs"] == [
            {"path": "configs/reference-system_a.yaml", "role": "reference"},
            {"path": "configs/candidate-system_c.yaml", "role": "candidate"},
        ]
        configs = list((ws / "configs").glob("*.yaml"))
        assert len(configs) >= 2
        assert check_workspace(ws).is_valid

    def test_single_system_scaffold_uses_system_specific_template(self, tmp_path):
        ws = tmp_path / "aw-ws"
        manifest = _make_manifest(
            workspace_id="aw-ws",
            system_under_test="system_aw",
        )
        scaffold_workspace(ws, manifest)

        config_path = ws / "configs" / "system_aw-baseline.yaml"
        data = yaml.safe_load(config_path.read_text())
        assert data["execution"] == {
            "max_steps": 200,
            "trace_mode": "delta",
            "parallelism_mode": "episodes",
            "max_workers": 4,
        }
        assert data["logging"] == {
            "enabled": False,
            "console_enabled": False,
            "jsonl_enabled": False,
            "verbosity": "compact",
        }
        assert "curiosity" in data["system"]
        assert "arbitration" in data["system"]
        cfg = _load_config_file(config_path)
        assert cfg.system_type == "system_aw"

    def test_comparison_scaffold_uses_world_appropriate_template(self, tmp_path):
        ws = tmp_path / "b-cmp"
        manifest = WorkspaceManifest.model_validate({
            "workspace_id": "b-cmp",
            "title": "Comparison",
            "workspace_class": "investigation",
            "workspace_type": "system_comparison",
            "status": "draft",
            "lifecycle_stage": "idea",
            "created_at": "2026-01-01",
            "question": "Which is better?",
            "reference_system": "system_b",
            "candidate_system": "system_c",
        })
        scaffold_workspace(ws, manifest)

        ref_cfg = _load_config_file(ws / "configs" / "reference-system_b.yaml")
        cand_cfg = _load_config_file(ws / "configs" / "candidate-system_c.yaml")
        assert ref_cfg.world.world_type == "signal_landscape"
        assert cand_cfg.world.world_type == "grid_2d"
        assert ref_cfg.execution.trace_mode == "delta"
        assert cand_cfg.execution.parallelism_mode == "episodes"

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
        readme = (ws / "README.md").read_text()
        notes = (ws / "notes.md").read_text()
        assert "develop `system_d` as a system artifact" in readme
        assert "pre-candidate" in readme
        assert "Development goal: Build it" in notes
        assert (ws / "concept").is_dir()
        assert (ws / "engineering").is_dir()
        assert check_workspace(ws).is_valid

    def test_fails_if_path_exists(self, tmp_path):
        ws = tmp_path / "existing"
        ws.mkdir()
        with pytest.raises(FileExistsError):
            scaffold_workspace(ws, _make_manifest())
