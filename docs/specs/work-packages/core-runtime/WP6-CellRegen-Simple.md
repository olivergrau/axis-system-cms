You have already implemented WP6 (Transition Engine) based on the AXIS System A specification.

However, Phase 1 (World Update / Regeneration) is currently implemented as a no-op.

Your task is to correctly implement **cell regeneration behavior** in strict alignment with the existing architecture and specifications.

-------------------------------------
CONTEXT
-------------------------------------

The Transition Engine must follow strict phase ordering:

1. World Update (Regeneration)
2. Action Application
3. Observation Construction
4. Agent Update
5. Memory Update
6. Termination Evaluation

Cell regeneration belongs **exclusively to Phase 1**.

-------------------------------------
OBJECTIVE
-------------------------------------

Replace the current no-op world update with a **deterministic cell regeneration mechanism**.

-------------------------------------
REQUIREMENTS
-------------------------------------

1. LOCAL CELL-BASED REGENERATION

- Each cell has a resource value r ∈ [0, 1]
- At each step, resource values increase by a fixed regeneration rate

Example rule:

    r_next = min(1.0, r_current + regen_rate)

- Regen rate must be configurable (from existing config system)
- No randomness (deterministic baseline)

---

2. APPLY TO ALL CELLS

- Regeneration must be applied to all cells in the grid
- Obstacle cells must NOT regenerate resources
- Traversability must not change

---

3. STRICT PHASE ISOLATION

- Regeneration must occur BEFORE action effects
- It must NOT depend on:
  - selected action
  - agent state
  - memory
  - policy

- It must NOT:
  - consume resources
  - move the agent
  - alter position

---

4. NO HIDDEN SIDE EFFECTS

- Do not mutate unrelated structures
- Keep world update explicit and local

---

5. WORLD OWNERSHIP

- Regeneration logic should live in the world layer OR a clearly scoped helper used by the Transition Engine

Valid options:
- World.apply_regeneration(...)
- or a dedicated function used by TransitionEngine

Do NOT:
- place regeneration logic in agent logic
- place regeneration logic in policy
- distribute it across multiple components

---

6. CONFIG INTEGRATION

- Use a clear parameter, e.g.:

    resource_regen_rate: float

- Validate:
    0 <= regen_rate <= 1

---

7. CLIPPING

- Resource values must remain within [0, 1]
- No overflow

---

-------------------------------------
OUT OF SCOPE
-------------------------------------

Do NOT implement:

- stochastic regeneration
- spatial diffusion
- resource spawning
- different cell types with different regen behavior
- time-dependent or history-dependent regen
- any coupling to agent behavior

This is a minimal deterministic baseline only.

---

-------------------------------------
TESTING REQUIREMENTS
-------------------------------------

Add or extend tests to verify:

1. Regeneration increases resource values correctly
2. Values are clipped at 1.0
3. Obstacle cells do not regenerate
4. Regeneration is applied before action effects
5. Determinism: same state → same result
6. Regeneration does not affect:
   - agent position
   - memory
   - action selection

Use small handcrafted worlds.

---

-------------------------------------
IMPORTANT CONSTRAINTS
-------------------------------------

- Do not modify other phases of the transition
- Do not introduce new architectural layers
- Do not refactor unrelated code
- Keep the implementation minimal and explicit
- Preserve all existing behavior except replacing the no-op

---

-------------------------------------
DELIVERABLE
-------------------------------------

Return:

1. Updated implementation of regeneration
2. Any modified files
3. New or updated tests
4. Short explanation of design choice (where regen lives and why)