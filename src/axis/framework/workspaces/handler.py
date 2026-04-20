"""Workspace type handler base class and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from axis.framework.persistence import ExperimentRepository
    from axis.framework.workspaces.compare_resolution import (
        WorkspaceComparisonPlan,
    )
    from axis.framework.workspaces.resolution import WorkspaceRunTarget
    from axis.framework.workspaces.types import WorkspaceManifest
    from axis.framework.workspaces.validation import WorkspaceCheckIssue


class WorkspaceHandler(ABC):
    """Base class for workspace-type-specific behavior.

    Each workspace type (single_system, system_comparison, etc.)
    provides a concrete subclass that implements the type-specific
    parts of scaffolding, run resolution, compare resolution, and
    validation.
    """

    def create_directories(
        self, ws: Path, manifest: "WorkspaceManifest",
    ) -> None:
        """Create type-specific directories beyond the shared set.

        Default implementation does nothing.
        """

    @abstractmethod
    def create_configs(
        self, ws: Path, manifest: "WorkspaceManifest",
    ) -> list[str]:
        """Create type-specific config files during scaffold.

        Returns workspace-relative paths to created configs.
        """

    @abstractmethod
    def resolve_run_targets(
        self,
        ws: Path,
        manifest: "WorkspaceManifest",
        configs: list[str],
        run_filter: str | None = None,
    ) -> list["WorkspaceRunTarget"]:
        """Assign roles to resolved config paths."""

    def resolve_comparison_targets(
        self,
        ws: Path,
        manifest: "WorkspaceManifest",
        repo: "ExperimentRepository",
        experiments: list[str],
    ) -> "WorkspaceComparisonPlan":
        """Auto-resolve comparison targets.

        Default implementation raises ValueError (comparison not
        supported).
        """
        raise ValueError(
            f"Comparison not supported for workspace type "
            f"'{manifest.workspace_type}'"
        )

    def scaffold_manifest_fields(
        self, ws: Path, manifest: "WorkspaceManifest",
    ) -> dict:
        """Return extra manifest fields to merge after scaffold.

        Default implementation returns an empty dict.
        """
        return {}

    def validate(
        self, ws: Path, manifest: "WorkspaceManifest",
    ) -> list["WorkspaceCheckIssue"]:
        """Return type-specific validation issues.

        Default implementation returns an empty list.
        """
        return []


def get_handler(workspace_type) -> WorkspaceHandler:
    """Return the handler instance for a workspace type."""
    from axis.framework.workspaces.types import WorkspaceType

    from axis.framework.workspaces.handlers.single_system import (
        SingleSystemHandler,
    )
    from axis.framework.workspaces.handlers.system_comparison import (
        SystemComparisonHandler,
    )
    from axis.framework.workspaces.handlers.system_development import (
        SystemDevelopmentHandler,
    )

    _HANDLERS: dict[WorkspaceType, WorkspaceHandler] = {
        WorkspaceType.SINGLE_SYSTEM: SingleSystemHandler(),
        WorkspaceType.SYSTEM_COMPARISON: SystemComparisonHandler(),
        WorkspaceType.SYSTEM_DEVELOPMENT: SystemDevelopmentHandler(),
    }

    handler = _HANDLERS.get(workspace_type)
    if handler is None:
        raise ValueError(f"No handler for workspace type '{workspace_type}'")
    return handler
