# System C -- Work Package Definitions

**Based on:** `implementation-roadmap.md`, `system-c-engineering-spec.md`  
**Date:** 2026-04-15

---

## Phase 1 -- Construction Kit Components

WP1, WP2, and WP3 are independent and can be developed in parallel.
Each fills one of the three empty Phase 2 placeholder packages.

---

### WP1 -- Prediction Package

**Goal:** Fill `src/axis/systems/construction_kit/prediction/` with predictive
feature extraction, context encoding, predictive memory, and prediction error
computation.

**Modules to create:**

| File | Contents |
|---|---|
| `features.py` | `extract_predictive_features(observation) -> tuple[float, ...]` -- extracts the 5 resource values (center, up, down, left, right) from an `Observation`. Simple delegation, exists as the explicit $\Omega$ boundary. |
| `context.py` | `encode_context(features, *, threshold=0.5) -> int` -- binary-thresholds each of the 5 features and packs them into a 5-bit integer (bit 4=center ... bit 0=right). Returns int in [0, 31]. |
| `memory.py` | `PredictiveMemory` frozen Pydantic model storing `entries: tuple[tuple[tuple[int, str], tuple[float, ...]], ...]` and `feature_dim: int = 5`. Functions: `create_predictive_memory(*, num_contexts=32, actions=(...), feature_dim=5) -> PredictiveMemory` (all entries zero), `get_prediction(memory, context, action) -> tuple[float, ...]` (returns zero vector if unseen), `update_predictive_memory(memory, context, action, observed_features, *, learning_rate) -> PredictiveMemory` (EMA update for one pair, others unchanged). Follow the `WorldModelState` pattern for tuple-of-tuples storage. |
| `error.py` | `PredictionError` frozen model with `positive`, `negative` (per-dimension tuples), `scalar_positive`, `scalar_negative` (aggregated floats). Function: `compute_prediction_error(predicted, observed, *, positive_weights, negative_weights) -> PredictionError`. Component-wise: $\delta^+ = \max(y - \hat{y}, 0)$, $\delta^- = \max(\hat{y} - y, 0)$. Scalar: weighted sum with provided weights. |
| `__init__.py` | Replace the placeholder docstring with exports: `extract_predictive_features`, `encode_context`, `PredictiveMemory`, `create_predictive_memory`, `get_prediction`, `update_predictive_memory`, `PredictionError`, `compute_prediction_error`. |

**Imports allowed:** `axis.sdk` (none needed in practice), `construction_kit.observation.types` (for `Observation` type in `features.py`).

**Tests to create:**

| Test file | Test cases |
|---|---|
| `tests/systems/construction_kit/prediction/__init__.py` | empty |
| `tests/systems/construction_kit/prediction/test_features.py` | Extract from a known `Observation` returns correct 5-tuple. Verify ordering matches (center, up, down, left, right). Zero-resource observation returns all zeros. |
| `tests/systems/construction_kit/prediction/test_context.py` | All-zero features -> context 0. All-above-threshold -> context 31. Single feature above threshold -> correct bit position. Threshold edge case: exactly 0.5 maps to 1. Below 0.5 maps to 0. Custom threshold works. |
| `tests/systems/construction_kit/prediction/test_memory.py` | `create_predictive_memory` returns 192 entries (32 x 6) all zero. `get_prediction` for unseen pair returns zero vector of length 5. `update_predictive_memory` with $\eta_q = 1.0$ replaces old value entirely. With $\eta_q = 0.5$, result is midpoint. Only updated pair changes; all others unchanged. Model is frozen (immutable). Multiple sequential updates converge toward observed value. |
| `tests/systems/construction_kit/prediction/test_error.py` | Perfect prediction (predicted == observed) -> all zeros. Positive surprise only: observed > predicted -> positive nonzero, negative zero. Negative surprise only: observed < predicted -> negative nonzero, positive zero. Mixed: some dimensions positive, some negative. Scalar aggregation: center-heavy weights (0.5, 0.125...) applied correctly. Verify weights sum check or behavior when they don't sum to 1. |

**Estimated tests:** 18-22

**Acceptance criteria:**
- All functions match signatures from engineering spec Section 4.1
- `PredictiveMemory` is a frozen Pydantic model
- All functions are pure (no side effects, no mutation)
- No imports from `axis.framework`, `axis.world`, or any `axis.systems.system_*`

---

### WP2 -- Traces Package

**Goal:** Fill `src/axis/systems/construction_kit/traces/` with the dual-trace
state model and EMA update function.

**Modules to create:**

| File | Contents |
|---|---|
| `state.py` | `TraceState` frozen Pydantic model with `frustration: tuple[tuple[tuple[int, str], float], ...]` and `confidence: tuple[tuple[tuple[int, str], float], ...]`, both defaulting to `()`. Functions: `create_trace_state() -> TraceState` (returns empty -- all zeros implicitly), `get_frustration(state, context, action) -> float` (returns 0.0 if pair not found), `get_confidence(state, context, action) -> float` (same). |
| `update.py` | `update_traces(state, context, action, scalar_positive, scalar_negative, *, frustration_rate, confidence_rate) -> TraceState` -- EMA update: $f_{t+1} = (1 - \eta_f) f_t + \eta_f \varepsilon^-$, $c_{t+1} = (1 - \eta_c) c_t + \eta_c \varepsilon^+$. Only the specified (context, action) pair is updated. All others unchanged. Returns new `TraceState`. |
| `__init__.py` | Replace the placeholder docstring with exports: `TraceState`, `create_trace_state`, `get_frustration`, `get_confidence`, `update_traces`. |

**Imports allowed:** `pydantic` only. No `axis.*` imports needed.

**Tests to create:**

| Test file | Test cases |
|---|---|
| `tests/systems/construction_kit/traces/__init__.py` | empty |
| `tests/systems/construction_kit/traces/test_state.py` | `create_trace_state` returns empty frustration and confidence. `get_frustration` returns 0.0 for unseen pair. `get_confidence` returns 0.0 for unseen pair. Model is frozen. |
| `tests/systems/construction_kit/traces/test_update.py` | From empty state, first update with $\varepsilon^- = 1.0$, $\eta_f = 0.2$ -> frustration = 0.2. First update with $\varepsilon^+ = 1.0$, $\eta_c = 0.15$ -> confidence = 0.15. Second update accumulates correctly (EMA formula). With $\varepsilon^- = 0$ and $\varepsilon^+ = 0$, traces decay toward zero. Only specified pair changes; other pairs unchanged. Both traces updated simultaneously in one call. |

**Estimated tests:** 10-12

**Acceptance criteria:**
- `TraceState` is frozen Pydantic model
- Trace values are always non-negative
- Update function is pure
- No imports from `axis.framework`, `axis.world`, or any `axis.systems.system_*`

---

### WP3 -- Modulation Package

**Goal:** Fill `src/axis/systems/construction_kit/modulation/` with the
exponential modulation factor and batch score modulation.

**Modules to create:**

| File | Contents |
|---|---|
| `modulation.py` | `compute_modulation(frustration, confidence, *, positive_sensitivity, negative_sensitivity, modulation_min, modulation_max) -> float` -- computes $\tilde{\mu} = \exp(\lambda_+ c - \lambda_- f)$, then clips to $[\mu_{\min}, \mu_{\max}]$. `modulate_action_scores(action_scores, context, actions, trace_state, *, positive_sensitivity, negative_sensitivity, modulation_min, modulation_max) -> tuple[float, ...]` -- for each action, looks up frustration and confidence from trace_state, computes modulation factor, multiplies the base score. Returns new tuple of modulated scores. |
| `__init__.py` | Replace the placeholder docstring with exports: `compute_modulation`, `modulate_action_scores`. |

**Imports allowed:** `math` (for `exp`), `construction_kit.traces.state` (for `TraceState`, `get_frustration`, `get_confidence`) in `modulate_action_scores`.

**Tests to create:**

| Test file | Test cases |
|---|---|
| `tests/systems/construction_kit/modulation/__init__.py` | empty |
| `tests/systems/construction_kit/modulation/test_modulation.py` | **compute_modulation:** Zero frustration and confidence -> $\mu = 1.0$. Pure frustration ($f > 0, c = 0$) -> $\mu < 1.0$. Pure confidence ($c > 0, f = 0$) -> $\mu > 1.0$. Clipping at $\mu_{\min}$: high frustration clips to 0.3. Clipping at $\mu_{\max}$: high confidence clips to 2.0. With $\lambda_+ = \lambda_- = 0$ -> $\mu = 1.0$ regardless of trace values (reduction property). Numerical check: $f = 0.5, c = 0.3, \lambda_+ = 1.0, \lambda_- = 1.5$ -> verify exact value. **modulate_action_scores:** With empty trace state (all traces zero) -> output equals input. With non-zero traces for one action -> only that action's score changes. Output tuple has same length as input. Negative base scores remain correctly modulated (multiplication, not addition). |

**Estimated tests:** 10-12

**Acceptance criteria:**
- `compute_modulation` matches formula from engineering spec Section 4.3
- With $\lambda_+ = \lambda_- = 0$, modulation is exactly 1.0 (reduction property)
- Clipping bounds are enforced
- `modulate_action_scores` delegates to `compute_modulation` per action

---

## Phase 2 -- Kit Integration Verification

---

### WP4 -- Kit Pipeline Integration Test

**Goal:** Verify that WP1 + WP2 + WP3 compose correctly end-to-end on
synthetic data before building System C on top.

**No production modules to create.** Test-only work package.

**Tests to create:**

| Test file | Test cases |
|---|---|
| `tests/systems/construction_kit/test_predictive_pipeline.py` | **Full cycle test:** Given a synthetic `Observation`, run the complete predictive pipeline: `extract_predictive_features` -> `encode_context` -> `get_prediction` -> `compute_prediction_error` -> `update_traces` -> `update_predictive_memory` -> `modulate_action_scores`. Verify all intermediate values are reasonable (no NaN, no negative where non-negative required). **Convergence test:** Run 10 update cycles with the same observation. Verify predictive memory converges toward the observed features. Verify prediction error decreases over iterations. **Neutral start test:** At $t=0$ with empty traces, modulated scores equal base scores exactly. **Asymmetric learning test:** After 5 cycles of disappointment (observed < predicted), frustration trace is positive, confidence is zero. The modulated action score is lower than the base score. After 5 cycles of positive surprise (observed > predicted), confidence is positive. The modulated score is higher. |

**Estimated tests:** 5-7

**Acceptance criteria:**
- Full pipeline executes without error
- All intermediate types are correct
- Convergence behavior matches EMA expectations
- Neutral modulation at $t=0$ is verified

**Additional task:** Update `tests/systems/construction_kit/test_dependency_constraints.py`:
- Add `prediction`, `traces`, `modulation` to the circular-dependency import test (`test_no_circular_construction_kit_imports`)
- Add `system_c` to the cross-system boundary test (`test_no_cross_system_imports`)

---

## Phase 3 -- System C Core

---

### WP5 -- System C Configuration, State, and Decide Pipeline

**Goal:** Create the `systems/system_c/` package with config models, agent
state, and the `SystemC` class with a working `decide()` pipeline.

**Modules to create:**

| File | Contents |
|---|---|
| `config.py` | `PredictionConfig` frozen Pydantic model with all 10 prediction parameters and their spec defaults (see engineering spec Section 5.2). `SystemCConfig` frozen model with `agent: AgentConfig`, `policy: PolicyConfig`, `transition: TransitionConfig`, `prediction: PredictionConfig = PredictionConfig()`. |
| `types.py` | `AgentStateC` frozen Pydantic model: `energy: float` (ge=0), `observation_buffer: ObservationBuffer`, `predictive_memory: PredictiveMemory`, `trace_state: TraceState`, `last_observation: Observation | None = None`. |
| `system.py` | `SystemC` class implementing all `SystemInterface` methods. Constructor composes: `VonNeumannSensor`, `HungerDrive`, `SoftmaxPolicy`, `SystemCTransition` (from WP6 -- stub or import). `decide()` implements the 6-step pipeline: perception -> drive -> features/context -> modulation -> policy -> return. `initialize_state()` returns `AgentStateC` with zero energy, empty buffer, `create_predictive_memory()`, `create_trace_state()`, `last_observation=None`. Other methods: `system_type() -> "system_c"`, `action_space()`, `vitality()`, `action_handlers()`, `observe()`, `action_context()`. |
| `__init__.py` | Exports: `SystemC`, `SystemCConfig`, `handle_consume`. `register()` function with factory and visualization adapter registration (same pattern as System A). |

**Imports from kit:** `VonNeumannSensor`, `HungerDrive`, `SoftmaxPolicy`, `ObservationBuffer`, `create_predictive_memory`, `create_trace_state`, `extract_predictive_features`, `encode_context`, `modulate_action_scores`, `handle_consume`.

**Tests to create:**

| Test file | Test cases |
|---|---|
| `tests/systems/system_c/__init__.py` | empty |
| `tests/systems/system_c/test_config.py` | `PredictionConfig()` defaults match spec values: $\eta_q = 0.3$, context_threshold = 0.5, $\eta_f = 0.2$, $\eta_c = 0.15$, $\lambda_+ = 1.0$, $\lambda_- = 1.5$, $\mu_{\min} = 0.3$, $\mu_{\max} = 2.0$, weights = (0.5, 0.125, 0.125, 0.125, 0.125). `SystemCConfig` parses from dict (reuse System A's agent/policy/transition + add prediction). `SystemCConfig` works without prediction section (defaults apply). Validation: frozen model. |
| `tests/systems/system_c/test_types.py` | `AgentStateC` is frozen. Contains all 5 fields. `last_observation` defaults to None. Accepts a `PredictiveMemory` and `TraceState`. |
| `tests/systems/system_c/test_system.py` | `SystemC` satisfies `SystemInterface` (isinstance check). `system_type()` returns `"system_c"`. `action_space()` returns 6-tuple. `initialize_state()` returns `AgentStateC` with correct energy, empty buffer, zero memory, zero traces, None last_observation. `vitality()` returns energy / max_energy. `action_handlers()` returns `{"consume": handle_consume}`. `action_context()` returns max_consume dict. |
| `tests/systems/system_c/test_decide.py` | Decide with fresh state (zero traces) -> returns a valid `DecideResult` with action in action_space. Decision_data contains "observation", "drive", "prediction", "policy" keys. With zero traces, modulated_scores in decision_data equal raw action_contributions (modulation is neutral). With non-zero traces injected into agent state, modulated_scores differ from raw contributions. |

**Test builder to create:**

| File | Contents |
|---|---|
| `tests/builders/system_c_config_builder.py` | `SystemCConfigBuilder` -- fluent builder extending `SystemAConfigBuilder` pattern. Adds `with_prediction_*` methods for all prediction parameters. `build()` returns dict with agent, policy, transition, prediction sections. |

**Estimated tests:** 15-18

**Acceptance criteria:**
- `SystemC` passes `isinstance(system, SystemInterface)` check
- `decide()` returns valid `DecideResult`
- Config defaults exactly match engineering spec Section 11 parameter table
- Modulation is neutral (1.0) when trace state is empty

---

## Phase 4 -- System C Transition

---

### WP6 -- Transition Function with Predictive Update Cycle

**Goal:** Implement `SystemCTransition` with the full predictive update cycle
(phases 4-8 from engineering spec Section 5.5).

**Modules to create:**

| File | Contents |
|---|---|
| `transition.py` | `SystemCTransition` class. Constructor takes `config: SystemCConfig`. `transition(agent_state, action_outcome, observation, *, timestep=0) -> TransitionResult` implements: **Phase 4** -- energy update via `clip_energy` (same as System A). **Phase 5** -- observation buffer update via `update_observation_buffer`. **Phase 6** -- predictive update cycle (skipped if `agent_state.last_observation is None`): (6a) extract post-action features from observation, (6b) extract pre-action features from `last_observation` and encode context, retrieve prediction, (6c) compute prediction error, (6d) update traces, (6e) update predictive memory. **Phase 7** -- build new `AgentStateC` with updated fields and `last_observation=observation`. **Phase 8** -- termination check ($e \le 0$). Emit trace_data dict with energy, buffer, and prediction sub-dicts. |

**Tests to create:**

| Test file | Test cases |
|---|---|
| `tests/systems/system_c/test_transition.py` | **Energy update:** Verify action cost deduction and energy gain from consume, same as System A. Energy clips at 0 and max_energy. **Buffer update:** Observation appended to buffer. Buffer respects capacity. **First-step skip:** When `last_observation is None`, predictive memory and traces are unchanged. `last_observation` in new state is set to the current observation. **Predictive update -- memory:** After one transition with `last_observation` set, predictive memory is updated for the (context, action) pair. Other pairs unchanged. **Predictive update -- traces:** After transition with positive surprise (observed > predicted), confidence trace increases. After transition with negative surprise (observed < predicted), frustration trace increases. **Predictive update -- error in trace_data:** trace_data contains `"prediction"` key with context, predicted_features, observed_features, error values. **last_observation lifecycle:** After transition, `new_state.last_observation` equals the post-action observation passed to transition. **Multi-step:** Run 3 transitions in sequence. Verify memory converges, traces accumulate, last_observation chains correctly. **Termination:** Energy at exactly 0 -> terminated=True, reason="energy_depleted". Energy > 0 -> terminated=False. |

**Estimated tests:** 12-15

**Acceptance criteria:**
- Transition produces valid `TransitionResult`
- First step ($t=0$): predictive update is skipped, `last_observation` is populated
- Subsequent steps: memory, traces, and modulation state all update correctly
- Energy and buffer behavior identical to System A
- `trace_data["prediction"]` contains all expected fields

---

## Phase 5 -- Integration and Registration

---

### WP7 -- Plugin Registration, Experiment Config, and Integration Tests

**Goal:** Wire System C into the AXIS framework so it can be run from the CLI,
and validate end-to-end behavior including the reduction property.

**Files to create / modify:**

| File | Action |
|---|---|
| `experiments/configs/system-c-baseline.yaml` | Create. Full experiment config as specified in engineering spec Section 6.2. `system_type: "system_c"`, all prediction parameters explicit. |
| `setup.cfg` or `pyproject.toml` | Modify. Add `system_c = "axis.systems.system_c:register"` to `axis.plugins` entry point group. |

**Tests to create:**

| Test file | Test cases |
|---|---|
| `tests/systems/system_c/test_registration.py` | `register()` adds `"system_c"` to `registered_system_types()`. Factory creates a valid `SystemC` instance from a config dict. Double-registration is idempotent (no error). |
| `tests/systems/system_c/test_reduction.py` | **Single-step reduction:** With $\lambda_+ = \lambda_- = 0$ and fresh state (zero traces), `SystemC.decide()` produces the same action as `SystemA.decide()` given identical state, observation, and RNG seed. Test with 5 different energy levels and argmax selection. **Multi-step reduction:** 10 steps with $\lambda_+ = \lambda_- = 0$, argmax. Identical action sequences and energy trajectories as System A. Follow the pattern from `tests/systems/system_aw/test_reduction.py`. **Energy trajectory:** After 10 reduction steps, System C energy matches System A energy within tolerance. |
| `tests/systems/system_c/test_episode.py` | **Smoke test:** Construct `SystemC` with default config. Run a 50-step loop: `decide()` -> build `ActionOutcome` -> `transition()`. No crashes, no NaN. Vitality stays in [0, 1]. **Trace accumulation:** After 50 steps, at least some trace entries are non-zero (the agent has learned something). **Memory convergence:** After 50 steps, at least some predictive memory entries differ from zero (expectations have been formed). **Prediction active:** After 20+ steps, `decision_data["prediction"]["modulated_scores"]` differs from `decision_data["drive"]["action_contributions"]` for at least one step (prediction is actually influencing behavior). |
| `tests/systems/system_c/test_experiment_config.py` | YAML config loads without error. Parsed config matches expected types. Config round-trips through `SystemCConfig` constructor. |

**Estimated tests:** 10-14

**Acceptance criteria:**
- `axis experiments run experiments/configs/system-c-baseline.yaml` runs without error (manual verification)
- Reduction test passes: System C == System A when prediction disabled
- Full episode completes with observable prediction activity
- Plugin registration works through entry point mechanism

---

## Phase 6 -- Visualization and Documentation

---

### WP8 -- Visualization Adapter and Documentation

**Goal:** Add a visualization adapter for System C and update documentation
to reflect the three new kit packages and the new system.

**Files to create:**

| File | Contents |
|---|---|
| `src/axis/systems/system_c/visualization.py` | `SystemCVisualizationAdapter` following the System A adapter pattern. Extracts prediction-specific data from step traces for rendering: context index, frustration/confidence for selected action, modulation factor, prediction error. Registers via `register_system_visualization("system_c", ...)`. |

**Documentation updates:**

| File | Change |
|---|---|
| `README.md` | Add System C to the systems table. Update test count. |
| `docs/manuals/axis-overview.md` | Add System C to system descriptions, mention predictive modulation. |
| `docs/construction-kit/index.md` | Move prediction, traces, modulation from "Phase 2 placeholders" to the active component catalog table with descriptions. |
| `docs/construction-kit/prediction.md` | Create. Document `extract_predictive_features`, `encode_context`, `PredictiveMemory`, `compute_prediction_error` with formulas and usage examples. |
| `docs/construction-kit/traces.md` | Create. Document `TraceState`, `update_traces` with EMA formulas and usage examples. |
| `docs/construction-kit/modulation.md` | Create. Document `compute_modulation`, `modulate_action_scores` with exponential formula and usage examples. |
| `mkdocs.yml` | Add the 3 new construction kit pages to the nav. |

**Tests to create:**

| Test file | Test cases |
|---|---|
| `tests/systems/system_c/test_visualization.py` | Adapter registers successfully. Adapter extracts prediction data from a step trace dict without error. |

**Estimated tests:** 3-5

**Acceptance criteria:**
- Visualization adapter renders without error for a System C episode
- All three new kit packages documented with formulas, signatures, and examples
- Construction kit index table updated (no more "Phase 2" placeholders)
- MkDocs builds without errors

---

## Summary

| WP | Phase | New modules | New test files | Est. tests |
|---|---|---|---|---|
| WP1 | 1 | 5 (prediction pkg) | 4 | 18-22 |
| WP2 | 1 | 3 (traces pkg) | 2 | 10-12 |
| WP3 | 1 | 2 (modulation pkg) | 1 | 10-12 |
| WP4 | 2 | 0 (test-only) | 1 + 1 update | 5-7 |
| WP5 | 3 | 4 (system_c core) + 1 builder | 4 | 15-18 |
| WP6 | 4 | 1 (transition) | 1 | 12-15 |
| WP7 | 5 | 1 config + 1 entry point | 4 | 10-14 |
| WP8 | 6 | 1 (visualization) + 6 docs | 1 | 3-5 |
| **Total** | | **17 modules + 6 docs** | **19 test files** | **83-105** |
