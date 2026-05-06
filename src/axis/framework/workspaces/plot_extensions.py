"""Extension dispatch for system-specific series measurement plots."""

from __future__ import annotations

from typing import Any

from axis.sdk.measurement_plots import (
    GeneratedPlotArtifact,
    MeasurementPlotExtensionProtocol,
    SeriesMeasurementPlotRequest,
)

_MEASUREMENT_PLOT_EXTENSION_REGISTRY: dict[str, MeasurementPlotExtensionProtocol] = {}


def register_measurement_plot_extension(system_type: str) -> Any:
    """Decorator to register a system-specific measurement plot extension."""

    def decorator(
        func: MeasurementPlotExtensionProtocol,
    ) -> MeasurementPlotExtensionProtocol:
        _MEASUREMENT_PLOT_EXTENSION_REGISTRY[system_type] = func
        return func

    return decorator


def registered_measurement_plot_extensions() -> tuple[str, ...]:
    """Return all system types with registered measurement plot extensions."""
    return tuple(_MEASUREMENT_PLOT_EXTENSION_REGISTRY.keys())


def build_system_measurement_plots(
    system_type: str,
    request: SeriesMeasurementPlotRequest,
    *,
    extension_catalog: Any | None = None,
) -> list[GeneratedPlotArtifact]:
    """Run the system-specific plot extension if available."""
    if extension_catalog is not None:
        ext = extension_catalog.get_optional(system_type)
    else:
        ext = _MEASUREMENT_PLOT_EXTENSION_REGISTRY.get(system_type)
    if ext is None:
        return []
    return ext(request)
