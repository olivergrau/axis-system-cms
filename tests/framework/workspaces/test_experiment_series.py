from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from axis.framework.workspaces.experiment_series import (
    load_experiment_series,
)


def test_load_experiment_series_success(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "experiment.yaml").write_text(yaml.dump({
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
    }))

    series = load_experiment_series(ws)
    assert series.workflow_type == "experiment_series"
    assert len(series.experiments) == 1
    assert series.experiments[0].id == "exp_01"


def test_load_experiment_series_rejects_duplicate_ids(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "experiment.yaml").write_text(yaml.dump({
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
    }))

    with pytest.raises(ValueError, match="experiment IDs must be unique"):
        load_experiment_series(ws)


def test_load_experiment_series_rejects_no_enabled_experiments(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "experiment.yaml").write_text(yaml.dump({
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
    }))

    with pytest.raises(ValueError, match="at least one experiment must be enabled"):
        load_experiment_series(ws)
