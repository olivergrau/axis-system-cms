"""Placeholder detail panel (VWP6).

Reserves UI space for future detail/inspection views.
Displays minimal selection context only.
"""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from axis_system_a.visualization.view_models import (
    SelectionType,
    SelectionViewModel,
)


class DetailPlaceholderPanel(QWidget):
    """Placeholder for future detail panel content."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title_label = QLabel("Detail View")
        self._selection_label = QLabel("No selection")

        layout = QVBoxLayout(self)
        layout.addWidget(self._title_label)
        layout.addWidget(self._selection_label)
        layout.addStretch()

    def set_frame(self, selection: SelectionViewModel) -> None:
        """Update selection display text."""
        if (
            selection.selection_type == SelectionType.CELL
            and selection.selected_cell is not None
        ):
            self._selection_label.setText(
                f"Selected: Cell {selection.selected_cell}",
            )
        elif selection.selection_type == SelectionType.AGENT:
            self._selection_label.setText("Selected: Agent")
        else:
            self._selection_label.setText("No selection")
