"""Experiment-level orchestration for AXIS System A.

Provides the ExperimentExecutor — a thin sequential orchestration layer
that wires together config resolution, run execution, and persistence.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from axis_system_a.experiment import (
    ExperimentConfig,
    ExperimentResult,
    ExperimentType,
    compute_experiment_summary,
    resolve_run_configs,
    variation_description,
)
from axis_system_a.repository import (
    ExperimentMetadata,
    ExperimentRepository,
    ExperimentStatus,
    RunMetadata,
    RunStatus,
)
from axis_system_a.run import RunConfig, RunExecutor, RunResult


def is_run_complete(
    repo: ExperimentRepository, experiment_id: str, run_id: str,
) -> bool:
    """Check whether a run is fully complete and safe to skip during resume.

    Returns True only if the run has COMPLETED status AND all required
    completion artifacts (config, summary, result) exist and load correctly.
    """
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


class ExperimentExecutor:
    """Orchestrates one complete experiment from config to persisted result.

    Executes resolved runs sequentially through RunExecutor and persists
    all artifacts via ExperimentRepository.
    """

    def __init__(
        self,
        repository: ExperimentRepository,
        run_executor: RunExecutor | None = None,
    ) -> None:
        self._repository = repository
        self._run_executor = run_executor or RunExecutor()

    def execute(self, config: ExperimentConfig) -> ExperimentResult:
        """Execute a complete experiment: resolve, run, persist, summarize."""
        repo = self._repository
        experiment_id = config.name or uuid.uuid4().hex

        # -- Initialize experiment artifacts --------------------------------
        repo.create_experiment_dir(experiment_id)
        repo.save_experiment_config(experiment_id, config)
        repo.save_experiment_metadata(
            experiment_id,
            ExperimentMetadata(
                experiment_id=experiment_id,
                created_at=datetime.utcnow().isoformat() + "Z",
                experiment_type=config.experiment_type.value,
                name=config.name,
            ),
        )
        repo.save_experiment_status(experiment_id, ExperimentStatus.CREATED)
        repo.save_experiment_status(experiment_id, ExperimentStatus.RUNNING)

        # -- Resolve run configs --------------------------------------------
        run_configs = resolve_run_configs(config)

        # -- Execute runs sequentially --------------------------------------
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

        # -- Build and persist experiment summary ---------------------------
        return self._finalize_experiment(experiment_id, config, run_results)

    def resume(self, experiment_id: str) -> ExperimentResult:
        """Resume a previously started experiment, skipping completed runs."""
        repo = self._repository

        # -- Load persisted experiment config -------------------------------
        config = repo.load_experiment_config(experiment_id)

        # -- Set experiment to RUNNING during resume ------------------------
        repo.save_experiment_status(experiment_id, ExperimentStatus.RUNNING)

        # -- Resolve full run plan ------------------------------------------
        run_configs = resolve_run_configs(config)

        # -- Classify and execute/skip each run in order --------------------
        run_results: list[RunResult] = []
        completed_count = 0

        for i, run_config in enumerate(run_configs):
            run_id = run_config.run_id or f"run-{i:04d}"

            if is_run_complete(repo, experiment_id, run_id):
                # Skip — load existing result
                run_results.append(repo.load_run_result(experiment_id, run_id))
                completed_count += 1
            else:
                # Re-execute from scratch
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

        # -- Build and persist experiment summary ---------------------------
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
        repo = self._repository
        run_id = run_config.run_id or f"run-{run_index:04d}"

        # Initialize run artifacts (overwrite=True for resume safety)
        repo.create_run_dir(experiment_id, run_id)
        repo.save_run_config(
            experiment_id, run_id, run_config, overwrite=True,
        )
        repo.save_run_metadata(
            experiment_id,
            run_id,
            RunMetadata(
                run_id=run_id,
                experiment_id=experiment_id,
                variation_description=variation_description(config, run_index),
                created_at=datetime.utcnow().isoformat() + "Z",
                base_seed=run_config.base_seed,
            ),
        )
        repo.save_run_status(experiment_id, run_id, RunStatus.PENDING)
        repo.save_run_status(experiment_id, run_id, RunStatus.RUNNING)

        result = self._run_executor.execute(run_config)

        # Persist run results (overwrite=True for resume safety)
        repo.save_run_result(
            experiment_id, run_id, result, overwrite=True,
        )
        repo.save_run_summary(
            experiment_id, run_id, result.summary, overwrite=True,
        )
        for ep_idx, ep_result in enumerate(
            result.episode_results, start=1,
        ):
            repo.save_episode_result(
                experiment_id, run_id, ep_idx, ep_result, overwrite=True,
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
        repo = self._repository
        results_tuple = tuple(run_results)

        baseline_summary = None
        if config.experiment_type == ExperimentType.OFAT and len(results_tuple) > 0:
            baseline_summary = results_tuple[0].summary

        summary = compute_experiment_summary(
            results_tuple, config, baseline_summary,
        )
        repo.save_experiment_summary(
            experiment_id, summary, overwrite=overwrite_summary,
        )

        experiment_result = ExperimentResult(
            experiment_config=config,
            run_results=results_tuple,
            summary=summary,
        )
        repo.save_experiment_status(experiment_id, ExperimentStatus.COMPLETED)
        return experiment_result


def execute_experiment(
    config: ExperimentConfig,
    repository: ExperimentRepository,
) -> ExperimentResult:
    """Execute an experiment using the default ExperimentExecutor. Convenience wrapper."""
    return ExperimentExecutor(repository).execute(config)


def resume_experiment(
    experiment_id: str,
    repository: ExperimentRepository,
) -> ExperimentResult:
    """Resume an experiment using the default ExperimentExecutor. Convenience wrapper."""
    return ExperimentExecutor(repository).resume(experiment_id)
