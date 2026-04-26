"""CLI-friendly progress reporting helpers."""

from __future__ import annotations

from typing import Any


class NullProgressReporter:
    """No-op progress reporter used for JSON mode and tests."""

    def __enter__(self) -> NullProgressReporter:
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None

    def add_task(self, description: str, total: float | None = None) -> int:
        return 0

    def advance(self, task_id: int, advance: float = 1) -> None:
        return None

    def update(
        self,
        task_id: int,
        *,
        description: str | None = None,
        completed: float | None = None,
        total: float | None = None,
    ) -> None:
        return None


class RichProgressReporter:
    """Thin wrapper around ``rich.progress.Progress``."""

    def __init__(self) -> None:
        from rich.progress import (
            BarColumn,
            MofNCompleteColumn,
            Progress,
            SpinnerColumn,
            TaskProgressColumn,
            TextColumn,
            TimeElapsedColumn,
            TimeRemainingColumn,
        )

        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            transient=False,
        )

    def __enter__(self) -> RichProgressReporter:
        self._progress.start()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self._progress.stop()

    def add_task(self, description: str, total: float | None = None) -> int:
        return int(self._progress.add_task(description, total=total))

    def advance(self, task_id: int, advance: float = 1) -> None:
        self._progress.advance(task_id, advance=advance)

    def update(
        self,
        task_id: int,
        *,
        description: str | None = None,
        completed: float | None = None,
        total: float | None = None,
    ) -> None:
        kwargs: dict[str, Any] = {}
        if description is not None:
            kwargs["description"] = description
        if completed is not None:
            kwargs["completed"] = completed
        if total is not None:
            kwargs["total"] = total
        if kwargs:
            self._progress.update(task_id, **kwargs)


def create_progress_reporter(enabled: bool) -> NullProgressReporter | RichProgressReporter:
    """Return a real or no-op reporter depending on output mode."""
    if enabled:
        return RichProgressReporter()
    return NullProgressReporter()
