"""Small plotting helpers for workspace measurement rendering."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


def create_figure(*, figsize: tuple[float, float] = (8.0, 5.0)):
    """Create a matplotlib figure/axes pair with project-default sizing."""
    fig, ax = plt.subplots(figsize=figsize)
    return fig, ax


def finalize_plot(
    fig,
    output_path: Path,
    *,
    title: str | None = None,
) -> None:
    """Apply final layout and save one plot."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if title:
        fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
