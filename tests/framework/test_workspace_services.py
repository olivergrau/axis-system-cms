"""Tests for workspace service layer — WP-07."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from axis.framework.workspaces.services.run_service import (
    WorkspaceRunService,
)
from axis.framework.workspaces.services.compare_service import (
    WorkspaceCompareService,
)
from axis.framework.workspaces.services.inspection_service import (
    WorkspaceInspectionService,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_run_service(execute_fn=None, sync_fn=None):
    return WorkspaceRunService(
        execute_fn=execute_fn or MagicMock(return_value=[]),
        sync_fn=sync_fn or MagicMock(),
        set_candidate_config_fn=MagicMock(),
        load_yaml_roundtrip_fn=MagicMock(),
        save_yaml_roundtrip_fn=MagicMock(),
    )


def _make_compare_service(compare_fn=None, sync_fn=None):
    return WorkspaceCompareService(
        compare_fn=compare_fn or MagicMock(),
        sync_fn=sync_fn or MagicMock(),
    )


def _make_inspection_service(
    summarize_fn=None, check_fn=None, drift_fn=None, sweep_result_fn=None,
):
    return WorkspaceInspectionService(
        summarize_fn=summarize_fn or MagicMock(),
        check_fn=check_fn or MagicMock(),
        drift_fn=drift_fn or MagicMock(return_value=[]),
        sweep_result_fn=sweep_result_fn or MagicMock(),
    )


# ---------------------------------------------------------------------------
# Constructor injection
# ---------------------------------------------------------------------------

class TestRunServiceInjection:
    """RunService delegates to injected callables."""

    def test_execute_calls_execute_fn(self) -> None:
        execute_fn = MagicMock(return_value=[])
        sync_fn = MagicMock()
        svc = WorkspaceRunService(
            execute_fn=execute_fn, sync_fn=sync_fn,
            set_candidate_config_fn=MagicMock(),
            load_yaml_roundtrip_fn=MagicMock(),
            save_yaml_roundtrip_fn=MagicMock(),
        )

        result = svc.execute(Path("/ws"))
        execute_fn.assert_called_once_with(Path("/ws"), run_filter=None)
        assert result == []

    def test_execute_calls_sync_fn_per_result(self) -> None:
        @dataclass
        class FakeRunResult:
            run_id: str

        @dataclass
        class FakeConfig:
            system_type: str = "sys_a"

            class experiment_type:
                value = "single_run"

        @dataclass
        class FakeExpResult:
            experiment_id: str = "exp-001"
            run_results: tuple = ()
            experiment_config: object = None
            summary: object = None

        @dataclass
        class FakeExecResult:
            experiment_result: object = None
            role: str = "primary"
            config_path: str = "configs/a.yaml"

        config = FakeConfig()
        summary = MagicMock(num_runs=1)
        exp_result = FakeExpResult(
            run_results=(FakeRunResult("run-0000"),),
            experiment_config=config,
            summary=summary,
        )
        exec_result = FakeExecResult(experiment_result=exp_result)

        execute_fn = MagicMock(return_value=[exec_result])
        sync_fn = MagicMock()
        svc = WorkspaceRunService(
            execute_fn=execute_fn, sync_fn=sync_fn,
            set_candidate_config_fn=MagicMock(),
            load_yaml_roundtrip_fn=MagicMock(),
            save_yaml_roundtrip_fn=MagicMock(),
        )

        summaries = svc.execute(Path("/ws"))
        sync_fn.assert_called_once()
        assert len(summaries) == 1
        assert summaries[0].experiment_id == "exp-001"


class TestCompareServiceInjection:
    """CompareService delegates to injected callables."""

    def test_compare_calls_both_fns(self) -> None:
        envelope = MagicMock(comparison_number=1)
        compare_fn = MagicMock(return_value=(envelope, "comparisons/c-001.json"))
        sync_fn = MagicMock()
        svc = WorkspaceCompareService(compare_fn=compare_fn, sync_fn=sync_fn)

        result = svc.compare(Path("/ws"))
        compare_fn.assert_called_once()
        sync_fn.assert_called_once_with(Path("/ws"), "comparisons/c-001.json")
        assert result.comparison_number == 1
        assert result.output_path == "comparisons/c-001.json"


class TestInspectionServiceInjection:
    """InspectionService delegates to injected callables."""

    def test_summarize_delegates(self) -> None:
        summarize_fn = MagicMock(return_value="summary")
        svc = _make_inspection_service(summarize_fn=summarize_fn)
        assert svc.summarize(Path("/ws")) == "summary"
        summarize_fn.assert_called_once_with(Path("/ws"))

    def test_check_delegates(self) -> None:
        check_fn = MagicMock(return_value="result")
        drift_fn = MagicMock(return_value=["issue"])
        svc = _make_inspection_service(check_fn=check_fn, drift_fn=drift_fn)
        result, drift = svc.check(Path("/ws"))
        assert result == "result"
        assert drift == ["issue"]

    def test_sweep_result_delegates(self) -> None:
        sweep_fn = MagicMock(return_value={"key": "val"})
        svc = _make_inspection_service(sweep_result_fn=sweep_fn)
        assert svc.sweep_result(Path("/ws"), experiment="e1") == {"key": "val"}
        sweep_fn.assert_called_once_with(Path("/ws"), experiment="e1")


# ---------------------------------------------------------------------------
# set_candidate
# ---------------------------------------------------------------------------

class TestSetCandidate:
    """RunService.set_candidate delegates to manifest mutator."""

    def _make_real_run_service(self):
        """Create a run service with real yaml IO + mutator for set_candidate."""
        from axis.framework.workspaces.manifest_mutator import set_candidate_config
        from axis.framework.workspaces.sync import (
            _load_yaml_roundtrip,
            _save_yaml_roundtrip,
        )
        return WorkspaceRunService(
            execute_fn=MagicMock(return_value=[]),
            sync_fn=MagicMock(),
            set_candidate_config_fn=set_candidate_config,
            load_yaml_roundtrip_fn=_load_yaml_roundtrip,
            save_yaml_roundtrip_fn=_save_yaml_roundtrip,
        )

    def test_set_candidate_updates_manifest(self, tmp_path: Path) -> None:
        import yaml

        ws = tmp_path / "my_ws"
        ws.mkdir()
        configs_dir = ws / "configs"
        configs_dir.mkdir()
        (configs_dir / "candidate.yaml").write_text("system_type: sys_a")
        (ws / "workspace.yaml").write_text(yaml.dump({
            "workspace_type": "system_development",
            "primary_configs": ["configs/baseline.yaml"],
        }))

        svc = self._make_real_run_service()
        svc.set_candidate(ws, "configs/candidate.yaml")

        data = yaml.safe_load((ws / "workspace.yaml").read_text())
        assert data["candidate_config"] == "configs/candidate.yaml"
        assert "configs/candidate.yaml" in data["primary_configs"]

    def test_set_candidate_rejects_non_dev(self, tmp_path: Path) -> None:
        import yaml

        ws = tmp_path / "my_ws"
        ws.mkdir()
        (ws / "workspace.yaml").write_text(yaml.dump({
            "workspace_type": "single_system",
        }))
        (ws / "configs").mkdir()
        (ws / "configs" / "c.yaml").write_text("x: 1")

        svc = self._make_real_run_service()
        with pytest.raises(ValueError, match="development"):
            svc.set_candidate(ws, "configs/c.yaml")

    def test_set_candidate_rejects_missing_config(self, tmp_path: Path) -> None:
        import yaml

        ws = tmp_path / "my_ws"
        ws.mkdir()
        (ws / "workspace.yaml").write_text(yaml.dump({
            "workspace_type": "system_development",
        }))

        svc = self._make_real_run_service()
        with pytest.raises(ValueError, match="does not exist"):
            svc.set_candidate(ws, "configs/nope.yaml")

    def test_set_candidate_uses_injected_fns(self) -> None:
        """Verify set_candidate calls the injected functions, not imports."""
        load_fn = MagicMock(return_value=("yaml_obj", {
            "workspace_type": "system_development",
        }))
        save_fn = MagicMock()
        mutate_fn = MagicMock()
        svc = WorkspaceRunService(
            execute_fn=MagicMock(return_value=[]),
            sync_fn=MagicMock(),
            set_candidate_config_fn=mutate_fn,
            load_yaml_roundtrip_fn=load_fn,
            save_yaml_roundtrip_fn=save_fn,
        )
        ws = Path("/fake/ws")
        # We need the config file "to exist" — mock Path.exists
        import unittest.mock
        with unittest.mock.patch.object(Path, "exists", return_value=True):
            svc.set_candidate(ws, "configs/c.yaml")

        load_fn.assert_called_once()
        mutate_fn.assert_called_once()
        save_fn.assert_called_once()


# ---------------------------------------------------------------------------
# Context integration
# ---------------------------------------------------------------------------

class TestContextIncludesServices:
    """CLIContext built by build_context exposes workspace services."""

    def test_services_present(self, tmp_path: Path) -> None:
        from axis.framework.cli.context import build_context

        ctx = build_context(tmp_path)
        assert isinstance(ctx.run_service, WorkspaceRunService)
        assert isinstance(ctx.compare_service, WorkspaceCompareService)
        assert isinstance(ctx.inspection_service, WorkspaceInspectionService)

    def test_services_have_injected_deps(self, tmp_path: Path) -> None:
        """Services must have real collaborators, not None."""
        from axis.framework.cli.context import build_context

        ctx = build_context(tmp_path)
        assert ctx.run_service._execute_fn is not None
        assert ctx.run_service._sync_fn is not None
        assert ctx.run_service._set_candidate_config_fn is not None
        assert ctx.run_service._load_yaml_roundtrip_fn is not None
        assert ctx.run_service._save_yaml_roundtrip_fn is not None
        assert ctx.compare_service._compare_fn is not None
        assert ctx.compare_service._sync_fn is not None
        assert ctx.inspection_service._summarize_fn is not None
        assert ctx.inspection_service._check_fn is not None
        assert ctx.inspection_service._drift_fn is not None
        assert ctx.inspection_service._sweep_result_fn is not None
