# System A+W: Implementation Roadmap

## Metadata
- Project: AXIS -- Complex Mechanistic Systems Experiment
- Author: Oliver Grau
- Type: Implementation Roadmap
- Status: Draft v1.0
- Prerequisites: `01_System A+W Model.md`, `02_System A+W Worked Examples.md`

---

## 1. Scope

This document defines the work packages required to implement System A+W as a fully operational system type within the AXIS framework. All work packages are derived from the formal model specification in `01_System A+W Model.md`.

The implementation follows the existing System A architecture as a structural template. System A+W will be a **new, independent system type** (`system_aw`) -- it does not modify System A.

---

## 2. Guiding Principles

1. **One module per mathematical component.** Each section of the formal model maps to exactly one source file.
2. **No framework changes.** The SDK's `SystemInterface` protocol already supports multi-drive systems. All new code lives under `src/axis/systems/system_aw/`.
3. **Strict superset of System A.** When curiosity parameters are zeroed, System A+W must reproduce System A behavior exactly (Section 12 of the model).
4. **Test against worked examples.** Every test traces a calculation path from `02_System A+W Worked Examples.md`.
5. **Incremental delivery.** Each work package produces a testable artifact. Later packages build on earlier ones but never break them.

---

## 3. Target File Layout

```
src/axis/systems/system_aw/
├── __init__.py              # Package exports
├── config.py                # WP-1: SystemAWConfig (Pydantic)
├── types.py                 # WP-2: Internal data types (WorldModel, CuriosityDriveOutput, etc.)
├── sensor.py                # WP-3: Sensor (inherited from System A, re-exported or extended)
├── memory.py                # WP-3: Memory update (inherited)
├── world_model.py           # WP-4: Visit-count map (new)
├── drive_hunger.py          # WP-5: Hunger drive module (reuse from System A)
├── drive_curiosity.py       # WP-6: Curiosity drive module (new)
├── drive_arbitration.py     # WP-7: Dynamic weight functions (new)
├── policy.py                # WP-8: Softmax policy (inherited)
├── transition.py            # WP-9: Extended transition function (new)
├── actions.py               # WP-3: Consume handler (inherited)
├── system.py                # WP-10: SystemAW orchestrator (new)
└── visualization.py         # WP-12: Visualization adapter (new)

tests/systems/system_aw/
├── __init__.py
├── test_config.py           # WP-1
├── test_types.py            # WP-2
├── test_world_model.py      # WP-4
├── test_drive_hunger.py     # WP-5
├── test_drive_curiosity.py  # WP-6
├── test_drive_arbitration.py # WP-7
├── test_transition.py       # WP-9
├── test_system_aw.py        # WP-10
├── test_pipeline.py         # WP-10
├── test_reduction.py        # WP-11 (System A equivalence)
└── test_worked_examples.py  # WP-11 (numerical validation)

experiments/configs/
├── system-aw-baseline.yaml       # WP-13
├── system-aw-curiosity-sweep.yaml # WP-13
└── system-aw-exploration-demo.yaml # WP-13
```

---

## 4. Work Packages

---

### WP-1: Configuration Model

**Goal:** Define `SystemAWConfig` with all parameters from Model Section 11.

**Source:** `config.py`

**Details:**
- Extend the System A configuration structure with new sub-configs:
  - `CuriosityConfig`: `base_curiosity` ($\mu_C$), `spatial_sensory_balance` ($\alpha$), `explore_suppression` ($\lambda_{explore}$)
  - `ArbitrationConfig`: `hunger_weight_base` ($w_H^{base}$), `curiosity_weight_base` ($w_C^{base}$), `gating_sharpness` ($\gamma$)
- Compose into `SystemAWConfig` alongside inherited `AgentConfig`, `PolicyConfig`, `TransitionConfig`
- Frozen Pydantic v2 models with validators (e.g., $\alpha \in [0, 1]$, $\gamma > 0$, $w_H^{base} \in (0, 1]$)
- Defaults match Section 11.2: $\mu_C = 1.0$, $\alpha = 0.5$, $\lambda_{explore} = 0.3$, $w_H^{base} = 0.3$, $w_C^{base} = 1.0$, $\gamma = 2.0$

**Acceptance Criteria:**
- [ ] All parameters from Section 11 are representable
- [ ] Defaults match the specification
- [ ] Validators reject invalid domains
- [ ] Config instantiates from a dict (YAML-compatible)

**Dependencies:** None

---

### WP-2: Internal Data Types

**Goal:** Define the type vocabulary for System A+W.

**Source:** `types.py`

**Details:**
- Reuse from System A: `CellObservation`, `Observation`, `MemoryEntry`, `MemoryState`, `clip_energy`
- New types:
  - `WorldModelState`: encapsulates the visit-count map $w_t : \mathbb{Z}^2 \to \mathbb{N}_0$ and the relative position $\hat{p}_t$
  - `CuriosityDriveOutput`: activation $d_C$, per-direction novelty components ($\nu^{spatial}$, $\nu^{sensory}$, $\nu_{composite}$), per-action contributions
  - `DriveWeights`: $w_H(t)$, $w_C(t)$
  - `AgentStateAW`: extends `AgentState` with `world_model: WorldModelState` (which includes `relative_position` and `visit_counts`)
- All frozen Pydantic models

**Acceptance Criteria:**
- [ ] All types are immutable
- [ ] `AgentStateAW` composes energy + memory + world model
- [ ] Serializable (for trace logging)

**Dependencies:** WP-1

---

### WP-3: Inherited Components

**Goal:** Wire reusable System A components into the System A+W package.

**Source:** `sensor.py`, `memory.py`, `actions.py`

**Details:**
- **Sensor**: Reuse `SystemASensor` directly (observation model is identical per Section 1.1)
- **Memory**: Reuse `update_memory` directly (memory mechanics are unchanged per Section 1.1)
- **Consume**: Reuse `handle_consume` directly (energy dynamics are unchanged per Section 1.1)
- Approach: import and re-export from System A, or copy if decoupling is preferred

**Design Decision Required:**
- *Import from System A* (less duplication, couples the packages) vs. *Copy* (independent, more files). Recommendation: import and re-export. If System A changes, System A+W tests will catch regressions.

**Acceptance Criteria:**
- [ ] `SystemAWSensor` (or re-exported `SystemASensor`) produces identical observations
- [ ] Memory update works with `AgentStateAW`
- [ ] Consume action handler works unchanged

**Dependencies:** WP-1, WP-2

---

### WP-4: Spatial World Model

**Goal:** Implement the visit-count map with dead reckoning from Model Section 4.1.

**Source:** `world_model.py`

**Details:**
- `WorldModelState` stores:
  - `relative_position: tuple[int, int]` — agent's position estimate via path integration
  - `visit_counts: dict[tuple[int, int], int]` — visit counts indexed by relative coordinates
- Direction delta function: maps action strings to displacement vectors (Section 4.1.2)
- Functions:
  - `create_world_model() -> WorldModelState`: initializes with $\hat{p}_0 = (0, 0)$, $w_0(0,0) = 1$
  - `update_world_model(state, action, moved) -> WorldModelState`: dead reckoning update using only the action taken and whether displacement occurred (Section 4.1.3). **Does not consume any absolute position data.**
  - `get_visit_count(state, rel_pos) -> int`: returns $w_t(\hat{p})$, defaulting to 0
  - `spatial_novelty(state, direction) -> float`: returns $\frac{1}{1 + w_t(\hat{p}_t + \Delta(dir))}$
  - `get_neighbor_position(state, direction) -> tuple[int, int]`: computes $\hat{p}_t + \Delta(dir)$
- Pure functions operating on immutable state (consistent with the Pydantic frozen model pattern)

**Dead Reckoning Mechanism:**
The world model update consumes exactly two inputs:
1. `action: str` — the action the agent selected (to determine $\Delta(a)$)
2. `moved: bool` — whether the action resulted in displacement ($\mu_t$)

The update rule: $\hat{p}_{t+1} = \hat{p}_t + \mu_t \cdot \Delta(a_t)$, then increment $w_{t+1}(\hat{p}_{t+1})$.

This is path integration — the same mechanism used by desert ants and honeybees. In the discrete grid world, dead reckoning is exact (no drift, no slip).

**Acceptance Criteria:**
- [ ] Initial state has $\hat{p}_0 = (0,0)$ and $w_0(0,0) = 1$
- [ ] Successful movement updates relative position correctly
- [ ] Failed movement ($\mu_t = 0$) leaves position unchanged but increments visit count
- [ ] Non-movement actions (CONSUME, STAY) leave position unchanged but increment visit count
- [ ] Spatial novelty: unvisited = 1.0, visited once = 0.5, visited $n$ = $\frac{1}{1+n}$
- [ ] **No absolute position data is consumed at any point**
- [ ] Matches worked examples F1 (6-step trajectory), F2 (decay table), F3 (stationary actions)

**Dependencies:** WP-2

---

### WP-5: Hunger Drive Module

**Goal:** Provide the hunger drive for System A+W.

**Source:** `drive_hunger.py`

**Details:**
- Reuse or wrap `SystemAHungerDrive` from System A
- Interface must produce:
  - Scalar activation $d_H(t) = 1 - e_t / E_{\max}$
  - Per-action hunger contributions $\phi_H(a, u_t)$ (identical to System A Section 11.4)
- Output type: the existing `HungerDriveOutput` or an adapter to the new type vocabulary

**Acceptance Criteria:**
- [ ] $d_H$ matches System A for all energy levels
- [ ] $\phi_H$ values match System A for all observations
- [ ] Works with `AgentStateAW`

**Dependencies:** WP-2, WP-3

---

### WP-6: Curiosity Drive Module

**Goal:** Implement the curiosity drive from Model Sections 5.2 and 6.3.

**Source:** `drive_curiosity.py`

**Details:**

This is the most novel component of System A+W.

- **Inputs:** observation $u_t$, memory $m_t$, world model $w_t$, curiosity config
- **Outputs:** `CuriosityDriveOutput` containing:
  - Drive activation $d_C(t) = \mu_C \cdot (1 - \bar{\nu}_t)$
  - Per-direction spatial novelty $\nu^{spatial}_{dir}$
  - Per-direction sensory novelty $\nu^{sensory}_{dir}$
  - Per-direction composite novelty $\nu_{dir} = \alpha \cdot \nu^{spatial}_{dir} + (1-\alpha) \cdot \nu^{sensory}_{dir}$
  - Per-action curiosity contributions $\phi_C(a)$:
    - Movement: $\phi_C(dir) = \nu_{dir}$
    - CONSUME: $\phi_C = -\lambda_{explore}$
    - STAY: $\phi_C = -\lambda_{explore}$

- **Sub-computations:**
  - `compute_spatial_novelty(world_model, neighbor_positions) -> dict[dir, float]`
  - `compute_sensory_novelty(observation, memory) -> dict[dir, float]`
  - `compute_composite_novelty(spatial, sensory, alpha) -> dict[dir, float]`
  - `compute_novelty_saturation(memory) -> float`
  - `compute_curiosity_activation(mu_c, saturation) -> float`

**Acceptance Criteria:**
- [ ] Spatial novelty matches Section 5.2.4 (hyperbolic decay)
- [ ] Sensory novelty matches Section 5.2.5 (absolute difference from memory mean)
- [ ] Composite novelty matches Section 5.2.6 ($\alpha$-weighted)
- [ ] $d_C$ range: $[0, \mu_C]$
- [ ] Movement contributions equal composite novelty per direction
- [ ] CONSUME and STAY produce $-\lambda_{explore}$
- [ ] Numerical match with worked examples A1, B1, C1

**Dependencies:** WP-2, WP-4

---

### WP-7: Drive Arbitration

**Goal:** Implement dynamic drive weights from Model Section 6.4.

**Source:** `drive_arbitration.py`

**Details:**
- Functions:
  - `compute_drive_weights(d_H, config) -> DriveWeights`
    - $w_H = w_H^{base} + (1 - w_H^{base}) \cdot d_H^{\gamma}$
    - $w_C = w_C^{base} \cdot (1 - d_H)^{\gamma}$
  - `compute_action_scores(hunger_output, curiosity_output, weights) -> dict[action, float]`
    - $\psi(a) = w_H \cdot d_H \cdot \phi_H(a) + w_C \cdot d_C \cdot \phi_C(a)$

**Acceptance Criteria:**
- [ ] Weight properties from Section 6.4 hold:
  - Hunger floor: $w_H \geq w_H^{base}$
  - Curiosity ceiling: $w_C \leq w_C^{base}$
  - Curiosity suppression: $w_C \to 0$ as $d_H \to 1$
  - Monotonicity: $w_H$ increasing in $d_H$, $w_C$ decreasing
- [ ] $\gamma$ sensitivity matches Example E1 (all four $\gamma$ values)
- [ ] Combined scores match worked examples A1, B1, C1

**Dependencies:** WP-5, WP-6

---

### WP-8: Policy

**Goal:** Provide the softmax policy for System A+W.

**Source:** `policy.py`

**Details:**
- Reuse `SystemAPolicy` from System A
- The policy is unchanged (Section 7): it receives combined action scores and applies softmax with admissibility masking
- The policy does not know about drives; it only sees $\psi(a)$ scores

**Acceptance Criteria:**
- [ ] Softmax probabilities match worked examples A1, B1, C1
- [ ] Admissibility masking works (Example B1: LEFT blocked)
- [ ] Both `sample` and `argmax` modes work

**Dependencies:** WP-3

---

### WP-9: Extended Transition Function

**Goal:** Implement the state transition from Model Section 8.

**Source:** `transition.py`

**Details:**
- Extends System A's transition with dead reckoning and world model update phases:
  1. Energy update (unchanged): $e_{t+1} = \text{clip}(e_t - c(a_t) + \kappa \cdot \Delta R_t^{cons}, 0, E_{\max})$
  2. Memory update (unchanged): $m_{t+1} = M(m_t, u_{t+1})$
  3. **Dead reckoning update (new):** $\hat{p}_{t+1} = \hat{p}_t + \mu_t \cdot \Delta(a_t)$ — uses `action_outcome.action` and `action_outcome.moved`
  4. **World model update (new):** increment $w_{t+1}(\hat{p}_{t+1})$
  5. Termination check (unchanged): $e_{t+1} \leq 0$
- Returns updated `AgentStateAW` plus trace data
- **Critical constraint:** The transition reads only `action_outcome.action` and `action_outcome.moved`. It **never reads** `action_outcome.new_position`. The agent has no access to absolute coordinates.

**Acceptance Criteria:**
- [ ] Energy update matches System A
- [ ] Memory update matches System A
- [ ] Dead reckoning updates relative position correctly from action + moved
- [ ] World model increments visit count at the (relative) current position
- [ ] Termination triggers at energy $\leq 0$
- [ ] Trace data includes relative position and world model state for logging
- [ ] `action_outcome.new_position` is never accessed

**Dependencies:** WP-2, WP-3, WP-4

---

### WP-10: System Orchestrator + Registration

**Goal:** Wire all components together as `SystemAW` and register it with the framework.

**Source:** `system.py`, `__init__.py`, framework `registry.py`

**Details:**
- `SystemAW` implements `SystemInterface` with the execution cycle from Section 9:
  1. Perception (sensor)
  2. Drive evaluation (hunger + curiosity)
  3. Drive arbitration (dynamic weights)
  4. Action modulation (combined scores)
  5. Admissibility masking
  6. Action selection (policy)
  7. *(Framework handles action execution)*
  8. State transition (energy + memory + world model)
  9. Termination check
- Methods: `decide()`, `transition()`, `action_space()`, `initialize_state()`, `vitality()`, `action_handlers()`, `observe()`, `action_context()`
- Register `"system_aw"` in framework `registry.py` following the System A pattern
- `__init__.py` exports: `SystemAW`, `SystemAWConfig`

**Acceptance Criteria:**
- [ ] `create_system("system_aw", config_dict)` returns a working `SystemAW` instance
- [ ] Full episode runs without errors
- [ ] `decide()` produces action intents with correct probability distributions
- [ ] `transition()` updates all three state components (energy, memory, world model)
- [ ] Pipeline test: sensor → drive → arbitration → policy → transition chain works end-to-end

**Dependencies:** WP-1 through WP-9

---

### WP-11: Validation + Reduction Tests

**Goal:** Verify numerical correctness and System A reduction property.

**Source:** `test_worked_examples.py`, `test_reduction.py`

**Details:**

**Worked Example Validation:**
- Implement each example from `02_System A+W Worked Examples.md` as a test:
  - A1: Well-fed agent in novel territory → verify all action probabilities within $\epsilon = 0.01$
  - B1: Moderate hunger with resource → verify scores with admissibility masking
  - C1: Starving agent → verify curiosity contribution < 0.2% of any score
  - D1: Forage-explore cycle → run 4-step trajectory, verify energy, position, and dominant drive at each step
  - E1: $\gamma$ sensitivity → verify $w_H$, $w_C$ for all four $\gamma$ values
  - E2: $\alpha$ sensitivity → verify composite novelty for all three $\alpha$ values
  - F1: Dead reckoning trajectory → verify relative positions and visit counts over 6 steps, including failed movement
  - F2: Novelty decay table → verify $\nu^{spatial}$ for all visit counts in the table
  - F3: Stationary actions → verify CONSUME/STAY increment visit count without changing position

**Reduction Validation (Section 12):**
- With $\mu_C = 0$: run identical scenario through System A and System A+W, assert action probabilities match within $\epsilon$
- With $w_C^{base} = 0$: same test
- With $\alpha = 1$: verify no memory dependency in curiosity output
- With $\alpha = 0$: verify no world model dependency in curiosity output

**Acceptance Criteria:**
- [ ] All 6 worked examples pass
- [ ] Reduction to System A verified for both $\mu_C = 0$ and $w_C^{base} = 0$
- [ ] $\alpha$ boundary conditions verified

**Dependencies:** WP-10

---

### WP-12: Visualization Adapter

**Goal:** Provide visualization support for System A+W.

**Source:** `visualization.py`

**Details:**
- Follow the pattern of `SystemAVisualizationAdapter`
- Analysis sections:
  - Step Overview (energy, position, action -- inherited)
  - Observation (sensor readout -- inherited)
  - Hunger Drive Output (activation + contributions -- inherited)
  - **Curiosity Drive Output** (new): activation, spatial novelty per direction, sensory novelty per direction, composite novelty per direction, per-action contributions
  - **Drive Arbitration** (new): $w_H$, $w_C$, dominant drive label
  - Decision Pipeline (combined scores + probabilities -- extended)
  - Outcome (energy delta, transition result -- inherited)
- Overlay types:
  - `action_preference` (inherited)
  - `drive_contribution` (extended: show hunger vs curiosity contributions as stacked bars)
  - **`visit_count_heatmap`** (new): render world model as a heatmap overlay
  - **`novelty_field`** (new): render per-direction composite novelty arrows
- Register via `register_system_visualization("system_aw", ...)`

**Acceptance Criteria:**
- [ ] All analysis sections produce valid output for a sample step
- [ ] Visualization adapter is auto-registered
- [ ] Visit count heatmap renders correctly
- [ ] Adapter degrades gracefully to System A view when curiosity is zeroed

**Dependencies:** WP-10

---

### WP-13: Experiment Configurations

**Goal:** Provide ready-to-run YAML configs for System A+W experiments.

**Source:** `experiments/configs/system-aw-*.yaml`

**Details:**

Three experiment configurations:

1. **`system-aw-baseline.yaml`** -- Baseline dual-drive experiment
   - Default parameters from Section 11.2
   - 10x10 grid, moderate resource density, 5 episodes, 200 steps
   - Compact logging enabled
   - Purpose: verify basic forage-explore cycle

2. **`system-aw-curiosity-sweep.yaml`** -- OFAT sweep over curiosity parameters
   - Sweep factor: `system.curiosity.base_curiosity` over $[0.0, 0.25, 0.5, 0.75, 1.0]$
   - Shows transition from pure System A behavior ($\mu_C = 0$) to full curiosity
   - JSONL logging for quantitative analysis

3. **`system-aw-exploration-demo.yaml`** -- Exploration-focused demo
   - High initial energy ($e_0 = E_{\max}$), sparse resources, large grid (20x20)
   - $\gamma = 3.0$ (sharp gating -- long exploration phases)
   - Verbose logging to see novelty computations
   - Purpose: demonstrate systematic territory coverage

**Acceptance Criteria:**
- [ ] All configs parse and run without errors
- [ ] Baseline shows forage-explore cycle in logs
- [ ] Sweep produces differentiated behavior across $\mu_C$ values
- [ ] Exploration demo shows high spatial coverage

**Dependencies:** WP-10

---

### WP-14: Documentation Update

**Goal:** Update project-level documentation to reflect System A+W.

**Details:**
- Update `README.md`:
  - Add System A+W to the "Systems" section
  - Add `system-aw-*` configs to the CLI examples
- Update `tests/test_scaffold.py`:
  - Add `SystemAW`, `SystemAWConfig` to expected exports
- Verify `__init__.py` at all levels exports correctly

**Acceptance Criteria:**
- [ ] README documents System A+W as an available system
- [ ] Scaffold tests pass with new exports
- [ ] `axis run experiments/configs/system-aw-baseline.yaml` works end-to-end

**Dependencies:** WP-10, WP-13

---

## 5. Work Package Dependency Graph

```
WP-1  Config
  │
  ├──► WP-2  Types
  │      │
  │      ├──► WP-4  World Model
  │      │      │
  │      │      └──► WP-6  Curiosity Drive ◄── WP-2
  │      │             │
  │      ├──► WP-3  Inherited Components
  │      │      │
  │      │      ├──► WP-5  Hunger Drive
  │      │      │      │
  │      │      │      └──► WP-7  Arbitration ◄── WP-6
  │      │      │             │
  │      │      ├──► WP-8  Policy
  │      │      │      │
  │      │      └──► WP-9  Transition ◄── WP-4
  │      │             │
  │      └─────────────┴──► WP-10  System Orchestrator ◄── WP-7, WP-8
  │                           │
  │                           ├──► WP-11  Validation Tests
  │                           ├──► WP-12  Visualization
  │                           ├──► WP-13  Experiment Configs
  │                           └──► WP-14  Documentation
```

---

## 6. Suggested Execution Order

The dependency graph admits some parallelism. The recommended sequential order that maximizes testability at each step:

| Phase | Work Packages | Rationale |
|---|---|---|
| **Phase 1: Foundation** | WP-1, WP-2 | Config and types must exist before any logic |
| **Phase 2: Core Components** | WP-3, WP-4, WP-5 | Inherited components + world model + hunger drive |
| **Phase 3: New Drive** | WP-6, WP-7 | Curiosity drive + arbitration (the novel logic) |
| **Phase 4: Integration** | WP-8, WP-9, WP-10 | Policy + transition + orchestrator |
| **Phase 5: Validation** | WP-11 | Worked examples + reduction tests |
| **Phase 6: Polish** | WP-12, WP-13, WP-14 | Visualization, configs, docs |

**Estimated scope:** ~12 source files, ~12 test files, ~3 config files, 1 doc update.

---

## 7. Risk Assessment

| Risk | Impact | Status | Resolution |
|---|---|---|---|
| ~~Position tracking: the world model needs the agent's position, but `SystemInterface` doesn't expose it directly~~ | ~~High~~ | **Resolved** | Dead reckoning via path integration. The world model uses relative coordinates updated from `action_outcome.action` + `action_outcome.moved`. No absolute position is consumed. See Model Section 4.1. |
| Sensory novelty depends on memory contents that System A stores but doesn't expose as structured data | Medium | Open | Verify that `MemoryState` entries contain full observation vectors. Memory capacity is configurable (parameter $k$), not a fixed constant. If memory entries lack structured per-direction resource values, extend `MemoryEntry` in WP-2. |
| Softmax numerical stability with two-drive scores spanning a wider range than System A | Low | Open | System A's policy already handles `-inf` masking. The score range increase from curiosity is bounded by $w_C^{base} \cdot \mu_C \leq 1.0$, so overflow is unlikely. Monitor in WP-11. |
| Performance of visit-count map on large grids | Low | Open | Dict-based map is $O(1)$ per lookup. For 20x20 grids with 200 steps, max map size is 200 entries. Not a concern at current scale. |

---

## 8. Success Criteria

The implementation is complete when:

1. `axis run experiments/configs/system-aw-baseline.yaml` executes successfully
2. All unit tests pass (`pytest tests/systems/system_aw/`)
3. All worked examples from `02_System A+W Worked Examples.md` are verified numerically
4. System A reduction property is verified ($\mu_C = 0$ produces identical behavior)
5. The forage-explore cycle is observable in logs (compact or verbose)
6. Visualization renders curiosity-specific overlays (visit heatmap, novelty field)
