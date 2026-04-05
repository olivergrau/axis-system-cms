# VWP10 — Debug Overlay Readability Improvements

## Context

VWP9 added three debug overlay types (action preference arrows, drive contribution bars,
consumption opportunity indicators). Users report they are hard to interpret: there is no
legend explaining the visual encoding, no numeric readout panel, and the drive bars have
no labels identifying which action each bar represents. VWP10 addresses all three issues.

## Three Requirements

1. **R1 — Compact Legend**: Color/shape key below the overlay checkboxes, only for enabled overlays
2. **R2 — Debug Info Panel**: Numeric detail panel LEFT of the grid showing overlay values
3. **R3 — Action Labels on Drive Bars**: U/D/L/R/C/S text on each bar + activation display

## Files to Create

### `src/axis_system_a/visualization/ui/debug_info_panel.py`
New widget following the `DetailPanel` pattern (QVBoxLayout, title + content label):
- `set_frame(overlay: DebugOverlayViewModel | None)` — builds text from overlay data
- Hides itself when overlay is None or master disabled; shows when active
- **Action Preference section**: table of action name, probability, admissibility, selected marker
- **Drive Contribution section**: activation value + per-action score table
- **Consumption section**: current resource + neighbor resource/traversability table
- Uses `_ACTION_LABELS = ("UP", "DOWN", "LEFT", "RIGHT", "CONSUME", "STAY")` local constant
- Monospace font for tabular alignment
- Calls `self.show()`/`self.hide()` + `setMinimumWidth(180)`/`setMinimumWidth(0)`

### `tests/visualization/test_debug_info_panel.py`
- `TestConstruction`: creates successfully, has title/content labels
- `TestSetFrameNone`: hides when overlay None, hides when master disabled
- `TestActionPreferenceDisplay`: shows probabilities, admissibility, selected action, all 6 actions
- `TestDriveContributionDisplay`: shows activation, contributions, all 6 actions
- `TestConsumptionDisplay`: shows current resource, neighbor resources, traversability
- `TestMultipleOverlays`: shows all when all enabled, shows only enabled sections

## Files to Modify

### `src/axis_system_a/visualization/ui/grid_widget.py` (R3)
Modify `_draw_overlay_drive_contribution`:
- Add `QFont` to the `PySide6.QtGui` import
- Define `_DRIVE_LABELS = ("U", "D", "L", "R", "C", "S")`
- Draw activation value text at top of cell: `f"act:{dc.activation:.2f}"` in white
- Draw action label for each bar to the left of the bar: white text, small font scaled to bar height
- Shift bar drawing rightward by label margin (~12px or `w * 0.12`)
- Skip labels if `cell_h < 40` (too small to read)

### `src/axis_system_a/visualization/ui/debug_overlay_panel.py` (R1)
Extend layout from single row to two rows:
- Row 0: existing `QHBoxLayout` with 4 checkboxes (unchanged)
- Row 1: new `QHBoxLayout` with 3 `QLabel` legend entries (HTML rich text for colored symbols)
  - Action Pref: `"<span style='color:cyan'>■</span>=selected  <span style='color:orange'>■</span>=candidate  length=probability"`
  - Drive Contrib: `"<span style='color:#00C800'>■</span>=positive  <span style='color:#C80000'>■</span>=negative  U/D/L/R/C/S"`
  - Consumption: `"<span style='color:#FFD700'>◆</span>=resource  <span style='color:#00C800'>●</span>=neighbor  <span style='color:red'>✕</span>=blocked"`
- Each legend label visibility tracks its checkbox state (connect toggled → setVisible)
- All legend labels start hidden; entire legend row hides when master off
- Increase `setMaximumHeight` from 35 to 70
- Smaller font (point size 8) for legend labels

### `src/axis_system_a/visualization/ui/main_window.py` (R2)
- Import `DebugInfoPanel`
- Create `self._debug_info_panel = DebugInfoPanel()` in `__init__`
- Insert into splitter as index 0 (before grid):
  ```
  self._splitter.addWidget(self._debug_info_panel)  # index 0
  self._splitter.addWidget(self._grid_widget)        # index 1
  self._splitter.addWidget(self._detail_panel)       # index 2
  self._splitter.setSizes([0, 750, 250])
  ```
- Route overlay data in `set_frame`: `self._debug_info_panel.set_frame(frame.debug_overlay)`
- Add `@property debug_info_panel` for testing

### `tests/visualization/test_debug_overlay_panel.py` (R1)
Add `TestLegend` class:
- `test_legend_labels_hidden_by_default`
- `test_action_pref_legend_visible_when_checked`
- `test_drive_contrib_legend_visible_when_checked`
- `test_consumption_legend_visible_when_checked`
- `test_all_legends_hide_when_master_off`

### `tests/visualization/test_ui_construction.py` (R2)
- Add `test_contains_debug_info_panel` and `test_debug_info_panel_property`
- Add `test_widget_modules_do_not_import_replay_internals`: include `debug_info_panel` module
- Add `test_set_frame_routes_overlay_to_debug_info_panel` in `TestFramePropagation`

## Implementation Order

1. **R3 — Action Labels** (`grid_widget.py`) → run existing tests
2. **R1 — Compact Legend** (`debug_overlay_panel.py` + tests) → run tests
3. **R2 — Debug Info Panel** (new file + `main_window.py` + tests) → run full suite

## Verification

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python -m pytest tests/ -v --tb=short
```

All 1168 existing tests must continue to pass. New tests should add ~25-30 tests.
Manual verification: launch visualizer, enable debug overlays, confirm:
- Drive bars show U/D/L/R/C/S labels and activation value
- Legend appears below checkboxes for enabled overlay types
- Debug info panel slides in from left with numeric values


