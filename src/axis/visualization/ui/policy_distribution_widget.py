"""Generic policy distribution widget for the detail panel.

Shows:
- pre-softmax score shape (raw and masked)
- post-softmax probability distribution
- the sampled action highlight
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

_HEADER_H = 22.0
_META_H = 18.0
_SECTION_HEADER_H = 14.0
_ROW_H = 14.0
_ROW_SPACING = 3.0
_SECTION_GAP = 8.0


def _coerce_numeric(value: object, *, default: float = 0.0) -> float:
    """Convert trace payload values into safe finite floats."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_score_list(values: object) -> list[float | None]:
    """Normalize score-like sequences while preserving masked sentinels."""
    if not isinstance(values, (list, tuple)):
        return []

    normalized: list[float | None] = []
    for value in values:
        if value is None:
            normalized.append(None)
        elif value == float("-inf"):
            normalized.append(float("-inf"))
        else:
            normalized.append(_coerce_numeric(value))
    return normalized


def _coerce_probability_list(values: object) -> list[float]:
    """Normalize probability-like sequences into safe floats."""
    if not isinstance(values, (list, tuple)):
        return []
    return [_coerce_numeric(v) for v in values]


def _required_height(n_actions: int) -> int:
    row_block = n_actions * (_ROW_H + _ROW_SPACING)
    return int(
        _HEADER_H
        + _META_H
        + _SECTION_HEADER_H + row_block + _SECTION_GAP
        + _SECTION_HEADER_H + row_block
        + 8.0
    )


class PolicyDistributionWidget(QWidget):
    """Compact generic visualization of score shape and probabilities."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: dict[str, Any] | None = None
        self._n_actions = 6
        self._update_size()

    def set_data(self, data: dict[str, Any] | None) -> None:
        """Update widget data. Pass None to hide the widget."""
        self._data = data
        self.setVisible(data is not None)
        if data is not None:
            labels = data.get("labels", [])
            self._n_actions = max(1, len(labels))
            self._update_size()
        self.update()

    def _update_size(self) -> None:
        h = _required_height(self._n_actions)
        self.setMinimumHeight(h)
        self.setFixedHeight(h)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(250, _required_height(self._n_actions))

    def paintEvent(self, event: object) -> None:  # noqa: N802
        if self._data is None:
            return

        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            w = float(self.width())
            y = 4.0

            painter.setPen(QColor(180, 180, 180))
            painter.setFont(QFont("monospace", 9, QFont.Weight.Bold))
            painter.drawText(4, int(y + 12), "--- Policy Distribution ---")
            y += _HEADER_H

            painter.setFont(QFont("monospace", 7))
            painter.setPen(QColor(150, 150, 150))
            temp = self._data.get("temperature")
            mode = self._data.get("selection_mode")
            selected = str(self._data.get("selected_action", ""))
            meta_parts = [f"selected={selected}"]
            if temp is not None:
                meta_parts.append(f"T={_coerce_numeric(temp):.2f}")
            if mode:
                meta_parts.append(f"mode={mode}")
            painter.drawText(4, int(y + 10), "  ".join(meta_parts))
            y += _META_H

            y = self._draw_score_section(painter, w, y)
            self._draw_probability_section(painter, w, y)
        finally:
            painter.end()

    def _draw_score_section(
        self, painter: QPainter, width: float, y: float,
    ) -> float:
        painter.setFont(QFont("monospace", 7))
        painter.setPen(QColor(160, 160, 160))
        painter.drawText(4, int(y + 9), "Pre-softmax score shape:")
        y += _SECTION_HEADER_H

        labels = list(self._data.get("labels", []))
        raw = _coerce_score_list(self._data.get("raw_scores", []))
        masked = _coerce_score_list(self._data.get("masked_scores", []))

        values = [v for v in raw + masked if v not in (None, float("-inf"))]
        min_value = min(values, default=0.0)
        max_value = max(values, default=0.0)
        min_value = min(min_value, 0.0)
        max_value = max(max_value, 0.0)
        span = max(max_value - min_value, 1e-9)

        label_w = 52.0
        value_w = 40.0
        chart_w = width - label_w - value_w - 10.0
        baseline_ratio = (0.0 - min_value) / span
        baseline_ratio = max(0.0, min(1.0, baseline_ratio))
        baseline_x = label_w + chart_w * baseline_ratio

        for i, label in enumerate(labels):
            row_y = y + i * (_ROW_H + _ROW_SPACING)
            raw_val = raw[i] if i < len(raw) else 0.0
            masked_val = masked[i] if i < len(masked) else raw_val
            draw_raw = (
                raw_val is not None
                and raw_val != float("-inf")
            )
            raw_num = _coerce_numeric(raw_val)

            painter.setPen(QColor(180, 180, 180))
            painter.drawText(4, int(row_y + _ROW_H - 2), label[:7].ljust(7))

            painter.setPen(QPen(QColor(100, 100, 100), 1.0))
            painter.drawLine(
                int(baseline_x), int(row_y),
                int(baseline_x), int(row_y + _ROW_H),
            )

            if draw_raw:
                self._draw_signed_bar(
                    painter, raw_num, min_value, max_value,
                    label_w, chart_w, row_y, _ROW_H,
                    QColor(110, 110, 110, 90),
                )
            if masked_val != float("-inf"):
                self._draw_signed_bar(
                    painter, _coerce_numeric(masked_val), min_value, max_value,
                    label_w, chart_w, row_y + 2.0, _ROW_H - 4.0,
                    QColor(120, 180, 255, 180),
                )

            painter.setPen(QColor(140, 140, 140))
            painter.drawText(
                int(label_w + chart_w + 4), int(row_y + _ROW_H - 2),
                (
                    f"{_coerce_numeric(masked_val):.2f}"
                    if masked_val != float("-inf") and masked_val is not None
                    else "-inf"
                ),
            )

        return y + len(labels) * (_ROW_H + _ROW_SPACING) + _SECTION_GAP

    def _draw_probability_section(
        self, painter: QPainter, width: float, y: float,
    ) -> float:
        painter.setFont(QFont("monospace", 7))
        painter.setPen(QColor(160, 160, 160))
        painter.drawText(4, int(y + 9), "Post-softmax probabilities:")
        y += _SECTION_HEADER_H

        labels = list(self._data.get("labels", []))
        probabilities = _coerce_probability_list(
            self._data.get("probabilities", []),
        )
        selected = str(self._data.get("selected_action", ""))

        label_w = 52.0
        value_w = 40.0
        chart_w = width - label_w - value_w - 10.0

        for i, label in enumerate(labels):
            row_y = y + i * (_ROW_H + _ROW_SPACING)
            prob = probabilities[i] if i < len(probabilities) else 0.0

            painter.setPen(QColor(180, 180, 180))
            painter.drawText(4, int(row_y + _ROW_H - 2), label[:7].ljust(7))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(80, 170, 255, 190))
            painter.drawRect(QRectF(label_w, row_y, chart_w * prob, _ROW_H))

            if label == selected:
                painter.setPen(QPen(QColor(255, 200, 0), 1.5))
                painter.setBrush(QColor(0, 0, 0, 0))
                painter.drawRect(QRectF(label_w, row_y, chart_w, _ROW_H))

            painter.setPen(QColor(140, 140, 140))
            painter.drawText(
                int(label_w + chart_w + 4), int(row_y + _ROW_H - 2),
                f"{prob:.2f}",
            )

        return y + len(labels) * (_ROW_H + _ROW_SPACING)

    @staticmethod
    def _draw_signed_bar(
        painter: QPainter,
        value: float,
        min_value: float,
        max_value: float,
        chart_x: float,
        chart_w: float,
        y: float,
        h: float,
        color: QColor,
    ) -> None:
        span = max(max_value - min_value, 1e-9)
        baseline_ratio = (0.0 - min_value) / span
        baseline_ratio = max(0.0, min(1.0, baseline_ratio))
        baseline_x = chart_x + chart_w * baseline_ratio

        if value >= 0:
            positive_span = max(max_value, 1e-9)
            width = min(value / positive_span, 1.0) * (chart_w * (1.0 - baseline_ratio))
            x = baseline_x
        else:
            negative_span = max(abs(min_value), 1e-9)
            width = min(abs(value) / negative_span, 1.0) * (chart_w * baseline_ratio)
            x = baseline_x - width

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRect(QRectF(x, y, width, h))
