# WP-5: Hunger Drive Module

## Metadata
- Work Package: WP-5
- Title: Hunger Drive Module
- System: System A+W
- Source File: `src/axis/systems/system_aw/drive_hunger.py`
- Test File: `tests/systems/system_aw/test_drive_hunger.py`
- Model Reference: `01_System A+W Model.md`, Sections 5.1, 6.2
- Worked Examples: `02_System A+W Worked Examples.md`, Examples A1 (hunger part), B1 (hunger part), C1 (hunger part)
- Dependencies: WP-2 (types), WP-3 (inherited components)

---

## 1. Objective

Provide the hunger drive for System A+W. The hunger drive is **unchanged** from System A (Model Section 5.1). This WP wraps System A's `SystemAHungerDrive` so it can be used within the System A+W package with the `AgentStateAW` type.

---

## 2. Design

### 2.1 Why a Wrapper?

System A's `SystemAHungerDrive.compute()` expects:
- `agent_state: object` — it reads `agent_state.energy` via attribute access
- `observation: Observation` — the Von Neumann neighborhood

And returns:
- `HungerDriveOutput` — activation + 6-element action contributions tuple

This interface already works with `AgentStateAW` because:
- `AgentStateAW` has an `energy: float` field (duck-typing matches)
- `Observation` type is identical (reused from System A)
- `HungerDriveOutput` type is identical (reused from System A)

**Decision: Thin wrapper that delegates to `SystemAHungerDrive`.**

The wrapper:
1. Provides a local import point within the `system_aw` package
2. Documents the relationship to the formal model
3. Makes it explicit that the hunger drive is unchanged
4. Can be replaced with a local implementation if divergence is ever needed

### 2.2 Alternative Considered

**Direct instantiation of `SystemAHungerDrive` in the orchestrator (WP-10).**

Rejected because:
- Cross-package import in the orchestrator is less explicit
- Inconsistent with the wrapper pattern established in WP-3
- WP-5 tests would not exist, leaving the hunger-drive-with-AgentStateAW compatibility unverified

---

## 3. Specification

### 3.1 Module Interface

```python
"""System A+W hunger drive -- wraps System A's hunger drive.

The hunger drive is identical to System A (Model Section 5.1):
    d_H(t) = clamp(1 - E_t / E_max, 0, 1)

The drive depends only on internal energy. It has no dependency
on observations, memory, or the world model.

Action contributions (Model Section 6.2):
    Movement:  phi_H(dir) = d_H * r_dir
    Consume:   phi_H(consume) = d_H * w_consume * r_current
    Stay:      phi_H(stay) = -lambda_stay * d_H
"""

from axis.systems.system_a.drive import SystemAHungerDrive
from axis.systems.system_a.types import HungerDriveOutput, Observation


class SystemAWHungerDrive:
    """Hunger drive for System A+W.
    
    Delegates entirely to System A's hunger drive.
    The hunger drive is unchanged between the two systems.
    """

    def __init__(
        self,
        *,
        consume_weight: float,
        stay_suppression: float,
        max_energy: float,
    ) -> None:
        self._drive = SystemAHungerDrive(
            consume_weight=consume_weight,
            stay_suppression=stay_suppression,
            max_energy=max_energy,
        )

    def compute(
        self,
        agent_state: object,
        observation: Observation,
    ) -> HungerDriveOutput:
        """Compute hunger drive output.
        
        agent_state must have an `energy: float` attribute.
        This works with both AgentState (System A) and
        AgentStateAW (System A+W).
        """
        return self._drive.compute(agent_state, observation)
```

### 3.2 Construction from Config

The orchestrator (WP-10) will construct the hunger drive from `SystemAWConfig`:

```python
hunger_drive = SystemAWHungerDrive(
    consume_weight=config.policy.consume_weight,
    stay_suppression=config.policy.stay_suppression,
    max_energy=config.agent.max_energy,
)
```

These parameters come from the inherited `PolicyConfig` and `AgentConfig` sub-models.

---

## 4. Mathematical Summary

Reproduced from Model Sections 5.1 and 6.2 for reference.

### 4.1 Drive Activation

$$
d_H(t) = \text{clamp}\left(1 - \frac{e_t}{E_{\max}},\; 0,\; 1\right)
$$

### 4.2 Action Contributions

| Action | $\phi_H(a, u_t)$ | Code in System A |
|---|---|---|
| UP | $d_H \cdot r_{up}$ | `d_h * observation.up.resource` |
| DOWN | $d_H \cdot r_{down}$ | `d_h * observation.down.resource` |
| LEFT | $d_H \cdot r_{left}$ | `d_h * observation.left.resource` |
| RIGHT | $d_H \cdot r_{right}$ | `d_h * observation.right.resource` |
| CONSUME | $d_H \cdot w_{consume} \cdot r_c$ | `d_h * consume_weight * observation.current.resource` |
| STAY | $-\lambda_{stay} \cdot d_H$ | `-stay_suppression * d_h` |

### 4.3 Properties

- $d_H \in [0, 1]$
- $d_H = 0$ when $e_t = E_{\max}$ (fully sated)
- $d_H = 1$ when $e_t = 0$ (starving)
- Depends only on $e_t$ — no dependency on memory, world model, or curiosity state

---

## 5. Compatibility with AgentStateAW

System A's drive uses `agent_state.energy` via duck-typing:

```python
energy: float = agent_state.energy  # type: ignore[attr-defined]
```

`AgentStateAW` has `energy: float = Field(..., ge=0)`, so this access works unchanged. No adapter or conversion is needed.

---

## 6. Test Plan

### File: `tests/systems/system_aw/test_drive_hunger.py`

#### Basic Behavior

| # | Test | Description |
|---|---|---|
| 1 | `test_fully_sated` | $e_t = E_{\max} = 100$ → $d_H = 0.0$, all contributions = 0 except STAY |
| 2 | `test_starving` | $e_t = 0$ → $d_H = 1.0$, CONSUME contribution = $w_{consume} \cdot r_c$ |
| 3 | `test_half_energy` | $e_t = 50, E_{\max} = 100$ → $d_H = 0.5$ |
| 4 | `test_movement_contribution` | With $r_{up} = 0.4$ and $d_H = 0.5$ → UP contribution = $0.2$ |
| 5 | `test_consume_contribution` | With $r_c = 0.8$, $w_{consume} = 2.5$, $d_H = 0.5$ → CONSUME = $1.0$ |
| 6 | `test_stay_suppression` | STAY contribution = $-\lambda_{stay} \cdot d_H$ |

#### AgentStateAW Compatibility

| # | Test | Description |
|---|---|---|
| 7 | `test_works_with_agent_state_aw` | Construct `AgentStateAW` with energy=90, pass to `compute()` → no error, correct $d_H = 0.1$ |
| 8 | `test_output_type` | `compute()` returns `HungerDriveOutput` |
| 9 | `test_contributions_tuple_length` | `action_contributions` has exactly 6 elements |

#### Worked Example Verification

| # | Test | Description |
|---|---|---|
| 10 | `test_example_a1_hunger` | Example A1: $e=90, E_{\max}=100$ → $d_H = 0.10$. With observation from A1, verify all 6 hunger contributions match the example table (e.g., CONSUME $\phi_H = 2.0$). |
| 11 | `test_example_b1_hunger` | Example B1: $e=50$ → $d_H = 0.50$. Verify contributions match (e.g., DOWN = 0.4, CONSUME = 1.5). |
| 12 | `test_example_c1_hunger` | Example C1: $e=5$ → $d_H = 0.95$. Verify CONSUME contribution = $2.5 \times 0.5 = 1.25$. |

#### Identity with System A

| # | Test | Description |
|---|---|---|
| 13 | `test_matches_system_a_drive` | For a random set of (energy, observation) pairs, verify `SystemAWHungerDrive` and `SystemAHungerDrive` produce identical `HungerDriveOutput`. |

---

## 7. Acceptance Criteria

- [ ] $d_H$ matches System A for all energy levels
- [ ] $\phi_H$ values match System A for all observations
- [ ] Works with `AgentStateAW` (energy attribute access)
- [ ] Output type is `HungerDriveOutput` (reused from System A)
- [ ] Action contributions tuple has 6 elements in correct order
- [ ] Numerical match with worked examples A1, B1, C1 (hunger columns only)
- [ ] Identical output to `SystemAHungerDrive` for all inputs
- [ ] All 13 tests pass
