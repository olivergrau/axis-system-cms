"""Prediction summary widget for the detail panel."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

ACTION_NAMES: tuple[str, ...] = ("up", "down", "left", "right", "consume", "stay")

_HEADER_H = 20.0
_CONTEXT_H = 96.0
_SECTION_HEADER_H = 14.0
_ROW_H = 12.0
_ROW_SPACING = 2.0
_SECTION_GAP = 8.0
_FOOTER_H = 34.0


def _required_height(n_actions: int, *, dual_mode: bool = False) -> int:
    """Calculate the minimum height needed for all content."""
    row_block = n_actions * (_ROW_H + _ROW_SPACING)
    if dual_mode:
        return int(
            _HEADER_H
            + _CONTEXT_H
            + (_SECTION_HEADER_H + row_block + _SECTION_GAP) * 2
            + _FOOTER_H
            + 4.0
        )
    return int(
        _HEADER_H
        + _CONTEXT_H
        + _SECTION_HEADER_H + row_block + _SECTION_GAP
        + _SECTION_HEADER_H + row_block + _SECTION_GAP
        + 4.0
    )


def _visible_modulation_bar_width(delta: float, half_gauge_width: float) -> float:
    """Return a visible width for non-neutral modulation values."""
    if abs(delta) <= 1e-9:
        return 0.0
    return max(min(abs(delta), 1.0) * half_gauge_width, 1.0)


def _channel_data(data: dict[str, Any], channel: str) -> dict[str, Any]:
    """Return one channel payload for dual-mode widgets."""
    value = data.get(channel, {})
    return value if isinstance(value, dict) else {}


class PredictionSummaryWidget(QWidget):
    """Graphical summary of prediction state."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: dict[str, Any] | None = None
        self._n_actions = len(ACTION_NAMES)
        self._dual_mode = False
        self._update_size()

    def set_data(self, data: dict[str, Any] | None) -> None:
        """Update prediction data. Pass None to hide."""
        self._data = data
        self._dual_mode = bool(data and data.get("widget_mode") == "dual_prediction")
        self.setVisible(data is not None)
        if data is not None:
            self._n_actions = self._infer_action_count(data)
            self._update_size()
        self.update()

    def _infer_action_count(self, data: dict[str, Any]) -> int:
        """Infer action count from single- or dual-channel payloads."""
        if data.get("widget_mode") == "dual_prediction":
            hunger = _channel_data(data, "hunger").get("modulation_factors", {})
            curiosity = _channel_data(data, "curiosity").get("modulation_factors", {})
            return max(len(hunger), len(curiosity), len(ACTION_NAMES))
        mod = data.get("modulation_factors", {})
        return max(len(mod), len(ACTION_NAMES)) if mod else len(ACTION_NAMES)

    def _update_size(self) -> None:
        height = _required_height(self._n_actions, dual_mode=self._dual_mode)
        self.setMinimumHeight(height)
        self.setFixedHeight(height)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(250, _required_height(self._n_actions, dual_mode=self._dual_mode))

    def paintEvent(self, event: object) -> None:  # noqa: N802
        """Render single- or dual-channel prediction summaries."""
        del event
        if self._data is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        try:
            width = self.width()
            y = 4.0
            painter.setPen(QColor(180, 180, 180))
            painter.setFont(QFont("monospace", 9, QFont.Weight.Bold))
            title = "--- Prediction Summary ---" if not self._dual_mode else "--- Shared Prediction Summary ---"
            painter.drawText(4, int(y + 12), title)
            y += _HEADER_H
            y = self._draw_context_grid(painter, width, y)
            if self._dual_mode:
                self._draw_separator(painter, width, y - 4.0)
                y = self._draw_dual_channel_block(
                    painter,
                    width,
                    y,
                    title="Hunger-side Modulation",
                    title_color=QColor(100, 180, 255),
                    channel=_channel_data(self._data, "hunger"),
                )
                self._draw_separator(painter, width, y - 4.0)
                y = self._draw_dual_channel_block(
                    painter,
                    width,
                    y,
                    title="Curiosity-side Modulation",
                    title_color=QColor(110, 220, 120),
                    channel=_channel_data(self._data, "curiosity"),
                )
                self._draw_separator(painter, width, y - 4.0)
                self._draw_dual_footer(painter, width, y)
            else:
                self._draw_separator(painter, width, y - 4.0)
                y = self._draw_trace_bars(painter, width, y)
                self._draw_separator(painter, width, y - 4.0)
                self._draw_modulation_gauges(painter, width, y)
        finally:
            painter.end()

    def _action_names(self, channel: dict[str, Any] | None = None) -> list[str]:
        """Return action names from the payload or the defaults."""
        if channel:
            mod = channel.get("modulation_factors", {})
            if mod:
                return list(mod.keys())
        if self._data:
            mod = self._data.get("modulation_factors", {})
            if mod:
                return list(mod.keys())
        return list(ACTION_NAMES)

    def _draw_context_grid(self, painter: QPainter, width: float, y: float) -> float:
        """Draw 5-cell cross pattern showing binary context bits and features."""
        context = int(self._data.get("context", 0)) if self._data else 0
        bits = [(context >> i) & 1 for i in range(5)]

        painter.setFont(QFont("monospace", 8))
        painter.setPen(QColor(160, 160, 160))
        painter.drawText(4, int(y + 10), f"Context: {context} (0b{context:05b})")
        y += 16.0

        cell_size = 14.0
        cx = width / 2.0
        cy = y + cell_size * 1.5
        positions = [
            (cx, cy),
            (cx, cy - cell_size - 2),
            (cx, cy + cell_size + 2),
            (cx - cell_size - 2, cy),
            (cx + cell_size + 2, cy),
        ]

        for index, (px, py) in enumerate(positions):
            bit_index = 4 - index
            filled = bits[bit_index] == 1
            rect = QRectF(px - cell_size / 2, py - cell_size / 2, cell_size, cell_size)
            if filled:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(100, 200, 255, 180))
            else:
                painter.setPen(QPen(QColor(100, 100, 100), 1.0))
                painter.setBrush(QColor(40, 40, 40))
            painter.drawRect(rect)

        features = self._data.get("features", ()) if self._data else ()
        if features:
            feature_values = [f"{float(value):.2f}" for value in list(features)[:4]]
            if len(features) > 4:
                feature_values.append("...")
            preview = " ".join(feature_values)
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(8, int(cy + cell_size + 22), f"Features: {preview}")
        return cy + cell_size + 30.0

    def _draw_separator(self, painter: QPainter, width: float, y: float) -> None:
        """Draw a subtle separator line between major blocks."""
        painter.setPen(QPen(QColor(85, 85, 85, 160), 1.0))
        painter.drawLine(6, int(y), int(width - 6), int(y))

    def _draw_trace_bars(self, painter: QPainter, width: float, y: float) -> float:
        """Draw frustration and confidence bars for the single-channel payload."""
        frustrations = self._data.get("frustrations", {}) if self._data else {}
        confidences = self._data.get("confidences", {}) if self._data else {}

        painter.setFont(QFont("monospace", 7))
        painter.setPen(QColor(160, 160, 160))
        painter.drawText(4, int(y + 9), "Traces (f/c):")
        y += _SECTION_HEADER_H

        label_width = 55.0
        bar_max_width = (width - label_width - 12.0) / 2.0

        for action in self._action_names():
            frustration = float(frustrations.get(action, 0.0))
            confidence = float(confidences.get(action, 0.0))
            painter.setPen(QColor(180, 180, 180))
            painter.drawText(4, int(y + _ROW_H - 2), action[:7].ljust(7))

            frustration_width = max(1.0, frustration * bar_max_width) if frustration > 0 else 0.0
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(220, 60, 60, 160))
            if frustration_width > 0:
                painter.drawRect(QRectF(label_width, y, frustration_width, _ROW_H))

            confidence_x = label_width + bar_max_width + 4.0
            confidence_width = max(1.0, confidence * bar_max_width) if confidence > 0 else 0.0
            painter.setBrush(QColor(60, 200, 80, 160))
            if confidence_width > 0:
                painter.drawRect(QRectF(confidence_x, y, confidence_width, _ROW_H))
            y += _ROW_H + _ROW_SPACING

        return y + _SECTION_GAP

    def _draw_modulation_gauges(self, painter: QPainter, width: float, y: float) -> float:
        """Draw modulation factor gauges centered on μ=1.0 for single mode."""
        mod_factors = self._data.get("modulation_factors", {}) if self._data else {}

        painter.setFont(QFont("monospace", 7))
        painter.setPen(QColor(160, 160, 160))
        painter.drawText(4, int(y + 9), "Modulation (μ):")
        y += _SECTION_HEADER_H

        label_width = 55.0
        value_width = 35.0
        gauge_width = width - label_width - value_width - 8.0
        center_x = label_width + gauge_width / 2.0

        for action in self._action_names():
            mu = float(mod_factors.get(action, 1.0))
            painter.setPen(QColor(180, 180, 180))
            painter.drawText(4, int(y + _ROW_H - 2), action[:7].ljust(7))
            painter.setPen(QPen(QColor(100, 100, 100), 1.0))
            painter.drawLine(int(center_x), int(y), int(center_x), int(y + _ROW_H))

            delta = mu - 1.0
            painter.setPen(Qt.PenStyle.NoPen)
            if delta > 0:
                bar_width = _visible_modulation_bar_width(delta, gauge_width / 2.0)
                painter.setBrush(QColor(60, 200, 80, 160))
                painter.drawRect(QRectF(center_x, y, bar_width, _ROW_H))
            elif delta < 0:
                bar_width = _visible_modulation_bar_width(delta, gauge_width / 2.0)
                painter.setBrush(QColor(220, 60, 60, 160))
                painter.drawRect(QRectF(center_x - bar_width, y, bar_width, _ROW_H))

            painter.setPen(QColor(140, 140, 140))
            painter.drawText(int(label_width + gauge_width + 4), int(y + _ROW_H - 2), f"{mu:.2f}")
            y += _ROW_H + _ROW_SPACING

        return y + _SECTION_GAP

    def _draw_dual_channel_block(
        self,
        painter: QPainter,
        width: float,
        y: float,
        *,
        title: str,
        title_color: QColor,
        channel: dict[str, Any],
    ) -> float:
        """Draw one C+W channel block with traces and modulation on shared rows."""
        frustrations = channel.get("frustrations", {})
        confidences = channel.get("confidences", {})
        modulation = channel.get("modulation_factors", {})

        painter.setFont(QFont("monospace", 7))
        painter.setPen(title_color)
        painter.drawText(4, int(y + 9), title)
        painter.setPen(QColor(125, 125, 125))
        painter.drawText(int(width - 118), int(y + 9), "f/c            μ")
        y += _SECTION_HEADER_H

        label_width = 48.0
        trace_width = 76.0
        gauge_value_width = 34.0
        gauge_width = max(40.0, width - label_width - trace_width - gauge_value_width - 12.0)
        frustration_width = trace_width / 2.0 - 2.0
        confidence_x = label_width + frustration_width + 6.0
        gauge_x = label_width + trace_width + 6.0
        center_x = gauge_x + gauge_width / 2.0

        for action in self._action_names(channel):
            frustration = float(frustrations.get(action, 0.0))
            confidence = float(confidences.get(action, 0.0))
            mu = float(modulation.get(action, 1.0))

            painter.setPen(QColor(180, 180, 180))
            painter.drawText(4, int(y + _ROW_H - 2), action[:7].ljust(7))

            painter.setPen(Qt.PenStyle.NoPen)
            if frustration > 0:
                painter.setBrush(QColor(220, 60, 60, 160))
                painter.drawRect(QRectF(label_width, y, max(1.0, frustration * frustration_width), _ROW_H))
            if confidence > 0:
                painter.setBrush(QColor(60, 200, 80, 160))
                painter.drawRect(QRectF(confidence_x, y, max(1.0, confidence * frustration_width), _ROW_H))

            painter.setPen(QPen(QColor(100, 100, 100), 1.0))
            painter.drawLine(int(center_x), int(y), int(center_x), int(y + _ROW_H))
            delta = mu - 1.0
            painter.setPen(Qt.PenStyle.NoPen)
            if delta > 0:
                bar_width = _visible_modulation_bar_width(delta, gauge_width / 2.0)
                painter.setBrush(QColor(60, 200, 80, 160))
                painter.drawRect(QRectF(center_x, y, bar_width, _ROW_H))
            elif delta < 0:
                bar_width = _visible_modulation_bar_width(delta, gauge_width / 2.0)
                painter.setBrush(QColor(220, 60, 60, 160))
                painter.drawRect(QRectF(center_x - bar_width, y, bar_width, _ROW_H))

            painter.setPen(QColor(145, 145, 145))
            painter.drawText(int(gauge_x + gauge_width + 4), int(y + _ROW_H - 2), f"{mu:.2f}")
            y += _ROW_H + _ROW_SPACING

        return y + _SECTION_GAP

    def _draw_dual_footer(self, painter: QPainter, width: float, y: float) -> None:
        """Draw a compact footer with action and error summaries."""
        hunger = _channel_data(self._data or {}, "hunger")
        curiosity = _channel_data(self._data or {}, "curiosity")
        selected = str((self._data or {}).get("selected_action", ""))
        counterfactual = str((self._data or {}).get("counterfactual_top_action", ""))
        painter.setFont(QFont("monospace", 7))
        painter.setPen(QColor(150, 150, 150))
        footer_y = y + 8.0
        painter.drawText(4, int(footer_y), "summary")
        painter.drawText(
            4,
            int(footer_y + 13.0),
            (
                f"sel={selected or '-'} cf={counterfactual or '-'}  "
                f"H±={float(hunger.get('error_positive', 0.0)):.2f}/{float(hunger.get('error_negative', 0.0)):.2f}  "
                f"C±={float(curiosity.get('error_positive', 0.0)):.2f}/{float(curiosity.get('error_negative', 0.0)):.2f}"
            ),
        )
