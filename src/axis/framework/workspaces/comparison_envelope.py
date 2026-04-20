"""Workspace comparison envelope — self-contained comparison result.

Wraps a ``RunComparisonResult`` with full copies of the experiment
configs used, a timestamp, and a sequential identifier.  This ensures
each comparison result is self-contained and interpretable even after
the source configs have been modified.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class WorkspaceComparisonEnvelope(BaseModel):
    """Self-contained workspace comparison result.

    Embeds the full experiment configurations alongside the comparison
    metrics so that results remain interpretable across iterative
    config-change cycles.
    """

    model_config = ConfigDict(frozen=True)

    #: Sequential comparison number within this workspace (1, 2, 3, …).
    comparison_number: int

    #: ISO-8601 timestamp of when the comparison was produced.
    timestamp: str

    #: Full copy of the reference experiment configuration at comparison time.
    reference_config: dict

    #: Full copy of the candidate experiment configuration at comparison time.
    candidate_config: dict

    #: The framework-level comparison result (RunComparisonResult payload).
    comparison_result: dict
