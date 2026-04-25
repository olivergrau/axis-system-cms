"""Tests for WP-01: Workspace manifest model."""

from __future__ import annotations

import pytest
from pathlib import Path

from axis.framework.workspaces.types import (
    ArtifactKind,
    ConfigEntry,
    LinkedArtifactRef,
    WorkspaceClass,
    WorkspaceLifecycleStage,
    WorkspaceManifest,
    WorkspaceStatus,
    WorkspaceType,
    config_entry_path,
    config_entry_role,
    load_manifest,
)


# -- Helpers ------------------------------------------------------------------

def _minimal_investigation_single() -> dict:
    return {
        "workspace_id": "test-single",
        "title": "Test",
        "workspace_class": "investigation",
        "workspace_type": "single_system",
        "status": "draft",
        "lifecycle_stage": "idea",
        "created_at": "2026-01-01",
        "question": "Does it work?",
        "system_under_test": "system_a",
    }


def _minimal_investigation_comparison() -> dict:
    return {
        "workspace_id": "test-cmp",
        "title": "Test comparison",
        "workspace_class": "investigation",
        "workspace_type": "system_comparison",
        "status": "draft",
        "lifecycle_stage": "idea",
        "created_at": "2026-01-01",
        "question": "Which is better?",
        "reference_system": "system_a",
        "candidate_system": "system_c",
    }


def _minimal_development_system() -> dict:
    return {
        "workspace_id": "test-dev",
        "title": "Test dev",
        "workspace_class": "development",
        "workspace_type": "system_development",
        "status": "draft",
        "lifecycle_stage": "idea",
        "created_at": "2026-01-01",
        "development_goal": "Build something",
        "artifact_kind": "system",
        "artifact_under_development": "system_d",
    }


# -- Valid manifests ----------------------------------------------------------

class TestValidManifests:
    def test_single_system(self):
        m = WorkspaceManifest.model_validate(_minimal_investigation_single())
        assert m.workspace_class == WorkspaceClass.INVESTIGATION
        assert m.workspace_type == WorkspaceType.SINGLE_SYSTEM

    def test_system_comparison(self):
        m = WorkspaceManifest.model_validate(
            _minimal_investigation_comparison())
        assert m.reference_system == "system_a"
        assert m.candidate_system == "system_c"

    def test_system_development(self):
        m = WorkspaceManifest.model_validate(_minimal_development_system())
        assert m.artifact_kind == ArtifactKind.SYSTEM

    def test_optional_fields(self):
        data = _minimal_investigation_single()
        data["tags"] = ["test", "probe"]
        data["primary_configs"] = ["configs/a.yaml"]
        data["description"] = "A test workspace"
        m = WorkspaceManifest.model_validate(data)
        assert m.tags == ["test", "probe"]
        assert m.primary_configs == ["configs/a.yaml"]

    def test_structured_primary_configs(self):
        data = _minimal_investigation_comparison()
        data["primary_configs"] = [
            {"path": "configs/reference.yaml", "role": "reference"},
            {"path": "configs/candidate.yaml", "role": "candidate"},
        ]
        m = WorkspaceManifest.model_validate(data)
        assert isinstance(m.primary_configs[0], ConfigEntry)
        assert (
            config_entry_path(m.primary_configs[0])
            == "configs/reference.yaml"
        )
        assert config_entry_role(m.primary_configs[1]) == "candidate"

    def test_linked_artifact_ref(self):
        ref = LinkedArtifactRef(id="exp-001", role="reference")
        assert ref.id == "exp-001"
        assert ref.role == "reference"

    def test_accepts_new_status_values(self):
        data = _minimal_investigation_single()
        data["status"] = "active"
        m = WorkspaceManifest.model_validate(data)
        assert m.status == WorkspaceStatus.ACTIVE

    def test_accepts_new_lifecycle_values(self):
        data = _minimal_investigation_single()
        data["lifecycle_stage"] = "final"
        m = WorkspaceManifest.model_validate(data)
        assert m.lifecycle_stage == WorkspaceLifecycleStage.FINAL


# -- Invalid manifests --------------------------------------------------------

class TestInvalidManifests:
    def test_invalid_class_type_combination(self):
        data = _minimal_investigation_single()
        data["workspace_class"] = "development"
        with pytest.raises(ValueError, match="Invalid class/type"):
            WorkspaceManifest.model_validate(data)

    def test_investigation_without_question(self):
        data = _minimal_investigation_single()
        del data["question"]
        with pytest.raises(ValueError, match="question"):
            WorkspaceManifest.model_validate(data)

    def test_development_without_goal(self):
        data = _minimal_development_system()
        del data["development_goal"]
        with pytest.raises(ValueError, match="development_goal"):
            WorkspaceManifest.model_validate(data)

    def test_single_system_without_system_under_test(self):
        data = _minimal_investigation_single()
        del data["system_under_test"]
        with pytest.raises(ValueError, match="system_under_test"):
            WorkspaceManifest.model_validate(data)

    def test_comparison_without_reference(self):
        data = _minimal_investigation_comparison()
        del data["reference_system"]
        with pytest.raises(ValueError, match="reference_system"):
            WorkspaceManifest.model_validate(data)

    def test_comparison_without_candidate(self):
        data = _minimal_investigation_comparison()
        del data["candidate_system"]
        with pytest.raises(ValueError, match="candidate_system"):
            WorkspaceManifest.model_validate(data)

    def test_system_dev_wrong_artifact_kind(self):
        data = _minimal_development_system()
        data["artifact_kind"] = "invalid"
        with pytest.raises(ValueError):
            WorkspaceManifest.model_validate(data)

    def test_system_dev_missing_artifact_kind(self):
        data = _minimal_development_system()
        del data["artifact_kind"]
        with pytest.raises(ValueError, match="artifact_kind"):
            WorkspaceManifest.model_validate(data)

    def test_removed_legacy_status_idea_is_rejected(self):
        data = _minimal_investigation_single()
        data["status"] = "idea"
        with pytest.raises(ValueError, match="status"):
            WorkspaceManifest.model_validate(data)

    def test_removed_legacy_status_running_is_rejected(self):
        data = _minimal_investigation_single()
        data["status"] = "running"
        with pytest.raises(ValueError, match="status"):
            WorkspaceManifest.model_validate(data)


# -- Load from existing workspaces -------------------------------------------

WORKSPACE_ROOT = Path(__file__).resolve().parents[3] / "workspaces"


class TestLoadExistingWorkspaces:
    @pytest.mark.skipif(
        not (WORKSPACE_ROOT / "system-c-baseline-grid2d").exists(),
        reason="probe workspace not present",
    )
    def test_load_single_system(self):
        m = load_manifest(WORKSPACE_ROOT / "system-c-baseline-grid2d")
        assert m.workspace_type == WorkspaceType.SINGLE_SYSTEM
        assert m.system_under_test == "system_c"

    @pytest.mark.skipif(
        not (WORKSPACE_ROOT / "system-a-vs-system-c-grid2d-baseline").exists(),
        reason="probe workspace not present",
    )
    def test_load_system_comparison(self):
        m = load_manifest(
            WORKSPACE_ROOT / "system-a-vs-system-c-grid2d-baseline"
        )
        assert m.workspace_type == WorkspaceType.SYSTEM_COMPARISON
        assert m.reference_system == "system_a"

    @pytest.mark.skipif(
        not (WORKSPACE_ROOT / "system-d-development").exists(),
        reason="probe workspace not present",
    )
    def test_load_system_development(self):
        m = load_manifest(WORKSPACE_ROOT / "system-d-development")
        assert m.workspace_type == WorkspaceType.SYSTEM_DEVELOPMENT
        assert m.artifact_kind == ArtifactKind.SYSTEM
