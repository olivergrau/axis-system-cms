# System C+W -- Engineering Specification

## Predictive Dual-Drive Agent on the Existing AXIS System Stack

**Status:** Draft  
**Based on:** `docs-internal/ideas/system-cw/spec.md`  
**Target version:** v0.3.x  
**Implementation posture:** conservative new system package aligned with
existing `system_aw` and `system_c` patterns, but independent from both at
runtime  

---

## 1. Purpose

This document maps the conceptual and mathematical `System C+W` specification
onto the current AXIS implementation.

Its role is to define:

- which existing components should be reused unchanged
- which new files and types should be introduced
- where C+W-specific logic should live
- how the decision and transition pipelines should be assembled
- which configuration surfaces are required
- and which implementation boundaries should be preserved so that later
  work-packages can be derived cleanly

System C+W is implemented as:

> the structural shell of System A+W plus the predictive layer pattern of
> System C, with shared predictive memory and drive-specific trace/modulation
> paths.

This is a structural mapping only. It does not imply inheritance, direct
runtime dependency, or cross-system imports between `system_aw`, `system_c`,
and `system_cw`.

---

## 2. Scope

### In scope

- new system package `src/axis/systems/system_cw/`
- new config model for C+W
- new agent state model for C+W
- C+W-specific predictive feature assembly
- C+W-specific context compression
- C+W-specific hunger / curiosity outcome semantics
- dual modulation before A+W-style arbitration
- C+W transition logic
- registration, baseline experiment config, metrics, and visualization

### Out of scope

- changes to SDK protocols
- planner-like world modeling
- route memory or global map inference
- replacement of the existing System C implementation
- behavioral redesign of System A+W
- framework orchestration changes

---

## 3. Recommended Implementation Route

If a human were implementing the system manually, the most natural starting
point would be to copy `system_aw` and then graft predictive logic into it.

That is also the recommended engineering route here.

### 3.1 Why `system_aw` is the right structural base

`system_aw` already contains the correct first-order structure for C+W:

- dual drives
- world model
- observation buffer usage
- drive arbitration
- trace-friendly decision payload for hunger and curiosity

By contrast, `system_c` has the predictive layer but only one drive and no
world-model-dependent curiosity path.

### 3.2 Practical engineering rule

The implementation should therefore treat:

- `system_aw` as the primary composition template
- `system_c` as the predictive-layer reference

This does **not** require a literal long-term code fork of A+W internals into
the construction kit. It means:

- start from the A+W package structure
- preserve A+W behavioral structure where prediction is neutralized
- add predictive memory, two trace states, and dual modulation in the same
  places where C adds single-drive modulation

It also means:

- `system_cw` is implemented as its own package, not as a subclass or wrapper
  of `system_aw` or `system_c`
- `system_aw`, `system_c`, and `system_cw` may all depend on the
  `construction_kit`, but must not depend on one another
- any shared generalization work must happen in `construction_kit` under
  backward-compatible interfaces

### 3.3 Compatibility objective

The implementation must preserve these two guarantees:

1. Neutralizing predictive influence yields exact A+W behavior.
2. C+W-specific changes do not alter the behavior of the existing `system_aw`
   or `system_c` packages.
3. `system_aw`, `system_c`, and `system_cw` remain independent system packages
   with no inheritance or direct internal reuse across system-package
   boundaries.

---

## 4. Existing Components To Reuse

The following existing implementation pieces should be reused unchanged in the
first wave.

### 4.1 Observation and policy

- `construction_kit.observation.sensor.VonNeumannSensor`
- `construction_kit.policy.softmax.SoftmaxPolicy`

### 4.2 Drives and arbitration

- `construction_kit.drives.hunger.HungerDrive`
- `construction_kit.drives.curiosity.CuriosityDrive`
- `construction_kit.arbitration.weights.compute_maslow_weights`
- `construction_kit.arbitration.scoring.combine_drive_scores`

### 4.3 Memory and world model

- `construction_kit.memory.observation_buffer.update_observation_buffer`
- `construction_kit.memory.world_model.create_world_model`
- `construction_kit.memory.world_model.update_world_model`
- `construction_kit.memory.types.ObservationBuffer`
- `construction_kit.memory.types.WorldModelState`

### 4.4 Predictive core

- `construction_kit.prediction.memory.PredictiveMemory`
- `construction_kit.prediction.memory.create_predictive_memory`
- `construction_kit.prediction.memory.get_prediction`
- `construction_kit.prediction.memory.update_predictive_memory`
- `construction_kit.prediction.error.compute_prediction_error`
- `construction_kit.traces.state.TraceState`
- `construction_kit.traces.state.create_trace_state`
- `construction_kit.traces.state.get_confidence`
- `construction_kit.traces.state.get_frustration`
- `construction_kit.traces.update.update_traces`
- `construction_kit.modulation.modulation.describe_action_modulation`

### 4.5 Energy and action handling

- `construction_kit.energy.functions.clip_energy`
- `construction_kit.types.actions.handle_consume`

---

## 5. New Package Layout

The new system package should be:

```text
src/axis/systems/system_cw/
  __init__.py
  config.py
  types.py
  features.py
  context.py
  outcomes.py
  system.py
  transition.py
  metrics.py
  visualization.py
```

### 5.1 Rationale

The new package keeps C+W-specific feature, context, and outcome logic local to
the system rather than mutating the existing generic System C helpers.

This is the safest first-wave strategy because:

- `System C` currently assumes a 5-feature resource-only predictive substrate
- `System C+W` needs a richer feature vector and different outcome semantics
- the shared predictive memory and trace primitives are still reusable

### 5.2 Optional later extraction

If later systems reuse the same predictive feature assembly or context
compression logic, those helpers can be migrated into the construction kit in a
second step. That migration is explicitly not required for first-wave delivery.

---

## 6. Component Map

| Spec element | Implementation artifact | Reuse vs new | Location |
|---|---|---|---|
| $u_t$ | `Observation` | reuse | `construction_kit/observation/types.py` |
| $d_H(t)$ | `HungerDrive.compute()` | reuse | `construction_kit/drives/hunger.py` |
| $d_C(t)$ | `CuriosityDrive.compute()` | reuse | `construction_kit/drives/curiosity.py` |
| $\hat p_t, w_t$ | `WorldModelState` | reuse | `construction_kit/memory/types.py` |
| $q_t(s,a)$ | `PredictiveMemory` | reuse | `construction_kit/prediction/memory.py` |
| $z_t^H$ | `TraceState` field for hunger | reuse primitive, new composition | `system_cw/types.py` |
| $z_t^C$ | `TraceState` field for curiosity | reuse primitive, new composition | `system_cw/types.py` |
| $y_t^{CW}$ | `extract_predictive_features_cw()` | new | `system_cw/features.py` |
| $C(y_t^{CW})$ | `encode_context_cw()` | new | `system_cw/context.py` |
| $R_{local}, Y_t^H, Y_t^C$ | outcome helpers | new | `system_cw/outcomes.py` |
| $\tilde G_H$ | modulation over hunger trace state | composed reuse | `system_cw/system.py` |
| $\tilde G_C$ | modulation over curiosity trace state | composed reuse | `system_cw/system.py` |
| arbitration | `compute_maslow_weights`, `combine_drive_scores` | reuse | kit |
| state transition | `SystemCWTransition` | new | `system_cw/transition.py` |
| registration | `register()` | new | `system_cw/__init__.py` |

---

## 7. Configuration Model

The config model should be a new standalone `SystemCWConfig`.

### 7.1 Design rule

`System C+W` is structurally:

- A+W-like baseline config surface
- plus a new predictive block

This means schema similarity, not Python inheritance from `SystemAWConfig` or
`SystemCConfig`.

The file should therefore define:

- `PredictionSharedConfig`
- `DrivePredictionConfig`
- `PredictionOutcomeConfig`
- `SystemCWPredictionConfig`
- `SystemCWConfig`

### 7.2 Shared prediction config

`PredictionSharedConfig` should contain parameters that belong to the shared
predictive memory and context substrate:

- `memory_learning_rate`
- context compression parameters
- context cardinality parameter if explicitly required by the encoder
- `positive_weights`
- `negative_weights`

It should also contain the local resource-value parameters used by both hunger-
 and curiosity-side outcome definitions:

- `local_resource_current_weight`
- `local_resource_neighbor_weight`

### 7.3 Drive-specific prediction config

`DrivePredictionConfig` should contain the modulation and trace parameters that
belong to one drive-specific trace path:

- `frustration_rate`
- `confidence_rate`
- `positive_sensitivity`
- `negative_sensitivity`
- `modulation_min`
- `modulation_max`
- `modulation_mode`
- `prediction_bias_scale`
- `prediction_bias_clip`

The same model should be instantiated twice:

- `prediction.hunger`
- `prediction.curiosity`

### 7.4 Curiosity-outcome config

`PredictionOutcomeConfig` should contain at minimum:

- `nonmove_curiosity_penalty`

This parameter implements $\kappa_{nonmove}^C$ from the system specification.

### 7.5 Full system config

`SystemCWConfig` should mirror the A+W config structure:

- `agent`
- `policy`
- `transition`
- `curiosity`
- `arbitration`

and add:

- `prediction`

The intended YAML shape is:

```yaml
system:
  agent: ...
  policy: ...
  transition: ...
  curiosity: ...
  arbitration: ...
  prediction:
    shared: ...
    hunger: ...
    curiosity: ...
    outcomes: ...
```

This layout keeps the existing A+W semantics legible while cleanly separating:

- shared predictive memory parameters
- hunger-side predictive interpretation
- curiosity-side predictive interpretation

`SystemCWConfig` should therefore be implemented as an independent model with
its own fields and validation rules, even where those fields intentionally
parallel `SystemAWConfig`.

---

## 8. Agent State Model

The agent state should be declared in `system_cw/types.py` as `AgentStateCW`.

### 8.1 Required fields

`AgentStateCW` must contain:

- `energy: float`
- `observation_buffer: ObservationBuffer`
- `world_model: WorldModelState`
- `predictive_memory: PredictiveMemory`
- `hunger_trace_state: TraceState`
- `curiosity_trace_state: TraceState`
- `last_observation: Observation | None`

### 8.2 Initialization

Initial state should be:

- energy from `config.agent.initial_energy`
- empty observation buffer with configured capacity
- fresh world model from `create_world_model()`
- predictive memory from `create_predictive_memory(feature_dim=...)`
- fresh hunger trace state from `create_trace_state()`
- fresh curiosity trace state from `create_trace_state()`
- `last_observation = None`

### 8.3 Feature dimension

The predictive memory must be initialized with the C+W feature dimension, not
the System C default.

For the current `spec.md`, that means:

$$
\dim(y_t^{CW}) = 10
$$

Therefore:

- `feature_dim=10`

must be passed explicitly when creating predictive memory.

---

## 9. C+W-Specific Predictive Helpers

The first-wave implementation should keep three helpers local to
`system_cw/`.

### 9.1 `features.py`

This module should assemble:

$$
y_t^{CW} =
(r_c, r_u, r_d, r_l, r_r, \nu_u, \nu_d, \nu_l, \nu_r, \bar\nu_{local})
$$

Inputs should be explicit, not recomputed implicitly from hidden state:

- current `Observation`
- `CuriosityDriveOutput`

This avoids recomputing novelty after the drive already computed it in the
decision path.

Recommended function:

- `extract_predictive_features_cw(observation, curiosity_output) -> tuple[float, ...]`

### 9.2 `context.py`

This module should implement the compact context encoder required by the
specification.

The key engineering constraint is:

- do not reuse System C's 5-bit resource-only encoder
- do not naively threshold all 10 dimensions into a 1024-state context space

The encoder must compress the C+W feature vector aggressively into a small,
well-covered discrete set.

The concrete bit layout is an implementation decision, but the module must own:

- the compression strategy
- the declared effective context cardinality
- any thresholds used by that compression

Recommended function:

- `encode_context_cw(features, *, ...) -> int`

### 9.3 `outcomes.py`

This module should own the system-specific outcome semantics:

- `compute_local_resource_value(...)`
- `compute_hunger_outcome(...)`
- `compute_curiosity_outcome(...)`

This logic belongs in `system_cw`, not the generic prediction package, because:

- it depends on the dual-drive interpretation
- it uses the curiosity pre-action novelty weight
- it includes the non-movement curiosity penalty rule

Keeping it local keeps the generic prediction package reusable and simple.

---

## 10. Decide Pipeline

`system_cw/system.py` should follow the structure of `system_aw/system.py` as a
design reference, while remaining an independent implementation.

### 10.1 Pipeline order

The `decide()` method should perform:

1. perceive via `VonNeumannSensor`
2. compute hunger drive output
3. compute curiosity drive output
4. build shared predictive features and compressed context
5. modulate hunger action contributions using `hunger_trace_state`
6. modulate curiosity action contributions using `curiosity_trace_state`
7. compute A+W arbitration weights
8. combine the two modulated score vectors
9. run policy selection
10. return structured `decision_data`

### 10.2 Modulation rule

The existing `describe_action_modulation()` helper should be called twice:

- once with hunger raw scores and hunger trace state
- once with curiosity raw scores and curiosity trace state

using different config blocks:

- `prediction.hunger`
- `prediction.curiosity`

### 10.3 Arbitration boundary

The engineering implementation must preserve the conceptual layering:

```text
hunger raw projection
curiosity raw projection
-> drive-specific predictive modulation
-> A+W arbitration weights
-> score combination
-> policy
```

This means:

- prediction must not be applied to already-combined scores
- arbitration must consume already-modulated drive outputs

### 10.4 Decision trace payload

`decision_data` should include, at minimum:

- observation
- hunger drive activation and raw contributions
- curiosity drive activation, novelty breakdown, and raw contributions
- predictive context and feature vector
- hunger-side modulation details
- curiosity-side modulation details
- arbitration weights
- final combined scores
- policy data

This is required so visualization and later comparison extensions can explain:

- raw motivational pressure
- predictive reshaping
- post-modulation arbitration

---

## 11. Transition Pipeline

`system_cw/transition.py` should follow the structure of
`system_aw/transition.py` for the world-model path, and the structure of
`system_c/transition.py` for the predictive update path, but remain an
independent transition implementation.

### 11.1 Constructor model

As with `SystemCTransition`, the constructor should receive the full parsed
`SystemCWConfig`, not just isolated scalars.

That keeps:

- shared prediction config
- hunger predictive config
- curiosity predictive config
- outcome parameters

available in one place.

### 11.2 Transition phases

The transition should execute these phases:

1. energy update
2. observation buffer update
3. world-model update (dead reckoning + visit counts)
4. predictive post-action feature extraction
5. pre-action context reconstruction
6. shared predictive memory lookup
7. hunger-side outcome computation
8. curiosity-side outcome computation
9. hunger trace update
10. curiosity trace update
11. shared predictive memory update
12. state assembly
13. termination check

### 11.3 Pre-action data access

As in System C, the predictive update cycle needs the pre-action observation.

The first-wave implementation should preserve the existing System C pattern:

- store `_pre_observation` in `decision_data`
- pass it through `action_outcome.data`
- fall back to `agent_state.last_observation` if needed

### 11.4 Shared memory, separate traces

Transition must enforce the core rule:

- one call to `get_prediction(...)`
- one shared predicted feature vector
- two separate outcome computations
- two separate calls to `update_traces(...)`
- one shared call to `update_predictive_memory(...)`

### 11.5 Curiosity non-movement rule

For `consume` and `stay`, the curiosity-side outcome path must use the v1
specification:

$$
Y_t^C(a_t) = \hat Y_t^C(a_t) = -\kappa_{nonmove}^C \cdot d_C(t)
$$

This means:

- non-movement actions cannot create curiosity-positive evidence
- curiosity-side traces for those actions can only remain neutral or encode
  suppressive history

### 11.6 Transition trace payload

`trace_data` should include:

- energy update info
- buffer sizes / buffer snapshot as needed
- world-model snapshot
- shared predicted vs observed features
- hunger-side predicted and observed scalar outcomes
- curiosity-side predicted and observed scalar outcomes
- hunger confidence/frustration values
- curiosity confidence/frustration values

This gives the visualizer and metrics layer enough information to explain both
predictive channels.

---

## 12. Metrics and Visualization

### 12.1 Metrics

`system_cw/metrics.py` should be implemented and registered, following the
existing patterns in `system_aw/metrics.py` and `system_c/metrics.py`.

The first-wave metrics should cover:

- arbitration statistics
- curiosity-pressure statistics
- hunger modulation summaries
- curiosity modulation summaries
- confidence / frustration summaries for both drives

### 12.2 Visualization

`system_cw/visualization.py` should extend the A+W viewer style, not the C
viewer style.

Reason:

- the visible behavioral structure is still dual-drive + world model
- prediction should appear as an explanatory overlay, not the primary layout

The viewer should therefore present:

- hunger and curiosity sections
- novelty sections
- arbitration section
- prediction sections for hunger and curiosity separately

### 12.3 Comparison extension

A dedicated comparison extension is optional for the first functional release.

It may be deferred if needed.

The first milestone requires:

- runnable system
- metrics extension
- visualization adapter

not necessarily a custom pairwise comparison extension.

---

## 13. Registration and Artifact Surface

The following files or entries are required beyond the core package.

### 13.1 Registration

- add `src/axis/systems/system_cw/__init__.py`
- register `system_cw` with the framework
- register metrics extension
- register visualization adapter

### 13.2 Packaging

Add the plugin entry point alongside the existing systems in `pyproject.toml`.

### 13.3 Experiment configs

Add at least:

- `experiments/configs/system-cw-baseline.yaml`

Optionally later:

- curiosity/prediction sweep configs
- exploration-biased demo configs

---

## 14. Backward-Compatibility Rules

The engineering implementation must follow these rules:

1. `system_aw` behavior must remain unchanged.
2. `system_c` behavior must remain unchanged.
3. `system_a`, `system_aw`, `system_c`, and `system_cw` must remain independent
   system packages; no system may subclass, import internal runtime logic from,
   or otherwise depend directly on another system package.
4. Shared reuse across systems is allowed only through stable
   `construction_kit` interfaces.
5. Generic prediction/traces/modulation helpers must remain
   backward-compatible if touched at all.
6. No framework or SDK protocol changes are allowed for first-wave delivery.

If a needed change would alter `system_c` semantics, it should be implemented
as a new C+W-local helper instead.

If a prediction-related helper needs to become more generic for reuse, that
generalization should occur inside `construction_kit` with backward-compatible
behavior for existing systems, not through direct reuse of `system_c`
implementation modules.

---

## 15. Validation Targets

The later work-packages derived from this document should validate at least the
following properties.

### 15.1 Structural correctness

- `SystemCW` satisfies `SystemInterface`
- config parses cleanly
- state initializes with shared predictive memory and two trace states

### 15.2 Reduction correctness

- disabling predictive influence reduces C+W exactly to A+W
- disabling curiosity pathways and masking novelty context produces a
  System-C-like regime

### 15.3 Behavioral correctness

- hunger modulation and curiosity modulation can diverge under the same shared
  predictive memory
- curiosity-positive evidence arises only from movement-based exploration yield
- non-movement curiosity outcomes remain neutral or suppressive

### 15.4 Artifact correctness

- decision traces expose both predictive channels
- transition traces expose both predictive update paths
- visualization can display both raw and modulated dual-drive behavior

---

## 16. Work-Package Readiness

This engineering spec is intentionally written so that work-packages can be cut
along clean module and responsibility boundaries.

The natural implementation slices are:

- config and state model
- C+W-local predictive helpers
- decide pipeline integration
- transition pipeline integration
- registration and config artifacts
- metrics and visualization

That slicing should be used when generating the later work-package plan.
