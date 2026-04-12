# System B: A Scout Agent with Scan Action on a Dynamic Signal Landscape

## Metadata
- Project: AXIS -- Complex Mechanistic Systems Experiment
- Author: Oliver Grau
- Type: Formal Research Note
- Status: Draft v1.0
- Scope: Scout agent with non-extractive scan action operating on a non-stationary signal field
- Constraints: No drives, no world model, no observation buffer, no resource extraction, monotonically decreasing energy

---

## 1. Objective

This document defines **System B** as a scout agent for the *Complex Mechanistic Systems Experiment*.

System B demonstrates that the AXIS SDK can support fundamentally different agent architectures. Where System A is a modular drive-based forager decomposed into sensor, drive, policy, and transition subsystems, System B is a monolithic lightweight agent that:

- scans its local neighborhood to estimate nearby signal strength,
- biases movement toward cells with higher signal values,
- operates on a **non-stationary** world (the signal landscape) whose resource field changes every timestep,
- has a **finite, non-replenishable** energy budget that determines its lifetime,
- and implements all decision logic inline (no separate sensor, drive, or policy modules).

System B intentionally **does not** contain:

- drives or drive modulation,
- resource extraction (scanning is read-only),
- an observation buffer or episodic memory,
- a world model or spatial memory,
- or any mechanism to replenish energy.

The central research question:

> What signal-tracking behavior emerges from a minimal scan-and-move agent on a dynamic Gaussian signal landscape with a fixed energy budget?

---

## 2. Design Principles

### 2.1 Pure Mechanism

Like System A, all behavior arises from explicit state variables, update functions, and action selection rules. No mental vocabulary is implied.

### 2.2 Information-Only Sensing

The scan action reads the world but never modifies it. This is a fundamental contrast to System A's consume action, which extracts resources from the environment. System B is a **passive observer** of a dynamic landscape.

### 2.3 Monotonic Energy Budget

System B has no mechanism to gain energy. Every action costs energy, and the agent terminates when energy reaches zero. The agent's total lifetime is bounded by $\lfloor E_0 / c_{\min} \rfloor$ steps, where $E_0$ is initial energy and $c_{\min}$ is the minimum action cost.

### 2.4 Reactive Decision Making

System B makes decisions based solely on the current scan result and the immediately adjacent cells. It stores no history beyond the most recent scan. Each decision is a direct reaction to the current local signal field.

### 2.5 Monolithic Architecture

Unlike System A's modular decomposition (SensorInterface, DriveInterface, PolicyInterface, TransitionInterface), System B implements all logic directly in the SystemInterface methods. This demonstrates that the SDK protocol does not impose a particular internal architecture.

---

## 3. Relationship to System A

System B and System A share the AXIS SDK contract (SystemInterface) and base infrastructure:

| Aspect | System A | System B |
|--------|----------|----------|
| Internal architecture | Modular (sensor, drive, policy, transition) | Monolithic (all inline) |
| Drive system | Hunger drive with modulation | None |
| Custom action | CONSUME (extractive) | SCAN (read-only) |
| Energy dynamics | Loses and gains energy | Loses energy only |
| Observation | 10-dimensional Von Neumann vector | Position only $(x, y)$ |
| Memory | Observation buffer (sliding window) | Last scan result only |
| World model | None (System A), visit counts (A+W) | None |
| Target world | Grid 2D (static) | Signal landscape (dynamic) |
| Lifetime | Until starvation or max steps | Bounded by energy budget |
| Policy | Softmax over drive-modulated scores | Softmax over signal-biased weights |

The key architectural insight: both systems implement the same 9-method protocol, yet produce entirely different behavior from entirely different internal designs.

---

## 4. Formal Definition

System B is defined as a 6-tuple:

$$B = (\mathcal{X},\ \mathcal{U},\ \mathcal{A},\ W,\ \pi,\ F)$$

| Component | Symbol | Description |
|-----------|--------|-------------|
| Internal state | $\mathcal{X}$ | Agent state: energy and last scan result |
| Observation | $\mathcal{U}$ | Minimal observation: agent position |
| Action space | $\mathcal{A}$ | Six discrete actions |
| Weight function | $W$ | Maps state and world view to action weights |
| Policy | $\pi$ | Softmax action selection over weights |
| Transition | $F$ | State update: energy cost and scan result |

---

## 5. Internal State

The agent state at time $t$ is:

$$x_t = (e_t,\ s_t)$$

where:

- $e_t \in [0, E_{\max}]$ is the agent's current energy level,
- $s_t = (\sigma_t, n_t)$ is the result of the most recent scan:
  - $\sigma_t \geq 0$: total resource (signal) value summed across scanned cells,
  - $n_t \in \mathbb{N}_0$: number of cells included in the scan.

At initialization: $e_0 = E_{\text{init}}$, $s_0 = (0, 0)$ (no scan performed yet).

---

## 6. The Signal Landscape

System B is designed to operate on the **signal landscape** world, a non-stationary environment whose resource field changes every timestep.

### 6.1 Grid Structure

The world is a 2D rectangular grid of cells $(x, y)$ where $0 \leq x < W_{\text{grid}}$ and $0 \leq y < H_{\text{grid}}$. Each cell has a type:

- **EMPTY**: traversable, $r(x, y) = 0$
- **RESOURCE**: traversable, $r(x, y) > 0$ (carries a signal value)
- **OBSTACLE**: not traversable, $r(x, y) = 0$

### 6.2 Hotspot Model

The signal field is generated by $K$ **hotspots**, each defined by:

$$h_k = (c_k^x, c_k^y, \rho_k, I_k)$$

where $c_k^x, c_k^y \in \mathbb{R}$ are the center coordinates (sub-cell precision), $\rho_k > 0$ is the radius, and $I_k \in (0, 1]$ is the intensity.

### 6.3 Signal Computation

The signal (resource) value at cell $(x, y)$ is computed as a sum of Gaussian contributions from all hotspots, using **toroidal distance**:

$$r(x, y) = \min\!\left(1,\ (1 - \delta) \sum_{k=1}^{K} I_k \cdot \exp\!\left(-\frac{d_k^2}{2\rho_k^2}\right)\right)$$

where $\delta \in [0, 1]$ is the decay rate, and the toroidal distance $d_k$ from $(x, y)$ to hotspot $k$ is:

$$d_k^2 = \Delta x_k^2 + \Delta y_k^2$$

$$\Delta x_k = \min(|x - c_k^x|,\ W_{\text{grid}} - |x - c_k^x|)$$

$$\Delta y_k = \min(|y - c_k^y|,\ H_{\text{grid}} - |y - c_k^y|)$$

This is a **Gaussian radial basis function (RBF)** field with toroidal wrapping. Each hotspot produces a bell-curve signal centered at $(c_k^x, c_k^y)$ with standard deviation $\rho_k$.

### 6.4 Hotspot Drift

At each world tick, every hotspot center drifts by a random displacement:

$$c_k^x \leftarrow (c_k^x + \xi_k^x) \mod W_{\text{grid}}$$

$$c_k^y \leftarrow (c_k^y + \xi_k^y) \mod H_{\text{grid}}$$

where $\xi_k^x, \xi_k^y \sim \text{Uniform}(-v_{\text{drift}},\ v_{\text{drift}})$ and $v_{\text{drift}} \geq 0$ is the drift speed.

After drift, the entire signal field is recomputed. This makes the landscape **non-stationary**: the optimal position changes every timestep.

### 6.5 Non-Extractive Property

Unlike Grid 2D, the signal landscape does not support resource extraction. Calling `extract_resource()` always returns $0$. The agent can read signal values but cannot consume them. Signals are informational, not consumable.

---

## 7. Observation Model

System B uses a **minimal observation**: the agent's current grid position.

$$u_t = (x_t, y_t)$$

This is deliberately simpler than System A's 10-dimensional Von Neumann neighborhood sensor. System B does not observe neighbor cells through its observation model -- it uses the scan action and direct cell queries in the weight computation instead.

---

## 8. Action Space

$$\mathcal{A} = \{\text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}, \text{SCAN}, \text{STAY}\}$$

- **Movement actions** (UP, DOWN, LEFT, RIGHT): move the agent one cell in the specified direction. Handled by the framework's base movement system.
- **SCAN**: a custom action that reads the local neighborhood without modifying the world.
- **STAY**: the agent remains in place. Handled by the framework.

### 8.1 Scan Mechanics

The scan action reads a square neighborhood of radius $r$ (default $r = 1$, giving a $3 \times 3$ area) centered on the agent's current position:

$$\text{SCAN}(x, y, r) = \left(\sum_{\substack{(x', y') \in N_r(x,y) \\ (x', y') \in \text{bounds}}} r(x', y'),\quad |N_r(x,y) \cap \text{bounds}|\right)$$

where $N_r(x, y) = \{(x', y') : |x' - x| \leq r \text{ and } |y' - y| \leq r\}$.

The scan result $(\sigma, n)$ -- total signal and cell count -- is stored in the agent state and persists until the next scan action.

Key properties:

- Scanning is **non-mutating**: the world is not modified.
- Scanning is **bounded**: at most $(2r + 1)^2$ cells are read.
- At grid boundaries, out-of-bounds cells are skipped (reducing both $\sigma$ and $n$).

---

## 9. Weight Computation

The weight function $W$ maps the current world view and agent state to a weight vector $w \in \mathbb{R}^{|\mathcal{A}|}$.

### 9.1 Base Weights

All actions start with a uniform base weight:

$$w_a^{\text{base}} = 1.0 \quad \forall a \in \mathcal{A}$$

### 9.2 Scan Bonus

If the last scan found no resources ($\sigma_t = 0$, which includes the initial state before any scan), the scan action receives a bonus:

$$w_{\text{SCAN}} = \begin{cases} b_{\text{scan}} & \text{if } \sigma_t = 0 \\ 1.0 & \text{otherwise} \end{cases}$$

where $b_{\text{scan}} \geq 0$ is the scan bonus parameter (default $2.0$).

This creates a natural scan-move cycle: the agent scans first, then moves toward detected signals, then scans again when signals are depleted or lost.

### 9.3 Directional Resource Bias

For each movement direction $\text{DIR} \in \{\text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}\}$, the weight is adjusted based on the resource value of the adjacent cell in that direction:

$$w_{\text{DIR}} = \begin{cases} 1.0 + 2 \cdot r_{\text{target}} & \text{if target cell is in bounds and traversable} \\ 0.0 & \text{otherwise (inadmissible)} \end{cases}$$

where $r_{\text{target}}$ is the `resource_value` (signal strength) of the cell in direction DIR.

Setting $w_{\text{DIR}} = 0$ for inaccessible directions ensures the agent never attempts to move into obstacles or off the grid.

### 9.4 Final Weight Vector

The complete weight vector is:

$$\mathbf{w} = (w_{\text{UP}}, w_{\text{DOWN}}, w_{\text{LEFT}}, w_{\text{RIGHT}}, w_{\text{SCAN}}, w_{\text{STAY}})$$

---

## 10. Policy

The policy $\pi$ converts the weight vector into action probabilities using **softmax** (Boltzmann) selection:

$$P(a) = \frac{\exp(\beta \cdot w_a)}{\sum_{a' \in \mathcal{A}_{\text{adm}}} \exp(\beta \cdot w_{a'})}$$

where:

- $\beta = 1 / T$ is the inverse temperature,
- $T > 0$ is the temperature parameter,
- $\mathcal{A}_{\text{adm}} = \{a \in \mathcal{A} : w_a > 0\}$ is the set of admissible actions.

Inadmissible actions ($w_a = 0$) receive $P(a) = 0$.

**Numerical stability**: the softmax is computed as $\exp(\beta \cdot (w_a - w_{\max}))$ where $w_{\max} = \max_{a \in \mathcal{A}_{\text{adm}}} w_a$.

### 10.1 Selection Modes

- **Sample mode** (default): the action is drawn from the categorical distribution defined by $(P(a))_{a \in \mathcal{A}}$.
- **Argmax mode**: the action with the highest probability is selected deterministically.

### 10.2 Temperature Effects

| Temperature $T$ | Behavior |
|---|---|
| $T \to 0^+$ | Greedy: highest-weight action selected deterministically |
| $T = 1.0$ | Moderate exploration: weights directly determine relative probabilities |
| $T \to \infty$ | Uniform: all admissible actions become equally likely |

---

## 11. Transition Function

The transition function $F$ updates the agent state after each action.

### 11.1 Energy Cost

Each action incurs a fixed energy cost:

| Action | Cost | Default |
|--------|------|---------|
| UP, DOWN, LEFT, RIGHT | $c_{\text{move}}$ | 1.0 |
| SCAN | $c_{\text{scan}}$ | 0.5 |
| STAY | $c_{\text{stay}}$ | 0.5 |

### 11.2 Energy Update

$$e_{t+1} = \text{clip}(e_t - c_a,\ 0,\ E_{\max})$$

where $c_a$ is the cost of the chosen action.

Since there is no energy gain mechanism, energy is **monotonically non-increasing**:

$$e_{t+1} \leq e_t \quad \forall t$$

### 11.3 Scan Result Update

$$s_{t+1} = \begin{cases} (\sigma_{\text{new}}, n_{\text{new}}) & \text{if } a_t = \text{SCAN} \\ s_t & \text{otherwise} \end{cases}$$

The scan result persists across non-scan steps, providing a form of minimal memory.

### 11.4 Termination

The agent terminates when energy is depleted:

$$\text{terminated}(t) = \begin{cases} \texttt{true} & \text{if } e_{t+1} \leq 0 \\ \texttt{false} & \text{otherwise} \end{cases}$$

Termination reason: `"energy_depleted"`.

### 11.5 Lifetime Bound

Since energy decreases by at least $c_{\min} = \min(c_{\text{move}}, c_{\text{scan}}, c_{\text{stay}})$ per step:

$$T_{\max} = \left\lfloor \frac{E_0}{c_{\min}} \right\rfloor$$

With defaults ($E_0 = 100$, $c_{\min} = 0.5$), the maximum lifetime is 200 steps.

---

## 12. Behavioral Analysis

### 12.1 The Scan-Move-Track Loop

System B exhibits a characteristic behavioral cycle:

1. **Scan**: with no prior scan data ($\sigma = 0$), the scan bonus makes scanning the most attractive action.
2. **Move toward signal**: after scanning, directional weights are biased toward cells with higher signal values. The agent moves toward the nearest signal peak.
3. **Track drifting hotspots**: because the signal landscape changes every timestep (hotspot drift), the agent's optimal direction shifts continuously. The agent must periodically re-scan to update its estimate.
4. **Return to step 1**: as the agent moves away from a hotspot or the hotspot drifts away, scan results become stale and the cycle repeats.

### 12.2 Emergent Behavior Modes

| Condition | Behavior |
|---|---|
| Uniform signal field | Near-random movement (all directions equally weighted) |
| Near a hotspot peak | Strong directional bias toward the peak cell |
| After hotspot drift | Stale scan data; agent may follow outdated gradient until re-scanning |
| At grid boundary | Reduced admissible actions; boundary-following behavior |
| Low energy | No behavioral change (unlike System A, urgency does not increase) |

### 12.3 Comparison to System A

System A adapts its behavior as energy decreases: the hunger drive grows, increasingly dominating action selection. System B has **no such adaptation** -- its decision weights are energy-independent. A System B agent with 1 energy remaining makes the same decision it would with 100 energy (given the same scan data and neighborhood). The agent cannot "know" it is about to die.

---

## 13. Configuration Parameters

| Parameter | Config Path | Type | Default | Description |
|-----------|-------------|------|---------|-------------|
| $E_{\text{init}}$ | `agent.initial_energy` | float | (required) | Starting energy |
| $E_{\max}$ | `agent.max_energy` | float | (required) | Maximum energy |
| Selection mode | `policy.selection_mode` | str | `"sample"` | `"sample"` or `"argmax"` |
| $T$ | `policy.temperature` | float | 1.0 | Softmax temperature |
| $b_{\text{scan}}$ | `policy.scan_bonus` | float | 2.0 | Scan action weight when no resources found |
| $c_{\text{move}}$ | `transition.move_cost` | float | 1.0 | Energy cost per movement |
| $c_{\text{scan}}$ | `transition.scan_cost` | float | 0.5 | Energy cost per scan |
| $c_{\text{stay}}$ | `transition.stay_cost` | float | 0.5 | Energy cost for staying |

Constraint: $E_{\text{init}} \leq E_{\max}$.

---

## 14. Validation Criteria

The following properties must hold and are verified by tests:

1. **Protocol conformance**: `SystemB` satisfies `SystemInterface` (runtime checkable).
2. **Action space**: exactly 6 actions in the order (up, down, left, right, scan, stay).
3. **Scan non-mutation**: a scan action does not modify any cell in the world.
4. **Scan boundary clipping**: scanning at a corner yields fewer than $(2r+1)^2$ cells.
5. **Energy monotonicity**: $e_{t+1} \leq e_t$ for all $t$.
6. **Termination**: the agent terminates exactly when $e_{t+1} \leq 0$.
7. **Lifetime bound**: no episode exceeds $\lfloor E_0 / c_{\min} \rfloor$ steps (absent max-step cutoff).
8. **Inadmissibility**: movements into obstacles or off-grid receive probability zero.
9. **Scan bonus**: when $\sigma_t = 0$, scan weight equals $b_{\text{scan}}$ (not $1.0$).
10. **Determinism**: with a fixed seed and argmax mode, the action sequence is fully deterministic.
