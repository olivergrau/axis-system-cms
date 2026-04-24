"""Extension dispatch for system-specific behavioral metrics."""

from __future__ import annotations

from typing import Any

from axis.framework.metrics.types import StandardBehaviorMetrics
from axis.sdk.metrics import MetricExtensionProtocol
from axis.sdk.trace import BaseEpisodeTrace

_METRIC_EXTENSION_REGISTRY: dict[str, MetricExtensionProtocol] = {}


def register_metric_extension(system_type: str) -> Any:
    """Decorator to register a behavioral metric extension for a system type."""

    def decorator(func: MetricExtensionProtocol) -> MetricExtensionProtocol:
        _METRIC_EXTENSION_REGISTRY[system_type] = func
        return func

    return decorator


def registered_metric_extensions() -> tuple[str, ...]:
    """Return all system types with registered metric extensions."""
    return tuple(_METRIC_EXTENSION_REGISTRY.keys())


def build_system_behavior_metrics(
    system_type: str,
    episode_traces: tuple[BaseEpisodeTrace, ...],
    standard_metrics: StandardBehaviorMetrics,
    extension_catalog: Any | None = None,
) -> dict[str, Any] | None:
    """Run the system-specific behavioral metrics extension if available."""
    if extension_catalog is not None:
        ext = extension_catalog.get_optional(system_type)
    else:
        ext = _METRIC_EXTENSION_REGISTRY.get(system_type)
    if ext is None:
        return None
    return ext(episode_traces, standard_metrics)
