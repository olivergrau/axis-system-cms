"""SDK protocol for system-specific comparison extensions."""

from __future__ import annotations

from typing import Any, Protocol

from axis.sdk.trace import BaseEpisodeTrace


class ComparisonExtensionProtocol(Protocol):
    """Contract for system-specific comparison analysis functions.

    Extensions receive the reference and candidate episode traces plus
    alignment information, and return a dict of system-specific metrics
    (or ``None`` if no analysis is applicable).
    """

    def __call__(
        self,
        reference: BaseEpisodeTrace,
        candidate: BaseEpisodeTrace,
        alignment: Any,
    ) -> dict[str, Any] | None: ...
