"""Detached config viewer window for replay sessions."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow,
    QPlainTextEdit,
    QTabWidget,
    QWidget,
)


class ConfigViewerWindow(QMainWindow):
    """Non-modal window showing experiment and run config payloads."""

    def __init__(
        self,
        *,
        experiment_config_text: str,
        run_config_text: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("AXIS Config Viewer")
        self.resize(760, 720)

        tabs = QTabWidget()
        tabs.addTab(
            self._build_text_panel(experiment_config_text),
            "Experiment Config",
        )
        tabs.addTab(
            self._build_text_panel(run_config_text),
            "Run Config",
        )
        self.setCentralWidget(tabs)

    @staticmethod
    def _build_text_panel(text: str) -> QPlainTextEdit:
        editor = QPlainTextEdit()
        editor.setReadOnly(True)
        editor.setPlainText(text)
        return editor
