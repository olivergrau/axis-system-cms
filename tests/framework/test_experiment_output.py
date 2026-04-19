"""Tests for the Experiment Output abstraction (WP-10)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from axis.framework.experiment_output import (
    ExperimentOutputForm,
    PointExperimentOutput,
    SweepExperimentOutput,
    load_experiment_output,
    output_form_for_type,
)
from axis.framework.persistence import (
    ExperimentMetadata,
    ExperimentRepository,
    ExperimentStatus,
    RunMetadata,
    RunStatus,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_point_experiment(repo: ExperimentRepository, eid: str = "exp-001") -> None:
    """Create a minimal persisted point experiment."""
    repo.create_experiment_dir(eid)
    repo.save_experiment_metadata(
        eid,
        ExperimentMetadata(
            experiment_id=eid,
            created_at="2025-01-01T00:00:00",
            experiment_type="single_run",
            system_type="system_a",
            output_form="point",
            primary_run_id="run-0000",
        ),
    )
    repo.save_experiment_status(eid, ExperimentStatus.COMPLETED)
    repo.create_run_dir(eid, "run-0000")
    repo.save_run_metadata(
        eid, "run-0000",
        RunMetadata(
            run_id="run-0000",
            experiment_id=eid,
            variation_description="baseline",
            created_at="2025-01-01T00:00:00",
            base_seed=42,
        ),
    )
    repo.save_run_status(eid, "run-0000", RunStatus.COMPLETED)


def _create_sweep_experiment(repo: ExperimentRepository, eid: str = "exp-002") -> None:
    """Create a minimal persisted sweep experiment."""
    repo.create_experiment_dir(eid)
    repo.save_experiment_metadata(
        eid,
        ExperimentMetadata(
            experiment_id=eid,
            created_at="2025-01-01T00:00:00",
            experiment_type="ofat",
            system_type="system_a",
            output_form="sweep",
            baseline_run_id="run-0000",
        ),
    )
    repo.save_experiment_status(eid, ExperimentStatus.COMPLETED)
    for i in range(3):
        rid = f"run-{i:04d}"
        repo.create_run_dir(eid, rid)
        repo.save_run_metadata(
            eid, rid,
            RunMetadata(
                run_id=rid,
                experiment_id=eid,
                variation_description=f"param={i}",
                created_at="2025-01-01T00:00:00",
                base_seed=42 + i * 1000,
                variation_index=i,
                variation_value=i * 0.1,
                is_baseline=(i == 0),
            ),
        )
        repo.save_run_status(eid, rid, RunStatus.COMPLETED)


# ---------------------------------------------------------------------------
# output_form_for_type
# ---------------------------------------------------------------------------


class TestOutputFormForType:
    def test_single_run_maps_to_point(self):
        assert output_form_for_type("single_run") == ExperimentOutputForm.POINT

    def test_ofat_maps_to_sweep(self):
        assert output_form_for_type("ofat") == ExperimentOutputForm.SWEEP

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="No output form"):
            output_form_for_type("unknown_type")


# ---------------------------------------------------------------------------
# load_experiment_output — Point
# ---------------------------------------------------------------------------


class TestLoadPointOutput:
    def test_loads_point_output(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        _create_point_experiment(repo)

        output = load_experiment_output(repo, "exp-001")

        assert isinstance(output, PointExperimentOutput)
        assert output.output_form == ExperimentOutputForm.POINT
        assert output.experiment_id == "exp-001"
        assert output.experiment_type == "single_run"
        assert output.system_type == "system_a"
        assert output.primary_run_id == "run-0000"
        assert output.num_runs == 1
        assert output.status == "completed"

    def test_point_output_paths(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        _create_point_experiment(repo)

        output = load_experiment_output(repo, "exp-001")

        assert output.experiment_root_path == "exp-001"
        assert output.primary_run_path == "exp-001/runs/run-0000"


# ---------------------------------------------------------------------------
# load_experiment_output — Sweep
# ---------------------------------------------------------------------------


class TestLoadSweepOutput:
    def test_loads_sweep_output(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        _create_sweep_experiment(repo)

        output = load_experiment_output(repo, "exp-002")

        assert isinstance(output, SweepExperimentOutput)
        assert output.output_form == ExperimentOutputForm.SWEEP
        assert output.experiment_id == "exp-002"
        assert output.baseline_run_id == "run-0000"
        assert output.num_runs == 3
        assert output.run_ids == ("run-0000", "run-0001", "run-0002")
        assert len(output.variation_descriptions) == 3

    def test_sweep_output_paths(self, tmp_path):
        repo = ExperimentRepository(tmp_path)
        _create_sweep_experiment(repo)

        output = load_experiment_output(repo, "exp-002")

        assert output.experiment_root_path == "exp-002"
        assert output.baseline_run_path == "exp-002/runs/run-0000"
        assert len(output.run_paths) == 3


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestOutputValidation:
    def test_rejects_inconsistent_form(self, tmp_path):
        """output_form=sweep with experiment_type=single_run should fail."""
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-bad")
        repo.save_experiment_metadata(
            "exp-bad",
            ExperimentMetadata(
                experiment_id="exp-bad",
                created_at="2025-01-01T00:00:00",
                experiment_type="single_run",
                system_type="system_a",
                output_form="sweep",  # wrong!
            ),
        )

        with pytest.raises(ValueError, match="disagrees with experiment_type"):
            load_experiment_output(repo, "exp-bad")

    def test_raises_when_form_not_persisted(self, tmp_path):
        """Experiments without output_form must fail explicitly."""
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-legacy")
        repo.save_experiment_metadata(
            "exp-legacy",
            ExperimentMetadata(
                experiment_id="exp-legacy",
                created_at="2025-01-01T00:00:00",
                experiment_type="single_run",
                system_type="system_a",
                # No output_form
            ),
        )
        repo.create_run_dir("exp-legacy", "run-0000")
        repo.save_run_metadata(
            "exp-legacy", "run-0000",
            RunMetadata(
                run_id="run-0000",
                experiment_id="exp-legacy",
                created_at="2025-01-01T00:00:00",
            ),
        )

        with pytest.raises(ValueError, match="missing output_form"):
            load_experiment_output(repo, "exp-legacy")

    def test_raises_when_primary_run_id_missing(self, tmp_path):
        """Point output without primary_run_id must fail."""
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-no-pri")
        repo.save_experiment_metadata(
            "exp-no-pri",
            ExperimentMetadata(
                experiment_id="exp-no-pri",
                created_at="2025-01-01T00:00:00",
                experiment_type="single_run",
                system_type="system_a",
                output_form="point",
                # No primary_run_id
            ),
        )

        with pytest.raises(ValueError, match="missing primary_run_id"):
            load_experiment_output(repo, "exp-no-pri")

    def test_raises_when_baseline_run_id_missing(self, tmp_path):
        """Sweep output without baseline_run_id must fail."""
        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp-no-base")
        repo.save_experiment_metadata(
            "exp-no-base",
            ExperimentMetadata(
                experiment_id="exp-no-base",
                created_at="2025-01-01T00:00:00",
                experiment_type="ofat",
                system_type="system_a",
                output_form="sweep",
                # No baseline_run_id
            ),
        )

        with pytest.raises(ValueError, match="missing baseline_run_id"):
            load_experiment_output(repo, "exp-no-base")
