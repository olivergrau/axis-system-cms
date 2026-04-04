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
from axis_system_a.run import RunExecutor, RunResult


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

            # Initialize run artifacts
            repo.create_run_dir(experiment_id, run_id)
            repo.save_run_config(experiment_id, run_id, run_config)
            repo.save_run_metadata(
                experiment_id,
                run_id,
                RunMetadata(
                    run_id=run_id,
                    experiment_id=experiment_id,
                    variation_description=variation_description(config, i),
                    created_at=datetime.utcnow().isoformat() + "Z",
                    base_seed=run_config.base_seed,
                ),
            )
            repo.save_run_status(experiment_id, run_id, RunStatus.PENDING)

            try:
                repo.save_run_status(experiment_id, run_id, RunStatus.RUNNING)
                result = self._run_executor.execute(run_config)
                run_results.append(result)

                # Persist run results
                repo.save_run_result(experiment_id, run_id, result)
                repo.save_run_summary(experiment_id, run_id, result.summary)
                for ep_idx, ep_result in enumerate(
                    result.episode_results, start=1,
                ):
                    repo.save_episode_result(
                        experiment_id, run_id, ep_idx, ep_result,
                    )
                repo.save_run_status(experiment_id, run_id, RunStatus.COMPLETED)
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
        results_tuple = tuple(run_results)

        baseline_summary = None
        if config.experiment_type == ExperimentType.OFAT and len(results_tuple) > 0:
            baseline_summary = results_tuple[0].summary

        summary = compute_experiment_summary(
            results_tuple, config, baseline_summary,
        )
        repo.save_experiment_summary(experiment_id, summary)

        # -- Construct result and finalize ----------------------------------
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
