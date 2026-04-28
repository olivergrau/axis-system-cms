"""Notes scaffold generation for experiment series execution."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SeriesNotesExperiment:
    """Minimal experiment note scaffold payload."""

    experiment_id: str
    title: str
    measurement_dir: str
    hypothesis: list[str]


def render_notes_scaffold(
    *,
    series_title: str | None,
    experiments: list[SeriesNotesExperiment],
) -> str:
    """Render a fresh ``notes.md`` scaffold for one completed series."""
    title = series_title or "Experiment Series Notes"
    lines: list[str] = [f"# {title}", "", "## Context", "", "TBD", ""]
    for experiment in experiments:
        lines.extend([
            f"# {experiment.title}",
            "",
            f"## Experiment folder: {experiment.measurement_dir}",
            "",
            "### Hypothesis",
            "",
        ])
        if experiment.hypothesis:
            for item in experiment.hypothesis:
                lines.append(f"* {item}")
        else:
            lines.append("* TBD")
        lines.extend([
            "",
            "### Key Observations",
            "",
            "* TBD",
            "",
            "### Interpretation",
            "",
            "* TBD",
            "",
            "### Conclusion",
            "",
            "* TBD",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"
