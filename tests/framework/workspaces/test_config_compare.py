"""Tests for workspace config comparison."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from axis.framework.workspaces.config_compare import compare_workspace_configs
from axis.framework.workspaces.scaffold import scaffold_workspace
from axis.framework.workspaces.types import WorkspaceManifest


def _comparison_manifest() -> WorkspaceManifest:
    return WorkspaceManifest.model_validate({
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


def _single_manifest() -> WorkspaceManifest:
    return WorkspaceManifest.model_validate({
        "workspace_id": "single-ws",
        "title": "Single",
        "workspace_class": "investigation",
        "workspace_type": "single_system",
        "status": "draft",
        "lifecycle_stage": "idea",
        "created_at": "2026-01-01",
        "question": "What happens?",
        "system_under_test": "system_a",
    })


def test_compares_reference_and_candidate_configs(tmp_path: Path) -> None:
    ws = tmp_path / "cmp-ws"
    scaffold_workspace(ws, _comparison_manifest())

    candidate = ws / "configs" / "candidate-system_c.yaml"
    data = yaml.safe_load(candidate.read_text())
    data["execution"]["max_steps"] = 200
    data["system"]["policy"]["temperature"] = 2.0
    candidate.write_text(yaml.dump(data, default_flow_style=False))

    result = compare_workspace_configs(ws)

    assert result.reference_config == "configs/reference-system_a.yaml"
    assert result.candidate_config == "configs/candidate-system_c.yaml"
    assert result.candidate_delta["system_type"] == "system_c"
    assert result.candidate_delta["execution"]["max_steps"] == 200
    assert result.candidate_delta["system"]["policy"]["temperature"] == 2.0
    assert result.reference_values["system_type"] == "system_a"
    assert result.reference_values["execution"]["max_steps"] == 100
    assert result.reference_values["system"]["policy"]["temperature"] == 1.0


def test_rejects_single_system_workspace(tmp_path: Path) -> None:
    ws = tmp_path / "single-ws"
    scaffold_workspace(ws, _single_manifest())

    with pytest.raises(ValueError, match="only supported"):
        compare_workspace_configs(ws)


def test_requires_primary_config_roles(tmp_path: Path) -> None:
    ws = tmp_path / "cmp-ws"
    scaffold_workspace(ws, _comparison_manifest())
    manifest_path = ws / "workspace.yaml"
    manifest_data = yaml.safe_load(manifest_path.read_text())
    manifest_data["primary_configs"] = [
        "configs/reference-system_a.yaml",
        "configs/candidate-system_c.yaml",
    ]
    manifest_path.write_text(yaml.dump(manifest_data, default_flow_style=False))

    with pytest.raises(ValueError, match="requires role annotations"):
        compare_workspace_configs(ws)
