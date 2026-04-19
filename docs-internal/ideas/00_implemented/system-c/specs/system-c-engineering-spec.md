# System C -- Engineering Specification

## Predictive Action Modulation on the AXIS SDK and Construction Kit

**Status:** Draft  
**Based on:** `docs-internal/ideas/system-c/detailed-draft.md` (consolidated model)  
**Target version:** v0.3.0  
**Date:** 2026-04-15

---

## 1. Purpose

This document specifies the concrete implementation of System C on the AXIS SDK
and Construction Kit. It maps every mathematical component from the detailed
draft to a Python module, class, or function -- with exact signatures, types, and
file locations.

System C is the first single-drive predictive agent. It extends System A by
inserting a prediction-based modulation factor into the hunger action projection:

$$
\psi_C(a) = d_H(t) \cdot \phi_H(a, u_t) \cdot \mu_H(s_t, a)
$$

where $\mu_H$ encodes learned action reliability from retrospective prediction
error. When prediction is disabled ($\lambda_+ = \lambda_- = 0$), System C
reduces exactly to System A.

---

## 2. Scope

### In scope

- Three new Construction Kit subpackages: `prediction`, `traces`, `modulation`
- New system package: `systems/system_c/`
- YAML experiment config for System C
- Plugin registration
- Unit tests for all new components
- Visualization adapter

### Out of scope

- Multi-drive prediction (System C+W) -- future work
- Planning or multi-step rollouts
- Changes to existing System A or A+W code
- Changes to SDK protocols or framework orchestration

---

## 3. Component Map

This table maps each mathematical element from the detailed draft to a concrete
implementation artifact.

| Math symbol | Role | Implementation | Location |
|---|---|---|---|
| $u_t$ | Observation | `Observation` (reuse) | `construction_kit/observation/types.py` |
| $S(\cdot)$ | Sensor | `VonNeumannSensor` (reuse) | `construction_kit/observation/sensor.py` |
| $d_H(t)$ | Drive activation | `HungerDrive` (reuse) | `construction_kit/drives/hunger.py` |
| $\phi_H(a, u_t)$ | Action projection | `HungerDrive.compute()` (reuse) | `construction_kit/drives/hunger.py` |
| $\pi(\psi_C)$ | Policy | `SoftmaxPolicy` (reuse) | `construction_kit/policy/softmax.py` |
| $e_t$ | Energy | `clip_energy`, `compute_vitality` (reuse) | `construction_kit/energy/functions.py` |
| $m_t$ | Observation buffer | `ObservationBuffer` (reuse) | `construction_kit/memory/` |
| $\Omega(u_t) \to y_t$ | Predictive feature extraction | `extract_predictive_features()` | `construction_kit/prediction/features.py` **NEW** |
| $C(y_t) \to s_t$ | Context encoding | `encode_context()` | `construction_kit/prediction/context.py` **NEW** |
| $q_t(s, a)$ | Predictive memory | `PredictiveMemory` | `construction_kit/prediction/memory.py` **NEW** |
| $\delta_t^+, \delta_t^-$ | Signed prediction error | `compute_prediction_error()` | `construction_kit/prediction/error.py` **NEW** |
| $\varepsilon_t^+, \varepsilon_t^-$ | Scalar aggregation | `aggregate_prediction_error()` | `construction_kit/prediction/error.py` **NEW** |
| $f_t(s, a)$ | Frustration trace | `TraceState` | `construction_kit/traces/state.py` **NEW** |
| $c_t(s, a)$ | Confidence trace | `TraceState` | `construction_kit/traces/state.py` **NEW** |
| $z_t = (f_t, c_t)$ | Trace update | `update_traces()` | `construction_kit/traces/update.py` **NEW** |
| $\mu_H(s_t, a)$ | Action modulation | `compute_modulation()` | `construction_kit/modulation/modulation.py` **NEW** |
| -- | System config | `SystemCConfig` | `systems/system_c/config.py` **NEW** |
| -- | Agent state | `AgentStateC` | `systems/system_c/types.py` **NEW** |
| -- | System class | `SystemC` | `systems/system_c/system.py` **NEW** |
| -- | Transition | `SystemCTransition` | `systems/system_c/transition.py` **NEW** |

---

## 4. New Construction Kit Components

All new kit components follow existing conventions:

- Frozen Pydantic models for state
- Pure functions for stateless computations
- Imports only from `axis.sdk` and other `construction_kit` modules
- No framework or system imports

### 4.1 Prediction Package (`construction_kit/prediction/`)

#### 4.1.1 `features.py` -- Predictive Feature Extraction

Implements $\Omega(u_t) \to y_t$. Extracts the 5 resource values from an
`Observation`.

```python
def extract_predictive_features(observation: Observation) -> tuple[float, ...]:
    """Extract predictive feature vector y_t from observation u_t.

    For the hunger-centered instantiation, y_t contains the 5 local
    resource values in canonical order: (center, up, down, left, right).

    Returns:
        5-element tuple of resource values in [0, 1].
    """
```

This function is deliberately simple -- it exists as the explicit abstraction
boundary $\Omega$ so that future systems can swap in a different feature
extractor without touching the rest of the predictive pipeline.

#### 4.1.2 `context.py` -- Context Encoding

Implements $C(y_t) \to s_t$ with binary quantization.

```python
def encode_context(
    features: tuple[float, ...],
    *,
    threshold: float = 0.5,
) -> int:
    """Encode predictive features into a discrete context index.

    Binary thresholding: each feature is mapped to 0 (below threshold)
    or 1 (at or above threshold). The 5-bit result is packed into an
    integer in [0, 31].

    Context index layout (MSB to LSB):
        bit 4: center, bit 3: up, bit 2: down, bit 1: left, bit 0: right

    Args:
        features: Predictive feature vector y_t (5 elements).
        threshold: Binary threshold (default 0.5).

    Returns:
        Integer context index in [0, 31].
    """
```

#### 4.1.3 `memory.py` -- Predictive Memory

Implements $q_t(s, a)$ as an immutable state object.

```python
from pydantic import BaseModel, ConfigDict


class PredictiveMemory(BaseModel):
    """Predictive memory q_t: expected next features per (context, action).

    Stores expectations as a flat tuple of entries, keyed by
    (context_index, action_name). Immutable -- updates return a new
    instance.

    Internal layout: dict-like storage serialized as a tuple of
    ((context, action), expected_features) pairs for Pydantic
    compatibility.
    """
    model_config = ConfigDict(frozen=True)

    entries: tuple[tuple[tuple[int, str], tuple[float, ...]], ...] = ()
    feature_dim: int = 5


def create_predictive_memory(
    *,
    num_contexts: int = 32,
    actions: tuple[str, ...] = ("up", "down", "left", "right", "consume", "stay"),
    feature_dim: int = 5,
) -> PredictiveMemory:
    """Create an initial predictive memory with all expectations at zero.

    Returns:
        PredictiveMemory with q_0(s, a) = (0, ..., 0) for all (s, a).
    """


def get_prediction(
    memory: PredictiveMemory,
    context: int,
    action: str,
) -> tuple[float, ...]:
    """Retrieve the expected features for a (context, action) pair.

    Returns:
        Expected feature vector y_hat. Zero vector if pair not found.
    """


def update_predictive_memory(
    memory: PredictiveMemory,
    context: int,
    action: str,
    observed_features: tuple[float, ...],
    *,
    learning_rate: float,
) -> PredictiveMemory:
    """Update predictive memory for one (context, action) pair.

    q_{t+1}(s_t, a_t) = (1 - eta_q) * q_t(s_t, a_t) + eta_q * y_{t+1}

    All other pairs remain unchanged.

    Args:
        memory: Current predictive memory state.
        context: Active context index s_t.
        action: Selected action a_t.
        observed_features: Realized feature vector y_{t+1}.
        learning_rate: eta_q in (0, 1].

    Returns:
        New PredictiveMemory with updated entry.
    """
```

**Implementation note:** The entries are stored as a sorted tuple for Pydantic
frozen-model compatibility. Internally, the functions should reconstruct a dict
for lookup, update, and re-serialize. This matches the `WorldModelState` pattern
in the existing memory package.

#### 4.1.4 `error.py` -- Prediction Error

Implements signed prediction error decomposition and scalar aggregation.

```python
class PredictionError(BaseModel):
    """Signed prediction error decomposition."""
    model_config = ConfigDict(frozen=True)

    positive: tuple[float, ...]   # delta_t^+ per feature dimension
    negative: tuple[float, ...]   # delta_t^- per feature dimension
    scalar_positive: float        # epsilon_t^+ (aggregated)
    scalar_negative: float        # epsilon_t^- (aggregated)


def compute_prediction_error(
    predicted: tuple[float, ...],
    observed: tuple[float, ...],
    *,
    positive_weights: tuple[float, ...] = (0.5, 0.125, 0.125, 0.125, 0.125),
    negative_weights: tuple[float, ...] = (0.5, 0.125, 0.125, 0.125, 0.125),
) -> PredictionError:
    """Compute signed prediction error with scalar aggregation.

    Component-wise:
        delta_t^+ = max(y_{t+1} - y_hat_{t+1}, 0)
        delta_t^- = max(y_hat_{t+1} - y_{t+1}, 0)

    Scalar aggregation:
        epsilon_t^+ = sum_j(w_j^+ * delta_t_j^+)
        epsilon_t^- = sum_j(w_j^- * delta_t_j^-)

    Args:
        predicted: Expected feature vector y_hat_{t+1}.
        observed: Realized feature vector y_{t+1}.
        positive_weights: Aggregation weights w_j^+ (must sum to 1).
        negative_weights: Aggregation weights w_j^- (must sum to 1).

    Returns:
        PredictionError with component-wise and scalar errors.
    """
```

#### 4.1.5 `__init__.py`

```python
"""Predictive memory and prediction error processing.

Provides:
- extract_predictive_features: Omega(u_t) -> y_t
- encode_context: C(y_t) -> s_t
- PredictiveMemory: q_t(s, a) expectation store
- compute_prediction_error: signed error with aggregation
"""
```

### 4.2 Traces Package (`construction_kit/traces/`)

#### 4.2.1 `state.py` -- Trace State

Implements $z_t = (f_t, c_t)$ as an immutable state model.

```python
class TraceState(BaseModel):
    """Dual-trace state: frustration f_t and confidence c_t.

    Both traces are non-negative functions over (context, action) pairs.
    Stored as sorted tuple of ((context, action), value) pairs.
    """
    model_config = ConfigDict(frozen=True)

    frustration: tuple[tuple[tuple[int, str], float], ...] = ()
    confidence: tuple[tuple[tuple[int, str], float], ...] = ()


def create_trace_state() -> TraceState:
    """Create initial trace state with all values at zero.

    f_0(s, a) = 0, c_0(s, a) = 0 for all (s, a).
    This ensures mu_H = 1 at t=0 (System A behavior).
    """


def get_frustration(state: TraceState, context: int, action: str) -> float:
    """Retrieve f_t(s, a). Returns 0.0 if pair not found."""


def get_confidence(state: TraceState, context: int, action: str) -> float:
    """Retrieve c_t(s, a). Returns 0.0 if pair not found."""
```

#### 4.2.2 `update.py` -- Trace Update

```python
def update_traces(
    state: TraceState,
    context: int,
    action: str,
    scalar_positive: float,
    scalar_negative: float,
    *,
    frustration_rate: float,
    confidence_rate: float,
) -> TraceState:
    """Update frustration and confidence traces for one (context, action) pair.

    f_{t+1}(s_t, a_t) = (1 - eta_f) * f_t(s_t, a_t) + eta_f * epsilon_t^-
    c_{t+1}(s_t, a_t) = (1 - eta_c) * c_t(s_t, a_t) + eta_c * epsilon_t^+

    All other pairs remain unchanged.

    Args:
        state: Current trace state.
        context: Active context index s_t.
        action: Selected action a_t.
        scalar_positive: Aggregated positive error epsilon_t^+.
        scalar_negative: Aggregated negative error epsilon_t^-.
        frustration_rate: eta_f.
        confidence_rate: eta_c.

    Returns:
        New TraceState with updated entries.
    """
```

#### 4.2.3 `__init__.py`

```python
"""Trace dynamics -- frustration and confidence accumulation.

Provides:
- TraceState: dual-trace state z_t = (f_t, c_t)
- update_traces: EMA update for one (context, action) pair
"""
```

### 4.3 Modulation Package (`construction_kit/modulation/`)

#### 4.3.1 `modulation.py` -- Action Score Modulation

Implements $\mu_H(s_t, a)$.

```python
def compute_modulation(
    frustration: float,
    confidence: float,
    *,
    positive_sensitivity: float,
    negative_sensitivity: float,
    modulation_min: float,
    modulation_max: float,
) -> float:
    """Compute action modulation factor from frustration and confidence.

    mu_tilde = exp(lambda_+ * c - lambda_- * f)
    mu = clip(mu_tilde, mu_min, mu_max)

    Args:
        frustration: f_t(s, a) for this context-action pair.
        confidence: c_t(s, a) for this context-action pair.
        positive_sensitivity: lambda_+ (>= 0).
        negative_sensitivity: lambda_- (>= 0).
        modulation_min: mu_min (> 0, <= 1).
        modulation_max: mu_max (>= 1).

    Returns:
        Modulation factor mu in [mu_min, mu_max].
    """


def modulate_action_scores(
    action_scores: tuple[float, ...],
    context: int,
    actions: tuple[str, ...],
    trace_state: TraceState,
    *,
    positive_sensitivity: float,
    negative_sensitivity: float,
    modulation_min: float,
    modulation_max: float,
) -> tuple[float, ...]:
    """Apply prediction-based modulation to all action scores.

    For each action a:
        modulated_score(a) = base_score(a) * mu(context, a)

    This is the main entry point for the modulation step.

    Args:
        action_scores: Baseline scores from the drive, one per action.
        context: Current context index s_t.
        actions: Action names in the same order as action_scores.
        trace_state: Current trace state z_t.
        positive_sensitivity: lambda_+.
        negative_sensitivity: lambda_-.
        modulation_min: mu_min.
        modulation_max: mu_max.

    Returns:
        Modulated action scores, same length as input.
    """
```

#### 4.3.2 `__init__.py`

```python
"""Action score modulation from prediction-derived traces.

Provides:
- compute_modulation: single (context, action) modulation factor
- modulate_action_scores: batch modulation across all actions
"""
```

---

## 5. System C Package (`systems/system_c/`)

### 5.1 File Layout

```
src/axis/systems/system_c/
    __init__.py           # exports, register()
    config.py             # SystemCConfig, PredictionConfig
    types.py              # AgentStateC
    system.py             # SystemC (SystemInterface)
    transition.py         # SystemCTransition (TransitionInterface)
    visualization.py      # SystemCVisualizationAdapter
```

### 5.2 `config.py` -- Configuration

```python
class PredictionConfig(BaseModel):
    """System C prediction parameters."""
    model_config = ConfigDict(frozen=True)

    # Predictive memory
    memory_learning_rate: float = 0.3       # eta_q
    context_threshold: float = 0.5          # binary quantization threshold

    # Traces
    frustration_rate: float = 0.2           # eta_f
    confidence_rate: float = 0.15           # eta_c

    # Modulation
    positive_sensitivity: float = 1.0       # lambda_+
    negative_sensitivity: float = 1.5       # lambda_-
    modulation_min: float = 0.3             # mu_min
    modulation_max: float = 2.0             # mu_max

    # Aggregation weights (center, up, down, left, right)
    positive_weights: tuple[float, ...] = (0.5, 0.125, 0.125, 0.125, 0.125)
    negative_weights: tuple[float, ...] = (0.5, 0.125, 0.125, 0.125, 0.125)


class SystemCConfig(BaseModel):
    """Complete System C configuration."""
    model_config = ConfigDict(frozen=True)

    agent: AgentConfig
    policy: PolicyConfig
    transition: TransitionConfig
    prediction: PredictionConfig = PredictionConfig()
```

**Design notes:**

- `PredictionConfig` contains all parameters from Section 15 of the detailed
  draft. All have defaults matching the resolved values.
- `SystemCConfig` extends `SystemAConfig` with one additional section. The
  `agent`, `policy`, and `transition` sections are identical to System A.
- `prediction` defaults to the resolved parameter set. This means a System C
  YAML config with no `prediction:` section runs with the spec defaults.

### 5.3 `types.py` -- Agent State

```python
class AgentStateC(BaseModel):
    """System C agent state.

    Extends System A's state with predictive memory, trace state,
    and the last observation (needed for prediction error computation
    in transition).
    Position is NOT part of agent state (world-owned).
    """
    model_config = ConfigDict(frozen=True)

    energy: float = Field(..., ge=0)
    observation_buffer: ObservationBuffer
    predictive_memory: PredictiveMemory
    trace_state: TraceState
    last_observation: Observation | None = None
```

The `last_observation` field stores the post-action observation from the
previous step. It serves as the pre-action observation for the current step's
predictive update cycle. At $t=0$, it is `None`, which signals the transition
to skip the predictive update (no prior action-outcome pair to evaluate).

### 5.4 `system.py` -- System Class

`SystemC` implements `SystemInterface`. It composes kit components via plain
Python construction, following the exact same pattern as `SystemA`.

```python
class SystemC:
    """System C: hunger-driven agent with predictive action modulation.

    Extends System A by inserting a prediction-based modulation layer
    between drive output and policy input. When prediction is disabled
    (lambda_+ = lambda_- = 0), behavior is identical to System A.
    """

    def __init__(self, config: SystemCConfig) -> None:
        self._config = config
        self._sensor = VonNeumannSensor()
        self._drive = HungerDrive(
            consume_weight=config.policy.consume_weight,
            stay_suppression=config.policy.stay_suppression,
            max_energy=config.agent.max_energy,
        )
        self._policy = SoftmaxPolicy(
            temperature=config.policy.temperature,
            selection_mode=config.policy.selection_mode,
        )
        self._transition = SystemCTransition(
            config=config,
        )
```

#### `decide()` Pipeline

The decide method implements the 6-step pipeline from Section 11 of the
detailed draft. Steps 1-2 are identical to System A. Steps 3-4 are new.
Step 5 feeds the modulated scores to the existing policy.

```
Step 1: Perception       u_t = sensor.observe(world_view, position)
Step 2: Drive            drive_output = hunger_drive.compute(state, u_t)
                         -> d_H(t), phi_H(a, u_t)
Step 3: Feature + Context  y_t = extract_predictive_features(u_t)
                           s_t = encode_context(y_t)
Step 4: Modulation       modulated_scores = modulate_action_scores(
                             drive_output.action_contributions,
                             s_t, actions, state.trace_state, ...)
Step 5: Policy           policy_result = policy.select(modulated_scores, u_t, rng)
Step 6: Return           DecideResult(action, decision_data)
```

```python
    def decide(
        self,
        world_view: Any,
        agent_state: Any,
        rng: np.random.Generator,
    ) -> DecideResult:
        # Step 1: Perception
        observation = self._sensor.observe(
            world_view, world_view.agent_position)

        # Step 2: Drive activation + action projection
        drive_output = self._drive.compute(agent_state, observation)

        # Step 3: Predictive feature extraction + context encoding
        features = extract_predictive_features(observation)
        context = encode_context(
            features, threshold=self._config.prediction.context_threshold)

        # Step 4: Prediction-based modulation
        modulated_scores = modulate_action_scores(
            action_scores=drive_output.action_contributions,
            context=context,
            actions=self.action_space(),
            trace_state=agent_state.trace_state,
            positive_sensitivity=self._config.prediction.positive_sensitivity,
            negative_sensitivity=self._config.prediction.negative_sensitivity,
            modulation_min=self._config.prediction.modulation_min,
            modulation_max=self._config.prediction.modulation_max,
        )

        # Step 5: Policy (softmax over modulated scores)
        policy_result = self._policy.select(
            modulated_scores, observation, rng)

        # Step 6: Decision data for trace
        decision_data = {
            "observation": observation.model_dump(),
            "drive": {
                "activation": drive_output.activation,
                "action_contributions": drive_output.action_contributions,
            },
            "prediction": {
                "context": context,
                "features": features,
                "modulated_scores": modulated_scores,
            },
            "policy": policy_result.policy_data,
        }

        return DecideResult(
            action=policy_result.action,
            decision_data=decision_data,
        )
```

**Key difference from System A:** Between steps 2 and 5, the raw
`action_contributions` are multiplied element-wise by the modulation factor
$\mu_H(s_t, a)$. The policy sees `modulated_scores` instead of raw drive
output.

#### Other `SystemInterface` methods

```python
    def system_type(self) -> str:
        return "system_c"

    def action_space(self) -> tuple[str, ...]:
        return ("up", "down", "left", "right", "consume", "stay")

    def initialize_state(self) -> AgentStateC:
        return AgentStateC(
            energy=self._config.agent.initial_energy,
            observation_buffer=ObservationBuffer(
                entries=(), capacity=self._config.agent.buffer_capacity,
            ),
            predictive_memory=create_predictive_memory(),
            trace_state=create_trace_state(),
        )

    def vitality(self, agent_state: Any) -> float:
        return agent_state.energy / self._config.agent.max_energy

    def action_handlers(self) -> dict[str, Any]:
        from axis.systems.construction_kit.types.actions import handle_consume
        return {"consume": handle_consume}

    def observe(self, world_view: Any, position: Any) -> Any:
        return self._sensor.observe(world_view, position)

    def action_context(self) -> dict[str, Any]:
        return {"max_consume": self._config.transition.max_consume}
```

### 5.5 `transition.py` -- Transition Function

`SystemCTransition` implements `TransitionInterface`. It extends System A's
transition with the predictive update cycle (steps 11.8--11.11 from the
detailed draft).

The transition executes after the framework applies the action.
At this point, the system knows the chosen action $a_t$ and sees the new
observation $u_{t+1}$. It also has the pre-action observation stored in the
decision data from `decide()`.

```python
class SystemCTransition:
    """Transition function for System C.

    Extends System A's transition with:
    - Phase 4: Energy update (same as System A)
    - Phase 5: Observation buffer update (same as System A)
    - Phase 6: Predictive update cycle (NEW)
        - 6a: Extract post-action features y_{t+1}
        - 6b: Retrieve prediction y_hat_{t+1}
        - 6c: Compute signed prediction error
        - 6d: Update traces
        - 6e: Update predictive memory
    - Phase 7: Termination check (same as System A)
    """

    def __init__(self, *, config: SystemCConfig) -> None:
        self._config = config

    def transition(
        self,
        agent_state: AgentStateC,
        action_outcome: ActionOutcome,
        observation: Observation,
        *,
        timestep: int = 0,
    ) -> TransitionResult:
```

#### Transition Pipeline Detail

```
Phase 4: Energy update
    cost = get_action_cost(action, move_cost=..., stay_cost=...,
                           custom_costs={"consume": consume_cost})
    gain = energy_gain_factor * resource_consumed
    new_energy = clip_energy(energy - cost + gain, max_energy)

Phase 5: Observation buffer update
    new_buffer = update_observation_buffer(buffer, observation, timestep)

Phase 6: Predictive update cycle (skipped if last_observation is None)
    6a: y_{t+1} = extract_predictive_features(observation)
    6b: Retrieve pre-action context and prediction:
        y_t = extract_predictive_features(agent_state.last_observation)
        s_t = encode_context(y_t)
        y_hat = get_prediction(memory, s_t, action)
    6c: error = compute_prediction_error(y_hat, y_{t+1},
                    positive_weights=..., negative_weights=...)
    6d: new_traces = update_traces(trace_state, s_t, action,
                        error.scalar_positive, error.scalar_negative,
                        frustration_rate=..., confidence_rate=...)
    6e: new_memory = update_predictive_memory(memory, s_t, action,
                        y_{t+1}, learning_rate=...)

Phase 7: Build new state (store observation as last_observation)
    new_state = AgentStateC(
        energy=new_energy,
        observation_buffer=new_buffer,
        predictive_memory=new_memory,
        trace_state=new_traces,
        last_observation=observation,
    )

Phase 8: Termination check
    terminated = new_energy <= 0.0
```

**Critical design point:** The transition needs the **pre-action** observation
to compute the context $s_t = C(\Omega(u_t))$. This observation was computed in
`decide()` but is not available in `transition()` directly.

The framework runner (`src/axis/framework/runner.py`) does **not** forward
`decision_data` into the `ActionOutcome` -- `action_outcome.data` contains
only world-level data from the action handler. Therefore, the agent state
carries the previous observation via `last_observation: Observation | None`.

At step $t$, `last_observation` holds the post-action observation from the
previous step (= the pre-action observation for step $t$). The transition
reads it, uses it for prediction error computation, then stores the current
post-action observation as `last_observation` in the new state.

At $t = 0$, `last_observation` is `None`. The predictive update is skipped
entirely -- no prediction error, no trace update, no memory update. The agent
starts with $\mu_H = 1$ everywhere (System A behavior).

#### Trace Data

The transition emits trace data for visualization and debugging:

```python
trace_data = {
    # Energy (same as System A)
    "energy_before": ...,
    "energy_after": ...,
    "energy_delta": ...,
    "action_cost": ...,
    "energy_gain": ...,
    # Observation buffer (same as System A)
    "buffer_entries_before": ...,
    "buffer_entries_after": ...,
    # Prediction (new)
    "prediction": {
        "context": s_t,
        "predicted_features": y_hat,
        "observed_features": y_{t+1},
        "error_positive": epsilon_t_plus,
        "error_negative": epsilon_t_minus,
        "frustration": f_t(s_t, a_t),   # after update
        "confidence": c_t(s_t, a_t),     # after update
        "modulation_factor": mu,          # the mu that was used in decide
    },
}
```

### 5.6 `__init__.py` -- Registration

```python
"""System C -- hunger-driven agent with predictive action modulation."""

from axis.systems.construction_kit.types.actions import handle_consume
from axis.systems.system_c.config import SystemCConfig
from axis.systems.system_c.system import SystemC

__all__ = [
    "SystemC",
    "SystemCConfig",
    "handle_consume",
]


def register() -> None:
    """Register system_c: system factory + visualization adapter."""
    from axis.framework.registry import register_system, registered_system_types

    if "system_c" not in registered_system_types():

        def _factory(cfg: dict) -> SystemC:
            return SystemC(SystemCConfig(**cfg))

        register_system("system_c", _factory)

    from axis.visualization.registry import registered_system_visualizations

    if "system_c" not in registered_system_visualizations():
        try:
            import axis.systems.system_c.visualization  # noqa: F401
        except ImportError:
            pass
```

### 5.7 `visualization.py` -- Visualization Adapter

The visualization adapter follows the same pattern as System A's adapter.
It additionally surfaces prediction-specific data (context, traces,
modulation factor) in the step trace rendering. Detailed specification of
the visualization adapter is deferred to implementation time -- it is not
architecturally critical.

---

## 6. Plugin Registration

System C must be registered as a plugin so the framework discovers it.

### 6.1 Entry Point

In `pyproject.toml` / `setup.cfg`, add to the `axis.plugins` entry point group:

```toml
[project.entry-points."axis.plugins"]
system_a = "axis.systems.system_a:register"
system_aw = "axis.systems.system_aw:register"
system_b = "axis.systems.system_b:register"
system_c = "axis.systems.system_c:register"    # NEW
```

### 6.2 Experiment Config

```yaml
# experiments/configs/system-c-baseline.yaml
system_type: "system_c"

general:
  seed: 42

execution:
  max_steps: 200

world:
  grid_width: 10
  grid_height: 10
  obstacle_density: 0.1
  resource_regen_rate: 0.05

system:
  agent:
    initial_energy: 30.0
    max_energy: 50.0
    buffer_capacity: 10
  policy:
    selection_mode: "sample"
    temperature: 1.0
    consume_weight: 2.0
    stay_suppression: 0.5
  transition:
    move_cost: 1.0
    consume_cost: 0.5
    stay_cost: 0.5
    max_consume: 1.0
    energy_gain_factor: 10.0
  prediction:
    memory_learning_rate: 0.3
    context_threshold: 0.5
    frustration_rate: 0.2
    confidence_rate: 0.15
    positive_sensitivity: 1.0
    negative_sensitivity: 1.5
    modulation_min: 0.3
    modulation_max: 2.0

num_episodes_per_run: 5
```

Since all `prediction` fields have defaults, a minimal config can omit the
entire section:

```yaml
system_type: "system_c"
# ... (identical to a system_a config)
# prediction section omitted => uses spec defaults
```

---

## 7. Dependency Graph

```
axis.sdk                         (no changes)
  ^
  |
construction_kit.observation     (no changes)
construction_kit.drives          (no changes)
construction_kit.policy          (no changes)
construction_kit.arbitration     (no changes -- not used by System C)
construction_kit.energy          (no changes)
construction_kit.memory          (no changes)
construction_kit.types           (no changes)
construction_kit.prediction      NEW -- imports: sdk, observation
construction_kit.traces          NEW -- imports: sdk only
construction_kit.modulation      NEW -- imports: traces
  ^
  |
systems.system_c                 NEW -- imports: sdk, construction_kit
```

All new kit packages follow the dependency rule: **Kit -> SDK only**,
with intra-kit imports permitted (modulation imports from traces).

---

## 8. Testing Strategy

### 8.1 Unit Tests -- New Kit Components

Each new kit module gets a dedicated test file:

| Test file | What it tests |
|---|---|
| `tests/construction_kit/prediction/test_features.py` | `extract_predictive_features` extracts correct 5-tuple from `Observation` |
| `tests/construction_kit/prediction/test_context.py` | `encode_context` binary encoding: known inputs -> known bit patterns; threshold edge cases |
| `tests/construction_kit/prediction/test_memory.py` | `create_predictive_memory` returns zeros; `get_prediction` returns zeros for unseen pairs; `update_predictive_memory` EMA correctness; immutability |
| `tests/construction_kit/prediction/test_error.py` | `compute_prediction_error` signed decomposition; aggregation weight correctness; zero-error case |
| `tests/construction_kit/traces/test_state.py` | `create_trace_state` returns zeros; getters return 0 for unseen pairs |
| `tests/construction_kit/traces/test_update.py` | `update_traces` EMA correctness; only updates the specified pair; immutability |
| `tests/construction_kit/modulation/test_modulation.py` | `compute_modulation` exponential formula; clipping at bounds; $\lambda=0$ gives $\mu=1$; `modulate_action_scores` preserves length |

### 8.2 Unit Tests -- System C

| Test file | What it tests |
|---|---|
| `tests/systems/system_c/test_config.py` | `PredictionConfig` defaults match spec values; `SystemCConfig` parses from dict; validation |
| `tests/systems/system_c/test_types.py` | `AgentStateC` frozen model; includes predictive_memory and trace_state |
| `tests/systems/system_c/test_system.py` | `SystemC` satisfies `SystemInterface`; `initialize_state` returns correct initial state; `system_type` returns `"system_c"`; `action_space` returns 6 actions |
| `tests/systems/system_c/test_decide.py` | Full decide pipeline: sensor -> drive -> modulate -> policy; modulated scores differ from raw when traces are non-zero; modulated scores equal raw when traces are zero |
| `tests/systems/system_c/test_transition.py` | Energy update; buffer update; prediction update cycle (memory, error, traces all updated); first-step skip (no previous observation) |
| `tests/systems/system_c/test_registration.py` | `register()` succeeds; factory creates `SystemC` instance |

### 8.3 Integration Tests

| Test file | What it tests |
|---|---|
| `tests/systems/system_c/test_reduction.py` | **Reduction to System A:** With $\lambda_+ = \lambda_- = 0$, System C produces identical action distributions to System A given the same state, observation, and RNG seed |
| `tests/systems/system_c/test_episode.py` | Full episode run: 200 steps, no crashes, vitality in [0,1], traces accumulate, memory updates observed in trace data |

### 8.4 Test Counts

Estimated new tests: ~60-80 across the above files.

---

## 9. Implementation Order

The implementation should proceed bottom-up: kit components first, system
composition second.

### Phase 1: Kit Components

1. `construction_kit/prediction/features.py` + tests
2. `construction_kit/prediction/context.py` + tests
3. `construction_kit/prediction/memory.py` + tests
4. `construction_kit/prediction/error.py` + tests
5. `construction_kit/prediction/__init__.py`
6. `construction_kit/traces/state.py` + tests
7. `construction_kit/traces/update.py` + tests
8. `construction_kit/traces/__init__.py`
9. `construction_kit/modulation/modulation.py` + tests
10. `construction_kit/modulation/__init__.py`

### Phase 2: System C

11. `systems/system_c/config.py` + tests
12. `systems/system_c/types.py` + tests
13. `systems/system_c/transition.py` + tests
14. `systems/system_c/system.py` + tests
15. `systems/system_c/__init__.py` + registration test
16. Reduction test (System C == System A when prediction off)
17. Full episode integration test

### Phase 3: Integration

18. `experiments/configs/system-c-baseline.yaml`
19. Plugin entry point registration
20. `systems/system_c/visualization.py`
21. Documentation updates (README, overview, construction kit docs)

---

## 10. Observation Passing: Resolved

The framework runner (`src/axis/framework/runner.py`) does **not** forward
`decision_data` into `action_outcome.data`. The `ActionOutcome` is constructed
entirely by the action handler, and `decision_data` is only stored in the
step trace for logging.

**Resolution:** The agent state carries a `last_observation: Observation | None`
field. During each transition, the current post-action observation is stored
as `last_observation` in the new state, making it available as the pre-action
observation for the next step's predictive update.

This is consistent with the framework's design intent: `decide()` produces an
action intent, `transition()` receives only the world-level outcome and a fresh
observation, and agent state is the sole mechanism for persisting data across
the two phases.

---

## 11. Parameter Reference

All parameters from Section 15 of the detailed draft, with their config
field names:

| Parameter | Symbol | Default | Config path |
|---|---|---|---|
| Memory learning rate | $\eta_q$ | `0.3` | `system.prediction.memory_learning_rate` |
| Context threshold | -- | `0.5` | `system.prediction.context_threshold` |
| Frustration learning rate | $\eta_f$ | `0.2` | `system.prediction.frustration_rate` |
| Confidence learning rate | $\eta_c$ | `0.15` | `system.prediction.confidence_rate` |
| Positive sensitivity | $\lambda_+$ | `1.0` | `system.prediction.positive_sensitivity` |
| Negative sensitivity | $\lambda_-$ | `1.5` | `system.prediction.negative_sensitivity` |
| Modulation floor | $\mu_{\min}$ | `0.3` | `system.prediction.modulation_min` |
| Modulation ceiling | $\mu_{\max}$ | `2.0` | `system.prediction.modulation_max` |
| Positive agg. weights | $w_j^+$ | `(0.5, 0.125, 0.125, 0.125, 0.125)` | `system.prediction.positive_weights` |
| Negative agg. weights | $w_j^-$ | `(0.5, 0.125, 0.125, 0.125, 0.125)` | `system.prediction.negative_weights` |

System A parameters (`agent`, `policy`, `transition`) are inherited unchanged.

---

## 12. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Pydantic serialization overhead for large trace tables | Slow transitions for $32 \times 6 = 192$ entries | Profile; if needed, switch to a raw dict wrapper instead of tuple-of-tuples |
| Modulation dominates drive signal | Agent ignores perception | Conservative bounds ($[0.3, 2.0]$) already mitigate this; reduction test validates |
| Sparse context visitation | Some (context, action) pairs never learned | 32 contexts is small enough; 200-step episodes provide ~33 visits per context on average |
