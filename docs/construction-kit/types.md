# Types

**Package:** `axis.systems.construction_kit.types`

**Source:** `src/axis/systems/construction_kit/types/`

Shared configuration models and the consume action handler. These types
enforce consistent parameter validation across all systems that use
energy-based survival and the standard action space.

---

## AgentConfig

Agent initialization parameters: energy capacity and observation buffer
size.

```python
from axis.systems.construction_kit.types.config import AgentConfig
```

Frozen Pydantic model.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `initial_energy` | `float` | $> 0$ | Starting energy at episode begin |
| `max_energy` | `float` | $> 0$ | Energy capacity (gains capped here) |
| `buffer_capacity` | `int` | $> 0$ | Observation buffer size |

**Validation:** `initial_energy <= max_energy` (enforced by model
validator).

```yaml
# In experiment config:
system:
  agent:
    initial_energy: 100.0
    max_energy: 100.0
    buffer_capacity: 20
```

---

## PolicyConfig

Action selection parameters for the softmax policy.

```python
from axis.systems.construction_kit.types.config import PolicyConfig
```

Frozen Pydantic model.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `selection_mode` | `str` | -- | `"sample"` or `"argmax"` |
| `temperature` | `float` | $> 0$ | Softmax temperature |
| `stay_suppression` | `float` | $\geq 0$ | Penalty for stay in hunger drive |
| `consume_weight` | `float` | $> 0$ | Bonus for consume action |

```yaml
system:
  policy:
    selection_mode: "sample"
    temperature: 1.5
    stay_suppression: 0.1
    consume_weight: 2.5
```

---

## TransitionConfig

Energy dynamics parameters: action costs and resource-to-energy
conversion.

```python
from axis.systems.construction_kit.types.config import TransitionConfig
```

Frozen Pydantic model.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `move_cost` | `float` | $> 0$ | Energy cost per movement action |
| `consume_cost` | `float` | $> 0$ | Energy cost for consume action |
| `stay_cost` | `float` | $\geq 0$ | Energy cost for stay action |
| `max_consume` | `float` | $> 0$ | Maximum resource extracted per consume |
| `energy_gain_factor` | `float` | $\geq 0$ | Multiplier: energy = resource $\times$ factor |

```yaml
system:
  transition:
    move_cost: 0.5
    consume_cost: 0.5
    stay_cost: 0.3
    max_consume: 1.0
    energy_gain_factor: 15.0
```

---

## `handle_consume`

The shared consume action handler. Extracts resource from the agent's
current cell and returns the result as an `ActionOutcome`. Registered
with the `ActionRegistry` via `action_handlers()`.

```python
from axis.systems.construction_kit.types.actions import handle_consume
```

### Signature

```python
def handle_consume(
    world: MutableWorldProtocol,
    *,
    context: dict[str, Any],
) -> ActionOutcome
```

### Behavior

1. Reads the agent's current position from `world.agent_position`.
2. Calls `world.extract_resource(pos, max_consume)` where `max_consume`
   comes from `context["max_consume"]`.
3. Returns `ActionOutcome` with:
   - `action = "consume"`
   - `moved = False`
   - `new_position = pos`
   - `data = {"consumed": bool, "resource_consumed": float}`

The `resource_consumed` value is the actual amount extracted -- it may
be less than `max_consume` if the cell has less resource available.

### Registration

In your system's `action_handlers()` and `action_context()`:

```python
def action_handlers(self) -> dict[str, Any]:
    return {"consume": handle_consume}

def action_context(self) -> dict[str, Any]:
    return {"max_consume": self._config.transition.max_consume}
```

---

## Usage Example

```python
from axis.systems.construction_kit.types.config import (
    AgentConfig, PolicyConfig, TransitionConfig,
)
from axis.systems.construction_kit.types.actions import handle_consume

# Build system config using shared types
class MySystemConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    agent: AgentConfig
    policy: PolicyConfig
    transition: TransitionConfig

# Parse from experiment YAML
config = MySystemConfig(**raw_system_dict)

# Access validated parameters
sensor = VonNeumannSensor()
drive = HungerDrive(
    consume_weight=config.policy.consume_weight,
    stay_suppression=config.policy.stay_suppression,
    max_energy=config.agent.max_energy,
)
```

---

## Design References

- [Configuration Reference](../manuals/config-manual.md)
  -- full YAML config documentation
- [System Developer Manual -- Section 6](../manuals/system-dev-manual.md#6-writing-a-config-file-for-your-system)
  -- config file structure
