# System C+W -- Visualization Work Packages

**Visualization spec**: `docs-internal/ideas/system-cw/visualization-spec.md`  
**Visualization engineering spec**:
`docs-internal/ideas/system-cw/visualization-engineering-spec.md`  
**Phase**: First serious visualization implementation pass

---

## Implementation Strategy

The efficient implementation route is:

1. replace the minimal C+W adapter with a full left-panel analysis model
2. introduce a strong first overlay set using existing viewer primitives
3. upgrade the system-widget payload on the right side
4. only then decide whether generic viewer extensions are truly needed
5. finish with zoom-view checks, polish, and tests

This preserves the core architectural rule from the visualization
engineering spec:

> `system_cw` visualization should stay local to its own package unless a
> clearly generic viewer capability is required.

---

## Work Packages

| WP | Title | Dependencies | Scope | Key change |
|---|---|---|---|---|
| VIZ-WP-01 | C+W Adapter Analysis Panel Rebuild | None | Medium | Replace the minimal left-panel output with the full structured C+W section set |
| VIZ-WP-02 | First Overlay Set With Existing Primitives | VIZ-WP-01 | Medium | Add the initial C+W overlay set without changing generic overlay infrastructure |
| VIZ-WP-03 | Right-Side System Widget Payload Upgrade | VIZ-WP-01 | Medium | Expand `build_system_widget_data()` so the detail panel carries real C+W predictive/trace state |
| VIZ-WP-04 | Generic Widget Generalization Review | VIZ-WP-03 | Small/Medium | Decide whether the current prediction widget can represent C+W cleanly or needs a generic extension |
| VIZ-WP-05 | Dual-Modulation Overlay Decision | VIZ-WP-02 | Medium | Deliver `dual_modulation_split` either with existing primitives or a small generic overlay extension |
| VIZ-WP-06 | Zoom-View Compatibility and Detail-Panel Polish | VIZ-WP-02, VIZ-WP-03, VIZ-WP-05 | Medium | Ensure the zoomed agent-cell and right detail surface remain useful with the new C+W overlays |
| VIZ-WP-07 | Visualization Hardening, Tests, and Manual Acceptance | VIZ-WP-04, VIZ-WP-05, VIZ-WP-06 | Medium | Lock down adapter behavior, generic viewer changes, and acceptance checks |

---

## Dependency Graph

```text
VIZ-WP-01 (analysis panel rebuild)
  ├── VIZ-WP-02 (first overlay set)
  └── VIZ-WP-03 (right-side system widget payload)

VIZ-WP-03
  └── VIZ-WP-04 (generic widget generalization review)

VIZ-WP-02
  └── VIZ-WP-05 (dual-modulation overlay decision)

VIZ-WP-02 + VIZ-WP-03 + VIZ-WP-05
  └── VIZ-WP-06 (zoom compatibility and detail-panel polish)

VIZ-WP-04 + VIZ-WP-05 + VIZ-WP-06
  └── VIZ-WP-07 (hardening, tests, manual acceptance)
```

---

## Execution Strategy

- `VIZ-WP-01` must happen first because the section model is the main
  interpretability surface and also clarifies what data the overlays and
  widget should summarize.
- `VIZ-WP-02` and `VIZ-WP-03` can proceed in parallel after the section
  builders are structurally clear.
- `VIZ-WP-04` should not happen too early; first we should see how far the
  current widget path can be pushed using a better payload.
- `VIZ-WP-05` should explicitly stay behind the first overlay pass so the
  team can decide whether `dual_modulation_split` really needs a generic
  renderer extension.
- `VIZ-WP-06` belongs late because zoom-view usefulness depends on the
  overlay and widget choices that actually landed.
- `VIZ-WP-07` should remain the final hardening pass.

---

## Detailed Packages

### VIZ-WP-01: C+W Adapter Analysis Panel Rebuild

**Goal:** Replace the current minimal C+W left-panel output with a full,
structured analysis panel that reflects the System C+W execution model.

**Primary file:**

- `src/axis/systems/system_cw/visualization.py`

**Required outputs:**

- `build_step_analysis()` emits the full target section set
- sections appear in the order defined by the visualization spec
- per-action data is rendered using structured sub-rows rather than
  unreadable flat dumps
- section content aligns with C+W concepts:
  - raw drives
  - arbitration
  - shared predictive representation
  - drive-specific modulation
  - predictive update
  - drive-specific traces

**Likely local helper groups:**

- observation-format helpers
- novelty/world-context helpers
- action-score row builders
- predictive update row builders
- counterfactual summary row builders

**Explicit non-goals:**

- no generic viewer changes
- no overlay work yet
- no widget redesign yet

**Acceptance criteria:**

- the left panel is substantially more structured than the current adapter
- all mandatory sections exist
- action ordering is stable and consistent
- tests verify section presence and order

---

### VIZ-WP-02: First Overlay Set With Existing Primitives

**Goal:** Introduce the first useful overlay set for C+W while staying inside
the existing overlay infrastructure.

**Primary files:**

- `src/axis/systems/system_cw/visualization.py`

**Required outputs:**

- `available_overlay_types()` declares at least:
  - `action_preference`
  - `visit_count_heatmap`
  - `novelty_field`
  - `modulation_factor`
- `build_overlays()` emits meaningful C+W overlay data using currently
  supported item types

**Preferred existing overlay primitives:**

- `direction_arrow`
- `bar_chart`
- `center_dot`
- `saturation_ring`
- `modulation_cell`

**Design rule:**

- this phase should stay adapter-only
- no new generic overlay item type unless absolutely necessary

**Acceptance criteria:**

- overlays render correctly on the main grid
- overlay legends are coherent
- no generic viewer changes were needed for the first pass

---

### VIZ-WP-03: Right-Side System Widget Payload Upgrade

**Goal:** Make the right-side system-specific area genuinely informative for
System C+W.

**Primary files:**

- `src/axis/systems/system_cw/visualization.py`

**Required outputs:**

- `build_system_widget_data()` emits structured C+W payload data
- payload covers:
  - shared context
  - feature summary
  - hunger-side modulation
  - curiosity-side modulation
  - hunger confidence/frustration state
  - curiosity confidence/frustration state
  - prediction-error summary

**Preferred payload philosophy:**

- compact, high-signal, not maximal
- one payload that can drive a richer generic widget later

**Explicit non-goals:**

- do not yet commit to a new widget class
- do not let payload shape depend on imports from other systems

**Acceptance criteria:**

- the payload is nontrivial and clearly C+W-specific
- tests verify expected keys and stable structure

---

### VIZ-WP-04: Generic Widget Generalization Review

**Goal:** Decide whether the existing `PredictionSummaryWidget` can be
generalized cleanly for C+W or whether a small generic widget extension is
needed.

**Primary files if touched:**

- `src/axis/visualization/ui/prediction_summary_widget.py`
- `src/axis/visualization/ui/detail_panel.py`

**Decision branches:**

1. `PredictionSummaryWidget` can be generalized:
   - keep the current system-widget path
   - branch by payload shape, not by `system_type`

2. It becomes too awkward:
   - introduce a new generic widget path in `axis.visualization.ui`
   - keep the detail panel generic

**Key rule:**

- any viewer-side extension must remain generic and backward-compatible

**Acceptance criteria:**

- a clear decision is made
- if framework changes are needed, they do not special-case C+W by name
- `system_c` visualization still works unchanged or with compatible
  payload handling

---

### VIZ-WP-05: Dual-Modulation Overlay Decision

**Goal:** Deliver the most important new C+W overlay:
`dual_modulation_split`.

**Primary files:**

- `src/axis/systems/system_cw/visualization.py`
- maybe `src/axis/visualization/ui/overlay_renderer.py`
- maybe `src/axis/visualization/types.py`

**Possible implementation paths:**

1. Adapter-only approximation using existing overlay primitives
2. Small generic overlay renderer extension if the approximation is not
   sufficiently legible

**Design requirement:**

- both predictive channels must remain clearly distinguishable
- channel agreement vs divergence must be visually legible

**Acceptance criteria:**

- `dual_modulation_split` exists and is interpretable
- if a generic viewer change was introduced, it stays renderer-generic
- no cross-system visualization imports are added

---

### VIZ-WP-06: Zoom-View Compatibility and Detail-Panel Polish

**Goal:** Ensure the new overlays and right-side widget remain useful in the
detail panel, especially in the zoomed agent-cell view.

**Primary files if touched:**

- `src/axis/systems/system_cw/visualization.py`
- maybe `src/axis/visualization/ui/agent_cell_zoom.py`
- maybe `src/axis/visualization/ui/detail_panel.py`

**Required outputs:**

- validate which important C+W overlays are visible in the zoom view
- add agent-cell-local summary representations where necessary
- reduce clutter or redundancy if the detail area becomes overloaded

**Engineering rule:**

- do not redesign the detail panel globally
- only make the smallest generic improvements necessary

**Acceptance criteria:**

- zoomed agent-cell rendering remains meaningful for C+W
- the right-side combination of zoom + text + system widget does not feel
  redundant or unreadable

---

### VIZ-WP-07: Visualization Hardening, Tests, and Manual Acceptance

**Goal:** Lock down the visualization behavior and verify that the final
surface meets the intended interpretability goals.

**Likely touchpoints:**

- `tests/systems/system_cw/`
- `tests/visualization/` if generic viewer changes landed

**Required outputs:**

- adapter registration tests
- analysis section order/content tests
- overlay declaration tests
- system-widget payload tests
- viewer-level tests for any new generic widget or overlay behavior
- manual acceptance checklist for replay inspection

**Manual review checklist should verify:**

1. raw hunger vs raw curiosity is visible
2. arbitration is visible
3. shared predictive state is visible
4. hunger-side vs curiosity-side modulation is visible
5. prediction impact is visible
6. separate trace-pair state is visible
7. the zoom view still provides value

**Acceptance criteria:**

- tests cover all new adapter responsibilities
- any generic viewer extension is covered by dedicated tests
- the final visualization meets the acceptance criteria from the
  engineering spec

---

## Recommended Parallelization

For implementation, the most efficient split is likely:

- one stream on `VIZ-WP-01`
- one stream on `VIZ-WP-02`
- one stream on `VIZ-WP-03`

Then converge for:

- `VIZ-WP-04`
- `VIZ-WP-05`
- `VIZ-WP-06`

This keeps the early work largely adapter-local and avoids premature
framework churn.

---

## Recommended Next Practical Step

If implementation starts immediately, the best first package is:

- `VIZ-WP-01: C+W Adapter Analysis Panel Rebuild`

Reason:

- it is fully local to `system_cw`
- it improves interpretability immediately
- it clarifies the data organization needed for overlays and widget work
