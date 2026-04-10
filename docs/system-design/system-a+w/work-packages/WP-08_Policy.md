# WP-8: Policy

## Metadata
- Work Package: WP-8
- Title: Policy (Softmax Action Selection)
- System: System A+W
- Source File: `src/axis/systems/system_aw/policy.py`
- Test File: `tests/systems/system_aw/test_policy.py`
- Model Reference: `01_System A+W Model.md`, Sections 6.6, 7
- Worked Examples: `02_System A+W Worked Examples.md`, Examples A1, B1, C1
- Dependencies: WP-3 (inherited components)

---

## 1. Objective

Provide the softmax policy for System A+W. The policy is **unchanged** from System A (Model Section 7). It receives a single combined action score vector (from WP-7) and applies admissibility masking + softmax selection.

> "The policy does not know that the action scores originate from multiple drives. It receives a single combined score per action and applies softmax selection." — Model Section 7

---

## 2. Design

### 2.1 Interface Difference from System A

System A's `SystemAPolicy.select()` takes a `HungerDriveOutput` directly:

```python
def select(self, drive_outputs: HungerDriveOutput, observation, rng) -> PolicyResult
```

It reads `drive_outputs.action_contributions` to get the score tuple. In System A+W, the scores come from the arbitration layer (WP-7), not from a single drive output. The policy needs to accept a pre-computed score tuple instead.

### 2.2 Approach: Thin Adapter

Rather than modifying System A's policy, we create a thin wrapper that:
1. Accepts the combined score tuple from WP-7
2. Packages it in a way that `SystemAPolicy` can consume
3. Delegates to `SystemAPolicy` for the actual softmax + selection

Alternatively, we can create a `SystemAWPolicy` that directly operates on score tuples. Since the policy's internal logic (mask computation, softmax, selection) is identical, the difference is only in the input interface.

**Decision: Create `SystemAWPolicy` that accepts score tuples directly.**

Rationale: The wrapper approach would require constructing a fake `HungerDriveOutput` just to carry the scores, which is misleading. A clean interface that takes `(scores, observation, rng)` is clearer and aligns with the model's separation of concerns.

However, the internal implementation (masking, softmax, selection) will reuse `SystemAPolicy`'s static methods where possible.

---

## 3. Specification

```python
"""System A+W policy -- softmax action selection with admissibility masking.

The policy is unchanged from System A (Model Section 7). It receives
a single combined action score vector and applies:
1. Admissibility masking (blocked directions -> -inf)
2. Softmax with inverse temperature beta
3. Stochastic (sample) or deterministic (argmax) selection
"""

from __future__ import annotations

import numpy as np

from axis.sdk.types import PolicyResult
from axis.systems.system_a.policy import SystemAPolicy
from axis.systems.system_a.types import Observation


class SystemAWPolicy:
    """Softmax policy for System A+W.

    Accepts pre-computed action scores (from the arbitration layer)
    rather than a single drive output. Delegates masking, softmax,
    and selection to System A's policy implementation.
    """

    def __init__(self, *, temperature: float, selection_mode: str) -> None:
        self._inner = SystemAPolicy(
            temperature=temperature,
            selection_mode=selection_mode,
        )
        self._temperature = temperature
        self._selection_mode = selection_mode

    def select(
        self,
        action_scores: tuple[float, float, float, float, float, float],
        observation: Observation,
        rng: np.random.Generator,
    ) -> PolicyResult:
        """Run the policy pipeline on pre-computed action scores.

        Steps:
        1. Compute admissibility mask from observation
        2. Apply mask (blocked -> -inf)
        3. Softmax with temperature beta
        4. Select action (sample or argmax)
        """
        mask = SystemAPolicy._compute_admissibility_mask(observation)
        masked = SystemAPolicy._apply_mask(action_scores, mask)
        probs = SystemAPolicy._softmax(action_scores, self._temperature, mask)
        action_idx = self._inner._select_from_distribution(probs, rng)

        action_names = ("up", "down", "left", "right", "consume", "stay")
        action = action_names[action_idx]

        policy_data = {
            "raw_scores": action_scores,
            "admissibility_mask": mask,
            "masked_scores": masked,
            "probabilities": probs,
            "selected_action": action,
            "temperature": self._temperature,
            "selection_mode": self._selection_mode,
        }

        return PolicyResult(action=action, policy_data=policy_data)
```

### 3.1 Policy Data Differences from System A

System A's policy records `raw_contributions` (from the single drive). System A+W records `raw_scores` (the combined arbitrated scores). This distinction matters for trace logging and visualization:

| Key | System A | System A+W |
|---|---|---|
| `raw_contributions` | Single-drive output | Not present |
| `raw_scores` | Not present | Combined scores from arbitration |
| `admissibility_mask` | Same | Same |
| `masked_scores` / `masked_contributions` | Same semantics | Same semantics |
| `probabilities` | Same | Same |

---

## 4. Mathematical Summary

**Model Section 7:**

$$
P(a \mid x_t, u_t, m_t) = \frac{\exp(\beta \cdot \psi(a))}{\sum_{a'} \exp(\beta \cdot \psi(a'))}
$$

**Model Section 6.6 — Admissibility Masking:**

Movement actions toward non-traversable cells receive $\psi(a) = -\infty$ and probability 0 in the softmax.

The mask is derived from the observation's traversability signals:
- `observation.up.traversability > 0` → UP admissible
- `observation.down.traversability > 0` → DOWN admissible
- `observation.left.traversability > 0` → LEFT admissible
- `observation.right.traversability > 0` → RIGHT admissible
- CONSUME → always admissible
- STAY → always admissible

---

## 5. Test Plan

### File: `tests/systems/system_aw/test_policy.py`

#### Basic Behavior

| # | Test | Description |
|---|---|---|
| 1 | `test_uniform_scores_equal_probs` | All scores equal → all admissible actions have equal probability |
| 2 | `test_high_score_dominates` | One action has much higher score → near-1.0 probability |
| 3 | `test_masked_action_zero_prob` | Blocked direction → probability = 0.0 |
| 4 | `test_consume_stay_always_admissible` | Even with all directions blocked, CONSUME and STAY are admissible |
| 5 | `test_argmax_mode` | `selection_mode="argmax"` → always selects highest-probability action |
| 6 | `test_sample_mode_respects_probs` | Run 1000 samples → distribution approximately matches probabilities |

#### System A Equivalence

| # | Test | Description |
|---|---|---|
| 7 | `test_same_probs_as_system_a` | Given the same score tuple, verify `SystemAWPolicy` produces the same probabilities as `SystemAPolicy` (by constructing a `HungerDriveOutput` with those scores) |

#### Worked Example Verification

| # | Test | Description |
|---|---|---|
| 8 | `test_example_a1_probabilities` | Example A1 scores → probabilities match: UP=0.205, DOWN=0.205, LEFT=0.266, RIGHT=0.205, CONSUME=0.063, STAY=0.056 (within $\epsilon = 0.01$) |
| 9 | `test_example_b1_probabilities` | Example B1 scores (with LEFT masked) → probabilities match: UP=0.179, DOWN=0.231, LEFT=0.000, RIGHT=0.175, CONSUME=0.283, STAY=0.132 (within $\epsilon = 0.01$) |
| 10 | `test_example_c1_probabilities` | Example C1 scores → CONSUME dominates at ~0.634 |

#### Edge Cases

| # | Test | Description |
|---|---|---|
| 11 | `test_all_negative_scores` | All scores negative → valid probability distribution (no NaN) |
| 12 | `test_large_score_difference` | Score range > 10 → numerically stable (no overflow) |
| 13 | `test_policy_result_type` | Returns `PolicyResult` with `action` and `policy_data` |

---

## 6. Acceptance Criteria

- [ ] Softmax probabilities match worked examples A1, B1, C1 within $\epsilon = 0.01$
- [ ] Admissibility masking works (Example B1: LEFT blocked → P(LEFT) = 0)
- [ ] Both `sample` and `argmax` modes work
- [ ] Probabilities sum to 1.0 (within floating-point tolerance)
- [ ] Numerically stable for large score differences
- [ ] `PolicyResult` output contains all policy trace data
- [ ] All 13 tests pass
