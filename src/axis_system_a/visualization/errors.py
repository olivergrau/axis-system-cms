"""Exception hierarchy for the Visualization Layer.

All visualization-specific errors inherit from ReplayError,
allowing callers to catch broadly or narrowly as needed.
"""

from __future__ import annotations


class ReplayError(Exception):
    """Base exception for all visualization replay errors."""


class ExperimentNotFoundError(ReplayError):
    """Raised when a requested experiment does not exist in the repository."""


class RunNotFoundError(ReplayError):
    """Raised when a requested run does not exist within an experiment."""


class EpisodeNotFoundError(ReplayError):
    """Raised when a requested episode does not exist within a run."""


class ReplayContractViolation(ReplayError):
    """Raised when an episode fails replay contract validation.

    Carries a tuple of human-readable violation descriptions.
    """

    def __init__(self, violations: tuple[str, ...], *args: object) -> None:
        self.violations = violations
        msg = f"{len(violations)} replay contract violation(s): {'; '.join(violations)}"
        super().__init__(msg, *args)


class MalformedArtifactError(ReplayError):
    """Raised when a persisted artifact cannot be deserialized or reconstructed."""


class StepOutOfBoundsError(ReplayError):
    """Raised when step_index is outside the valid range [0, total_steps-1]."""

    def __init__(self, step_index: int, total_steps: int) -> None:
        self.step_index = step_index
        self.total_steps = total_steps
        super().__init__(
            f"Step index {step_index} out of bounds "
            f"(valid range: 0..{total_steps - 1})"
        )


class PhaseNotAvailableError(ReplayError):
    """Raised when the requested phase has no valid snapshot at the given step."""

    def __init__(self, step_index: int, phase: object) -> None:
        self.step_index = step_index
        self.phase = phase
        super().__init__(
            f"Phase {phase} not available at step index {step_index}"
        )
