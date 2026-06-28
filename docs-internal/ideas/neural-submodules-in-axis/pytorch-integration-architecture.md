# PyTorch Integration Architecture for AXIS Neural Submodules

## 1. Purpose

This document fixes a concrete technical point for the initiative:

> can a PyTorch-based neural submodule be integrated cleanly into AXIS agent
> implementations, including optional GPU usage?

The answer is yes.

This is not a conceptual problem. It is an engineering design problem.

The important architectural constraint is:

- AXIS remains the outer cognitive architecture
- PyTorch is used as the implementation technology for one bounded submodule

So the goal is not to make AXIS “a PyTorch system.”
The goal is to make one subcomponent of an AXIS system PyTorch-based while the
surrounding system remains mechanistic and explicit.

---

## 2. High-Level Integration Principle

A PyTorch component should enter AXIS in the same way that other bounded
submodules already do.

Examples of current bounded components in AXIS include:

- sensor
- drive
- policy
- transition helper
- predictive memory helper
- curiosity helper

A neural submodule should be treated as one more internal subsystem with a
narrow and explicit role.

The clean design principle is:

> the system owns the PyTorch module, but the system as a whole is not reduced
> to the PyTorch module.

This means, for example, that `System C` might become:

- explicit hunger drive
- explicit policy
- explicit transition logic
- **PyTorch predictor submodule**

and `System C+W` might become:

- explicit hunger drive
- explicit curiosity drive
- explicit arbitration
- explicit transition logic
- **shared PyTorch predictor submodule**

---

## 3. Seamless Integration Is Technically Feasible

There is nothing unusual about embedding a PyTorch module into the existing
AXIS runtime.

At runtime, the pattern is simple:

1. AXIS system receives observation
2. system extracts predictive features
3. features are converted into tensors
4. tensors are moved to the configured device
5. PyTorch module performs forward pass
6. output is converted back into an AXIS-usable numerical structure
7. the rest of the AXIS decision pipeline stays analytical
8. after transition, the system computes a target and optionally performs an
   optimizer step

This is fully compatible with the current AXIS execution model.

The key point is:

- PyTorch lives **inside** the system implementation
- AXIS lifecycle remains outside

---

## 4. Recommended Integration Boundary

The best first integration boundary is the predictive layer.

### 4.1 System C

Current structure:

- explicit predictive features $y_t$
- explicit context encoder $s_t$
- explicit predictive memory $q_t(s,a)$
- explicit signed error
- explicit traces
- explicit modulation

Natural replacement:

$$
\hat y_{t+1} = f_\theta(y_t, a_t)
$$

or more conservatively:

$$
\hat y_{t+1} = f_\theta(s_t, a_t)
$$

The PyTorch module replaces the predictor only.

### 4.2 System C+W

Current structure:

- shared predictive feature vector $y_t^{CW}$
- shared predictive memory $q_t(s,a)$
- drive-specific trace interpretation
- explicit dual modulation before arbitration

Natural replacement:

$$
\hat y_{t+1}^{CW} = f_\theta(y_t^{CW}, a_t)
$$

Again, the predictor is the learned piece. The rest of the system remains
analytical.

---

## 5. Runtime Placement Inside AXIS Systems

### 5.1 System Object vs Agent State

This is the first important design distinction.

There are two possible homes for neural runtime state:

1. **System runtime object**
2. **Agent state**

These should not be conflated.

#### System runtime object

Good place for:

- `nn.Module`
- optimizer instance
- device object
- loss function
- training mode flags

This is runtime machinery, not conceptual cognitive state.

#### Agent state

Good place for:

- conceptual internal variables the model is supposed to expose explicitly
- perhaps lightweight predictor-facing metadata if needed

Poor place for:

- raw optimizer internals
- low-level tensor bookkeeping

So the default recommendation is:

> keep PyTorch module and optimizer in the system runtime object, not in the
> explicit AXIS agent state model.

---

## 6. Device Model

### 6.1 CPU/GPU Support

A PyTorch submodule can absolutely use GPU power.

The standard pattern is:

$$
\text{module} \to \texttt{device}
$$

$$
\text{input tensor} \to \texttt{device}
$$

$$
\text{output tensor} \to \text{host / Python values as needed}
$$

So there is no conceptual obstacle to:

- CPU execution for early small models
- GPU execution for accelerated online updates

### 6.2 Recommended Device Policy

The first design should support:

- explicit device selection via config
- CPU fallback if CUDA is unavailable
- no hard dependency on GPU presence

This means the neural submodule should be device-aware, but the outer AXIS
system should remain device-agnostic except for passing that configuration in.

### 6.3 Practical Recommendation

For first experiments:

- CPU should be the baseline
- GPU should be optional acceleration

The model sizes we are discussing for first predictors are small enough that
CPU is likely sufficient.

But the architecture should not block GPU use.

---

## 7. Persistence and Checkpointing

This is the most important technical implication.

Once a system contains a PyTorch module, we must define what exactly persists
across time.

### 7.1 Key Questions

We must decide:

- are weights reset at every episode?
- do weights persist across episodes in the same run?
- does optimizer state persist?
- can runs resume from a saved checkpoint?
- are initial weights loaded from an artifact?

These choices are scientifically meaningful.

### 7.2 Recommended First Policy

For the first controlled experiments, the cleanest regime is probably:

- initial weights loaded once at run start
- online updates persist across episodes within the run
- weights are saved as part of the run artifact
- optimizer state may also be saved for exact reproducibility

This best matches the idea of within-lifetime or within-run adaptation.

### 7.3 Separation of Concerns

AXIS should distinguish clearly between:

- **conceptual agent state**
- **learned model artifact state**

That means predictor weights should likely live in a checkpoint artifact rather
than being flattened into the ordinary explicit agent-state JSON structure.

---

## 8. Configuration Implications

A PyTorch-based submodule will require an explicit config surface.

Typical fields would include:

- enabled / disabled
- architecture type
- input dimension
- hidden dimension(s)
- output dimension
- device
- learning rate
- optimizer type
- update frequency
- checkpoint policy
- online learning enabled / disabled

So a future AXIS config might include something like:

```yaml
prediction:
  mode: neural
  architecture:
    kind: mlp
    hidden_dims: [32, 32]
  runtime:
    device: cuda
    online_learning: true
    update_every_steps: 1
    optimizer: adam
    learning_rate: 1e-3
  checkpoint:
    save_weights: true
    save_optimizer: true
```

The exact schema can be decided later, but the need for an explicit config
surface is unavoidable.

---

## 9. Reduction and Fallback Requirements

A PyTorch integration must preserve AXIS-style reduction logic.

That means there should be a neutral mode in which the predictor’s influence is
removed or bypassed.

Examples:

- disable online updates
- force modulation to 1.0
- bypass neural output and use analytical fallback
- load a zero-influence predictor

This is important because it allows direct comparison between:

- analytical baseline
- analytical system with manual predictor
- analytical system with neural predictor

Without this, the neural integration becomes much harder to analyze.

---

## 10. Recommended First Runtime Shape

### 10.1 For System C

A plausible runtime shape is:

- `SystemC`
  - owns sensor, hunger drive, policy, transition
  - owns `NeuralPredictorModule`
  - owns optimizer
  - owns device selection

Decision phase:

1. extract features
2. run predictor forward pass
3. use predicted output in the existing signed-error / trace / modulation logic

Transition phase:

1. compute actual post-action features
2. form target
3. compute loss
4. step optimizer if online learning is enabled

### 10.2 For System C+W

A plausible runtime shape is:

- `SystemCW`
  - owns hunger drive, curiosity drive, arbitration, policy, transition
  - owns one shared `NeuralPredictorModule`
  - owns optimizer and device

The shared predictor output is then interpreted through:

- hunger-side outcome semantics
- curiosity-side outcome semantics

exactly as the manual shared memory is interpreted today.

---

## 11. What Should Not Be Done First

Even though PyTorch integration is feasible, several technical moves would be
poor first choices.

### 11.1 Do Not Make the Entire Agent a Torch Module

That would destroy the clean subsystem boundary.

### 11.2 Do Not Put Raw Torch Runtime Internals into AgentState

That would pollute the explicit conceptual state model with engineering-level
training machinery.

### 11.3 Do Not Make GPU a Hard Requirement

That would make early scientific experimentation unnecessarily brittle.

### 11.4 Do Not Entangle Predictor Learning with Global Policy Learning

The first submodule should be isolated.

---

## 12. Bottom-Line Conclusion

The technical answer is straightforward:

> yes, a PyTorch-based neural submodule can be integrated cleanly into AXIS
> system implementations, and yes, it can use GPU power.

The important design constraints are not about feasibility. They are about:

- module boundary
- runtime placement
- state vs checkpoint separation
- device handling
- reduction paths
- persistence semantics

The cleanest first use remains:

- `System C` with a PyTorch predictor
- then `System C+W` with a shared PyTorch predictor

That gives AXIS a practical route into neural online learning without forcing
AXIS itself to become a monolithic ML runtime.
