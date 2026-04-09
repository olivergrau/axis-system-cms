"""Dynamic overlay toggle panel built from OverlayTypeDeclaration."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from axis.visualization.types import OverlayTypeDeclaration


class OverlayPanel(QWidget):
    """Overlay toggle panel with dynamically created checkboxes.

    Replaces v0.1.0's DebugOverlayPanel which had hard-coded
    checkboxes for 3 System A overlay types.  Now includes a
    legend row that shows per-overlay legend text when the
    corresponding checkbox is enabled.
    """

    master_toggled = Signal(bool)
    overlay_toggled = Signal(str, bool)  # (overlay_key, enabled)

    def __init__(
        self,
        overlay_declarations: list[OverlayTypeDeclaration],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._checkboxes: dict[str, QCheckBox] = {}
        self._legend_labels: dict[str, QLabel] = {}

        # Master checkbox
        self._master_cb = QCheckBox("Overlays")
        self._master_cb.setFont(QFont("sans-serif", 9, QFont.Weight.Bold))
        self._master_cb.toggled.connect(self._on_master_toggled)

        # Per-overlay checkboxes (built from declarations)
        cb_layout = QHBoxLayout()
        cb_layout.addWidget(self._master_cb)

        # Legend row
        legend_font = QFont()
        legend_font.setPointSize(8)
        self._legend_row = QHBoxLayout()

        for decl in overlay_declarations:
            cb = QCheckBox(decl.label)
            cb.setToolTip(decl.description)
            cb.setEnabled(False)  # disabled until master is on
            cb.toggled.connect(
                lambda checked, key=decl.key: self._on_overlay_toggled(
                    key, checked),
            )
            self._checkboxes[decl.key] = cb
            cb_layout.addWidget(cb)

            # Legend label (hidden until overlay is toggled on)
            if decl.legend_html:
                lbl = QLabel(decl.legend_html)
                lbl.setFont(legend_font)
                lbl.setVisible(False)
                self._legend_labels[decl.key] = lbl
                self._legend_row.addWidget(lbl)

        self._legend_row.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)
        layout.addLayout(cb_layout)
        layout.addLayout(self._legend_row)
        self.setMaximumHeight(70)

    def _on_master_toggled(self, checked: bool) -> None:
        for cb in self._checkboxes.values():
            cb.setEnabled(checked)
        if not checked:
            for lbl in self._legend_labels.values():
                lbl.setVisible(False)
        else:
            for key, lbl in self._legend_labels.items():
                cb = self._checkboxes.get(key)
                lbl.setVisible(cb is not None and cb.isChecked())
        self.master_toggled.emit(checked)

    def _on_overlay_toggled(self, key: str, checked: bool) -> None:
        lbl = self._legend_labels.get(key)
        if lbl is not None:
            lbl.setVisible(checked)
        self.overlay_toggled.emit(key, checked)
