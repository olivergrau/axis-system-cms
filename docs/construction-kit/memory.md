# Memory

**Package:** `axis.systems.construction_kit.memory`

**Source:** `src/axis/systems/construction_kit/memory/`

The memory package provides two bounded memory structures:

1. **Observation buffer** -- a FIFO ring buffer of recent observations,
   giving the agent short-term sensory memory.
2. **Spatial world model** -- a dead-reckoning position estimate with
   visit-count map, giving the agent spatial memory of where it has been.

Both structures are immutable Pydantic models. Update functions return
new instances rather than mutating existing ones.

---

## Observation Buffer

### BufferEntry

A single timestamped record in the observation buffer.

```python
from axis.systems.construction_kit.memory.types import BufferEntry
```

Frozen Pydantic model.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `timestep` | `int` | $\geq 0$ | Step at which the observation was recorded |
| `observation` | `Observation` | -- | The observation data |

### ObservationBuffer

Bounded FIFO buffer of recent observations.

```python
from axis.systems.construction_kit.memory.types import ObservationBuffer
```

Frozen Pydantic model.

| Field | Type | Default | Constraints | Description |
|-------|------|---------|-------------|-------------|
| `entries` | `tuple[BufferEntry, ...]` | `()` | `len <= capacity` | Stored observations (oldest first) |
| `capacity` | `int` | -- | $> 0$ | Maximum number of entries |

A model validator ensures `len(entries) <= capacity` at construction.

### `update_observation_buffer`

Appends a new observation to the buffer, dropping the oldest entry if
the buffer is full.

```python
from axis.systems.construction_kit.memory.observation_buffer import update_observation_buffer
```

```python
def update_observation_buffer(
    buffer: ObservationBuffer,
    observation: Observation,
    timestep: int,
) -> ObservationBuffer
```

Pure function -- returns a new `ObservationBuffer` instance.

---

## Spatial World Model

The spatial world model tracks the agent's position estimate via dead
reckoning and maintains a visit-count map. It uses **agent-relative
coordinates** -- the origin $(0, 0)$ is the agent's starting position
for the episode.

### WorldModelState

```python
from axis.systems.construction_kit.memory.types import WorldModelState
```

Frozen Pydantic model.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `relative_position` | `tuple[int, int]` | `(0, 0)` | Agent's estimated position in relative coordinates |
| `visit_counts` | `tuple[tuple[tuple[int, int], int], ...]` | `()` | Immutable sequence of `((x, y), count)` pairs |

### `create_world_model`

Creates the initial world model state.

```python
from axis.systems.construction_kit.memory.world_model import create_world_model
```

```python
def create_world_model() -> WorldModelState
```

**Returns:** State with `relative_position = (0, 0)` and
`visit_counts = {(0, 0): 1}`.

### `update_world_model`

Updates the world model after an action.

```python
from axis.systems.construction_kit.memory.world_model import update_world_model
```

```python
def update_world_model(
    state: WorldModelState,
    action: str,        # the chosen action
    moved: bool,        # whether the agent actually moved
) -> WorldModelState
```

**Dead reckoning formula:**

$$\hat{p}_{t+1} = \hat{p}_t + \mu_t \cdot \delta(a_t)$$

where $\mu_t = 1$ if the agent moved, $\mu_t = 0$ otherwise, and
$\delta(a_t)$ is the direction delta. The visit count at the new
position is incremented.

**Direction deltas** (agent-relative, independent of SDK coordinates):

| Action | Delta |
|--------|-------|
| up | $(0, +1)$ |
| down | $(0, -1)$ |
| left | $(-1, 0)$ |
| right | $(+1, 0)$ |
| consume | $(0, 0)$ |
| stay | $(0, 0)$ |

!!! note "Coordinate system"
    The world model uses its own agent-relative coordinate system where
    UP = $(0, +1)$ (y increases upward). This differs from the SDK's
    world grid where UP = $(0, -1)$. The visualization adapter handles
    the y-axis flip when rendering overlays.

Raises `ValueError` for unknown actions.

### `get_visit_count`

Returns the visit count at a relative position.

```python
from axis.systems.construction_kit.memory.world_model import get_visit_count
```

```python
def get_visit_count(state: WorldModelState, rel_pos: tuple[int, int]) -> int
```

Returns `0` for unvisited positions.

### `get_neighbor_position`

Computes the relative position of a neighbor in a given direction.

```python
from axis.systems.construction_kit.memory.world_model import get_neighbor_position
```

```python
def get_neighbor_position(state: WorldModelState, direction: str) -> tuple[int, int]
```

### `spatial_novelty`

Computes spatial novelty for a single neighbor direction.

```python
from axis.systems.construction_kit.memory.world_model import spatial_novelty
```

```python
def spatial_novelty(state: WorldModelState, direction: str, k: float = 1.0) -> float
```

$$\nu = \frac{1}{(1 + w)^k}$$

where $w$ is the visit count at the neighbor cell. Unvisited cells
($w = 0$) have novelty 1.0. The parameter $k$ controls decay
sharpness:

| Visit count | k=1 | k=2 | k=3 |
|:-----------:|:---:|:---:|:---:|
| 0 | 1.000 | 1.000 | 1.000 |
| 1 | 0.500 | 0.250 | 0.125 |
| 2 | 0.333 | 0.111 | 0.037 |
| 4 | 0.200 | 0.040 | 0.008 |

### `all_spatial_novelties`

Spatial novelty for all four cardinal directions.

```python
from axis.systems.construction_kit.memory.world_model import all_spatial_novelties
```

```python
def all_spatial_novelties(state: WorldModelState, k: float = 1.0) -> tuple[float, float, float, float]
```

Returns $(\nu_{\text{up}}, \nu_{\text{down}}, \nu_{\text{left}}, \nu_{\text{right}})$.

---

## Usage Example

```python
from axis.systems.construction_kit.memory.types import ObservationBuffer, WorldModelState
from axis.systems.construction_kit.memory.observation_buffer import update_observation_buffer
from axis.systems.construction_kit.memory.world_model import (
    create_world_model, update_world_model, get_visit_count,
)

# Initialize at episode start
buffer = ObservationBuffer(capacity=20)
world_model = create_world_model()  # position (0,0), visited once

# In transition():
buffer = update_observation_buffer(buffer, observation, timestep=step)
world_model = update_world_model(world_model, action="right", moved=True)

# Query the world model
visits = get_visit_count(world_model, world_model.relative_position)
```

---

## Design References

- [System A+W Formal Model](../system-design/system-a+w/01_System A+W Model.md)
  -- dead reckoning and visit-count map
- [System A+W Manual -- World Model](../manuals/system-aw-manual.md#4-world-model)
  -- coordinate system and tuning
