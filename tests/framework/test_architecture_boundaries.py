"""Architectural boundary tests — WP-11.

These tests verify that the refactored architecture boundaries are
maintained, preventing accidental drift back to monolithic patterns.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"


class TestCLIPackageStructure:
    """Verify CLI is a package with proper module split."""

    def test_cli_is_package(self) -> None:
        cli_dir = SRC / "axis" / "framework" / "cli"
        assert cli_dir.is_dir()
        assert (cli_dir / "__init__.py").is_file()

    def test_handlers_removed(self) -> None:
        """The temporary _handlers.py should no longer exist."""
        assert not (SRC / "axis" / "framework" /
                    "cli" / "_handlers.py").exists()

    def test_command_modules_exist(self) -> None:
        commands_dir = SRC / "axis" / "framework" / "cli" / "commands"
        for name in ("experiments", "runs", "compare", "visualize", "workspaces"):
            assert (commands_dir /
                    f"{name}.py").is_file(), f"Missing {name}.py"

    def test_dispatch_does_not_import_handlers(self) -> None:
        """dispatch.py should import from commands/, not _handlers."""
        source = (SRC / "axis" / "framework" /
                  "cli" / "dispatch.py").read_text()
        assert "_handlers" not in source


class TestCompositionRoot:
    """Verify the composition root assembles all expected dependencies."""

    def test_main_entrypoint_importable(self) -> None:
        from axis.framework.cli import main
        assert callable(main)

    def test_build_context_returns_services(self, tmp_path: Path) -> None:
        from axis.framework.cli.context import build_context
        from axis.plugins import discover_plugins

        discover_plugins()
        ctx = build_context(tmp_path)

        assert ctx.repo is not None
        assert ctx.run_service is not None
        assert ctx.compare_service is not None
        assert ctx.inspection_service is not None
        assert len(ctx.catalogs) > 0


class TestCatalogsBridged:
    """Verify catalogs are populated from global registries."""

    def test_all_catalog_domains_present(self) -> None:
        from axis.plugins import discover_plugins
        from axis.framework.catalogs import build_catalogs_from_registries

        discover_plugins()
        catalogs = build_catalogs_from_registries()

        expected = {"systems", "worlds", "world_vis", "system_vis",
                    "comparison_extensions"}
        assert set(catalogs.keys()) == expected


class TestHandlerContractStable:
    """Verify workspace handlers have stable signatures (no inspect needed)."""

    def test_no_inspect_in_resolution(self) -> None:
        source = (
            SRC / "axis" / "framework" / "workspaces" / "resolution.py"
        ).read_text()
        assert "inspect.signature" not in source
        assert "import inspect" not in source

    def test_all_handlers_accept_run_filter(self) -> None:
        from axis.framework.workspaces.handler import get_handler
        from axis.framework.workspaces.types import WorkspaceType
        import inspect

        for wt in WorkspaceType:
            handler = get_handler(wt)
            sig = inspect.signature(handler.resolve_run_targets)
            assert "run_filter" in sig.parameters, (
                f"{wt.value} handler missing run_filter parameter"
            )


class TestManifestMutatorExists:
    """Verify manifest mutation layer is in place."""

    def test_mutator_module_importable(self) -> None:
        from axis.framework.workspaces import manifest_mutator
        assert hasattr(manifest_mutator, "append_primary_result")
        assert hasattr(manifest_mutator, "append_primary_comparison")
        assert hasattr(manifest_mutator, "update_development_results")
        assert hasattr(manifest_mutator,
                       "update_current_validation_comparison")
        assert hasattr(manifest_mutator, "set_candidate_config")
        assert hasattr(manifest_mutator, "set_primary_configs")
        assert hasattr(manifest_mutator, "merge_scaffold_fields")

    def test_sync_delegates_to_mutator(self) -> None:
        """sync.py should import from manifest_mutator."""
        source = (
            SRC / "axis" / "framework" / "workspaces" / "sync.py"
        ).read_text()
        assert "manifest_mutator" in source


class TestCommandModuleBoundaries:
    """Workspace command module must not contain business logic."""

    def test_workspaces_commands_no_direct_yaml_mutation(self) -> None:
        """workspace commands must not import yaml for direct mutation."""
        source = (
            SRC / "axis" / "framework" / "cli" / "commands" / "workspaces.py"
        ).read_text()
        tree = ast.parse(source)
        # Check that no function imports yaml (the old set_candidate pattern)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "yaml", (
                        "workspaces.py should not import yaml directly"
                    )

    def test_workspaces_commands_no_execute_workspace_import(self) -> None:
        """Command module must not import execute_workspace directly."""
        source = (
            SRC / "axis" / "framework" / "cli" / "commands" / "workspaces.py"
        ).read_text()
        assert "execute_workspace" not in source
        assert "sync_manifest_after_run" not in source
        assert "compare_workspace" not in source
        assert "sync_manifest_after_compare" not in source

    def test_workspaces_commands_no_service_fallbacks(self) -> None:
        """No 'if service is not None ... else ...' fallback pattern."""
        source = (
            SRC / "axis" / "framework" / "cli" / "commands" / "workspaces.py"
        ).read_text()
        assert "if run_service is not None" not in source
        assert "if compare_service is not None" not in source
        assert "if inspection_service is not None" not in source


class TestCatalogMigration:
    """Verify catalog parameters are threaded through high-level consumers."""

    def test_run_executor_accepts_system_catalog(self) -> None:
        import inspect
        from axis.framework.run import RunExecutor
        sig = inspect.signature(RunExecutor.__init__)
        assert "system_catalog" in sig.parameters

    def test_setup_episode_accepts_world_catalog(self) -> None:
        import inspect
        from axis.framework.runner import setup_episode
        sig = inspect.signature(setup_episode)
        assert "world_catalog" in sig.parameters

    def test_launch_visualization_accepts_catalogs(self) -> None:
        import inspect
        from axis.visualization.launch import launch_visualization
        sig = inspect.signature(launch_visualization)
        assert "world_vis_catalog" in sig.parameters
        assert "system_vis_catalog" in sig.parameters

    def test_compare_episode_traces_accepts_extension_catalog(self) -> None:
        import inspect
        from axis.framework.comparison.compare import compare_episode_traces
        sig = inspect.signature(compare_episode_traces)
        assert "extension_catalog" in sig.parameters

    def test_compare_runs_accepts_extension_catalog(self) -> None:
        import inspect
        from axis.framework.comparison.compare import compare_runs
        sig = inspect.signature(compare_runs)
        assert "extension_catalog" in sig.parameters

    def test_experiment_executor_accepts_catalogs(self) -> None:
        import inspect
        from axis.framework.experiment import ExperimentExecutor
        sig = inspect.signature(ExperimentExecutor.__init__)
        assert "system_catalog" in sig.parameters
        assert "world_catalog" in sig.parameters

    def test_cmd_visualize_accepts_catalogs(self) -> None:
        import inspect
        from axis.framework.cli.commands.visualize import cmd_visualize
        sig = inspect.signature(cmd_visualize)
        assert "catalogs" in sig.parameters

    def test_cmd_compare_accepts_catalogs(self) -> None:
        import inspect
        from axis.framework.cli.commands.compare import cmd_compare
        sig = inspect.signature(cmd_compare)
        assert "catalogs" in sig.parameters

    def test_cmd_experiments_run_accepts_catalogs(self) -> None:
        import inspect
        from axis.framework.cli.commands.experiments import cmd_experiments_run
        sig = inspect.signature(cmd_experiments_run)
        assert "catalogs" in sig.parameters


class TestScaffoldUseMutator:
    """Verify scaffold delegates manifest mutations to mutator."""

    def test_scaffold_imports_mutator(self) -> None:
        source = (
            SRC / "axis" / "framework" / "workspaces" / "scaffold.py"
        ).read_text()
        assert "manifest_mutator" in source
        assert "set_primary_configs" in source
        assert "merge_scaffold_fields" in source
