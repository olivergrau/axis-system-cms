"""Debug overlay toggle panel (VWP9).

A compact row of checkboxes that controls debug overlay visibility.
The master checkbox gates the three sub-type checkboxes.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QWidget


class DebugOverlayPanel(QWidget):
    """Horizontal checkbox strip for debug overlay toggles."""

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

        layout = QHBoxLayout(self)
        layout.addWidget(self._master_cb)
        layout.addWidget(self._action_pref_cb)
        layout.addWidget(self._drive_contrib_cb)
        layout.addWidget(self._consumption_cb)
        self.setMaximumHeight(35)

        self._master_cb.toggled.connect(self._on_master_toggled)
        self._action_pref_cb.toggled.connect(self.action_preference_toggled)
        self._drive_contrib_cb.toggled.connect(self.drive_contribution_toggled)
        self._consumption_cb.toggled.connect(
            self.consumption_opportunity_toggled)

    def _on_master_toggled(self, checked: bool) -> None:
        self._action_pref_cb.setEnabled(checked)
        self._drive_contrib_cb.setEnabled(checked)
        self._consumption_cb.setEnabled(checked)
        self.master_toggled.emit(checked)
