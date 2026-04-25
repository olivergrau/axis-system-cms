"""Tests for workspace service layer — WP-07."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from unittest.mock import MagicMock, call, patch

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
from axis.framework.workspaces.services.workflow_service import (
    WorkspaceWorkflowService,
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


def _make_workflow_service(
    close_workspace_fn=None,
    load_yaml_roundtrip_fn=None,
    save_yaml_roundtrip_fn=None,
):
    return WorkspaceWorkflowService(
        close_workspace_fn=close_workspace_fn or MagicMock(),
        load_yaml_roundtrip_fn=load_yaml_roundtrip_fn or MagicMock(),
        save_yaml_roundtrip_fn=save_yaml_roundtrip_fn or MagicMock(),
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

        with (
            patch(
                "axis.framework.workspaces.types.load_manifest",
                return_value=MagicMock(primary_results=[]),
            ),
            patch(
                "axis.framework.workspaces.resolution.resolve_run_targets",
                return_value=MagicMock(targets=[]),
            ),
        ):
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

        fake_plan = MagicMock(targets=[])
        fake_manifest = MagicMock(primary_results=[])
        with (
            patch(
                "axis.framework.workspaces.types.load_manifest",
                return_value=fake_manifest,
            ),
            patch(
                "axis.framework.workspaces.resolution.resolve_run_targets",
                return_value=fake_plan,
            ),
        ):
            summaries = svc.execute(Path("/ws"))
        sync_fn.assert_called_once()
        assert len(summaries) == 1
        assert summaries[0].experiment_id == "exp-001"

    def test_execute_aborts_when_config_matches_previous_comparable_result(self, tmp_path: Path) -> None:
        import yaml

        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / "configs").mkdir()
        (ws / "results" / "exp-001").mkdir(parents=True)

        config_data = {
            "system_type": "system_a",
            "experiment_type": "single_run",
            "general": {"seed": 7},
            "execution": {"max_steps": 100},
            "world": {"world_type": "grid_2d", "grid_width": 5, "grid_height": 5},
            "system": {
                "agent": {
                    "initial_energy": 50,
                    "max_energy": 100,
                    "buffer_capacity": 5,
                },
                "policy": {
                    "selection_mode": "sample",
                    "temperature": 1.0,
                    "stay_suppression": 0.1,
                    "consume_weight": 2.5,
                },
                "transition": {
                    "move_cost": 0.5,
                    "consume_cost": 0.5,
                    "stay_cost": 0.3,
                    "max_consume": 1.0,
                    "energy_gain_factor": 15.0,
                },
            },
            "num_episodes_per_run": 5,
        }
        (ws / "configs" / "baseline.yaml").write_text(yaml.dump(config_data))
        from axis.framework.cli import _load_config_file
        normalized = _load_config_file(ws / "configs" / "baseline.yaml").model_dump(mode="json")
        (ws / "results" / "exp-001" / "experiment_config.json").write_text(
            json.dumps(normalized)
        )
        (ws / "workspace.yaml").write_text(yaml.dump({
            "workspace_id": "ws",
            "title": "Workspace",
            "workspace_class": "investigation",
            "workspace_type": "single_system",
            "status": "draft",
            "lifecycle_stage": "idea",
            "created_at": "2026-04-22",
            "question": "Q?",
            "system_under_test": "system_a",
            "primary_configs": ["configs/baseline.yaml"],
            "primary_results": [
                {
                    "path": "results/exp-001",
                    "role": "system_under_test",
                    "config": "results/exp-001/experiment_config.json",
                },
            ],
        }))

        execute_fn = MagicMock(return_value=[])
        svc = _make_run_service(execute_fn=execute_fn)

        fake_target = MagicMock(config_path="configs/baseline.yaml", role="system_under_test")
        with patch(
            "axis.framework.workspaces.resolution.resolve_run_targets",
            return_value=MagicMock(targets=[fake_target]),
        ):
            with pytest.raises(ValueError, match="no config changes detected"):
                svc.execute(ws)

        execute_fn.assert_not_called()

    def test_execute_allows_comparison_when_only_one_side_changes(
        self, tmp_path: Path,
    ) -> None:
        import yaml

        from axis.framework.cli import _load_config_file

        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / "configs").mkdir()
        (ws / "results" / "exp-ref").mkdir(parents=True)
        (ws / "results" / "exp-cand").mkdir(parents=True)

        reference_config = {
            "system_type": "system_a",
            "experiment_type": "single_run",
            "general": {"seed": 7},
            "execution": {"max_steps": 100},
            "world": {
                "world_type": "grid_2d",
                "grid_width": 5,
                "grid_height": 5,
            },
            "system": {
                "agent": {
                    "initial_energy": 50,
                    "max_energy": 100,
                    "buffer_capacity": 5,
                },
                "policy": {
                    "selection_mode": "sample",
                    "temperature": 1.0,
                    "stay_suppression": 0.1,
                    "consume_weight": 2.5,
                },
                "transition": {
                    "move_cost": 0.5,
                    "consume_cost": 0.5,
                    "stay_cost": 0.3,
                    "max_consume": 1.0,
                    "energy_gain_factor": 15.0,
                },
            },
            "num_episodes_per_run": 5,
        }
        candidate_config = dict(reference_config)
        candidate_config["num_episodes_per_run"] = 6

        (ws / "configs" / "reference.yaml").write_text(
            yaml.dump(reference_config)
        )
        (ws / "configs" / "candidate.yaml").write_text(
            yaml.dump(candidate_config)
        )

        ref_normalized = _load_config_file(
            ws / "configs" / "reference.yaml"
        ).model_dump(mode="json")
        cand_normalized = _load_config_file(
            ws / "configs" / "candidate.yaml"
        ).model_dump(mode="json")
        (ws / "results" / "exp-ref" / "experiment_config.json").write_text(
            json.dumps(ref_normalized)
        )
        (ws / "results" / "exp-cand" / "experiment_config.json").write_text(
            json.dumps({
                **cand_normalized,
                "num_episodes_per_run": 5,
            })
        )
        (ws / "workspace.yaml").write_text(yaml.dump({
            "workspace_id": "ws",
            "title": "Workspace",
            "workspace_class": "investigation",
            "workspace_type": "system_comparison",
            "status": "draft",
            "lifecycle_stage": "idea",
            "created_at": "2026-04-22",
            "question": "Q?",
            "reference_system": "system_a",
            "candidate_system": "system_a",
            "primary_configs": [
                {"path": "configs/reference.yaml", "role": "reference"},
                {"path": "configs/candidate.yaml", "role": "candidate"},
            ],
            "primary_results": [
                {
                    "path": "results/exp-ref",
                    "role": "reference",
                    "config": "results/exp-ref/experiment_config.json",
                },
                {
                    "path": "results/exp-cand",
                    "role": "candidate",
                    "config": "results/exp-cand/experiment_config.json",
                },
            ],
        }))

        execute_fn = MagicMock(return_value=[])
        svc = _make_run_service(execute_fn=execute_fn)

        fake_targets = [
            MagicMock(config_path="configs/reference.yaml", role="reference"),
            MagicMock(config_path="configs/candidate.yaml", role="candidate"),
        ]
        with patch(
            "axis.framework.workspaces.resolution.resolve_run_targets",
            return_value=MagicMock(targets=fake_targets),
        ):
            svc.execute(ws)

        execute_fn.assert_called_once()

    def test_execute_override_guard_allows_matching_previous_result(
        self, tmp_path: Path,
    ) -> None:
        import yaml

        from axis.framework.cli import _load_config_file

        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / "configs").mkdir()
        (ws / "results" / "exp-001").mkdir(parents=True)

        config_data = {
            "system_type": "system_a",
            "experiment_type": "single_run",
            "general": {"seed": 7},
            "execution": {"max_steps": 100},
            "world": {
                "world_type": "grid_2d",
                "grid_width": 5,
                "grid_height": 5,
            },
            "system": {
                "agent": {
                    "initial_energy": 50,
                    "max_energy": 100,
                    "buffer_capacity": 5,
                },
                "policy": {
                    "selection_mode": "sample",
                    "temperature": 1.0,
                    "stay_suppression": 0.1,
                    "consume_weight": 2.5,
                },
                "transition": {
                    "move_cost": 0.5,
                    "consume_cost": 0.5,
                    "stay_cost": 0.3,
                    "max_consume": 1.0,
                    "energy_gain_factor": 15.0,
                },
            },
            "num_episodes_per_run": 5,
        }
        (ws / "configs" / "baseline.yaml").write_text(yaml.dump(config_data))
        normalized = _load_config_file(
            ws / "configs" / "baseline.yaml"
        ).model_dump(mode="json")
        (ws / "results" / "exp-001" / "experiment_config.json").write_text(
            json.dumps(normalized)
        )
        (ws / "workspace.yaml").write_text(yaml.dump({
            "workspace_id": "ws",
            "title": "Workspace",
            "workspace_class": "investigation",
            "workspace_type": "single_system",
            "status": "draft",
            "lifecycle_stage": "idea",
            "created_at": "2026-04-22",
            "question": "Q?",
            "system_under_test": "system_a",
            "primary_configs": ["configs/baseline.yaml"],
            "primary_results": [
                {
                    "path": "results/exp-001",
                    "role": "system_under_test",
                    "config": "results/exp-001/experiment_config.json",
                },
            ],
        }))

        execute_fn = MagicMock(return_value=[])
        svc = _make_run_service(execute_fn=execute_fn)

        fake_target = MagicMock(
            config_path="configs/baseline.yaml",
            role="system_under_test",
        )
        with patch(
            "axis.framework.workspaces.resolution.resolve_run_targets",
            return_value=MagicMock(targets=[fake_target]),
        ):
            svc.execute(ws, override_guard=True)

        execute_fn.assert_called_once()

    def test_execute_blocks_world_only_change_without_allow_flag(
        self, tmp_path: Path,
    ) -> None:
        import yaml

        from axis.framework.cli import _load_config_file

        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / "configs").mkdir()
        (ws / "results" / "exp-001").mkdir(parents=True)

        config_data = {
            "system_type": "system_a",
            "experiment_type": "single_run",
            "general": {"seed": 7},
            "execution": {"max_steps": 100},
            "world": {"world_type": "grid_2d", "grid_width": 7, "grid_height": 5},
            "system": {
                "agent": {
                    "initial_energy": 50,
                    "max_energy": 100,
                    "buffer_capacity": 5,
                },
                "policy": {
                    "selection_mode": "sample",
                    "temperature": 1.0,
                    "stay_suppression": 0.1,
                    "consume_weight": 2.5,
                },
                "transition": {
                    "move_cost": 0.5,
                    "consume_cost": 0.5,
                    "stay_cost": 0.3,
                    "max_consume": 1.0,
                    "energy_gain_factor": 15.0,
                },
            },
            "num_episodes_per_run": 5,
        }
        (ws / "configs" / "baseline.yaml").write_text(yaml.dump(config_data))
        normalized = _load_config_file(
            ws / "configs" / "baseline.yaml"
        ).model_dump(mode="json")
        normalized["world"]["grid_width"] = 5
        (ws / "results" / "exp-001" / "experiment_config.json").write_text(
            json.dumps(normalized)
        )
        (ws / "workspace.yaml").write_text(yaml.dump({
            "workspace_id": "ws",
            "title": "Workspace",
            "workspace_class": "investigation",
            "workspace_type": "single_system",
            "status": "draft",
            "lifecycle_stage": "idea",
            "created_at": "2026-04-22",
            "question": "Q?",
            "system_under_test": "system_a",
            "primary_configs": ["configs/baseline.yaml"],
            "primary_results": [
                {
                    "path": "results/exp-001",
                    "role": "system_under_test",
                    "config": "results/exp-001/experiment_config.json",
                },
            ],
        }))

        execute_fn = MagicMock(return_value=[])
        svc = _make_run_service(execute_fn=execute_fn)

        fake_target = MagicMock(
            config_path="configs/baseline.yaml",
            role="system_under_test",
        )
        with patch(
            "axis.framework.workspaces.resolution.resolve_run_targets",
            return_value=MagicMock(targets=[fake_target]),
        ):
            with pytest.raises(ValueError, match="no config changes detected"):
                svc.execute(ws)

        execute_fn.assert_not_called()

    def test_execute_allows_world_only_change_with_allow_flag(
        self, tmp_path: Path,
    ) -> None:
        import yaml

        from axis.framework.cli import _load_config_file

        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / "configs").mkdir()
        (ws / "results" / "exp-001").mkdir(parents=True)

        config_data = {
            "system_type": "system_a",
            "experiment_type": "single_run",
            "general": {"seed": 7},
            "execution": {"max_steps": 100},
            "world": {"world_type": "grid_2d", "grid_width": 7, "grid_height": 5},
            "system": {
                "agent": {
                    "initial_energy": 50,
                    "max_energy": 100,
                    "buffer_capacity": 5,
                },
                "policy": {
                    "selection_mode": "sample",
                    "temperature": 1.0,
                    "stay_suppression": 0.1,
                    "consume_weight": 2.5,
                },
                "transition": {
                    "move_cost": 0.5,
                    "consume_cost": 0.5,
                    "stay_cost": 0.3,
                    "max_consume": 1.0,
                    "energy_gain_factor": 15.0,
                },
            },
            "num_episodes_per_run": 5,
        }
        (ws / "configs" / "baseline.yaml").write_text(yaml.dump(config_data))
        normalized = _load_config_file(
            ws / "configs" / "baseline.yaml"
        ).model_dump(mode="json")
        normalized["world"]["grid_width"] = 5
        (ws / "results" / "exp-001" / "experiment_config.json").write_text(
            json.dumps(normalized)
        )
        (ws / "workspace.yaml").write_text(yaml.dump({
            "workspace_id": "ws",
            "title": "Workspace",
            "workspace_class": "investigation",
            "workspace_type": "single_system",
            "status": "draft",
            "lifecycle_stage": "idea",
            "created_at": "2026-04-22",
            "question": "Q?",
            "system_under_test": "system_a",
            "primary_configs": ["configs/baseline.yaml"],
            "primary_results": [
                {
                    "path": "results/exp-001",
                    "role": "system_under_test",
                    "config": "results/exp-001/experiment_config.json",
                },
            ],
        }))

        execute_fn = MagicMock(return_value=[])
        svc = _make_run_service(execute_fn=execute_fn)

        fake_target = MagicMock(
            config_path="configs/baseline.yaml",
            role="system_under_test",
        )
        with patch(
            "axis.framework.workspaces.resolution.resolve_run_targets",
            return_value=MagicMock(targets=[fake_target]),
        ):
            svc.execute(ws, allow_world_changes=True)

        execute_fn.assert_called_once()

    def test_execute_rejects_closed_workspace(self, tmp_path: Path) -> None:
        import yaml

        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / "workspace.yaml").write_text(yaml.dump({
            "workspace_id": "ws",
            "title": "Workspace",
            "workspace_class": "investigation",
            "workspace_type": "single_system",
            "status": "closed",
            "lifecycle_stage": "final",
            "created_at": "2026-04-22",
            "question": "Q?",
            "system_under_test": "system_a",
        }))

        execute_fn = MagicMock(return_value=[])
        svc = _make_run_service(execute_fn=execute_fn)

        with pytest.raises(ValueError, match="no further executions"):
            svc.execute(ws)

        execute_fn.assert_not_called()

    def test_set_candidate_rejects_closed_workspace(self, tmp_path: Path) -> None:
        import yaml

        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / "configs").mkdir()
        (ws / "configs" / "candidate.yaml").write_text("system_type: system_a\n")
        (ws / "workspace.yaml").write_text(yaml.dump({
            "workspace_id": "ws",
            "title": "Workspace",
            "workspace_class": "development",
            "workspace_type": "system_development",
            "status": "closed",
            "lifecycle_stage": "final",
            "created_at": "2026-04-22",
            "development_goal": "Build it",
            "artifact_kind": "system",
            "artifact_under_development": "system_d",
        }))

        svc = _make_run_service()

        with pytest.raises(ValueError, match="candidate config cannot be changed"):
            svc.set_candidate(ws, "configs/candidate.yaml")


class TestCompareServiceInjection:
    """CompareService delegates to injected callables."""

    def test_compare_calls_both_fns(self) -> None:
        envelope = MagicMock(comparison_number=1)
        compare_fn = MagicMock(return_value=(envelope, "comparisons/c-001.json"))
        sync_fn = MagicMock()
        svc = WorkspaceCompareService(compare_fn=compare_fn, sync_fn=sync_fn)

        with patch(
            "axis.framework.workspaces.types.load_manifest",
            return_value=MagicMock(status=MagicMock(value="draft")),
        ):
            result = svc.compare(Path("/ws"))
        compare_fn.assert_called_once()
        sync_fn.assert_called_once_with(Path("/ws"), "comparisons/c-001.json")
        assert result.comparison_number == 1
        assert result.output_path == "comparisons/c-001.json"

    def test_compare_rejects_closed_workspace(self, tmp_path: Path) -> None:
        import yaml

        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / "workspace.yaml").write_text(yaml.dump({
            "workspace_id": "ws",
            "title": "Workspace",
            "workspace_class": "investigation",
            "workspace_type": "single_system",
            "status": "closed",
            "lifecycle_stage": "final",
            "created_at": "2026-04-22",
            "question": "Q?",
            "system_under_test": "system_a",
        }))

        compare_fn = MagicMock()
        svc = _make_compare_service(compare_fn=compare_fn)

        with pytest.raises(ValueError, match="no further comparisons"):
            svc.compare(ws)

        compare_fn.assert_not_called()


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


class TestWorkflowServiceInjection:

    def test_close_updates_manifest_via_injected_collaborators(self) -> None:
        yaml_obj = object()
        data = {
            "status": "draft",
            "lifecycle_stage": "implementation",
        }
        load_fn = MagicMock(return_value=(yaml_obj, data))
        close_fn = MagicMock(side_effect=lambda d: d.update({
            "status": "closed",
            "lifecycle_stage": "final",
        }))
        save_fn = MagicMock()
        svc = _make_workflow_service(
            close_workspace_fn=close_fn,
            load_yaml_roundtrip_fn=load_fn,
            save_yaml_roundtrip_fn=save_fn,
        )

        result = svc.close(Path("/ws"))

        load_fn.assert_called_once_with(Path("/ws") / "workspace.yaml")
        close_fn.assert_called_once_with(data)
        save_fn.assert_called_once_with(Path("/ws") / "workspace.yaml", yaml_obj, data)
        assert result.status == "closed"
        assert result.lifecycle_stage == "final"


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

    def _valid_dev_manifest(self) -> dict:
        return {
            "workspace_id": "my_ws",
            "title": "Workspace",
            "workspace_class": "development",
            "workspace_type": "system_development",
            "status": "draft",
            "lifecycle_stage": "implementation",
            "created_at": "2026-04-22",
            "development_goal": "Build it",
            "artifact_kind": "system",
            "artifact_under_development": "system_d",
        }

    def test_set_candidate_updates_manifest(self, tmp_path: Path) -> None:
        import yaml

        ws = tmp_path / "my_ws"
        ws.mkdir()
        configs_dir = ws / "configs"
        configs_dir.mkdir()
        (configs_dir / "candidate.yaml").write_text("system_type: sys_a")
        data = self._valid_dev_manifest()
        data["primary_configs"] = ["configs/baseline.yaml"]
        (ws / "workspace.yaml").write_text(yaml.dump(data))

        svc = self._make_real_run_service()
        svc.set_candidate(ws, "configs/candidate.yaml")

        data = yaml.safe_load((ws / "workspace.yaml").read_text())
        assert data["candidate_config"] == "configs/candidate.yaml"
        assert {
            "path": "configs/candidate.yaml",
            "role": "candidate",
        } in data["primary_configs"]

    def test_set_candidate_rejects_non_dev(self, tmp_path: Path) -> None:
        import yaml

        ws = tmp_path / "my_ws"
        ws.mkdir()
        bad_manifest = self._valid_dev_manifest()
        bad_manifest["workspace_class"] = "investigation"
        bad_manifest["workspace_type"] = "single_system"
        bad_manifest["question"] = "Q?"
        bad_manifest.pop("development_goal")
        bad_manifest.pop("artifact_kind")
        bad_manifest.pop("artifact_under_development")
        bad_manifest["system_under_test"] = "system_a"
        (ws / "workspace.yaml").write_text(yaml.dump(bad_manifest))
        (ws / "configs").mkdir()
        (ws / "configs" / "c.yaml").write_text("x: 1")

        svc = self._make_real_run_service()
        with pytest.raises(ValueError, match="development"):
            svc.set_candidate(ws, "configs/c.yaml")

    def test_set_candidate_rejects_missing_config(self, tmp_path: Path) -> None:
        import yaml

        ws = tmp_path / "my_ws"
        ws.mkdir()
        (ws / "workspace.yaml").write_text(yaml.dump(self._valid_dev_manifest()))

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
        with (
            unittest.mock.patch.object(Path, "exists", return_value=True),
            patch(
                "axis.framework.workspaces.types.load_manifest",
                return_value=MagicMock(status=MagicMock(value="draft")),
            ),
        ):
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
        assert isinstance(ctx.workflow_service, WorkspaceWorkflowService)

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
        assert ctx.workflow_service._close_workspace_fn is not None
        assert ctx.workflow_service._load_yaml_roundtrip_fn is not None
        assert ctx.workflow_service._save_yaml_roundtrip_fn is not None
