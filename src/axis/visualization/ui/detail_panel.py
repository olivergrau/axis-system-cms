"""Detail panel showing selected entity info and world metadata."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from axis.visualization.types import CellColorConfig
from axis.visualization.ui.agent_cell_zoom import AgentCellZoomWidget
from axis.visualization.view_models import (
    GridCellViewModel,
    GridViewModel,
    SelectionType,
    ViewerFrameViewModel,
)


class DetailPanel(QWidget):
    """Shows cell info, agent info, or world metadata sections."""

    def __init__(
        self,
        cell_color_config: CellColorConfig,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._zoom_widget = AgentCellZoomWidget(cell_color_config)
        self._content_label = QLabel()
        self._content_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._content_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self._zoom_widget)
        layout.addWidget(self._content_label)

    def set_frame(
        self,
        frame: ViewerFrameViewModel,
    ) -> None:
        # Update zoomed agent cell
        agent = frame.agent
        agent_cell = self._find_cell(frame.grid, agent.row, agent.col)
        self._zoom_widget.set_data(
            agent_cell, agent, frame.overlay_data,
        )

        lines: list[str] = []

        sel = frame.selection
        if sel.selection_type == SelectionType.CELL and sel.selected_cell is not None:
            row, col = sel.selected_cell
            cell = self._find_cell(frame.grid, row, col)
            if cell is not None:
                lines.append("--- Cell Info ---")
                lines.append(f"Position: ({row}, {col})")
                lines.append(
                    f"Obstacle: {'Yes' if cell.is_obstacle else 'No'}")
                lines.append(
                    f"Traversable: {'Yes' if cell.is_traversable else 'No'}")
                lines.append(f"Resource: {cell.resource_value:.3f}")
                lines.append(
                    f"Agent here: {'Yes' if cell.is_agent_here else 'No'}")
        elif sel.selection_type == SelectionType.AGENT:
            agent = frame.agent
            lines.append("--- Agent Info ---")
            lines.append(f"Position: ({agent.row}, {agent.col})")
            lines.append(f"Vitality: {frame.status.vitality_display}")
            lines.append(f"Step: {frame.status.step_index + 1}")
        else:
            lines.append("No entity selected")

        if frame.world_metadata_sections:
            lines.append("")
            for section in frame.world_metadata_sections:
                lines.append(f"--- {section.title} ---")
                for row_data in section.rows:
                    lines.append(f"  {row_data.label}: {row_data.value}")

        self._content_label.setText("\n".join(lines))

    @staticmethod
    def _find_cell(
        grid: GridViewModel, row: int, col: int,
    ) -> GridCellViewModel | None:
        idx = row * grid.width + col
        if 0 <= idx < len(grid.cells):
            return grid.cells[idx]
        return None
