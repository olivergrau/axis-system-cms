# WP-V.2.5 Implementation Brief -- System B Visualization Adapter

## Context

System B is a simpler system than System A -- 2-phase lifecycle, 6 actions (with `scan` instead of `consume`), a flat decision data structure, and no energy gain mechanism. Its visualization adapter is correspondingly simpler but introduces a new overlay item type (`radius_circle` for scan area).

### System B `system_data` Shape

```python
system_data = {
    "decision_data": {
        "weights": [float, ...],       # 6-element: up, down, left, right, scan, stay
        "probabilities": [float, ...], # 6-element: softmax output
        "last_scan": {
            "total_resource": float,   # total resource in last scan
            "cell_count": int,         # number of cells scanned
        },
    },
    "trace_data": {
        "energy_before": float,
        "energy_after": float,
        "energy_delta": float,
        "action_cost": float,
        "scan_total": float,           # persists from most recent scan
    },
}
```

### System B Config (relevant for visualization)

- `SystemBConfig.agent.max_energy: float` -- for vitality formatting
- `scan_radius` is hardcoded as `1` in `SystemB.action_context()`

### Action Space

`("up", "down", "left", "right", "scan", "stay")` -- 6 actions.

### Reference Documents

- `docs/v0.2.0/architecture/evolution/visualization-architecture.md` -- Section 11.2 (SystemBVisualizationAdapter)

---

## Objective

Implement `SystemBVisualizationAdapter` with 5 analysis sections and 2 overlay types.

---

## Scope

### 1. SystemBVisualizationAdapter

**File**: `src/axis/systems/system_b/visualization.py` (new)

```python
"""System B visualization adapter.

Simpler decision pipeline than System A. Features scan-area overlay
using the radius_circle item type.
"""

from __future__ import annotations

from typing import Any

from axis.sdk.trace import BaseStepTrace
from axis.visualization.types import (
    AnalysisRow,
    AnalysisSection,
    OverlayData,
    OverlayItem,
    OverlayTypeDeclaration,
)

ACTION_NAMES: tuple[str, ...] = ("up", "down", "left", "right", "scan", "stay")
DIRECTION_ACTIONS: tuple[str, ...] = ("up", "down", "left", "right")


class SystemBVisualizationAdapter:
    """Visualization adapter for System B."""

    def __init__(self, max_energy: float) -> None:
        self._max_energy = max_energy

    def phase_names(self) -> list[str]:
        return ["BEFORE", "AFTER_ACTION"]

    def vitality_label(self) -> str:
        return "Energy"

    def format_vitality(
        self,
        value: float,
        system_data: dict[str, Any],
    ) -> str:
        energy = value * self._max_energy
        return f"{energy:.2f} / {self._max_energy:.2f}"

    def build_step_analysis(
        self,
        step_trace: BaseStepTrace,
    ) -> list[AnalysisSection]:
        dd = step_trace.system_data.get("decision_data", {})
        td = step_trace.system_data.get("trace_data", {})
        return [
            self._section_step_overview(step_trace, td),
            self._section_decision_weights(dd),
            self._section_probabilities(dd),
            self._section_last_scan(dd),
            self._section_outcome(step_trace, td),
        ]

    def build_overlays(
        self,
        step_trace: BaseStepTrace,
    ) -> list[OverlayData]:
        dd = step_trace.system_data.get("decision_data", {})
        pos = (step_trace.agent_position_before.x, step_trace.agent_position_before.y)
        return [
            self._overlay_action_weights(dd, pos, step_trace.action),
            self._overlay_scan_result(dd, td=step_trace.system_data.get("trace_data", {}), agent_pos=pos),
        ]

    def available_overlay_types(self) -> list[OverlayTypeDeclaration]:
        return [
            OverlayTypeDeclaration(
                key="action_weights",
                label="Action Weights",
                description="Arrows showing action probabilities, highlighting selected action.",
            ),
            OverlayTypeDeclaration(
                key="scan_result",
                label="Scan Result",
                description="Circle showing scan area around agent with total resource label.",
            ),
        ]

    # ... private helper methods below ...
```

### 2. Analysis Section Helpers

#### `_section_step_overview(step_trace, trace_data)`

```
Title: "Step Overview"
Rows:
  - Timestep: str(step_trace.timestep)
  - Action: step_trace.action
  - Energy Before: f"{trace_data['energy_before']:.2f}"
  - Energy After: f"{trace_data['energy_after']:.2f}"
  - Energy Delta: f"{trace_data['energy_delta']:+.2f}"
  - Action Cost: f"{trace_data['action_cost']:.2f}"
```

#### `_section_decision_weights(decision_data)`

```
Title: "Decision Weights"
Rows:
  For each action in ACTION_NAMES:
    - label: action name
    - value: f"{weights[i]:.4f}"
```

#### `_section_probabilities(decision_data)`

```
Title: "Probabilities"
Rows:
  For each action in ACTION_NAMES:
    - label: action name
    - value: f"{probabilities[i]:.4f}"
```

#### `_section_last_scan(decision_data)`

```
Title: "Last Scan"
Rows:
  - Total Resource: f"{last_scan['total_resource']:.3f}"
  - Cell Count: str(last_scan['cell_count'])
```

Handle missing `last_scan` key defensively: if absent, show "No scan performed".

#### `_section_outcome(step_trace, trace_data)`

```
Title: "Outcome"
Rows:
  - Action: step_trace.action
  - Energy Delta: f"{trace_data['energy_delta']:+.2f}"
  - Scan Total: f"{trace_data['scan_total']:.3f}"
  - Terminated: "Yes" | "No"
  - Reason: step_trace.termination_reason or "—"
```

### 3. Overlay Helpers

#### `_overlay_action_weights(decision_data, agent_pos, selected_action)`

```
overlay_type: "action_weights"
items:
  For each direction action (up/down/left/right):
    OverlayItem(
        item_type="direction_arrow",
        grid_position=agent_pos,
        data={
            "direction": action,
            "length": probabilities[i],
            "is_selected": action == selected_action,
            "color": "selected" if selected else "default",
        },
    )
```

**Note**: Uses `probabilities` (not raw weights) for arrow length, since probabilities are normalized and produce consistent visual sizing. The selected action is passed explicitly from `step_trace.action`.

#### `_overlay_scan_result(decision_data, trace_data, agent_pos)`

```
overlay_type: "scan_result"
items:
  OverlayItem(
      item_type="radius_circle",
      grid_position=agent_pos,
      data={
          "radius_cells": 1,   # scan_radius is hardcoded as 1
          "label": f"Σ={trace_data['scan_total']:.2f}",
      },
  )
```

The scan result overlay always shows the circle (even when the agent didn't scan this step), because `scan_total` persists from the most recent scan.

### 4. Registration

**Same file**:

```python
from axis.visualization.registry import register_system_visualization

def _system_b_vis_factory() -> SystemBVisualizationAdapter:
    return SystemBVisualizationAdapter(max_energy=100.0)

register_system_visualization("system_b", _system_b_vis_factory)
```

Same note as System A: default `max_energy` in factory, actual value provided by session controller in WP-V.4.4.

---

## Out of Scope

- Canvas rendering of `radius_circle` overlay (WP-V.4.2)
- Modifications to System B code
- Any PySide6 code

---

## Architectural Constraints

### 1. Reads system_data Only

No imports from `axis.systems.system_b` at runtime. The adapter works on deserialized replay data.

### 2. No PySide6 Imports

All output is structured data.

### 3. 2-Phase Lifecycle

System B has only `["BEFORE", "AFTER_ACTION"]` -- no intermediate snapshots.

### 4. Action Order Convention

Action indices: `(up=0, down=1, left=2, right=3, scan=4, stay=5)`. Matches System B's `weights` and `probabilities` lists.

---

## Testing Requirements

**File**: `tests/v02/visualization/test_system_b_adapter.py` (new)

Create a fixture `_sample_step_trace()` with realistic System B `system_data`.

### Phase and vitality tests

1. **`test_phase_names`**: Assert `["BEFORE", "AFTER_ACTION"]`
2. **`test_vitality_label`**: Assert `"Energy"`
3. **`test_format_vitality`**: With `max_energy=50.0`, `format_vitality(0.8, {})` returns `"40.00 / 50.00"`

### Analysis section tests

4. **`test_build_step_analysis_section_count`**: Assert 5 sections
5. **`test_step_overview_section`**: Assert title, energy rows, action cost row
6. **`test_decision_weights_section`**: Assert title "Decision Weights", 6 rows with action names
7. **`test_probabilities_section`**: Assert title "Probabilities", 6 rows
8. **`test_last_scan_section`**: Assert title "Last Scan", total_resource and cell_count rows
9. **`test_last_scan_section_no_scan`**: When `last_scan` key is missing, assert graceful display
10. **`test_outcome_section`**: Assert title "Outcome", has action/delta/scan_total/terminated

### Overlay tests

11. **`test_build_overlays_count`**: Assert 2 overlays
12. **`test_action_weights_overlay`**: Assert `overlay_type == "action_weights"`
13. **`test_action_weights_direction_arrows`**: Assert 4 `direction_arrow` items
14. **`test_action_weights_selected_marked`**: Assert selected action has `is_selected=True`
15. **`test_scan_result_overlay`**: Assert `overlay_type == "scan_result"`
16. **`test_scan_result_radius_circle`**: Assert 1 `radius_circle` item with `radius_cells=1`
17. **`test_scan_result_label`**: Assert label contains scan total value

### Overlay declaration tests

18. **`test_available_overlay_types`**: Assert 2 declarations with correct keys
19. **`test_overlay_keys_match_data`**: Assert keys match overlay data types

### Registration test

20. **`test_system_b_registration`**: Import module, resolve `"system_b"`, assert adapter works

---

## Expected Deliverable

1. `src/axis/systems/system_b/visualization.py`
2. `tests/v02/visualization/test_system_b_adapter.py`
3. Confirmation that all existing tests still pass

---

## Important Final Constraint

System B's adapter is simpler than System A's (flat decision data, no drive subsystem, no memory). The implementation should be straightforward -- approximately 150-200 lines. The key new element is the `radius_circle` overlay item type, which the `OverlayRenderer` (WP-V.4.2) will render as a circle around the agent position.
