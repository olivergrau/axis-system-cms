# Work Packages: Series Measurement Visualizations

This document turns the idea spec and engineering spec into an actionable
implementation plan.

Related documents:

- [spec.md](spec.md)
- [engineering-spec.md](engineering-spec.md)

## Goal

Implement a reusable measurement-plotting layer for workspace experiment series
that:

- renders generic plots from existing structured artifacts
- supports system-specific plot extensions
- fits the current AXIS framework / SDK architecture
- remains additive and best-effort

---

## Delivery Strategy

Implementation should proceed in four staged work packages:

1. **WP-01: Generic rendering foundation**
2. **WP-02: Standalone workspace command and service**
3. **WP-03: Plot extension architecture**
4. **WP-04: Initial system-specific plot implementations**

Optional later:

5. **WP-05: `run-series` end-of-workflow integration**
6. **WP-06: Lifespan-vs-horizon plot family**

The order matters. Generic plotting and standalone rendering should exist before
system-specific extensions are added, and workflow integration should come last.
The lifespan-vs-horizon block should follow once the generic renderer is
stable, because it reuses the same comparison artifacts but sharpens the
interpretation of survival.

---

## WP-01: Generic Rendering Foundation

### Objective

Create the framework-side plotting infrastructure and implement the generic
series-level and per-experiment plots described in the engineering spec.

### Scope

Add:

- framework plotting helpers
- generic rendering module
- plot file layout
- deterministic output naming
- optional plots manifest

### Planned modules

- `src/axis/framework/workspaces/plotting.py`
- `src/axis/framework/workspaces/series_plot_rendering.py`

### Inputs

- `series-summary.json`
- `comparison-XXX.json`
- current aggregate entry model from `series_reporting.py`

### Outputs

Under:

- `series/<series-id>/measurements/plots/`
- `series/<series-id>/measurements/experiment_<n>/plots/`

### Generic plots to implement

#### Series-level

- `survival-rates.png`
- `paired-survival-counts.png`
- `trajectory-vs-survival.png`
- `efficiency-vs-survival.png`
- `series-progression.png`

#### Per-experiment

- `paired-steps-delta-hist.png`
- `paired-final-vitality-delta-hist.png`
- `episode-outcomes-strip.png`
- `mismatch-vs-outcome.png`
- `trajectory-distance-distribution.png`

### Acceptance criteria

- Plot generation works from structured artifacts only
- No text-log parsing is required
- Output directories are created deterministically
- Re-running the renderer overwrites plot outputs deterministically
- Failures are isolated per plot and do not crash the whole rendering pass

### Risks

- matplotlib layout instability
- edge cases for tiny series (1 experiment, missing comparisons)
- inconsistent labeling across `single_system` and `system_comparison`

### Tests

- unit tests for plotting helpers
- rendering tests against synthetic aggregate inputs
- integration tests against small temporary workspace series fixtures

---

## WP-02: Standalone Workspace Command And Service

### Objective

Expose plot rendering as a first-class, re-runnable workspace operation.

### Scope

Add:

- new workspace plot-rendering service
- new CLI command
- result summary object

### Planned modules

- `src/axis/framework/workspaces/services/series_plot_service.py`
- `src/axis/framework/cli/commands/...` integration for
  `axis workspaces render-series-plots`

### Command shape

Proposed:

```bash
axis workspaces render-series-plots <workspace> --series <series-id>
```

### Responsibilities

- resolve workspace + series paths
- load required structured artifacts
- call generic renderer
- return summary of generated, skipped, and failed plots

### Acceptance criteria

- command works without re-running experiments
- command can regenerate plots for an already completed series
- command does not mutate results/comparisons, only plot outputs
- command exits successfully even if some plots fail, while reporting failures

### Risks

- series path resolution mismatch
- partial series state
- stale or manually edited artifacts

### Tests

- CLI parser tests
- service tests with temporary workspace fixtures
- integration test for a minimal completed series

---

## WP-03: Plot Extension Architecture

### Objective

Add a new extension family for system-specific measurement plots, following the
existing AXIS registry/catalog pattern.

### Scope

Add:

- SDK protocol for measurement plot extensions
- framework registry
- catalog integration
- renderer-side extension dispatch

### Planned modules

- `src/axis/sdk/measurement_plots.py`
- `src/axis/framework/workspaces/plot_extensions.py`
- updates to `src/axis/framework/catalogs.py`

### Design rules

- must mirror the current extension style used by metrics/comparison
- must support both:
  - global registry lookup
  - injected catalog lookup
- must be series-aware
- must dispatch by candidate system type

### Acceptance criteria

- systems can register a plot extension without changing the generic renderer
- plugin discovery is sufficient for registration side effects
- extension rendering is isolated from generic rendering failures
- no existing registry/cataloĝ behavior is broken

### Risks

- over-coupling SDK types to framework internals
- passing overly rich framework dataclasses into SDK protocol boundaries
- extension result format becoming too ad hoc

### Tests

- registry tests
- catalog injection tests
- renderer dispatch tests
- failure isolation tests

---

## WP-04: Initial System-Specific Plot Implementations

### Objective

Implement the first system-specific plot extensions using the new architecture.

### Priority order

1. `system_cw`
2. `system_aw`
3. `system_c`

`system_a` does not need a dedicated v1 extension.

### 4.1 `system_cw`

#### Objective

Provide the first full reference implementation for measurement plot extensions.

#### Planned module

- `src/axis/systems/system_cw/measurement_plots.py`

#### Planned plots

- `prediction-impact-vs-survival.png`
- `modulation-strength-vs-performance.png`
- `prediction-error-profile.png`
- `curiosity-hunger-weight-plane.png`
- `cw-trace-balance-profile.png`
- `cw-comparison-deltas.png`

#### Acceptance criteria

- plots are generated from current `system_cw` metrics/comparison payloads
- no custom trace parsing is needed
- plots help answer whether prediction is:
  - active
  - behaviorally influential
  - performance-relevant

### 4.2 `system_aw`

#### Planned module

- `src/axis/systems/system_aw/measurement_plots.py`

#### Planned plots

- `aw-curiosity-profile.png`
- `aw-arbitration-balance.png`
- `aw-world-model-profile.png`

### 4.3 `system_c`

#### Planned module

- `src/axis/systems/system_c/measurement_plots.py`

#### Planned plots

- `c-prediction-error-profile.png`
- `c-trace-balance.png`
- `c-comparison-impact.png`

### Acceptance criteria

- each extension is optional
- generic rendering still works if a system extension is absent
- extension outputs land in the same plot tree with deterministic names

### Risks

- metrics insufficient for some proposed plots
- too much implementation drift between systems
- weak consistency in styling and naming

### Tests

- unit tests per extension
- one integration test per system where feasible

---

## WP-05: Optional `run-series` Integration

### Objective

Make plot generation available automatically at the end of `run-series`, while
keeping standalone rendering the primary mechanism.

### Scope

Add an optional final step inside:

- `WorkspaceExperimentSeriesService.run_series(...)`

Behavior:

- after aggregate artifacts are written, invoke the plot service
- rendering remains best-effort
- rendering failures are reported but do not fail the series run

### Acceptance criteria

- automatic rendering uses exactly the same rendering service as the standalone
  command
- no duplicate implementation path exists
- completed series without plots can still be rendered later manually

### Risks

- workflow output becoming noisy
- longer end-of-series latency
- confusion about whether rendering is mandatory

### Tests

- integration test that `run-series` produces plots when the feature is enabled
- failure-isolation test showing that a rendering error does not invalidate the
  completed series

---

## WP-06: Lifespan-vs-Horizon Plot Family

### Objective

Add a dedicated generic plot family that makes **horizon-reaching survival**
and **sub-horizon lifespan robustness** visible as separate analytical signals.

### Motivation

Current plots already show:

- survival rate
- paired longer/equal counts
- per-experiment step deltas

But they do not yet provide a strong, explicit view of cases where:

- neither system reaches the horizon
- yet one system consistently lives longer

For many AXIS questions, especially around prediction, arbitration, and local
robustness, this is an important outcome class rather than a footnote.

### Scope

Add the following generic plots:

#### Series-level

- `horizon-vs-lifespan-delta.png`
- `sub-horizon-advantage.png`

#### Per-experiment or experiment-indexed overview

- `paired-outcome-categories.png`
- `steps-lived-distribution.png`

### Planned modules

Primarily:

- `src/axis/framework/workspaces/series_plot_rendering.py`

Possibly small helper additions in:

- `src/axis/framework/workspaces/plotting.py`

### Required data

These plots should be derived from existing structured comparison artifacts,
especially:

- paired per-episode `reference_total_steps`
- paired per-episode `candidate_total_steps`
- comparison-summary survival rates
- configured horizon from the paired run config

No log parsing should be introduced.

### Plot semantics

#### `paired-outcome-categories.png`

Show, per experiment:

- both reached horizon
- candidate/current reached, reference/baseline not
- reference/baseline reached, candidate/current not
- both died, candidate/current longer
- both died, reference/baseline longer
- both died equal

This plot should make it immediately obvious whether a system is winning by
crossing the horizon or merely by lasting longer below it.

#### `steps-lived-distribution.png`

Show actual steps-lived distributions for the two paired sides, so that
late-failing but non-surviving behavior remains visible.

Preferred forms:

- box plot
- violin plot

#### `horizon-vs-lifespan-delta.png`

Show:

- x = survival-rate delta
- y = mean total-steps-lived delta

This should make it easy to spot experiments that:

- do not improve horizon success
- but still improve lifespan robustness

#### `sub-horizon-advantage.png`

Restrict to episode pairs where both sides die before the horizon and show:

- candidate/current longer
- reference/baseline longer
- equal
- optionally mean or median sub-horizon total-steps delta

### Acceptance criteria

- The plots clearly distinguish survival success from lifespan robustness
- The plots work for both:
  - `system_comparison`
  - `single_system`
- The plots use only structured AXIS comparison artifacts
- The plots are understandable without reading comparison logs first

### Risks

- category definitions becoming opaque if not labeled carefully
- cluttered visuals for experiments with many outcome classes
- confusion between absolute steps lived and step delta if both are shown

### Tests

- synthetic rendering tests for each category combination
- integration tests for:
  - `system_comparison`
  - `single_system`
- at least one test ensuring a “both died, candidate longer” case is rendered
  distinctly from a horizon-reaching win

---

## Cross-Cutting Requirements

These apply to all work packages.

### 1. Do not break existing framework / SDK layering

- SDK defines protocol-level types
- framework owns orchestration and registries
- systems own system-specific implementations

### 2. Do not parse display logs

Use structured artifacts only:

- JSON aggregates
- comparison JSON
- behavior metrics JSON

### 3. Keep rendering additive

No changes to:

- trace semantics
- run persistence
- comparison semantics
- visualizer runtime

### 4. Prefer deterministic filenames

Names should be stable so that:

- docs can link to them
- notebooks can rely on them
- reruns replace them cleanly

### 5. Keep failures local

One broken plot should not invalidate:

- other plots
- the rendering pass
- the completed series

---

## Recommended Execution Order

If we implement this now, the recommended order is:

1. WP-01
2. WP-02
3. WP-03
4. WP-04 (`system_cw` first)
5. WP-04 (`system_aw`, `system_c`)
6. WP-06
7. WP-05

This gives us:

- useful plots early
- a clean architecture before system-specific code lands
- a standalone tool before workflow automation

---

## Suggested Milestone Boundaries

### Milestone A

- WP-01 + WP-02

Result:

- generic plots can be rendered on demand for completed series

### Milestone B

- WP-03 + `system_cw` part of WP-04

Result:

- first full extension-backed system-specific plots

### Milestone C

- remaining `system_aw` / `system_c` plots
- WP-06
- optional WP-05

Result:

- complete first-generation plot pipeline for current systems, including
  lifespan-aware comparison visuals

---

## Definition Of Done

This initiative is done when:

- generic plots can be rendered from completed series artifacts
- system-specific plot extensions are supported through the framework
- `system_cw` has a full first-class implementation
- documentation exists for the new command and artifact layout
- optional integration with `run-series` is either implemented or explicitly
  deferred with no architectural blockers remaining
