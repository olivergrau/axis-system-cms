"""Path helpers for AXIS research notebooks and scripts."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Return the repository root from the research package location."""
    return Path(__file__).resolve().parents[2]


def research_root() -> Path:
    """Return the research directory root."""
    return repo_root() / "research"


def workspace_path(workspace_id: str) -> Path:
    """Return the absolute path to one workspace directory."""
    return repo_root() / "workspaces" / workspace_id
