"""SDK protocol for system-specific behavioral metric extensions."""

from __future__ import annotations

from typing import Any, Protocol

from axis.sdk.trace import BaseEpisodeTrace


class MetricExtensionProtocol(Protocol):
    """Contract for system-specific run-level behavioral metric analysis."""

    def __call__(
        self,
        episode_traces: tuple[BaseEpisodeTrace, ...],
        standard_metrics: Any,
    ) -> dict[str, Any] | None: ...
