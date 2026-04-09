"""Repository-backed access layer for the Visualization Layer.

Wraps ExperimentRepository to provide visualization-oriented read-only
access with replay-specific validation and error signaling.
"""

from __future__ import annotations

import json
import re

from pydantic import ValidationError

from axis.framework.config import ExperimentConfig
from axis.framework.persistence import (
    ExperimentMetadata,
    ExperimentRepository,
    RunMetadata,
)
from axis.framework.run import RunConfig, RunSummary
from axis.sdk.trace import BaseEpisodeTrace

from axis.visualization.errors import (
    EpisodeNotFoundError,
    ExperimentNotFoundError,
    MalformedArtifactError,
    ReplayContractViolation,
    RunNotFoundError,
)
from axis.visualization.replay_models import (
    ReplayEpisodeHandle,
    ReplayExperimentHandle,
    ReplayRunHandle,
    ReplayValidationResult,
)
from axis.visualization.replay_validation import (
    validate_episode_for_replay,
)

_EPISODE_RE = re.compile(r"^episode_(\d+)\.json$")


class ReplayAccessService:
    """Read-only visualization gateway to the experiment repository.

    All data access delegates to ExperimentRepository. This service
    adds replay-oriented validation, typed error mapping, and
    discovery helpers.
    """

    def __init__(self, repository: ExperimentRepository) -> None:
        self._repo = repository

    # -- internal helpers ---------------------------------------------------

    def _require_experiment(self, experiment_id: str) -> None:
        if experiment_id not in self._repo.list_experiments():
            raise ExperimentNotFoundError(
                f"Experiment not found: {experiment_id}"
            )

    def _require_run(self, experiment_id: str, run_id: str) -> None:
        self._require_experiment(experiment_id)
        if run_id not in self._repo.list_runs(experiment_id):
            raise RunNotFoundError(
                f"Run not found: {run_id} in experiment {experiment_id}"
            )

    # -- discovery ----------------------------------------------------------

    def list_experiments(self) -> tuple[str, ...]:
        """Return sorted experiment IDs available in the repository."""
        return tuple(self._repo.list_experiments())

    def list_runs(self, experiment_id: str) -> tuple[str, ...]:
        """Return sorted run IDs for *experiment_id*."""
        self._require_experiment(experiment_id)
        return tuple(self._repo.list_runs(experiment_id))

    def list_episode_indices(
        self, experiment_id: str, run_id: str,
    ) -> tuple[int, ...]:
        """Return sorted episode indices for a run."""
        self._require_run(experiment_id, run_id)
        paths = self._repo.list_episode_files(experiment_id, run_id)
        indices: list[int] = []
        for p in paths:
            m = _EPISODE_RE.match(p.name)
            if m:
                indices.append(int(m.group(1)))
        return tuple(sorted(indices))

    # -- handles ------------------------------------------------------------

    def get_experiment_handle(
        self, experiment_id: str,
    ) -> ReplayExperimentHandle:
        """Load experiment config/metadata and list available runs."""
        config = self.load_experiment_config(experiment_id)
        metadata = self._load_optional_experiment_metadata(experiment_id)
        runs = self.list_runs(experiment_id)
        return ReplayExperimentHandle(
            experiment_id=experiment_id,
            experiment_config=config,
            experiment_metadata=metadata,
            available_runs=runs,
        )

    def get_run_handle(
        self, experiment_id: str, run_id: str,
    ) -> ReplayRunHandle:
        """Load run config/metadata/summary and list available episodes."""
        run_config = self.load_run_config(experiment_id, run_id)
        run_metadata = self._load_optional_run_metadata(
            experiment_id, run_id,
        )
        run_summary = self._load_optional_run_summary(
            experiment_id, run_id,
        )
        episodes = self.list_episode_indices(experiment_id, run_id)
        return ReplayRunHandle(
            experiment_id=experiment_id,
            run_id=run_id,
            run_config=run_config,
            run_metadata=run_metadata,
            run_summary=run_summary,
            available_episodes=episodes,
        )

    # -- artifact loading ---------------------------------------------------

    def load_experiment_config(
        self, experiment_id: str,
    ) -> ExperimentConfig:
        """Load and return the experiment configuration."""
        self._require_experiment(experiment_id)
        return self._safe_load(
            lambda: self._repo.load_experiment_config(experiment_id),
            f"experiment config for {experiment_id}",
        )

    def load_run_config(
        self, experiment_id: str, run_id: str,
    ) -> RunConfig:
        """Load and return the run configuration."""
        self._require_run(experiment_id, run_id)
        return self._safe_load(
            lambda: self._repo.load_run_config(experiment_id, run_id),
            f"run config for {experiment_id}/{run_id}",
        )

    def load_episode_trace(
        self, experiment_id: str, run_id: str, episode_index: int,
    ) -> BaseEpisodeTrace:
        """Load raw episode trace without validation."""
        self._require_run(experiment_id, run_id)
        if episode_index not in self.list_episode_indices(
            experiment_id, run_id,
        ):
            raise EpisodeNotFoundError(
                f"Episode {episode_index} not found in "
                f"{experiment_id}/{run_id}"
            )
        return self._safe_load(
            lambda: self._repo.load_episode_trace(
                experiment_id, run_id, episode_index,
            ),
            f"episode {episode_index} for {experiment_id}/{run_id}",
        )

    # -- replay loading (primary API) ---------------------------------------

    def load_replay_episode(
        self, experiment_id: str, run_id: str, episode_index: int,
    ) -> ReplayEpisodeHandle:
        """Load and validate an episode for replay.

        Returns a ReplayEpisodeHandle with validation attached.
        Raises ReplayContractViolation if the episode fails validation.
        """
        episode = self.load_episode_trace(
            experiment_id, run_id, episode_index,
        )
        validation = validate_episode_for_replay(episode)
        if not validation.valid:
            raise ReplayContractViolation(validation.violations)
        return ReplayEpisodeHandle(
            experiment_id=experiment_id,
            run_id=run_id,
            episode_index=episode_index,
            episode_trace=episode,
            validation=validation,
        )

    def validate_episode(
        self, experiment_id: str, run_id: str, episode_index: int,
    ) -> ReplayValidationResult:
        """Load and validate an episode, returning the result
        (never raises ReplayContractViolation)."""
        episode = self.load_episode_trace(
            experiment_id, run_id, episode_index,
        )
        return validate_episode_for_replay(episode)

    # -- optional loaders ---------------------------------------------------

    def _load_optional_experiment_metadata(
        self, experiment_id: str,
    ) -> ExperimentMetadata | None:
        path = self._repo.experiment_metadata_path(experiment_id)
        if not self._repo.artifact_exists(path):
            return None
        return self._safe_load(
            lambda: self._repo.load_experiment_metadata(experiment_id),
            f"experiment metadata for {experiment_id}",
        )

    def _load_optional_run_metadata(
        self, experiment_id: str, run_id: str,
    ) -> RunMetadata | None:
        path = self._repo.run_metadata_path(experiment_id, run_id)
        if not self._repo.artifact_exists(path):
            return None
        return self._safe_load(
            lambda: self._repo.load_run_metadata(experiment_id, run_id),
            f"run metadata for {experiment_id}/{run_id}",
        )

    def _load_optional_run_summary(
        self, experiment_id: str, run_id: str,
    ) -> RunSummary | None:
        path = self._repo.run_summary_path(experiment_id, run_id)
        if not self._repo.artifact_exists(path):
            return None
        return self._safe_load(
            lambda: self._repo.load_run_summary(experiment_id, run_id),
            f"run summary for {experiment_id}/{run_id}",
        )

    # -- safe-load wrapper --------------------------------------------------

    @staticmethod
    def _safe_load(loader, description: str):  # noqa: ANN001, ANN205
        """Call *loader()* and wrap non-visualization exceptions."""
        try:
            return loader()
        except (
            FileNotFoundError, ValidationError, KeyError,
            json.JSONDecodeError,
        ) as exc:
            raise MalformedArtifactError(
                f"Failed to load {description}: {exc}"
            ) from exc
