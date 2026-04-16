# System C -- Implementation Roadmap

**Based on:** `system-c-engineering-spec.md`  
**Date:** 2026-04-15

---

## Overview

The implementation follows a strict bottom-up order: Construction Kit
components first, then System C composition, then integration. Each work
package (WP) produces tested, independently mergeable code.

---

## Dependency Graph

```
WP1  WP2  WP3        (Kit: independent, can run in parallel)
 \    |    /
  \   |   /
    WP4              (Kit: depends on WP1+WP2+WP3)
     |
    WP5              (System C: core, depends on WP4)
     |
    WP6              (System C: transition, depends on WP5)
     |
    WP7              (Integration: config + registration + episode test)
     |
    WP8              (Polish: visualization + documentation)
```

---

## Work Packages

### WP1 -- Prediction Package

Fill `construction_kit/prediction/` (currently an empty Phase 2 placeholder).

Modules: `features.py`, `context.py`, `memory.py`, `error.py`, `__init__.py`

Delivers: predictive feature extraction, binary context encoding, predictive
memory state + CRUD, signed prediction error with scalar aggregation.

Tests: ~15-20 unit tests.

No dependencies on other new work packages.

---

### WP2 -- Traces Package

Fill `construction_kit/traces/` (currently an empty Phase 2 placeholder).

Modules: `state.py`, `update.py`, `__init__.py`

Delivers: dual-trace state model (frustration + confidence), EMA update
function, accessor functions.

Tests: ~10-12 unit tests.

No dependencies on other new work packages.

---

### WP3 -- Modulation Package

Fill `construction_kit/modulation/` (currently an empty Phase 2 placeholder).

Modules: `modulation.py`, `__init__.py`

Delivers: single-pair modulation factor (`compute_modulation`), batch
modulation across all actions (`modulate_action_scores`).

Tests: ~8-10 unit tests.

Depends on `TraceState` type from WP2 for the batch function signature, but
the core `compute_modulation` function is self-contained. Can be developed
in parallel with WP2 if the type import is stubbed or if WP2 lands first.

---

### WP4 -- Kit Integration Verification

Verify that WP1 + WP2 + WP3 compose correctly end-to-end.

No new modules -- this is a test-only work package.

Delivers: one integration test that runs the full predictive cycle on
synthetic data: features -> context -> predict -> error -> update traces ->
update memory -> modulate scores. Validates the complete kit pipeline before
building the system on top.

Tests: ~3-5 integration tests.

Depends on WP1, WP2, WP3.

---

### WP5 -- System C Core

Create `systems/system_c/` with config, types, and the system class.

Modules: `config.py`, `types.py`, `system.py`, `__init__.py`

Delivers: `PredictionConfig`, `SystemCConfig`, `AgentStateC`, `SystemC`
class with the full `decide()` pipeline (sensor -> drive -> modulate ->
policy). Registration factory. All `SystemInterface` methods except
`transition()` (delegated to WP6).

Tests: ~10-12 unit tests (config validation, state model, decide pipeline,
interface compliance, registration).

Depends on WP4 (all kit components available).

---

### WP6 -- System C Transition

Implement the transition function with the predictive update cycle.

Modules: `transition.py`

Delivers: `SystemCTransition` with phases 4-8 (energy -> buffer ->
predictive update -> build state -> termination). Handles the
`last_observation` lifecycle (skip at t=0, store for next step).

Tests: ~10-15 unit tests (energy update, buffer update, predictive cycle,
first-step skip, reduction to System A when prediction off).

Depends on WP5 (agent state type, config).

---

### WP7 -- Integration and Registration

Wire System C into the framework and validate end-to-end.

Delivers:
- Plugin entry point in `pyproject.toml` / `setup.cfg`
- Experiment config `experiments/configs/system-c-baseline.yaml`
- Reduction test: System C == System A when $\lambda_+ = \lambda_- = 0$
- Full episode integration test (200 steps, no crashes, traces accumulate)

Tests: ~5-8 integration tests.

Depends on WP6.

---

### WP8 -- Visualization and Documentation

Non-blocking polish work.

Delivers:
- `visualization.py` -- System C visualization adapter surfacing
  prediction-specific trace data
- README and docs updates (construction kit docs for the 3 new packages,
  system overview mentions, design doc if desired)

Tests: visualization adapter unit tests.

Depends on WP7.

---

## Suggested Execution Order

| Phase | Work packages | Can parallelize? |
|---|---|---|
| 1 | WP1, WP2, WP3 | Yes -- all three are independent |
| 2 | WP4 | No -- needs all of Phase 1 |
| 3 | WP5 | No -- needs WP4 |
| 4 | WP6 | No -- needs WP5 |
| 5 | WP7 | No -- needs WP6 |
| 6 | WP8 | No -- needs WP7, but non-blocking for functionality |

Phases 1-4 are the kit layer. Phases 5-7 are the system layer.

If working sequentially (one WP at a time), the natural order is:
**WP1 -> WP2 -> WP3 -> WP4 -> WP5 -> WP6 -> WP7 -> WP8**

---

## Milestone Gates

| After WP | Gate |
|---|---|
| WP3 | All three kit packages have passing unit tests. Existing tests still green. |
| WP4 | Kit pipeline composes end-to-end on synthetic data. |
| WP6 | `SystemC` passes `SystemInterface` protocol check. Reduction test passes. |
| WP7 | Full episode runs without error. System C is usable from CLI. |
| WP8 | Documentation complete. Ready for release. |
