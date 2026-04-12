# WP-4: Spatial World Model

## Metadata
- Work Package: WP-4
- Title: Spatial World Model (Dead Reckoning + Visit-Count Map)
- System: System A+W
- Source File: `src/axis/systems/system_aw/world_model.py`
- Test File: `tests/systems/system_aw/test_world_model.py`
- Model Reference: `01_System A+W Model.md`, Section 4.1 (all subsections)
- Worked Examples: `02_System A+W Worked Examples.md`, Examples F1, F2, F3
- Dependencies: WP-2 (types: `WorldModelState`)

---

## 1. Objective

Implement the spatial world model as a pure-function module that manages the visit-count map through dead reckoning. This is the first entirely new component of System A+W — it has no counterpart in System A.

The module provides:
- Creation of the initial world model state
- Dead reckoning position update from action + movement signal
- Visit count queries and updates
- Per-direction spatial novelty computation

**Critical constraint:** No function in this module accepts or returns absolute position data. All spatial reasoning uses the agent-relative coordinate frame.

---

## 2. Design

### 2.1 Pure Function Architecture

All functions are **stateless and pure**: they take a `WorldModelState` (immutable) and return a new `WorldModelState`. This is consistent with the frozen Pydantic model pattern used throughout the project.

### 2.2 Internal Representation

`WorldModelState` (defined in WP-2) stores visit counts as an immutable tuple of pairs. For efficient lookup and update, the functions in this module convert to/from `dict[tuple[int, int], int]` internally:

```python
# WorldModelState.visit_counts: tuple[tuple[tuple[int, int], int], ...]
# Working dict:                 dict[tuple[int, int], int]

def _to_dict(visit_counts: tuple[tuple[tuple[int, int], int], ...]) -> dict[tuple[int, int], int]:
    return dict(visit_counts)

def _to_tuple(visit_dict: dict[tuple[int, int], int]) -> tuple[tuple[tuple[int, int], int], ...]:
    return tuple(sorted(visit_dict.items()))
```

The sort ensures deterministic serialization. The conversion cost is negligible for typical map sizes (< 200 entries for 200-step episodes).

### 2.3 Direction Delta Map

The direction delta function (Model Section 4.1.2) is defined as a module-level constant:

```python
DIRECTION_DELTAS: dict[str, tuple[int, int]] = {
    "up":      (0, +1),
    "down":    (0, -1),
    "left":    (-1, 0),
    "right":   (+1, 0),
    "consume": (0, 0),
    "stay":    (0, 0),
}
```

Action strings match the framework's action vocabulary (lowercase).

---

## 3. Function Specifications

### 3.1 `create_world_model() -> WorldModelState`

**Model reference:** Section 4.1.6

Creates the initial world model state:
- $\hat{p}_0 = (0, 0)$
- $w_0(0, 0) = 1$

```python
def create_world_model() -> WorldModelState:
    """Create the initial world model state.
    
    The agent starts at relative origin (0, 0) with one visit recorded.
    """
    return WorldModelState(
        relative_position=(0, 0),
        visit_counts=(((0, 0), 1),),
    )
```

---

### 3.2 `update_world_model(state, action, moved) -> WorldModelState`

**Model reference:** Sections 4.1.3, 4.1.5

The core dead reckoning update. This is the only function that mutates the world model.

**Inputs:**
- `state: WorldModelState` — current world model
- `action: str` — the action the agent selected (e.g., `"up"`, `"consume"`)
- `moved: bool` — whether the framework reported displacement ($\mu_t$)

**Algorithm:**
1. Look up $\Delta(a)$ from `DIRECTION_DELTAS`
2. Compute $\mu_t$: `1 if moved else 0`
3. Compute $\hat{p}_{t+1} = \hat{p}_t + \mu_t \cdot \Delta(a_t)$
4. Increment $w_{t+1}(\hat{p}_{t+1})$
5. Return new `WorldModelState`

**Edge cases:**
- Unknown action string: raise `ValueError`
- `moved=True` for non-movement actions (`consume`, `stay`): the delta is $(0, 0)$, so position is unchanged regardless. No special handling needed.

```python
def update_world_model(
    state: WorldModelState,
    action: str,
    moved: bool,
) -> WorldModelState:
    """Update world model via dead reckoning.
    
    Uses only the action taken and whether displacement occurred.
    Does NOT consume any absolute position data.
    
    Model reference: Sections 4.1.3, 4.1.5.
    """
    delta = DIRECTION_DELTAS.get(action)
    if delta is None:
        raise ValueError(f"Unknown action: {action!r}")

    dx, dy = delta
    mu = 1 if moved else 0
    px, py = state.relative_position
    new_pos = (px + mu * dx, py + mu * dy)

    visits = _to_dict(state.visit_counts)
    visits[new_pos] = visits.get(new_pos, 0) + 1

    return WorldModelState(
        relative_position=new_pos,
        visit_counts=_to_tuple(visits),
    )
```

---

### 3.3 `get_visit_count(state, rel_pos) -> int`

**Model reference:** Section 4.1.5

Returns the visit count at a relative position, defaulting to 0 for unvisited positions.

```python
def get_visit_count(state: WorldModelState, rel_pos: tuple[int, int]) -> int:
    """Return visit count at a relative position (0 if never visited)."""
    visits = _to_dict(state.visit_counts)
    return visits.get(rel_pos, 0)
```

---

### 3.4 `get_neighbor_position(state, direction) -> tuple[int, int]`

**Model reference:** Section 4.1.7

Computes the relative position of a neighbor in the given direction.

```python
def get_neighbor_position(
    state: WorldModelState,
    direction: str,
) -> tuple[int, int]:
    """Compute relative position of neighbor in given direction.
    
    direction: one of "up", "down", "left", "right"
    """
    dx, dy = DIRECTION_DELTAS[direction]
    px, py = state.relative_position
    return (px + dx, py + dy)
```

---

### 3.5 `spatial_novelty(state, direction) -> float`

**Model reference:** Section 5.2.4

Computes the spatial novelty for a neighboring direction:

$$
\nu^{spatial}_{dir} = \frac{1}{1 + w_t(\hat{p}_t + \Delta(dir))}
$$

```python
def spatial_novelty(state: WorldModelState, direction: str) -> float:
    """Compute spatial novelty for a neighboring direction.
    
    Returns 1/(1 + visit_count) -- hyperbolic decay.
    Unvisited: 1.0, visited once: 0.5, visited n times: 1/(1+n).
    
    Model reference: Section 5.2.4.
    """
    neighbor = get_neighbor_position(state, direction)
    count = get_visit_count(state, neighbor)
    return 1.0 / (1.0 + count)
```

---

### 3.6 `all_spatial_novelties(state) -> tuple[float, float, float, float]`

Convenience function returning spatial novelty for all four directions in the standard ordering (up, down, left, right). Used by the curiosity drive (WP-6).

```python
def all_spatial_novelties(
    state: WorldModelState,
) -> tuple[float, float, float, float]:
    """Compute spatial novelty for all four cardinal directions.
    
    Returns: (nu_up, nu_down, nu_left, nu_right)
    """
    return (
        spatial_novelty(state, "up"),
        spatial_novelty(state, "down"),
        spatial_novelty(state, "left"),
        spatial_novelty(state, "right"),
    )
```

---

## 4. What This Module Does NOT Do

- Does not compute sensory novelty (that uses memory — handled in WP-6)
- Does not compute composite novelty (that blends spatial + sensory — handled in WP-6)
- Does not compute the curiosity drive activation (handled in WP-6)
- Does not access `WorldView`, `Position`, or any framework/SDK types
- Does not store observations, resources, or cell types at positions

The module is self-contained: it depends only on `WorldModelState` from WP-2 and the action string vocabulary.

---

## 5. Test Plan

### File: `tests/systems/system_aw/test_world_model.py`

#### Creation Tests

| # | Test | Description |
|---|---|---|
| 1 | `test_create_initial_state` | `create_world_model()` returns position `(0,0)`, visit count at `(0,0)` = 1 |
| 2 | `test_create_empty_elsewhere` | Visit count at any other position = 0 |

#### Dead Reckoning Tests

| # | Test | Description |
|---|---|---|
| 3 | `test_move_right_updates_position` | Action `"right"`, moved=True → position changes to `(1, 0)` |
| 4 | `test_move_up_updates_position` | Action `"up"`, moved=True → position changes to `(0, 1)` |
| 5 | `test_move_left_updates_position` | Action `"left"`, moved=True → position changes to `(-1, 0)` |
| 6 | `test_move_down_updates_position` | Action `"down"`, moved=True → position changes to `(0, -1)` |
| 7 | `test_failed_move_position_unchanged` | Action `"right"`, moved=False → position stays at `(0, 0)` |
| 8 | `test_failed_move_increments_visit` | After failed move, visit count at current position increases |
| 9 | `test_consume_position_unchanged` | Action `"consume"` → position stays, visit count increments |
| 10 | `test_stay_position_unchanged` | Action `"stay"` → position stays, visit count increments |
| 11 | `test_unknown_action_raises` | Action `"fly"` → `ValueError` |

#### Spatial Novelty Tests

| # | Test | Description |
|---|---|---|
| 12 | `test_novelty_unvisited` | Unvisited neighbor → $\nu = 1.0$ |
| 13 | `test_novelty_visited_once` | Visited once → $\nu = 0.5$ |
| 14 | `test_novelty_visited_n_times` | Visited 4 times → $\nu = 0.2$ |
| 15 | `test_novelty_all_directions` | `all_spatial_novelties` returns 4-tuple in correct order |

#### Worked Example F1: 6-Step Trajectory

| # | Test | Description |
|---|---|---|
| 16 | `test_f1_full_trajectory` | Replays the 6-step trajectory from Example F1. After each step, asserts: relative position, visit count at current position, total map size. After all 6 steps: verifies the spatial novelty at position `(0, 1)` for all four directions matches the example (UP=1.0, DOWN=0.5, LEFT=1.0, RIGHT=0.5). |

#### Worked Example F2: Novelty Decay Table

| # | Test | Description |
|---|---|---|
| 17 | `test_f2_novelty_decay_table` | For visit counts $[0, 1, 2, 3, 5, 10, 20, 100]$, verify $\nu^{spatial}$ matches the table values within $\epsilon = 0.001$ |

#### Worked Example F3: Stationary Actions

| # | Test | Description |
|---|---|---|
| 18 | `test_f3_consume_then_stay` | Starting at `(3, 2)` with $w=1$: CONSUME → $w=2$, CONSUME → $w=3$, STAY → $w=4$. Position unchanged throughout. Spatial novelty at current position = $1/(1+4) = 0.2$. |

#### Immutability

| # | Test | Description |
|---|---|---|
| 19 | `test_update_returns_new_state` | Original state is not modified after `update_world_model` |
| 20 | `test_state_is_frozen` | Assigning to `relative_position` or `visit_counts` raises error |

---

## 6. Acceptance Criteria

- [ ] Initial state: $\hat{p}_0 = (0,0)$, $w_0(0,0) = 1$
- [ ] Successful movement updates relative position correctly for all 4 directions
- [ ] Failed movement ($\mu_t = 0$) leaves position unchanged but increments visit count
- [ ] Non-movement actions (CONSUME, STAY) leave position unchanged but increment visit count
- [ ] Spatial novelty: unvisited = 1.0, visited once = 0.5, visited $n$ times = $\frac{1}{1+n}$
- [ ] **No absolute position data is consumed or returned at any point**
- [ ] All functions are pure (return new state, never mutate input)
- [ ] Numerical match with worked examples F1, F2, F3
- [ ] All 20 tests pass
