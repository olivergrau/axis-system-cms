"""Experiment Output abstraction: normalized semantic layer above persistence.

Interprets completed experiment artifacts as either a PointExperimentOutput
(single_run) or a SweepExperimentOutput (ofat).  This module sits above
raw persistence and below workspace / CLI consumers.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Output form enum
# ---------------------------------------------------------------------------


class ExperimentOutputForm(StrEnum):
    POINT = "point"
    SWEEP = "sweep"


# ---------------------------------------------------------------------------
# Mapping from experiment_type to output_form
# ---------------------------------------------------------------------------

_TYPE_TO_FORM: dict[str, ExperimentOutputForm] = {
    "single_run": ExperimentOutputForm.POINT,
    "ofat": ExperimentOutputForm.SWEEP,
}


def output_form_for_type(experiment_type: str) -> ExperimentOutputForm:
    """Return the required output form for an experiment type."""
    form = _TYPE_TO_FORM.get(experiment_type)
    if form is None:
        raise ValueError(
            f"No output form defined for experiment_type='{experiment_type}'"
        )
    return form


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------


class ExperimentOutput(BaseModel):
    """Base experiment output with common fields."""

    model_config = ConfigDict(frozen=True)

    experiment_id: str
    experiment_type: str
    output_form: ExperimentOutputForm
    system_type: str
    created_at: str
    num_runs: int
    experiment_root_path: str
    summary_path: str | None = None

    name: str | None = None
    description: str | None = None
    status: str | None = None


class PointExperimentOutput(ExperimentOutput):
    """Output for a single_run experiment (one primary run)."""

    primary_run_id: str
    primary_run_path: str
    primary_run_summary_path: str | None = None


class SweepExperimentOutput(ExperimentOutput):
    """Output for an OFAT experiment (ordered parameter sweep)."""

    parameter_path: str | None = None
    parameter_values: tuple[Any, ...] | None = None
    baseline_run_id: str
    run_ids: tuple[str, ...]
    variation_descriptions: tuple[str, ...] = ()

    baseline_run_path: str | None = None
    run_paths: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def load_experiment_output(
    repo: "ExperimentRepository",
    experiment_id: str,
) -> PointExperimentOutput | SweepExperimentOutput:
    """Load and normalize a completed experiment into a typed output.

    Parameters
    ----------
    repo:
        The experiment repository to load from.
    experiment_id:
        The experiment to interpret.

    Raises
    ------
    ValueError
        If persisted output semantics are missing or inconsistent.
    """
    from axis.framework.persistence import ExperimentRepository  # noqa: F811

    meta = repo.load_experiment_metadata(experiment_id)
    run_ids = tuple(repo.list_runs(experiment_id))

    # Require explicit persisted output_form — no silent derivation.
    if not meta.output_form:
        raise ValueError(
            f"Experiment '{experiment_id}': missing output_form in metadata. "
            f"Re-run the experiment to populate output semantics."
        )
    form = ExperimentOutputForm(meta.output_form)
    expected = output_form_for_type(meta.experiment_type)
    if form != expected:
        raise ValueError(
            f"Experiment '{experiment_id}': persisted output_form='{form}' "
            f"disagrees with experiment_type='{meta.experiment_type}' "
            f"(expected '{expected}')"
        )

    # Status
    status: str | None = None
    try:
        status = repo.load_experiment_status(experiment_id).value
    except FileNotFoundError:
        pass

    # Summary path
    summary_path: str | None = None
    sp = repo.experiment_summary_path(experiment_id)
    if sp.exists():
        summary_path = str(sp.relative_to(repo.root))

    exp_root = str(repo.experiment_dir(experiment_id).relative_to(repo.root))

    common = dict(
        experiment_id=experiment_id,
        experiment_type=meta.experiment_type,
        output_form=form,
        system_type=meta.system_type,
        created_at=meta.created_at,
        num_runs=len(run_ids),
        experiment_root_path=exp_root,
        summary_path=summary_path,
        name=meta.name,
        description=meta.description,
        status=status,
    )

    if form == ExperimentOutputForm.POINT:
        if not meta.primary_run_id:
            raise ValueError(
                f"Experiment '{experiment_id}': point output missing "
                f"primary_run_id in metadata."
            )
        primary_run_id = meta.primary_run_id
        primary_run_path = f"{exp_root}/runs/{primary_run_id}"
        primary_run_summary: str | None = None
        srp = repo.run_summary_path(experiment_id, primary_run_id)
        if srp.exists():
            primary_run_summary = str(srp.relative_to(repo.root))

        return PointExperimentOutput(
            **common,
            primary_run_id=primary_run_id,
            primary_run_path=primary_run_path,
            primary_run_summary_path=primary_run_summary,
        )

    # SWEEP
    if not meta.baseline_run_id:
        raise ValueError(
            f"Experiment '{experiment_id}': sweep output missing "
            f"baseline_run_id in metadata."
        )
    baseline_run_id = meta.baseline_run_id

    # Load sweep metadata from config
    parameter_path: str | None = None
    parameter_values: tuple[Any, ...] | None = None
    try:
        config = repo.load_experiment_config(experiment_id)
        parameter_path = config.parameter_path
        parameter_values = config.parameter_values
    except (FileNotFoundError, KeyError):
        pass

    # Load variation descriptions from run metadata
    var_descs: list[str] = []
    for rid in run_ids:
        try:
            rm = repo.load_run_metadata(experiment_id, rid)
            var_descs.append(rm.variation_description or rid)
        except (FileNotFoundError, KeyError):
            var_descs.append(rid)

    run_paths = tuple(f"{exp_root}/runs/{rid}" for rid in run_ids)

    return SweepExperimentOutput(
        **common,
        parameter_path=parameter_path,
        parameter_values=parameter_values,
        baseline_run_id=baseline_run_id,
        run_ids=run_ids,
        variation_descriptions=tuple(var_descs),
        baseline_run_path=f"{exp_root}/runs/{baseline_run_id}",
        run_paths=run_paths,
    )
