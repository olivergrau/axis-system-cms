"""Step analysis panel that renders generic AnalysisSection data."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QContextMenuEvent, QFont, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from axis.visualization.types import AnalysisSection


class _DebugTextView(QPlainTextEdit):
    """Read-only text view with a small copy-focused context menu."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )

    def text(self) -> str:
        """Compatibility helper for tests and callers expecting QLabel-like text."""
        return self.toPlainText()

    def setText(self, text: str) -> None:
        """Compatibility helper mirroring QLabel.setText()."""
        self.setPlainText(text)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """Show a minimal context menu tailored for clipboard usage."""
        menu = self._build_context_menu()
        menu.exec(event.globalPos())

    def _build_context_menu(self) -> QMenu:
        """Build the copy-focused context menu."""
        menu = QMenu(self)

        copy_all_action = QAction("Copy All", menu)
        copy_all_action.triggered.connect(self.copy_all)
        menu.addAction(copy_all_action)

        copy_selection_action = QAction("Copy Selection", menu)
        copy_selection_action.setEnabled(self.textCursor().hasSelection())
        copy_selection_action.triggered.connect(self.copy_selection)
        menu.addAction(copy_selection_action)

        return menu

    def copy_all(self) -> None:
        """Copy the full debug output to the clipboard."""
        QApplication.clipboard().setText(self.toPlainText())

    def copy_selection(self) -> None:
        """Copy the current text selection to the clipboard if present."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
        QApplication.clipboard().setText(
            cursor.selectedText().replace("\u2029", "\n")
        )


class StepAnalysisPanel(QWidget):
    """Renders a list of AnalysisSection objects as formatted text.

    System-agnostic: the adapter decides what sections and rows to
    produce. The panel just formats and displays them.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._content_label = _DebugTextView()
        self._content_label.setFont(QFont("monospace", 9))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._content_label)

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
        self._content_label.moveCursor(QTextCursor.MoveOperation.Start)
        self.setMinimumWidth(220)
        self.show()
