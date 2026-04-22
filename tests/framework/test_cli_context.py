"""Tests for CLI context (composition root) — WP-02."""

from __future__ import annotations

from pathlib import Path

import pytest

from axis.framework.cli.context import CLIContext, build_context


class TestBuildContext:
    """Verify the composition root assembles a usable context."""

    def test_returns_cli_context(self, tmp_path: Path) -> None:
        ctx = build_context(tmp_path)
        assert isinstance(ctx, CLIContext)

    def test_repo_is_experiment_repository(self, tmp_path: Path) -> None:
        from axis.framework.persistence import ExperimentRepository

        ctx = build_context(tmp_path)
        assert isinstance(ctx.repo, ExperimentRepository)

    def test_root_matches_input(self, tmp_path: Path) -> None:
        ctx = build_context(tmp_path)
        assert ctx.root == tmp_path

    def test_context_is_frozen(self, tmp_path: Path) -> None:
        ctx = build_context(tmp_path)
        with pytest.raises(AttributeError):
            ctx.root = tmp_path  # type: ignore[misc]

    def test_services_have_real_dependencies(self, tmp_path: Path) -> None:
        """Services must be wired with actual collaborator functions."""
        ctx = build_context(tmp_path)

        # RunService
        from axis.framework.workspaces.execute import execute_workspace
        from axis.framework.workspaces.manifest_mutator import (
            close_workspace,
            set_candidate_config,
        )
        from axis.framework.workspaces.sync import (
            _load_yaml_roundtrip,
            _save_yaml_roundtrip,
            sync_manifest_after_run,
        )
        assert ctx.run_service._execute_fn is execute_workspace
        assert ctx.run_service._sync_fn is sync_manifest_after_run
        assert ctx.run_service._set_candidate_config_fn is set_candidate_config
        assert ctx.run_service._load_yaml_roundtrip_fn is _load_yaml_roundtrip
        assert ctx.run_service._save_yaml_roundtrip_fn is _save_yaml_roundtrip

        # CompareService
        from axis.framework.workspaces.compare import compare_workspace
        from axis.framework.workspaces.sync import sync_manifest_after_compare
        assert ctx.compare_service._compare_fn is compare_workspace
        assert ctx.compare_service._sync_fn is sync_manifest_after_compare

        # InspectionService
        from axis.framework.workspaces.summary import summarize_workspace
        from axis.framework.workspaces.validation import check_workspace
        from axis.framework.workspaces.drift import detect_drift
        from axis.framework.workspaces.sweep_result import resolve_sweep_result
        assert ctx.inspection_service._summarize_fn is summarize_workspace
        assert ctx.inspection_service._check_fn is check_workspace
        assert ctx.inspection_service._drift_fn is detect_drift
        assert ctx.inspection_service._sweep_result_fn is resolve_sweep_result

        # WorkflowService
        assert ctx.workflow_service._close_workspace_fn is close_workspace
        assert ctx.workflow_service._load_yaml_roundtrip_fn is _load_yaml_roundtrip
        assert ctx.workflow_service._save_yaml_roundtrip_fn is _save_yaml_roundtrip


class TestCLIMainUsesContext:
    """Verify the main entrypoint still works after context introduction."""

    def test_main_help_returns_one(self) -> None:
        from axis.framework.cli import main

        assert main([]) == 1  # no entity → help → exit 1

    def test_main_experiments_list(self, tmp_path: Path) -> None:
        from axis.framework.cli import main

        rc = main([
            "--root", str(tmp_path),
            "--output", "json",
            "experiments", "list",
        ])
        assert rc == 0
