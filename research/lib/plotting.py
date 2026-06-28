"""Small plotting helpers for research notebooks."""

from __future__ import annotations

from typing import Iterable, Sequence


def ensure_matplotlib():
    """Import matplotlib lazily with a clear error if it is unavailable."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - import guard
        raise RuntimeError(
            "matplotlib is required for notebook plotting. "
            "Rebuild the devcontainer or install research dependencies."
        ) from exc
    return plt


def lines_plot(
    series: Sequence[dict[str, object]],
    *,
    title: str,
    xlabel: str,
    ylabel: str,
):
    """Create a styled multi-line plot and return ``(fig, ax)``.

    Each series entry must provide:

    - ``x``: x values
    - ``y``: y values

    Optional keys:

    - ``label``: legend label
    - ``linewidth``: line width override
    """
    plt = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(8, 4.5))

    any_labels = False
    for entry in series:
        x = entry["x"]
        y = entry["y"]
        label = entry.get("label")
        linewidth = entry.get("linewidth", 2.0)
        ax.plot(list(x), list(y), linewidth=linewidth, label=label)
        any_labels = any_labels or label is not None

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    if any_labels:
        ax.legend()
    fig.tight_layout()
    return fig, ax


def line_plot(
    x: Iterable[float],
    y: Iterable[float],
    *,
    label: str | None = None,
    title: str,
    xlabel: str,
    ylabel: str,
):
    """Create a single-line plot via ``lines_plot`` for API compatibility."""
    return lines_plot(
        [
            {
                "x": x,
                "y": y,
                "label": label,
            }
        ],
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
    )


def bar_plot(
    labels: Iterable[str],
    values: Iterable[float],
    *,
    title: str,
    ylabel: str,
):
    """Create a simple styled bar plot and return ``(fig, ax)``."""
    plt = ensure_matplotlib()
    labels_list = list(labels)
    values_list = list(values)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(labels_list, values_list)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(True, axis="y", alpha=0.3)
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    return fig, ax
