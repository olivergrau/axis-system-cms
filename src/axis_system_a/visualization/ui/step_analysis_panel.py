"""Standalone decision-analysis panel (VWP11).

Shows ALL step decision data in a scrollable text panel to the left of
the grid.  Always visible when step data is available — not gated by
debug overlay checkboxes.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from axis_system_a.visualization.view_models import StepAnalysisViewModel

_ACTION_LABELS = ("UP", "DOWN", "LEFT", "RIGHT", "CONSUME", "STAY")
_NEIGHBOR_LABELS = ("UP", "DOWN", "LEFT", "RIGHT")


class StepAnalysisPanel(QWidget):
    """Comprehensive numeric readout for one step's decision data."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._title_label = QLabel("Step Analysis")
        title_font = QFont()
        title_font.setBold(True)
        self._title_label.setFont(title_font)

        self._content_label = QLabel("")
        mono = QFont("monospace")
        mono.setPointSize(9)
        self._content_label.setFont(mono)
        self._content_label.setWordWrap(True)
        self._content_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
        )
        self._content_label.setTextFormat(Qt.TextFormat.PlainText)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._content_label)

        layout = QVBoxLayout(self)
        layout.addWidget(self._title_label)
        layout.addWidget(scroll, stretch=1)

        self.setMinimumWidth(0)
        self.hide()

    def set_frame(self, vm: StepAnalysisViewModel | None) -> None:
        """Update content from step analysis data, or hide if unavailable."""
        if vm is None:
            self.setMinimumWidth(0)
            self.hide()
            return

        lines: list[str] = []
        lines.extend(self._fmt_overview(vm))
        lines.append("")
        lines.extend(self._fmt_observation(vm))
        lines.append("")
        lines.extend(self._fmt_drive(vm))
        lines.append("")
        lines.extend(self._fmt_decision(vm))
        lines.append("")
        lines.extend(self._fmt_outcome(vm))

        self._content_label.setText("\n".join(lines))
        self.setMinimumWidth(220)
        self.show()

    # -- Section formatters ------------------------------------------------

    @staticmethod
    def _fmt_overview(vm: StepAnalysisViewModel) -> list[str]:
        return [
            "=== Step Overview ===",
            f"Timestep:  {vm.timestep}",
            f"Energy:    {vm.energy_before:.2f} → {vm.energy_after:.2f}",
            f"Δ Energy:  {vm.energy_delta:+.2f}",
        ]

    @staticmethod
    def _fmt_observation(vm: StepAnalysisViewModel) -> list[str]:
        lines = [
            "=== Observation ===",
            f"Current resource: {vm.current_resource:.2f}",
            f"{'Dir':<9}{'Res':>5}  {'Status'}",
        ]
        for i, label in enumerate(_NEIGHBOR_LABELS):
            nb = vm.neighbor_observations[i]
            status = "traversable" if nb.traversable else "blocked"
            lines.append(f"{label:<9}{nb.resource:>5.2f}  {status}")
        return lines

    @staticmethod
    def _fmt_drive(vm: StepAnalysisViewModel) -> list[str]:
        lines = [
            "=== Drive Output ===",
            f"Activation: {vm.drive_activation:.2f}",
            f"{'Action':<9}{'Contrib':>8}",
        ]
        for i, label in enumerate(_ACTION_LABELS):
            lines.append(f"{label:<9}{vm.drive_contributions[i]:>+8.3f}")
        return lines

    @staticmethod
    def _fmt_decision(vm: StepAnalysisViewModel) -> list[str]:
        lines = [
            "=== Decision Pipeline ===",
            f"Temperature:    {vm.temperature:.4f}",
            f"Selection mode: {vm.selection_mode}",
            f"Selected:       {vm.selected_action}",
            "",
            f"{'Action':<9}{'Raw':>7}{'Adm':>4}{'Eff':>8}{'Prob':>6}",
        ]
        for i, label in enumerate(_ACTION_LABELS):
            raw = vm.raw_contributions[i]
            adm = "Y" if vm.admissibility_mask[i] else "N"
            eff = vm.masked_contributions[i]
            prob = vm.probabilities[i]
            marker = " *" if label == vm.selected_action else ""
            if eff == float("-inf"):
                lines.append(
                    f"{label:<9}{raw:>+7.3f}{adm:>4}  {'  -inf':>6}{prob:>6.3f}{marker}",
                )
            else:
                lines.append(
                    f"{label:<9}{raw:>+7.3f}{adm:>4}{eff:>+8.3f}{prob:>6.3f}{marker}",
                )
        return lines

    @staticmethod
    def _fmt_outcome(vm: StepAnalysisViewModel) -> list[str]:
        r_before, c_before = vm.position_before
        r_after, c_after = vm.position_after
        lines = [
            "=== Outcome ===",
            f"Moved:     {'yes' if vm.moved else 'no'}",
            f"Position:  ({r_before},{c_before}) → ({r_after},{c_after})",
            f"Consumed:  {'yes' if vm.consumed else 'no'}",
            f"Res eaten: {vm.resource_consumed:.2f}",
            f"Terminated: {'yes' if vm.terminated else 'no'}",
        ]
        if vm.termination_reason:
            lines.append(f"Reason:    {vm.termination_reason}")
        return lines
