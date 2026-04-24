"""Repository-backed loading helpers for behavioral metrics computation."""

from __future__ import annotations

import re

from axis.sdk.trace import BaseEpisodeTrace

_EPISODE_RE = re.compile(r"episode_(\d{4})\.json$")


def load_run_episode_traces(
    repo,
    experiment_id: str,
    run_id: str,
) -> tuple[BaseEpisodeTrace, ...]:
    """Load all replay-capable episode traces for one run."""
    files = repo.list_episode_files(experiment_id, run_id)
    episode_indices: list[int] = []
    for path in files:
        match = _EPISODE_RE.fullmatch(path.name)
        if match is None:
            continue
        episode_indices.append(int(match.group(1)))
    return tuple(
        repo.load_episode_trace(experiment_id, run_id, episode_index)
        for episode_index in episode_indices
    )
