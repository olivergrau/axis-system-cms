# System C+W Visualization Specification

## 1. Purpose

This document specifies the intended visualization behavior for
`system_cw`.

It refines the earlier visualization draft into a more concrete target
for later engineering work. The scope is the existing AXIS replay
viewer:

- left step-analysis panel
- center grid canvas and overlays
- right detail panel, including
  - the zoomed agent-cell view at the top
  - the system-specific widget area below it

The design goal is to make System C+W legible as a synthesis of
System A+W and System C while preserving the current viewer
architecture as much as possible.

---

## 2. Constraints

The implementation must respect the following constraints.

### 2.1 System independence

The `system_cw` visualization code must not depend on runtime imports
from `system_aw` or `system_c`.

Allowed:

- reading those implementations as design references
- copying small local helper ideas where appropriate
- relying on shared visualization framework contracts

Not allowed:

- importing helper functions from other system visualization modules
- subclassing other system visualization adapters
- creating runtime dependencies from `system_cw` to `system_aw` or
  `system_c`

### 2.2 Viewer contract stability

The implementation should fit the current visualization architecture:

- `build_step_analysis()`
- `build_overlays()`
- `available_overlay_types()`
- `build_system_widget_data()`

No change to replay compatibility or trace-mode semantics is allowed.

### 2.3 Trace assumptions

The visualization must work for replay-compatible traces:

- `full`
- `delta` after reconstruction

It must not assume `light` support.

---

## 3. Viewer Surfaces To Cover

System C+W visualization is not just one adapter output. It affects
three distinct viewer surfaces.

## 3.1 Left: step-analysis panel

This is the primary textual inspection surface. It must become more
structured and easier to scan than the current minimal C+W output.

## 3.2 Right top: zoomed agent-cell view

This is the enlarged rendering of the agent's current cell in the
detail panel. It already renders overlays that land on the agent cell.

System C+W design must therefore consider whether the new overlays are
meaningful when seen:

- on the full grid
- in the zoomed agent-cell widget

If an overlay is only legible on the main grid but visually useless in
the zoom view, that is a design problem.

## 3.3 Right bottom: system-specific widget

This is currently fed by `build_system_widget_data()` and rendered via
the generic prediction-style widget path in the detail panel.

For System C+W, the right-side system widget must become more capable
than the current minimal placeholder data.

---

## 4. Conceptual Visualization Model

System C+W must visually expose the following model structure:

1. raw local observation and world-model context
2. raw dual-drive outputs
3. arbitration state
4. shared predictive representation
5. separate hunger-side predictive modulation
6. separate curiosity-side predictive modulation
7. behavioral competition after modulation
8. post-action predictive update
9. separate hunger and curiosity trace states

This is the core interpretation path the viewer must support.

The user should be able to answer, for any step:

1. What did hunger want?
2. What did curiosity want?
3. How were the drives weighted?
4. What was the shared predictive context?
5. How did prediction change hunger-side scoring?
6. How did prediction change curiosity-side scoring?
7. Did prediction alter the effective winner?
8. What evidence was observed after acting?
9. How did the two trace pairs update?

---

## 5. Left Panel Specification

The left step-analysis panel will remain text-based, but its text
arrangement should become substantially more structured.

The spec does not require a new widget. It explicitly prefers better
sectioning and row arrangement inside the existing `AnalysisSection` /
`AnalysisRow` model.

## 5.1 Section order

The analysis panel should contain the following sections in this exact
conceptual order:

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

This order is mandatory because it mirrors the mental model of the
system.

## 5.2 Text arrangement style

The left panel should not present large comma-joined value blobs when a
structured row group is possible.

Preferred patterns:

- one scalar per row for key step values
- grouped sub-rows for per-action values
- short aligned summaries before detailed rows
- consistent ordering of actions:
  `up, down, left, right, consume, stay`

Discouraged patterns:

- long single-line action dumps like
  `up:0.123, down:0.031, left:-0.22, ...`
- mixing raw and modulated values in the same row without labeling

## 5.3 Detailed section content

### 5.3.1 `Step Overview`

Must show:

- timestep
- chosen action
- energy before
- energy after
- energy delta
- relative position
- visit count at current cell
- encoded context id

### 5.3.2 `Observation`

Must show:

- current cell resource
- per-direction resource
- per-direction traversability

### 5.3.3 `Curiosity And World Context`

Must show:

- spatial novelty per direction
- sensory novelty per direction
- composite novelty per direction
- optional mean composite novelty
- current relative position
- current visit count

### 5.3.4 `Raw Drive Outputs`

Must show:

- hunger activation
- curiosity activation
- hunger raw action contributions
- curiosity raw action contributions

These must be clearly separated from predictive modulation values.

### 5.3.5 `Arbitration`

Must show:

- hunger weight
- curiosity weight
- weighted hunger pressure
- weighted curiosity pressure

If concise enough, may also show:

- whether curiosity dominates

### 5.3.6 `Shared Predictive Representation`

Must show:

- encoded context
- predictive feature vector
- a short textual note or label indicating that the feature vector
  mixes resource-derived and novelty-derived components

If the raw feature vector is long, it may be split into:

- compact named summary rows
- one full vector row

### 5.3.7 `Hunger-side Predictive Modulation`

Must show:

- raw hunger scores
- final hunger modulated scores
- hunger reliability / modulation factors
- optional delta row set `final - raw`

### 5.3.8 `Curiosity-side Predictive Modulation`

Must show:

- raw curiosity scores
- final curiosity modulated scores
- curiosity reliability / modulation factors
- novelty weight used in curiosity-side prediction
- optional delta row set `final - raw`

### 5.3.9 `Decision Pipeline`

Must show:

- final combined scores
- policy probabilities if available
- selected action
- counterfactual combined scores without prediction
- counterfactual winner without prediction

Should also show, if available:

- winner without hunger-side prediction
- winner without curiosity-side prediction

### 5.3.10 `Predictive Update`

Must show:

- feature error positive
- feature error negative
- hunger actual outcome
- hunger predicted outcome
- hunger error positive
- hunger error negative
- curiosity actual outcome
- curiosity predicted outcome
- curiosity error positive
- curiosity error negative

### 5.3.11 `Drive-Specific Trace Update`

Must show:

- hunger confidence
- hunger frustration
- hunger trace balance
- curiosity confidence
- curiosity frustration
- curiosity trace balance

This section is mandatory. It is one of the defining visual features
of C+W.

### 5.3.12 `Outcome`

Must show:

- action cost
- energy gain
- terminated?
- termination reason

If buffer-related values are helpful and already available, they may be
included here or in the world-context section.

---

## 6. Overlay Specification

System C+W overlays must be selective. The viewer should not simply
inherit everything from A+W and C conceptually without curation.

## 6.1 Required overlay types

The adapter should provide at least these overlay types:

1. `action_preference`
2. `visit_count_heatmap`
3. `novelty_field`
4. `modulation_factor`
5. `dual_modulation_split`

## 6.2 Overlay meanings

### 6.2.1 `action_preference`

Purpose:

- fast view of what action is behaviorally favored

### 6.2.2 `visit_count_heatmap`

Purpose:

- makes the world-model revisit structure visible

### 6.2.3 `novelty_field`

Purpose:

- visualizes curiosity-relevant directional novelty

### 6.2.4 `modulation_factor`

Purpose:

- visualizes signed predictive reinforcement / suppression

### 6.2.5 `dual_modulation_split`

Purpose:

- shows hunger-side and curiosity-side predictive modulation
  simultaneously

This is the primary new C+W-specific overlay.

Preferred semantics:

- each directional target indicates both predictive channels
- disagreement between the channels should be visually noticeable

Possible rendering families:

- split cell tint
- paired micro-bars
- dual directional glyphs

Exact rendering can be chosen in engineering as long as the two
channels remain clearly separable.

---

## 7. Right Top Specification: Zoomed Agent Cell

The zoomed agent-cell widget must be treated as a first-class C+W
surface.

## 7.1 General rule

Any overlay declared important for System C+W should remain meaningful
when the agent cell is enlarged in the detail panel.

That means the overlay design must be evaluated not only on the main
grid, but also in the one-cell zoom context.

## 7.2 Specific implications

### 7.2.1 Agent-cell overlays

Overlays that render on the agent cell itself should be chosen so they
scale well in the zoom widget:

- trace-state indicators
- local modulation summary
- current-cell curiosity / consume context markers

### 7.2.2 Neighbor-directed overlays

Because the zoom widget only shows the current cell, purely
neighbor-positioned overlays may become invisible there.

Therefore, if directional information is crucial, the design should
also include an agent-cell-local summary form, such as:

- inward-facing directional glyphs anchored to the current cell
- miniature directional bars centered on the cell
- ring segments or quadrant indicators

This is particularly important for:

- novelty field
- modulation factor
- dual modulation split

## 7.3 Requirement

The engineering implementation must explicitly verify that the chosen
C+W overlays remain interpretable in both:

- the full grid canvas
- the zoomed agent-cell view

---

## 8. Right Bottom Specification: System-Specific Widget

The current viewer already supports system-specific widget data through
`build_system_widget_data()`.

System C+W must provide meaningful structured data here.

## 8.1 Required design goal

The right-side system widget should present a compact, high-signal
summary of the predictive and trace state without requiring the user to
read the full left-panel text.

## 8.2 Required contents

The widget data should support at least:

- shared context display
- predictive feature summary
- hunger-side modulation summary
- curiosity-side modulation summary
- hunger confidence / frustration summary
- curiosity confidence / frustration summary
- current prediction-error summary

## 8.3 Preferred visual organization

The widget should be conceptually divided into three mini-blocks:

1. `Shared Predictive State`
   context and feature summary

2. `Dual Modulation State`
   hunger-side and curiosity-side modulation summaries

3. `Dual Trace State`
   hunger and curiosity confidence / frustration summaries

## 8.4 Widget implementation direction

Two viable implementation directions are acceptable:

### Option A: extend the existing generic prediction widget

This is preferred if the widget can be generalized cleanly without
embedding System C+W-specific assumptions into the framework.

In that case:

- the widget becomes a more generic predictive summary surface
- `system_c` and `system_cw` can both feed it different structured data

### Option B: introduce a new generic framework widget hook

This is acceptable only if the current `PredictionSummaryWidget`
cannot represent C+W cleanly.

In that case:

- the framework change must remain generic
- the new UI element must not be hard-wired to System C+W by name
- `system_cw` still provides only structured data, not direct widget
  dependencies on other systems

## 8.5 Non-goal

`system_cw` must not depend on widget code inside `system_c` or any
other system package.

---

## 9. Interaction With Existing Viewer Architecture

## 9.1 What can remain unchanged

The following should remain unchanged if possible:

- phase navigation model
- replay loading model
- adapter registration model
- general overlay toggle model
- generic left-panel rendering model

## 9.2 What may need modest generic extension

The following may need generic viewer-level improvement:

- richer right-side system widget data interpretation
- a new overlay item pattern if `dual_modulation_split` cannot be
  expressed well using existing overlay primitives

If either change is needed, it must be implemented as a generic viewer
capability, not as an ad hoc system-specific shortcut.

---

## 10. Minimal Deliverable vs Target Deliverable

## 10.1 Minimal acceptable upgrade

The minimum acceptable C+W visualization upgrade must include:

- the full improved left-panel section structure
- meaningful right-side system widget data
- at least one truly C+W-specific overlay

Without these three, the visualization should still be considered
incomplete.

## 10.2 Recommended target deliverable

The recommended first serious implementation should include:

- all twelve left-panel sections
- a richer right-side predictive / trace widget
- action preference overlay
- visit count heatmap
- novelty field
- modulation factor
- dual modulation split

---

## 11. Acceptance Criteria

The visualization implementation should be considered successful if it
allows a reviewer to inspect a single step and answer:

1. whether hunger or curiosity dominated before prediction
2. how shared prediction affected each drive separately
3. whether prediction altered the effective action winner
4. what the post-action evidence was
5. how the hunger and curiosity trace states diverged

Additionally:

- the left panel must be noticeably more readable than the current
  minimal C+W output
- the right-side system widget must provide nontrivial C+W-specific
  value
- the zoomed agent-cell view must remain useful with the chosen
  overlays

---

## 12. Recommended Next Step

The next engineering-oriented artifact should define:

- the exact adapter sections and row builders
- the exact structured payload for `build_system_widget_data()`
- whether the existing prediction summary widget is extended or a new
  generic hook is introduced
- whether a new overlay primitive is required for
  `dual_modulation_split`
- the implementation sequence and tests
