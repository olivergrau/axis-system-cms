# WP-6: Curiosity Drive Module

## Metadata
- Work Package: WP-6
- Title: Curiosity Drive Module
- System: System A+W
- Source File: `src/axis/systems/system_aw/drive_curiosity.py`
- Test File: `tests/systems/system_aw/test_drive_curiosity.py`
- Model Reference: `01_System A+W Model.md`, Sections 5.2 (all subsections), 6.3
- Worked Examples: `02_System A+W Worked Examples.md`, Examples A1, B1, C1, E2, F1, F2
- Dependencies: WP-2 (types: `CuriosityDriveOutput`, `WorldModelState`), WP-4 (world model: `all_spatial_novelties`)

---

## 1. Objective

Implement the curiosity drive — the most novel component of System A+W. The curiosity drive computes a composite novelty signal from two independent channels (spatial and sensory), derives the drive activation, and produces per-action contributions that bias the agent toward exploration.

This module has **no counterpart** in System A.

---

## 2. Design

### 2.1 Computation Pipeline

The curiosity drive computation follows a strict pipeline:

```
                 WorldModelState          Observation + MemoryState
                      │                          │
            ┌─────────▼──────────┐    ┌──────────▼──────────┐
            │  Spatial Novelty   │    │  Sensory Novelty    │
            │  ν^spatial (×4)    │    │  ν^sensory (×4)     │
            └─────────┬──────────┘    └──────────┬──────────┘
                      │                          │
                      └────────┬─────────────────┘
                               │ α-blend
                     ┌─────────▼──────────┐
                     │  Composite Novelty  │
                     │  ν_dir (×4)         │
                     └─────────┬──────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                   │
   ┌────────▼────────┐  ┌─────▼──────┐  ┌────────▼────────┐
   │  Move contribs  │  │ CONSUME/   │  │  Drive          │
   │  φ_C = ν_dir    │  │ STAY pentl │  │  Activation     │
   │  (×4 dirs)      │  │ = -λ_explr │  │  d_C = μ_C·f(ν) │
   └────────┬────────┘  └─────┬──────┘  └────────┬────────┘
            │                  │                   │
            └──────────────────┼───────────────────┘
                               │
                     ┌─────────▼──────────┐
                     │  CuriosityDrive    │
                     │  Output            │
                     └────────────────────┘
```

### 2.2 Module Structure

The module exposes one class (`SystemAWCuriosityDrive`) and several pure helper functions that can be tested independently:

| Function | Model Section | Purpose |
|---|---|---|
| `compute_spatial_novelty` | 5.2.4 | Per-direction $\nu^{spatial}$ from world model |
| `compute_sensory_novelty` | 5.2.5 | Per-direction $\nu^{sensory}$ from observation + memory |
| `compute_composite_novelty` | 5.2.6 | $\alpha$-weighted blend of spatial and sensory |
| `compute_novelty_saturation` | 5.2.2 | $\bar{\nu}_t$ from memory |
| `compute_curiosity_activation` | 5.2.1 | $d_C = \mu_C \cdot (1 - \bar{\nu}_t)$ |
| `SystemAWCuriosityDrive.compute` | 6.3 | Full pipeline → `CuriosityDriveOutput` |

### 2.3 Dependency on WP-4

Spatial novelty could be computed entirely within this module by calling `get_visit_count` on the world model. However, WP-4 already provides `all_spatial_novelties(state) -> tuple[float, float, float, float]`, which is exactly what this module needs. Using it avoids duplicating the $\frac{1}{1+n}$ formula and keeps the spatial novelty definition in one place.

---

## 3. Function Specifications

### 3.1 `compute_spatial_novelty`

**Model reference:** Section 5.2.4

Delegates to WP-4's `all_spatial_novelties`.

```python
from axis.systems.system_aw.world_model import all_spatial_novelties

def compute_spatial_novelty(
    world_model: WorldModelState,
) -> tuple[float, float, float, float]:
    """Per-direction spatial novelty from the visit-count map.
    
    Returns: (ν_up, ν_down, ν_left, ν_right)
    
    ν^spatial_dir = 1 / (1 + w_t(p̂_t + Δ(dir)))
    """
    return all_spatial_novelties(world_model)
```

---

### 3.2 `compute_sensory_novelty`

**Model reference:** Section 5.2.5

Computes per-direction sensory novelty by comparing the current observation with the mean observation stored in memory.

**Inputs:**
- `observation: Observation` — current sensor output
- `memory: MemoryState` — episodic memory buffer

**Algorithm:**

For each direction $dir \in \{up, down, left, right\}$:

$$
\bar{r}_{dir} = \frac{1}{|m_t|} \sum_{j=1}^{|m_t|} r_{dir}^{(j)}
$$

$$
\nu^{sensory}_{dir} = |r_{dir}(t) - \bar{r}_{dir}|
$$

When memory is empty ($|m_t| = 0$): $\bar{r}_{dir} = 0$, so $\nu^{sensory}_{dir} = r_{dir}(t)$.

```python
def compute_sensory_novelty(
    observation: Observation,
    memory: MemoryState,
) -> tuple[float, float, float, float]:
    """Per-direction sensory novelty from observation vs memory mean.
    
    Returns: (ν_up, ν_down, ν_left, ν_right)
    
    ν^sensory_dir = |r_dir(t) - mean(r_dir over memory)|
    When memory is empty, mean = 0.
    """
    current = (
        observation.up.resource,
        observation.down.resource,
        observation.left.resource,
        observation.right.resource,
    )

    if len(memory.entries) == 0:
        return current  # |r - 0| = r (all non-negative)

    n = len(memory.entries)
    means = [0.0, 0.0, 0.0, 0.0]
    for entry in memory.entries:
        obs = entry.observation
        means[0] += obs.up.resource
        means[1] += obs.down.resource
        means[2] += obs.left.resource
        means[3] += obs.right.resource
    means = [m / n for m in means]

    return tuple(abs(c - m) for c, m in zip(current, means))
```

**Note on directions:** The sensory novelty is computed for the 4 cardinal neighbors, not for the current cell. This mirrors the spatial novelty (which is also per-neighbor-direction). The current cell's resource is used by the hunger drive, not the curiosity drive.

---

### 3.3 `compute_composite_novelty`

**Model reference:** Section 5.2.6

$$
\nu_{dir} = \alpha \cdot \nu^{spatial}_{dir} + (1 - \alpha) \cdot \nu^{sensory}_{dir}
$$

```python
def compute_composite_novelty(
    spatial: tuple[float, float, float, float],
    sensory: tuple[float, float, float, float],
    alpha: float,
) -> tuple[float, float, float, float]:
    """Alpha-weighted blend of spatial and sensory novelty.
    
    alpha=1.0: pure spatial (visit-count only)
    alpha=0.0: pure sensory (observation-difference only)
    alpha=0.5: equal weighting (default)
    """
    return tuple(
        alpha * s_spatial + (1 - alpha) * s_sensory
        for s_spatial, s_sensory in zip(spatial, sensory)
    )
```

---

### 3.4 `compute_novelty_saturation`

**Model reference:** Section 5.2.2

The novelty saturation $\bar{\nu}_t$ measures how much novel experience the agent has recently encountered.

$$
\bar{\nu}_t = \frac{1}{|m_t|} \sum_{j=1}^{|m_t|} \sigma_j
$$

where $\sigma_j$ is the sensory surprise of the $j$-th memory entry. To compute $\sigma_j$, we need to compare each memory entry against the memory mean. A practical approximation: compute the per-entry deviation from the overall mean, averaged across directions.

```python
def compute_novelty_saturation(memory: MemoryState) -> float:
    """Compute mean novelty saturation from memory.
    
    Returns 0.0 when memory is empty (maximum curiosity).
    
    σ_j = mean over directions of |r_dir^(j) - mean(r_dir)|
    ν̄_t = mean over entries of σ_j
    """
    entries = memory.entries
    if len(entries) == 0:
        return 0.0

    n = len(entries)
    directions = ["up", "down", "left", "right"]

    # Compute per-direction means across all entries
    dir_means = {d: 0.0 for d in directions}
    for entry in entries:
        obs = entry.observation
        dir_means["up"] += obs.up.resource
        dir_means["down"] += obs.down.resource
        dir_means["left"] += obs.left.resource
        dir_means["right"] += obs.right.resource
    dir_means = {d: v / n for d, v in dir_means.items()}

    # Compute per-entry surprise σ_j
    total_surprise = 0.0
    for entry in entries:
        obs = entry.observation
        entry_resources = {
            "up": obs.up.resource,
            "down": obs.down.resource,
            "left": obs.left.resource,
            "right": obs.right.resource,
        }
        sigma_j = sum(
            abs(entry_resources[d] - dir_means[d]) for d in directions
        ) / len(directions)
        total_surprise += sigma_j

    return total_surprise / n
```

**When memory is empty:** Returns 0.0. This means $d_C = \mu_C \cdot (1 - 0) = \mu_C$ — curiosity is at maximum. This is the correct behavior: an agent with no experience should be maximally curious.

**When all memory entries are identical:** All $\sigma_j = 0$, so $\bar{\nu}_t = 0$ and curiosity is at maximum. This is also correct: monotonous experience drives curiosity up.

---

### 3.5 `compute_curiosity_activation`

**Model reference:** Section 5.2.1

$$
d_C(t) = \mu_C \cdot (1 - \bar{\nu}_t)
$$

```python
def compute_curiosity_activation(
    base_curiosity: float,
    novelty_saturation: float,
) -> float:
    """Compute curiosity drive activation.
    
    d_C = mu_C * (1 - ν̄_t)
    
    Bounded to [0, mu_C].
    """
    return base_curiosity * (1.0 - novelty_saturation)
```

---

### 3.6 `SystemAWCuriosityDrive.compute`

**Model reference:** Sections 5.2 + 6.3

The full pipeline. Takes all inputs and returns `CuriosityDriveOutput`.

```python
class SystemAWCuriosityDrive:
    """Curiosity drive for System A+W.
    
    Computes the curiosity drive activation and per-action
    contributions from the composite novelty signal.
    """

    def __init__(
        self,
        *,
        base_curiosity: float,
        spatial_sensory_balance: float,
        explore_suppression: float,
    ) -> None:
        self._mu_c = base_curiosity
        self._alpha = spatial_sensory_balance
        self._lambda_explore = explore_suppression

    def compute(
        self,
        observation: Observation,
        memory: MemoryState,
        world_model: WorldModelState,
    ) -> CuriosityDriveOutput:
        """Compute curiosity drive output.
        
        Pipeline:
        1. Spatial novelty (from world model)
        2. Sensory novelty (from observation + memory)
        3. Composite novelty (alpha-blend)
        4. Novelty saturation (from memory)
        5. Drive activation
        6. Action contributions
        """
        # Step 1-3: Novelty computation
        spatial = compute_spatial_novelty(world_model)
        sensory = compute_sensory_novelty(observation, memory)
        composite = compute_composite_novelty(spatial, sensory, self._alpha)

        # Step 4-5: Drive activation
        saturation = compute_novelty_saturation(memory)
        activation = compute_curiosity_activation(self._mu_c, saturation)

        # Step 6: Action contributions (Model Section 6.3)
        # Movement: φ_C(dir) = ν_dir (composite novelty)
        # CONSUME:  φ_C = -λ_explore
        # STAY:     φ_C = -λ_explore
        action_contributions = (
            composite[0],               # UP
            composite[1],               # DOWN
            composite[2],               # LEFT
            composite[3],               # RIGHT
            -self._lambda_explore,      # CONSUME
            -self._lambda_explore,      # STAY
        )

        return CuriosityDriveOutput(
            activation=activation,
            spatial_novelty=spatial,
            sensory_novelty=sensory,
            composite_novelty=composite,
            action_contributions=action_contributions,
        )
```

### 3.7 Construction from Config

The orchestrator (WP-10) constructs the curiosity drive from `SystemAWConfig`:

```python
curiosity_drive = SystemAWCuriosityDrive(
    base_curiosity=config.curiosity.base_curiosity,
    spatial_sensory_balance=config.curiosity.spatial_sensory_balance,
    explore_suppression=config.curiosity.explore_suppression,
)
```

---

## 4. Boundary Conditions

| Condition | $\bar{\nu}_t$ | $d_C$ | Behavior |
|---|---|---|---|
| Empty memory | 0.0 | $\mu_C$ | Maximum curiosity — no experience yet |
| All-identical memories | 0.0 | $\mu_C$ | Maximum curiosity — monotonous experience |
| Highly diverse memories | high | low | Curiosity temporarily sated |
| $\mu_C = 0$ | any | 0.0 | Curiosity disabled — reduction to System A |
| $\alpha = 1$ | - | - | Pure spatial novelty — no memory dependency in novelty |
| $\alpha = 0$ | - | - | Pure sensory novelty — no world model dependency in novelty |

---

## 5. Test Plan

### File: `tests/systems/system_aw/test_drive_curiosity.py`

#### Spatial Novelty Tests

| # | Test | Description |
|---|---|---|
| 1 | `test_spatial_novelty_all_unvisited` | All four neighbors unvisited → all $\nu^{spatial} = 1.0$ |
| 2 | `test_spatial_novelty_mixed` | Mix of visited/unvisited → correct per-direction values |

#### Sensory Novelty Tests

| # | Test | Description |
|---|---|---|
| 3 | `test_sensory_novelty_empty_memory` | Empty memory → $\nu^{sensory}_{dir} = r_{dir}$ |
| 4 | `test_sensory_novelty_matching_memory` | Observation matches memory mean → all $\nu^{sensory} = 0$ |
| 5 | `test_sensory_novelty_divergent` | Observation differs from memory mean → correct absolute differences |

#### Composite Novelty Tests

| # | Test | Description |
|---|---|---|
| 6 | `test_composite_alpha_one` | $\alpha = 1$ → composite = spatial (sensory ignored) |
| 7 | `test_composite_alpha_zero` | $\alpha = 0$ → composite = sensory (spatial ignored) |
| 8 | `test_composite_alpha_half` | $\alpha = 0.5$ → composite = mean of spatial and sensory |

#### Novelty Saturation Tests

| # | Test | Description |
|---|---|---|
| 9 | `test_saturation_empty_memory` | Returns 0.0 |
| 10 | `test_saturation_identical_entries` | All same observation → returns 0.0 |
| 11 | `test_saturation_diverse_entries` | Varied observations → returns positive value |

#### Drive Activation Tests

| # | Test | Description |
|---|---|---|
| 12 | `test_activation_max` | $\bar{\nu}_t = 0$ → $d_C = \mu_C$ |
| 13 | `test_activation_zero_base` | $\mu_C = 0$ → $d_C = 0$ regardless of saturation |
| 14 | `test_activation_partial` | $\mu_C = 1.0$, $\bar{\nu}_t = 0.3$ → $d_C = 0.7$ |

#### Action Contributions Tests

| # | Test | Description |
|---|---|---|
| 15 | `test_movement_contributions_equal_composite` | $\phi_C(dir)$ = composite novelty for each direction |
| 16 | `test_consume_suppressed` | $\phi_C(CONSUME) = -\lambda_{explore}$ |
| 17 | `test_stay_suppressed` | $\phi_C(STAY) = -\lambda_{explore}$ |

#### Full Pipeline Tests

| # | Test | Description |
|---|---|---|
| 18 | `test_full_pipeline_output_type` | `compute()` returns `CuriosityDriveOutput` |
| 19 | `test_full_pipeline_all_fields_present` | All 5 fields populated: activation, spatial, sensory, composite, contributions |

#### Worked Example Verification

| # | Test | Description |
|---|---|---|
| 20 | `test_example_a1_curiosity` | Example A1: $e=90$, all unvisited, empty memory. Verify: spatial novelty all 1.0, sensory novelty = $(0.0, 0.0, 0.3, 0.0)$, composite = $(0.50, 0.50, 0.65, 0.50)$, $d_C = 1.0$, contributions = $(0.50, 0.50, 0.65, 0.50, -0.3, -0.3)$ |
| 21 | `test_example_b1_curiosity` | Example B1: Verify spatial, sensory, and composite novelty match tables. Verify $d_C = 0.85$. |
| 22 | `test_example_c1_curiosity` | Example C1: Verify contributions are tiny (< 0.002 per direction) despite high composite novelty, because $w_C$ is near zero in the final scores (but that's WP-7's responsibility — here just verify the raw $\phi_C$ values). |
| 23 | `test_example_e2_alpha_sensitivity` | Example E2: Verify composite novelty for $\alpha = 0.0$, $\alpha = 0.5$, $\alpha = 1.0$ for a cell visited 3 times with resource surprise. |

#### Reduction Tests

| # | Test | Description |
|---|---|---|
| 24 | `test_zero_base_curiosity` | $\mu_C = 0$ → $d_C = 0$, but $\phi_C$ values are still computed (the arbitration layer will zero them out via $d_C = 0$) |
| 25 | `test_alpha_one_no_memory_dependency` | $\alpha = 1.0$ → composite novelty is independent of memory content |
| 26 | `test_alpha_zero_no_world_model_dependency` | $\alpha = 0.0$ → composite novelty is independent of visit counts |

---

## 6. Acceptance Criteria

- [ ] Spatial novelty matches Section 5.2.4 (hyperbolic decay from visit counts)
- [ ] Sensory novelty matches Section 5.2.5 (absolute difference from memory mean)
- [ ] Composite novelty matches Section 5.2.6 ($\alpha$-weighted blend)
- [ ] Novelty saturation returns 0.0 for empty or monotonous memory
- [ ] $d_C$ range: $[0, \mu_C]$
- [ ] Movement contributions equal composite novelty per direction
- [ ] CONSUME and STAY produce $-\lambda_{explore}$
- [ ] Numerical match with worked examples A1, B1, C1, E2
- [ ] $\alpha = 1$ eliminates memory dependency in composite novelty
- [ ] $\alpha = 0$ eliminates world model dependency in composite novelty
- [ ] $\mu_C = 0$ produces zero activation
- [ ] All 26 tests pass
