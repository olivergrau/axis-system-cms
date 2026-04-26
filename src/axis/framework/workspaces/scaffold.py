"""Workspace scaffolder – non-interactive API (WP-03)."""

from __future__ import annotations

from pathlib import Path

import yaml

from axis.framework.workspaces.manifest_mutator import (
    merge_scaffold_fields,
    set_primary_configs,
)
from axis.framework.workspaces.types import (
    WorkspaceManifest,
)


# Shared required top-level items.
_REQUIRED_DIRS = ("configs", "results", "comparisons", "exports")
_SCAFFOLD_EXECUTION = {
    "max_steps": 200,
    "trace_mode": "delta",
    "parallelism_mode": "episodes",
    "max_workers": 4,
}
_SCAFFOLD_LOGGING = {
    "enabled": False,
    "console_enabled": False,
    "jsonl_enabled": False,
    "verbosity": "compact",
}
_KNOWN_SYSTEM_TEMPLATE_FILES = {
    "system_a": "experiments/configs/system-a-baseline.yaml",
    "system_aw": "experiments/configs/system-aw-baseline.yaml",
    "system_b": "experiments/configs/system-b-sdk-demo.yaml",
    "system_c": "experiments/configs/system-c-baseline.yaml",
}


def scaffold_workspace(path: Path, manifest: WorkspaceManifest) -> Path:
    """Create a workspace directory tree with initial files.

    Parameters
    ----------
    path:
        Target directory.  Must not already exist.
    manifest:
        A validated WorkspaceManifest describing the workspace to create.

    Returns
    -------
    Path to the created workspace root.

    Raises
    ------
    FileExistsError
        If *path* already exists.
    """
    from axis.framework.workspaces.handler import get_handler

    if path.exists():
        raise FileExistsError(f"Workspace path already exists: {path}")

    path.mkdir(parents=True)

    # --- Write workspace.yaml ---
    manifest_data = manifest.model_dump(mode="json", exclude_none=True)
    (path / "workspace.yaml").write_text(
        yaml.dump(manifest_data, default_flow_style=False, sort_keys=False)
    )

    # --- Starter documentation ---
    (path / "README.md").write_text(_render_readme(manifest))
    (path / "notes.md").write_text(_render_notes(manifest))

    # --- Required directories ---
    for d in _REQUIRED_DIRS:
        (path / d).mkdir()

    # --- Type-specific directories and configs (delegated to handler) ---
    handler = get_handler(manifest.workspace_type)
    handler.create_directories(path, manifest)
    config_paths = handler.create_configs(path, manifest)

    # --- Update workspace.yaml with primary_configs + handler fields ---
    extra_fields = handler.scaffold_manifest_fields(path, manifest)
    if config_paths:
        set_primary_configs(manifest_data, _primary_config_entries(
            manifest, config_paths,
        ))
    if extra_fields:
        merge_scaffold_fields(manifest_data, extra_fields)
    if config_paths or extra_fields:
        (path / "workspace.yaml").write_text(
            yaml.dump(manifest_data, default_flow_style=False,
                      sort_keys=False)
        )

    return path


def _primary_config_entries(
    manifest: WorkspaceManifest,
    config_paths: list[str],
) -> list[dict[str, str]]:
    """Return scaffolded primary config entries with explicit roles."""
    if manifest.workspace_type == "single_system":
        return [{"path": path, "role": "reference"} for path in config_paths]

    if manifest.workspace_type == "system_comparison":
        roles = ["reference", "candidate"]
        return [
            {"path": path, "role": roles[i] if i < len(roles) else "candidate"}
            for i, path in enumerate(config_paths)
        ]

    if manifest.workspace_type == "system_development":
        roles = ["baseline", "candidate"]
        return [
            {"path": path, "role": roles[i] if i < len(roles) else "candidate"}
            for i, path in enumerate(config_paths)
        ]

    return [{"path": path} for path in config_paths]


def _render_readme(manifest: WorkspaceManifest) -> str:
    """Render type-aware starter README content for a new workspace."""
    if manifest.workspace_type == "single_system":
        system = manifest.system_under_test or "system_a"
        description = _description_or_default(
            manifest,
            f"Probe workspace for studying `{system}` in a controlled run "
            "context.",
        )
        return (
            f"# {manifest.title}\n\n"
            f"{description}\n\n"
            f"Workspace classification: {_workspace_classification(manifest)}.\n\n"
            "Primary purpose:\n\n"
            f"- inspect and document the behavior of `{system}`\n"
            f"- answer: {manifest.question}\n\n"
            "This workspace contains:\n\n"
            "- one executable baseline config in `configs/`\n"
            "- authoritative workspace semantics in `workspace.yaml`\n"
            "- workspace-owned execution artifacts under `results/`\n"
            "- optional point-vs-point comparisons under `comparisons/`\n\n"
            "It is an investigation workspace rather than a development "
            "workspace, so it intentionally starts without engineering "
            "artifacts.\n"
        )

    if manifest.workspace_type == "system_comparison":
        reference = manifest.reference_system or "system_a"
        candidate = manifest.candidate_system or "system_a"
        description = _description_or_default(
            manifest,
            "Comparison workspace for running two systems or configurations "
            "under shared conditions.",
        )
        return (
            f"# {manifest.title}\n\n"
            f"{description}\n\n"
            f"Workspace classification: {_workspace_classification(manifest)}.\n\n"
            "Primary purpose:\n\n"
            f"- compare `{reference}` as reference against `{candidate}` "
            "as candidate\n"
            f"- answer: {manifest.question}\n\n"
            "This workspace contains:\n\n"
            "- reference and candidate configs in `configs/`\n"
            "- authoritative workspace semantics in `workspace.yaml`\n"
            "- workspace-owned execution artifacts under `results/`\n"
            "- numbered comparison outputs under `comparisons/`\n\n"
            "Both scaffolded configs start with shared world and execution "
            "settings so later comparisons have a fair baseline.\n"
        )

    if manifest.workspace_type == "system_development":
        artifact = manifest.artifact_under_development or "system_a"
        description = _description_or_default(
            manifest,
            f"Development workspace for iterating on `{artifact}` against a "
            "known baseline.",
        )
        return (
            f"# {manifest.title}\n\n"
            f"{description}\n\n"
            f"Workspace classification: {_workspace_classification(manifest)}.\n\n"
            "Primary purpose:\n\n"
            f"- develop `{artifact}` as a system artifact\n"
            f"- goal: {manifest.development_goal}\n\n"
            "This workspace contains:\n\n"
            "- a baseline config in `configs/`\n"
            "- authoritative workspace semantics in `workspace.yaml`\n"
            "- conceptual modeling space under `concept/`\n"
            "- engineering planning space under `engineering/`\n"
            "- workspace-owned baseline and candidate results under `results/`\n"
            "- validation comparisons under `comparisons/`\n\n"
            "It starts in pre-candidate state: run the baseline first, then "
            "create and register a candidate config when the implementation is "
            "ready to validate.\n"
        )

    return (
        f"# {manifest.title}\n\n"
        f"{manifest.description or ''}\n"
    )


def _render_notes(manifest: WorkspaceManifest) -> str:
    """Render type-aware starter notes for a new workspace."""
    if manifest.workspace_type == "single_system":
        system = manifest.system_under_test or "system_a"
        return (
            "# Notes\n\n"
            f"- This workspace exists to study `{system}` as a single system.\n"
            f"- Workspace class/type: {_workspace_classification(manifest)}.\n"
            f"- Research question: {manifest.question}\n"
            "- Start by tuning the baseline config, then run "
            "`axis workspaces run`.\n"
            "- After at least two point runs, use `axis workspaces compare` "
            "to inspect behavioral changes.\n"
        )

    if manifest.workspace_type == "system_comparison":
        reference = manifest.reference_system or "system_a"
        candidate = manifest.candidate_system or "system_a"
        return (
            "# Notes\n\n"
            "- This workspace exists to compare two systems or two "
            "configurations under shared conditions.\n"
            f"- Workspace class/type: {_workspace_classification(manifest)}.\n"
            f"- Reference: `{reference}`.\n"
            f"- Candidate: `{candidate}`.\n"
            f"- Research question: {manifest.question}\n"
            "- Keep world, seed, execution, and episode settings aligned "
            "unless the workspace question explicitly changes them.\n"
            "- Run both configs with `axis workspaces run`, then create a "
            "numbered comparison with `axis workspaces compare`.\n"
        )

    if manifest.workspace_type == "system_development":
        artifact = manifest.artifact_under_development or "system_a"
        return (
            "# Notes\n\n"
            f"- This workspace exists to develop `{artifact}` as a system "
            "artifact.\n"
            f"- Workspace class/type: {_workspace_classification(manifest)}.\n"
            f"- Development goal: {manifest.development_goal}\n"
            "- Current initial state: pre-candidate, with only a baseline "
            "config registered.\n"
            "- Use `concept/` for conceptual modeling and `engineering/` for "
            "implementation planning.\n"
            "- Run the baseline first. After a candidate config exists, "
            "register it and compare baseline against candidate outputs.\n"
        )

    return f"# Notes - {manifest.workspace_id}\n"


def _description_or_default(
    manifest: WorkspaceManifest,
    default: str,
) -> str:
    """Return the manifest description, or a type-specific fallback."""
    return manifest.description.strip() if manifest.description else default


def _workspace_classification(manifest: WorkspaceManifest) -> str:
    """Return the human-readable class/type marker used in docs."""
    return f"`{manifest.workspace_class}` / `{manifest.workspace_type}`"


def _write_placeholder_config(path: Path, *, system_type: str) -> None:
    """Write a minimal but valid experiment config.

    This is a shared utility used by workspace type handlers.
    """
    data = {
        "system_type": system_type,
        "experiment_type": "single_run",
        "general": {"seed": 42},
        "execution": {"max_steps": 100},
        "logging": {"console_enabled": False},
        "world": {
            "world_type": "grid_2d",
            "grid_width": 10,
            "grid_height": 10,
            "obstacle_density": 0.15,
            "resource_regen_rate": 0.2,
        },
        "system": {
            "agent": {
                "initial_energy": 50.0,
                "max_energy": 100.0,
                "buffer_capacity": 25,
            },
            "policy": {
                "selection_mode": "sample",
                "temperature": 1.0,
                "stay_suppression": 0.1,
                "consume_weight": 2.5,
            },
            "transition": {
                "move_cost": 1.0,
                "consume_cost": 1.0,
                "stay_cost": 0.5,
                "max_consume": 1.0,
                "energy_gain_factor": 10.0,
            },
        },
        "num_episodes_per_run": 3,
    }
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))


def _write_investigation_config(path: Path, *, system_type: str) -> None:
    """Write a directly runnable investigation config for *system_type*."""
    template = _load_known_system_template(system_type)
    if template is None:
        _write_placeholder_config(path, system_type=system_type)
        return

    template["system_type"] = system_type
    template["experiment_type"] = "single_run"
    template["execution"] = dict(_SCAFFOLD_EXECUTION)
    template["logging"] = dict(_SCAFFOLD_LOGGING)
    path.write_text(yaml.dump(template, default_flow_style=False, sort_keys=False))


def _load_known_system_template(system_type: str) -> dict | None:
    """Load a repo-native scaffold template for a built-in system."""
    rel_path = _KNOWN_SYSTEM_TEMPLATE_FILES.get(system_type)
    if rel_path is None:
        return None

    repo_root = Path(__file__).resolve().parents[4]
    template_path = repo_root / rel_path
    if not template_path.is_file():
        return None

    data = yaml.safe_load(template_path.read_text())
    if not isinstance(data, dict):
        return None
    return data


def _write_ofat_starter_config(path: Path, *, system_type: str) -> None:
    """Write a minimal OFAT starter config.

    This is an optional convenience for single_system workspaces.
    """
    data = {
        "system_type": system_type,
        "experiment_type": "ofat",
        "parameter_path": "system.transition.energy_gain_factor",
        "parameter_values": [5.0, 10.0, 15.0, 20.0],
        "general": {"seed": 42},
        "execution": {"max_steps": 100},
        "logging": {"console_enabled": False},
        "world": {
            "world_type": "grid_2d",
            "grid_width": 10,
            "grid_height": 10,
            "obstacle_density": 0.15,
            "resource_regen_rate": 0.2,
        },
        "system": {
            "agent": {
                "initial_energy": 50.0,
                "max_energy": 100.0,
                "buffer_capacity": 25,
            },
            "policy": {
                "selection_mode": "sample",
                "temperature": 1.0,
                "stay_suppression": 0.1,
                "consume_weight": 2.5,
            },
            "transition": {
                "move_cost": 1.0,
                "consume_cost": 1.0,
                "stay_cost": 0.5,
                "max_consume": 1.0,
                "energy_gain_factor": 10.0,
            },
        },
        "num_episodes_per_run": 3,
    }
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))
