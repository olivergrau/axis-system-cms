"""Deterministic view-model builder for the Visualization Layer (VWP5).

Projects ``(ViewerState, SnapshotResolver)`` into a single
:class:`ViewerFrameViewModel` suitable for rendering.

Coordinate mapping
------------------
Domain ``Position(x, y)`` uses **x = column, y = row**.
The grid is stored as ``grid[row][col]``.
View models use ``(row, col)`` consistently.

This builder is the **single translation point**:

* ``agent_position.x`` → ``col``
* ``agent_position.y`` → ``row``
* ``ViewerState.selected_cell`` is already ``(row, col)`` — no translation.
"""

from __future__ import annotations

from axis_system_a.enums import CellType
from axis_system_a.visualization.debug_overlay_models import (
    ActionPreferenceOverlay,
    ConsumptionOpportunityOverlay,
    DebugOverlayViewModel,
    DriveContributionOverlay,
)
from axis_system_a.visualization.playback_controller import (
    is_at_final,
    is_at_initial,
)
from axis_system_a.visualization.snapshot_resolver import SnapshotResolver
from axis_system_a.visualization.view_models import (
    ActionContextViewModel,
    AgentViewModel,
    GridCellViewModel,
    GridViewModel,
    NeighborObservationViewModel,
    SelectionType,
    SelectionViewModel,
    StatusBarViewModel,
    StepAnalysisViewModel,
    ViewerFrameViewModel,
)
from axis_system_a.visualization.viewer_state import ViewerState


class ViewModelBuilder:
    """Stateless, deterministic builder.

    Resolves the current snapshot from the viewer state's coordinate
    and projects all sub-models in a single ``build()`` call.
    """

    def __init__(self, snapshot_resolver: SnapshotResolver) -> None:
        self._resolver = snapshot_resolver

    def build(self, state: ViewerState) -> ViewerFrameViewModel:
        """Build a complete frame view model from *state*."""
        snapshot = self._resolver.resolve(
            state.episode_handle,
            state.coordinate.step_index,
            state.coordinate.phase,
        )

        # -- Grid projection ------------------------------------------------
        agent_row = snapshot.agent_position.y
        agent_col = snapshot.agent_position.x

        cells: list[GridCellViewModel] = []
        for row_idx, row in enumerate(snapshot.grid):
            for col_idx, cell in enumerate(row):
                cells.append(
                    GridCellViewModel(
                        row=row_idx,
                        col=col_idx,
                        cell_type=cell.cell_type,
                        resource_value=cell.resource_value,
                        is_obstacle=(cell.cell_type == CellType.OBSTACLE),
                        is_traversable=cell.is_traversable,
                        is_agent_here=(
                            row_idx == agent_row and col_idx == agent_col
                        ),
                        is_selected=(
                            state.selected_cell == (row_idx, col_idx)
                        ),
                    ),
                )

        grid_vm = GridViewModel(
            width=snapshot.grid_width,
            height=snapshot.grid_height,
            cells=tuple(cells),
        )

        # -- Agent projection -----------------------------------------------
        agent_vm = AgentViewModel(
            row=agent_row,
            col=agent_col,
            energy=snapshot.agent_energy,
            is_selected=state.selected_agent,
        )

        # -- Status projection ----------------------------------------------
        status_vm = StatusBarViewModel(
            step_index=state.coordinate.step_index,
            total_steps=state.episode_handle.validation.total_steps,
            phase=state.coordinate.phase,
            playback_mode=state.playback_mode,
            energy=snapshot.agent_energy,
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

        # -- Action context projection --------------------------------------
        action_ctx_vm = ActionContextViewModel(
            action=snapshot.action,
            moved=snapshot.moved,
            consumed=snapshot.consumed,
            resource_consumed=snapshot.resource_consumed,
            energy_delta=snapshot.energy_delta,
            terminated=snapshot.terminated,
            termination_reason=snapshot.termination_reason,
        )

        # -- Assemble frame -------------------------------------------------
        return ViewerFrameViewModel(
            coordinate=state.coordinate,
            grid=grid_vm,
            agent=agent_vm,
            status=status_vm,
            selection=selection_vm,
            action_context=action_ctx_vm,
            debug_overlay=self._build_debug_overlay(state, agent_row, agent_col),
            step_analysis=self._build_step_analysis(state, agent_row, agent_col),
        )

    # -- Debug overlay projection ------------------------------------------

    def _build_debug_overlay(
        self,
        state: ViewerState,
        agent_row: int,
        agent_col: int,
    ) -> DebugOverlayViewModel | None:
        """Build the debug overlay view model if the master flag is on."""
        cfg = state.debug_overlay_config
        if not cfg.master_enabled:
            return None

        step = state.episode_handle.episode_result.steps[
            state.coordinate.step_index
        ]

        action_pref = None
        if cfg.action_preference_enabled:
            action_pref = ActionPreferenceOverlay(
                agent_row=agent_row,
                agent_col=agent_col,
                probabilities=step.decision_result.probabilities,
                admissibility_mask=step.decision_result.admissibility_mask,
                selected_action_index=step.decision_result.selected_action.value,
            )

        drive_contrib = None
        if cfg.drive_contribution_enabled:
            drive_contrib = DriveContributionOverlay(
                agent_row=agent_row,
                agent_col=agent_col,
                activation=step.drive_output.activation,
                action_contributions=step.drive_output.action_contributions,
            )

        consumption = None
        if cfg.consumption_opportunity_enabled:
            obs = step.observation
            consumption = ConsumptionOpportunityOverlay(
                agent_row=agent_row,
                agent_col=agent_col,
                current_resource=obs.current.resource,
                neighbor_resources=(
                    obs.up.resource,
                    obs.down.resource,
                    obs.left.resource,
                    obs.right.resource,
                ),
                neighbor_traversable=(
                    obs.up.traversability > 0,
                    obs.down.traversability > 0,
                    obs.left.traversability > 0,
                    obs.right.traversability > 0,
                ),
            )

        return DebugOverlayViewModel(
            config=cfg,
            action_preference=action_pref,
            drive_contribution=drive_contrib,
            consumption_opportunity=consumption,
        )

    # -- Step analysis projection ------------------------------------------

    def _build_step_analysis(
        self,
        state: ViewerState,
        agent_row: int,
        agent_col: int,
    ) -> StepAnalysisViewModel | None:
        """Build comprehensive step analysis — always, not gated by overlays."""
        step = state.episode_handle.episode_result.steps[
            state.coordinate.step_index
        ]
        obs = step.observation
        dr = step.decision_result
        tt = step.transition_trace

        return StepAnalysisViewModel(
            timestep=step.timestep,
            energy_before=step.energy_before,
            energy_after=step.energy_after,
            energy_delta=tt.energy_delta,
            current_resource=obs.current.resource,
            neighbor_observations=(
                NeighborObservationViewModel(
                    resource=obs.up.resource,
                    traversable=obs.up.traversability > 0,
                ),
                NeighborObservationViewModel(
                    resource=obs.down.resource,
                    traversable=obs.down.traversability > 0,
                ),
                NeighborObservationViewModel(
                    resource=obs.left.resource,
                    traversable=obs.left.traversability > 0,
                ),
                NeighborObservationViewModel(
                    resource=obs.right.resource,
                    traversable=obs.right.traversability > 0,
                ),
            ),
            drive_activation=step.drive_output.activation,
            drive_contributions=step.drive_output.action_contributions,
            raw_contributions=dr.raw_contributions,
            admissibility_mask=dr.admissibility_mask,
            masked_contributions=dr.masked_contributions,
            probabilities=dr.probabilities,
            temperature=dr.temperature,
            selection_mode=dr.selection_mode.value,
            selected_action=dr.selected_action.name,
            moved=tt.moved,
            consumed=tt.consumed,
            resource_consumed=tt.resource_consumed,
            position_before=(tt.position_before.y, tt.position_before.x),
            position_after=(tt.position_after.y, tt.position_after.x),
            terminated=tt.terminated,
            termination_reason=(
                tt.termination_reason.value if tt.termination_reason else None
            ),
        )
