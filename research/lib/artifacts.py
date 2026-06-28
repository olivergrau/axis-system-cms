"""Helpers for loading common AXIS research artifacts."""

from __future__ import annotations

import ast
import csv
import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> Any:
    """Load a JSON artifact and return the decoded object."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_csv_rows(path: str | Path) -> list[dict[str, Any]]:
    """Load a CSV file into plain Python row dictionaries.

    Numeric-looking values are converted to int/float where possible.
    Embedded dict-like string values such as metric-extension columns are
    parsed with ``ast.literal_eval``.
    """
    with Path(path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [_normalize_row(row) for row in reader]


def load_series_summary(path: str | Path) -> dict[str, Any]:
    """Load a ``series-summary.json`` artifact."""
    data = load_json(path)
    if not isinstance(data, dict):
        raise ValueError(f"Series summary must be a JSON object: {path}")
    return data


def load_series_metrics_csv(path: str | Path) -> list[dict[str, Any]]:
    """Load a ``series-metrics.csv`` artifact into normalized rows."""
    return load_csv_rows(path)


def _normalize_row(row: dict[str, str]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in row.items():
        normalized[key] = _parse_scalar(value)
    return normalized


def _parse_scalar(value: str | None) -> Any:
    if value is None:
        return None
    stripped = value.strip()
    if stripped == "":
        return None
    if stripped == "None":
        return None
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            return ast.literal_eval(stripped)
        except (SyntaxError, ValueError):
            return stripped
    try:
        if any(ch in stripped for ch in (".", "e", "E")):
            return float(stripped)
        return int(stripped)
    except ValueError:
        return stripped
