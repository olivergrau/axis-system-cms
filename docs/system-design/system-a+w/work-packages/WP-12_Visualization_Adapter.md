# WP-12: Visualization Adapter

## Metadata
- Work Package: WP-12
- Title: Visualization Adapter for System A+W
- System: System A+W
- Source File: `src/axis/systems/system_aw/visualization.py`
- Test File: `tests/systems/system_aw/test_visualization.py`
- Model Reference: `01_System A+W Model.md` (for data structures in decision_data and trace_data)
- Dependencies: WP-10 (system orchestrator — defines `decision_data` and `trace_data` structure)

---

## 1. Objective

Provide a visualization adapter for System A+W that extends System A's adapter with curiosity-specific analysis sections and overlay types. The adapter reads `decision_data` and `trace_data` from step traces and produces structured visualization data for the viewer.

---

## 2. Design

### 2.1 Pattern: Follow System A

System A's `SystemAVisualizationAdapter` (361 lines) provides:
- 5 analysis sections (Step Overview, Observation, Drive Output, Decision Pipeline, Outcome)
- 3 overlay types (action_preference, drive_contribution, consumption_opportunity)
- Registration via `register_system_visualization("system_a", factory)`

System A+W's adapter follows the same pattern but extends it with curiosity and world model data.

### 2.2 Data Source

The adapter reads from `step_trace.system_data`, which contains:

```
system_data
├── decision_data          (from SystemAW.decide())
│   ├── observation
│   ├── hunger_drive       { activation, action_contributions }
│   ├── curiosity_drive    { activation, spatial_novelty, sensory_novelty,
│   │                        composite_novelty, action_contributions }
│   ├── arbitration        { hunger_weight, curiosity_weight }
│   ├── combined_scores    (6-tuple)
│   └── policy             { raw_scores, mask, probs, selected_action, ... }
│
└── trace_data             (from SystemAWTransition.transition())
    ├── energy_before, energy_after, energy_delta
    ├── action_cost, energy_gain
    ├── memory_entries_before, memory_entries_after
    ├── relative_position   (tuple[int, int])
    └── visit_count_at_current (int)
```

---

## 3. Analysis Sections (7 sections)

| # | Section | Source | Status |
|---|---|---|---|
| 1 | Step Overview | `trace_data` + `step_trace` | Extended with relative position |
| 2 | Observation | `decision_data.observation` | Inherited from System A pattern |
| 3 | Hunger Drive | `decision_data.hunger_drive` | Inherited from System A pattern |
| 4 | **Curiosity Drive** | `decision_data.curiosity_drive` | **New** |
| 5 | **Drive Arbitration** | `decision_data.arbitration` | **New** |
| 6 | Decision Pipeline | `decision_data.combined_scores` + `policy` | Extended (scores come from arbitration, not a single drive) |
| 7 | Outcome | `trace_data` + `step_trace` | Extended with world model info |

### 3.1 Step Overview (Extended)

Adds relative position and visit count:

| Row | Value |
|---|---|
| Timestep | `step_trace.timestep` |
| Action | `step_trace.action` |
| Energy Before | `trace_data["energy_before"]` |
| Energy After | `trace_data["energy_after"]` |
| Energy Delta | `trace_data["energy_delta"]` |
| **Relative Position** | `trace_data["relative_position"]` |
| **Visit Count** | `trace_data["visit_count_at_current"]` |

### 3.2 Curiosity Drive (New)

| Row | Value |
|---|---|
| Activation ($d_C$) | `curiosity_drive["activation"]` |
| Spatial Novelty | Per-direction: UP, DOWN, LEFT, RIGHT |
| Sensory Novelty | Per-direction: UP, DOWN, LEFT, RIGHT |
| Composite Novelty | Per-direction: UP, DOWN, LEFT, RIGHT |
| Action Contributions | Per-action: UP, DOWN, LEFT, RIGHT, CONSUME, STAY |

Each novelty type (spatial, sensory, composite) is shown as a parent row with 4 sub-rows for the directions.

### 3.3 Drive Arbitration (New)

| Row | Value |
|---|---|
| Hunger Weight ($w_H$) | `arbitration["hunger_weight"]` |
| Curiosity Weight ($w_C$) | `arbitration["curiosity_weight"]` |
| Dominant Drive | "Hunger" if $w_H \cdot d_H > w_C \cdot d_C$ else "Curiosity" |
| Weight Ratio ($w_C / w_H$) | Formatted ratio |

### 3.4 Decision Pipeline (Extended)

Same structure as System A but reads from `combined_scores` (post-arbitration) instead of single-drive `raw_contributions`. The key name in `policy_data` is `raw_scores` (set by `SystemAWPolicy` in WP-8).

### 3.5 Outcome (Extended)

Adds world model trace info:

| Row | Value |
|---|---|
| Moved | Yes/No |
| Position (world) | `step_trace.agent_position_after` |
| **Relative Position** | `trace_data["relative_position"]` |
| Action Cost | `trace_data["action_cost"]` |
| Energy Gain | `trace_data["energy_gain"]` |
| Terminated | Yes/No |
| Reason | termination reason or "—" |

---

## 4. Overlay Types (5 types)

| # | Key | Label | Status | Description |
|---|---|---|---|---|
| 1 | `action_preference` | Action Preference | Inherited | Arrows for movement probs, dot for consume, ring for stay |
| 2 | `drive_contribution` | Drive Contribution | **Extended** | Stacked bars: hunger (blue) + curiosity (green) per action |
| 3 | `consumption_opportunity` | Consumption Opportunity | Inherited | Diamond for current resource, neighbor dots |
| 4 | **`visit_count_heatmap`** | Visit Count Map | **New** | Heatmap of visit counts from the world model |
| 5 | **`novelty_field`** | Novelty Field | **New** | Per-direction composite novelty as arrows/indicators |

### 4.1 Drive Contribution (Extended)

System A shows only hunger contributions as a bar chart. System A+W shows both:
- Blue bars: $w_H \cdot d_H \cdot \phi_H(a)$ (hunger contribution to each action)
- Green bars: $w_C \cdot d_C \cdot \phi_C(a)$ (curiosity contribution to each action)

This visually shows the competition between the two drives.

### 4.2 Visit Count Heatmap (New)

Renders the agent's world model as a heatmap overlay on the grid:
- Each visited relative position gets a colored cell
- Color intensity proportional to visit count
- Requires mapping relative coordinates to world coordinates for rendering

**Implementation note:** The step trace contains `agent_position_before` (world coordinates) and `relative_position` (agent-relative). The offset between them gives the mapping: $p^{world} = p^{relative} + (p^{world}_0 - \hat{p}_0)$ where $p^{world}_0$ is the starting position. Since the adapter sees step traces but not the initial position directly, it derives the offset from: $\text{offset} = p^{world}_{before} - p^{relative}_{before+1}$ using the current step's data. Alternatively, the offset could be stored in trace_data during the first step.

For the initial implementation, a simpler approach: render the heatmap centered on the agent's current world position, using the visit counts at relative offsets. This avoids needing the initial position.

### 4.3 Novelty Field (New)

Renders the composite novelty signal as directional indicators at the agent's position:
- 4 arrows (one per cardinal direction)
- Arrow length proportional to $\nu_{dir}$
- Color indicates novelty intensity (white=low, bright=high)

Data source: `decision_data["curiosity_drive"]["composite_novelty"]`

---

## 5. Registration

```python
def _system_aw_vis_factory() -> SystemAWVisualizationAdapter:
    return SystemAWVisualizationAdapter(max_energy=100.0)

register_system_visualization("system_aw", _system_aw_vis_factory)
```

Following the same pattern as System A's registration at module import time.

---

## 6. Graceful Degradation

When curiosity is disabled ($\mu_C = 0$ or $w_C^{base} = 0$):
- Curiosity Drive section shows all zeros
- Drive Arbitration shows $w_C = 0$ or $d_C = 0$, dominant = "Hunger"
- Novelty field shows zero-length arrows
- Visit count heatmap still renders (world model is still updated)
- The adapter does **not** switch to System A's adapter — it always shows the full A+W structure

---

## 7. Test Plan

### File: `tests/systems/system_aw/test_visualization.py`

#### Analysis Sections

| # | Test | Description |
|---|---|---|
| 1 | `test_build_step_analysis_returns_7_sections` | Returns exactly 7 `AnalysisSection` objects |
| 2 | `test_section_titles` | Titles match: Step Overview, Observation, Hunger Drive, Curiosity Drive, Drive Arbitration, Decision Pipeline, Outcome |
| 3 | `test_curiosity_drive_section_rows` | Curiosity section has activation + 3 novelty groups + contributions |
| 4 | `test_arbitration_section_rows` | Arbitration section has hunger_weight, curiosity_weight, dominant drive |
| 5 | `test_step_overview_has_relative_position` | Step Overview includes "Relative Position" row |
| 6 | `test_outcome_has_world_model_info` | Outcome section includes relative position and visit count |

#### Overlays

| # | Test | Description |
|---|---|---|
| 7 | `test_available_overlay_types_count` | 5 overlay type declarations |
| 8 | `test_overlay_keys` | Keys: action_preference, drive_contribution, consumption_opportunity, visit_count_heatmap, novelty_field |
| 9 | `test_build_overlays_returns_5` | `build_overlays()` returns 5 `OverlayData` objects |
| 10 | `test_drive_contribution_has_both_drives` | Drive contribution overlay data contains both hunger and curiosity bar sets |
| 11 | `test_visit_count_heatmap_items` | Heatmap items correspond to visited positions |
| 12 | `test_novelty_field_has_4_directions` | Novelty field has 4 direction indicators |

#### Registration

| # | Test | Description |
|---|---|---|
| 13 | `test_visualization_registered` | `"system_aw"` is registered in the visualization registry |

#### Degradation

| # | Test | Description |
|---|---|---|
| 14 | `test_curiosity_zero_no_crash` | With all curiosity outputs = 0: all sections and overlays still produce valid output |
| 15 | `test_empty_world_model_heatmap` | World model with only origin visited: heatmap has 1 item |

---

## 8. Acceptance Criteria

- [ ] All 7 analysis sections produce valid output for a sample step
- [ ] All 5 overlay types produce valid overlay data
- [ ] Visualization adapter is auto-registered as `"system_aw"`
- [ ] Curiosity Drive section shows all novelty layers (spatial, sensory, composite)
- [ ] Drive Arbitration section shows weights and dominant drive
- [ ] Drive contribution overlay shows both hunger and curiosity bars
- [ ] Visit count heatmap renders visited positions
- [ ] Novelty field renders per-direction composite novelty
- [ ] Adapter degrades gracefully when curiosity is zeroed (no crashes, valid output)
- [ ] All 15 tests pass
