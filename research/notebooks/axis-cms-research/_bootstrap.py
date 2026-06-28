"""Notebook-local bootstrap for the AXIS research track.

This module is intentionally placed next to the notebooks so it can be
imported before the repository root is on ``sys.path``.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_repo_root_on_path() -> Path:
    """Discover the repository root and prepend it to ``sys.path``."""
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / "research" / "lib" / "__init__.py").exists():
            root_str = str(candidate)
            if root_str not in sys.path:
                sys.path.insert(0, root_str)
            return candidate
    raise RuntimeError("Could not locate the AXIS repository root from notebook bootstrap.")


_ensure_repo_root_on_path()

from research.lib.notebook_setup import setup_notebook

__all__ = ["setup_notebook"]
