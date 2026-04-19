# AXIS - System Construction Kit

## Draft for Reusable Internal System Components

---

## 1. Purpose

This document proposes a new architectural layer for AXIS:

> a reusable **System Construction Kit** for composing multiple systems from shared internal mechanisms.

The purpose of this layer is to avoid two failure modes:

- pushing cognitive mechanisms into the framework, where they do not belong
- re-implementing the same mechanisms independently in each new system

This is a draft-level design document intended as a conceptual basis for later engineering work.

---

## 2. Problem Statement

The current AXIS architecture separates:

- `sdk/` as the contract layer
- `framework/` as the execution layer
- `world/` as the environment layer
- `systems/` as the behavior layer

This separation is correct, but it leaves an important gap.

At the moment, any substantial internal mechanism added to a system tends to live entirely inside that concrete system implementation.

Examples:

- a predictive memory module
- signed prediction error processing
- action-level modulation logic
- reusable arbitration helpers
- generic observation-to-feature transforms

If these mechanisms are implemented only inside a concrete system such as `System C`, then later systems face an undesirable choice:

- duplicate the mechanism
- depend on `System C` as if it were a reusable base class
- or move the mechanism upward into the framework, even though it is not a framework concern

None of these outcomes is architecturally clean.

---

## 3. Core Proposal

Introduce an internal layer between the framework-facing system boundary and the concrete system definitions:

> the **System Construction Kit**

This layer contains reusable system-internal building blocks for composing agent architectures.

It is:

- below the `sdk/` boundary in terms of specialization
- above individual systems in terms of reuse
- outside `framework/`
- outside `world/`

It is not a plugin system and not a runtime abstraction for the framework.

It is a design and implementation layer for reusable cognitive and decision components.

---

## 4. Architectural Position

### 4.1 Existing Layering

Current architectural intention:

- SDK defines contracts
- framework defines execution
- systems define behavior

This remains correct.

### 4.2 Missing Layer

The missing layer is:

- reusable behavior primitives for systems

This new layer should not be introduced by changing the framework contract.

Instead, it should exist entirely on the system side of the architecture.

### 4.3 Proposed Layering

The intended architectural stack becomes:

- `sdk/`
  contract interfaces and replay/base types
- `framework/`
  execution, persistence, experiment orchestration
- `world/`
  world model, world dynamics, action handlers, world views
- `systems/construction_kit/`
  reusable internal system mechanisms
- `systems/system_a/`, `systems/system_c/`, future systems
  concrete system compositions

Conceptually:

```text
Framework owns execution.
Systems own behavior.
Construction kit owns reusable behavior mechanisms.
```

---

## 5. Design Principle

The key principle is:

> Reusable cognitive mechanisms belong in a system-components layer, not in the framework layer.

This has several consequences.

### 5.1 What Must Stay Out of the Framework

The framework should not know about:

- prediction
- drives as concrete data structures
- world models
- arbitration internals
- curiosity, hunger, safety, or similar semantics
- internal memory topologies

The framework should continue to know only:

- how to call `decide()`
- how to apply actions to the world
- how to call `transition()`
- how to persist and visualize trace contracts

### 5.2 What Should Become Reusable

The following should be reusable across systems when they express a general design pattern:

- local predictive memory
- prediction error decomposition
- action modulation by learned traces
- feature extraction from observation
- generic drive arbitration patterns
- memory update schemes
- bounded trace accumulation
- local expectation update rules

---

## 6. Why This Layer Is Needed

### 6.1 Avoiding False Inheritance

Future systems should not need to inherit from `System C` merely to reuse prediction.

Prediction is not the identity of `System C`.

It is a mechanism that `System C` happens to instantiate.

Therefore:

- `System C` should be a composition target
- not the canonical home of prediction logic

### 6.2 Avoiding Duplication

Without a construction kit, later systems such as `System D`, `System E`, or predictive variants of `System B` may independently rebuild:

- expectation memory
- signed surprise
- reinforcement/frustration traces
- modulation functions

That would create:

- duplicated mathematics
- inconsistent semantics
- fragmented trace structures
- increased maintenance cost

### 6.3 Preserving Framework Cleanliness

Moving such mechanisms into the framework would solve duplication at the wrong level.

That would blur the framework/system boundary and introduce architectural leakage.

The construction-kit layer preserves the clean separation:

- framework stays generic
- systems stay expressive
- reusable internal mechanisms gain a proper home

---

## 7. What the Construction Kit Is

The System Construction Kit is a library of reusable internal primitives for building systems.

These primitives can include:

- abstract state structures
- reusable pure functions
- reusable update rules
- reusable component protocols internal to the system layer
- shared trace vocabulary
- shared composition patterns

These are not required to be framework-level protocols.

They are internal design contracts for system engineering.

---

## 8. What the Construction Kit Is Not

The construction kit is not:

- a replacement for `SystemInterface`
- a second framework
- a plugin architecture
- a requirement that all systems share the same internal design
- a mandatory inheritance hierarchy
- a hidden attempt to standardize all cognition under one model

Systems should remain free to opt into only the mechanisms they need.

This layer exists to support reuse, not to enforce uniformity for its own sake.

---

## 9. Candidate Component Families

This section sketches the first set of reusable component families that could belong in the construction kit.

### 9.1 Observation Feature Extraction

Purpose:

- derive reusable local predictive or drive-relevant feature vectors from raw observations

Examples:

- resource-focused local feature projection
- signal-focused local feature projection
- traversability-focused projections
- composite feature extraction for multi-drive systems

This is where a generic concept such as:

$$
y_t = \Omega(u_t)
$$

can live without binding it to one specific system.

### 9.2 Predictive Memory

Purpose:

- store local context-conditioned expectations

Typical responsibilities:

- context encoding
- expectation storage
- prediction retrieval
- expectation update

Examples:

- discrete context-action expectation tables
- bounded expectation traces
- context-conditioned exponential averages

### 9.3 Prediction Error Processing

Purpose:

- compute signed mismatch between expected and observed outcomes

Typical responsibilities:

- signed error decomposition
- per-feature aggregation
- drive-facing error summaries

Examples:

- positive surprise
- disappointment
- absolute surprise
- uncertainty-like summaries

### 9.4 Predictive Trace Dynamics

Purpose:

- convert prediction error into reusable action-history signals

Examples:

- frustration traces
- confidence traces
- reliability traces
- decay-based local reinforcement traces

### 9.5 Action Modulation

Purpose:

- map learned traces or predictive summaries into action-level score modulation

Examples:

- multiplicative confidence damping
- bounded positive reinforcement
- additive risk penalties
- clipped exponential modulation

### 9.6 Arbitration Helpers

Purpose:

- support composition of multiple drives or multiple projected action scores

Examples:

- weighted drive combination
- bounded normalization rules
- hierarchy-aware weighting
- conflict-sensitive aggregation

### 9.7 Memory Update Utilities

Purpose:

- provide reusable update schemes for local adaptive state

Examples:

- exponential moving averages
- bounded decay traces
- finite-buffer updates
- saturating accumulation

---

## 10. First Target Use Case: Prediction Beyond System C

The immediate motivation is predictive behavior.

Prediction should initially appear in `System C` as the first concrete composition using:

- predictive feature extraction
- predictive memory
- signed prediction error
- positive and negative traces
- action-level modulation

But the mechanism itself should be reusable later by:

- a predictive extension of `System B`
- systems with different worlds but similar local expectation structure
- systems combining prediction with world models
- systems using prediction for curiosity or safety rather than hunger

This is the clearest example of why the construction kit is needed.

---

## 11. Reuse Model

The construction kit should support reuse by composition, not by deep inheritance.

Preferred pattern:

- a concrete system chooses a set of components
- wires them into its own `decide()` and `transition()` flow
- exposes only `SystemInterface` at the framework boundary

This means:

- the framework sees a system
- the system internally sees a composition of reusable parts

This preserves the current outer architecture while making the inside more modular.

---

## 12. Relationship to Existing Systems

### 12.1 System A

`System A` can remain largely self-contained.

It is simple enough that forced extraction into a construction kit may not be worth it immediately.

However, over time some pieces may become shareable:

- observation handling patterns
- action projection helpers
- drive contribution structures

### 12.2 System C

`System C` should be treated as the first system likely to motivate extraction of reusable mechanisms.

It is the first place where:

- predictive state
- signed learning signals
- reusable modulation logic

become substantial enough to justify generalization.

### 12.3 Later Systems

Future systems should be able to reuse selected parts of the construction kit without inheriting from earlier systems.

This is especially important for systems that:

- share mechanisms but not goals
- share local learning logic but not drive semantics
- share modulation structure but not state representation

---

## 13. Suggested Repository Placement

This document does not prescribe final implementation details, but the intended placement should be explicitly separated from both framework and concrete systems.

Possible package names:

- `axis.systems.construction_kit`
- `axis.systems.components`
- `axis.systems.primitives`

The most explicit and conceptually accurate name is likely:

- `axis.systems.construction_kit`

because it communicates:

- this is for building systems
- this is not the framework
- this is not one concrete system

---

## 14. Suggested Internal Substructure

One possible long-term organization:

```text
axis/systems/construction_kit/
    features/
    prediction/
    modulation/
    arbitration/
    memory/
    traces/
    types/
```

Possible contents:

- `features/`
  observation-to-feature extraction helpers
- `prediction/`
  predictive memory and prediction error logic
- `modulation/`
  action modulation functions
- `arbitration/`
  score combination helpers
- `memory/`
  generic bounded/adaptive memory utilities
- `traces/`
  reusable local trace dynamics
- `types/`
  shared internal data structures

This is only a draft shape, not a frozen package design.

---

## 15. Engineering Constraints

If this layer is implemented later, it should obey the same architectural values as the rest of AXIS:

- deterministic behavior
- immutable state models
- explicit data flow
- traceability
- local interpretability
- no hidden global state

Additionally:

- construction-kit components should not depend on `framework/`
- construction-kit components should not mutate the world
- construction-kit components should not bypass `SystemInterface`

They are internal system-building primitives, not execution owners.

---

## 16. Expected Benefits

If introduced carefully, the construction kit should provide:

- less duplication across systems
- cleaner experimentation with new system variants
- easier extraction of shared mathematics into reusable implementations
- reduced pressure to misuse inheritance across systems
- better conceptual separation between architecture and instantiation
- a cleaner path from design documents to engineering work packages

---

## 17. Risks

This idea also carries risks and should not be over-applied.

### 17.1 Premature Abstraction

If introduced too early, the construction kit may abstract patterns that are not yet stable.

That would create unnecessary indirection.

### 17.2 Hidden Mini-Framework

If over-designed, the construction kit could become a second framework inside the systems layer.

That would be a mistake.

It should remain lightweight and mechanism-oriented.

### 17.3 Forced Uniformity

Not all systems should be forced to use the same internal components.

The layer should support reuse without requiring universal adoption.

### 17.4 Semantic Drift

If shared components are extracted without clear conceptual boundaries, different systems may start using the same primitives in incompatible ways.

This means the construction kit needs:

- explicit semantics
- carefully named abstractions
- deliberate extraction criteria

---

## 18. Extraction Criteria

Not every internal mechanism should be moved into the construction kit.

A mechanism is a good candidate for extraction when all of the following are true:

- it is conceptually stable
- it is useful in more than one concrete system
- it is not framework-owned
- it has clear inputs and outputs
- it can be reused without dragging in one system's full semantics

This should be the rule for deciding what belongs in the kit.

---

## 19. Current Recommendation

The recommended architectural direction is:

1. Keep the framework unchanged.
2. Continue defining `System C` as a concrete system.
3. Treat predictive mechanisms as the first likely candidates for later extraction.
4. Introduce a system-side construction kit once at least one or two reusable mechanism families are sufficiently stable.

This avoids premature refactoring while preserving a clear long-term direction.

---

## 20. Working Conclusion

AXIS currently has a clean separation between framework and systems, but it lacks a reusable internal layer for shared system mechanisms.

The proposed **System Construction Kit** fills that gap.

Its purpose is not to standardize all systems internally, but to provide a proper architectural home for mechanisms that are:

- too system-specific for the framework
- too general to belong only to one concrete system

Prediction is the clearest first example.

For that reason, this layer should be considered a serious architectural direction for future engineering work.
