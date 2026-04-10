# WP-1: Configuration Model

## Metadata
- Work Package: WP-1
- Title: Configuration Model
- System: System A+W
- Source File: `src/axis/systems/system_aw/config.py`
- Test File: `tests/systems/system_aw/test_config.py`
- Model Reference: `01_System A+W Model.md`, Section 11 (Configuration Parameters)
- Dependencies: None (first work package)

---

## 1. Objective

Define `SystemAWConfig` as the complete Pydantic v2 configuration model for System A+W. This config must represent every parameter from the formal model (Sections 11.1 and 11.2) and be instantiable from a flat dictionary (YAML-compatible).

---

## 2. Design

### 2.1 Structural Approach

System A's config is composed of three frozen sub-models:

```
SystemAConfig
├── agent: AgentConfig        (initial_energy, max_energy, memory_capacity)
├── policy: PolicyConfig      (selection_mode, temperature, stay_suppression, consume_weight)
└── transition: TransitionConfig (move_cost, consume_cost, stay_cost, max_consume, energy_gain_factor)
```

System A+W extends this with two new sub-models:

```
SystemAWConfig
├── agent: AgentConfig            # inherited unchanged
├── policy: PolicyConfig          # inherited unchanged
├── transition: TransitionConfig  # inherited unchanged
├── curiosity: CuriosityConfig    # NEW
└── arbitration: ArbitrationConfig # NEW
```

The inherited sub-models (`AgentConfig`, `PolicyConfig`, `TransitionConfig`) are **imported from System A** — not copied. This ensures they stay in sync and avoids duplication.

### 2.2 Decision: Import vs. Copy

**Decision: Import from System A.**

Rationale:
- The formal model (Section 1.1) states that all inherited parameters are unchanged
- If System A's config models evolve, System A+W picks up the change automatically
- Test isolation is maintained because System A+W tests verify their own configs independently
- If decoupling is ever needed, the import can be replaced with a local copy in a single commit

---

## 3. Specification

### 3.1 CuriosityConfig

Frozen Pydantic model for curiosity drive parameters (Model Section 11.2).

| Field | Type | Constraint | Default | Model Symbol | Description |
|---|---|---|---|---|---|
| `base_curiosity` | `float` | `ge=0, le=1` | `1.0` | $\mu_C$ | Maximum curiosity activation |
| `spatial_sensory_balance` | `float` | `ge=0, le=1` | `0.5` | $\alpha$ | Weighting of spatial vs sensory novelty |
| `explore_suppression` | `float` | `ge=0` | `0.3` | $\lambda_{explore}$ | Curiosity penalty on CONSUME and STAY |

### 3.2 ArbitrationConfig

Frozen Pydantic model for drive weight parameters (Model Section 6.4).

| Field | Type | Constraint | Default | Model Symbol | Description |
|---|---|---|---|---|---|
| `hunger_weight_base` | `float` | `gt=0, le=1` | `0.3` | $w_H^{base}$ | Minimum hunger influence (strict positive) |
| `curiosity_weight_base` | `float` | `gt=0` | `1.0` | $w_C^{base}$ | Maximum curiosity influence |
| `gating_sharpness` | `float` | `gt=0` | `2.0` | $\gamma$ | Hunger-curiosity transition sharpness |

**Validator:** `hunger_weight_base` must be strictly positive ($w_H^{base} \in (0, 1]$) to guarantee the hunger floor property (Model Section 6.4, Property 1).

### 3.3 SystemAWConfig

Top-level frozen model composing all sub-configs.

| Field | Type | Default | Source |
|---|---|---|---|
| `agent` | `AgentConfig` | (required) | Imported from `axis.systems.system_a.config` |
| `policy` | `PolicyConfig` | (required) | Imported from `axis.systems.system_a.config` |
| `transition` | `TransitionConfig` | (required) | Imported from `axis.systems.system_a.config` |
| `curiosity` | `CuriosityConfig` | Uses class defaults | New |
| `arbitration` | `ArbitrationConfig` | Uses class defaults | New |

**Validator (cross-field):** None required. All constraints are local to sub-models.

### 3.4 YAML Mapping

A YAML experiment config maps to `SystemAWConfig` as:

```yaml
system_type: "system_aw"
system:
  agent:
    initial_energy: 100.0
    max_energy: 100.0
    memory_capacity: 5
  policy:
    selection_mode: "sample"
    temperature: 0.5
    stay_suppression: 0.1
    consume_weight: 2.5
  transition:
    move_cost: 1.0
    consume_cost: 1.0
    stay_cost: 0.5
    max_consume: 1.0
    energy_gain_factor: 10.0
  curiosity:                    # optional — defaults used if omitted
    base_curiosity: 1.0
    spatial_sensory_balance: 0.5
    explore_suppression: 0.3
  arbitration:                  # optional — defaults used if omitted
    hunger_weight_base: 0.3
    curiosity_weight_base: 1.0
    gating_sharpness: 2.0
```

When `curiosity` or `arbitration` sections are omitted from the YAML, the defaults from the formal model (Section 11.2) apply. This means System A+W can be run with **only** System A's config keys to verify the reduction property (Section 12).

---

## 4. Implementation Sketch

```python
"""System A+W configuration models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

# Import inherited config models from System A
from axis.systems.system_a.config import AgentConfig, PolicyConfig, TransitionConfig


class CuriosityConfig(BaseModel):
    """Curiosity drive parameters (Model Section 11.2)."""

    model_config = ConfigDict(frozen=True)

    base_curiosity: float = Field(default=1.0, ge=0, le=1)
    spatial_sensory_balance: float = Field(default=0.5, ge=0, le=1)
    explore_suppression: float = Field(default=0.3, ge=0)


class ArbitrationConfig(BaseModel):
    """Drive arbitration parameters (Model Section 6.4)."""

    model_config = ConfigDict(frozen=True)

    hunger_weight_base: float = Field(default=0.3, gt=0, le=1)
    curiosity_weight_base: float = Field(default=1.0, gt=0)
    gating_sharpness: float = Field(default=2.0, gt=0)


class SystemAWConfig(BaseModel):
    """Complete System A+W configuration.

    Extends SystemAConfig with curiosity drive and
    drive arbitration parameters.
    """

    model_config = ConfigDict(frozen=True)

    agent: AgentConfig
    policy: PolicyConfig
    transition: TransitionConfig
    curiosity: CuriosityConfig = Field(default_factory=CuriosityConfig)
    arbitration: ArbitrationConfig = Field(default_factory=ArbitrationConfig)
```

---

## 5. Test Plan

### File: `tests/systems/system_aw/test_config.py`

| # | Test | Description |
|---|---|---|
| 1 | `test_default_curiosity_config` | `CuriosityConfig()` produces defaults: $\mu_C=1.0$, $\alpha=0.5$, $\lambda_{explore}=0.3$ |
| 2 | `test_default_arbitration_config` | `ArbitrationConfig()` produces defaults: $w_H^{base}=0.3$, $w_C^{base}=1.0$, $\gamma=2.0$ |
| 3 | `test_custom_curiosity_config` | Explicit values are stored correctly |
| 4 | `test_custom_arbitration_config` | Explicit values are stored correctly |
| 5 | `test_curiosity_base_bounds` | `base_curiosity < 0` and `> 1` raise `ValidationError` |
| 6 | `test_alpha_bounds` | `spatial_sensory_balance < 0` and `> 1` raise `ValidationError` |
| 7 | `test_explore_suppression_nonneg` | `explore_suppression < 0` raises `ValidationError` |
| 8 | `test_hunger_weight_base_bounds` | `hunger_weight_base <= 0` and `> 1` raise `ValidationError` |
| 9 | `test_gating_sharpness_positive` | `gating_sharpness <= 0` raises `ValidationError` |
| 10 | `test_system_aw_config_full` | Full `SystemAWConfig` from dict with all fields |
| 11 | `test_system_aw_config_defaults` | `SystemAWConfig` with only agent/policy/transition; curiosity and arbitration use defaults |
| 12 | `test_config_frozen` | Assigning to any field raises `ValidationError` |
| 13 | `test_inherited_agent_validation` | `initial_energy > max_energy` still raises (inherited validator) |
| 14 | `test_reduction_config` | Config with `base_curiosity=0.0` is valid (for System A reduction) |

---

## 6. Acceptance Criteria

- [ ] All parameters from Model Section 11 are representable
- [ ] Defaults match Section 11.2 exactly
- [ ] Validators reject all out-of-domain values
- [ ] Config instantiates from a nested dict (YAML-compatible)
- [ ] Inherited sub-configs (`AgentConfig`, `PolicyConfig`, `TransitionConfig`) are imported from System A, not duplicated
- [ ] All models are frozen (immutable)
- [ ] All 14 tests pass
