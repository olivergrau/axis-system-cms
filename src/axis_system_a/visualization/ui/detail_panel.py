"""Contextual detail panel (VWP7).

Displays cell or agent details based on the current selection.
Receives the full ``ViewerFrameViewModel`` to access grid cells,
agent state, and action context.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from axis_system_a.visualization.view_models import (
    SelectionType,
    ViewerFrameViewModel,
)


class DetailPanel(QWidget):
    """Shows contextual information for the currently selected entity."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title_label = QLabel("Detail View")
        self._content_label = QLabel("No entity selected")
        self._content_label.setWordWrap(True)
        self._content_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self._title_label)
        layout.addWidget(self._content_label)
        layout.addStretch()

    def set_frame(self, frame: ViewerFrameViewModel) -> None:
        """Update detail content based on the frame's selection state."""
        sel = frame.selection

        if sel.selection_type == SelectionType.CELL and sel.selected_cell is not None:
            self._show_cell(frame)
        elif sel.selection_type == SelectionType.AGENT:
            self._show_agent(frame)
        else:
            self._title_label.setText("Detail View")
            self._content_label.setText("No entity selected")

    def _show_cell(self, frame: ViewerFrameViewModel) -> None:
        row, col = frame.selection.selected_cell  # type: ignore[misc]
        idx = row * frame.grid.width + col
        cell = frame.grid.cells[idx]

        self._title_label.setText(f"Cell ({row}, {col})")

        lines = [
            f"Type: {cell.cell_type.value}",
            f"Obstacle: {cell.is_obstacle}",
            f"Traversable: {cell.is_traversable}",
            f"Resource: {cell.resource_value:.2f}",
            f"Agent here: {cell.is_agent_here}",
        ]
        self._content_label.setText("\n".join(lines))

    def _show_agent(self, frame: ViewerFrameViewModel) -> None:
        agent = frame.agent
        ctx = frame.action_context

        self._title_label.setText("Agent")

        lines = [
            f"Position: ({agent.row}, {agent.col})",
            f"Energy: {agent.energy:.2f}",
            f"Action: {ctx.action.name}",
            f"Moved: {ctx.moved}",
            f"Energy delta: {ctx.energy_delta:+.2f}",
        ]
        if ctx.terminated:
            lines.append(f"Terminated: {ctx.termination_reason}")
        self._content_label.setText("\n".join(lines))
