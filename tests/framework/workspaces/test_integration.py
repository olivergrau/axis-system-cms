"""WP-12: Integration tests for workspace CLI and end-to-end workflows."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

import yaml

from axis.framework.workspaces.scaffold import scaffold_workspace
from axis.framework.workspaces.summary import summarize_workspace
from axis.framework.workspaces.types import WorkspaceManifest, WorkspaceType
from axis.framework.workspaces.validation import check_workspace
from axis.framework.workspaces.resolution import resolve_run_targets
from axis.framework.workspaces.drift import detect_drift
from axis.framework.workspaces.sync import (
    sync_manifest_after_run,
    sync_manifest_after_compare,
)
from axis.framework.cli import main as cli_main


def _entry_path(entry) -> str:
    """Extract path from a primary_results entry (str, dict, or ResultEntry)."""
    from axis.framework.workspaces.types import ResultEntry
    if isinstance(entry, ResultEntry):
        return entry.path
    if isinstance(entry, dict):
        return entry["path"]
    return entry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _scaffold_single_system(tmp_path: Path) -> Path:
    ws = tmp_path / "integration-single"
    manifest = WorkspaceManifest.model_validate({
        "workspace_id": "integration-single",
        "title": "Integration test workspace",
        "workspace_class": "investigation",
        "workspace_type": "single_system",
        "status": "draft",
        "lifecycle_stage": "idea",
        "created_at": "2026-04-17",
        "question": "Does integration testing work?",
        "system_under_test": "system_a",
    })
    scaffold_workspace(ws, manifest)
    return ws


def _scaffold_comparison(tmp_path: Path) -> Path:
    ws = tmp_path / "integration-cmp"
    manifest = WorkspaceManifest.model_validate({
        "workspace_id": "integration-cmp",
        "title": "Integration comparison",
        "workspace_class": "investigation",
        "workspace_type": "system_comparison",
        "status": "draft",
        "lifecycle_stage": "idea",
        "created_at": "2026-04-17",
        "question": "Which system is better?",
        "reference_system": "system_a",
        "candidate_system": "system_a",
    })
    scaffold_workspace(ws, manifest)
    return ws


def _write_experiment_series(workspace_path: Path) -> None:
    series_id = "integration-series"
    data = {
        "version": 1,
        "workflow_type": "experiment_series",
        "workspace_type": "system_comparison",
        "title": "Integration Series",
        "defaults": {
            "labels": {"measurement_label_pattern": "{experiment_id}"},
            "notes": {"scaffold_notes": True},
        },
        "experiments": [
            {
                "id": "exp_01",
                "title": "Weak candidate tweak",
                "enabled": True,
                "hypothesis": [
                    "Prediction should have a small effect.",
                ],
                "candidate_config_delta": {
                    "num_episodes_per_run": 4,
                },
            },
            {
                "id": "exp_02",
                "title": "Stronger candidate tweak",
                "enabled": True,
                "hypothesis": [
                    "Prediction should have a larger effect.",
                ],
                "candidate_config_delta": {
                    "num_episodes_per_run": 6,
                    "system": {
                        "policy": {
                            "temperature": 0.9,
                        },
                    },
                },
            },
            {
                "id": "exp_03",
                "title": "Disabled experiment",
                "enabled": False,
                "candidate_config_delta": {
                    "num_episodes_per_run": 8,
                },
            },
        ],
    }
    series_dir = workspace_path / "series" / series_id
    series_dir.mkdir(parents=True, exist_ok=True)
    (series_dir / "experiment.yaml").write_text(
        yaml.dump(data, default_flow_style=False, sort_keys=False)
    )
    manifest = yaml.safe_load((workspace_path / "workspace.yaml").read_text())
    manifest["experiment_series"] = {
        "entries": [
            {
                "id": series_id,
                "path": f"series/{series_id}/experiment.yaml",
                "title": "Integration Series",
            },
        ],
    }
    (workspace_path / "workspace.yaml").write_text(
        yaml.dump(manifest, default_flow_style=False, sort_keys=False)
    )


def _write_single_system_experiment_series(workspace_path: Path) -> None:
    series_id = "single-series"
    data = {
        "version": 1,
        "workflow_type": "experiment_series",
        "workspace_type": "single_system",
        "title": "Single-System Series",
        "defaults": {
            "labels": {"measurement_label_pattern": "{experiment_id}"},
            "notes": {"scaffold_notes": True},
        },
        "experiments": [
            {
                "id": "exp_01",
                "title": "Baseline run",
                "enabled": True,
                "hypothesis": ["Establish baseline behavior."],
                "candidate_config_delta": {
                    "num_episodes_per_run": 4,
                },
            },
            {
                "id": "exp_02",
                "title": "Policy tweak",
                "enabled": True,
                "hypothesis": ["Behavior should shift relative to the baseline."],
                "candidate_config_delta": {
                    "num_episodes_per_run": 6,
                    "system": {
                        "policy": {
                            "temperature": 0.9,
                        },
                    },
                },
            },
        ],
    }
    series_dir = workspace_path / "series" / series_id
    series_dir.mkdir(parents=True, exist_ok=True)
    (series_dir / "experiment.yaml").write_text(
        yaml.dump(data, default_flow_style=False, sort_keys=False)
    )
    manifest = yaml.safe_load((workspace_path / "workspace.yaml").read_text())
    manifest["experiment_series"] = {
        "entries": [
            {
                "id": series_id,
                "path": f"series/{series_id}/experiment.yaml",
                "title": "Single-System Series",
            },
        ],
    }
    (workspace_path / "workspace.yaml").write_text(
        yaml.dump(manifest, default_flow_style=False, sort_keys=False)
    )


def _set_candidate_world_override(
    workspace_path: Path,
    *,
    grid_width: int | None = None,
    resource_density: float | None = None,
) -> None:
    """Apply a small world-config override to the candidate config."""
    candidate_config_path = workspace_path / "configs" / "candidate-system_a.yaml"
    data = yaml.safe_load(candidate_config_path.read_text())
    world = data.setdefault("world", {})
    if grid_width is not None:
        world["grid_width"] = grid_width
    if resource_density is not None:
        world["resource_density"] = resource_density
    candidate_config_path.write_text(
        yaml.dump(data, default_flow_style=False, sort_keys=False)
    )


def _set_reference_world_override(
    workspace_path: Path,
    *,
    grid_width: int | None = None,
    resource_density: float | None = None,
) -> None:
    """Apply a small world-config override to the reference config."""
    reference_config_path = workspace_path / "configs" / "reference-system_a.yaml"
    data = yaml.safe_load(reference_config_path.read_text())
    world = data.setdefault("world", {})
    if grid_width is not None:
        world["grid_width"] = grid_width
    if resource_density is not None:
        world["resource_density"] = resource_density
    reference_config_path.write_text(
        yaml.dump(data, default_flow_style=False, sort_keys=False)
    )


def _scaffold_development(tmp_path: Path) -> Path:
    ws = tmp_path / "integration-dev"
    manifest = WorkspaceManifest.model_validate({
        "workspace_id": "integration-dev",
        "title": "Integration dev workspace",
        "workspace_class": "development",
        "workspace_type": "system_development",
        "status": "draft",
        "lifecycle_stage": "idea",
        "created_at": "2026-04-17",
        "development_goal": "Build it",
        "artifact_kind": "system",
        "artifact_under_development": "system_d",
    })
    scaffold_workspace(ws, manifest)
    return ws


# ---------------------------------------------------------------------------
# End-to-end: scaffold → check → show → resolve
# ---------------------------------------------------------------------------


class TestEndToEndSingleSystem:
    def test_scaffold_check_show_resolve(self, tmp_path):
        ws = _scaffold_single_system(tmp_path)

        # Check
        result = check_workspace(ws)
        assert result.is_valid, result.issues

        # Show
        summary = summarize_workspace(ws)
        assert summary.workspace_id == "integration-single"
        assert summary.workspace_type == WorkspaceType.SINGLE_SYSTEM
        assert len(summary.primary_configs) >= 1

        # Resolve
        plan = resolve_run_targets(ws)
        assert len(plan.targets) == 1
        assert plan.targets[0].role == "system_under_test"

        # Drift (no drift expected on fresh workspace without primary_results)
        drift = detect_drift(ws)
        # No declared results, so no missing artifacts
        assert not any(i.severity.value == "error" for i in drift)


class TestEndToEndComparison:
    def test_scaffold_check_resolve(self, tmp_path):
        ws = _scaffold_comparison(tmp_path)

        result = check_workspace(ws)
        assert result.is_valid

        plan = resolve_run_targets(ws)
        assert len(plan.targets) == 2
        roles = {t.role for t in plan.targets}
        assert "reference" in roles
        assert "candidate" in roles


class TestEndToEndDevelopment:
    def test_scaffold_check_resolve(self, tmp_path):
        ws = _scaffold_development(tmp_path)

        result = check_workspace(ws)
        assert result.is_valid
        assert (ws / "concept").is_dir()
        assert (ws / "engineering").is_dir()

        plan = resolve_run_targets(ws)
        assert len(plan.targets) >= 1
        assert all(t.role == "baseline" for t in plan.targets)


# ---------------------------------------------------------------------------
# End-to-end workspace run: artifacts must land under workspace/results/
# ---------------------------------------------------------------------------


class TestWorkspaceRun:
    """Verify workspace-owned execution creates real artifacts."""

    def test_single_system_run_produces_workspace_artifacts(self, tmp_path):
        from axis.framework.workspaces.execute import execute_workspace
        from axis.framework.workspaces.sync import sync_manifest_after_run

        ws = _scaffold_single_system(tmp_path)

        # Execute the workspace
        exec_results = execute_workspace(ws)
        assert len(exec_results) == 1

        er = exec_results[0]
        exp_id = er.experiment_result.experiment_id
        run_ids = [rr.run_id for rr in er.experiment_result.run_results]
        assert len(run_ids) >= 1

        # Verify artifacts exist inside the workspace
        for run_id in run_ids:
            run_dir = ws / "results" / exp_id / "runs" / run_id
            assert run_dir.is_dir(), (
                f"Run dir should exist inside workspace: {run_dir}"
            )
            episodes_dir = run_dir / "episodes"
            assert episodes_dir.is_dir()
            episode_files = list(episodes_dir.glob("episode_*.json"))
            assert len(episode_files) > 0

        # Artifacts must NOT be under the default experiments/results/
        default_repo = Path("experiments/results")
        if default_repo.exists():
            assert not (default_repo / exp_id).exists(), (
                "Workspace run must use workspace-owned mode, "
                "not the default repository"
            )

        # Sync manifest and verify paths are real
        sync_manifest_after_run(ws, exp_id, run_ids, er.role)

        manifest_data = yaml.safe_load((ws / "workspace.yaml").read_text())
        primary_results = manifest_data.get("primary_results", [])
        assert len(primary_results) >= 1

        for entry in primary_results:
            rel_path = _entry_path(entry)
            full_path = ws / rel_path
            assert full_path.exists(), (
                f"primary_results entry '{rel_path}' must point to a "
                f"real artifact inside the workspace"
            )

    def test_comparison_run_produces_workspace_artifacts(self, tmp_path):
        from axis.framework.workspaces.execute import execute_workspace

        ws = _scaffold_comparison(tmp_path)
        exec_results = execute_workspace(ws)
        assert len(exec_results) == 2

        # Both reference and candidate should have artifacts in workspace
        for er in exec_results:
            exp_id = er.experiment_result.experiment_id
            assert (ws / "results" / exp_id).is_dir()


# ---------------------------------------------------------------------------
# Workspace compare: must use workspace-local results only
# ---------------------------------------------------------------------------


class TestWorkspaceCompare:
    """Verify workspace compare uses workspace-owned results."""

    def test_compare_aborts_without_runs(self, tmp_path):
        """Compare must fail if workspace has no execution results."""
        from axis.framework.workspaces.compare import compare_workspace

        ws = _scaffold_comparison(tmp_path)
        with pytest.raises(ValueError, match="No execution results"):
            compare_workspace(ws)

    def test_compare_aborts_with_empty_results_dir(self, tmp_path):
        from axis.framework.workspaces.compare import compare_workspace

        ws = _scaffold_comparison(tmp_path)
        # results/ dir exists (from scaffold) but is empty
        assert (ws / "results").is_dir()
        with pytest.raises(ValueError, match="No execution results"):
            compare_workspace(ws)

    def test_compare_succeeds_after_run(self, tmp_path):
        """Full flow: scaffold → run → sync → compare using workspace results."""
        from axis.framework.workspaces.execute import execute_workspace
        from axis.framework.workspaces.compare import compare_workspace
        from axis.framework.workspaces.sync import sync_manifest_after_run

        ws = _scaffold_comparison(tmp_path)
        exec_results = execute_workspace(ws)

        # Sync manifest (as the CLI does) so compare can resolve by order.
        for er in exec_results:
            run_ids = [rr.run_id for rr in er.experiment_result.run_results]
            sync_manifest_after_run(
                ws, er.experiment_result.experiment_id, run_ids, er.role)

        envelope, ws_path = compare_workspace(ws)
        assert envelope is not None
        assert (ws / "comparisons" / "comparison-001.json").exists()
        assert envelope.comparison_number == 1
        assert envelope.reference_config  # config copies present
        assert envelope.candidate_config

    def test_compare_with_explicit_experiment_ids(self, tmp_path):
        """Manual override with --reference-experiment / --candidate-experiment."""
        from axis.framework.workspaces.execute import execute_workspace
        from axis.framework.workspaces.compare import compare_workspace
        from axis.framework.workspaces.sync import sync_manifest_after_run

        ws = _scaffold_comparison(tmp_path)
        exec_results = execute_workspace(ws)
        for er in exec_results:
            run_ids = [rr.run_id for rr in er.experiment_result.run_results]
            sync_manifest_after_run(
                ws, er.experiment_result.experiment_id, run_ids, er.role)

        ref_eid = exec_results[0].experiment_result.experiment_id
        cand_eid = exec_results[1].experiment_result.experiment_id

        envelope, ws_path = compare_workspace(
            ws,
            reference_experiment=ref_eid,
            candidate_experiment=cand_eid,
        )
        assert envelope is not None

    def test_compare_rejects_nonexistent_experiment(self, tmp_path):
        from axis.framework.workspaces.execute import execute_workspace
        from axis.framework.workspaces.compare import compare_workspace

        ws = _scaffold_comparison(tmp_path)
        exec_results = execute_workspace(ws)
        cand_eid = exec_results[1].experiment_result.experiment_id

        with pytest.raises(ValueError, match="must be provided together"):
            compare_workspace(
                ws, reference_experiment="nonexistent-id",
            )

        with pytest.raises(ValueError, match="not found in workspace"):
            compare_workspace(
                ws,
                reference_experiment="nonexistent-id",
                candidate_experiment=cand_eid,
            )

    def test_compare_cli_aborts_without_runs(self, tmp_path, capsys):
        ws = _scaffold_comparison(tmp_path)
        code = cli_main(["workspaces", "compare", str(ws)])
        assert code == 1
        err = capsys.readouterr().err
        assert "No execution results" in err or "Error" in err


# ---------------------------------------------------------------------------
# Manifest sync round-trip
# ---------------------------------------------------------------------------


class TestManifestSync:
    def test_sync_after_run_preserves_manifest(self, tmp_path):
        ws = _scaffold_single_system(tmp_path)

        # Create a fake result directory so the path is real
        run_dir = ws / "results" / "exp-001" / "runs" / "run-0000"
        run_dir.mkdir(parents=True)

        sync_manifest_after_run(ws, "exp-001", ["run-0000"])

        updated = yaml.safe_load((ws / "workspace.yaml").read_text())
        result_paths = [_entry_path(e) for e in updated["primary_results"]]
        assert "results/exp-001" in result_paths
        # Original fields preserved
        assert updated["workspace_id"] == "integration-single"

    def test_sync_after_compare(self, tmp_path):
        ws = _scaffold_single_system(tmp_path)

        sync_manifest_after_compare(ws, "comparisons/result.json")

        updated = yaml.safe_load((ws / "workspace.yaml").read_text())
        assert "comparisons/result.json" in updated["primary_comparisons"]

    def test_sync_idempotent(self, tmp_path):
        ws = _scaffold_single_system(tmp_path)

        sync_manifest_after_run(ws, "exp-001", ["run-0000"])
        sync_manifest_after_run(ws, "exp-001", ["run-0000"])

        data = yaml.safe_load((ws / "workspace.yaml").read_text())
        result_paths = [_entry_path(e) for e in data["primary_results"]]
        assert result_paths.count("results/exp-001") == 1


# ---------------------------------------------------------------------------
# CLI integration (non-interactive commands)
# ---------------------------------------------------------------------------


class TestCLIIntegration:
    def test_check_text(self, tmp_path, capsys):
        ws = _scaffold_single_system(tmp_path)
        code = cli_main(["workspaces", "check", str(ws)])
        assert code == 0
        out = capsys.readouterr().out
        assert "VALID" in out

    def test_check_json(self, tmp_path, capsys):
        ws = _scaffold_single_system(tmp_path)
        code = cli_main(["workspaces", "check", str(ws), "--output", "json"])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert "issues" in data

    def test_show_text(self, tmp_path, capsys):
        ws = _scaffold_single_system(tmp_path)
        code = cli_main(["workspaces", "show", str(ws)])
        assert code == 0
        out = capsys.readouterr().out
        assert "integration-single" in out

    def test_measure_rejects_non_comparison_workspace(self, tmp_path, capsys):
        ws = _scaffold_single_system(tmp_path)
        code = cli_main(["workspaces", "measure", str(ws)])
        captured = capsys.readouterr()
        assert code == 1
        assert "only supported for system_comparison workspaces" in captured.err
        assert "single_system" in captured.err

    def test_measure_runs_workflow_and_exports_configured_logs(
        self, tmp_path, capsys,
    ):
        ws = _scaffold_comparison(tmp_path)
        manifest_path = ws / "workspace.yaml"
        data = yaml.safe_load(manifest_path.read_text())
        data["measurement_workflow"] = {
            "root_dir": "measurements",
            "experiment_dir_pattern": "experiment_{number}",
            "label_pattern": "trial{number}",
            "comparison_log_pattern": "{label}-cmp.log",
            "run_summary_log_pattern": "{label}-{role}.log",
            "default_run_summary_role": "candidate",
        }
        manifest_path.write_text(yaml.dump(data))

        code = cli_main(["workspaces", "measure", str(ws), "--output", "json"])
        captured = capsys.readouterr()
        assert code == 0

        payload = json.loads(captured.out)
        assert payload["measurement_number"] == 1
        assert payload["measurement_dir"] == "measurements/experiment_1"
        assert payload["comparison_log_path"] == (
            "measurements/experiment_1/trial1-cmp.log"
        )
        assert payload["run_summary_log_path"] == (
            "measurements/experiment_1/trial1-candidate.log"
        )

        comparison_log = ws / payload["comparison_log_path"]
        run_summary_log = ws / payload["run_summary_log_path"]
        assert comparison_log.is_file()
        assert run_summary_log.is_file()
        assert "Run Comparison" in comparison_log.read_text()
        assert "Run run-0000" in run_summary_log.read_text()

    def test_measure_allows_label_override(self, tmp_path, capsys):
        ws = _scaffold_comparison(tmp_path)
        manifest_path = ws / "workspace.yaml"
        data = yaml.safe_load(manifest_path.read_text())
        data["measurement_workflow"] = {
            "root_dir": "measurements",
            "experiment_dir_pattern": "experiment_{number}",
            "label_pattern": "trial{number}",
            "comparison_log_pattern": "{label}-cmp.log",
            "run_summary_log_pattern": "{label}-{role}.log",
            "default_run_summary_role": "candidate",
        }
        manifest_path.write_text(yaml.dump(data))

        code = cli_main([
            "workspaces", "measure", str(ws),
            "--label", "hybrid-x",
            "--output", "json",
        ])
        captured = capsys.readouterr()
        assert code == 0

        payload = json.loads(captured.out)
        assert payload["measurement_number"] == 1
        assert payload["label"] == "hybrid-x"
        assert payload["measurement_dir"] == "measurements/experiment_1"
        assert payload["comparison_log_path"] == (
            "measurements/experiment_1/hybrid-x-cmp.log"
        )
        assert payload["run_summary_log_path"] == (
            "measurements/experiment_1/hybrid-x-candidate.log"
        )

    def test_run_series_rejects_unsupported_workspace_type(self, tmp_path, capsys):
        ws = _scaffold_development(tmp_path)
        code = cli_main(["workspaces", "run-series", str(ws), "--series", "any"])
        captured = capsys.readouterr()
        assert code == 1
        assert (
            "only supported for system_comparison and single_system workspaces"
            in captured.err
        )

    def test_run_series_executes_enabled_experiments_and_writes_aggregate_outputs(
        self, tmp_path, capsys,
    ):
        ws = _scaffold_comparison(tmp_path)
        _write_experiment_series(ws)
        original_notes = (
            (ws / "notes.md").read_text(encoding="utf-8")
            if (ws / "notes.md").exists()
            else None
        )

        code = cli_main([
            "workspaces", "run-series", str(ws), "--series", "integration-series", "--output", "json",
        ])
        captured = capsys.readouterr()
        assert code == 0

        payload = json.loads(captured.out)
        assert payload["executed_experiment_count"] == 2
        assert payload["executed_experiment_ids"] == ["exp_01", "exp_02"]
        assert (ws / payload["series_summary_markdown_path"]).is_file()
        assert (ws / payload["series_summary_json_path"]).is_file()
        assert (ws / payload["series_metrics_csv_path"]).is_file()
        assert (ws / payload["series_manifest_json_path"]).is_file()
        assert payload["notes_updated"] is False
        if original_notes is not None:
            assert (ws / "notes.md").read_text(encoding="utf-8") == original_notes

        summary_text = (ws / payload["series_summary_markdown_path"]).read_text()
        assert "Progression View" in summary_text
        assert "Reference-System View" in summary_text

    def test_run_series_text_output_prefixes_progress_with_experiment_context(
        self, tmp_path, capsys,
    ):
        ws = _scaffold_comparison(tmp_path)
        _write_experiment_series(ws)

        code = cli_main(["workspaces", "run-series", str(ws), "--series", "integration-series"])
        captured = capsys.readouterr()
        assert code == 0
        assert "1/2 exp_01 | Experiment runs" in captured.out
        assert "1/2 exp_01 | run-0000: episodes" in captured.out
        assert "1/2 exp_01 | Episode comparisons" in captured.out
        assert "2/2 exp_02 | Experiment runs" in captured.out
        assert "2/2 exp_02 | run-0000: episodes" in captured.out
        assert "2/2 exp_02 | Episode comparisons" in captured.out
        assert "Workspace configs" not in captured.out

    def test_run_series_update_notes_overwrites_notes_scaffold(
        self, tmp_path, capsys,
    ):
        ws = _scaffold_comparison(tmp_path)
        _write_experiment_series(ws)
        (ws / "series" / "integration-series" / "notes.md").write_text("old notes\n", encoding="utf-8")

        code = cli_main([
            "workspaces", "run-series", str(ws), "--series", "integration-series", "--update-notes", "--output", "json",
        ])
        captured = capsys.readouterr()
        assert code == 0

        payload = json.loads(captured.out)
        assert payload["notes_updated"] is True
        notes_text = (ws / "series" / "integration-series" / "notes.md").read_text()
        assert "Weak candidate tweak" in notes_text
        assert "## Experiment folder: series/integration-series/measurements/experiment_1" in notes_text

    def test_run_series_supports_single_system_baseline_comparisons(
        self, tmp_path, capsys,
    ):
        ws = _scaffold_single_system(tmp_path)
        _write_single_system_experiment_series(ws)
        original_notes = (ws / "notes.md").read_text(encoding="utf-8")

        code = cli_main([
            "workspaces", "run-series", str(ws), "--series", "single-series", "--output", "json",
        ])
        captured = capsys.readouterr()
        assert code == 0

        payload = json.loads(captured.out)
        assert payload["executed_experiment_count"] == 2
        assert payload["executed_experiment_ids"] == ["exp_01", "exp_02"]
        assert (ws / payload["series_summary_markdown_path"]).is_file()
        assert (ws / payload["series_metrics_csv_path"]).is_file()
        assert (ws / payload["series_manifest_json_path"]).is_file()
        assert (ws / "notes.md").read_text(encoding="utf-8") == original_notes

        summary_text = (ws / payload["series_summary_markdown_path"]).read_text()
        assert "Baseline Comparison View" in summary_text

    def test_show_json(self, tmp_path, capsys):
        ws = _scaffold_single_system(tmp_path)
        code = cli_main(["workspaces", "show", str(ws), "--output", "json"])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert data["workspace_id"] == "integration-single"

    def test_run_produces_workspace_artifacts(self, tmp_path, capsys):
        """E2E: axis workspaces run writes artifacts under workspace/results/."""
        ws = _scaffold_single_system(tmp_path)
        code = cli_main(["workspaces", "run", str(ws)])
        assert code == 0

        # Verify artifacts in workspace
        results_dir = ws / "results"
        experiments = [d for d in results_dir.iterdir() if d.is_dir()]
        assert len(experiments) >= 1

        # Verify manifest was synced with real paths
        manifest_data = yaml.safe_load((ws / "workspace.yaml").read_text())
        for entry in manifest_data.get("primary_results", []):
            rel_path = _entry_path(entry)
            assert (ws / rel_path).exists(), (
                f"Synced path '{rel_path}' must exist in workspace"
            )

    def test_run_json_output(self, tmp_path, capsys):
        ws = _scaffold_single_system(tmp_path)
        code = cli_main(["workspaces", "run", str(ws), "--output", "json"])
        assert code == 0
        # Extract JSON array from output (may have logging lines mixed in).
        out = capsys.readouterr().out
        # Find the JSON array — it starts with "[\n  {".
        import re
        m = re.search(r'\[\s*\n\s*\{', out)
        assert m, f"No JSON array found in output: {out[:200]}"
        start = m.start()
        end = out.rindex("]") + 1
        data = json.loads(out[start:end])
        assert len(data) >= 1
        assert "experiment_id" in data[0]

    def test_run_aborts_when_config_is_unchanged(self, tmp_path, capsys):
        ws = _scaffold_single_system(tmp_path)

        code = cli_main(["workspaces", "run", str(ws)])
        assert code == 0
        capsys.readouterr()

        code = cli_main(["workspaces", "run", str(ws)])
        assert code == 1
        err = capsys.readouterr().err
        assert "no config changes detected" in err

    def test_run_override_guard_allows_unchanged_config(self, tmp_path, capsys):
        ws = _scaffold_single_system(tmp_path)

        code = cli_main(["workspaces", "run", str(ws)])
        assert code == 0
        capsys.readouterr()

        code = cli_main(["workspaces", "run", str(ws), "--override-guard"])
        assert code == 0

    def test_run_allows_comparison_when_only_candidate_changes(
        self, tmp_path, capsys,
    ):
        import yaml

        ws = _scaffold_comparison(tmp_path)

        code = cli_main(["workspaces", "run", str(ws)])
        assert code == 0
        capsys.readouterr()

        candidate_config = ws / "configs" / "candidate-system_a.yaml"
        data = yaml.safe_load(candidate_config.read_text())
        data["num_episodes_per_run"] = 6
        candidate_config.write_text(
            yaml.dump(data, default_flow_style=False, sort_keys=False)
        )

        code = cli_main(["workspaces", "run", str(ws)])
        assert code == 0

    def test_run_notes_are_stored_and_shown(self, tmp_path, capsys):
        import yaml

        ws = _scaffold_single_system(tmp_path)
        notes = "My notes for this run"

        code = cli_main([
            "workspaces", "run", str(ws), "--notes", notes,
        ])
        assert code == 0
        capsys.readouterr()

        manifest = yaml.safe_load((ws / "workspace.yaml").read_text())
        results = manifest.get("primary_results", [])
        assert results, "Expected primary_results entries after workspace run"
        assert results[-1].get("run_notes") == notes

        code = cli_main(["workspaces", "show", str(ws)])
        assert code == 0
        out = capsys.readouterr().out
        assert "Run notes" in out
        assert notes in out

        code = cli_main(["workspaces", "run-summary", str(ws)])
        assert code == 0
        out = capsys.readouterr().out
        assert "Run notes" in out
        assert notes in out

    def test_run_treats_world_only_change_as_normal_config_change(
        self, tmp_path, capsys,
    ):
        ws = _scaffold_comparison(tmp_path)

        code = cli_main(["workspaces", "run", str(ws)])
        assert code == 0
        capsys.readouterr()

        _set_reference_world_override(ws, grid_width=7)
        _set_candidate_world_override(ws, grid_width=7)

        code = cli_main(["workspaces", "run", str(ws)])
        assert code == 0


    def test_show_after_run_displays_real_artifacts(self, tmp_path, capsys):
        """After workspace run, show must display actual artifact paths."""
        ws = _scaffold_single_system(tmp_path)
        # Run first
        cli_main(["workspaces", "run", str(ws)])
        capsys.readouterr()  # discard run output

        # Show
        code = cli_main(["workspaces", "show", str(ws)])
        assert code == 0
        out = capsys.readouterr().out
        assert "Primary results:" in out
        assert "[OK]" in out
        assert "results/" in out

    def test_show_json_after_run_has_artifact_existence(self, tmp_path, capsys):
        ws = _scaffold_single_system(tmp_path)
        cli_main(["workspaces", "run", str(ws)])
        capsys.readouterr()

        code = cli_main(["workspaces", "show", str(ws), "--output", "json"])
        assert code == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        # primary_results should have entries with exists=True
        assert len(data["primary_results"]) >= 1
        assert data["primary_results"][0]["exists"] is True

    def test_show_displays_config_changes_between_runs(self, tmp_path, capsys):
        ws = _scaffold_single_system(tmp_path)

        results_root = ws / "results"
        exp1 = results_root / "exp-001"
        exp2 = results_root / "exp-002"
        (exp1 / "runs" / "run-0000").mkdir(parents=True)
        (exp2 / "runs" / "run-0000").mkdir(parents=True)

        config1 = {
            "system_type": "system_a",
            "experiment_type": "single_run",
            "general": {"seed": 7},
            "execution": {"max_steps": 100},
            "world": {"world_type": "grid_2d", "grid_width": 10, "grid_height": 10},
            "system": {"policy": {"temperature": 1.0, "selection_mode": "sample"}},
            "num_episodes_per_run": 5,
        }
        config2 = {
            "system_type": "system_a",
            "experiment_type": "single_run",
            "general": {"seed": 7},
            "execution": {"max_steps": 150},
            "world": {"world_type": "grid_2d", "grid_width": 10, "grid_height": 10},
            "system": {"policy": {"temperature": 2.0, "selection_mode": "sample"}},
            "num_episodes_per_run": 5,
        }
        (exp1 / "experiment_config.json").write_text(json.dumps(config1))
        (exp2 / "experiment_config.json").write_text(json.dumps(config2))

        sync_manifest_after_run(
            ws, "exp-001", ["run-0000"], "system_under_test",
            output_form="point", system_type="system_a", primary_run_id="run-0000",
        )
        sync_manifest_after_run(
            ws, "exp-002", ["run-0000"], "system_under_test",
            output_form="point", system_type="system_a", primary_run_id="run-0000",
        )

        code = cli_main(["workspaces", "show", str(ws)])
        assert code == 0
        out = capsys.readouterr().out
        assert "Config changes vs previous comparable run:" in out
        assert "execution.max_steps: 150" in out
        assert "system.policy.temperature: 2.0" in out

    def test_show_json_includes_config_changes_between_runs(self, tmp_path, capsys):
        ws = _scaffold_single_system(tmp_path)

        results_root = ws / "results"
        exp1 = results_root / "exp-001"
        exp2 = results_root / "exp-002"
        (exp1 / "runs" / "run-0000").mkdir(parents=True)
        (exp2 / "runs" / "run-0000").mkdir(parents=True)

        config1 = {
            "system_type": "system_a",
            "experiment_type": "single_run",
            "general": {"seed": 7},
            "execution": {"max_steps": 100},
            "system": {"policy": {"temperature": 1.0}},
            "num_episodes_per_run": 5,
        }
        config2 = {
            "system_type": "system_a",
            "experiment_type": "single_run",
            "general": {"seed": 7},
            "execution": {"max_steps": 110},
            "system": {"policy": {"temperature": 2.5}},
            "num_episodes_per_run": 5,
        }
        (exp1 / "experiment_config.json").write_text(json.dumps(config1))
        (exp2 / "experiment_config.json").write_text(json.dumps(config2))

        sync_manifest_after_run(
            ws, "exp-001", ["run-0000"], "system_under_test",
            output_form="point", system_type="system_a", primary_run_id="run-0000",
        )
        sync_manifest_after_run(
            ws, "exp-002", ["run-0000"], "system_under_test",
            output_form="point", system_type="system_a", primary_run_id="run-0000",
        )

        code = cli_main(["workspaces", "show", str(ws), "--output", "json"])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert data["primary_results"][0]["config_changes"] is None
        assert data["primary_results"][1]["config_changes"] == {
            "execution": {"max_steps": 110},
            "system": {"policy": {"temperature": 2.5}},
        }

    def test_show_displays_compared_experiments_and_config_differences(self, tmp_path, capsys):
        ws = _scaffold_single_system(tmp_path)
        comparisons_dir = ws / "comparisons"
        comparisons_dir.mkdir(exist_ok=True)

        comparison_data = {
            "comparison_number": 1,
            "timestamp": "2026-04-22T12:00:00",
            "reference_config": {
                "system_type": "system_a",
                "execution": {"max_steps": 100},
                "system": {"policy": {"temperature": 1.0}},
            },
            "candidate_config": {
                "system_type": "system_a",
                "execution": {"max_steps": 150},
                "system": {"policy": {"temperature": 2.0}},
            },
            "comparison_result": {
                "reference_experiment_id": "exp-ref",
                "candidate_experiment_id": "exp-cand",
            },
        }
        (comparisons_dir / "comparison-001.json").write_text(json.dumps(comparison_data))
        sync_manifest_after_compare(ws, "comparisons/comparison-001.json")

        code = cli_main(["workspaces", "show", str(ws)])
        assert code == 0
        out = capsys.readouterr().out
        assert "Compared experiments: exp-ref vs exp-cand" in out
        assert "Config differences between compared experiments:" in out
        assert "execution.max_steps: 150" in out
        assert "system.policy.temperature: 2.0" in out

    def test_show_json_includes_comparison_details(self, tmp_path, capsys):
        ws = _scaffold_single_system(tmp_path)
        comparisons_dir = ws / "comparisons"
        comparisons_dir.mkdir(exist_ok=True)

        comparison_data = {
            "comparison_number": 1,
            "timestamp": "2026-04-22T12:00:00",
            "reference_config": {
                "system_type": "system_a",
                "execution": {"max_steps": 100},
            },
            "candidate_config": {
                "system_type": "system_a",
                "execution": {"max_steps": 120},
            },
            "comparison_result": {
                "reference_experiment_id": "exp-ref",
                "candidate_experiment_id": "exp-cand",
            },
        }
        (comparisons_dir / "comparison-001.json").write_text(json.dumps(comparison_data))
        sync_manifest_after_compare(ws, "comparisons/comparison-001.json")

        code = cli_main(["workspaces", "show", str(ws), "--output", "json"])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert data["primary_comparisons"][0]["reference_experiment_id"] == "exp-ref"
        assert data["primary_comparisons"][0]["candidate_experiment_id"] == "exp-cand"
        assert data["primary_comparisons"][0]["comparison_config_changes"] == {
            "execution": {"max_steps": 120},
        }

    def test_show_displays_registered_experiment_series_artifacts(self, tmp_path, capsys):
        ws = _scaffold_single_system(tmp_path)
        series_root = ws / "series" / "alpha"
        (series_root / "results" / "exp-001" / "runs" / "run-0000").mkdir(parents=True)
        (series_root / "measurements" / "experiment_1").mkdir(parents=True)
        (series_root / "comparisons").mkdir(parents=True)
        (series_root / "experiment.yaml").write_text(yaml.dump({
            "version": 1,
            "workflow_type": "experiment_series",
            "workspace_type": "single_system",
            "title": "Alpha Series",
            "base_configs": {"system_under_test": "configs/system_a.yaml"},
            "experiments": [
                {
                    "id": "exp_01",
                    "title": "Experiment 1",
                    "enabled": True,
                    "candidate_config_delta": {"system": {"policy": {"temperature": 2.0}}},
                },
            ],
        }))
        comparison_data = {
            "comparison_number": 1,
            "timestamp": "2026-04-22T12:00:00",
            "reference_config": {"system_type": "system_a", "execution": {"max_steps": 100}},
            "candidate_config": {"system_type": "system_a", "execution": {"max_steps": 120}},
            "comparison_result": {
                "reference_experiment_id": "exp-ref",
                "candidate_experiment_id": "exp-cand",
            },
        }
        (series_root / "comparisons" / "comparison-001.json").write_text(json.dumps(comparison_data))
        manifest = yaml.safe_load((ws / "workspace.yaml").read_text())
        manifest["experiment_series"] = {
            "entries": [
                {
                    "id": "alpha",
                    "path": "series/alpha/experiment.yaml",
                    "generated": {
                        "results": [
                            {
                                "path": "series/alpha/results/exp-001",
                                "output_form": "point",
                                "system_type": "system_a",
                                "role": "system_under_test",
                                "timestamp": "2026-04-22T12:00:00",
                            },
                        ],
                        "comparisons": ["series/alpha/comparisons/comparison-001.json"],
                        "measurement_runs": [
                            {
                                "path": "series/alpha/measurements/experiment_1",
                                "label": "alpha-1",
                                "timestamp": "2026-04-22T12:05:00",
                            },
                        ],
                    },
                },
            ],
        }
        (ws / "workspace.yaml").write_text(yaml.dump(manifest))

        code = cli_main(["workspaces", "show", str(ws)])
        assert code == 0
        out = capsys.readouterr().out
        assert "Experiment Series" in out
        assert "[OK] alpha" in out
        assert "Series results:" in out
        assert "series/alpha/results/exp-001" in out
        assert "Series comparisons:" in out
        assert "Compared experiments: exp-ref vs exp-cand" in out
        assert "Series measurements:" in out
        assert "label=alpha-1" in out

    def test_show_json_includes_registered_experiment_series_artifacts(self, tmp_path, capsys):
        ws = _scaffold_single_system(tmp_path)
        series_root = ws / "series" / "alpha"
        (series_root / "results" / "exp-001").mkdir(parents=True)
        (series_root / "measurements" / "experiment_1").mkdir(parents=True)
        (series_root / "comparisons").mkdir(parents=True)
        (series_root / "experiment.yaml").write_text(yaml.dump({
            "version": 1,
            "workflow_type": "experiment_series",
            "workspace_type": "single_system",
            "title": "Alpha Series",
            "base_configs": {"system_under_test": "configs/system_a.yaml"},
            "experiments": [
                {
                    "id": "exp_01",
                    "title": "Experiment 1",
                    "enabled": True,
                    "candidate_config_delta": {"system": {"policy": {"temperature": 2.0}}},
                },
            ],
        }))
        (series_root / "comparisons" / "comparison-001.json").write_text(json.dumps({
            "comparison_number": 1,
            "timestamp": "2026-04-22T12:00:00",
            "reference_config": {"system_type": "system_a", "execution": {"max_steps": 100}},
            "candidate_config": {"system_type": "system_a", "execution": {"max_steps": 120}},
            "comparison_result": {
                "reference_experiment_id": "exp-ref",
                "candidate_experiment_id": "exp-cand",
            },
        }))
        manifest = yaml.safe_load((ws / "workspace.yaml").read_text())
        manifest["experiment_series"] = {
            "entries": [
                {
                    "id": "alpha",
                    "path": "series/alpha/experiment.yaml",
                    "generated": {
                        "results": [{"path": "series/alpha/results/exp-001"}],
                        "comparisons": ["series/alpha/comparisons/comparison-001.json"],
                        "measurement_runs": [{"path": "series/alpha/measurements/experiment_1", "label": "alpha-1"}],
                    },
                },
            ],
        }
        (ws / "workspace.yaml").write_text(yaml.dump(manifest))

        code = cli_main(["workspaces", "show", str(ws), "--output", "json"])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert len(data["experiment_series"]) == 1
        assert data["experiment_series"][0]["id"] == "alpha"
        assert data["experiment_series"][0]["exists"] is True
        assert data["experiment_series"][0]["results"][0]["exists"] is True
        assert data["experiment_series"][0]["comparisons"][0]["reference_experiment_id"] == "exp-ref"
        assert data["experiment_series"][0]["comparisons"][0]["candidate_experiment_id"] == "exp-cand"
        assert data["experiment_series"][0]["measurement_runs"][0]["label"] == "alpha-1"

    def test_config_changes_use_previous_result_with_same_role(self, tmp_path):
        ws = _scaffold_comparison(tmp_path)

        results_root = ws / "results"
        configs = {
            "ref-001": {"system_type": "system_a", "system": {"policy": {"temperature": 1.0}}},
            "cand-001": {"system_type": "system_a", "system": {"policy": {"temperature": 5.0}}},
            "ref-002": {"system_type": "system_a", "system": {"policy": {"temperature": 2.0}}},
        }
        for exp_id, cfg in configs.items():
            exp_dir = results_root / exp_id
            (exp_dir / "runs" / "run-0000").mkdir(parents=True)
            (exp_dir / "experiment_config.json").write_text(json.dumps(cfg))

        sync_manifest_after_run(
            ws, "ref-001", ["run-0000"], "reference",
            output_form="point", system_type="system_a", primary_run_id="run-0000",
        )
        sync_manifest_after_run(
            ws, "cand-001", ["run-0000"], "candidate",
            output_form="point", system_type="system_a", primary_run_id="run-0000",
        )
        sync_manifest_after_run(
            ws, "ref-002", ["run-0000"], "reference",
            output_form="point", system_type="system_a", primary_run_id="run-0000",
        )

        data = yaml.safe_load((ws / "workspace.yaml").read_text())
        assert data["primary_results"][0].get("config_changes") is None
        assert data["primary_results"][1].get("config_changes") is None
        assert data["primary_results"][2]["config_changes"] == {
            "system": {"policy": {"temperature": 2.0}},
        }


# ---------------------------------------------------------------------------
# Single-system comparison workflow
# ---------------------------------------------------------------------------


class TestSingleSystemComparison:
    """Verify single_system workspaces support run → run → compare workflow."""

    def _run_and_sync(self, ws):
        from axis.framework.workspaces.execute import execute_workspace
        from axis.framework.workspaces.sync import sync_manifest_after_run

        exec_results = execute_workspace(ws)
        for er in exec_results:
            run_ids = [rr.run_id for rr in er.experiment_result.run_results]
            sync_manifest_after_run(
                ws, er.experiment_result.experiment_id, run_ids, er.role)
        return exec_results

    def test_multiple_runs_accumulate(self, tmp_path):
        ws = _scaffold_single_system(tmp_path)

        results_1 = self._run_and_sync(ws)
        results_2 = self._run_and_sync(ws)

        eid_1 = results_1[0].experiment_result.experiment_id
        eid_2 = results_2[0].experiment_result.experiment_id
        assert eid_1 != eid_2

        assert (ws / "results" / eid_1).is_dir()
        assert (ws / "results" / eid_2).is_dir()

        manifest = yaml.safe_load((ws / "workspace.yaml").read_text())
        result_paths = [_entry_path(e) for e in manifest["primary_results"]]
        assert len(result_paths) >= 2

    def test_compare_after_two_runs(self, tmp_path):
        from axis.framework.workspaces.compare import compare_workspace
        from axis.framework.workspaces.sync import sync_manifest_after_compare

        ws = _scaffold_single_system(tmp_path)
        self._run_and_sync(ws)
        self._run_and_sync(ws)

        env, ws_path = compare_workspace(ws)
        sync_manifest_after_compare(ws, ws_path)

        assert env.comparison_number == 1
        assert (ws / ws_path).exists()
        assert env.reference_config
        assert env.candidate_config

    def test_compare_fails_with_single_run(self, tmp_path):
        """Need at least 2 experiments to compare."""
        from axis.framework.workspaces.compare import compare_workspace

        ws = _scaffold_single_system(tmp_path)
        self._run_and_sync(ws)

        with pytest.raises(ValueError, match="at least 2 point outputs"):
            compare_workspace(ws)

    def test_compare_with_explicit_ids(self, tmp_path):
        from axis.framework.workspaces.compare import compare_workspace

        ws = _scaffold_single_system(tmp_path)
        r1 = self._run_and_sync(ws)
        r2 = self._run_and_sync(ws)

        eid_1 = r1[0].experiment_result.experiment_id
        eid_2 = r2[0].experiment_result.experiment_id

        env, _ = compare_workspace(
            ws, reference_experiment=eid_1, candidate_experiment=eid_2)
        cr = env.comparison_result
        assert cr["reference_experiment_id"] == eid_1
        assert cr["candidate_experiment_id"] == eid_2

    def test_comparison_result_cli(self, tmp_path, capsys):
        from axis.framework.workspaces.compare import compare_workspace
        from axis.framework.workspaces.sync import sync_manifest_after_compare

        ws = _scaffold_single_system(tmp_path)
        self._run_and_sync(ws)
        self._run_and_sync(ws)

        _, ws_path = compare_workspace(ws)
        sync_manifest_after_compare(ws, ws_path)

        code = cli_main(["workspaces", "comparison-summary", str(ws)])
        assert code == 0
        out = capsys.readouterr().out
        assert "Comparison #1" in out


# ---------------------------------------------------------------------------
# Multiple comparison runs (iterative workflow)
# ---------------------------------------------------------------------------


class TestMultipleComparisons:
    """Verify iterative compare workflow produces sequential results."""

    def _run_and_sync(self, ws):
        from axis.framework.workspaces.execute import execute_workspace
        from axis.framework.workspaces.sync import sync_manifest_after_run

        exec_results = execute_workspace(ws)
        for er in exec_results:
            run_ids = [rr.run_id for rr in er.experiment_result.run_results]
            sync_manifest_after_run(
                ws, er.experiment_result.experiment_id, run_ids, er.role)
        return exec_results

    def test_sequential_comparison_numbering(self, tmp_path):
        from axis.framework.workspaces.compare import compare_workspace
        from axis.framework.workspaces.sync import sync_manifest_after_compare

        ws = _scaffold_comparison(tmp_path)
        self._run_and_sync(ws)

        env1, path1 = compare_workspace(ws)
        sync_manifest_after_compare(ws, path1)
        assert env1.comparison_number == 1
        assert path1 == "comparisons/comparison-001.json"

        env2, path2 = compare_workspace(ws)
        sync_manifest_after_compare(ws, path2)
        assert env2.comparison_number == 2
        assert path2 == "comparisons/comparison-002.json"

        # Both files exist
        assert (ws / "comparisons" / "comparison-001.json").exists()
        assert (ws / "comparisons" / "comparison-002.json").exists()

        # Manifest has both entries
        manifest = yaml.safe_load((ws / "workspace.yaml").read_text())
        assert len(manifest["primary_comparisons"]) == 2

    def test_envelope_contains_config_copies(self, tmp_path):
        from axis.framework.workspaces.compare import compare_workspace

        ws = _scaffold_comparison(tmp_path)
        self._run_and_sync(ws)

        env, _ = compare_workspace(ws)
        assert "system_type" in env.reference_config
        assert "system_type" in env.candidate_config
        assert "system" in env.reference_config
        assert "system" in env.candidate_config

    def test_envelope_persisted_with_configs(self, tmp_path):
        """On-disk envelope matches in-memory envelope."""
        from axis.framework.workspaces.compare import compare_workspace
        from axis.framework.workspaces.comparison_envelope import (
            WorkspaceComparisonEnvelope,
        )

        ws = _scaffold_comparison(tmp_path)
        self._run_and_sync(ws)

        env, ws_path = compare_workspace(ws)
        loaded = WorkspaceComparisonEnvelope.model_validate(
            json.loads((ws / ws_path).read_text()))
        assert loaded.comparison_number == env.comparison_number
        assert loaded.reference_config == env.reference_config
        assert loaded.candidate_config == env.candidate_config


# ---------------------------------------------------------------------------
# CLI: comparison-summary command
# ---------------------------------------------------------------------------


class TestComparisonResultCLI:
    """Verify axis workspaces comparison-summary command."""

    def _prepare_workspace_with_comparison(self, tmp_path):
        from axis.framework.workspaces.execute import execute_workspace
        from axis.framework.workspaces.compare import compare_workspace
        from axis.framework.workspaces.sync import (
            sync_manifest_after_run,
            sync_manifest_after_compare,
        )

        ws = _scaffold_comparison(tmp_path)
        exec_results = execute_workspace(ws)
        for er in exec_results:
            run_ids = [rr.run_id for rr in er.experiment_result.run_results]
            sync_manifest_after_run(
                ws, er.experiment_result.experiment_id, run_ids, er.role)
        _, ws_path = compare_workspace(ws)
        sync_manifest_after_compare(ws, ws_path)
        return ws

    def test_comparison_result_shows_single(self, tmp_path, capsys):
        ws = self._prepare_workspace_with_comparison(tmp_path)
        code = cli_main(["workspaces", "comparison-summary", str(ws)])
        assert code == 0
        out = capsys.readouterr().out
        assert "Comparison #1" in out

    def test_comparison_result_json(self, tmp_path, capsys):
        ws = self._prepare_workspace_with_comparison(tmp_path)
        code = cli_main([
            "workspaces", "comparison-summary", str(ws), "--output", "json",
        ])
        assert code == 0
        out = capsys.readouterr().out
        # Extract JSON object from output (may have logging lines mixed in).
        import re
        m = re.search(r'\{\s*\n\s*"', out)
        assert m, f"No JSON object found in output: {out[:200]}"
        start = m.start()
        end = out.rindex("}") + 1
        data = json.loads(out[start:end])
        assert data["comparison_number"] == 1
        assert "reference_config" in data
        assert "candidate_config" in data
        assert "comparison_result" in data

    def test_comparison_result_by_number(self, tmp_path, capsys):
        from axis.framework.workspaces.compare import compare_workspace
        from axis.framework.workspaces.sync import sync_manifest_after_compare

        ws = self._prepare_workspace_with_comparison(tmp_path)
        # Add a second comparison
        _, ws_path = compare_workspace(ws)
        sync_manifest_after_compare(ws, ws_path)

        code = cli_main([
            "workspaces", "comparison-summary", str(ws), "--number", "2",
        ])
        assert code == 0
        out = capsys.readouterr().out
        assert "Comparison #2" in out

    def test_comparison_result_defaults_to_latest_when_multiple(
        self, tmp_path, capsys,
    ):
        from axis.framework.workspaces.compare import compare_workspace
        from axis.framework.workspaces.sync import sync_manifest_after_compare

        ws = self._prepare_workspace_with_comparison(tmp_path)
        _, ws_path = compare_workspace(ws)
        sync_manifest_after_compare(ws, ws_path)

        code = cli_main(["workspaces", "comparison-summary", str(ws)])
        assert code == 0
        out = capsys.readouterr().out
        assert "Comparison #2" in out
        assert "Showing latest comparison by default." in out

    def test_comparison_result_error_no_comparisons(self, tmp_path, capsys):
        ws = _scaffold_comparison(tmp_path)
        code = cli_main(["workspaces", "comparison-summary", str(ws)])
        assert code == 1

    def test_comparison_result_accepts_world_config_differences_by_default(
        self, tmp_path, capsys,
    ):
        from axis.framework.workspaces.execute import execute_workspace
        from axis.framework.workspaces.compare import compare_workspace
        from axis.framework.workspaces.sync import (
            sync_manifest_after_run,
            sync_manifest_after_compare,
        )

        ws = _scaffold_comparison(tmp_path)
        _set_candidate_world_override(ws, grid_width=7)

        exec_results = execute_workspace(ws)
        for er in exec_results:
            run_ids = [rr.run_id for rr in er.experiment_result.run_results]
            sync_manifest_after_run(
                ws, er.experiment_result.experiment_id, run_ids, er.role)

        _, ws_path = compare_workspace(ws)
        sync_manifest_after_compare(ws, ws_path)

        code = cli_main(["workspaces", "comparison-summary", str(ws)])
        assert code == 0
        out = capsys.readouterr().out
        assert "No valid episode pairs to summarize" not in out


class TestWorkspaceCompareWorldDifferences:
    def test_compare_succeeds_with_world_differences_by_default(self, tmp_path):
        from axis.framework.workspaces.execute import execute_workspace
        from axis.framework.workspaces.compare import compare_workspace
        from axis.framework.workspaces.sync import (
            sync_manifest_after_run,
            sync_manifest_after_compare,
        )
        from axis.framework.workspaces.comparison_envelope import (
            WorkspaceComparisonEnvelope,
        )

        ws = _scaffold_comparison(tmp_path)
        _set_candidate_world_override(ws, resource_density=0.2)

        exec_results = execute_workspace(ws)
        for er in exec_results:
            run_ids = [rr.run_id for rr in er.experiment_result.run_results]
            sync_manifest_after_run(
                ws, er.experiment_result.experiment_id, run_ids, er.role)

        _, ws_path = compare_workspace(ws)
        sync_manifest_after_compare(ws, ws_path)

        loaded = WorkspaceComparisonEnvelope.model_validate(
            json.loads((ws / ws_path).read_text())
        )
        summary = loaded.comparison_result["summary"]
        assert summary["num_valid_pairs"] >= 1


# ---------------------------------------------------------------------------
# Backward compatibility: existing commands unchanged
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:
    def test_experiments_list_still_works(self, capsys):
        code = cli_main(["experiments", "list"])
        assert code == 0

    def test_help_still_works(self, capsys):
        code = cli_main([])
        assert code == 1  # No entity → help + exit 1


# ---------------------------------------------------------------------------
# System development workflow
# ---------------------------------------------------------------------------


class TestSystemDevelopmentWorkflow:
    """Verify development/system_development baseline/candidate workflow."""

    def test_scaffold_has_development_fields(self, tmp_path):
        ws = _scaffold_development(tmp_path)
        data = yaml.safe_load((ws / "workspace.yaml").read_text())
        assert data["baseline_config"] == "configs/baseline-system_d.yaml"
        assert data["candidate_config"] is None
        assert data["baseline_results"] == []
        assert data["candidate_results"] == []
        assert data["current_candidate_result"] is None
        assert data["current_validation_comparison"] is None
        # Config file must exist with spec naming
        assert (ws / "configs" / "baseline-system_d.yaml").exists()

    def test_pre_candidate_run(self, tmp_path):
        """Pre-candidate state: only baseline runs."""
        from axis.framework.workspaces.execute import execute_workspace
        from axis.framework.workspaces.sync import sync_manifest_after_run

        ws = _scaffold_development(tmp_path)
        exec_results = execute_workspace(ws)
        assert len(exec_results) == 1
        assert exec_results[0].role == "baseline"

        # Sync
        er = exec_results[0]
        run_ids = [rr.run_id for rr in er.experiment_result.run_results]
        sync_manifest_after_run(
            ws, er.experiment_result.experiment_id, run_ids, er.role)

        data = yaml.safe_load((ws / "workspace.yaml").read_text())
        assert len(data["baseline_results"]) >= 1
        assert data["candidate_results"] == []

    def test_post_candidate_run(self, tmp_path):
        """Post-candidate: both baseline and candidate run."""
        import shutil
        from axis.framework.workspaces.execute import execute_workspace
        from axis.framework.workspaces.sync import sync_manifest_after_run
        from ruamel.yaml import YAML

        ws = _scaffold_development(tmp_path)

        # Create candidate config by copying baseline
        baseline = ws / "configs" / "baseline-system_d.yaml"
        candidate = ws / "configs" / "candidate-system_d.yaml"
        shutil.copy(baseline, candidate)

        # Set candidate_config in manifest
        ryaml = YAML()
        ryaml.preserve_quotes = True
        manifest_path = ws / "workspace.yaml"
        mdata = ryaml.load(manifest_path)
        mdata["candidate_config"] = "configs/candidate-system_d.yaml"
        ryaml.dump(mdata, manifest_path)

        exec_results = execute_workspace(ws)
        assert len(exec_results) == 2
        roles = {er.role for er in exec_results}
        assert "baseline" in roles
        assert "candidate" in roles

    def test_baseline_only_flag(self, tmp_path):
        """--baseline-only runs only baseline."""
        import shutil
        from axis.framework.workspaces.execute import execute_workspace
        from ruamel.yaml import YAML

        ws = _scaffold_development(tmp_path)

        # Add candidate config
        baseline = ws / "configs" / "baseline-system_d.yaml"
        candidate = ws / "configs" / "candidate-system_d.yaml"
        shutil.copy(baseline, candidate)

        ryaml = YAML()
        ryaml.preserve_quotes = True
        manifest_path = ws / "workspace.yaml"
        mdata = ryaml.load(manifest_path)
        mdata["candidate_config"] = "configs/candidate-system_d.yaml"
        ryaml.dump(mdata, manifest_path)

        exec_results = execute_workspace(ws, run_filter="baseline")
        assert len(exec_results) == 1
        assert exec_results[0].role == "baseline"

    def test_candidate_only_flag(self, tmp_path):
        """--candidate-only runs only candidate."""
        import shutil
        from axis.framework.workspaces.execute import execute_workspace
        from ruamel.yaml import YAML

        ws = _scaffold_development(tmp_path)

        baseline = ws / "configs" / "baseline-system_d.yaml"
        candidate = ws / "configs" / "candidate-system_d.yaml"
        shutil.copy(baseline, candidate)

        ryaml = YAML()
        ryaml.preserve_quotes = True
        manifest_path = ws / "workspace.yaml"
        mdata = ryaml.load(manifest_path)
        mdata["candidate_config"] = "configs/candidate-system_d.yaml"
        ryaml.dump(mdata, manifest_path)

        exec_results = execute_workspace(ws, run_filter="candidate")
        assert len(exec_results) == 1
        assert exec_results[0].role == "candidate"

    def test_candidate_only_fails_without_config(self, tmp_path):
        """--candidate-only fails if no candidate_config."""
        from axis.framework.workspaces.execute import execute_workspace

        ws = _scaffold_development(tmp_path)
        with pytest.raises(ValueError, match="No candidate_config"):
            execute_workspace(ws, run_filter="candidate")

    def test_compare_fails_without_candidate(self, tmp_path):
        """Compare must fail if no candidate result exists."""
        from axis.framework.workspaces.compare import compare_workspace
        from axis.framework.workspaces.execute import execute_workspace
        from axis.framework.workspaces.sync import sync_manifest_after_run

        ws = _scaffold_development(tmp_path)
        exec_results = execute_workspace(ws)
        er = exec_results[0]
        run_ids = [rr.run_id for rr in er.experiment_result.run_results]
        sync_manifest_after_run(
            ws, er.experiment_result.experiment_id, run_ids, er.role)

        with pytest.raises(ValueError, match="No candidate result"):
            compare_workspace(ws)

    def test_compare_succeeds_with_candidate(self, tmp_path):
        """Full workflow: baseline run → add candidate → candidate run → compare."""
        import shutil
        from axis.framework.workspaces.compare import compare_workspace
        from axis.framework.workspaces.execute import execute_workspace
        from axis.framework.workspaces.sync import (
            sync_manifest_after_compare,
            sync_manifest_after_run,
        )
        from ruamel.yaml import YAML

        ws = _scaffold_development(tmp_path)

        # 1. Run baseline
        exec_results = execute_workspace(ws, run_filter="baseline")
        er = exec_results[0]
        run_ids = [rr.run_id for rr in er.experiment_result.run_results]
        sync_manifest_after_run(
            ws, er.experiment_result.experiment_id, run_ids, er.role)

        # 2. Create candidate config
        baseline = ws / "configs" / "baseline-system_d.yaml"
        candidate = ws / "configs" / "candidate-system_d.yaml"
        shutil.copy(baseline, candidate)

        ryaml = YAML()
        ryaml.preserve_quotes = True
        manifest_path = ws / "workspace.yaml"
        mdata = ryaml.load(manifest_path)
        mdata["candidate_config"] = "configs/candidate-system_d.yaml"
        ryaml.dump(mdata, manifest_path)

        # 3. Run candidate
        exec_results = execute_workspace(ws, run_filter="candidate")
        er = exec_results[0]
        run_ids = [rr.run_id for rr in er.experiment_result.run_results]
        sync_manifest_after_run(
            ws, er.experiment_result.experiment_id, run_ids, er.role)

        # 4. Compare
        env, ws_path = compare_workspace(ws)
        sync_manifest_after_compare(ws, ws_path)

        assert env.comparison_number == 1
        assert (ws / ws_path).exists()

        # 5. Verify manifest updated
        data = yaml.safe_load((ws / "workspace.yaml").read_text())
        assert data["current_validation_comparison"] == ws_path
        assert len(data["baseline_results"]) >= 1
        assert len(data["candidate_results"]) >= 1

    def test_sync_updates_development_fields(self, tmp_path):
        """Sync populates baseline_results/candidate_results correctly."""
        ws = _scaffold_development(tmp_path)

        # Fake baseline run
        run_dir = ws / "results" / "exp-base" / "runs" / "run-0000"
        run_dir.mkdir(parents=True)
        sync_manifest_after_run(ws, "exp-base", ["run-0000"], "baseline")

        data = yaml.safe_load((ws / "workspace.yaml").read_text())
        assert "results/exp-base" in data["baseline_results"]

        # Fake candidate run
        run_dir2 = ws / "results" / "exp-cand" / "runs" / "run-0001"
        run_dir2.mkdir(parents=True)
        sync_manifest_after_run(ws, "exp-cand", ["run-0001"], "candidate")

        data = yaml.safe_load((ws / "workspace.yaml").read_text())
        assert "results/exp-cand" in data["candidate_results"]
        assert data["current_candidate_result"] == "results/exp-cand"

    def test_show_displays_development_state(self, tmp_path, capsys):
        ws = _scaffold_development(tmp_path)
        code = cli_main(["workspaces", "show", str(ws)])
        assert code == 0
        out = capsys.readouterr().out
        assert "Development state: pre-candidate" in out
        assert "Baseline config:" in out

    def test_validation_pre_candidate_info(self, tmp_path):
        ws = _scaffold_development(tmp_path)
        result = check_workspace(ws)
        assert result.is_valid
        infos = [i for i in result.issues if i.severity == "info"]
        assert any("pre-candidate" in i.message for i in infos)


# ---------------------------------------------------------------------------
# Experiment type guardrail (single_run only)
# ---------------------------------------------------------------------------


class TestExperimentTypeGuardrail:
    """Workspace mode allows OFAT for single_system, rejects for others."""

    _OFAT_CONFIG = {
        "system_type": "system_a",
        "experiment_type": "ofat",
        "parameter_path": "system.policy.temperature",
        "parameter_values": [0.5, 1.0, 2.0],
        "general": {"seed": 42},
        "execution": {"max_steps": 50},
        "logging": {"console_enabled": False},
        "world": {
            "world_type": "grid_2d",
            "grid_width": 5,
            "grid_height": 5,
        },
        "system": {
            "agent": {"initial_energy": 50, "max_energy": 100,
                      "buffer_capacity": 5},
            "policy": {"selection_mode": "sample", "temperature": 1.0,
                       "stay_suppression": 0.1, "consume_weight": 2.5},
            "transition": {"move_cost": 1.0, "consume_cost": 1.0,
                           "stay_cost": 0.5, "max_consume": 1.0,
                           "energy_gain_factor": 10.0},
        },
        "num_episodes_per_run": 1,
    }

    def _inject_ofat_config(self, ws: Path) -> None:
        """Overwrite the primary config of a workspace with an OFAT config."""
        manifest_data = yaml.safe_load((ws / "workspace.yaml").read_text())
        config_rel = manifest_data["primary_configs"][0]
        if isinstance(config_rel, dict):
            config_rel = config_rel["path"]
        (ws / config_rel).write_text(yaml.dump(self._OFAT_CONFIG))

    # --- single_system: OFAT is allowed ---

    def test_single_system_accepts_ofat(self, tmp_path):
        ws = _scaffold_single_system(tmp_path)
        self._inject_ofat_config(ws)
        result = check_workspace(ws)
        assert result.is_valid, [i.message for i in result.issues
                                 if i.severity == "error"]

    def test_single_system_runs_ofat(self, tmp_path):
        from axis.framework.workspaces.execute import execute_workspace

        ws = _scaffold_single_system(tmp_path)
        self._inject_ofat_config(ws)
        results = execute_workspace(ws)
        assert len(results) == 1

    # --- system_comparison: OFAT is rejected ---

    def test_comparison_rejects_ofat(self, tmp_path):
        ws = _scaffold_comparison(tmp_path)
        self._inject_ofat_config(ws)
        result = check_workspace(ws)
        assert not result.is_valid
        errors = [i for i in result.issues if i.severity == "error"]
        assert any("ofat" in i.message for i in errors), (
            f"Expected OFAT error, got: {[i.message for i in errors]}"
        )

    def test_comparison_run_fails_for_ofat(self, tmp_path):
        from axis.framework.workspaces.execute import execute_workspace

        ws = _scaffold_comparison(tmp_path)
        self._inject_ofat_config(ws)
        with pytest.raises(ValueError, match="OFAT is only supported"):
            execute_workspace(ws)

    def test_cli_run_fails_for_ofat_comparison(self, tmp_path, capsys):
        ws = _scaffold_comparison(tmp_path)
        self._inject_ofat_config(ws)
        code = cli_main(["workspaces", "run", str(ws)])
        assert code == 1
        err = capsys.readouterr().err
        assert "OFAT" in err or "single_run" in err

    # --- single_run always works ---

    def test_single_run_still_works(self, tmp_path):
        """Ensure that normal single_run configs are not blocked."""
        from axis.framework.workspaces.execute import execute_workspace

        ws = _scaffold_single_system(tmp_path)
        results = execute_workspace(ws)
        assert len(results) == 1


# ---------------------------------------------------------------------------
# Strict Experiment Output & Visualization tests
# ---------------------------------------------------------------------------


def _add_point_experiment_to_workspace(ws: Path, eid: str = "exp-001") -> None:
    """Add a point experiment with proper metadata to a workspace results dir."""
    from axis.framework.persistence import (
        ExperimentMetadata, ExperimentRepository, ExperimentStatus,
        RunMetadata, RunStatus,
    )
    repo = ExperimentRepository(ws / "results")
    repo.create_experiment_dir(eid)
    repo.save_experiment_metadata(eid, ExperimentMetadata(
        experiment_id=eid, created_at="2025-01-01T00:00:00",
        experiment_type="single_run", system_type="system_a",
        output_form="point", primary_run_id="run-0000",
    ))
    repo.save_experiment_status(eid, ExperimentStatus.COMPLETED)
    repo.create_run_dir(eid, "run-0000")
    repo.save_run_metadata(eid, "run-0000", RunMetadata(
        run_id="run-0000", experiment_id=eid,
        created_at="2025-01-01T00:00:00", base_seed=42,
    ))
    repo.save_run_status(eid, "run-0000", RunStatus.COMPLETED)


def _add_sweep_experiment_to_workspace(ws: Path, eid: str = "exp-002") -> None:
    """Add a sweep experiment with proper metadata to a workspace results dir."""
    from axis.framework.persistence import (
        ExperimentMetadata, ExperimentRepository, ExperimentStatus,
        RunMetadata, RunStatus,
    )
    repo = ExperimentRepository(ws / "results")
    repo.create_experiment_dir(eid)
    repo.save_experiment_metadata(eid, ExperimentMetadata(
        experiment_id=eid, created_at="2025-01-01T00:00:00",
        experiment_type="ofat", system_type="system_a",
        output_form="sweep", baseline_run_id="run-0000",
    ))
    repo.save_experiment_status(eid, ExperimentStatus.COMPLETED)
    for i in range(3):
        rid = f"run-{i:04d}"
        repo.create_run_dir(eid, rid)
        repo.save_run_metadata(eid, rid, RunMetadata(
            run_id=rid, experiment_id=eid,
            created_at="2025-01-01T00:00:00", base_seed=42 + i * 1000,
            variation_index=i, variation_value=i * 0.1, is_baseline=(i == 0),
        ))
        repo.save_run_status(eid, rid, RunStatus.COMPLETED)


class TestStrictVisualizationResolution:
    """Visualization resolution respects output form and --run flag."""

    def test_point_with_explicit_run(self, tmp_path):
        from axis.framework.workspaces.visualization import resolve_visualization_target
        ws = _scaffold_single_system(tmp_path)
        _add_point_experiment_to_workspace(ws, "exp-001")

        eid, rid, ep = resolve_visualization_target(
            ws, episode=1, experiment="exp-001", run="run-0000",
        )
        assert eid == "exp-001"
        assert rid == "run-0000"

    def test_sweep_without_run_raises(self, tmp_path):
        from axis.framework.workspaces.visualization import resolve_visualization_target
        ws = _scaffold_single_system(tmp_path)
        _add_sweep_experiment_to_workspace(ws, "exp-002")

        with pytest.raises(ValueError, match="explicit run selection"):
            resolve_visualization_target(
                ws, episode=1, experiment="exp-002",
            )

    def test_sweep_with_explicit_run(self, tmp_path):
        from axis.framework.workspaces.visualization import resolve_visualization_target
        ws = _scaffold_single_system(tmp_path)
        _add_sweep_experiment_to_workspace(ws, "exp-002")

        eid, rid, ep = resolve_visualization_target(
            ws, episode=1, experiment="exp-002", run="run-0001",
        )
        assert eid == "exp-002"
        assert rid == "run-0001"

    def test_sweep_with_invalid_run_raises(self, tmp_path):
        from axis.framework.workspaces.visualization import resolve_visualization_target
        ws = _scaffold_single_system(tmp_path)
        _add_sweep_experiment_to_workspace(ws, "exp-002")

        with pytest.raises(ValueError, match="not found in experiment"):
            resolve_visualization_target(
                ws, episode=1, experiment="exp-002", run="run-9999",
            )


class TestWorkspaceRunSummaryResolution:
    """run-summary resolves workspace-local runs using workspace semantics."""

    def test_single_system_defaults_to_latest_point_result(self, tmp_path):
        import yaml

        from axis.framework.workspaces.run_summary import (
            resolve_run_summary_target,
        )

        ws = _scaffold_single_system(tmp_path)
        _add_point_experiment_to_workspace(ws, "exp-old")
        _add_point_experiment_to_workspace(ws, "exp-new")

        data = yaml.safe_load((ws / "workspace.yaml").read_text())
        data["primary_results"] = [
            {"path": "results/exp-old", "output_form": "point"},
            {"path": "results/exp-new", "output_form": "point"},
        ]
        (ws / "workspace.yaml").write_text(yaml.dump(data))

        target = resolve_run_summary_target(ws)
        assert target.experiment_id == "exp-new"
        assert target.run_id == "run-0000"

    def test_single_system_sweep_requires_explicit_run(self, tmp_path):
        import yaml

        from axis.framework.workspaces.run_summary import (
            resolve_run_summary_target,
        )

        ws = _scaffold_single_system(tmp_path)
        _add_sweep_experiment_to_workspace(ws, "exp-sweep")

        data = yaml.safe_load((ws / "workspace.yaml").read_text())
        data["primary_results"] = [
            {"path": "results/exp-sweep", "output_form": "sweep"},
        ]
        (ws / "workspace.yaml").write_text(yaml.dump(data))

        with pytest.raises(ValueError, match="explicit run selection"):
            resolve_run_summary_target(ws)

        target = resolve_run_summary_target(
            ws, experiment="exp-sweep", run="run-0001",
        )
        assert target.experiment_id == "exp-sweep"
        assert target.run_id == "run-0001"

    def test_comparison_requires_role_and_uses_latest_role_entry(self, tmp_path):
        import yaml

        from axis.framework.persistence import (
            ExperimentMetadata, ExperimentRepository, ExperimentStatus,
            RunMetadata, RunStatus,
        )
        from axis.framework.workspaces.run_summary import (
            resolve_run_summary_target,
        )

        ws = _scaffold_comparison(tmp_path)
        repo = ExperimentRepository(ws / "results")

        def _add_point_experiment(eid: str, system_type: str) -> None:
            repo.create_experiment_dir(eid)
            repo.save_experiment_metadata(eid, ExperimentMetadata(
                experiment_id=eid,
                created_at="2025-01-01T00:00:00",
                experiment_type="single_run",
                system_type=system_type,
                output_form="point",
                primary_run_id="run-0000",
            ))
            repo.save_experiment_status(eid, ExperimentStatus.COMPLETED)
            repo.create_run_dir(eid, "run-0000")
            repo.save_run_metadata(eid, "run-0000", RunMetadata(
                run_id="run-0000",
                experiment_id=eid,
                created_at="2025-01-01T00:00:00",
                base_seed=42,
            ))
            repo.save_run_status(eid, "run-0000", RunStatus.COMPLETED)

        _add_point_experiment("ref-old", "system_a")
        _add_point_experiment("ref-new", "system_a")
        _add_point_experiment("cand-old", "system_a")
        _add_point_experiment("cand-new", "system_a")

        data = yaml.safe_load((ws / "workspace.yaml").read_text())
        data["primary_results"] = [
            {"path": "results/ref-old", "role": "reference", "output_form": "point"},
            {"path": "results/cand-old", "role": "candidate", "output_form": "point"},
            {"path": "results/ref-new", "role": "reference", "output_form": "point"},
            {"path": "results/cand-new", "role": "candidate", "output_form": "point"},
        ]
        (ws / "workspace.yaml").write_text(yaml.dump(data))

        with pytest.raises(ValueError, match="requires --role"):
            resolve_run_summary_target(ws)

        ref_target = resolve_run_summary_target(ws, role="reference")
        cand_target = resolve_run_summary_target(ws, role="candidate")
        assert ref_target.experiment_id == "ref-new"
        assert cand_target.experiment_id == "cand-new"

    def test_development_uses_baseline_and_candidate_roles(self, tmp_path):
        from axis.framework.workspaces.run_summary import (
            resolve_run_summary_target,
        )

        ws = _scaffold_development(tmp_path)
        _add_point_experiment_to_workspace(ws, "base-exp")
        _add_point_experiment_to_workspace(ws, "cand-exp")

        manifest_path = ws / "workspace.yaml"
        data = yaml.safe_load(manifest_path.read_text())
        data["baseline_results"] = ["results/base-exp"]
        data["candidate_results"] = ["results/cand-exp"]
        data["current_candidate_result"] = "results/cand-exp"
        manifest_path.write_text(yaml.dump(data))

        baseline = resolve_run_summary_target(ws, role="baseline")
        candidate = resolve_run_summary_target(ws, role="candidate")
        assert baseline.experiment_id == "base-exp"
        assert candidate.experiment_id == "cand-exp"

    def test_cli_run_summary_uses_workspace_results(self, tmp_path, capsys):
        import yaml

        from axis.framework.cli import main as cli_main

        ws = _scaffold_single_system(tmp_path)
        _add_point_experiment_to_workspace(ws, "exp-001")

        data = yaml.safe_load((ws / "workspace.yaml").read_text())
        data["primary_results"] = [
            {"path": "results/exp-001", "output_form": "point"},
        ]
        (ws / "workspace.yaml").write_text(yaml.dump(data))

        code = cli_main(["workspaces", "run-summary", str(ws)])
        captured = capsys.readouterr()
        assert code == 0
        assert "Run run-0000" in captured.out
        assert "exp-001" in captured.out

    def test_cli_run_metrics_uses_workspace_results(self, tmp_path, capsys):
        import yaml

        from axis.framework.cli import main as cli_main

        ws = _scaffold_single_system(tmp_path)
        _add_point_experiment_to_workspace(ws, "exp-001")

        data = yaml.safe_load((ws / "workspace.yaml").read_text())
        data["primary_results"] = [
            {"path": "results/exp-001", "output_form": "point"},
        ]
        (ws / "workspace.yaml").write_text(yaml.dump(data))

        code = cli_main(["workspaces", "run-metrics", str(ws)])
        captured = capsys.readouterr()
        assert code == 0
        assert "Behavioral Metrics For run-0000" in captured.out
        assert "exp-001" in captured.out


class TestStrictCompareResolution:
    """Compare resolution enforces output metadata."""

    def test_compare_fails_without_output_metadata(self, tmp_path):
        from axis.framework.persistence import (
            ExperimentMetadata, ExperimentRepository, ExperimentStatus,
            RunMetadata, RunStatus,
        )
        from axis.framework.workspaces.compare_resolution import (
            resolve_comparison_targets,
        )
        ws = _scaffold_comparison(tmp_path)
        repo = ExperimentRepository(ws / "results")
        # Create experiment without output_form
        for eid in ("exp-a", "exp-b"):
            repo.create_experiment_dir(eid)
            repo.save_experiment_metadata(eid, ExperimentMetadata(
                experiment_id=eid, created_at="2025-01-01T00:00:00",
                experiment_type="single_run", system_type="system_a",
                # No output_form!
            ))
            repo.save_experiment_status(eid, ExperimentStatus.COMPLETED)
            repo.create_run_dir(eid, "run-0000")
            repo.save_run_metadata(eid, "run-0000", RunMetadata(
                run_id="run-0000", experiment_id=eid,
                created_at="2025-01-01T00:00:00", base_seed=42,
            ))
            repo.save_run_status(eid, "run-0000", RunStatus.COMPLETED)

        with pytest.raises(ValueError, match="missing output_form"):
            resolve_comparison_targets(
                ws,
                reference_experiment="exp-a",
                candidate_experiment="exp-b",
            )

    def test_compare_defaults_to_latest_reference_and_candidate_results(
        self, tmp_path,
    ):
        import yaml

        from axis.framework.persistence import (
            ExperimentMetadata, ExperimentRepository, ExperimentStatus,
            RunMetadata, RunStatus,
        )
        from axis.framework.workspaces.compare_resolution import (
            resolve_comparison_targets,
        )

        ws = _scaffold_comparison(tmp_path)
        repo = ExperimentRepository(ws / "results")

        def _add_point_experiment(eid: str, system_type: str) -> None:
            repo.create_experiment_dir(eid)
            repo.save_experiment_metadata(eid, ExperimentMetadata(
                experiment_id=eid,
                created_at="2025-01-01T00:00:00",
                experiment_type="single_run",
                system_type=system_type,
                output_form="point",
                primary_run_id="run-0000",
            ))
            repo.save_experiment_status(eid, ExperimentStatus.COMPLETED)
            repo.create_run_dir(eid, "run-0000")
            repo.save_run_metadata(eid, "run-0000", RunMetadata(
                run_id="run-0000",
                experiment_id=eid,
                created_at="2025-01-01T00:00:00",
                base_seed=42,
            ))
            repo.save_run_status(eid, "run-0000", RunStatus.COMPLETED)

        _add_point_experiment("ref-old", "system_a")
        _add_point_experiment("cand-old", "system_a")
        _add_point_experiment("ref-new", "system_a")
        _add_point_experiment("cand-new", "system_a")

        data = yaml.safe_load((ws / "workspace.yaml").read_text())
        data["primary_results"] = [
            {
                "path": "results/ref-old",
                "role": "reference",
                "output_form": "point",
                "config": "results/ref-old/experiment_config.json",
            },
            {
                "path": "results/cand-old",
                "role": "candidate",
                "output_form": "point",
                "config": "results/cand-old/experiment_config.json",
            },
            {
                "path": "results/ref-new",
                "role": "reference",
                "output_form": "point",
                "config": "results/ref-new/experiment_config.json",
            },
            {
                "path": "results/cand-new",
                "role": "candidate",
                "output_form": "point",
                "config": "results/cand-new/experiment_config.json",
            },
        ]
        (ws / "workspace.yaml").write_text(yaml.dump(data))

        plan = resolve_comparison_targets(ws)
        assert plan.reference.experiment_id == "ref-new"
        assert plan.candidate.experiment_id == "cand-new"

    def test_compare_for_different_systems_prefers_latest_role_entries(
        self, tmp_path,
    ):
        import yaml

        from axis.framework.persistence import (
            ExperimentMetadata, ExperimentRepository, ExperimentStatus,
            RunMetadata, RunStatus,
        )
        from axis.framework.workspaces.compare_resolution import (
            resolve_comparison_targets,
        )

        ws = _scaffold_comparison(tmp_path)
        repo = ExperimentRepository(ws / "results")

        def _add_point_experiment(eid: str, system_type: str) -> None:
            repo.create_experiment_dir(eid)
            repo.save_experiment_metadata(eid, ExperimentMetadata(
                experiment_id=eid,
                created_at="2025-01-01T00:00:00",
                experiment_type="single_run",
                system_type=system_type,
                output_form="point",
                primary_run_id="run-0000",
            ))
            repo.save_experiment_status(eid, ExperimentStatus.COMPLETED)
            repo.create_run_dir(eid, "run-0000")
            repo.save_run_metadata(eid, "run-0000", RunMetadata(
                run_id="run-0000",
                experiment_id=eid,
                created_at="2025-01-01T00:00:00",
                base_seed=42,
            ))
            repo.save_run_status(eid, "run-0000", RunStatus.COMPLETED)

        _add_point_experiment("ref-old", "system_a")
        _add_point_experiment("cand-old", "system_aw")
        _add_point_experiment("ref-new", "system_a")
        _add_point_experiment("cand-new", "system_aw")

        data = yaml.safe_load((ws / "workspace.yaml").read_text())
        data["reference_system"] = "system_a"
        data["candidate_system"] = "system_aw"
        data["primary_results"] = [
            {
                "path": "results/ref-old",
                "role": "reference",
                "output_form": "point",
                "config": "results/ref-old/experiment_config.json",
            },
            {
                "path": "results/cand-old",
                "role": "candidate",
                "output_form": "point",
                "config": "results/cand-old/experiment_config.json",
            },
            {
                "path": "results/ref-new",
                "role": "reference",
                "output_form": "point",
                "config": "results/ref-new/experiment_config.json",
            },
            {
                "path": "results/cand-new",
                "role": "candidate",
                "output_form": "point",
                "config": "results/cand-new/experiment_config.json",
            },
        ]
        (ws / "workspace.yaml").write_text(yaml.dump(data))

        plan = resolve_comparison_targets(ws)
        assert plan.reference.experiment_id == "ref-new"
        assert plan.candidate.experiment_id == "cand-new"


class TestStrictManifestTyping:
    """Workspace manifest rejects legacy string-based primary_results."""

    def test_rejects_string_primary_results(self):
        with pytest.raises(Exception, match="plain string entries"):
            WorkspaceManifest.model_validate({
                "workspace_id": "test",
                "title": "Test",
                "workspace_class": "investigation",
                "workspace_type": "single_system",
                "status": "draft",
                "lifecycle_stage": "idea",
                "created_at": "2026-04-19",
                "question": "Test?",
                "system_under_test": "system_a",
                "primary_results": ["results/exp-001"],
            })

    def test_accepts_dict_primary_results(self):
        m = WorkspaceManifest.model_validate({
            "workspace_id": "test",
            "title": "Test",
            "workspace_class": "investigation",
            "workspace_type": "single_system",
            "status": "draft",
            "lifecycle_stage": "idea",
            "created_at": "2026-04-19",
            "question": "Test?",
            "system_under_test": "system_a",
            "primary_results": [
                {"path": "results/exp-001", "output_form": "point"},
            ],
        })
        from axis.framework.workspaces.types import ResultEntry
        assert len(m.primary_results) == 1
        assert isinstance(m.primary_results[0], ResultEntry)
        assert m.primary_results[0].path == "results/exp-001"
