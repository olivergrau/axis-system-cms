"""Shared text rendering helpers for the AXIS CLI."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import TextIO


def _style_enabled(stream: TextIO, enabled: bool | None) -> bool:
    """Return whether semantic ANSI styling should be applied."""
    if enabled is not None:
        return enabled
    if os.getenv("NO_COLOR"):
        return False
    isatty = getattr(stream, "isatty", None)
    return bool(isatty and isatty())


@dataclass(slots=True)
class CLITextOutput:
    """Small semantic text renderer for human-facing CLI output."""

    stream: TextIO = sys.stdout
    style: bool | None = None

    def line(self, text: str = "") -> None:
        print(text, file=self.stream)

    def blank(self) -> None:
        self.line()

    def title(self, text: str) -> None:
        self.line(self._decorate(text, role="title"))

    def section(self, text: str) -> None:
        self.blank()
        self.line(self._decorate(text, role="section"))

    def kv(self, label: str, value: object, *, indent: int = 2) -> None:
        self.line(f"{' ' * indent}{label}: {value}")

    def list_row(self, *parts: object, indent: int = 2) -> None:
        rendered = "  ".join(str(part) for part in parts if part not in (None, ""))
        self.line(f"{' ' * indent}{rendered}")

    def info(self, message: str) -> None:
        self.line(self._prefix("Info", message, role="info"))

    def success(self, message: str) -> None:
        self.line(self._prefix("Completed", message, role="success"))

    def warning(self, message: str) -> None:
        self.line(self._prefix("Warning", message, role="warning"))

    def error(self, message: str, *, hint: str | None = None) -> None:
        self.line(self._prefix("Error", message, role="error"))
        if hint:
            self.hint(hint)

    def hint(self, message: str) -> None:
        self.line(self._prefix("Hint", message, role="secondary", indent=2))

    def styled(self, text: str, *, role: str) -> str:
        """Return *text* decorated for the given semantic role."""
        return self._decorate(text, role=role)

    def _prefix(
        self,
        prefix: str,
        message: str,
        *,
        role: str,
        indent: int = 0,
    ) -> str:
        rendered_prefix = self._decorate(f"{prefix}:", role=role)
        return f"{' ' * indent}{rendered_prefix} {message}"

    def _decorate(self, text: str, *, role: str) -> str:
        if not _style_enabled(self.stream, self.style):
            return text
        code = {
            "title": "1",
            "section": "1",
            "emphasis": "1",
            "success": "1;32",
            "warning": "1;33",
            "error": "1;31",
            "info": "1;36",
            "secondary": "2",
            "diff": "1;33",
        }.get(role)
        if not code:
            return text
        return f"\033[{code}m{text}\033[0m"


def stdout_output(*, style: bool | None = None) -> CLITextOutput:
    """Create a CLI text output bound to stdout."""
    return CLITextOutput(stream=sys.stdout, style=style)


def stderr_output(*, style: bool | None = None) -> CLITextOutput:
    """Create a CLI text output bound to stderr."""
    return CLITextOutput(stream=sys.stderr, style=style)


def print_error(message: str, *, hint: str | None = None) -> None:
    """Render a normalized error line to stderr."""
    stderr_output().error(message, hint=hint)


def fail(message: str, *, hint: str | None = None, exit_code: int = 1) -> None:
    """Render an error to stderr and exit."""
    print_error(message, hint=hint)
    raise SystemExit(exit_code)
