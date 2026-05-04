# AXIS Trace and Replay Engineering Specification

## 1. Purpose

This engineering specification derives the implementation shape of the
trace/replay initiative from:

- [Delta-Opt Trace Specification](./spec.md)

This document covers the trace and replay contract initiative only.

Its purpose is to define how AXIS should introduce `delta-opt` as a new compact
replay-capable trace mode while preserving the current consumer-facing replay
experience.

This document does not define the broader execution-memory architecture. That
belongs to the execution-memory engineering initiative.


## 2. Initiative Boundary

This initiative is about:

- the `delta-opt` trace mode
- compact persisted replay contracts
- replay-data-layer reconstruction
- deterministic and stochastic world replay contracts
- compatibility with the current visualizer and replay consumers

This initiative is not about:

- worker-side persistence architecture
- parent / worker memory minimization
- run-summary streaming aggregation
- memory-safe parallel scheduling


## 3. Current System Reality

The trace/replay redesign must begin from the actual current implementation.

### 3.1 Current trace modes

Execution policy currently lives in:

- [src/axis/framework/execution_policy.py](/workspaces/axis-system-cms/src/axis/framework/execution_policy.py)

Current trace modes are:

- `full`
- `delta`
- `light`

`delta-opt` does not yet exist.

### 3.2 Current delta trace construction

Current delta episode construction lives in:

- [src/axis/framework/runner.py](/workspaces/axis-system-cms/src/axis/framework/runner.py)

Current behavior in `_run_episode_delta(...)`:

- keep full initial world snapshot
- persist explicit `regen_delta`
- persist explicit `action_delta`
- persist `system_data`
- persist `world_data`

This is replay-capable, but still too heavy in dense worlds.

### 3.3 Current delta world representation

Delta replay contract lives in:

- [src/axis/sdk/trace.py](/workspaces/axis-system-cms/src/axis/sdk/trace.py)

Current behavior:

- `DeltaStepTrace` stores `regen_delta` and `action_delta`
- `reconstruct_episode_trace(...)` rebuilds a full replay trace from those
  explicit deltas

This means replay currently depends on explicit persisted world deltas, not on
reconstruction from world dynamics.

### 3.4 Current deterministic world dynamics

Current deterministic grid-style world dynamics live in:

- [src/axis/world/grid_2d/dynamics.py](/workspaces/axis-system-cms/src/axis/world/grid_2d/dynamics.py)
- [src/axis/world/grid_2d/model.py](/workspaces/axis-system-cms/src/axis/world/grid_2d/model.py)
- [src/axis/world/toroidal/model.py](/workspaces/axis-system-cms/src/axis/world/toroidal/model.py)

Current observation:

- regeneration is deterministic
- regeneration depends on prior world state and world config
- this makes explicit `regen_delta` potentially reconstructable rather than
  necessary to persist

### 3.5 Current heavy per-step trace payloads

Notable heavy fields currently persisted include:

- `buffer_snapshot`
- `visit_counts_map`
- large prediction trace payloads
- duplicated score variants in `system_cw` decision payloads

Relevant files include:

- [src/axis/systems/system_aw/transition.py](/workspaces/axis-system-cms/src/axis/systems/system_aw/transition.py)
- [src/axis/systems/system_cw/transition.py](/workspaces/axis-system-cms/src/axis/systems/system_cw/transition.py)
- [src/axis/systems/system_cw/system.py](/workspaces/axis-system-cms/src/axis/systems/system_cw/system.py)

### 3.6 Current consumer assumption

Replay consumers currently operate as though they receive full replay-ready
traces.

Important implication:

- the visualizer should not become a simulator

This consumer contract is valuable and should be preserved by shifting
reconstruction into the replay data layer.


## 4. Engineering Goals

The trace/replay initiative should achieve the following:

1. introduce `delta-opt` as a replay-capable compact trace mode
2. preserve replay correctness for official consumers
3. move reconstruction below the visualizer
4. allow deterministic worlds to omit reconstructable world phases
5. support future stochastic worlds by persisting stochastic outcomes rather
   than full world deltas
6. reduce persisted trace size significantly


## 5. Target Architectural Direction

The target direction is:

- persisted compact storage trace
- replay-data-layer reconstruction
- consumer-facing full replay trace

Conceptually:

```text
delta-opt storage trace
-> replay reconstruction
-> replay-ready full trace
-> visualizer / comparison / replay analysis
```

This preserves the consumer contract while allowing the persisted format to be
smaller and more structured.


## 6. Required Refactoring Direction

### 6.1 Introduce `delta-opt` as a new trace mode

Primary target:

- [src/axis/framework/execution_policy.py](/workspaces/axis-system-cms/src/axis/framework/execution_policy.py)

Required direction:

- add a new trace mode value: `delta-opt`
- keep `full`, `light`, and `delta` unchanged during introduction

### 6.2 Introduce new storage trace models

Primary target:

- [src/axis/sdk/trace.py](/workspaces/axis-system-cms/src/axis/sdk/trace.py)

Required direction:

- define a new persisted compact episode model for `delta-opt`
- keep the existing consumer-facing replay trace concept intact
- distinguish clearly between:
  - compact storage representation
  - reconstructed replay representation

### 6.3 Move reconstruction into replay access path

Primary targets:

- [src/axis/framework/persistence.py](/workspaces/axis-system-cms/src/axis/framework/persistence.py)
- [src/axis/visualization/replay_access.py](/workspaces/axis-system-cms/src/axis/visualization/replay_access.py)
- [src/axis/visualization/snapshot_resolver.py](/workspaces/axis-system-cms/src/axis/visualization/snapshot_resolver.py)

Required direction:

- replay loading must detect `delta-opt`
- replay access must materialize a full replay trace for consumers
- visualizer-facing code should remain as close as possible to the current
  contract

### 6.4 Preserve phase-aware replay

Current replay and visualization assume:

- `BEFORE`
- `AFTER_REGEN`
- `AFTER_ACTION`

Required direction:

- `delta-opt` reconstruction must still produce these phase states correctly


## 7. Deterministic World Support

### 7.1 Grid worlds

For current deterministic grid worlds, `delta-opt` should support omitting full
persisted `regen_delta`.

Relevant current modules:

- [src/axis/world/grid_2d/dynamics.py](/workspaces/axis-system-cms/src/axis/world/grid_2d/dynamics.py)
- [src/axis/world/grid_2d/model.py](/workspaces/axis-system-cms/src/axis/world/grid_2d/model.py)
- [src/axis/world/toroidal/model.py](/workspaces/axis-system-cms/src/axis/world/toroidal/model.py)

Required direction:

- reconstruct the `AFTER_REGEN` phase through official world dynamics
- keep reconstruction centralized in the replay layer

### 7.2 Action-phase reconstruction

`action_delta` may still remain useful for the first implementation wave,
because world mutation due to action is small and already compact.

Recommended direction:

- optimize regen-phase persistence first
- only later reconsider whether action-phase persistence should also become more
  semantic or event-based


## 8. Stochastic World Support

### 8.1 Preferred replay contract

For stochastic worlds, `delta-opt` should not persist whole resulting world
deltas by default.

Instead, it should persist only the stochastic outcomes required to reproduce
the same transition.

This could take forms such as:

- sampled event payloads
- replay-state payloads
- world-specific stochastic decision records

### 8.2 Avoid seed-only fragility

Seed-only replay is too fragile as the main design target because it depends on:

- exact RNG schedule stability
- unchanged code paths
- unchanged call ordering

Therefore the preferred direction is:

- outcome-replayable design

not:

- seed-only implicit replay

### 8.3 World replay classes

The implementation should align with the world replay classes proposed in the
spec:

- deterministic replayable
- outcome-replayable
- optional seed-replayable


## 9. Trace Payload Reduction Targets

### 9.1 World-phase payloads

Primary target:

- remove persisted `regen_delta` where reconstructable

### 9.2 System trace payloads

Candidate reductions include:

- `buffer_snapshot`
- `visit_counts_map`
- duplicated score arrays and counterfactual fields
- other deterministic derived state that can be reconstructed in replay

Important constraint:

- if a consumer currently relies on a field through the official replay path,
  replay reconstruction must restore it before exposure

### 9.3 Current heavy system sites

Important targets:

- [src/axis/systems/system_aw/transition.py](/workspaces/axis-system-cms/src/axis/systems/system_aw/transition.py)
- [src/axis/systems/system_cw/transition.py](/workspaces/axis-system-cms/src/axis/systems/system_cw/transition.py)
- [src/axis/systems/system_cw/system.py](/workspaces/axis-system-cms/src/axis/systems/system_cw/system.py)


## 10. Replay Consumer Compatibility

### 10.1 Visualizer contract

The visualizer should continue to receive full replay-ready traces.

This means the visualizer must not become responsible for:

- world ticking
- stochastic event replay
- omitted phase inference

### 10.2 Comparison compatibility

Comparison workflows that currently load replay-capable episode traces should
continue to work via the official replay access path.

Relevant current consumers include:

- [src/axis/framework/comparison/compare.py](/workspaces/axis-system-cms/src/axis/framework/comparison/compare.py)
- [src/axis/framework/metrics/loader.py](/workspaces/axis-system-cms/src/axis/framework/metrics/loader.py)

### 10.3 Raw JSON caveat

Any tool that directly reads persisted raw episode JSON may require adaptation,
because `delta-opt` storage traces are expected to be more compact and less
directly consumer-facing than current `delta` traces.


## 11. Suggested Implementation Waves

### Wave 1: Add `delta-opt` mode and storage models

Primary changes:

- new trace mode enum value
- new compact trace model definitions
- no legacy mode removal

### Wave 2: Replay reconstruction for deterministic worlds

Primary changes:

- reconstruct `AFTER_REGEN` from official world dynamics
- keep replay outputs consumer-compatible

### Wave 3: Payload reduction for system traces

Primary changes:

- remove deterministically reconstructable fields from storage
- reconstruct them in replay as needed

### Wave 4: Stochastic replay contract

Primary changes:

- define outcome-replayable payload contract
- support future stochastic worlds explicitly


## 12. Validation Requirements

The trace/replay initiative should be considered successful only if it
demonstrates:

- replay parity for deterministic worlds
- visualizer compatibility
- comparison compatibility
- materially smaller episode artifact size
- materially smaller run-level replay persistence

Validation should include:

- deterministic `grid_2d`
- deterministic `toroidal`
- dense regeneration worlds
- sparse worlds
- side-by-side replay checks against current `delta` output


## 13. Open Questions

- What is the minimal safe storage contract for current deterministic worlds?
- Which system-trace fields should be reconstructed versus persisted?
- Should `action_delta` remain explicit in version 1 of `delta-opt`?
- What replay-state contract should future stochastic worlds expose?
- How much lazy reconstruction is acceptable before replay responsiveness
  degrades?


## 14. Summary

This initiative is the trace and replay side of the optimization program.

Its job is to make persisted replay data smaller while preserving the current
consumer-facing replay experience.

It does that by:

- adding `delta-opt`
- distinguishing storage trace from replay trace
- reconstructing full replay data in the replay layer
- omitting reconstructable deterministic world phases
- persisting stochastic outcomes rather than full stochastic world deltas

This provides the replay-contract foundation on which later execution-memory
optimizations can operate efficiently.
