"""Step analysis panel that renders generic AnalysisSection data."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from axis.visualization.types import AnalysisSection


class StepAnalysisPanel(QWidget):
    """Renders a list of AnalysisSection objects as formatted text.

    System-agnostic: the adapter decides what sections and rows to
    produce. The panel just formats and displays them.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._content_label = QLabel()
        self._content_label.setFont(QFont("monospace", 9))
        self._content_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._content_label.setWordWrap(True)
        self._content_label.setTextFormat(Qt.TextFormat.PlainText)

        scroll = QScrollArea()
        scroll.setWidget(self._content_label)
        scroll.setWidgetResizable(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        self.setMinimumWidth(0)
        self.hide()

    def set_sections(
        self, sections: tuple[AnalysisSection, ...],
    ) -> None:
        if not sections:
            self.hide()
            self.setMinimumWidth(0)
            return

        lines: list[str] = []
        for section in sections:
            lines.append(f"=== {section.title} ===")
            for row in section.rows:
                lines.append(f"  {row.label}: {row.value}")
                if row.sub_rows:
                    for sub in row.sub_rows:
                        lines.append(f"    {sub.label}: {sub.value}")
            lines.append("")

        self._content_label.setText("\n".join(lines))
        self.setMinimumWidth(220)
        self.show()
