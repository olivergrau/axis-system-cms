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
        *,
        config_overrides_by_role: dict[str, str] | None = None,
        allow_world_changes: bool = False,
        override_guard: bool = False,
        run_notes: str | None = None,
        progress: object | None = None,
    ) -> list[RunServiceResult]:
        """Execute all run targets and sync the manifest.

        Returns a summary per experiment executed.
        """
        from axis.framework.cli import _load_config_file
        from axis.framework.workspaces.config_changes import (
            has_same_config_as_previous_result,
        )
        from axis.framework.workspaces.resolution import resolve_run_targets
        from axis.framework.workspaces.types import load_manifest

        ws = Path(workspace_path)
        manifest = load_manifest(ws)
        if manifest.status.value == "closed":
            raise ValueError(
                "Workspace is closed; no further executions are allowed."
            )
        manifest_results = list(manifest.primary_results or [])
        plan = resolve_run_targets(ws, run_filter=run_filter)

        unchanged_targets: list[str] = []
        if not override_guard:
            for target in plan.targets:
                override_path = None
                if config_overrides_by_role is not None:
                    override_path = config_overrides_by_role.get(target.role)
                config_path = Path(override_path) if override_path else (ws / target.config_path)
                config = _load_config_file(config_path)
                current_config = config.model_dump(mode="json")
                if has_same_config_as_previous_result(
                    ws,
                    current_config,
                    manifest_results,
                    target.role,
                    ignore_world=not allow_world_changes,
                ):
                    unchanged_targets.append(target.config_path)

        if unchanged_targets and len(unchanged_targets) == len(plan.targets):
            if len(unchanged_targets) == 1:
                raise ValueError(
                    "Workspace run aborted: no config changes detected for "
                    f"'{unchanged_targets[0]}' compared to the previous "
                    "comparable result."
                )
            paths = ", ".join(f"'{p}'" for p in unchanged_targets)
            raise ValueError(
                "Workspace run aborted: no config changes detected for "
                f"{paths} compared to their previous comparable results."
            )

        execute_kwargs: dict[str, Any] = {"run_filter": run_filter}
        if config_overrides_by_role is not None:
            execute_kwargs["config_overrides_by_role"] = config_overrides_by_role
        if progress is not None:
            execute_kwargs["progress"] = progress
        exec_results = self._execute_fn(ws, **execute_kwargs)

        summaries: list[RunServiceResult] = []
        for er in exec_results:
            run_ids = [rr.run_id for rr in er.experiment_result.run_results]
            config = er.experiment_result.experiment_config
            execution = getattr(config, "execution", None)
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
                trace_mode=getattr(execution, "trace_mode", None),
                system_type=config.system_type,
                primary_run_id=p_run,
                baseline_run_id=b_run,
                run_notes=run_notes,
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
        from axis.framework.workspaces.types import load_manifest

        ws = Path(workspace_path)
        manifest = load_manifest(ws)
        if manifest.status.value == "closed":
            raise ValueError(
                "Workspace is closed; candidate config cannot be changed."
            )
        if not (ws / config_path).exists():
            raise ValueError(
                f"Config file does not exist: {ws / config_path}"
            )

        manifest_path = ws / "workspace.yaml"
        yaml, data = self._load_yaml_roundtrip_fn(manifest_path)
        self._set_candidate_config_fn(data, config_path)
        self._save_yaml_roundtrip_fn(manifest_path, yaml, data)
