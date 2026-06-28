"""SDK contracts for series measurement plot extensions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class GeneratedPlotArtifact:
    """Descriptor for one generated measurement plot."""

    plot_id: str
    level: str  # "series" or "experiment"
    plot_group: str  # "series_overview" | "experiment_comparison" | "system_specific" | "experiment_system_specific"
    relative_output_path: str
    title: str | None = None
    description: str | None = None
    system_type: str | None = None
    producer_kind: str = "framework"  # "framework" | "system_extension"
    producer_system_type: str | None = None


@dataclass(frozen=True)
class SeriesMeasurementPlotRequest:
    """Plain-data request passed into system-specific plot extensions."""

    workspace_path: Path
    series_id: str
    workspace_type: str
    measurements_root: Path
    series_plots_root: Path
    experiment_plot_roots: dict[str, Path]
    experiments: tuple[dict[str, Any], ...]


class MeasurementPlotExtensionProtocol(Protocol):
    """Protocol for system-specific series measurement plot extensions."""

    def __call__(
        self,
        request: SeriesMeasurementPlotRequest,
    ) -> list[GeneratedPlotArtifact]:
        """Generate one or more plots and return their descriptors."""
        ...
