# System C+W -- Visualization Engineering Specification

## Status

Draft

## Based on

- `docs-internal/ideas/system-cw/draft-visualization.md`
- `docs-internal/ideas/system-cw/visualization-spec.md`
- existing viewer manuals and extension contracts

---

## 1. Purpose

This document maps the C+W visualization design onto the current AXIS
viewer implementation.

Its role is to define:

- which parts can be implemented entirely inside the `system_cw`
  visualization adapter
- which parts may require a small generic viewer extension
- how left-panel analysis, overlays, zoomed agent-cell rendering, and
  right-side system widget should be assembled
- which implementation boundaries must be preserved

This is an engineering mapping document, not an implementation.

---

## 2. Scope

### In scope

- `src/axis/systems/system_cw/visualization.py`
- possible small generic extensions in `src/axis/visualization/`
- analysis-panel structure for C+W
- C+W overlay set
- C+W system-widget payload
- compatibility of overlays with the zoomed agent-cell widget
- visualization-oriented tests

### Out of scope

- changes to replay persistence formats
- changes to experiment execution
- new system semantics
- UI redesign of the whole viewer
- direct code reuse from `system_aw` or `system_c` visualization modules

---

## 3. Architectural Constraints

### 3.1 System independence

`system_cw` visualization code must remain independent from other
system packages.

Allowed:

- conceptually following the visual structure of `system_aw` and
  `system_c`
- locally re-implementing small helper logic when needed

Not allowed:

- importing helper functions from `axis.systems.system_aw.visualization`
- importing helper functions from `axis.systems.system_c.visualization`
- subclassing those adapters

### 3.2 Viewer extension rule

If a new viewer capability is needed, it must be introduced
generically inside `axis.visualization`.

Examples:

- a new overlay item type
- a more generic system-widget rendering path

It must not be added as a special-case hook named specifically for
System C+W.

### 3.3 Backward compatibility

Any generic viewer change must preserve:

- existing `system_a`, `system_aw`, `system_b`, and `system_c`
  visualization behavior
- current adapter registration and launch flow
- current replay mode assumptions (`full`, reconstructed `delta`)

---

## 4. Current Implementation Baseline

## 4.1 Existing `system_cw` adapter

The current file [src/axis/systems/system_cw/visualization.py](/workspaces/axis-system-cms/src/axis/systems/system_cw/visualization.py:1)
is a minimal placeholder adapter.

Current characteristics:

- a few compact analysis sections
- no meaningful overlays
- no substantial `build_system_widget_data()` payload

This is structurally valid but not sufficient for the design goals.

## 4.2 Existing generic viewer surfaces

The viewer currently separates system-specific outputs into:

- left textual analysis sections
- center overlay layers on the main grid
- right-side zoomed agent-cell widget
- right-side system widget payload via `build_system_widget_data()`

Relevant framework files:

- [src/axis/visualization/protocols.py](/workspaces/axis-system-cms/src/axis/visualization/protocols.py:1)
- [src/axis/visualization/view_model_builder.py](/workspaces/axis-system-cms/src/axis/visualization/view_model_builder.py:1)
- [src/axis/visualization/ui/detail_panel.py](/workspaces/axis-system-cms/src/axis/visualization/ui/detail_panel.py:1)
- [src/axis/visualization/ui/agent_cell_zoom.py](/workspaces/axis-system-cms/src/axis/visualization/ui/agent_cell_zoom.py:1)
- [src/axis/visualization/ui/prediction_summary_widget.py](/workspaces/axis-system-cms/src/axis/visualization/ui/prediction_summary_widget.py:1)
- [src/axis/visualization/ui/overlay_renderer.py](/workspaces/axis-system-cms/src/axis/visualization/ui/overlay_renderer.py:1)

---

## 5. Engineering Strategy

The recommended implementation strategy is:

1. fully replace the minimal C+W analysis-panel construction
2. add a first serious C+W overlay set
3. upgrade the C+W system-widget payload
4. evaluate whether the existing generic `PredictionSummaryWidget`
   can be generalized enough
5. only if necessary, introduce a small generic widget or overlay
   extension in the viewer framework

This mirrors the same philosophy as the rest of C+W:

- local C+W code first
- generic framework extraction only when clearly justified

---

## 6. File-Level Target Changes

## 6.1 System-local files

The primary implementation target is:

- [src/axis/systems/system_cw/visualization.py](/workspaces/axis-system-cms/src/axis/systems/system_cw/visualization.py:1)

This file should become the full C+W adapter and own:

- section building
- overlay declarations
- overlay data construction
- system-widget payload construction
- C+W-local formatting helpers

### Optional companion test file additions

The implementation should add or expand tests under:

- `tests/systems/system_cw/`
- `tests/visualization/` if generic viewer changes are introduced

## 6.2 Generic viewer files that may need extension

Potential generic touchpoints:

- [src/axis/visualization/ui/prediction_summary_widget.py](/workspaces/axis-system-cms/src/axis/visualization/ui/prediction_summary_widget.py:1)
- [src/axis/visualization/ui/detail_panel.py](/workspaces/axis-system-cms/src/axis/visualization/ui/detail_panel.py:1)
- [src/axis/visualization/ui/overlay_renderer.py](/workspaces/axis-system-cms/src/axis/visualization/ui/overlay_renderer.py:1)
- [src/axis/visualization/types.py](/workspaces/axis-system-cms/src/axis/visualization/types.py:1) only if a new overlay item payload pattern is needed

These changes are optional and must remain generic.

---

## 7. Left Analysis Panel Mapping

## 7.1 Adapter responsibility

All left-panel improvements should be delivered through
`build_step_analysis()`.

No framework changes are required for section ordering or row
structure. The existing `AnalysisSection` / `AnalysisRow` model is
sufficient.

## 7.2 Required adapter sections

`build_step_analysis()` should emit the following sections:

1. `Step Overview`
2. `Observation`
3. `Curiosity And World Context`
4. `Raw Drive Outputs`
5. `Arbitration`
6. `Shared Predictive Representation`
7. `Hunger-side Predictive Modulation`
8. `Curiosity-side Predictive Modulation`
9. `Decision Pipeline`
10. `Predictive Update`
11. `Drive-Specific Trace Update`
12. `Outcome`

## 7.3 Engineering note on row structure

The implementation should prefer nested `sub_rows` over flattened
comma-separated text when rendering:

- per-action hunger values
- per-action curiosity values
- per-action modulation factors
- counterfactual action winners or score summaries

This is important because left-panel readability is explicitly part of
scope.

## 7.4 Suggested local helper groups

Inside `system_cw/visualization.py`, the implementation should likely
split helpers by section family:

- observation formatting helpers
- world / novelty formatting helpers
- action-score row builders
- trace / error row builders
- counterfactual summary helpers

These should stay local to the file unless a truly generic pattern
emerges.

---

## 8. Overlay Engineering Plan

## 8.1 Overlay declaration set

`available_overlay_types()` should declare at least:

- `action_preference`
- `visit_count_heatmap`
- `novelty_field`
- `modulation_factor`
- `dual_modulation_split`

## 8.2 Overlay implementation categories

### 8.2.1 Reusable existing overlay primitives

The first four overlay concepts should preferentially use existing
overlay item types already supported by the renderer:

- `direction_arrow`
- `bar_chart`
- `diamond_marker`
- `center_dot`
- `saturation_ring`
- `modulation_cell`

This minimizes framework churn.

### 8.2.2 New overlay primitive evaluation

The only overlay likely to justify a generic extension is
`dual_modulation_split`.

The implementation should first attempt to express this using existing
items, for example:

- stacked bar charts on the same target cell
- paired center dots or rings
- two directional arrows with differentiated color coding

If these options are visually insufficient, then a new generic overlay
item type may be introduced.

### 8.2.3 If a new overlay type is required

The preferred generic addition would be something like:

- `split_modulation_cell`
  or
- `dual_bar_cell`

Its renderer must live in `overlay_renderer.py` and accept a neutral,
generic payload.

It must not encode C+W-specific naming directly.

## 8.3 Zoomed agent-cell compatibility

Because the right-top zoom widget only renders overlay items located on
the agent cell, the engineering implementation must check which C+W
signals actually appear there.

Implication:

- purely neighbor-placed dual-channel overlays will disappear from the
  zoom view
- therefore at least one important C+W overlay must also produce an
  agent-cell-local representation when appropriate

Recommended engineering rule:

- directional overlays may still target neighbors on the main grid
- but they should also provide a compact current-cell summary overlay
  when the information is central to the current step

This is especially relevant for:

- `dual_modulation_split`
- modulation summary
- trace-state indicator if implemented as an overlay

---

## 9. Right-Side System Widget Engineering Plan

## 9.1 Current architecture

The right-side widget path is currently:

- adapter emits `build_system_widget_data()`
- `ViewModelBuilder` stores this as `system_widget_data`
- `DetailPanel` passes it to `PredictionSummaryWidget`

This is already sufficient for a first C+W implementation if the
generic widget can be broadened.

## 9.2 Preferred implementation path

Preferred approach:

- extend the existing generic
  [PredictionSummaryWidget](/workspaces/axis-system-cms/src/axis/visualization/ui/prediction_summary_widget.py:1)
  so it can render both `system_c` and `system_cw` payloads

Why this is preferred:

- `system_cw` is still prediction-centric
- there is already a generic hook in place
- this avoids introducing an unnecessary second widget path

## 9.3 Required payload shape for C+W

`build_system_widget_data()` for `system_cw` should provide structured
data covering three blocks:

### Block A: shared predictive state

- `context`
- `features`

### Block B: dual modulation state

- hunger-side modulation factors
- curiosity-side modulation factors
- optional per-action final combined or delta summary

### Block C: dual trace state

- hunger confidences
- hunger frustrations
- curiosity confidences
- curiosity frustrations
- feature error summary
- hunger error summary
- curiosity error summary

## 9.4 Generic widget adaptation requirement

If `PredictionSummaryWidget` is extended, it must not become
System-C+W-specific in naming or assumptions.

It should instead support:

- single-channel prediction payloads (`system_c`)
- dual-channel prediction payloads (`system_cw`)

Possible engineering pattern:

- inspect the payload for optional channel keys
- render the simpler System C view when only one channel exists
- render the dual-channel layout when both channels exist

## 9.5 Fallback option

If this generalization becomes too awkward, a new generic widget class
may be introduced in `axis.visualization.ui`, but it must still be
driven by the same system-widget data hook.

The detail panel should remain generic:

- it may branch on payload shape
- it must not branch on concrete `system_type`

---

## 10. Proposed C+W Payload Contract

The exact final schema may evolve, but the engineering target should be
close to this structure:

```text
{
  "widget_mode": "dual_prediction",
  "context": int,
  "features": [...],
  "hunger_modulation_factors": {action -> float},
  "curiosity_modulation_factors": {action -> float},
  "hunger_confidences": {action or summary_key -> float},
  "hunger_frustrations": {action or summary_key -> float},
  "curiosity_confidences": {action or summary_key -> float},
  "curiosity_frustrations": {action or summary_key -> float},
  "feature_error_positive": float,
  "feature_error_negative": float,
  "hunger_error_positive": float,
  "hunger_error_negative": float,
  "curiosity_error_positive": float,
  "curiosity_error_negative": float
}
```

Engineering note:

- per-action trace maps are acceptable if they exist meaningfully
- compact summary values are also acceptable if the traces are not
  action-specific in C+W

The widget should optimize for clarity, not for maximal payload width.

---

## 11. Suggested Implementation Sequence

## Phase 1: adapter-only section rebuild

Deliver:

- full left-panel structure
- no generic viewer changes yet

Files:

- `src/axis/systems/system_cw/visualization.py`

## Phase 2: adapter overlay expansion

Deliver:

- action preference
- visit count heatmap
- novelty field
- modulation factor

Still prefer existing overlay primitives only.

## Phase 3: dual-modulation overlay decision

Deliver one of:

- adapter-only approximation using existing primitives
  or
- a new generic overlay renderer primitive

This phase is the most likely viewer-extension point.

## Phase 4: right-side system widget upgrade

Deliver:

- richer `build_system_widget_data()` payload
- generic widget broadening if needed

Files likely touched:

- `src/axis/systems/system_cw/visualization.py`
- maybe `src/axis/visualization/ui/prediction_summary_widget.py`
- maybe `src/axis/visualization/ui/detail_panel.py`

## Phase 5: polish and consistency

Deliver:

- overlay legend tuning
- section label tuning
- zoom-view sanity pass
- visual redundancy reduction if the display feels overloaded

---

## 12. Test Strategy

## 12.1 System-local tests

Add or extend tests that verify:

- adapter registration for `system_cw`
- analysis section count and ordering
- presence of expected overlay types
- presence of expected widget-data keys

These belong under `tests/systems/system_cw/`.

## 12.2 Generic viewer tests

Only if generic viewer code changes are introduced, add tests for:

- new overlay item rendering dispatch
- widget mode branching
- detail-panel behavior with dual-channel payloads

These belong under `tests/visualization/`.

## 12.3 Manual acceptance checks

Because visualization is partly perceptual, a manual smoke pass should
also be part of acceptance.

Recommended checks:

1. open a replay with strong curiosity behavior
2. open a replay with visible predictive divergence
3. inspect both main grid and zoomed agent cell
4. confirm that the right-side widget is informative without reading
   the left panel
5. confirm that left-panel sections tell a coherent story in order

---

## 13. Risks and Mitigations

## Risk 1: visual overload

System C+W carries both A+W and C information and can easily become too
dense.

Mitigation:

- strict section ordering
- compact right-side widget
- selective overlay set

## Risk 2: zoom-view mismatch

Important overlays may disappear or become unreadable in the zoomed
agent-cell widget.

Mitigation:

- require at least one agent-cell-local representation for the most
  important C+W state

## Risk 3: generic widget overfitting

Trying to retrofit C+W into the current prediction widget may create an
awkward, special-case-heavy implementation.

Mitigation:

- first attempt generic broadening
- if that becomes messy, introduce a cleaner generic widget path

## Risk 4: hidden dependency drift

There is a temptation to borrow helpers directly from `system_aw` or
`system_c` visualization files.

Mitigation:

- explicitly keep copied logic local
- enforce no cross-system imports during review

---

## 14. Acceptance Criteria

The visualization engineering work should be considered complete when:

1. `system_cw` has a substantially richer adapter than the current
   placeholder
2. left-panel step analysis is clearly structured and readable
3. the right-side system widget communicates shared prediction plus
   separate drive-specific trust state
4. at least one new C+W-specific overlay is implemented
5. the zoomed agent-cell view remains meaningful for the chosen
   overlays
6. no runtime dependency from `system_cw` visualization to
   `system_aw` or `system_c` exists

---

## 15. Recommended Next Artifact

The next operational document after this spec should be either:

- a `visualization-work-packages.md`
  or
- direct implementation tickets grouped into:
  - adapter sections
  - overlays
  - widget payload / widget rendering
  - tests
