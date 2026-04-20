"""Workspace run service — orchestrates execution + manifest sync."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RunServiceResult:
    """Summary of a single experiment execution within a workspace."""

    experiment_id: str
    num_runs: int
    role: str


class WorkspaceRunService:
    """Coordinates workspace execution and post-run manifest sync.

    Dependencies are injected via the constructor so that the
    composition root (``build_context``) controls wiring.
    """

    def __init__(
        self,
        execute_fn: Callable[..., Any],
        sync_fn: Callable[..., None],
        set_candidate_config_fn: Callable[..., None],
        load_yaml_roundtrip_fn: Callable[..., Any],
        save_yaml_roundtrip_fn: Callable[..., None],
    ) -> None:
        self._execute_fn = execute_fn
        self._sync_fn = sync_fn
        self._set_candidate_config_fn = set_candidate_config_fn
        self._load_yaml_roundtrip_fn = load_yaml_roundtrip_fn
        self._save_yaml_roundtrip_fn = save_yaml_roundtrip_fn

    def execute(
        self,
        workspace_path: Path,
        run_filter: str | None = None,
    ) -> list[RunServiceResult]:
        """Execute all run targets and sync the manifest.

        Returns a summary per experiment executed.
        """
        ws = Path(workspace_path)
        exec_results = self._execute_fn(ws, run_filter=run_filter)

        summaries: list[RunServiceResult] = []
        for er in exec_results:
            run_ids = [rr.run_id for rr in er.experiment_result.run_results]
            config = er.experiment_result.experiment_config
            if config.experiment_type.value == "single_run":
                o_form = "point"
                p_run = "run-0000"
                b_run = None
            else:
                o_form = "sweep"
                p_run = None
                b_run = "run-0000"
            self._sync_fn(
                ws, er.experiment_result.experiment_id, run_ids, er.role,
                config_path=er.config_path,
                output_form=o_form,
                system_type=config.system_type,
                primary_run_id=p_run,
                baseline_run_id=b_run,
            )
            summaries.append(RunServiceResult(
                experiment_id=er.experiment_result.experiment_id,
                num_runs=er.experiment_result.summary.num_runs,
                role=er.role,
            ))
        return summaries

    def set_candidate(
        self,
        workspace_path: Path,
        config_path: str,
    ) -> None:
        """Set the candidate config for a development workspace.

        Validates the config file exists, then delegates the manifest
        mutation to the manifest mutator via roundtrip YAML IO.
        """
        ws = Path(workspace_path)
        if not (ws / config_path).exists():
            raise ValueError(
                f"Config file does not exist: {ws / config_path}"
            )

        manifest_path = ws / "workspace.yaml"
        yaml, data = self._load_yaml_roundtrip_fn(manifest_path)
        self._set_candidate_config_fn(data, config_path)
        self._save_yaml_roundtrip_fn(manifest_path, yaml, data)
