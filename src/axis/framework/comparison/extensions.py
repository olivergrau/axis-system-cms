"""Extension dispatch for system-specific analysis (WP-09)."""

from __future__ import annotations

from typing import Any

from axis.framework.comparison.types import AlignmentSummary
from axis.sdk.trace import BaseEpisodeTrace

# Registry: system_type -> callable(ref, cand, alignment) -> dict
_EXTENSION_REGISTRY: dict[
    str,
    # Callable[[BaseEpisodeTrace, BaseEpisodeTrace, AlignmentSummary], dict]
    Any,
] = {}


def register_extension(
    system_type: str,
) -> Any:  # decorator
    """Decorator to register a comparison extension for a system type."""
    def decorator(func: Any) -> Any:
        _EXTENSION_REGISTRY[system_type] = func
        return func
    return decorator


def build_system_specific_analysis(
    reference: BaseEpisodeTrace,
    candidate: BaseEpisodeTrace,
    alignment: AlignmentSummary,
) -> dict[str, Any] | None:
    """Run system-specific analysis if an extension is registered.

    Dispatches based on the *candidate* system type.
    """
    ext = _EXTENSION_REGISTRY.get(candidate.system_type)
    if ext is None:
        return None
    return ext(reference, candidate, alignment)
