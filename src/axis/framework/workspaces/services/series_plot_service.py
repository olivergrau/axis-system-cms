"""Workspace service for standalone rendering of series measurement plots."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SeriesPlotServiceResult:
    """Summary of one series plot rendering pass."""

    series_id: str
    generated_count: int
    failure_count: int
    manifest_path: str
    report_path: str


class WorkspaceSeriesPlotService:
    """Coordinates workspace series plot rendering."""

    def __init__(
        self,
        render_fn: Callable[..., object],
    ) -> None:
        self._render_fn = render_fn

    def render(
        self,
        workspace_path: Path,
        *,
        series_id: str,
        extension_catalog: object | None = None,
    ) -> SeriesPlotServiceResult:
        """Render plots for one registered series."""
        render_kwargs = {"series_id": series_id}
        if extension_catalog is not None:
            render_kwargs["extension_catalog"] = extension_catalog
        result = self._render_fn(Path(workspace_path), **render_kwargs)
        return SeriesPlotServiceResult(
            series_id=result.series_id,
            generated_count=len(result.generated),
            failure_count=len(result.failures),
            manifest_path=result.manifest_path,
            report_path=result.report_path,
        )
