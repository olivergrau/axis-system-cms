from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from axis.framework.workspaces.experiment_series import (
    load_experiment_series,
)


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
