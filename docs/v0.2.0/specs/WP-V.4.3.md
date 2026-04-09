# WP-V.4.3 Implementation Brief -- Generalized UI Panels

## Context

The v0.1.0 visualization has 5 panel widgets: `StatusPanel` (48 lines), `StepAnalysisPanel` (155 lines), `DetailPanel` (80 lines), `ReplayControlsPanel` (76 lines), and `DebugOverlayPanel` (113 lines). All consume System A-specific view models (`StatusBarViewModel` with `ReplayPhase`, `StepAnalysisViewModel` with 6-action tuples, `ActionContextViewModel` with `Action` enum, `DebugOverlayPanel` with hard-coded 3-checkbox layout).

In v0.2.0, all panels consume adapter-produced structured data: `list[AnalysisSection]` for step analysis, `StatusBarViewModel` with string phase names and adapter-formatted vitality, `list[MetadataSection]` for world metadata, `list[OverlayTypeDeclaration]` for dynamic overlay checkboxes, and string phase names for the replay controls combo box.

### Predecessor State (After WP-V.4.2)

```
src/axis/visualization/
    ui/
        __init__.py
        canvas_widget.py
        overlay_renderer.py
    ...
```

### v0.1.0 Source Files Being Migrated

| v0.1.0 file | v0.2.0 destination | Key changes |
|---|---|---|
| `ui/status_panel.py` | `ui/status_panel.py` | Display adapter-provided vitality label + format, phase_name string, world info line |
| `ui/step_analysis_panel.py` | `ui/step_analysis_panel.py` | Render `list[AnalysisSection]` generically, not hard-coded 5 System A sections |
| `ui/detail_panel.py` | `ui/detail_panel.py` | Cell info from `GridCellViewModel`, world metadata sections from adapter |
| `ui/replay_controls_panel.py` | `ui/replay_controls_panel.py` | Phase combo box populated dynamically from `phase_names` list |
| `ui/debug_overlay_panel.py` | `ui/overlay_panel.py` | Checkboxes built dynamically from `OverlayTypeDeclaration` list |

### Reference Documents

- `docs/v0.2.0/architecture/evolution/visualization-architecture.md` -- Section 3 (Data Flow Pipeline), Section 14.1 (Migration map)
- `docs/v0.2.0/architecture/evolution/visualization-architecture-roadmap.md` -- WP-V.4.3

---

## Objective

Generalize the 5 UI panels to work with any system/world combination using adapter-produced structured data.

---

## Scope

### 1. StatusPanel

**File**: `src/axis/visualization/ui/status_panel.py` (new)

```python
"""Always-visible status bar for the visualization viewer."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from axis.visualization.view_models import StatusBarViewModel


class StatusPanel(QWidget):
    """Displays step, phase, playback, vitality, and world info."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._step_label = QLabel()
        self._phase_label = QLabel()
        self._playback_label = QLabel()
        self._vitality_label = QLabel()
        self._world_info_label = QLabel()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        for w in (
            self._step_label,
            self._phase_label,
            self._playback_label,
            self._vitality_label,
            self._world_info_label,
        ):
            layout.addWidget(w)
        self.setMaximumHeight(40)

    def set_frame(self, status: StatusBarViewModel) -> None:
        self._step_label.setText(
            f"Step: {status.step_index + 1} / {status.total_steps}"
        )
        self._phase_label.setText(f"Phase: {status.phase_name}")
        self._playback_label.setText(
            f"Playback: {status.playback_mode.value}"
        )
        self._vitality_label.setText(
            f"{status.vitality_label}: {status.vitality_display}"
        )
        if status.world_info:
            self._world_info_label.setText(status.world_info)
            self._world_info_label.show()
        else:
            self._world_info_label.hide()
```

**Changes from v0.1.0**:
- `Phase: {status.phase.name}` (ReplayPhase enum) → `Phase: {status.phase_name}` (string)
- `Energy: {status.energy:.2f}` (raw float) → `{status.vitality_label}: {status.vitality_display}` (adapter-formatted)
- New `_world_info_label` showing world adapter's `format_world_info()` output (e.g. "Toroidal topology (edges wrap)" or "3 hotspots active")

### 2. StepAnalysisPanel

**File**: `src/axis/visualization/ui/step_analysis_panel.py` (new)

```python
"""Step analysis panel that renders generic AnalysisSection data."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from axis.visualization.types import AnalysisRow, AnalysisSection


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
```

**Changes from v0.1.0**:
- Consumes `tuple[AnalysisSection, ...]` (generic) instead of `StepAnalysisViewModel` (System A-specific)
- Removes `_fmt_overview`, `_fmt_observation`, `_fmt_decision`, `_fmt_drive`, `_fmt_outcome` (5 System A-specific formatters)
- Single generic formatter that iterates sections → rows → sub_rows
- Method renamed from `set_frame(vm)` to `set_sections(sections)` for clarity
- `_ACTION_LABELS` and `_NEIGHBOR_LABELS` constants removed (system-specific)

### 3. DetailPanel

**File**: `src/axis/visualization/ui/detail_panel.py` (new)

```python
"""Detail panel showing selected entity info and world metadata."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from axis.visualization.types import MetadataSection
from axis.visualization.view_models import (
    AgentViewModel,
    GridCellViewModel,
    GridViewModel,
    SelectionType,
    SelectionViewModel,
    ViewerFrameViewModel,
)


class DetailPanel(QWidget):
    """Shows cell info, agent info, or world metadata sections."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._content_label = QLabel()
        self._content_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._content_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self._content_label)

    def set_frame(
        self,
        frame: ViewerFrameViewModel,
    ) -> None:
        lines: list[str] = []

        # Selection info
        sel = frame.selection
        if sel.selection_type == SelectionType.CELL and sel.selected_cell is not None:
            row, col = sel.selected_cell
            cell = self._find_cell(frame.grid, row, col)
            if cell is not None:
                lines.append("--- Cell Info ---")
                lines.append(f"Position: ({row}, {col})")
                lines.append(f"Obstacle: {'Yes' if cell.is_obstacle else 'No'}")
                lines.append(f"Traversable: {'Yes' if cell.is_traversable else 'No'}")
                lines.append(f"Resource: {cell.resource_value:.3f}")
                lines.append(f"Agent here: {'Yes' if cell.is_agent_here else 'No'}")
        elif sel.selection_type == SelectionType.AGENT:
            agent = frame.agent
            lines.append("--- Agent Info ---")
            lines.append(f"Position: ({agent.row}, {agent.col})")
            lines.append(f"Vitality: {frame.status.vitality_display}")
            lines.append(f"Step: {frame.status.step_index + 1}")
        else:
            lines.append("No entity selected")

        # World metadata sections
        if frame.world_metadata_sections:
            lines.append("")
            for section in frame.world_metadata_sections:
                lines.append(f"--- {section.title} ---")
                for row_data in section.rows:
                    lines.append(f"  {row_data.label}: {row_data.value}")

        self._content_label.setText("\n".join(lines))

    @staticmethod
    def _find_cell(
        grid: GridViewModel, row: int, col: int,
    ) -> GridCellViewModel | None:
        idx = row * grid.width + col
        if 0 <= idx < len(grid.cells):
            return grid.cells[idx]
        return None
```

**Changes from v0.1.0**:
- Cell info uses `GridCellViewModel` booleans (`is_obstacle`, `is_traversable`) instead of `cell.cell_type.value` (CellType enum)
- Agent info uses `frame.status.vitality_display` instead of `frame.agent.energy` and `frame.action_context`
- `ActionContextViewModel` references removed entirely (action context is in step analysis sections, not the detail panel)
- New: renders `frame.world_metadata_sections` below selection info (shows hotspot data for signal landscape, empty for grid_2d/toroidal)

### 4. ReplayControlsPanel

**File**: `src/axis/visualization/ui/replay_controls_panel.py` (new)

```python
"""Replay controls with dynamically populated phase combo box."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QWidget

from axis.visualization.view_models import StatusBarViewModel


class ReplayControlsPanel(QWidget):
    """Playback controls and phase selection."""

    step_backward_requested = Signal()
    step_forward_requested = Signal()
    play_requested = Signal()
    pause_requested = Signal()
    stop_requested = Signal()
    phase_selected = Signal(int)  # phase_index

    def __init__(
        self,
        phase_names: list[str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._updating = False

        # Buttons
        self._btn_back = QPushButton("<")
        self._btn_play = QPushButton("Play")
        self._btn_pause = QPushButton("Pause")
        self._btn_stop = QPushButton("Stop")
        self._btn_fwd = QPushButton(">")

        # Phase combo box -- populated from system adapter
        self._phase_combo = QComboBox()
        for name in phase_names:
            self._phase_combo.addItem(name)

        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        for btn in (
            self._btn_back, self._btn_play, self._btn_pause,
            self._btn_stop, self._btn_fwd,
        ):
            layout.addWidget(btn)
        layout.addWidget(self._phase_combo)
        self.setMaximumHeight(50)

        # Signals
        self._btn_back.clicked.connect(self.step_backward_requested)
        self._btn_play.clicked.connect(self.play_requested)
        self._btn_pause.clicked.connect(self.pause_requested)
        self._btn_stop.clicked.connect(self.stop_requested)
        self._btn_fwd.clicked.connect(self.step_forward_requested)
        self._phase_combo.currentIndexChanged.connect(self._on_phase_changed)

    def _on_phase_changed(self, index: int) -> None:
        if not self._updating:
            self.phase_selected.emit(index)

    def set_frame(self, status: StatusBarViewModel) -> None:
        self._updating = True
        try:
            self._phase_combo.setCurrentIndex(status.phase_index)
            self._btn_back.setEnabled(not status.at_start)
            self._btn_fwd.setEnabled(not status.at_end)
            playing = status.playback_mode.value == "playing"
            self._btn_play.setEnabled(not playing and not status.at_end)
            self._btn_pause.setEnabled(playing)
        finally:
            self._updating = False
```

**Changes from v0.1.0**:
- Constructor takes `phase_names: list[str]` to populate combo box dynamically (v0.1.0 hard-coded "BEFORE", "AFTER_REGEN", "AFTER_ACTION")
- `set_frame` uses `status.phase_index` (int) instead of `status.phase.value` (ReplayPhase enum)
- `phase_selected` signal emits `int` (phase_index) not `ReplayPhase`

### 5. OverlayPanel (renamed from DebugOverlayPanel)

**File**: `src/axis/visualization/ui/overlay_panel.py` (new)

```python
"""Dynamic overlay toggle panel built from OverlayTypeDeclaration."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QVBoxLayout, QWidget

from axis.visualization.types import OverlayTypeDeclaration


class OverlayPanel(QWidget):
    """Overlay toggle panel with dynamically created checkboxes.

    Replaces v0.1.0's DebugOverlayPanel which had hard-coded
    checkboxes for 3 System A overlay types.
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

        # Master checkbox
        self._master_cb = QCheckBox("Overlays")
        self._master_cb.setFont(QFont("sans-serif", 9, QFont.Weight.Bold))
        self._master_cb.toggled.connect(self._on_master_toggled)

        # Per-overlay checkboxes (built from declarations)
        cb_layout = QHBoxLayout()
        cb_layout.addWidget(self._master_cb)

        for decl in overlay_declarations:
            cb = QCheckBox(decl.label)
            cb.setToolTip(decl.description)
            cb.setEnabled(False)  # disabled until master is on
            cb.toggled.connect(
                lambda checked, key=decl.key: self._on_overlay_toggled(key, checked),
            )
            self._checkboxes[decl.key] = cb
            cb_layout.addWidget(cb)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.addLayout(cb_layout)
        self.setMaximumHeight(50)

    def _on_master_toggled(self, checked: bool) -> None:
        for cb in self._checkboxes.values():
            cb.setEnabled(checked)
        self.master_toggled.emit(checked)

    def _on_overlay_toggled(self, key: str, checked: bool) -> None:
        self.overlay_toggled.emit(key, checked)
```

**Changes from v0.1.0**:
- Constructor takes `list[OverlayTypeDeclaration]` to build checkboxes dynamically instead of hard-coding 3 System A overlays
- 3 individual signals (`action_preference_toggled`, `drive_contribution_toggled`, `consumption_opportunity_toggled`) replaced by single `overlay_toggled(str, bool)` signal with overlay key
- Renamed from `DebugOverlayPanel` to `OverlayPanel` (overlays are a first-class feature, not "debug")
- Legend labels removed (were System A-specific colored symbols)
- `OverlayTypeDeclaration.description` used as tooltip

---

## Out of Scope

- MainWindow assembly and signal wiring (WP-V.4.4)
- Session controller (WP-V.4.4)
- Launch entry point (WP-V.4.4)
- Keyboard shortcuts
- Panel styling beyond functional layout

---

## Architectural Constraints

### 1. No System-Specific Imports

All panels import from `axis.visualization.view_models` and `axis.visualization.types` only. No imports from `axis.systems.*`, `axis.world.*`, or `axis_system_a.*`.

### 2. Panels Are Passive Display

Panels receive data via `set_frame()` / `set_sections()` and display it. They do not call adapters, access the repository, or hold replay state. The session controller (WP-V.4.4) feeds them.

### 3. Generic Formatting

`StepAnalysisPanel` formats any `AnalysisSection` with a section title, rows (label: value), and optional sub-rows. It does not style or highlight specific rows -- the adapter controls what rows to produce, the panel renders them uniformly.

### 4. Dynamic Construction

`ReplayControlsPanel` and `OverlayPanel` take construction parameters (`phase_names`, `overlay_declarations`) that vary by system. They are constructed once per session with the system adapter's declared values.

---

## Testing Requirements

**File**: `tests/v02/visualization/test_ui_panels.py` (new)

PySide6 widget tests require a `QApplication` instance. Use a session-scoped fixture.

### StatusPanel tests

1. **`test_status_panel_construction`**: Create panel, assert no crash
2. **`test_status_panel_step_display`**: Call `set_frame()`, assert step label shows "Step: 1 / 10"
3. **`test_status_panel_phase_name`**: Assert phase label shows phase_name from status
4. **`test_status_panel_vitality_with_label`**: Assert vitality shows "Energy: 50.00 / 100.00" (adapter-formatted)
5. **`test_status_panel_world_info_shown`**: Assert world_info label visible when non-None
6. **`test_status_panel_world_info_hidden`**: Assert world_info label hidden when None

### StepAnalysisPanel tests

7. **`test_analysis_panel_hidden_initially`**: Assert hidden on construction
8. **`test_analysis_panel_shows_sections`**: Pass 2 sections, assert visible, text contains both titles
9. **`test_analysis_panel_hides_when_empty`**: Pass empty tuple, assert hidden
10. **`test_analysis_panel_renders_rows`**: Assert row labels and values appear in text
11. **`test_analysis_panel_renders_sub_rows`**: Assert sub_row content appears indented

### DetailPanel tests

12. **`test_detail_panel_no_selection`**: No selection → "No entity selected"
13. **`test_detail_panel_cell_selection`**: Cell selected → cell info displayed
14. **`test_detail_panel_agent_selection`**: Agent selected → agent info displayed
15. **`test_detail_panel_world_metadata`**: Frame with world_metadata_sections → sections displayed

### ReplayControlsPanel tests

16. **`test_controls_3phase_combo`**: Construct with 3 phases, assert combo has 3 items
17. **`test_controls_2phase_combo`**: Construct with 2 phases, assert combo has 2 items
18. **`test_controls_phase_selected_signal`**: Select combo item, assert `phase_selected` emitted with index
19. **`test_controls_button_enabled_state`**: At start → back disabled. At end → forward disabled.
20. **`test_controls_no_re_entrant_signal`**: `set_frame()` updates combo without emitting `phase_selected`

### OverlayPanel tests

21. **`test_overlay_panel_dynamic_checkboxes`**: Construct with 3 declarations, assert 3 checkboxes created
22. **`test_overlay_panel_2_declarations`**: Construct with 2 declarations (System B), assert 2 checkboxes
23. **`test_overlay_panel_master_enables_children`**: Toggle master on, assert child checkboxes enabled
24. **`test_overlay_panel_master_disables_children`**: Toggle master off, assert child checkboxes disabled
25. **`test_overlay_panel_overlay_toggled_signal`**: Toggle a checkbox, assert `overlay_toggled(key, True)` emitted
26. **`test_overlay_panel_tooltips`**: Assert checkbox tooltips match declaration descriptions

---

## Expected Deliverable

1. `src/axis/visualization/ui/status_panel.py`
2. `src/axis/visualization/ui/step_analysis_panel.py`
3. `src/axis/visualization/ui/detail_panel.py`
4. `src/axis/visualization/ui/replay_controls_panel.py`
5. `src/axis/visualization/ui/overlay_panel.py`
6. `tests/v02/visualization/test_ui_panels.py`
7. Confirmation that all existing tests still pass

---

## Expected File Structure

```
src/axis/visualization/
    ui/
        __init__.py                      # UNCHANGED (WP-V.4.1)
        canvas_widget.py                 # UNCHANGED (WP-V.4.1/4.2)
        overlay_renderer.py              # UNCHANGED (WP-V.4.2)
        status_panel.py                  # NEW
        step_analysis_panel.py           # NEW
        detail_panel.py                  # NEW
        replay_controls_panel.py         # NEW
        overlay_panel.py                 # NEW

tests/v02/visualization/
    test_ui_panels.py                    # NEW
```
