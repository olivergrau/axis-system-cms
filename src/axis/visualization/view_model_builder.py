"""Generalized view-model builder for the Visualization Layer.

Delegates to both world and system adapters to produce a composite
ViewerFrameViewModel. No system-specific or world-specific code.

Coordinate mapping:
    Domain Position(x, y) uses x = column, y = row.
    The grid is stored as grid[row][col].
    View models use (row, col) consistently.
"""

from __future__ import annotations

from typing import Any

from axis.sdk.trace import BaseStepTrace
from axis.visualization.playback_controller import is_at_final, is_at_initial
from axis.visualization.snapshot_models import ReplaySnapshot
from axis.visualization.snapshot_resolver import SnapshotResolver
from axis.visualization.types import (
    OverlayData,
)
from axis.visualization.view_models import (
    AgentViewModel,
    GridCellViewModel,
    GridViewModel,
    SelectionType,
    SelectionViewModel,
    StatusBarViewModel,
    ViewerFrameViewModel,
)
from axis.visualization.viewer_state import ViewerState


class ViewModelBuilder:
    """Stateless, deterministic builder.

    Delegates to the world adapter for cell geometry and coloring,
    and to the system adapter for analysis sections and overlays.
    """

    def __init__(
        self,
        snapshot_resolver: SnapshotResolver,
        world_adapter: Any,
        system_adapter: Any,
    ) -> None:
        self._resolver = snapshot_resolver
        self._world_adapter = world_adapter
        self._system_adapter = system_adapter

    def build(self, state: ViewerState) -> ViewerFrameViewModel:
        """Build a complete frame view model from *state*."""
        phase_names = self._system_adapter.phase_names()

        snapshot = self._resolver.resolve(
            state.episode_handle.episode_trace,
            state.coordinate.step_index,
            state.coordinate.phase_index,
            phase_names,
        )

        step_trace = state.episode_handle.episode_trace.steps[
            state.coordinate.step_index
        ]

        # -- Grid projection (world adapter) --------------------------------
        grid_vm = self._build_grid(snapshot, state)

        # -- Agent projection -----------------------------------------------
        agent_row = snapshot.agent_position.y
        agent_col = snapshot.agent_position.x

        agent_vm = AgentViewModel(
            row=agent_row,
            col=agent_col,
            vitality=snapshot.vitality,
            is_selected=state.selected_agent,
        )

        # -- Status projection (both adapters) ------------------------------
        vitality_display = self._system_adapter.format_vitality(
            snapshot.vitality, step_trace.system_data,
        )
        world_data = (
            step_trace.world_data
            if hasattr(step_trace, "world_data")
            else {}
        )
        world_info = self._world_adapter.format_world_info(world_data)

        status_vm = StatusBarViewModel(
            step_index=state.coordinate.step_index,
            total_steps=state.episode_handle.validation.total_steps,
            phase_index=state.coordinate.phase_index,
            phase_name=snapshot.phase_name,
            playback_mode=state.playback_mode,
            vitality_display=vitality_display,
            vitality_label=self._system_adapter.vitality_label(),
            world_info=world_info,
            at_start=is_at_initial(state),
            at_end=is_at_final(state),
        )

        # -- Selection projection -------------------------------------------
        if state.selected_agent:
            sel_type = SelectionType.AGENT
        elif state.selected_cell is not None:
            sel_type = SelectionType.CELL
        else:
            sel_type = SelectionType.NONE

        selection_vm = SelectionViewModel(
            selection_type=sel_type,
            selected_cell=state.selected_cell,
            agent_selected=state.selected_agent,
        )

        # -- World adapter outputs ------------------------------------------
        cell_layout = self._world_adapter.cell_layout(
            snapshot.world_snapshot.width,
            snapshot.world_snapshot.height,
            800,  # default canvas width (actual set by widget resize)
            600,  # default canvas height
        )

        topology_indicators = self._world_adapter.topology_indicators(
            snapshot.world_snapshot, world_data, cell_layout,
        )

        world_metadata_sections = self._world_adapter.world_metadata_sections(
            world_data,
        )

        # -- System adapter outputs -----------------------------------------
        analysis_sections = self._system_adapter.build_step_analysis(
            step_trace,
        )

        overlay_data = self._build_overlays(step_trace, state)

        # -- System widget data (optional) ----------------------------------
        system_widget_data = None
        if hasattr(self._system_adapter, "build_system_widget_data"):
            system_widget_data = self._system_adapter.build_system_widget_data(
                step_trace,
            )

        # -- Assemble frame -------------------------------------------------
        return ViewerFrameViewModel(
            coordinate=state.coordinate,
            grid=grid_vm,
            agent=agent_vm,
            status=status_vm,
            selection=selection_vm,
            topology_indicators=tuple(topology_indicators),
            world_metadata_sections=tuple(world_metadata_sections),
            analysis_sections=tuple(analysis_sections),
            overlay_data=tuple(overlay_data),
            system_widget_data=system_widget_data,
        )

    def _build_grid(
        self,
        snapshot: ReplaySnapshot,
        state: ViewerState,
    ) -> GridViewModel:
        """Project world snapshot to GridViewModel."""
        ws = snapshot.world_snapshot
        agent_row = snapshot.agent_position.y
        agent_col = snapshot.agent_position.x

        cells: list[GridCellViewModel] = []
        for row_idx, row in enumerate(ws.grid):
            for col_idx, cell in enumerate(row):
                cells.append(
                    GridCellViewModel(
                        row=row_idx,
                        col=col_idx,
                        resource_value=cell.resource_value,
                        is_obstacle=cell.cell_type == "obstacle",
                        is_traversable=cell.cell_type != "obstacle",
                        is_agent_here=(
                            row_idx == agent_row and col_idx == agent_col
                        ),
                        is_selected=(
                            state.selected_cell == (row_idx, col_idx)
                        ),
                    ),
                )

        return GridViewModel(
            width=ws.width,
            height=ws.height,
            cells=tuple(cells),
        )

    def _build_overlays(
        self,
        step_trace: BaseStepTrace,
        state: ViewerState,
    ) -> list[OverlayData]:
        """Build overlay data, filtered by overlay config."""
        cfg = state.overlay_config
        if not cfg.master_enabled:
            return []

        all_overlays = self._system_adapter.build_overlays(step_trace)

        # Filter to only enabled overlay types
        return [
            od for od in all_overlays
            if od.overlay_type in cfg.enabled_overlays
        ]
