# System C+W Draft

## Purpose

This draft explores a new AXIS system variant:

- `system_cw`

The purpose of `system_cw` is to combine three capabilities that currently live
in separate forms across `system_a+w` and `system_c`:

- a **hunger drive**
- a **curiosity drive**
- a **minimal world model**
- **prediction-based action modulation**

The intended result is a system that can:

- pursue energy regulation
- explore because novelty itself has motivational force
- retain minimal spatial and sensory structure about recent experience
- and learn which actions in which local contexts tend to succeed or fail


## Starting Point

AXIS already has two nearby systems:

- `system_a+w`
- `system_c`

`system_a+w` contributes:

- dual-drive behavior:
  - hunger
  - curiosity
- a minimal spatial world model:
  - relative-position tracking
  - visit-count map
- sensory novelty from episodic observation memory
- drive arbitration in which hunger can gate curiosity

`system_c` contributes:

- local predictive memory over context-action pairs
- signed prediction error
- confidence and frustration traces
- action-level predictive modulation

The most important design principle inherited from `system_c` is:

> prediction should modulate action expression, not directly change drive
> magnitude

This principle is worth preserving, because it keeps the AXIS layering clean:

- drives remain motivational sources
- projection maps drives into action tendencies
- prediction shapes the reliability of action expression


## Core Idea

`system_cw` should be understood as:

> a dual-drive predictive agent with a minimal world model

In practical terms, the system should:

- retain the hunger drive from System A / A+W
- retain the curiosity drive from A+W
- retain the minimal world model from A+W:
  - spatial visit structure
  - sensory novelty support
- add the predictive machinery from C:
  - predictive context encoding
  - local predictive memory
  - retrospective prediction error
  - positive and negative predictive traces
  - action-specific modulation

The system is therefore neither:

- just `system_a+w` with prediction glued on top
- nor `system_c` with a curiosity scalar added

It should instead be a coherent synthesis in which:

- exploration has its own motivational status
- prediction can shape how both exploitative and exploratory tendencies are
  expressed
- and the world model stays minimal rather than becoming a planning substrate


## Intended Behavioral Effect

The point of `system_cw` is to produce behavior that is richer than either
neighbor system alone.

Relative to `system_a+w`, it should be able to:

- reduce repeated futile exploration in contexts that historically disappoint
- become selectively confident in exploratory or consumptive actions
- distinguish novelty from reliability

Relative to `system_c`, it should be able to:

- explore even when hunger alone would not justify movement
- maintain structured spatial revisitation pressure through the visit-count map
- use sensory novelty as a second route into movement preference

The resulting behavioral expectation is:

- when hungry, the agent should still prefer energetically useful behavior
- when sated, curiosity should still drive exploration
- but in both regimes, predictive history should bias action selection toward
  locally reliable strategies

In other words:

- hunger says what matters metabolically
- curiosity says what matters epistemically
- prediction says which actions have recently earned trust


## Recommended Architectural Direction

The conservative and most AXIS-compatible path is:

- keep the A+W dual-drive structure
- keep the A+W minimal world model
- keep the C predictive memory and dual trace machinery
- preserve C's rule that prediction acts at the level of action projection
- avoid turning the world model into a planner or latent-state engine

So the recommended flow is:

1. observe locally
2. compute hunger drive output
3. compute curiosity drive output
4. derive predictive context and predictive features
5. apply predictive modulation to action contributions
6. arbitrate hunger and curiosity
7. select action with the ordinary policy layer
8. update:
   - energy
   - observation buffer
   - world model
   - predictive memory
   - predictive traces

This is attractive because:

- it reuses established AXIS components
- it preserves the current separation of concerns
- it keeps comparison against `system_a+w` and `system_c` interpretable
- it avoids a large first-wave redesign of trace, state, or world contracts


## First-Wave Design Recommendation

The safest first-wave design is not to make everything predictive at once.

Instead, `system_cw` should begin with:

- the same hunger drive as `system_a+w`
- the same curiosity drive as `system_a+w`
- the same world model as `system_a+w`
- the same predictive substrate as `system_c`
- a shared action-space modulation layer that can act on drive-specific action
  contributions before arbitration

That means we conceptually compute:

- hunger action tendency
- curiosity action tendency

and then prediction modulates these tendencies before final combination.

This creates the most interesting possibility in the new system:

- curiosity can remain motivationally real
- but not all novelty-seeking actions should remain equally attractive after
  repeated disappointment


## Key Design Choice: What Prediction Should Modulate

This is the most important design decision for the detailed draft.

There are three plausible options.

### Option A: Modulate Hunger Only

Prediction modulates only the hunger projection, while curiosity remains purely
novelty-driven.

Advantages:

- closest to current `system_c`
- simplest to reason about
- lowest implementation risk

Disadvantages:

- curiosity remains blind to learned action reliability
- the new system becomes less integrated than the name `C+W` suggests

### Option B: Modulate Hunger and Curiosity Separately

Prediction modulates both drive projections before arbitration.

Advantages:

- most coherent combined system
- allows learned suppression of futile exploration
- allows exploratory confidence to emerge

Disadvantages:

- introduces an extra interpretive layer:
  - what counts as predictive success for curiosity?

### Option C: Modulate Only the Combined Score

Prediction acts after drive combination.

Advantages:

- simpler output path

Disadvantages:

- breaks the clean AXIS separation between drive projection and arbitration
- loses interpretability at the drive level

Recommended direction for `system_cw`:

- **Option B**

This is the most meaningful synthesis, provided we keep the predictive signal
local and mechanistic.


## Key Design Choice: What Predictive Features Should Be

`system_c` currently predicts over a compact local sensory feature vector.

For `system_cw`, the temptation will be to make prediction world-model-heavy.
That should be resisted in the first version.

Recommended first-wave predictive substrate:

- keep the existing local sensory predictive features
- optionally add one or two compact world-model-derived indicators later

Examples of possible later additions:

- local visit pressure
- novelty estimate for the chosen direction

But the first implementation should avoid:

- full map prediction
- route planning
- explicit model-based search

The world model in `system_cw` should remain:

- minimal
- agent-relative
- non-planning


## Proposed State Shape

The likely first-wave internal state should be the union of the current A+W and
C commitments:

- `energy`
- `observation_buffer`
- `world_model`
- `predictive_memory`
- `trace_state`
- `last_observation`

This is attractive because it is mechanically legible:

- A+W contributes the curiosity-supporting memory substrate
- C contributes the predictive substrate

No additional planner state should be introduced in the first wave.


## Proposed Config Surface

The most plausible configuration strategy is:

- inherit the A+W-style structure for:
  - agent
  - policy
  - transition
  - curiosity
  - arbitration
- add the C-style:
  - `prediction`

So `SystemCWConfig` would likely resemble:

- `agent`
- `policy`
- `transition`
- `curiosity`
- `arbitration`
- `prediction`

This keeps the system configurable in terms users already understand from the
existing two parent systems.


## Required Compatibility

`system_cw` should fit the current AXIS contracts without requiring framework
changes.

That means:

- it must still be a standard AXIS system
- it must operate against the existing `WorldView`
- it must work with the current runner lifecycle
- it must produce ordinary episode traces
- it must remain visualizable and comparable using the existing experiment
  pipeline

This is important because the first value of `system_cw` is scientific
comparability.

We want to be able to compare:

- `system_a`
- `system_a+w`
- `system_c`
- `system_cw`

under the same world conditions and evaluation workflows.


## Main Risks

The main risk is not implementation complexity by itself.

The deeper risk is conceptual blurring.

If handled poorly, `system_cw` could become:

- an overstuffed hybrid
- harder to interpret than either parent system
- or a hidden planning system in disguise

The draft should therefore keep three constraints explicit:

- the world model remains minimal
- prediction remains local and mechanistic
- drive magnitudes remain distinct from predictive modulation


## Questions For The Detailed Draft

The next document should settle at least these questions:

1. Should prediction modulate both hunger and curiosity, or only hunger in
   v1?
2. What counts as positive or negative predictive outcome for curiosity-driven
   movement?
3. Should the predictive context remain purely sensory, or include compact
   world-model-derived bits?
4. Should there be separate predictive modulation parameters for hunger and
   curiosity?
5. How should we preserve interpretability in traces and visualization once two
   drives and predictive modulation interact?


## Recommendation

`system_cw` is worth pursuing.

It is a natural next system in the AXIS family because it joins:

- motivation for homeostatic regulation
- motivation for exploratory novelty
- minimal structure about the environment
- and learned reliability of action in context

The recommended first implementation should be conservative:

- build on A+W and C directly
- preserve the current AXIS architecture
- keep prediction local
- keep the world model minimal
- and make predictive modulation operate on drive-specific action expression
  rather than on drive magnitude

That gives AXIS a strong new comparison target without collapsing into
model-based planning.
