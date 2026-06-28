# Engineering Spec: Series Measurement Visualizations

## Status

Draft engineering spec

## Scope

This engineering spec covers the first implementation of measurement plot
generation for workspace experiment series.

It includes:

1. generic series-level plot rendering
2. generic per-experiment comparison plot rendering
3. a new extension mechanism for system-specific measurement plots
4. a standalone rendering command
5. optional later integration into `run-series`

It does **not** implement:

- interactive dashboards
- notebook integration
- custom report templating
- per-step visualization logic (already covered by the replay visualizer)

---

## 1. Verified Current Architecture

This spec is intentionally grounded in the current AXIS codebase.

### 1.1 Current series workflow

Verified in:

- [src/axis/framework/workspaces/services/experiment_series_service.py](/workspaces/axis-system-cms/src/axis/framework/workspaces/services/experiment_series_service.py)
- [src/axis/framework/workspaces/series_reporting.py](/workspaces/axis-system-cms/src/axis/framework/workspaces/series_reporting.py)

Current `run-series` flow:

1. execute experiment runs into `series/<id>/results/`
2. create comparison outputs into `series/<id>/comparisons/`
3. export per-experiment measurement logs into
   `series/<id>/measurements/experiment_N/`
4. compute behavior metrics via existing metrics extension system
5. render aggregate series artifacts:
   - `series-summary.md`
   - `series-summary.json`
   - `series-metrics.csv`
   - `series-manifest.json`

This means the series workflow already has a clear reporting phase, which is the
natural home for plot generation.

### 1.2 Current extension model

Verified in:

- [src/axis/framework/metrics/extensions.py](/workspaces/axis-system-cms/src/axis/framework/metrics/extensions.py)
- [src/axis/framework/comparison/extensions.py](/workspaces/axis-system-cms/src/axis/framework/comparison/extensions.py)
- [src/axis/framework/catalogs.py](/workspaces/axis-system-cms/src/axis/framework/catalogs.py)

Current pattern:

- global registry module
- optional injectable catalog
- plugin discovery imports modules that self-register

This is already used for:

- metrics extensions
- comparison extensions
- visualization adapters

This spec follows the same pattern instead of inventing a parallel mechanism.

### 1.3 Current plugin discovery

Verified in:

- [src/axis/plugins.py](/workspaces/axis-system-cms/src/axis/plugins.py)

Current behavior:

- plugin discovery imports modules so that registration side effects occur
- worker processes already call `discover_plugins()` where needed

This makes a new plot-extension registry compatible with the current plugin
system.

### 1.4 Current data sources

Verified in:

- [src/axis/framework/workspaces/series_reporting.py](/workspaces/axis-system-cms/src/axis/framework/workspaces/series_reporting.py)
- [src/axis/framework/comparison/types.py](/workspaces/axis-system-cms/src/axis/framework/comparison/types.py)
- [src/axis/framework/metrics/types.py](/workspaces/axis-system-cms/src/axis/framework/metrics/types.py)

Structured sources already available:

- aggregate series entries via `ExperimentSeriesAggregateEntry`
- `series-summary.json`
- per-experiment `comparison-XXX.json`
- per-run `behavior_metrics.json`

The first implementation should consume these structured artifacts rather than
text logs.

---

## 2. Architectural Goal

Add measurement plotting as a **reporting-layer extension** of the current
workspace series workflow, without changing:

- experiment execution semantics
- trace semantics
- comparison semantics
- replay visualizer contracts

Plot generation should be:

- additive
- best-effort
- re-runnable
- decoupled from execution correctness

---

## 3. High-Level Design

## 3.1 Two-layer model

The system should have:

1. **Standalone plot rendering service**
   Reads existing series artifacts and produces plot files.

2. **Optional workflow integration**
   `run-series` may call the same rendering service at the end.

This avoids coupling plot generation too tightly to execution.

## 3.2 Three rendering levels

The rendering system should support:

1. generic series-level plots
2. generic per-experiment comparison plots
3. system-specific plot extensions

## 3.3 Data ownership

### Framework owns:

- generic plot selection
- aggregate loading
- output layout
- rendering orchestration
- extension dispatch

### Systems own:

- mechanism-specific plot definitions
- interpretation-specific series plots based on system metrics
- any plot requiring system-specific metric namespaces

---

## 4. Proposed New Modules

## 4.1 SDK protocol

Add new protocol definitions in SDK, analogous to metrics/comparison protocols.

Proposed file:

- `src/axis/sdk/measurement_plots.py`

Purpose:

- define protocol types and lightweight typed request/result models

Reason:

- extension call signatures should live in SDK
- registry and orchestration can remain in framework

### Proposed SDK types

#### `GeneratedPlotArtifact`

Suggested fields:

- `plot_id: str`
- `level: Literal["series", "experiment"]`
- `relative_output_path: str`
- `title: str | None`
- `description: str | None`
- `system_type: str | None`

Purpose:

- describe one generated plot artifact in a stable machine-readable way

#### `SeriesPlotExtensionRequest`

Suggested fields:

- `workspace_path: Path`
- `series_id: str`
- `workspace_type: str`
- `measurement_root_dir: str`
- `entries: tuple[ExperimentSeriesAggregateEntryLike, ...]`

Note:

- the SDK should not import the framework dataclass directly
- define a lightweight protocol or plain dict-compatible access expectation

Preferred approach:

- extension request should contain only plain JSON-like structures

#### `MeasurementPlotExtensionProtocol`

Suggested signature:

```python
def __call__(
    request: SeriesPlotExtensionRequest,
) -> list[GeneratedPlotArtifact]:
    ...
```

This should be a **series-level** extension interface.

Reason:

- system-specific plots often need the whole series at once
- per-experiment plots can still be emitted by the extension if needed

## 4.2 Framework registry

Add new framework registry module:

- `src/axis/framework/workspaces/plot_extensions.py`

Pattern should mirror:

- `metrics/extensions.py`
- `comparison/extensions.py`

Proposed contents:

- `_MEASUREMENT_PLOT_EXTENSION_REGISTRY`
- `register_measurement_plot_extension(system_type: str)`
- `registered_measurement_plot_extensions()`
- `build_system_measurement_plots(...)`

## 4.3 Catalog integration

Extend:

- [src/axis/framework/catalogs.py](/workspaces/axis-system-cms/src/axis/framework/catalogs.py)

Add:

- `MeasurementPlotExtensionCatalog`
- `measurement_plot_extensions` entry in `build_catalogs_from_registries()`

This keeps the new extension family composition-friendly and consistent with the
rest of AXIS.

## 4.4 Framework rendering service

Add new module:

- `src/axis/framework/workspaces/series_plot_rendering.py`

Responsibilities:

- load aggregate series inputs
- render generic plots
- dispatch system-specific plot extensions
- write images to the correct output directories
- optionally write a manifest of generated plots

This service should be callable both from:

- CLI command
- `run-series` workflow

## 4.5 Optional plot manifest

Add a structured manifest file:

- `series/<series-id>/measurements/plots/plots-manifest.json`

Purpose:

- machine-readable record of generated images
- helpful for docs, notebooks, or future HTML reports

This is not strictly required for v1, but recommended because the framework
already treats other aggregate artifacts explicitly.

---

## 5. CLI Integration

## 5.1 New command

Add new workspace command:

- `axis workspaces render-series-plots <workspace> --series <series-id>`

Behavior:

- resolves the series
- loads existing aggregate artifacts and per-experiment comparison outputs
- renders generic plots
- invokes any applicable system-specific plot extensions
- writes outputs into the series measurement tree

### Output mode

Should support:

- text summary by default
- `--output json` later if useful

First version can remain text-only if needed.

## 5.2 `run-series` integration

Do **not** make this the only code path.

Instead:

- `run-series` may call the rendering service after `render_series_outputs(...)`
- any rendering failure should be reported but should not invalidate the series
  run itself

Implementation note:

- this should happen at the very end of `run_series(...)`, after all aggregate
  entries and summary artifacts exist

---

## 6. Generic Plot Inventory For V1

These plots should be implemented in framework code, not in system modules.

## 6.1 Series-level generic plots

Output root:

- `series/<series-id>/measurements/plots/`

### `survival-rates.png`

Data:

- `comparison_summary.candidate_survival_rate`
- `comparison_summary.reference_survival_rate`

Plot:

- grouped bar chart

### `paired-survival-counts.png`

Data:

- `candidate_longer_count`
- `reference_longer_count`
- `equal_count`

Plot:

- stacked bar chart

### `trajectory-vs-survival.png`

Data:

- `mean_trajectory_distance.mean`
- survival delta or candidate survival rate

Plot:

- scatter plot

### `efficiency-vs-survival.png`

Data:

- `behavior_metrics.standard_metrics.net_energy_efficiency.mean`
- survival delta or candidate survival rate

Plot:

- scatter plot

### `series-progression.png`

Data:

- experiment order
- death rate
- mean final vitality
- net energy efficiency
- candidate/reference survival

Plot:

- multi-line progression chart

## 6.2 Per-experiment generic plots

Output root:

- `series/<series-id>/measurements/experiment_<n>/plots/`

### `paired-steps-delta-hist.png`

Data:

- per-episode `outcome.total_steps_delta`

### `paired-final-vitality-delta-hist.png`

Data:

- per-episode `outcome.final_vitality_delta`

### `episode-outcomes-strip.png`

Data:

- per-episode `outcome.longer_survivor`

### `mismatch-vs-outcome.png`

Data:

- per-episode `metrics.action_divergence.mismatch_rate`
- paired outcome delta on y-axis

### `trajectory-distance-distribution.png`

Data:

- per-episode `metrics.position_divergence.mean_trajectory_distance`

---

## 7. System-Specific Plot Extension Strategy

The extension mechanism should be **series-aware**, not run-aware.

Reason:

- many system-specific plots need to compare multiple experiments
- the most interesting questions are usually series-level pattern questions

## 7.1 Dispatch key

Dispatch should be by **candidate system type**.

This matches the current comparison-extension convention and fits current series
usage where the varying system is usually the candidate.

## 7.2 Current system coverage

### `system_a`

Current state:

- no metrics extension
- no comparison extension

Decision:

- no system-specific plot extension in v1

### `system_aw`

Current state:

- metrics extension exists
- no comparison extension

Recommended v1 extension outputs:

- `aw-curiosity-profile.png`
- `aw-arbitration-balance.png`
- `aw-world-model-profile.png`

### `system_c`

Current state:

- metrics extension exists
- comparison extension exists

Recommended v1 extension outputs:

- `c-prediction-error-profile.png`
- `c-trace-balance.png`
- `c-comparison-impact.png`

### `system_cw`

Current state:

- metrics extension exists
- comparison extension exists
- richest system-specific artifact surface

Recommended v1 extension outputs:

- `prediction-impact-vs-survival.png`
- `modulation-strength-vs-performance.png`
- `prediction-error-profile.png`
- `curiosity-hunger-weight-plane.png`
- `cw-trace-balance-profile.png`
- `cw-comparison-deltas.png`

`system_cw` should be the first full implementation and reference design for
the extension API.

---

## 8. Data Model Constraints

## 8.1 Do not parse text logs

The renderer must not depend on:

- `*-candidate-run-summary.log`
- `*-comparison.log`

except possibly for human-facing linking.

Structured sources only:

- `series-summary.json`
- `comparison-XXX.json`
- `behavior_metrics.json` only if needed separately

## 8.2 Reuse current aggregate entry model

The generic renderer should preferably work from the same normalized aggregate
data already produced by `build_aggregate_entry(...)`.

This avoids duplicating:

- path resolution
- comparison summary extraction
- metric flattening logic

## 8.3 Per-experiment generic plots need comparison envelopes

For generic per-experiment plots, the renderer must load:

- the `comparison_output_path` referenced by each aggregate entry

That path already exists in the current series aggregate model.

---

## 9. Rendering Backend

No plotting utility exists yet in the framework reporting layer.

Recommended first choice:

- matplotlib

Reason:

- already a natural dependency in the research workflow
- stable for file-based rendering
- sufficient for PNG outputs

Implementation guidance:

- centralize style helpers in one framework module
- do not embed plot styling logic directly in service orchestration

Possible helper module:

- `src/axis/framework/workspaces/plotting.py`

This is separate from any research notebook plotting helpers.

---

## 10. Failure Model

Plot rendering must be **best-effort**.

### Required behavior

- if a generic plot fails, continue rendering remaining plots
- if a system-specific extension fails, continue generic rendering
- record failures in the returned rendering result
- do not invalidate completed experimental artifacts

### Suggested return model

Add a structured result type for rendering:

- generated plot artifacts
- skipped plots
- failed plots with error messages

This can power both:

- CLI text output
- optional JSON output later

---

## 11. Workspace-Service Integration

## 11.1 New service

Add a dedicated service, analogous to other workspace services.

Suggested file:

- `src/axis/framework/workspaces/services/series_plot_service.py`

Suggested responsibilities:

- load series manifest and series paths
- call framework renderer
- return a structured result object

This keeps plot rendering out of:

- CLI command bodies
- `experiment_series_service.py`

## 11.2 `run-series` hook

In `WorkspaceExperimentSeriesService.run_series(...)`, optional final step:

1. build series aggregate entries
2. write standard aggregate outputs
3. call plot service
4. include plot summary fields in the returned result later if desired

But this hook should be strictly additive.

---

## 12. Testing Strategy

## 12.1 Generic renderer tests

Add unit tests for:

- empty or degenerate series
- one-experiment series
- normal system-comparison series
- single-system baseline comparison series
- expected file paths and filenames

## 12.2 Extension dispatch tests

Test:

- no extension registered
- extension registered via global registry
- extension registered via injected catalog
- extension failure does not abort generic rendering

## 12.3 CLI / integration tests

Test:

- new `render-series-plots` command creates expected files
- `run-series` optional integration calls the renderer correctly
- plot outputs land in the correct directories

## 12.4 Artifact contract tests

Check:

- `plots-manifest.json` structure if implemented
- generated filenames are stable
- re-render overwrites or replaces deterministically

---

## 13. Backward Compatibility

This design does not require changing:

- experiment config schema
- trace schema
- comparison schema
- metrics schema
- visualization runtime

It only adds:

- new rendering modules
- new optional registry/catalog family
- new CLI/service entrypoints
- new generated files in measurement directories

That makes it a safe extension of the current architecture.

---

## 14. Proposed Implementation Order

### Phase 1: Generic renderer

- rendering helpers
- generic series-level plots
- generic per-experiment plots
- standalone CLI/service

### Phase 2: Extension infrastructure

- SDK protocol
- framework registry
- catalog integration
- dispatch from renderer

### Phase 3: First system-specific implementations

- `system_cw`
- then smaller `system_aw`
- then `system_c`

### Phase 4: Optional workflow integration

- end-of-`run-series` convenience rendering

---

## 15. Recommendation

Start with:

1. **generic rendering and standalone command**
2. **extension mechanism**
3. **`system_cw` first-class implementation**

This best matches the current codebase:

- the series workflow already has a strong aggregate reporting layer
- the extension pattern is already established
- `system_cw` already exposes the richest measurement surface

This approach extends AXIS cleanly rather than bending the current framework
into a notebook-style plotting system.
