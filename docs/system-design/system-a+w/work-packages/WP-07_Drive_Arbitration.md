# WP-7: Drive Arbitration

## Metadata
- Work Package: WP-7
- Title: Drive Arbitration (Dynamic Weight Functions + Score Combination)
- System: System A+W
- Source File: `src/axis/systems/system_aw/drive_arbitration.py`
- Test File: `tests/systems/system_aw/test_drive_arbitration.py`
- Model Reference: `01_System A+W Model.md`, Sections 6.4, 6.5
- Worked Examples: `02_System A+W Worked Examples.md`, Examples A1, B1, C1, D1, E1
- Dependencies: WP-5 (hunger drive: `HungerDriveOutput`), WP-6 (curiosity drive: `CuriosityDriveOutput`)

---

## 1. Objective

Implement the drive arbitration layer that:
1. Computes dynamic drive weights from the hunger activation level
2. Combines the two drive outputs into a single 6-element action score vector

This is the integration point where the two drives meet. The arbitration layer enforces the Maslow-like hierarchy: hunger gates curiosity.

---

## 2. Design

### 2.1 Two Responsibilities

The module has exactly two responsibilities, each implemented as a pure function:

| Function | Model Section | Input | Output |
|---|---|---|---|
| `compute_drive_weights` | 6.4 | $d_H$, `ArbitrationConfig` | `DriveWeights` |
| `compute_action_scores` | 6.5 | `HungerDriveOutput`, `CuriosityDriveOutput`, `DriveWeights` | 6-element score tuple |

### 2.2 Why a Separate Module?

The weight functions could live inside the orchestrator (WP-10). However:
- The weight formulas are mathematically defined with specific properties (floor, ceiling, monotonicity)
- They need independent unit testing against Example E1 ($\gamma$ sensitivity table)
- Separating arbitration from orchestration keeps the orchestrator thin

---

## 3. Function Specifications

### 3.1 `compute_drive_weights`

**Model reference:** Section 6.4

$$
w_H(t) = w_H^{base} + (1 - w_H^{base}) \cdot d_H(t)^{\gamma}
$$

$$
w_C(t) = w_C^{base} \cdot (1 - d_H(t))^{\gamma}
$$

```python
from axis.systems.system_aw.types import DriveWeights
from axis.systems.system_aw.config import ArbitrationConfig


def compute_drive_weights(
    hunger_activation: float,
    config: ArbitrationConfig,
) -> DriveWeights:
    """Compute dynamic drive weights from hunger activation.

    Enforces Maslow-like hierarchy: hunger gates curiosity.

    Properties:
    - Hunger floor: w_H >= w_H_base > 0 (hunger always contributes)
    - Curiosity ceiling: w_C <= w_C_base (max when fully sated)
    - Curiosity suppression: w_C -> 0 as d_H -> 1 (starving)
    - Monotonicity: w_H increasing in d_H, w_C decreasing in d_H

    Model reference: Section 6.4.
    """
    d_h = hunger_activation
    gamma = config.gating_sharpness

    w_h = config.hunger_weight_base + (1 - config.hunger_weight_base) * (d_h ** gamma)
    w_c = config.curiosity_weight_base * ((1 - d_h) ** gamma)

    return DriveWeights(hunger_weight=w_h, curiosity_weight=w_c)
```

---

### 3.2 `compute_action_scores`

**Model reference:** Section 6.5

$$
\psi(a) = w_H(t) \cdot d_H(t) \cdot \phi_H(a, u_t) + w_C(t) \cdot d_C(t) \cdot \phi_C(a, u_t, m_t, w_t)
$$

Combines the two drive outputs element-wise into a single score vector.

```python
from axis.systems.system_a.types import HungerDriveOutput
from axis.systems.system_aw.types import CuriosityDriveOutput, DriveWeights


def compute_action_scores(
    hunger: HungerDriveOutput,
    curiosity: CuriosityDriveOutput,
    weights: DriveWeights,
) -> tuple[float, float, float, float, float, float]:
    """Combine two drive outputs into final action scores.

    psi(a) = w_H * d_H * phi_H(a) + w_C * d_C * phi_C(a)

    Returns: 6-element tuple in action order (UP, DOWN, LEFT, RIGHT, CONSUME, STAY)

    Model reference: Section 6.5.
    """
    w_h = weights.hunger_weight
    w_c = weights.curiosity_weight
    d_h = hunger.activation
    d_c = curiosity.activation

    return tuple(
        w_h * d_h * phi_h + w_c * d_c * phi_c
        for phi_h, phi_c in zip(
            hunger.action_contributions,
            curiosity.action_contributions,
        )
    )
```

**Implementation note:** Both `HungerDriveOutput.action_contributions` and `CuriosityDriveOutput.action_contributions` are 6-element tuples with the same action ordering (UP, DOWN, LEFT, RIGHT, CONSUME, STAY). The zip produces correct pairwise combination because WP-2 established this shared convention.

---

## 4. Mathematical Properties

The following properties must hold for all valid inputs. They are derived from the formal model (Section 6.4) and serve as test invariants.

### 4.1 Weight Properties

| Property | Formal | Implication |
|---|---|---|
| Hunger floor | $w_H \geq w_H^{base} > 0$ | Hunger always contributes to action scores |
| Curiosity ceiling | $w_C \leq w_C^{base}$ | Curiosity never exceeds its base influence |
| Curiosity suppression | $w_C \to 0$ as $d_H \to 1$ | Starving agent ignores curiosity |
| Monotonicity (hunger) | $\partial w_H / \partial d_H \geq 0$ | More hunger → more hunger weight |
| Monotonicity (curiosity) | $\partial w_C / \partial d_H \leq 0$ | More hunger → less curiosity weight |

### 4.2 Boundary Values

| $d_H$ | $w_H$ | $w_C$ |
|---|---|---|
| 0.0 (fully sated) | $w_H^{base}$ | $w_C^{base}$ |
| 1.0 (starving) | 1.0 | 0.0 |

### 4.3 Score Properties

- When $d_H = 0$: only curiosity contributions survive ($w_H \cdot 0 = 0$), but scaled by $w_H^{base} \cdot 0 = 0$. So scores are purely curiosity-driven.
- When $d_C = 0$ (i.e., $\mu_C = 0$): scores are purely hunger-driven. This is the System A reduction.
- The score vector always has 6 elements, one per action.

---

## 5. Test Plan

### File: `tests/systems/system_aw/test_drive_arbitration.py`

#### Weight Function Tests

| # | Test | Description |
|---|---|---|
| 1 | `test_weights_fully_sated` | $d_H = 0$ → $w_H = w_H^{base}$, $w_C = w_C^{base}$ |
| 2 | `test_weights_starving` | $d_H = 1.0$ → $w_H = 1.0$, $w_C = 0.0$ |
| 3 | `test_weights_half_hunger` | $d_H = 0.5$, $\gamma = 2$ → verify exact values |
| 4 | `test_hunger_floor` | For $d_H \in \{0.0, 0.1, 0.5, 0.9, 1.0\}$: $w_H \geq w_H^{base}$ |
| 5 | `test_curiosity_ceiling` | For same $d_H$ values: $w_C \leq w_C^{base}$ |
| 6 | `test_curiosity_nonneg` | $w_C \geq 0$ for all $d_H \in [0, 1]$ |
| 7 | `test_monotonicity_hunger` | For increasing $d_H$ sequence: $w_H$ is non-decreasing |
| 8 | `test_monotonicity_curiosity` | For increasing $d_H$ sequence: $w_C$ is non-increasing |

#### Gamma Sensitivity (Worked Example E1)

| # | Test | Description |
|---|---|---|
| 9 | `test_e1_gamma_0_5` | $d_H=0.5$, $\gamma=0.5$ → $w_H=0.795$, $w_C=0.707$ |
| 10 | `test_e1_gamma_1_0` | $d_H=0.5$, $\gamma=1.0$ → $w_H=0.650$, $w_C=0.500$ |
| 11 | `test_e1_gamma_2_0` | $d_H=0.5$, $\gamma=2.0$ → $w_H=0.475$, $w_C=0.250$ |
| 12 | `test_e1_gamma_4_0` | $d_H=0.5$, $\gamma=4.0$ → $w_H=0.344$, $w_C=0.063$ |

#### Score Combination Tests

| # | Test | Description |
|---|---|---|
| 13 | `test_scores_pure_hunger` | $d_C = 0$ → all curiosity contributions zeroed, scores = $w_H \cdot d_H \cdot \phi_H$ |
| 14 | `test_scores_pure_curiosity` | $d_H = 0$ → all hunger contributions zeroed, scores = $w_C \cdot d_C \cdot \phi_C$ |
| 15 | `test_scores_both_drives` | Both active → verify element-wise summation |
| 16 | `test_scores_tuple_length` | Output always has 6 elements |

#### Worked Example Verification (Full Scores)

| # | Test | Description |
|---|---|---|
| 17 | `test_example_a1_scores` | Example A1: $d_H=0.10$, $d_C=1.0$, $w_H=0.307$, $w_C=0.810$. Verify all 6 combined scores match: UP=0.405, DOWN=0.405, LEFT=0.536, RIGHT=0.405, CONSUME=-0.182, STAY=-0.246 (within $\epsilon=0.005$) |
| 18 | `test_example_b1_scores` | Example B1: $d_H=0.50$, $d_C=0.85$, $w_H=0.475$, $w_C=0.250$. Verify masked scores (LEFT=$-\infty$ handled by policy, not here). |
| 19 | `test_example_c1_scores` | Example C1: $d_H=0.95$, $d_C=1.0$, $w_H=0.932$, $w_C=0.003$. Verify CONSUME=1.106 dominates. |
| 20 | `test_example_a1_weights` | Example A1: verify $w_H=0.307$, $w_C=0.810$ |
| 21 | `test_example_b1_weights` | Example B1: verify $w_H=0.475$, $w_C=0.250$ |
| 22 | `test_example_c1_weights` | Example C1: verify $w_H=0.932$, $w_C=0.003$ |

---

## 6. Acceptance Criteria

- [ ] Weight properties from Section 6.4 hold for all valid inputs (floor, ceiling, suppression, monotonicity)
- [ ] Boundary values correct: $d_H=0$ and $d_H=1$
- [ ] $\gamma$ sensitivity matches Example E1 (all four values within $\epsilon = 0.005$)
- [ ] Score combination is correct element-wise sum of weighted drive contributions
- [ ] Combined scores match worked examples A1, B1, C1 within $\epsilon = 0.005$
- [ ] All functions are pure (no side effects)
- [ ] All 22 tests pass
