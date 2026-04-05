"""Debug overlay toggle panel with legend (VWP9/VWP10).

A compact panel with checkboxes controlling debug overlay visibility
and a dynamic legend row explaining the visual encoding.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class DebugOverlayPanel(QWidget):
    """Checkbox strip + legend for debug overlay toggles."""

    master_toggled = Signal(bool)
    action_preference_toggled = Signal(bool)
    drive_contribution_toggled = Signal(bool)
    consumption_opportunity_toggled = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._master_cb = QCheckBox("Debug Overlays")
        self._action_pref_cb = QCheckBox("Action Pref")
        self._drive_contrib_cb = QCheckBox("Drive Contrib")
        self._consumption_cb = QCheckBox("Consumption")

        # Sub-checkboxes start disabled (master is off)
        self._action_pref_cb.setEnabled(False)
        self._drive_contrib_cb.setEnabled(False)
        self._consumption_cb.setEnabled(False)

        # Checkbox row
        cb_row = QHBoxLayout()
        cb_row.addWidget(self._master_cb)
        cb_row.addWidget(self._action_pref_cb)
        cb_row.addWidget(self._drive_contrib_cb)
        cb_row.addWidget(self._consumption_cb)

        # Legend labels (rich text for colored symbols)
        legend_font = QFont()
        legend_font.setPointSize(8)

        self._action_pref_legend = QLabel(
            "<span style='color:cyan'>\u25a0</span>=selected "
            "<span style='color:orange'>\u25a0</span>=candidate "
            "length=probability"
        )
        self._drive_contrib_legend = QLabel(
            "<span style='color:#00C800'>\u25a0</span>=positive "
            "<span style='color:#C80000'>\u25a0</span>=negative "
            "U/D/L/R/C/S"
        )
        self._consumption_legend = QLabel(
            "<span style='color:#FFD700'>\u25c6</span>=resource "
            "<span style='color:#00C800'>\u25cf</span>=neighbor "
            "<span style='color:red'>\u2715</span>=blocked"
        )

        for lbl in (self._action_pref_legend, self._drive_contrib_legend,
                     self._consumption_legend):
            lbl.setFont(legend_font)
            lbl.setVisible(False)

        # Legend row
        self._legend_row = QHBoxLayout()
        self._legend_row.addWidget(self._action_pref_legend)
        self._legend_row.addWidget(self._drive_contrib_legend)
        self._legend_row.addWidget(self._consumption_legend)
        self._legend_row.addStretch()

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)
        layout.addLayout(cb_row)
        layout.addLayout(self._legend_row)
        self.setMaximumHeight(70)

        # Signal wiring
        self._master_cb.toggled.connect(self._on_master_toggled)
        self._action_pref_cb.toggled.connect(self._on_action_pref_toggled)
        self._drive_contrib_cb.toggled.connect(self._on_drive_contrib_toggled)
        self._consumption_cb.toggled.connect(self._on_consumption_toggled)

    def _on_master_toggled(self, checked: bool) -> None:
        self._action_pref_cb.setEnabled(checked)
        self._drive_contrib_cb.setEnabled(checked)
        self._consumption_cb.setEnabled(checked)
        if not checked:
            self._action_pref_legend.setVisible(False)
            self._drive_contrib_legend.setVisible(False)
            self._consumption_legend.setVisible(False)
        else:
            self._action_pref_legend.setVisible(self._action_pref_cb.isChecked())
            self._drive_contrib_legend.setVisible(self._drive_contrib_cb.isChecked())
            self._consumption_legend.setVisible(self._consumption_cb.isChecked())
        self.master_toggled.emit(checked)

    def _on_action_pref_toggled(self, checked: bool) -> None:
        self._action_pref_legend.setVisible(checked)
        self.action_preference_toggled.emit(checked)

    def _on_drive_contrib_toggled(self, checked: bool) -> None:
        self._drive_contrib_legend.setVisible(checked)
        self.drive_contribution_toggled.emit(checked)

    def _on_consumption_toggled(self, checked: bool) -> None:
        self._consumption_legend.setVisible(checked)
        self.consumption_opportunity_toggled.emit(checked)
