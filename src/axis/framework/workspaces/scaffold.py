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

    # --- Placeholder files ---
    (path / "README.md").write_text(
        f"# {manifest.title}\n\n"
        f"{manifest.description or ''}\n"
    )
    (path / "notes.md").write_text(
        f"# Notes – {manifest.workspace_id}\n"
    )

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
        set_primary_configs(manifest_data, config_paths)
    if extra_fields:
        merge_scaffold_fields(manifest_data, extra_fields)
    if config_paths or extra_fields:
        (path / "workspace.yaml").write_text(
            yaml.dump(manifest_data, default_flow_style=False,
                      sort_keys=False)
        )

    return path


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
