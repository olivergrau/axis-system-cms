# Observation

**Package:** `axis.systems.construction_kit.observation`

**Source:** `src/axis/systems/construction_kit/observation/`

The observation package provides the sensor and observation data types
that form the perception layer of the agent pipeline. The sensor reads
the world state around the agent and produces a structured observation
that downstream components (drives, policy) consume.

---

## CellObservation

A per-cell sensory vector $z_j = (b_j, r_j)$ representing what the
agent perceives about a single grid cell.

```python
from axis.systems.construction_kit.observation.types import CellObservation
```

**Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `traversability` | `float` | $[0, 1]$ | `1.0` = traversable, `0.0` = blocked or out of bounds |
| `resource` | `float` | $[0, 1]$ | Normalized resource intensity at the cell |

Frozen Pydantic model (immutable after creation).

---

## Observation

The complete sensory input for one timestep: a Von Neumann neighborhood
consisting of the current cell and four cardinal neighbors. Corresponds
to the observation vector $\mathbf{u}_t \in \mathbb{R}^{10}$.

```python
from axis.systems.construction_kit.observation.types import Observation
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `current` | `CellObservation` | Cell the agent occupies |
| `up` | `CellObservation` | Cell above (y - 1) |
| `down` | `CellObservation` | Cell below (y + 1) |
| `left` | `CellObservation` | Cell to the left (x - 1) |
| `right` | `CellObservation` | Cell to the right (x + 1) |

**Methods:**

- **`to_vector() -> tuple[float, ...]`** -- Flattens to a 10-element
  tuple in canonical order:
  $(b_c, r_c, b_{up}, r_{up}, b_{down}, r_{down}, b_{left}, r_{left}, b_{right}, r_{right})$

- **`dimension -> int`** (property) -- Always returns `10`.

Frozen Pydantic model.

---

## VonNeumannSensor

Produces an `Observation` from the world state at the agent's position.
Reads the Von Neumann neighborhood (current cell + 4 cardinal neighbors)
via the read-only `WorldView` protocol. Satisfies `SensorInterface`.

```python
from axis.systems.construction_kit.observation.sensor import VonNeumannSensor
```

**Constructor:**

```python
sensor = VonNeumannSensor()
```

No parameters. The sensor is stateless.

**Method:**

```python
def observe(self, world_view: WorldView, position: Position) -> Observation
```

Reads five cells from the world view and returns a structured
`Observation`. Each cell is projected through `_observe_cell()`:

- If the position is **out of bounds**: returns
  `CellObservation(traversability=0.0, resource=0.0)`.
- If the cell type is `"obstacle"`: traversability = `0.0`.
- Otherwise: traversability = `1.0`, resource = `cell.resource_value`.

**Direction mapping:**

| Direction | Grid offset |
|-----------|-------------|
| up | $(x, y-1)$ |
| down | $(x, y+1)$ |
| left | $(x-1, y)$ |
| right | $(x+1, y)$ |

This uses screen coordinates where y increases downward, matching the
SDK's `MOVEMENT_DELTAS` convention.

---

## Usage Example

```python
from axis.sdk.position import Position
from axis.systems.construction_kit.observation.sensor import VonNeumannSensor

sensor = VonNeumannSensor()

# In your system's decide() method:
observation = sensor.observe(world_view, world_view.agent_position)

# Access individual directions
if observation.up.traversability > 0:
    print(f"Up is reachable, resource = {observation.up.resource}")

# Flatten for downstream processing
vector = observation.to_vector()  # 10-element tuple
```

---

## Design References

- [System A Formal Specification](../system-design/system-a/01_System A Baseline.md)
  -- defines the observation model $\mathbf{u}_t$
- [System Developer Manual -- Section 10a](../manuals/system-dev-manual.md#10a-the-system-construction-kit)
  -- kit overview
