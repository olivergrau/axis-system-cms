from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import yaml

from axis.framework.workspaces.experiment_series import (
    load_experiment_series,
)
from axis.framework.workspaces.services.experiment_series_service import (
    WorkspaceExperimentSeriesService,
)
from axis.framework.workspaces.types import WorkspaceType


def _write_registered_series(ws: Path, data: dict, *, series_id: str = "series-a") -> None:
    (ws / "series" / series_id).mkdir(parents=True, exist_ok=True)
    (ws / "series" / series_id / "experiment.yaml").write_text(yaml.dump(data))
    (ws / "workspace.yaml").write_text(yaml.dump({
        "workspace_id": "ws",
        "title": "Workspace",
        "workspace_class": "investigation",
        "workspace_type": data["workspace_type"],
        "status": "draft",
        "lifecycle_stage": "idea",
        "created_at": "2026-04-30",
        "question": "Q",
        "reference_system": "system_a" if data["workspace_type"] == "system_comparison" else None,
        "candidate_system": "system_a" if data["workspace_type"] == "system_comparison" else None,
        "system_under_test": "system_a" if data["workspace_type"] == "single_system" else None,
        "experiment_series": {
            "entries": [
                {
                    "id": series_id,
                    "path": f"series/{series_id}/experiment.yaml",
                    "title": "Series A",
                },
            ],
        },
    }, sort_keys=False))


def test_load_experiment_series_success(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_registered_series(ws, {
        "version": 1,
        "workflow_type": "experiment_series",
        "workspace_type": "system_comparison",
        "experiments": [
            {
                "id": "exp_01",
                "title": "First",
                "enabled": True,
                "candidate_config_delta": {
                    "system": {"prediction": {"alpha": 0.1}},
                },
                },
            ],
    })

    series = load_experiment_series(ws, series_id="series-a")
    assert series.workflow_type == "experiment_series"
    assert len(series.experiments) == 1
    assert series.experiments[0].id == "exp_01"


def test_load_experiment_series_accepts_optional_reference_delta(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_registered_series(ws, {
        "version": 1,
        "workflow_type": "experiment_series",
        "workspace_type": "system_comparison",
        "experiments": [
            {
                "id": "exp_01",
                "title": "Shared world change",
                "enabled": True,
                "reference_config_delta": {
                    "world": {"grid_width": 24},
                },
                "candidate_config_delta": {
                    "world": {"grid_width": 24},
                },
            },
        ],
    })

    series = load_experiment_series(ws, series_id="series-a")
    assert series.experiments[0].reference_config_delta == {
        "world": {"grid_width": 24},
    }


def test_load_experiment_series_rejects_duplicate_ids(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_registered_series(ws, {
        "version": 1,
        "workflow_type": "experiment_series",
        "workspace_type": "system_comparison",
        "experiments": [
            {
                "id": "exp_01",
                "title": "First",
                "enabled": True,
                "candidate_config_delta": {"system": {"a": 1}},
            },
            {
                "id": "exp_01",
                "title": "Second",
                "enabled": True,
                "candidate_config_delta": {"system": {"a": 2}},
                },
            ],
    })

    with pytest.raises(ValueError, match="experiment IDs must be unique"):
        load_experiment_series(ws, series_id="series-a")


def test_load_experiment_series_rejects_no_enabled_experiments(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_registered_series(ws, {
        "version": 1,
        "workflow_type": "experiment_series",
        "workspace_type": "system_comparison",
        "experiments": [
            {
                "id": "exp_01",
                "title": "First",
                "enabled": False,
                "candidate_config_delta": {"system": {"a": 1}},
                },
            ],
    })

    with pytest.raises(ValueError, match="at least one experiment must be enabled"):
        load_experiment_series(ws, series_id="series-a")


def test_run_series_removes_empty_measurement_dir_on_failure(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()

    service = WorkspaceExperimentSeriesService(
        measurement_service=object(),
        load_manifest_fn=lambda path: SimpleNamespace(
            workspace_type=WorkspaceType.SYSTEM_COMPARISON,
            measurement_workflow=None,
            workspace_id="ws",
        ),
        load_experiment_series_fn=lambda path, series_id: SimpleNamespace(
            workspace_type=WorkspaceType.SYSTEM_COMPARISON,
            base_configs=None,
            defaults=SimpleNamespace(
                labels=SimpleNamespace(measurement_label_pattern="{experiment_id}"),
            ),
            experiments=[
                SimpleNamespace(
                    id="exp_01",
                    title="Experiment 01",
                    label=None,
                    enabled=True,
                    notes=None,
                    reference_config_delta=None,
                    candidate_config_delta={},
                ),
            ],
        ),
        export_measurement_reports_fn=MagicMock(),
    )

    series_root = ws / "series" / "series-a"
    results_root = series_root / "results"
    measurements_root = series_root / "measurements"
    comparisons_root = series_root / "comparisons"
    results_root.mkdir(parents=True)
    measurements_root.mkdir(parents=True)
    comparisons_root.mkdir(parents=True)

    with (
        patch(
            "axis.framework.workspaces.series_paths.resolve_series_paths",
            return_value=SimpleNamespace(
                results_root=results_root,
                measurements_root=measurements_root,
                comparisons_root=comparisons_root,
            ),
        ),
        patch(
            "axis.framework.workspaces.config_materialization.resolve_base_config_paths",
            return_value={"reference": "ref.yaml", "candidate": "cand.yaml"},
        ),
        patch(
            "axis.framework.workspaces.config_materialization.materialize_candidate_config",
            return_value=SimpleNamespace(temp_config_path="tmp/candidate.yaml"),
        ),
        patch(
            "axis.framework.workspaces.execute.execute_workspace",
            side_effect=RuntimeError("boom"),
        ),
    ):
        with pytest.raises(RuntimeError, match="boom"):
            service.run_series(ws, series_id="series-a")

    assert not (measurements_root / "experiment_1").exists()
