# Grid World Cooldown Draft

## Purpose

This draft explores consolidating the current grid-world variants into a richer
parameterized `grid_2d` world.

The immediate motivation is to create a world that is:

- mechanically close to the existing `grid_2d` world
- fully compatible with the current AXIS world contracts
- but behaviorally richer along two controlled axes:
  - emptied resource cells do **not** begin regrowing immediately when a
    cooldown is configured
  - edge behavior can be either bounded or toroidal


## Starting Point

AXIS already has a pluggable world architecture:

- world selection is driven by `world.world_type`
- world instances are created through the world registry
- all worlds must satisfy `MutableWorldProtocol`
- systems see only the read-only `WorldView`

The built-in worlds currently include:

- `grid_2d`
- `toroidal`
- `signal_landscape`

Of these, `grid_2d` is the direct implementation target.

It already provides:

- rectangular grid topology
- cell-based resources
- obstacles
- deterministic regeneration
- configurable regeneration eligibility

The proposal is therefore best understood as:

> an extension of the existing `grid_2d` world whose regeneration semantics
> optionally include depletion cooldown and whose topology can be configured


## Core Idea

In the current `grid_2d` world:

- if a resource cell is depleted to zero
- and the cell is regeneration-eligible
- then regeneration may begin again on the very next `tick()`

The proposed `grid_2d` extension changes this rule when cooldown is enabled.

When a resource cell is depleted:

- the cell enters a cooldown state
- regeneration is suppressed for a fixed number of world ticks
- only after the cooldown expires does ordinary regeneration resume

This means the world still supports renewable resources, but renewal is no
longer immediate.


## Intended Behavioral Effect

The point of the cooldown is not merely cosmetic.

It changes the ecological structure of the world.

Without cooldown:

- a high-value resource location remains attractive almost continuously
- repeated revisits can be rewarded quickly
- local exploitation is comparatively easy

With cooldown:

- recently depleted locations become temporarily unproductive
- returning too early is wasteful
- movement and revisit timing matter more
- the world pushes systems toward broader search or delayed return behavior

This should create a cleaner separation between:

- exploitation of currently available resource
- and timing-aware revisitation


## Architectural Direction

The cleaner direction is probably **not** to introduce a new world type for
cooldown, and possibly not to keep toroidal as a separate world type either.

Instead:

- extend `grid_2d`
- add one new optional cooldown field
- add one topology field
- keep the default behavior unchanged for existing experiments by setting the
  default cooldown to `0` and the default topology to bounded behavior

This is attractive because:

- the grid representation does not change
- the cell semantics do not fundamentally change
- the movement model changes only at boundary handling
- the regeneration model changes only by one additional conditional timing rule
- existing `grid_2d` experiments remain backward-compatible by default
- existing `toroidal` behavior can be represented as configuration rather than
  as a separate world family

So the recommended implementation direction is:

- keep world type:
  - `grid_2d`
- extend:
  - `src/axis/world/grid_2d/config.py`
  - `src/axis/world/grid_2d/model.py`
  - `src/axis/world/grid_2d/dynamics.py`
  - `src/axis/world/grid_2d/factory.py`
  - and the boundary / movement integration points where topology is enforced


## Required Compatibility

The world must still satisfy the current AXIS world contracts.

That means the extended `grid_2d` world must still support at least:

- `WorldView`
  - `width`
  - `height`
  - `agent_position`
  - `get_cell()`
  - `is_within_bounds()`
  - `is_traversable()`
- `MutableWorldProtocol`
  - mutable `agent_position`
  - `get_internal_cell()`
  - `set_cell()`
  - `tick()`
  - `extract_resource()`
  - `snapshot()`
  - `world_metadata()`

This is important because:

- systems must remain world-agnostic
- the framework runner must continue to own the episode loop
- action handling must continue to work through the existing world/action
  contracts


## Scope Of Similarity To `grid_2d`

The updated `grid_2d` world should preserve the most useful operational
properties it already has.

Recommended first-wave similarities:

- rectangular grid storage
- same movement semantics
- same obstacle semantics
- same `CellView` projection to systems:
  - `cell_type`
  - `resource_value`
- same extraction semantics:
  - `extract_resource(position, max_amount)`
- same regeneration-eligibility concepts:
  - `all_traversable`
  - `sparse_fixed_ratio`

This makes the new world easy to reason about and easy to compare against the
existing baseline.


## New Semantic Additions

The world should add two optional semantic extensions:

- resource regeneration cooldown
- configurable topology

This should be represented explicitly in configuration.

Recommended new parameter:

- `resource_regen_cooldown_steps`

Recommended topology parameter:

- `topology`

Interpretation:

- integer number of ticks a depleted cell must wait before regeneration is
  allowed again

Recommended baseline behavior:

- `0` means effectively no cooldown
- `topology = "bounded"` means current `grid_2d` behavior

Recommended topology values:

- `bounded`
- `toroidal`

This preserves backward compatibility while making the cooldown feature
available to any `grid_2d` experiment that wants it.

It also creates a clean long-term path for toroidal behavior to live inside
the same world family.


## Cell-State Implication

The current `grid_2d` internal cell model contains:

- `cell_type`
- `resource_value`
- `regen_eligible`

That is not sufficient for cooldown semantics.

So `grid_2d` would need one additional internal per-cell state field beyond
what systems see through `CellView`.

The most straightforward addition is:

- `cooldown_remaining: int`

Expected meaning:

- obstacle cells: cooldown irrelevant
- resource cells with positive resource: cooldown normally `0`
- empty cells:
  - `cooldown_remaining > 0` means regeneration blocked
  - `cooldown_remaining == 0` means regeneration allowed if eligible

This is exactly the kind of world-internal extension the AXIS world contract
permits through `get_internal_cell()` and `set_cell()`.


## Cooldown Transition Rule

The key world-state transition is:

### On depletion

If `extract_resource()` causes a resource cell to reach zero:

- the cell becomes empty
- the cell enters cooldown
- `cooldown_remaining` is set to the configured cooldown value

### On each tick

For each eligible non-obstacle cell:

- if `cooldown_remaining > 0`:
  - decrement cooldown
  - do not regenerate this tick
- else:
  - ordinary regeneration may proceed

This means cooldown is part of world dynamics, not an action-level feature.


## Important Semantic Decision

One design choice matters immediately:

### Should regeneration begin on the same tick that cooldown reaches zero?

There are two coherent interpretations:

### Option A

- if a cell has `cooldown_remaining = 1`
- on the next `tick()` it becomes `0`
- but regeneration starts only on the following tick

### Option B

- if a cell has `cooldown_remaining = 1`
- on the next `tick()` it becomes `0`
- and regeneration may happen immediately in that same tick

The simpler and more intuitive first implementation is:

- **Option A**

Reason:

- “wait N full ticks before regrowth begins” is easier to reason about
- it avoids ambiguous partial-tick interpretations
- it makes tests and mental models cleaner

So the draft recommendation is:

> cooldown expiration and regeneration re-entry should be separated by one
> full tick boundary


## Factory And Config Shape

The extended `grid_2d` world should continue to accept the same config fields
it already supports, plus the new cooldown field and a topology field.

That implies a world-specific config model roughly shaped like:

- `grid_width`
- `grid_height`
- `obstacle_density`
- `resource_regen_rate`
- `regeneration_mode`
- `regen_eligible_ratio`
- `resource_regen_cooldown_steps`
- `topology`

This means:

- existing configs remain valid unchanged
- new cooldown experiments only need to add:
  - `resource_regen_cooldown_steps`
- toroidal experiments would only need to add:
  - `topology: toroidal`


## Why Extending `grid_2d` Is Probably Better

The more I look at the current AXIS world architecture, the less compelling a
separate `grid_2d_cooldown` world becomes.

Why extending `grid_2d` is likely better:

- cooldown changes timing semantics, not topology
- cooldown does not introduce a new system-facing world view
- toroidal changes boundary behavior, not cell semantics
- toroidal also does not introduce a new system-facing world view
- the config migration cost is lower
- the registry surface stays smaller
- public and internal docs stay simpler
- `resource_regen_cooldown_steps = 0` gives a clean backward-compatible default
- `topology = bounded` gives a clean backward-compatible default

The main tradeoff is:

- `grid_2d` becomes slightly richer internally
- `grid_2d` also becomes the home for multiple edge semantics

That seems acceptable, because the new state is small, explicit, and still
well within the conceptual boundary of a renewable grid-resource world.


## Relationship To Existing Worlds

### Relative to current `grid_2d`

The world remains the same world family.

Main new semantic options:

- regeneration timing may include cooldown
- edge behavior may be bounded or toroidal

### Relative to `toroidal`

The current separate `toroidal` world looks less like a distinct ecological
world and more like a `grid_2d` topology variant.

That suggests a draft direction:

> long-term, toroidal behavior should probably become a `grid_2d` topology
> mode rather than remain a separate world type

### Relative to other built-in worlds

No new world family is needed unless cooldown later grows into something much
more structurally different than delayed regeneration.


## Suggested First-Wave Scope

The first implementation wave should stay narrow.

Recommended in scope:

- extend the existing `grid_2d` package
- registration in world registry
- add `resource_regen_cooldown_steps` to `Grid2DWorldConfig`
- add `topology` to `Grid2DWorldConfig`
- add cooldown state to internal `Cell`
- add depletion cooldown semantics to extraction and regeneration
- add optional toroidal boundary handling
- compatibility with existing movement and consume handling
- tests for:
  - construction
  - extraction
  - cooldown countdown
  - delayed regeneration
  - sparse eligibility interaction
  - bounded topology behavior
  - toroidal wrapping behavior

Recommended out of scope for the first wave:

- special visualization panels
- world-specific replay overlays
- new world type registration or registry branching
- additional topology families beyond bounded and toroidal


## Draft Recommendation

The recommended direction is:

1. extend the existing `grid_2d` world
2. preserve existing config compatibility
3. add:
   - `resource_regen_cooldown_steps`
   - `topology`
4. default them to:
   - cooldown `0`
   - topology `bounded`
5. model cooldown as explicit internal per-cell state
6. handle toroidal wrapping through a topology switch
7. keep all system-facing world semantics unchanged except for the resulting
   resource availability over time and boundary behavior

This gives AXIS a richer `grid_2d` world that is:

- backward-compatible
- behaviorally meaningful
- architecturally simple
- and compatible with the existing SDK / framework layering


## Next Questions

Before moving from draft to spec, the main unresolved questions are:

1. Should cooldown apply only when a resource cell is fully depleted, or also
   after partial extraction events?
   Draft answer:
   - only after full depletion

2. Should cooldown countdown be visible in `world_metadata()` for replay and
   debugging?
   Draft answer:
   - probably yes, but not required for the first internal implementation

3. Should a zero-cooldown configuration be permitted?
   Draft answer:
   - yes, for semantic continuity and easier controlled experiments

4. Is a separate world type still justified?
   Draft answer:
   - probably not for the first wave
   - extending `grid_2d` with a default-zero cooldown is the cleaner direction

5. Should toroidal remain a separate world type?
   Draft answer:
   - probably not long-term
   - it looks more like a `grid_2d` topology mode than a distinct world family
