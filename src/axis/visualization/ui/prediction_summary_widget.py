"""Prediction summary widget for the detail panel.

Renders a compact graphical summary of the prediction system state:
context mini-grid, dual-trace bars, and modulation gauges.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

ACTION_NAMES: tuple[str, ...] = (
    "up", "down", "left", "right", "consume", "stay")

# Layout constants
_HEADER_H = 20.0
_CONTEXT_H = 70.0   # context label + cross grid
_SECTION_HEADER_H = 14.0
_ROW_H = 12.0
_ROW_SPACING = 2.0
_SECTION_GAP = 6.0


def _required_height(n_actions: int) -> int:
    """Calculate the minimum height needed for all content."""
    row_block = n_actions * (_ROW_H + _ROW_SPACING)
    return int(
        _HEADER_H
        + _CONTEXT_H
        + _SECTION_HEADER_H + row_block + _SECTION_GAP  # traces
        + _SECTION_HEADER_H + row_block + _SECTION_GAP  # modulation
        + 4.0  # bottom padding
    )


class PredictionSummaryWidget(QWidget):
    """Graphical summary of prediction state: context, traces, modulation."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: dict[str, Any] | None = None
        self._n_actions = len(ACTION_NAMES)
        self._update_size()

    def set_data(self, data: dict[str, Any] | None) -> None:
        """Update prediction data. Pass None to hide."""
        self._data = data
        self.setVisible(data is not None)
        if data is not None:
            # Adapt to actual action count from data
            mod = data.get("modulation_factors", {})
            if mod:
                self._n_actions = max(len(mod), len(ACTION_NAMES))
            self._update_size()
        self.update()

    def _update_size(self) -> None:
        h = _required_height(self._n_actions)
        self.setMinimumHeight(h)
        self.setFixedHeight(h)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(250, _required_height(self._n_actions))

    def paintEvent(self, event: object) -> None:  # noqa: N802
        """Render context grid, dual-trace bars, and modulation gauges."""
        if self._data is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        y = 4.0

        # Section header
        painter.setPen(QColor(180, 180, 180))
        painter.setFont(QFont("monospace", 9, QFont.Weight.Bold))
        painter.drawText(4, int(y + 12), "--- Prediction Summary ---")
        y += _HEADER_H

        # 1. Context mini-grid
        y = self._draw_context_grid(painter, w, y)

        # 2. Dual-trace bars
        y = self._draw_trace_bars(painter, w, y)

        # 3. Modulation gauges
        self._draw_modulation_gauges(painter, w, y)

        painter.end()

    def _action_names(self) -> list[str]:
        """Return action names from data or default list."""
        if self._data:
            mod = self._data.get("modulation_factors", {})
            if mod:
                return list(mod.keys())
        return list(ACTION_NAMES)

    def _draw_context_grid(
        self, painter: QPainter, width: float, y: float,
    ) -> float:
        """Draw 5-cell cross pattern showing binary context bits."""
        context = self._data.get("context", 0) if self._data else 0
        bits = [(context >> i) & 1 for i in range(5)]

        painter.setFont(QFont("monospace", 8))
        painter.setPen(QColor(160, 160, 160))
        painter.drawText(
            4, int(y + 10), f"Context: {context} (0b{context:05b})")
        y += 16.0

        cell_size = 14.0
        cx = width / 2.0
        cy = y + cell_size * 1.5

        # Positions: center, up, down, left, right
        positions = [
            (cx, cy),                          # center (bit 4)
            (cx, cy - cell_size - 2),          # up (bit 3)
            (cx, cy + cell_size + 2),          # down (bit 2)
            (cx - cell_size - 2, cy),          # left (bit 1)
            (cx + cell_size + 2, cy),          # right (bit 0)
        ]

        for i, (px, py) in enumerate(positions):
            bit_idx = 4 - i
            filled = bits[bit_idx] == 1
            rect = QRectF(
                px - cell_size / 2, py - cell_size / 2,
                cell_size, cell_size,
            )
            if filled:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(100, 200, 255, 180))
            else:
                painter.setPen(QPen(QColor(100, 100, 100), 1.0))
                painter.setBrush(QColor(40, 40, 40))
            painter.drawRect(rect)

        return cy + cell_size + 10.0

    def _draw_trace_bars(
        self, painter: QPainter, width: float, y: float,
    ) -> float:
        """Draw frustration (red) and confidence (green) bars per action."""
        frustrations = self._data.get("frustrations", {}) if self._data else {}
        confidences = self._data.get("confidences", {}) if self._data else {}

        painter.setFont(QFont("monospace", 7))
        painter.setPen(QColor(160, 160, 160))
        painter.drawText(4, int(y + 9), "Traces (f/c):")
        y += _SECTION_HEADER_H

        label_w = 55.0
        bar_max_w = (width - label_w - 12.0) / 2.0

        for action in self._action_names():
            f_val = frustrations.get(action, 0.0)
            c_val = confidences.get(action, 0.0)

            painter.setPen(QColor(180, 180, 180))
            painter.drawText(4, int(y + _ROW_H - 2), action[:7].ljust(7))

            f_w = max(1.0, f_val * bar_max_w)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(220, 60, 60, 160))
            painter.drawRect(QRectF(label_w, y, f_w, _ROW_H))

            c_x = label_w + bar_max_w + 4.0
            c_w = max(1.0, c_val * bar_max_w)
            painter.setBrush(QColor(60, 200, 80, 160))
            painter.drawRect(QRectF(c_x, y, c_w, _ROW_H))

            y += _ROW_H + _ROW_SPACING

        return y + _SECTION_GAP

    def _draw_modulation_gauges(
        self, painter: QPainter, width: float, y: float,
    ) -> float:
        """Draw modulation factor gauges centered on μ=1.0."""
        mod_factors = (
            self._data.get("modulation_factors", {}) if self._data else {}
        )

        painter.setFont(QFont("monospace", 7))
        painter.setPen(QColor(160, 160, 160))
        painter.drawText(4, int(y + 9), "Modulation (\u03bc):")
        y += _SECTION_HEADER_H

        label_w = 55.0
        value_w = 35.0
        gauge_w = width - label_w - value_w - 8.0
        center_x = label_w + gauge_w / 2.0

        for action in self._action_names():
            mu = mod_factors.get(action, 1.0)

            painter.setPen(QColor(180, 180, 180))
            painter.drawText(4, int(y + _ROW_H - 2), action[:7].ljust(7))

            # Center line at μ=1.0
            painter.setPen(QPen(QColor(100, 100, 100), 1.0))
            painter.drawLine(
                int(center_x), int(y),
                int(center_x), int(y + _ROW_H),
            )

            # Bar extends from center
            delta = mu - 1.0
            painter.setPen(Qt.PenStyle.NoPen)
            if delta > 0:
                bar_w = min(delta, 1.0) * (gauge_w / 2.0)
                painter.setBrush(QColor(60, 200, 80, 160))
                painter.drawRect(QRectF(center_x, y, bar_w, _ROW_H))
            elif delta < 0:
                bar_w = min(abs(delta), 1.0) * (gauge_w / 2.0)
                painter.setBrush(QColor(220, 60, 60, 160))
                painter.drawRect(QRectF(
                    center_x - bar_w, y, bar_w, _ROW_H))

            # Value text
            painter.setPen(QColor(140, 140, 140))
            painter.drawText(
                int(label_w + gauge_w + 4), int(y + _ROW_H - 2),
                f"{mu:.2f}",
            )

            y += _ROW_H + _ROW_SPACING

        return y + _SECTION_GAP
