"""Workspace measurement service — orchestrates run/compare/log planning."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WorkspaceMeasurementServiceResult:
    """Summary of one automated workspace measurement workflow."""

    measurement_number: int
    measurement_dir: str
    label: str
    comparison_number: int
    comparison_log_path: str
    run_summary_log_path: str
    run_summary_role: str
    run_experiment_ids: list[str]


class WorkspaceMeasurementService:
    """Coordinates the system-comparison measurement workflow."""

    def __init__(
        self,
        run_service: object,
        compare_service: object,
        load_manifest_fn: Callable[..., Any],
    ) -> None:
        self._run_service = run_service
        self._compare_service = compare_service
        self._load_manifest_fn = load_manifest_fn

    def measure(
        self,
        workspace_path: Path,
        *,
        label: str | None = None,
        allow_world_changes: bool = False,
        override_guard: bool = False,
        run_notes: str | None = None,
        extension_catalog: object | None = None,
        progress: object | None = None,
    ) -> WorkspaceMeasurementServiceResult:
        """Execute run + compare and plan the exported measurement logs."""
        from axis.framework.workspaces.types import (
            MeasurementWorkflowConfig,
            WorkspaceType,
        )

        ws = Path(workspace_path)
        manifest = self._load_manifest_fn(ws)
        if manifest.workspace_type != WorkspaceType.SYSTEM_COMPARISON:
            raise ValueError(
                "workspaces measure is only supported for "
                "system_comparison workspaces. "
                f"Workspace '{manifest.workspace_id}' has type "
                f"'{manifest.workspace_type.value}'."
            )

        workflow = manifest.measurement_workflow or MeasurementWorkflowConfig()
        measurement_root = ws / workflow.root_dir
        measurement_root.mkdir(parents=True, exist_ok=True)

        measurement_number = _next_measurement_number(
            measurement_root,
            workflow.experiment_dir_pattern,
        )
        effective_label = (
            label if label is not None else
            workflow.label_pattern.format(number=measurement_number)
        )
        run_summary_role = workflow.default_run_summary_role

        measurement_dir = (
            measurement_root /
            workflow.experiment_dir_pattern.format(number=measurement_number)
        )
        measurement_dir.mkdir(parents=True, exist_ok=False)

        run_kwargs = {
            "allow_world_changes": allow_world_changes,
            "override_guard": override_guard,
            "run_notes": run_notes,
        }
        if progress is not None:
            run_kwargs["progress"] = progress
        run_results = self._run_service.execute(ws, **run_kwargs)

        compare_kwargs = {
            "allow_world_changes": allow_world_changes,
            "extension_catalog": extension_catalog,
        }
        if progress is not None:
            compare_kwargs["progress"] = progress
        compare_result = self._compare_service.compare(ws, **compare_kwargs)

        tokens = {
            "label": effective_label,
            "number": measurement_number,
            "role": run_summary_role,
        }
        comparison_log_path = measurement_dir / workflow.comparison_log_pattern.format(
            **tokens
        )
        run_summary_log_path = measurement_dir / workflow.run_summary_log_pattern.format(
            **tokens
        )

        return WorkspaceMeasurementServiceResult(
            measurement_number=measurement_number,
            measurement_dir=str(measurement_dir.relative_to(ws)),
            label=effective_label,
            comparison_number=compare_result.comparison_number,
            comparison_log_path=str(comparison_log_path.relative_to(ws)),
            run_summary_log_path=str(run_summary_log_path.relative_to(ws)),
            run_summary_role=run_summary_role,
            run_experiment_ids=[result.experiment_id for result in run_results],
        )


def _next_measurement_number(root: Path, pattern: str) -> int:
    """Return the next measurement number for *pattern* under *root*."""
    regex = _numbered_pattern_regex(pattern)
    seen: list[int] = []
    for path in root.iterdir():
        if not path.is_dir():
            continue
        match = regex.fullmatch(path.name)
        if match:
            seen.append(int(match.group("number")))
    return (max(seen) + 1) if seen else 1


def _numbered_pattern_regex(pattern: str) -> re.Pattern[str]:
    """Convert a '{number}' pattern into a compiled regex."""
    escaped = re.escape(pattern)
    return re.compile(
        "^" + escaped.replace(r"\{number\}", r"(?P<number>\d+)") + "$"
    )
