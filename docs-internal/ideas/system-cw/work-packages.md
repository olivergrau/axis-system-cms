# System C+W -- Work Packages

**Spec**: `docs-internal/ideas/system-cw/spec.md`  
**Engineering spec**: `docs-internal/ideas/system-cw/engineering-spec.md`  
**Phase**: Initial implementation pass

---

## Implementation Strategy

The efficient implementation route is:

1. stabilize the minimum shared prediction surface in `construction_kit`
2. add the standalone `system_cw` config and state shell
3. implement the C+W-local predictive helpers
4. integrate the decide path
5. integrate the transition path
6. finish registration, baseline config, metrics, visualization, and hardening

This ordering preserves the core architectural rule from the engineering spec:

> `system_a`, `system_aw`, `system_c`, and `system_cw` remain independent system
> packages; shared reuse is allowed only through backward-compatible
> `construction_kit` interfaces.

---

## Work Packages

| WP | Title | Dependencies | Scope | Key change |
|---|---|---|---|---|
| WP-01 | Prediction Kit Compatibility Review and Generalization | None | Small | Make only the minimal backward-compatible `construction_kit` adjustments required for C+W |
| WP-02 | `system_cw` Config and State Model | WP-01 | Medium | Create standalone `SystemCWConfig` and `AgentStateCW` |
| WP-03 | C+W Predictive Feature, Context, and Outcome Helpers | WP-01 | Medium | Add `features.py`, `context.py`, and `outcomes.py` under `system_cw/` |
| WP-04 | Decide Pipeline Integration | WP-02, WP-03 | Medium | Implement `SystemCW.decide()` with dual predictive modulation before arbitration |
| WP-05 | Transition Pipeline Integration | WP-02, WP-03, WP-04 | Medium | Implement `SystemCWTransition` with shared predictive memory and drive-specific trace updates |
| WP-06 | Registration and Baseline Experiment Surface | WP-04, WP-05 | Small | Register `system_cw` and add runnable baseline config |
| WP-07 | Metrics and Visualization | WP-04, WP-05 | Medium | Add `system_cw` metrics and visualization surfaces |
| WP-08 | Reduction, Boundary, and Episode Hardening | WP-06, WP-07 | Medium | Prove A+W reduction, C-like regime, and cross-system independence with tests |
| WP-09 | Internal Docs and Workload Closure | WP-08 | Small | Finalize internal notes, implementation status, and follow-up deltas |

---

## Dependency Graph

```text
WP-01 (kit compatibility review/generalization)
  ├── WP-02 (config and state)
  └── WP-03 (C+W local helpers)

WP-02 + WP-03
  └── WP-04 (decide pipeline)
         └── WP-05 (transition pipeline)
                ├── WP-06 (registration and baseline config)
                └── WP-07 (metrics and visualization)

WP-06 + WP-07
  └── WP-08 (reduction, boundary, and episode hardening)
         └── WP-09 (docs and closure)
```

---

## Execution Strategy

- `WP-01` must happen first because it decides whether any prediction helpers in
  `construction_kit` need small generalization hooks for C+W.
- `WP-02` and `WP-03` can proceed in parallel once `WP-01` has defined the
  shared-kit boundary.
- `WP-04` should begin only when config/state shape and C+W-local helper
  signatures are stable.
- `WP-05` should wait for a working decide path so the transition payload can
  reuse real `decision_data` structure instead of inventing a placeholder.
- `WP-06` and `WP-07` can proceed in parallel after the runtime core works.
- `WP-08` should remain late because it depends on the full runtime, the
  baseline config, and the visualization/metrics artifact shape.
- `WP-09` should stay last so it documents the implementation that actually
  landed rather than an intermediate shape.

---

## Detailed Packages

### WP-01: Prediction Kit Compatibility Review and Generalization

**Goal:** Determine and implement the minimum `construction_kit` changes needed
for C+W without coupling system packages to one another.

**Scope:**

- review `construction_kit.prediction.*`, `construction_kit.traces.*`, and
  `construction_kit.modulation.*`
- verify which current assumptions are already sufficiently generic
- generalize only where C+W requires it
- preserve existing `system_c` semantics and tests

**Likely touchpoints:**

- `src/axis/systems/construction_kit/prediction/memory.py`
- `src/axis/systems/construction_kit/prediction/error.py`
- `src/axis/systems/construction_kit/traces/state.py`
- `src/axis/systems/construction_kit/traces/update.py`
- `src/axis/systems/construction_kit/modulation/modulation.py`
- dependency-boundary tests under `tests/systems/construction_kit/`

**Explicit non-goals:**

- no imports from `system_c` into `system_cw`
- no refactor of `system_aw`
- no behavior change in `system_c` unless covered by backward-compatible tests

**Acceptance criteria:**

- all required kit primitives support `system_cw`
- existing `system_c` tests still pass unchanged
- boundary tests assert no cross-system imports

### WP-02: `system_cw` Config and State Model

**Goal:** Create the standalone configuration and state shell for `system_cw`.

**Modules to create:**

- `src/axis/systems/system_cw/config.py`
- `src/axis/systems/system_cw/types.py`

**Required outputs:**

- standalone `PredictionSharedConfig`
- standalone `DrivePredictionConfig`
- standalone `PredictionOutcomeConfig`
- standalone `SystemCWPredictionConfig`
- standalone `SystemCWConfig`
- `AgentStateCW` with shared `predictive_memory` and two separate trace states

**Key rules:**

- no inheritance from `SystemAWConfig` or `SystemCConfig`
- field layout may parallel A+W, but implementation remains independent
- predictive memory initializes with `feature_dim=10`

**Acceptance criteria:**

- config parses from YAML-shaped dicts matching the engineering spec
- state initializes correctly with shared memory and two drive-specific traces
- dedicated tests exist for model defaults, validation, and immutability

### WP-03: C+W Predictive Feature, Context, and Outcome Helpers

**Goal:** Implement the `system_cw`-local predictive helpers that must not live
in `system_c`.

**Modules to create:**

- `src/axis/systems/system_cw/features.py`
- `src/axis/systems/system_cw/context.py`
- `src/axis/systems/system_cw/outcomes.py`

**Required outputs:**

- `extract_predictive_features_cw(observation, curiosity_output)`
- `encode_context_cw(features, *, ...)`
- `compute_local_resource_value(...)`
- `compute_hunger_outcome(...)`
- `compute_curiosity_outcome(...)`

**Key rules:**

- feature vector must contain both resource-valued and novelty-derived features
- context encoder must aggressively compress the 10-D feature vector
- curiosity non-movement outcome must follow the v1 suppressive rule
- no migration of this system-specific logic into `system_c`

**Acceptance criteria:**

- helper outputs match the `spec.md` definitions
- context cardinality stays compact by construction
- movement and non-movement curiosity outcomes are explicitly tested

### WP-04: Decide Pipeline Integration

**Goal:** Build the independent `SystemCW` runtime shell and integrate the full
decision pipeline.

**Modules to create:**

- `src/axis/systems/system_cw/system.py`
- `src/axis/systems/system_cw/__init__.py`

**Required outputs:**

- `SystemCW` satisfying `SystemInterface`
- initialization path returning `AgentStateCW`
- dual-drive decision flow with predictive modulation applied separately to
  hunger and curiosity before arbitration
- rich `decision_data` exposing raw scores, predictive features, modulation
  details, arbitration, and policy output

**Key rules:**

- structure may follow `system_aw` as a reference, but implementation must be
  local to `system_cw`
- use `construction_kit` components only
- do not apply prediction after drive combination

**Acceptance criteria:**

- `SystemCW.decide()` returns valid actions and a complete decision payload
- neutral predictive settings recover A+W-like decision behavior
- divergence between hunger and curiosity modulation is observable in tests

### WP-05: Transition Pipeline Integration

**Goal:** Implement the C+W transition cycle with one shared predictive update
surface and two drive-specific trace paths.

**Modules to create:**

- `src/axis/systems/system_cw/transition.py`

**Required outputs:**

- `SystemCWTransition`
- energy update and observation-buffer update
- world-model update following A+W semantics
- pre-action context reconstruction
- one shared `get_prediction(...)` call
- separate hunger and curiosity outcome computations
- separate hunger and curiosity `update_traces(...)` calls
- one shared `update_predictive_memory(...)` call
- trace payload exposing both predictive channels

**Key rules:**

- transition may reference `system_aw` and `system_c` as design examples only
- no import of internal transition logic from another system package
- first-step behavior must gracefully skip predictive update if no pre-action
  observation exists

**Acceptance criteria:**

- trace and memory updates follow the engineering spec exactly
- non-movement curiosity outcome cannot produce positive curiosity evidence
- first-step and multi-step behavior are both covered by tests

### WP-06: Registration and Baseline Experiment Surface

**Goal:** Make `system_cw` runnable through the standard framework surface.

**Files to create or modify:**

- `src/axis/systems/system_cw/__init__.py`
- `experiments/configs/system-cw-baseline.yaml`
- plugin entry points in `pyproject.toml`

**Required outputs:**

- framework registration for `system_cw`
- metrics and visualization registration hooks
- baseline config that is immediately runnable

**Key rules:**

- baseline config should exercise the actual C+W prediction stack
- config structure must remain explicit rather than relying on inherited config
  behavior from another system

**Acceptance criteria:**

- `system_cw` is discoverable and constructible through normal registration
- baseline YAML loads successfully
- manual smoke-run path is defined and documented

### WP-07: Metrics and Visualization

**Goal:** Add the first dedicated observability layer for C+W.

**Modules to create:**

- `src/axis/systems/system_cw/metrics.py`
- `src/axis/systems/system_cw/visualization.py`

**Required outputs:**

- metrics for arbitration, modulation, and both trace channels
- visualization that keeps the A+W dual-drive layout and presents prediction as
  an explanatory overlay

**Key rules:**

- viewer style should align with A+W, not the single-drive C presentation
- metrics must distinguish hunger-side and curiosity-side predictive effects

**Acceptance criteria:**

- traces and decision payloads can be rendered intelligibly
- system-specific metrics load through the standard extension path

### WP-08: Reduction, Boundary, and Episode Hardening

**Goal:** Prove that the implementation is behaviorally and architecturally
correct.

**Required test areas:**

- exact reduction to A+W when predictive influence is neutralized
- constructive System-C-like regime when curiosity and novelty pathways are
  neutralized
- shared predictive memory with diverging drive-specific traces
- no cross-system imports among `system_a`, `system_aw`, `system_c`, and
  `system_cw`
- episode smoke tests with non-trivial predictive activity

**Key rules:**

- architectural boundary tests are first-class acceptance criteria
- reduction tests should use the same style as existing A/A+W/C parity tests

**Acceptance criteria:**

- reduction and regime tests pass
- end-to-end episodes complete without crashes or invalid state
- dependency-constraint tests enforce system independence

### WP-09: Internal Docs and Workload Closure

**Goal:** Close the implementation loop so the feature is easy to continue and
maintain.

**Likely outputs:**

- implementation status note
- short follow-up delta list if any low-priority items were deferred
- updates to internal docs that reference available systems or baseline configs

**Acceptance criteria:**

- the delivered shape of `system_cw` is documented
- any remaining optional follow-ups are separated from the completed core

---

## Recommended Wave Plan

### Wave 1

- `WP-01`
- `WP-02`
- `WP-03`

### Wave 2

- `WP-04`
- `WP-05`

### Wave 3

- `WP-06`
- `WP-07`

### Wave 4

- `WP-08`
- `WP-09`

This wave plan keeps the highest-risk architectural questions early, the core
runtime in the middle, and proof / polish late.

---

## Verification Summary

After completing all work packages:

1. `system_cw` exists as a standalone system package with no direct dependency
   on `system_aw` or `system_c`.
2. Shared predictive primitives remain reusable through `construction_kit`.
3. `axis experiments run experiments/configs/system-cw-baseline.yaml` is
   runnable.
4. C+W reduces exactly to A+W when predictive influence is neutralized.
5. A C-like regime can be approximated by disabling curiosity and masking
   novelty pathways.
6. Metrics and visualization expose both predictive channels clearly.
