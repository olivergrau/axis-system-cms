# Grid World Cooldown Engineering Spec

## 1. Purpose

This engineering specification translates the draft direction in:

- [Grid World Cooldown Draft](./draft.md)

into a practical implementation shape for the current AXIS world framework.

The implementation goal is no longer a separate cooldown world.

The goal is to evolve the existing `grid_2d` world so it can support:

- optional resource regeneration cooldown
- optional toroidal topology

while preserving backward compatibility for existing `grid_2d` experiments.


## 2. Implementation Goal

The AXIS `grid_2d` world should gain two new optional semantics:

- delayed resource regeneration after depletion
- configurable edge behavior

These should be controlled by config parameters rather than by introducing new
world families.

The first wave should satisfy these requirements:

- existing `grid_2d` configs continue to behave exactly as before
- cooldown is disabled by default
- bounded topology remains the default
- toroidal wrapping is enabled only when explicitly configured
- systems remain unaware of the extra internal world state


## 3. Architectural Placement

The work should remain localized to the existing `grid_2d` implementation.

Primary modules to change:

- `src/axis/world/grid_2d/config.py`
- `src/axis/world/grid_2d/model.py`
- `src/axis/world/grid_2d/dynamics.py`
- `src/axis/world/grid_2d/factory.py`

Likely additional integration points:

- `src/axis/world/actions.py`
- `src/axis/world/registry.py` only if registration or comments need cleanup
- tests under:
  - `tests/world/`
  - possibly framework or visualization integration tests if topology or
    metadata assumptions surface there


## 4. Existing Constraints

### 4.1 World contract compatibility

`grid_2d` must continue to satisfy:

- `WorldView`
- `MutableWorldProtocol`

This means the implementation must preserve:

- `get_cell()`
- `is_within_bounds()`
- `is_traversable()`
- `extract_resource()`
- `tick()`
- `snapshot()`
- `world_metadata()`

### 4.2 Backward compatibility

The first wave must preserve current behavior for existing configs.

That implies:

- `resource_regen_cooldown_steps` defaults to `0`
- `topology` defaults to bounded behavior

### 4.3 System-facing surface

The system-facing `CellView` should remain unchanged.

Cooldown state and topology mode are world-internal semantics, not new
system-visible concepts.


## 5. New Configuration Surface

### 5.1 `Grid2DWorldConfig`

Extend `Grid2DWorldConfig` with:

- `resource_regen_cooldown_steps: int = Field(default=0, ge=0)`
- `topology: str = "bounded"`

### 5.2 Recommended topology values

The first wave should support exactly:

- `bounded`
- `toroidal`

This can later be tightened to an enum if that improves validation clarity.

### 5.3 Backward-compatible defaults

The config defaults must preserve the existing world:

- no cooldown
- no wrapping


## 6. Internal Cell Model Changes

The current `grid_2d` internal `Cell` model contains:

- `cell_type`
- `resource_value`
- `regen_eligible`

That is insufficient for cooldown semantics.

### 6.1 Required new field

Add:

- `cooldown_remaining: int = Field(default=0, ge=0)`

### 6.2 Intended invariants

Recommended invariants:

- obstacle cells:
  - `resource_value == 0`
  - `regen_eligible == False`
  - `cooldown_remaining == 0`
- resource cells:
  - `resource_value > 0`
  - `cooldown_remaining == 0`
- empty cells:
  - `resource_value == 0`
  - `cooldown_remaining >= 0`

The first wave should enforce at least the obstacle and resource constraints.


## 7. Cooldown Semantics

### 7.1 Trigger condition

Cooldown should be applied only when a resource cell is fully depleted.

That means:

- partial extraction does not start cooldown
- depletion to zero does start cooldown

### 7.2 Extraction integration

`World.extract_resource()` should be updated so that:

- if the cell remains a resource after extraction:
  - `cooldown_remaining = 0`
- if the cell is fully depleted:
  - the new empty cell receives
    `cooldown_remaining = resource_regen_cooldown_steps`

### 7.3 Tick integration

`tick()` should continue to own regeneration timing.

For eligible, non-obstacle cells:

- if `cooldown_remaining > 0`:
  - decrement cooldown
  - do not regenerate this tick
- else:
  - proceed with ordinary regeneration

### 7.4 Recommended first-wave interpretation

The draft recommends:

- if a cell had `cooldown_remaining = 1` at tick start
- that tick decrements it to `0`
- regeneration still does not happen during that same tick
- regeneration becomes eligible on the following tick

This is the cleaner interpretation for implementation and tests.


## 8. Dynamics Refactor

The current `apply_regeneration()` assumes only:

- non-obstacle
- regen-eligible
- additive regrowth

It should be extended to respect cooldown.

### 8.1 Suggested shape

Keep `apply_regeneration(world, regen_rate=...)`, but make it:

- read `cooldown_remaining` when present
- update cells by:
  - decrementing cooldown when needed
  - skipping regrowth for cooling cells
  - regrowing only cooldown-free eligible cells

### 8.2 Compatibility note

Because `apply_regeneration()` currently works against a generic
`MutableWorldProtocol`, we should be careful not to break any other world that
may reuse it.

The safer first implementation is:

- keep cooldown logic inside `grid_2d`
- either:
  - extend `apply_regeneration()` in a backward-compatible way
  - or split cooldown-aware regeneration into a `grid_2d`-specific helper

Recommended direction:

- extend `apply_regeneration()` conservatively only if all accessed fields are
  guaranteed on `grid_2d` cells
- otherwise create a `grid_2d`-specific regeneration helper and call it from
  `World.tick()`


## 9. Topology Semantics

### 9.1 Bounded mode

`bounded` must preserve the current behavior:

- out-of-bounds positions are invalid
- `is_within_bounds()` behaves exactly as today
- movement off-grid is blocked by ordinary world checks

### 9.2 Toroidal mode

When `topology = "toroidal"`:

- horizontal overflow wraps to the opposite side
- vertical overflow wraps to the opposite side

The key design question is where wrapping should occur.

### 9.3 Recommended placement for wrapping logic

Wrapping should happen in the movement/action handling layer, not in
`is_within_bounds()` itself.

Reason:

- `is_within_bounds()` should retain literal geometric meaning
- wrapping is an action-application semantic
- this keeps read-only geometry clearer for debugging and tests

That implies a likely change in:

- `src/axis/world/actions.py`

The movement handler should:

- detect toroidal mode from the world
- compute wrapped destination coordinates before traversability checks

### 9.4 World model support

`World` should therefore expose enough internal information for movement
handlers to know whether toroidal behavior is active.

Simplest first-wave option:

- store `_topology`
- expose a small property like `topology`


## 10. World Model Changes

### 10.1 `World.__init__`

Extend the world constructor with:

- `regen_cooldown_steps`
- `topology`

These should be stored as world-owned dynamics and topology state.

### 10.2 `world_metadata()`

The first wave may optionally expose:

- topology
- maybe aggregate cooldown information

This is not required for correctness, but could help later replay and
debugging.

Recommended first-wave behavior:

- include `topology`
- do not expose per-cell cooldown metadata unless needed


## 11. Factory Changes

`grid_2d.factory.create_world()` should:

- parse the new config fields
- pass them into `World(...)`
- preserve current obstacle and sparse eligibility logic

No new registry branch should be needed because the world type remains
`grid_2d`.


## 12. Existing Toroidal World

The current separate `toroidal` world should not necessarily be deleted in the
first implementation wave.

Recommended first-wave stance:

- implement toroidal topology inside `grid_2d`
- keep the existing `toroidal` world temporarily
- treat it as legacy / migration-compatible until the new parameterized path is
  proven stable

This reduces migration risk.


## 13. Test Strategy

The first wave needs focused world-level coverage.

### 13.1 Cooldown tests

Add or update tests for:

- config parsing with default cooldown
- config parsing with explicit cooldown
- depletion starts cooldown
- partial extraction does not start cooldown
- cooldown decrements over ticks
- no regrowth while cooldown is active
- regrowth resumes after cooldown expires
- zero cooldown preserves current immediate-regrowth semantics

### 13.2 Topology tests

Add or update tests for:

- default bounded behavior unchanged
- toroidal movement wraps left/right
- toroidal movement wraps up/down
- wrapped movement still respects obstacle traversability at the wrapped target

### 13.3 Compatibility tests

Protect:

- existing bounded `grid_2d` behavior
- existing experiment configs
- snapshot behavior
- system-facing `CellView` stability

### 13.4 Legacy toroidal coexistence

If the old `toroidal` world remains registered in the first wave, tests should
avoid making contradictory assumptions about immediate removal.


## 14. Suggested Delivery Sequence

The recommended implementation order is:

1. extend `Grid2DWorldConfig`
2. extend `Cell` and `World` internal state
3. update extraction and regeneration for cooldown
4. add cooldown-focused tests
5. add topology parameter storage
6. update movement handling for toroidal wrapping
7. add topology-focused tests
8. optionally add minimal metadata exposure

This keeps regeneration changes and topology changes logically separable even
if they ship under one idea.


## 15. Risks And Mitigations

### 15.1 Risk: `grid_2d` becomes too overloaded

Mitigation:

- keep the added semantics narrow
- use small explicit config parameters
- avoid broad world-family branching beyond bounded vs toroidal

### 15.2 Risk: cooldown logic leaks into system-facing contracts

Mitigation:

- keep cooldown entirely in internal cell/world state
- keep `CellView` unchanged

### 15.3 Risk: toroidal integration changes bounded behavior

Mitigation:

- make bounded mode the explicit default
- add regression tests for current movement semantics

### 15.4 Risk: generic regeneration helpers become harder to reason about

Mitigation:

- keep cooldown-aware logic localized to `grid_2d` if generic abstraction
  becomes awkward


## 16. Expected First-Wave Outcome

After implementation:

- `grid_2d` supports delayed resource regrowth through
  `resource_regen_cooldown_steps`
- `grid_2d` supports bounded or toroidal topology through `topology`
- existing experiments remain unchanged by default
- AXIS gains more experimental flexibility without multiplying world types
