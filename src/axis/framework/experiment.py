"""Experiment executor: config resolution, run orchestration, result aggregation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from axis.framework.config import (
    ExperimentConfig,
    ExperimentType,
    extract_framework_config,
    set_config_value,
)
from axis.framework.run import RunConfig, RunExecutor, RunResult, RunSummary

if TYPE_CHECKING:
    from axis.framework.persistence import ExperimentRepository


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


class RunSummaryEntry(BaseModel):
    """Per-run entry within an ExperimentSummary."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    variation_description: str
    summary: RunSummary
    delta_mean_steps: float | None = None
    delta_mean_final_vitality: float | None = None
    delta_death_rate: float | None = None


class ExperimentSummary(BaseModel):
    """Aggregated summary across all runs."""

    model_config = ConfigDict(frozen=True)

    num_runs: int = Field(..., ge=0)
    run_entries: tuple[RunSummaryEntry, ...]


class ExperimentResult(BaseModel):
    """Complete result of an experiment."""

    model_config = ConfigDict(frozen=True)

    experiment_id: str
    experiment_config: ExperimentConfig
    run_results: tuple[RunResult, ...]
    summary: ExperimentSummary


# ---------------------------------------------------------------------------
# Config resolution
# ---------------------------------------------------------------------------


def variation_description(config: ExperimentConfig, run_index: int) -> str:
    """Generate a human-readable description for a run."""
    if config.experiment_type == ExperimentType.SINGLE_RUN:
        return "baseline"
    assert config.parameter_path is not None
    assert config.parameter_values is not None
    return f"{config.parameter_path}={config.parameter_values[run_index]}"


def resolve_run_configs(config: ExperimentConfig) -> tuple[RunConfig, ...]:
    """Expand an ExperimentConfig into concrete RunConfig instances."""
    if config.experiment_type == ExperimentType.SINGLE_RUN:
        return _resolve_single_run(config)
    elif config.experiment_type == ExperimentType.OFAT:
        return _resolve_ofat(config)
    raise ValueError(f"Unknown experiment type: {config.experiment_type}")


def _resolve_single_run(config: ExperimentConfig) -> tuple[RunConfig, ...]:
    framework = extract_framework_config(config)
    return (
        RunConfig(
            system_type=config.system_type,
            system_config=dict(config.system),
            framework_config=framework,
            num_episodes=config.num_episodes_per_run,
            base_seed=config.general.seed,
            agent_start_position=config.agent_start_position,
            run_id="run-0000",
        ),
    )


def _resolve_ofat(config: ExperimentConfig) -> tuple[RunConfig, ...]:
    assert config.parameter_path is not None
    assert config.parameter_values is not None

    runs: list[RunConfig] = []
    for i, value in enumerate(config.parameter_values):
        varied_config = set_config_value(config, config.parameter_path, value)
        varied_framework = extract_framework_config(varied_config)
        base_seed = config.general.seed + i * 1000

        runs.append(
            RunConfig(
                system_type=config.system_type,
                system_config=dict(varied_config.system),
                framework_config=varied_framework,
                num_episodes=config.num_episodes_per_run,
                base_seed=base_seed,
                agent_start_position=config.agent_start_position,
                run_id=f"run-{i:04d}",
                description=f"{config.parameter_path}={value}",
            )
        )
    return tuple(runs)


# ---------------------------------------------------------------------------
# Experiment summary
# ---------------------------------------------------------------------------


def compute_experiment_summary(
    config: ExperimentConfig,
    run_results: tuple[RunResult, ...],
) -> ExperimentSummary:
    """Build experiment summary with optional OFAT deltas."""
    baseline: RunSummary | None = None
    if (
        config.experiment_type == ExperimentType.OFAT
        and len(run_results) > 0
    ):
        baseline = run_results[0].summary

    entries: list[RunSummaryEntry] = []
    for i, rr in enumerate(run_results):
        desc = variation_description(config, i)

        delta_steps: float | None = None
        delta_vitality: float | None = None
        delta_death: float | None = None

        if baseline is not None:
            delta_steps = rr.summary.mean_steps - baseline.mean_steps
            delta_vitality = (
                rr.summary.mean_final_vitality - baseline.mean_final_vitality
            )
            delta_death = rr.summary.death_rate - baseline.death_rate

        entries.append(
            RunSummaryEntry(
                run_id=rr.run_id,
                variation_description=desc,
                summary=rr.summary,
                delta_mean_steps=delta_steps,
                delta_mean_final_vitality=delta_vitality,
                delta_death_rate=delta_death,
            )
        )

    return ExperimentSummary(
        num_runs=len(run_results),
        run_entries=tuple(entries),
    )


# ---------------------------------------------------------------------------
# Run completion check
# ---------------------------------------------------------------------------


def is_run_complete(
    repo: ExperimentRepository, experiment_id: str, run_id: str,
) -> bool:
    """Check whether a run is fully complete and safe to skip during resume.

    Returns True only if the run has COMPLETED status AND all required
    completion artifacts (config, summary, result) exist and load correctly.
    """
    from axis.framework.persistence import RunStatus

    try:
        status = repo.load_run_status(experiment_id, run_id)
        if status != RunStatus.COMPLETED:
            return False
        repo.load_run_config(experiment_id, run_id)
        repo.load_run_summary(experiment_id, run_id)
        repo.load_run_result(experiment_id, run_id)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------


class ExperimentExecutor:
    """Orchestrate one complete experiment from config to results."""

    def __init__(
        self,
        run_executor: RunExecutor | None = None,
        repository: ExperimentRepository | None = None,
    ) -> None:
        self._run_executor = run_executor or RunExecutor()
        self._repository = repository

    def execute(self, config: ExperimentConfig) -> ExperimentResult:
        """Execute a complete experiment with optional persistence."""
        if self._repository is None:
            return self._execute_in_memory(config)
        return self._execute_with_persistence(config)

    def resume(self, experiment_id: str) -> ExperimentResult:
        """Resume a persisted experiment. Requires repository."""
        if self._repository is None:
            raise RuntimeError("resume() requires a repository")
        return self._resume_with_persistence(experiment_id)

    # -- In-memory execution (no repository) --------------------------------

    def _execute_in_memory(self, config: ExperimentConfig) -> ExperimentResult:
        run_configs = resolve_run_configs(config)

        results: list[RunResult] = []
        for rc in run_configs:
            result = self._run_executor.execute(rc)
            results.append(result)

        run_results = tuple(results)
        summary = compute_experiment_summary(config, run_results)

        return ExperimentResult(
            experiment_id=uuid.uuid4().hex,
            experiment_config=config,
            run_results=run_results,
            summary=summary,
        )

    # -- Persistent execution -----------------------------------------------

    def _execute_with_persistence(
        self, config: ExperimentConfig,
    ) -> ExperimentResult:
        from axis.framework.persistence import (
            ExperimentMetadata,
            ExperimentStatus,
            RunStatus,
        )

        repo = self._repository
        assert repo is not None
        experiment_id = uuid.uuid4().hex

        # Initialize experiment artifacts
        repo.create_experiment_dir(experiment_id)
        repo.save_experiment_config(experiment_id, config)

        # Derive output semantics from experiment type
        if config.experiment_type == ExperimentType.SINGLE_RUN:
            output_form = "point"
            primary_run_id = "run-0000"
            baseline_run_id = None
        elif config.experiment_type == ExperimentType.OFAT:
            output_form = "sweep"
            primary_run_id = None
            baseline_run_id = "run-0000"
        else:
            raise ValueError(
                f"Unknown experiment type: {config.experiment_type}")

        repo.save_experiment_metadata(
            experiment_id,
            ExperimentMetadata(
                experiment_id=experiment_id,
                created_at=datetime.now(timezone.utc).isoformat(),
                experiment_type=config.experiment_type.value,
                system_type=config.system_type,
                output_form=output_form,
                primary_run_id=primary_run_id,
                baseline_run_id=baseline_run_id,
            ),
        )
        repo.save_experiment_status(experiment_id, ExperimentStatus.RUNNING)

        # Resolve and execute runs
        run_configs = resolve_run_configs(config)
        run_results: list[RunResult] = []
        completed_count = 0

        for i, run_config in enumerate(run_configs):
            run_id = run_config.run_id or f"run-{i:04d}"
            try:
                result = self._execute_and_persist_run(
                    experiment_id, run_config, config, i,
                )
                run_results.append(result)
                completed_count += 1
            except Exception:
                repo.save_run_status(experiment_id, run_id, RunStatus.FAILED)
                if completed_count > 0:
                    repo.save_experiment_status(
                        experiment_id, ExperimentStatus.PARTIAL,
                    )
                else:
                    repo.save_experiment_status(
                        experiment_id, ExperimentStatus.FAILED,
                    )
                raise

        return self._finalize_experiment(experiment_id, config, run_results)

    # -- Resume -------------------------------------------------------------

    def _resume_with_persistence(
        self, experiment_id: str,
    ) -> ExperimentResult:
        from axis.framework.persistence import (
            ExperimentStatus,
            RunStatus,
        )

        repo = self._repository
        assert repo is not None

        config = repo.load_experiment_config(experiment_id)
        repo.save_experiment_status(experiment_id, ExperimentStatus.RUNNING)

        run_configs = resolve_run_configs(config)
        run_results: list[RunResult] = []
        completed_count = 0

        for i, run_config in enumerate(run_configs):
            run_id = run_config.run_id or f"run-{i:04d}"

            if is_run_complete(repo, experiment_id, run_id):
                run_results.append(repo.load_run_result(experiment_id, run_id))
                completed_count += 1
            else:
                try:
                    result = self._execute_and_persist_run(
                        experiment_id, run_config, config, i,
                    )
                    run_results.append(result)
                    completed_count += 1
                except Exception:
                    repo.save_run_status(
                        experiment_id, run_id, RunStatus.FAILED,
                    )
                    if completed_count > 0:
                        repo.save_experiment_status(
                            experiment_id, ExperimentStatus.PARTIAL,
                        )
                    else:
                        repo.save_experiment_status(
                            experiment_id, ExperimentStatus.FAILED,
                        )
                    raise

        return self._finalize_experiment(
            experiment_id, config, run_results, overwrite_summary=True,
        )

    # -- Private helpers ----------------------------------------------------

    def _execute_and_persist_run(
        self,
        experiment_id: str,
        run_config: RunConfig,
        config: ExperimentConfig,
        run_index: int,
    ) -> RunResult:
        """Execute a single run and persist all its artifacts."""
        from axis.framework.persistence import RunMetadata, RunStatus

        repo = self._repository
        assert repo is not None
        run_id = run_config.run_id or f"run-{run_index:04d}"

        # Initialize run artifacts (overwrite=True for resume safety)
        repo.create_run_dir(experiment_id, run_id)
        repo.save_run_config(
            experiment_id, run_id, run_config, overwrite=True,
        )

        # Build run metadata with optional sweep fields
        run_meta_kwargs: dict = dict(
            run_id=run_id,
            experiment_id=experiment_id,
            variation_description=variation_description(config, run_index),
            created_at=datetime.now(timezone.utc).isoformat(),
            base_seed=run_config.base_seed,
        )
        if config.experiment_type == ExperimentType.OFAT:
            assert config.parameter_values is not None
            run_meta_kwargs["variation_index"] = run_index
            run_meta_kwargs["variation_value"] = config.parameter_values[run_index]
            run_meta_kwargs["is_baseline"] = (run_index == 0)

        repo.save_run_metadata(
            experiment_id, run_id,
            RunMetadata(**run_meta_kwargs),
        )
        repo.save_run_status(experiment_id, run_id, RunStatus.RUNNING)

        result = self._run_executor.execute(run_config)

        # Persist run results (overwrite=True for resume safety)
        repo.save_run_result(
            experiment_id, run_id, result, overwrite=True,
        )
        repo.save_run_summary(
            experiment_id, run_id, result.summary, overwrite=True,
        )
        for ep_idx, ep_trace in enumerate(result.episode_traces, start=1):
            repo.save_episode_trace(
                experiment_id, run_id, ep_idx, ep_trace, overwrite=True,
            )
        repo.save_run_status(experiment_id, run_id, RunStatus.COMPLETED)
        return result

    def _finalize_experiment(
        self,
        experiment_id: str,
        config: ExperimentConfig,
        run_results: list[RunResult],
        *,
        overwrite_summary: bool = False,
    ) -> ExperimentResult:
        """Build summary, persist it, and return the final ExperimentResult."""
        from axis.framework.persistence import ExperimentStatus

        repo = self._repository
        assert repo is not None
        results_tuple = tuple(run_results)

        summary = compute_experiment_summary(config, results_tuple)
        repo.save_experiment_summary(
            experiment_id, summary, overwrite=overwrite_summary,
        )
        repo.save_experiment_status(experiment_id, ExperimentStatus.COMPLETED)

        return ExperimentResult(
            experiment_id=experiment_id,
            experiment_config=config,
            run_results=results_tuple,
            summary=summary,
        )


# ---------------------------------------------------------------------------
# Convenience wrappers
# ---------------------------------------------------------------------------


def execute_experiment(
    config: ExperimentConfig,
    repository: ExperimentRepository,
) -> ExperimentResult:
    """Execute an experiment with persistence. Convenience wrapper."""
    return ExperimentExecutor(repository=repository).execute(config)


def resume_experiment(
    experiment_id: str,
    repository: ExperimentRepository,
) -> ExperimentResult:
    """Resume an experiment. Convenience wrapper."""
    return ExperimentExecutor(repository=repository).resume(experiment_id)
