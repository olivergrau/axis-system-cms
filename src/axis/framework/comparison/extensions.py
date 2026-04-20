"""Extension dispatch for system-specific analysis (WP-09)."""

from __future__ import annotations

from typing import Any

from axis.framework.comparison.types import AlignmentSummary
from axis.sdk.comparison import ComparisonExtensionProtocol
from axis.sdk.trace import BaseEpisodeTrace

_EXTENSION_REGISTRY: dict[str, ComparisonExtensionProtocol] = {}


def register_extension(
    system_type: str,
) -> Any:  # decorator
    """Decorator to register a comparison extension for a system type."""
    def decorator(func: ComparisonExtensionProtocol) -> ComparisonExtensionProtocol:
        _EXTENSION_REGISTRY[system_type] = func
        return func
    return decorator


def registered_extensions() -> tuple[str, ...]:
    """Return the system types that have a registered comparison extension."""
    return tuple(_EXTENSION_REGISTRY.keys())


def build_system_specific_analysis(
    reference: BaseEpisodeTrace,
    candidate: BaseEpisodeTrace,
    alignment: AlignmentSummary,
    extension_catalog: Any | None = None,
) -> dict[str, Any] | None:
    """Run system-specific analysis if an extension is registered.

    Dispatches based on the *candidate* system type.  If
    *extension_catalog* is provided, uses catalog lookup instead of
    the global registry.
    """
    if extension_catalog is not None:
        ext = extension_catalog.get_optional(candidate.system_type)
    else:
        ext = _EXTENSION_REGISTRY.get(candidate.system_type)
    if ext is None:
        return None
    return ext(reference, candidate, alignment)
