"""Notebook session helpers for the AXIS research layer."""

from __future__ import annotations

import sys
from pathlib import Path

from .paths import repo_root


def setup_notebook(*, use_inline_plots: bool = True) -> Path:
    """Prepare an AXIS notebook session and return the repo root.

    This helper:

    - ensures the repository root is on ``sys.path``
    - optionally enables inline matplotlib output
    - returns the repository root for convenient path construction

    It assumes the caller can already import ``research.lib``. For notebooks
    opened from a nested directory, use the local ``_bootstrap.py`` helper in
    that notebook folder first.
    """
    root = repo_root()
    for candidate in (root, root / "src"):
        candidate_str = str(candidate)
        if candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)

    if use_inline_plots:
        try:
            from IPython import get_ipython
            from matplotlib_inline.backend_inline import set_matplotlib_formats
        except ImportError:
            pass
        else:
            shell = get_ipython()
            if shell is not None:
                set_matplotlib_formats("svg")

    return root
