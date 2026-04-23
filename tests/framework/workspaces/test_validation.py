"""Tests for WP-02: Workspace checker."""

from __future__ import annotations

import pytest
from pathlib import Path

from axis.framework.workspaces.validation import (
    WorkspaceCheckSeverity,
    check_workspace,
)


@pytest.fixture
def tmp_workspace(tmp_path):
    """Create a minimal valid single_system workspace."""
    import yaml

    ws = tmp_path / "test-ws"
    ws.mkdir()
    manifest = {
        "workspace_id": "test-ws",
        "title": "Test",
        "workspace_class": "investigation",
        "workspace_type": "single_system",
        "status": "draft",
        "lifecycle_stage": "idea",
        "created_at": "2026-01-01",
        "question": "Does it work?",
        "system_under_test": "system_a",
    }
    (ws / "workspace.yaml").write_text(yaml.dump(manifest))
    (ws / "README.md").write_text("# Test\n")
    (ws / "notes.md").write_text("")
    for d in ("configs", "results", "comparisons", "exports"):
        (ws / d).mkdir()
    (ws / "configs" / "baseline.yaml").write_text("system_type: system_a\n")
    return ws


class TestCheckWorkspace:
    def test_valid_workspace(self, tmp_workspace):
        result = check_workspace(tmp_workspace)
        assert result.is_valid

    def test_missing_manifest(self, tmp_path):
        result = check_workspace(tmp_path)
        assert not result.is_valid
        assert any("workspace.yaml" in i.message for i in result.issues)

    def test_missing_required_dir(self, tmp_workspace):
        import shutil
        shutil.rmtree(tmp_workspace / "comparisons")
        result = check_workspace(tmp_workspace)
        assert not result.is_valid
        assert any("comparisons" in i.message for i in result.issues)

    def test_missing_required_file(self, tmp_workspace):
        (tmp_workspace / "notes.md").unlink()
        result = check_workspace(tmp_workspace)
        assert not result.is_valid

    def test_development_missing_concept(self, tmp_path):
        import yaml
        ws = tmp_path / "dev-ws"
        ws.mkdir()
        manifest = {
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
        }
        (ws / "workspace.yaml").write_text(yaml.dump(manifest))
        (ws / "README.md").write_text("# Dev\n")
        (ws / "notes.md").write_text("")
        for d in ("configs", "results", "comparisons", "exports"):
            (ws / d).mkdir()
        (ws / "configs" / "baseline.yaml").write_text("system_type: system_a\n")
        # Missing concept/ and engineering/
        result = check_workspace(ws)
        assert not result.is_valid
        errors = [i for i in result.issues if i.severity ==
                  WorkspaceCheckSeverity.ERROR]
        assert any("concept" in i.message for i in errors)
        assert any("engineering" in i.message for i in errors)

    def test_declared_path_missing_warns(self, tmp_workspace):
        import yaml
        manifest_path = tmp_workspace / "workspace.yaml"
        data = yaml.safe_load(manifest_path.read_text())
        data["primary_results"] = [{"path": "results/nonexistent.md"}]
        manifest_path.write_text(yaml.dump(data))
        result = check_workspace(tmp_workspace)
        assert result.is_valid  # warnings don't invalidate
        assert any(
            "nonexistent" in i.message
            for i in result.issues
            if i.severity == WorkspaceCheckSeverity.WARNING
        )

    def test_no_configs_warns(self, tmp_workspace):
        for f in (tmp_workspace / "configs").iterdir():
            f.unlink()
        result = check_workspace(tmp_workspace)
        assert any(
            "No config files" in i.message for i in result.issues
        )

    def test_ofat_config_rejected_for_comparison(self, tmp_path):
        """OFAT config must be rejected for non-single_system workspaces."""
        import yaml
        # Create a system_comparison workspace
        ws = tmp_path / "cmp-ws"
        ws.mkdir()
        manifest = {
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
        }
        (ws / "workspace.yaml").write_text(yaml.dump(manifest))
        (ws / "README.md").write_text("# Test\n")
        (ws / "notes.md").write_text("")
        for d in ("configs", "results", "comparisons", "exports"):
            (ws / d).mkdir()
        ofat_config = {
            "system_type": "system_a",
            "experiment_type": "ofat",
            "parameter_path": "system.policy.temperature",
            "parameter_values": [0.5, 1.0, 2.0],
            "general": {"seed": 42},
            "execution": {"max_steps": 50},
        }
        (ws / "configs" / "baseline.yaml").write_text(yaml.dump(ofat_config))
        manifest["primary_configs"] = ["configs/baseline.yaml"]
        (ws / "workspace.yaml").write_text(yaml.dump(manifest))

        result = check_workspace(ws)
        assert not result.is_valid
        errors = [i for i in result.issues
                  if i.severity == WorkspaceCheckSeverity.ERROR]
        assert any("ofat" in i.message.lower() for i in errors)

    def test_ofat_config_accepted_for_single_system(self, tmp_workspace):
        """OFAT config is allowed for single_system workspaces."""
        import yaml
        ofat_config = {
            "system_type": "system_a",
            "experiment_type": "ofat",
            "parameter_path": "system.policy.temperature",
            "parameter_values": [0.5, 1.0, 2.0],
            "general": {"seed": 42},
            "execution": {"max_steps": 50},
        }
        (tmp_workspace / "configs" / "baseline.yaml").write_text(
            yaml.dump(ofat_config))
        manifest_path = tmp_workspace / "workspace.yaml"
        data = yaml.safe_load(manifest_path.read_text())
        data["primary_configs"] = ["configs/baseline.yaml"]
        manifest_path.write_text(yaml.dump(data))

        result = check_workspace(tmp_workspace)
        assert result.is_valid, [i.message for i in result.issues
                                 if i.severity == WorkspaceCheckSeverity.ERROR]

    def test_ofat_config_missing_fields_rejected(self, tmp_workspace):
        """OFAT config without parameter_path/parameter_values is invalid."""
        import yaml
        ofat_config = {
            "system_type": "system_a",
            "experiment_type": "ofat",
            "general": {"seed": 42},
            "execution": {"max_steps": 50},
            # Missing parameter_path and parameter_values
        }
        (tmp_workspace / "configs" / "baseline.yaml").write_text(
            yaml.dump(ofat_config))
        manifest_path = tmp_workspace / "workspace.yaml"
        data = yaml.safe_load(manifest_path.read_text())
        data["primary_configs"] = ["configs/baseline.yaml"]
        manifest_path.write_text(yaml.dump(data))

        result = check_workspace(tmp_workspace)
        assert not result.is_valid
        errors = [i for i in result.issues
                  if i.severity == WorkspaceCheckSeverity.ERROR]
        assert any("parameter_path" in i.message for i in errors)
        assert any("parameter_values" in i.message for i in errors)

    def test_single_run_config_passes(self, tmp_workspace):
        """Configs with experiment_type=single_run should not produce errors."""
        import yaml
        config = {
            "system_type": "system_a",
            "experiment_type": "single_run",
            "general": {"seed": 42},
        }
        (tmp_workspace / "configs" / "baseline.yaml").write_text(
            yaml.dump(config))
        manifest_path = tmp_workspace / "workspace.yaml"
        data = yaml.safe_load(manifest_path.read_text())
        data["primary_configs"] = ["configs/baseline.yaml"]
        manifest_path.write_text(yaml.dump(data))

        result = check_workspace(tmp_workspace)
        assert result.is_valid


WORKSPACE_ROOT = Path(__file__).resolve().parents[3] / "workspaces"


class TestCheckExistingWorkspaces:
    @pytest.mark.skipif(
        not (WORKSPACE_ROOT / "system-c-baseline-grid2d").exists(),
        reason="workspace not present",
    )
    def test_existing_single_system(self):
        result = check_workspace(WORKSPACE_ROOT / "system-c-baseline-grid2d")
        assert result.is_valid

    @pytest.mark.skipif(
        not (WORKSPACE_ROOT / "system-a-vs-system-c-grid2d-baseline").exists(),
        reason="workspace not present",
    )
    def test_existing_comparison(self):
        result = check_workspace(
            WORKSPACE_ROOT / "system-a-vs-system-c-grid2d-baseline"
        )
        assert result.is_valid

    @pytest.mark.skipif(
        not (WORKSPACE_ROOT / "system-d-development").exists(),
        reason="workspace not present",
    )
    def test_existing_development(self):
        result = check_workspace(WORKSPACE_ROOT / "system-d-development")
        assert result.is_valid
