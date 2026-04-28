# System C+W Visualization Draft

## Purpose

This draft proposes a first substantial visualization design for
`system_cw`.

The goal is not to invent a new viewer paradigm, but to extend the
existing AXIS visualization model so that System C+W becomes
interpretable along its two defining axes:

- A+W-like dual-drive arbitration with curiosity and world-model context
- C-like predictive modulation with drive-specific traces and errors

System C+W should therefore feel like a synthesis of the current
`system_aw` and `system_c` visualizations, not like a third unrelated
style.

---

## Current Situation

### Existing System A+W strengths

`system_aw` already visualizes the parts that matter for the
exploration / arbitration side:

- observation
- observation buffer
- hunger drive
- curiosity drive
- drive arbitration
- world model / visit counts
- novelty field overlays
- visit-count heatmap

This makes it good at answering:

- why curiosity was active
- how arbitration weighted hunger vs curiosity
- whether the agent was revisiting or exploring

### Existing System C strengths

`system_c` already visualizes the parts that matter for the predictive
side:

- context encoding
- predictive features
- raw vs modulated action scores
- prediction update / error
- modulation-factor overlays
- neighbor modulation view

This makes it good at answering:

- whether prediction was active
- how prediction changed action competition
- how prediction was reinforced or suppressed

### Current System C+W state

The current `system_cw` adapter is intentionally minimal:

- a few basic analysis sections
- no meaningful overlays
- no explicit rendering of the dual predictive channels
- no explicit rendering of shared memory vs separate traces

So the current adapter is structurally valid, but not yet adequate for
serious analysis.

---

## Design Principle

System C+W should visualize three layers explicitly:

1. `raw dual-drive layer`
   Hunger drive, curiosity drive, arbitration, world-model and novelty
   context before predictive interpretation.

2. `predictive modulation layer`
   Shared predictive features and context, plus separate hunger-side and
   curiosity-side predictive modulation.

3. `learning-update layer`
   Post-action evidence, separate outcome errors, and separate
   confidence/frustration trace updates.

This should preserve the conceptual order already fixed in the spec:

`raw drives -> predictive modulation -> arbitration-resolved behavior -> predictive update`

Even though arbitration happens before final policy choice, the viewer
should make the above progression legible rather than scattering the
relevant numbers across unrelated sections.

---

## Proposed Analysis Panel

## 1. Step Overview

Keep a compact top-level overview similar to `system_aw` and `system_c`:

- timestep
- chosen action
- energy before / after / delta
- relative position
- visit count at current cell
- encoded context id

Purpose:

- anchors the rest of the step interpretation

## 2. Observation

Reuse the general local observation presentation:

- current resource
- up/down/left/right resource
- traversability state per direction

Purpose:

- keeps the raw sensory basis visible
- helps interpret both hunger and curiosity drive outputs

## 3. Curiosity and World Context

This section should be closer to `system_aw` than to `system_c`.

Show:

- spatial novelty per direction
- sensory novelty per direction
- composite novelty per direction
- optional mean novelty summary
- world-model relative position
- visit count at current cell

Purpose:

- makes the non-predictive curiosity substrate explicit
- shows what the curiosity drive had available before predictive
  modulation

## 4. Raw Drive Outputs

Separate the raw drive layer clearly before any predictive influence.

Show:

- hunger activation
- curiosity activation
- raw hunger action contributions
- raw curiosity action contributions

This should not yet show final modulated scores.

Purpose:

- reveals whether a behavior came from raw appetite / exploration
  pressure or from predictive reinterpretation later

## 5. Arbitration

This section should remain close to `system_aw`.

Show:

- hunger arbitration weight
- curiosity arbitration weight
- weighted hunger pressure
- weighted curiosity pressure

If available, optionally show:

- selected-action rank before predictive modulation
- selected-action rank after predictive modulation

Purpose:

- keeps the motivational weighting explicit
- prevents the predictive layer from visually obscuring the role of
  arbitration

## 6. Shared Predictive Representation

This is the first C-like predictive section.

Show:

- encoded context
- predictive feature vector
- note that the feature vector mixes:
  - resource-valued exogenous features
  - novelty-derived endogenous features

If the vector is too long, render:

- compact full vector string
- plus named summaries where possible

Purpose:

- makes the shared predictive substrate explicit
- emphasizes that both drives read from the same predictive memory basis

## 7. Hunger-side Predictive Modulation

Dedicated section for the hunger channel.

Show:

- hunger raw scores
- hunger final modulated scores
- hunger reliability / modulation factors
- optional per-action delta `final - raw`

Purpose:

- isolates the hunger-side predictive reinterpretation
- allows the user to see where prediction reinforced or suppressed
  metabolic behavior

## 8. Curiosity-side Predictive Modulation

Dedicated section for the curiosity channel.

Show:

- curiosity raw scores
- curiosity final modulated scores
- curiosity reliability / modulation factors
- novelty weight used for curiosity-side yield
- optional per-action delta `final - raw`

Purpose:

- isolates the curiosity-side predictive reinterpretation
- makes the asymmetry with the hunger channel visible

## 9. Decision Pipeline

This should be the synthesis section.

Show:

- combined final scores
- policy probabilities if available
- chosen action
- counterfactual combined scores without prediction
- counterfactual top action without prediction
- optionally:
  - without hunger prediction
  - without curiosity prediction

Purpose:

- shows whether prediction merely perturbed scores or actually changed
  behavioral competition
- directly supports later interpretation of
  `behavioral_prediction_impact_rate`

## 10. Predictive Update

This is the post-action learning section.

Show:

- feature prediction error positive / negative
- hunger actual vs predicted outcome
- curiosity actual vs predicted outcome
- hunger error positive / negative
- curiosity error positive / negative

Purpose:

- makes visible what was learned from this step
- links back to the shared predictive representation

## 11. Drive-Specific Trace Update

This section is crucial and currently underrepresented.

Show:

- hunger confidence
- hunger frustration
- hunger trace balance
- curiosity confidence
- curiosity frustration
- curiosity trace balance

Purpose:

- makes the architectural core of C+W legible:
  shared predictive memory, but separate trust dynamics

## 12. Outcome

Retain the usual terminal / transition summary:

- terminated?
- termination reason
- action cost
- energy gain
- buffer growth if relevant

Purpose:

- provides closure for the step

---

## Proposed Overlay Strategy

System C+W should not simply merge all overlays from A+W and C without
selection. That would likely overload the grid.

The better approach is:

- preserve a compact core set always available
- add a few C+W-specific overlays that answer genuinely new questions

## Core overlays to keep from A+W

### 1. Action Preference

Keep the action-preference overlay.

Reason:

- still the best fast visual answer to "what was the agent about to do?"

### 2. Visit Count Heatmap

Keep the world-model heatmap.

Reason:

- necessary to interpret curiosity and novelty in spatial context

### 3. Novelty Field

Keep a directional novelty overlay.

Reason:

- still highly informative for the curiosity side

## Core overlays to keep from C

### 4. Modulation Factor

Keep a modulation-factor overlay.

Reason:

- remains the fastest visual cue for predictive reinforcement vs
  suppression

### 5. Neighbor Modulation

Keep some localized directional modulation view.

Reason:

- useful for movement interpretation in the immediate neighborhood

---

## New C+W-specific overlays

## 6. Dual Modulation Split

Per directional cell, show a split rendering of:

- hunger-side modulation state
- curiosity-side modulation state

Possible rendering:

- left half / right half cell tint
- or stacked micro-bars inside the direction cell

Interpretation:

- allows the viewer to see whether both predictive channels agree
  or diverge

This is likely the single most important new C+W overlay.

## 7. Arbitration vs Prediction Tension

Overlay the current cell or directional neighbors with a marker when:

- raw arbitration would favor one tendency
- but predictive modulation pushes the effective competition elsewhere

This should be conservative, not noisy.

Interpretation:

- helps answer when prediction actually mattered behaviorally
- visually corresponds to prediction-impact metrics

## 8. Trace Balance Indicator

Show a compact centered marker at the agent position representing:

- hunger trace balance
- curiosity trace balance

Possible rendering:

- two concentric rings
- or two small orthogonal bars

Interpretation:

- shows current internal trust state without having to read the panel

This is useful, but lower priority than the dual modulation overlay.

---

## Recommended First Implementation Scope

For a first serious `system_cw` visualization implementation, I would
not try to deliver every possible section and overlay at once.

Recommended v1 scope:

### Analysis sections

Implement these first:

- Step Overview
- Observation
- Curiosity and World Context
- Raw Drive Outputs
- Arbitration
- Shared Predictive Representation
- Hunger-side Predictive Modulation
- Curiosity-side Predictive Modulation
- Decision Pipeline
- Predictive Update
- Drive-Specific Trace Update
- Outcome

### Overlay types

Implement these first:

- Action Preference
- Visit Count Heatmap
- Novelty Field
- Modulation Factor
- Dual Modulation Split

This would already make System C+W much more interpretable without
overloading the UI.

---

## Prioritization Rationale

If implementation time is limited, the most important viewer questions
for C+W are:

1. What did hunger want?
2. What did curiosity want?
3. How did arbitration weight them?
4. How did shared prediction modulate each side separately?
5. Did prediction change the behavioral winner?
6. How were the two drive-specific traces updated?

Any visualization element that does not help answer one of these
questions should be treated as secondary.

---

## Interaction With Existing Viewer Architecture

This proposal fits the current viewer model well:

- phase model remains `BEFORE`, `AFTER_REGEN`, `AFTER_ACTION`
- no viewer architecture changes are required
- all system-specific logic can stay inside the `system_cw`
  visualization adapter
- existing overlay item types likely cover most of the required visuals

The one area that may need modest extension is the `Dual Modulation
Split` overlay, depending on whether current overlay primitives are
sufficiently expressive. That should be decided in the engineering-spec
for visualization.

---

## Recommended Next Document

If this direction looks right, the next artifact should be:

- `spec-visualization.md`

That document should define:

- the exact section list and their row contents
- the exact overlay set and rendering semantics
- which existing A+W and C helper logic can be reused conceptually
- any missing overlay primitive needed by the viewer
- a phased implementation plan for the adapter
