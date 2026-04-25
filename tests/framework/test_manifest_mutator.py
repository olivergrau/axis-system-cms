"""Tests for manifest mutator — WP-08."""

from __future__ import annotations

import pytest

from axis.framework.workspaces.manifest_mutator import (
    append_primary_comparison,
    append_primary_result,
    close_workspace,
    merge_scaffold_fields,
    set_candidate_config,
    set_primary_configs,
    update_current_validation_comparison,
    update_development_results,
)


class TestAppendPrimaryResult:

    def test_appends_to_empty(self) -> None:
        data: dict = {}
        append_primary_result(data, "exp-001", role="baseline")
        assert len(data["primary_results"]) == 1
        entry = data["primary_results"][0]
        assert entry["path"] == "results/exp-001"
        assert entry["role"] == "baseline"
        assert "timestamp" in entry
        assert entry["config"] == "results/exp-001/experiment_config.json"

    def test_idempotent(self) -> None:
        data: dict = {}
        append_primary_result(data, "exp-001")
        append_primary_result(data, "exp-001")
        assert len(data["primary_results"]) == 1

    def test_appends_with_output_form(self) -> None:
        data: dict = {}
        append_primary_result(
            data, "exp-001",
            output_form="sweep", system_type="system_a",
            baseline_run_id="run-0000",
        )
        entry = data["primary_results"][0]
        assert entry["output_form"] == "sweep"
        assert entry["system_type"] == "system_a"
        assert entry["baseline_run_id"] == "run-0000"

    def test_respects_existing_entries(self) -> None:
        data: dict = {
            "primary_results": [
                {"path": "results/exp-000", "timestamp": "t0"},
            ],
        }
        append_primary_result(data, "exp-001")
        assert len(data["primary_results"]) == 2

    def test_appends_config_changes_when_provided(self) -> None:
        data: dict = {}
        append_primary_result(
            data, "exp-001",
            config_changes={"system": {"policy": {"temperature": 2.0}}},
        )
        entry = data["primary_results"][0]
        assert entry["config_changes"] == {
            "system": {"policy": {"temperature": 2.0}},
        }

    def test_appends_run_notes_when_provided(self) -> None:
        data: dict = {}
        append_primary_result(
            data, "exp-001",
            run_notes="My notes for this run",
        )
        entry = data["primary_results"][0]
        assert entry["run_notes"] == "My notes for this run"


class TestUpdateDevelopmentResults:

    def test_noop_for_non_dev(self) -> None:
        data: dict = {"workspace_type": "single_system"}
        update_development_results(data, "exp-001", role="baseline")
        assert "baseline_results" not in data

    def test_baseline_appended(self) -> None:
        data: dict = {"workspace_type": "system_development"}
        update_development_results(data, "exp-001", role="baseline")
        assert data["baseline_results"] == ["results/exp-001"]

    def test_candidate_sets_current(self) -> None:
        data: dict = {"workspace_type": "system_development"}
        update_development_results(data, "exp-001", role="candidate")
        assert data["candidate_results"] == ["results/exp-001"]
        assert data["current_candidate_result"] == "results/exp-001"

    def test_idempotent(self) -> None:
        data: dict = {"workspace_type": "system_development"}
        update_development_results(data, "exp-001", role="baseline")
        update_development_results(data, "exp-001", role="baseline")
        assert len(data["baseline_results"]) == 1


class TestAppendPrimaryComparison:

    def test_appends(self) -> None:
        data: dict = {}
        append_primary_comparison(data, "comparisons/comparison-001.json")
        assert data["primary_comparisons"] == [
            "comparisons/comparison-001.json"]

    def test_idempotent(self) -> None:
        data: dict = {}
        append_primary_comparison(data, "comparisons/comparison-001.json")
        append_primary_comparison(data, "comparisons/comparison-001.json")
        assert len(data["primary_comparisons"]) == 1


class TestUpdateCurrentValidationComparison:

    def test_sets_for_dev(self) -> None:
        data: dict = {"workspace_type": "system_development"}
        update_current_validation_comparison(
            data, "comparisons/comparison-001.json")
        assert data["current_validation_comparison"] == \
            "comparisons/comparison-001.json"

    def test_noop_for_non_dev(self) -> None:
        data: dict = {"workspace_type": "single_system"}
        update_current_validation_comparison(
            data, "comparisons/comparison-001.json")
        assert "current_validation_comparison" not in data


class TestSetCandidateConfig:

    def test_sets_candidate(self) -> None:
        data: dict = {"workspace_type": "system_development"}
        set_candidate_config(data, "configs/candidate.yaml")
        assert data["candidate_config"] == "configs/candidate.yaml"

    def test_adds_to_primary_configs(self) -> None:
        data: dict = {
            "workspace_type": "system_development",
            "primary_configs": ["configs/baseline.yaml"],
        }
        set_candidate_config(data, "configs/candidate.yaml")
        assert {
            "path": "configs/candidate.yaml",
            "role": "candidate",
        } in data["primary_configs"]
        assert "configs/baseline.yaml" in data["primary_configs"]

    def test_idempotent_primary_configs(self) -> None:
        data: dict = {
            "workspace_type": "system_development",
            "primary_configs": [
                {"path": "configs/candidate.yaml", "role": "candidate"},
            ],
        }
        set_candidate_config(data, "configs/candidate.yaml")
        assert len(data["primary_configs"]) == 1

    def test_rejects_non_dev(self) -> None:
        data: dict = {"workspace_type": "single_system"}
        with pytest.raises(ValueError, match="development"):
            set_candidate_config(data, "configs/c.yaml")

    def test_creates_primary_configs_if_missing(self) -> None:
        data: dict = {"workspace_type": "system_development"}
        set_candidate_config(data, "configs/c.yaml")
        assert data["primary_configs"] == [
            {"path": "configs/c.yaml", "role": "candidate"},
        ]


class TestCloseWorkspace:

    def test_sets_closed_and_final(self) -> None:
        data: dict = {"status": "draft", "lifecycle_stage": "implementation"}
        close_workspace(data)
        assert data["status"] == "closed"
        assert data["lifecycle_stage"] == "final"

    def test_rejects_already_closed(self) -> None:
        data: dict = {"status": "closed", "lifecycle_stage": "final"}
        with pytest.raises(ValueError, match="already closed"):
            close_workspace(data)


class TestSetPrimaryConfigs:

    def test_sets_configs(self) -> None:
        data: dict = {}
        set_primary_configs(data, ["configs/a.yaml", "configs/b.yaml"])
        assert data["primary_configs"] == ["configs/a.yaml", "configs/b.yaml"]

    def test_overwrites_existing(self) -> None:
        data: dict = {"primary_configs": ["old.yaml"]}
        set_primary_configs(data, ["new.yaml"])
        assert data["primary_configs"] == ["new.yaml"]


class TestMergeScaffoldFields:

    def test_merges_fields(self) -> None:
        data: dict = {"workspace_type": "system_development"}
        merge_scaffold_fields(data, {
            "baseline_config": "configs/baseline.yaml",
            "development_state": "active",
        })
        assert data["baseline_config"] == "configs/baseline.yaml"
        assert data["development_state"] == "active"
        assert data["workspace_type"] == "system_development"
