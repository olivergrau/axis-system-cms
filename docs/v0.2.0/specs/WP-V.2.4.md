# WP-V.2.4 Implementation Brief -- System A Visualization Adapter

## Context

System A has the richest visualization of all systems -- 5 analysis sections and 3 overlay types reproducing the full v0.1.0 viewer experience. The adapter reads `system_data` from `BaseStepTrace` and builds structured data for the analysis panel and overlay renderer.

### System A `system_data` Shape

The framework runner packs System A's data as:

```python
system_data = {
    "decision_data": {
        "observation": {
            "current": {"traversability": float, "resource": float},
            "up":      {"traversability": float, "resource": float},
            "down":    {"traversability": float, "resource": float},
            "left":    {"traversability": float, "resource": float},
            "right":   {"traversability": float, "resource": float},
        },
        "drive": {
            "activation": float,                    # hunger drive d_H in [0, 1]
            "action_contributions": (float, ...,),  # 6-tuple: up, down, left, right, consume, stay
        },
        "policy": {
            "raw_contributions": (float, ...,),             # 6-tuple
            "admissibility_mask": (bool, ...,),              # 6-tuple
            "masked_contributions": (float, ...,),           # 6-tuple (-inf for masked)
            "probabilities": (float, ...,),                  # 6-tuple (softmax output)
            "selected_action": str,                          # e.g. "up"
            "temperature": float,
            "selection_mode": str,                           # "sample" or "argmax"
        },
    },
    "trace_data": {
        "energy_before": float,
        "energy_after": float,
        "energy_delta": float,
        "action_cost": float,
        "energy_gain": float,
        "memory_entries_before": int,
        "memory_entries_after": int,
    },
}
```

### System A Config (relevant for vitality formatting)

`SystemAConfig.agent.max_energy: float` -- needed to format `"3.45 / 5.00"`. The adapter receives `max_energy` at construction time via the factory.

### Action Space

`("up", "down", "left", "right", "consume", "stay")` -- 6 actions.

### Reference Documents

- `docs/v0.2.0/architecture/evolution/visualization-architecture.md` -- Section 11.2 (SystemAVisualizationAdapter)

---

## Objective

Implement `SystemAVisualizationAdapter` that produces 5 analysis sections, 3 overlay types, and System A-specific vitality formatting.

---

## Scope

### 1. SystemAVisualizationAdapter

**File**: `src/axis/systems/system_a/visualization.py` (new)

```python
"""System A visualization adapter.

Reproduces the full v0.1.0 analysis panel and debug overlay content
through structured data. Reads system_data from BaseStepTrace.
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

ACTION_NAMES: tuple[str, ...] = ("up", "down", "left", "right", "consume", "stay")
DIRECTION_ACTIONS: tuple[str, ...] = ("up", "down", "left", "right")


class SystemAVisualizationAdapter:
    """Visualization adapter for System A.

    Reads decision_data and trace_data from system_data to produce
    analysis sections and overlay data matching the v0.1.0 viewer.
    """

    def __init__(self, max_energy: float) -> None:
        self._max_energy = max_energy

    # ── Phase navigation ─────────────────────────────────────

    def phase_names(self) -> list[str]:
        return ["BEFORE", "AFTER_REGEN", "AFTER_ACTION"]

    # ── Vitality display ─────────────────────────────────────

    def vitality_label(self) -> str:
        return "Energy"

    def format_vitality(
        self,
        value: float,
        system_data: dict[str, Any],
    ) -> str:
        energy = value * self._max_energy
        return f"{energy:.2f} / {self._max_energy:.2f}"

    # ── Step analysis (5 sections) ───────────────────────────

    def build_step_analysis(
        self,
        step_trace: BaseStepTrace,
    ) -> list[AnalysisSection]:
        dd = step_trace.system_data.get("decision_data", {})
        td = step_trace.system_data.get("trace_data", {})
        return [
            self._section_step_overview(step_trace, td),
            self._section_observation(dd),
            self._section_drive_output(dd),
            self._section_decision_pipeline(dd),
            self._section_outcome(step_trace, td),
        ]

    # ── Debug overlays (3 types) ─────────────────────────────

    def build_overlays(
        self,
        step_trace: BaseStepTrace,
    ) -> list[OverlayData]:
        dd = step_trace.system_data.get("decision_data", {})
        pos = (step_trace.agent_position_before.x, step_trace.agent_position_before.y)
        return [
            self._overlay_action_preference(dd, pos),
            self._overlay_drive_contribution(dd, pos),
            self._overlay_consumption_opportunity(dd, pos),
        ]

    def available_overlay_types(self) -> list[OverlayTypeDeclaration]:
        return [
            OverlayTypeDeclaration(
                key="action_preference",
                label="Action Preference",
                description="Arrows showing action probabilities, dot for consume, ring for stay.",
            ),
            OverlayTypeDeclaration(
                key="drive_contribution",
                label="Drive Contribution",
                description="Bar chart showing hunger drive activation and per-action contributions.",
            ),
            OverlayTypeDeclaration(
                key="consumption_opportunity",
                label="Consumption Opportunity",
                description="Diamond on current cell if resource > 0, neighbor resource dots, X for blocked.",
            ),
        ]

    # ... private helper methods below ...
```

### 2. Analysis Section Helpers

Each `_section_*` method returns an `AnalysisSection`:

#### `_section_step_overview(step_trace, trace_data)`

```
Title: "Step Overview"
Rows:
  - Timestep: str(step_trace.timestep)
  - Action: step_trace.action
  - Energy Before: f"{trace_data['energy_before']:.2f}"
  - Energy After: f"{trace_data['energy_after']:.2f}"
  - Energy Delta: f"{trace_data['energy_delta']:+.2f}"
```

#### `_section_observation(decision_data)`

```
Title: "Observation"
Rows:
  - Current: f"resource={obs['current']['resource']:.3f}"
  - Up: f"resource={obs['up']['resource']:.3f}, {'traversable' | 'blocked'}"
  - Down: (same pattern)
  - Left: (same pattern)
  - Right: (same pattern)
```

Traversability: `"traversable"` if `traversability > 0`, else `"blocked"`.

#### `_section_drive_output(decision_data)`

```
Title: "Drive Output"
Rows:
  - Activation: f"{drive['activation']:.4f}"
  - Per-action contributions (sub_rows or individual rows):
    - Up: f"{contributions[0]:.4f}"
    - Down: f"{contributions[1]:.4f}"
    - Left: f"{contributions[2]:.4f}"
    - Right: f"{contributions[3]:.4f}"
    - Consume: f"{contributions[4]:.4f}"
    - Stay: f"{contributions[5]:.4f}"
```

#### `_section_decision_pipeline(decision_data)`

```
Title: "Decision Pipeline"
Rows:
  - Temperature: f"{policy['temperature']:.2f}"
  - Selection Mode: policy['selection_mode']
  - Per-action table (one row per action with sub_rows):
    For each action (up, down, left, right, consume, stay):
      - label: action name
      - value: f"p={probability:.4f}"
      - sub_rows:
          - Raw: f"{raw:.4f}"
          - Admissible: "Yes" | "No"
          - Masked: f"{masked:.4f}" or "-inf"
  - Selected: policy['selected_action']
```

#### `_section_outcome(step_trace, trace_data)`

```
Title: "Outcome"
Rows:
  - Moved: "Yes" | "No" (compare positions)
  - Position: f"({step_trace.agent_position_after.x}, {step_trace.agent_position_after.y})"
  - Action Cost: f"{trace_data['action_cost']:.2f}"
  - Energy Gain: f"{trace_data['energy_gain']:.2f}"
  - Terminated: "Yes" | "No"
  - Reason: step_trace.termination_reason or "—"
```

### 3. Overlay Helpers

Each `_overlay_*` method returns an `OverlayData`:

#### `_overlay_action_preference(decision_data, agent_pos)`

```
overlay_type: "action_preference"
items:
  For each direction action (up/down/left/right):
    OverlayItem(
        item_type="direction_arrow",
        grid_position=agent_pos,
        data={
            "direction": action,
            "length": probability,
            "is_selected": action == selected_action,
            "color": "selected" if selected else "default",
        },
    )
  If consume probability > 0:
    OverlayItem(
        item_type="center_dot",
        grid_position=agent_pos,
        data={"radius": probability, "is_selected": "consume" == selected_action},
    )
  If stay probability > 0:
    OverlayItem(
        item_type="center_ring",
        grid_position=agent_pos,
        data={"radius": probability, "is_selected": "stay" == selected_action},
    )
```

#### `_overlay_drive_contribution(decision_data, agent_pos)`

```
overlay_type: "drive_contribution"
items:
  OverlayItem(
      item_type="bar_chart",
      grid_position=agent_pos,
      data={
          "activation": drive["activation"],
          "values": list(drive["action_contributions"]),
          "labels": list(ACTION_NAMES),
      },
  )
```

#### `_overlay_consumption_opportunity(decision_data, agent_pos)`

```
overlay_type: "consumption_opportunity"
items:
  If current cell resource > 0:
    OverlayItem(item_type="diamond_marker", grid_position=agent_pos,
                data={"opacity": observation["current"]["resource"]})

  For each direction (up/down/left/right):
    neighbor_pos = compute neighbor position from agent_pos
    obs = observation[direction]
    if obs["traversability"] > 0:
      OverlayItem(item_type="neighbor_dot", grid_position=neighbor_pos,
                  data={"resource_value": obs["resource"], "is_traversable": True})
    else:
      OverlayItem(item_type="x_marker", grid_position=neighbor_pos, data={})
```

**Neighbor position computation**: Use SDK `MOVEMENT_DELTAS` from `axis.sdk.actions` to compute `(agent_x + dx, agent_y + dy)` for each direction.

### 4. Registration

**Same file**:

```python
from axis.visualization.registry import register_system_visualization

def _system_a_vis_factory() -> SystemAVisualizationAdapter:
    # Default max_energy for visualization when config is not available.
    # The actual value will be provided by the session controller (WP-V.4.4)
    # which reads it from the experiment config.
    return SystemAVisualizationAdapter(max_energy=100.0)

register_system_visualization("system_a", _system_a_vis_factory)
```

**Note on `max_energy`**: The factory uses a default value. In the full viewer (WP-V.4.4), the session controller will construct the adapter with the actual `max_energy` from the experiment config. For now, the factory provides a reasonable default. The `format_vitality()` method works correctly regardless -- it denormalizes `vitality * max_energy`.

### 5. Imports

```python
from axis.sdk.actions import MOVEMENT_DELTAS
```

Used for computing neighbor positions in the consumption opportunity overlay.

---

## Out of Scope

- Canvas rendering of overlays (WP-V.4.2)
- Analysis panel UI (WP-V.4.3)
- v0.1.0 code removal or migration
- Intermediate snapshot capture (the adapter declares 3 phases but `intermediate_snapshots["after_regen"]` is populated by the runner, not the adapter)

---

## Architectural Constraints

### 1. Reads system_data Only

The adapter never accesses `SystemA`, `SystemAConfig`, or any system-internal type at runtime. It reads `system_data` from `BaseStepTrace` as a plain dict. This ensures the adapter works on deserialized replay data without needing the system implementation to be available.

### 2. No PySide6 Imports

All output is structured data (`AnalysisSection`, `OverlayData`).

### 3. Satisfies SystemVisualizationAdapter Protocol

Through structural subtyping -- implements all 6 protocol methods.

### 4. Action Order Convention

Action indices in tuples follow the System A convention: `(up=0, down=1, left=2, right=3, consume=4, stay=5)`. This must match the order in `system_data["decision_data"]["drive"]["action_contributions"]` and `system_data["decision_data"]["policy"]["probabilities"]`.

---

## Testing Requirements

**File**: `tests/v02/visualization/test_system_a_adapter.py` (new)

Create a fixture `_sample_step_trace()` that returns a `BaseStepTrace` with realistic `system_data` matching the System A shape.

### Phase and vitality tests

1. **`test_phase_names`**: Assert `["BEFORE", "AFTER_REGEN", "AFTER_ACTION"]`
2. **`test_vitality_label`**: Assert `"Energy"`
3. **`test_format_vitality`**: With `max_energy=100.0`, `format_vitality(0.5, {})` returns `"50.00 / 100.00"`
4. **`test_format_vitality_full`**: `format_vitality(1.0, {})` returns `"100.00 / 100.00"`

### Analysis section tests

5. **`test_build_step_analysis_section_count`**: Assert 5 sections returned
6. **`test_step_overview_section`**: Assert title "Step Overview", has energy before/after/delta rows
7. **`test_observation_section`**: Assert title "Observation", has 5 rows (current + 4 directions)
8. **`test_observation_traversability_labels`**: Assert `"traversable"` and `"blocked"` appear correctly
9. **`test_drive_output_section`**: Assert title "Drive Output", has activation row, 6 contribution values
10. **`test_decision_pipeline_section`**: Assert title "Decision Pipeline", has temperature, selection mode, per-action rows
11. **`test_outcome_section`**: Assert title "Outcome", has moved/position/cost/gain/terminated rows

### Overlay tests

12. **`test_build_overlays_count`**: Assert 3 overlays returned
13. **`test_action_preference_overlay_type`**: Assert `overlay_type == "action_preference"`
14. **`test_action_preference_has_direction_arrows`**: Assert 4 `direction_arrow` items for movement actions
15. **`test_action_preference_selected_action_marked`**: Assert the selected action has `is_selected=True`
16. **`test_action_preference_consume_dot`**: When consume probability > 0, assert `center_dot` item present
17. **`test_action_preference_stay_ring`**: When stay probability > 0, assert `center_ring` item present
18. **`test_drive_contribution_overlay`**: Assert `overlay_type == "drive_contribution"`, single `bar_chart` item
19. **`test_drive_contribution_bar_chart_data`**: Assert `activation`, `values` (6 floats), `labels` (6 strings)
20. **`test_consumption_opportunity_overlay`**: Assert `overlay_type == "consumption_opportunity"`
21. **`test_consumption_opportunity_diamond_on_resource`**: When current resource > 0, assert `diamond_marker`
22. **`test_consumption_opportunity_neighbor_dots`**: Assert `neighbor_dot` for traversable neighbors
23. **`test_consumption_opportunity_x_marker_for_blocked`**: Assert `x_marker` for non-traversable neighbor

### Overlay declaration tests

24. **`test_available_overlay_types`**: Assert 3 declarations with correct keys
25. **`test_overlay_keys_match_data`**: Assert overlay declaration keys match `OverlayData.overlay_type` values

### Registration test

26. **`test_system_a_registration`**: Import module, resolve `"system_a"`, assert adapter has correct methods

---

## Expected Deliverable

1. `src/axis/systems/system_a/visualization.py`
2. `tests/v02/visualization/test_system_a_adapter.py`
3. Confirmation that all existing tests still pass
