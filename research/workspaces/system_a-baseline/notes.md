# Final Notes — System A (Argmax + Tie-Break)

## Context

System A was evaluated using:

- Single drive: **Hunger**
- Policy mode: **Argmax with stochastic tie-break**
- Standard environment: **locally regenerating resources (no cooldown)**
- Sensor: strictly **local, memoryless perception**

The goal was to understand whether meaningful exploration behavior emerges under these constraints.

---

## Key Observation

Once the agent discovers a resource patch, it **remains locally bound** to that region.

Typical behavior:

- The agent consumes available resources
- Moves slightly away when local gradients shift
- Immediately returns due to remaining resource signal
- Enters a stable loop such as:

consume → move away → move back → consume → ...

The stochastic tie-break changes *which direction is chosen under symmetry*, but does **not change the overall behavior pattern**.

---

## Interpretation

### 1. Hunger induces pure exploitation

The hunger drive directly couples action preference to **locally observed resource intensity**.

Consequences:

- Actions that increase immediate energy are always preferred
- There is **no representation of alternative locations**
- There is **no expected future benefit from exploration**

Result:

> The agent behaves as a **local optimizer** over immediate resource availability.

---

### 2. No structural mechanism for exploration

System A lacks:

- world model
- novelty signal
- uncertainty representation
- predictive structure

Therefore:

> Exploration is not just weak — it is **absent by design**.

Any movement away from a resource patch occurs only when:

- local signals flatten (resource depleted or symmetric), or
- stochastic tie-breaking resolves equal scores

This produces **diffusive motion**, not goal-directed exploration.

---

### 3. Argmax reveals the true system dynamics

Under previous softmax sampling:

- suboptimal actions retained non-zero probability
- behavior appeared more variable
- this could be misinterpreted as "exploration"

With argmax + tie-break:

- only top-scoring actions are selected
- randomness occurs **only under score degeneracy**

Result:

> The apparent exploration under softmax was largely **noise-driven**, not mechanism-driven.

Argmax exposes the underlying structure more clearly.

---

### 4. Patch-binding is an attractor

Given:

- continuous regeneration
- local sensing
- hunger-driven scoring

A resource patch becomes a **stable behavioral attractor**.

The agent:

- does not leave voluntarily
- does not search for alternatives
- remains in a locally sufficient energy loop

This is a direct consequence of the model, not a bug.

---

## Conclusion

System A demonstrates the following principle:

> A purely homeostatic agent with local perception does not generate exploration behavior.
> It converges to stable exploitation of locally available resources.

---

## Implications for System Design

### 1. Tie-break is necessary but limited

- Solves symmetry artifacts
- Prevents deterministic bias from implementation order
- Does **not** change behavioral regime

---

### 2. Softmax should not be interpreted as exploration

- It introduces continuous stochasticity
- It can mimic exploration-like motion
- But this behavior is **not structurally grounded**

---

### 3. Exploration requires additional mechanisms

To produce genuine exploration, the system needs at least one of:

- internal drive for novelty (e.g. curiosity)
- memory or world model
- uncertainty or prediction error signal

This is addressed in **System A+W** via:

- curiosity drive
- spatial visit-count model
- novelty-based action modulation

---

### 4. Environment changes vs. agent changes

Altering the environment (e.g. resource cooldown) can:

- reduce patch stability
- force movement

However:

> This shifts exploration from an **agent property** to an **environmental constraint**

Therefore:

- System A baseline should remain unchanged
- Environment variations should be treated as separate experiments

---

## Final Statement

System A serves as a **clean baseline**:

- It isolates the effect of a single homeostatic drive
- It demonstrates the limitations of local reactive control
- It shows that exploration does not emerge from hunger alone

This provides a strong foundation for evaluating extended systems such as System A+W.

## Addendum — Resource Cooldown Experiment

### Modification

A modified environment variant was introduced with **resource regeneration delay**:

- After consumption, a resource cell remains depleted for a fixed number of steps
- Only after this cooldown period does regeneration resume

All other components of System A remain unchanged:
- single hunger drive
- local sensor
- argmax policy with stochastic tie-break

---

### Observation

Under cooldown conditions, the agent no longer remains bound to a single resource patch.

Behavior changes:

- After consuming a resource, the local cell becomes temporarily unattractive
- The agent is forced to move away due to lack of immediate reward
- Movement becomes more spatially distributed
- The previous oscillatory loop disappears

---

### Interpretation

The behavioral change is not due to the agent architecture, but due to altered environment dynamics.

Specifically:

- The immediate reward structure is disrupted
- Local exploitation is no longer continuously viable
- Movement is externally induced by temporary resource depletion

---

### Key Insight

> Exploration-like behavior can be induced by environmental constraints,
> even in the absence of internal exploratory mechanisms.

However:

- The agent still does not represent alternative locations
- The agent does not seek novelty or unknown regions
- Movement remains reactive, not goal-directed

---

### Implication

This experiment highlights a critical distinction:

- **System-driven exploration** (e.g. curiosity, novelty, memory)
- **Environment-driven displacement** (e.g. resource cooldown)

The cooldown mechanism produces the latter.

---

### Conclusion

The cooldown variant confirms:

- System A, in its original form, produces stable patch exploitation
- Removing immediate regeneration breaks this stability
- Resulting movement should not be interpreted as true exploration

System A remains a purely reactive, homeostatic agent.